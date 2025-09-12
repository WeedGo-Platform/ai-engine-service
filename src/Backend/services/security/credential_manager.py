"""
Secure Credential Management System
Handles encryption, decryption, and secure storage of payment provider credentials
Following PCI DSS and industry best practices
"""

import os
import json
import base64
import hashlib
import secrets
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import asyncpg
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class EncryptionMethod(Enum):
    """Supported encryption methods"""
    AES_256_GCM = "aes_256_gcm"
    FERNET = "fernet"
    
    
class CredentialType(Enum):
    """Types of credentials that can be stored"""
    CLOVER_API = "clover_api"
    MONERIS_API = "moneris_api"
    STRIPE_API = "stripe_api"
    SQUARE_API = "square_api"
    INTERAC_API = "interac_api"
    NUVEI_API = "nuvei_api"
    WEBHOOK_SECRET = "webhook_secret"
    OAUTH_TOKEN = "oauth_token"


class CredentialManager:
    """
    Manages secure storage and retrieval of payment provider credentials
    Implements encryption at rest and audit logging
    """
    
    def __init__(self, db_pool: asyncpg.Pool, master_key: Optional[str] = None):
        """
        Initialize the credential manager
        
        Args:
            db_pool: Database connection pool
            master_key: Master encryption key (should be stored in environment/KMS)
        """
        self.db_pool = db_pool
        self.logger = logger
        
        # Initialize encryption key
        if master_key:
            self._master_key = master_key.encode()
        else:
            # Load from environment variable (production should use KMS)
            master_key_env = os.environ.get('PAYMENT_MASTER_KEY')
            if not master_key_env:
                # Generate a new key for development (WARNING: not for production)
                self.logger.warning("Generating new master key - Store this securely!")
                self._master_key = Fernet.generate_key()
                self.logger.info(f"Generated Master Key (STORE SECURELY): {self._master_key.decode()}")
            else:
                self._master_key = master_key_env.encode()
        
        # Initialize Fernet cipher
        self._cipher = Fernet(self._master_key)
        
        # Cache for decrypted credentials (with TTL)
        self._credential_cache: Dict[str, Tuple[Dict, datetime]] = {}
        self._cache_ttl = timedelta(minutes=5)  # Cache for 5 minutes
        
    def _generate_key_from_password(self, password: str, salt: bytes) -> bytes:
        """
        Generate encryption key from password using PBKDF2
        
        Args:
            password: Password to derive key from
            salt: Salt for key derivation
            
        Returns:
            Derived encryption key
        """
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def _encrypt_data(self, data: Dict[str, Any]) -> Tuple[str, str]:
        """
        Encrypt sensitive data
        
        Args:
            data: Dictionary containing sensitive data
            
        Returns:
            Tuple of (encrypted_data, encryption_metadata)
        """
        try:
            # Convert to JSON
            json_data = json.dumps(data)
            
            # Encrypt using Fernet (includes timestamp and HMAC)
            encrypted = self._cipher.encrypt(json_data.encode())
            
            # Generate metadata
            metadata = {
                "method": EncryptionMethod.FERNET.value,
                "version": "1.0",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            return base64.b64encode(encrypted).decode(), json.dumps(metadata)
            
        except Exception as e:
            self.logger.error(f"Encryption failed: {str(e)}")
            raise ValueError("Failed to encrypt credential data")
    
    def _decrypt_data(self, encrypted_data: str, metadata: str) -> Dict[str, Any]:
        """
        Decrypt sensitive data
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            metadata: Encryption metadata
            
        Returns:
            Decrypted data dictionary
        """
        try:
            # Parse metadata
            meta = json.loads(metadata) if isinstance(metadata, str) else metadata
            
            # Decode from base64
            encrypted = base64.b64decode(encrypted_data.encode())
            
            # Decrypt based on method
            if meta.get("method") == EncryptionMethod.FERNET.value:
                decrypted = self._cipher.decrypt(encrypted)
                return json.loads(decrypted.decode())
            else:
                raise ValueError(f"Unsupported encryption method: {meta.get('method')}")
                
        except Exception as e:
            self.logger.error(f"Decryption failed: {str(e)}")
            raise ValueError("Failed to decrypt credential data")
    
    async def store_credential(
        self,
        tenant_id: str,
        provider: str,
        credential_type: CredentialType,
        credentials: Dict[str, Any],
        description: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> str:
        """
        Store encrypted credentials for a tenant
        
        Args:
            tenant_id: Tenant UUID
            provider: Payment provider name (e.g., 'clover', 'moneris')
            credential_type: Type of credential being stored
            credentials: Dictionary containing sensitive credentials
            description: Optional description
            expires_at: Optional expiration time for the credential
            
        Returns:
            Credential ID
        """
        try:
            # Validate inputs
            if not tenant_id or not provider or not credentials:
                raise ValueError("Missing required parameters")
            
            # Encrypt the credentials
            encrypted_data, encryption_metadata = self._encrypt_data(credentials)
            
            # Generate unique credential ID
            credential_id = secrets.token_urlsafe(32)
            
            # Store in database
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO payment_credentials (
                        id, tenant_id, provider, credential_type,
                        encrypted_data, encryption_metadata,
                        description, expires_at, is_active,
                        created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, true,
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                """, credential_id, tenant_id, provider, credential_type.value,
                    encrypted_data, encryption_metadata, description, expires_at)
                
                # Log audit entry
                await self._log_audit(
                    conn, tenant_id, "credential_stored",
                    {"provider": provider, "credential_type": credential_type.value}
                )
            
            self.logger.info(f"Stored credential for tenant {tenant_id}, provider {provider}")
            return credential_id
            
        except Exception as e:
            self.logger.error(f"Failed to store credential: {str(e)}")
            raise
    
    async def retrieve_credential(
        self,
        tenant_id: str,
        provider: str,
        credential_type: Optional[CredentialType] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve and decrypt credentials for a tenant
        
        Args:
            tenant_id: Tenant UUID
            provider: Payment provider name
            credential_type: Optional specific credential type
            
        Returns:
            Decrypted credentials or None if not found
        """
        try:
            # Check cache first
            cache_key = f"{tenant_id}:{provider}:{credential_type.value if credential_type else 'any'}"
            if cache_key in self._credential_cache:
                cached_data, cached_time = self._credential_cache[cache_key]
                if datetime.now(timezone.utc) - cached_time < self._cache_ttl:
                    return cached_data
                else:
                    del self._credential_cache[cache_key]
            
            # Retrieve from database
            async with self.db_pool.acquire() as conn:
                query = """
                    SELECT encrypted_data, encryption_metadata, expires_at
                    FROM payment_credentials
                    WHERE tenant_id = $1 AND provider = $2 AND is_active = true
                """
                params = [tenant_id, provider]
                
                if credential_type:
                    query += " AND credential_type = $3"
                    params.append(credential_type.value)
                
                query += " ORDER BY created_at DESC LIMIT 1"
                
                row = await conn.fetchrow(query, *params)
                
                if not row:
                    return None
                
                # Check expiration
                if row['expires_at'] and row['expires_at'] < datetime.now(timezone.utc):
                    self.logger.warning(f"Credential expired for tenant {tenant_id}, provider {provider}")
                    return None
                
                # Decrypt credentials
                decrypted = self._decrypt_data(
                    row['encrypted_data'],
                    row['encryption_metadata']
                )
                
                # Cache the result
                self._credential_cache[cache_key] = (decrypted, datetime.now(timezone.utc))
                
                # Log audit entry
                await self._log_audit(
                    conn, tenant_id, "credential_accessed",
                    {"provider": provider}
                )
                
                return decrypted
                
        except Exception as e:
            self.logger.error(f"Failed to retrieve credential: {str(e)}")
            return None
    
    async def update_credential(
        self,
        tenant_id: str,
        provider: str,
        credentials: Dict[str, Any],
        credential_type: Optional[CredentialType] = None
    ) -> bool:
        """
        Update existing credentials for a tenant
        
        Args:
            tenant_id: Tenant UUID
            provider: Payment provider name
            credentials: New credentials to store
            credential_type: Optional specific credential type
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Encrypt new credentials
            encrypted_data, encryption_metadata = self._encrypt_data(credentials)
            
            # Update in database
            async with self.db_pool.acquire() as conn:
                query = """
                    UPDATE payment_credentials
                    SET encrypted_data = $1,
                        encryption_metadata = $2,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE tenant_id = $3 AND provider = $4 AND is_active = true
                """
                params = [encrypted_data, encryption_metadata, tenant_id, provider]
                
                if credential_type:
                    query += " AND credential_type = $5"
                    params.append(credential_type.value)
                
                result = await conn.execute(query, *params)
                
                # Clear cache
                cache_key = f"{tenant_id}:{provider}:{credential_type.value if credential_type else 'any'}"
                if cache_key in self._credential_cache:
                    del self._credential_cache[cache_key]
                
                # Log audit entry
                await self._log_audit(
                    conn, tenant_id, "credential_updated",
                    {"provider": provider}
                )
                
                return result != "UPDATE 0"
                
        except Exception as e:
            self.logger.error(f"Failed to update credential: {str(e)}")
            return False
    
    async def revoke_credential(
        self,
        tenant_id: str,
        provider: str,
        credential_type: Optional[CredentialType] = None
    ) -> bool:
        """
        Revoke (soft delete) credentials for a tenant
        
        Args:
            tenant_id: Tenant UUID
            provider: Payment provider name
            credential_type: Optional specific credential type
            
        Returns:
            True if revocation successful, False otherwise
        """
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    UPDATE payment_credentials
                    SET is_active = false,
                        revoked_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE tenant_id = $1 AND provider = $2 AND is_active = true
                """
                params = [tenant_id, provider]
                
                if credential_type:
                    query += " AND credential_type = $3"
                    params.append(credential_type.value)
                
                result = await conn.execute(query, *params)
                
                # Clear cache
                cache_key = f"{tenant_id}:{provider}:{credential_type.value if credential_type else 'any'}"
                if cache_key in self._credential_cache:
                    del self._credential_cache[cache_key]
                
                # Log audit entry
                await self._log_audit(
                    conn, tenant_id, "credential_revoked",
                    {"provider": provider}
                )
                
                return result != "UPDATE 0"
                
        except Exception as e:
            self.logger.error(f"Failed to revoke credential: {str(e)}")
            return False
    
    async def rotate_credential(
        self,
        tenant_id: str,
        provider: str,
        new_credentials: Dict[str, Any],
        credential_type: Optional[CredentialType] = None
    ) -> bool:
        """
        Rotate credentials (revoke old, create new)
        
        Args:
            tenant_id: Tenant UUID
            provider: Payment provider name
            new_credentials: New credentials to store
            credential_type: Optional specific credential type
            
        Returns:
            True if rotation successful, False otherwise
        """
        try:
            # Begin transaction
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    # Revoke existing credentials
                    await self.revoke_credential(tenant_id, provider, credential_type)
                    
                    # Store new credentials
                    credential_id = await self.store_credential(
                        tenant_id, provider,
                        credential_type or CredentialType.CLOVER_API,
                        new_credentials,
                        description="Rotated credential"
                    )
                    
                    # Log audit entry
                    await self._log_audit(
                        conn, tenant_id, "credential_rotated",
                        {"provider": provider, "new_credential_id": credential_id}
                    )
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to rotate credential: {str(e)}")
            return False
    
    async def _log_audit(
        self,
        conn: asyncpg.Connection,
        tenant_id: str,
        action: str,
        details: Dict[str, Any]
    ):
        """
        Log audit entry for credential operations
        
        Args:
            conn: Database connection
            tenant_id: Tenant UUID
            action: Action performed
            details: Additional details
        """
        try:
            await conn.execute("""
                INSERT INTO payment_audit_log (
                    tenant_id, action, details, created_at
                ) VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
            """, tenant_id, action, json.dumps(details))
        except Exception as e:
            self.logger.error(f"Failed to log audit entry: {str(e)}")
    
    async def cleanup_expired_credentials(self) -> int:
        """
        Clean up expired credentials from the database
        
        Returns:
            Number of credentials cleaned up
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute("""
                    UPDATE payment_credentials
                    SET is_active = false,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE is_active = true
                    AND expires_at IS NOT NULL
                    AND expires_at < CURRENT_TIMESTAMP
                """)
                
                count = int(result.split()[-1])
                if count > 0:
                    self.logger.info(f"Cleaned up {count} expired credentials")
                
                return count
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired credentials: {str(e)}")
            return 0
    
    def clear_cache(self):
        """Clear the credential cache"""
        self._credential_cache.clear()
        self.logger.info("Credential cache cleared")