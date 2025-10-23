"""
OCS OAuth 2.0 Authentication Service

Handles OAuth 2.0 client credentials flow for OCS API authentication.
Implements automatic token refresh, caching, and bcrypt encryption for credentials.
"""

import os
import logging
import asyncpg
import aiohttp
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OCSCredentials:
    """OCS OAuth credentials for a tenant"""
    tenant_id: str
    client_id: str
    client_secret: str
    token_url: str
    
    
@dataclass
class OCSToken:
    """OCS OAuth token"""
    access_token: str
    expires_at: datetime
    token_type: str = "Bearer"
    
    def is_expired(self) -> bool:
        """Check if token is expired (with 5 minute buffer)"""
        return datetime.utcnow() >= (self.expires_at - timedelta(minutes=5))


class OCSAuthService:
    """
    OCS OAuth 2.0 Authentication Service
    
    Features:
    - OAuth 2.0 client credentials flow
    - Automatic token refresh
    - Token caching in database
    - bcrypt encryption for client credentials
    - Tenant-specific credential management
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.ocs_base_url = os.getenv('OCS_API_BASE_URL', 'https://api.ocs.ca')
        self.token_url = f"{self.ocs_base_url}/oauth/token"
        
    async def encrypt_credential(self, value: str) -> str:
        """Encrypt credential using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(value.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    async def store_credentials(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str
    ) -> bool:
        """
        Store encrypted OCS credentials for a tenant
        
        Args:
            tenant_id: Tenant UUID
            client_id: OCS OAuth client ID
            client_secret: OCS OAuth client secret
            
        Returns:
            bool: True if successful
        """
        try:
            # Encrypt credentials
            encrypted_client_id = await self.encrypt_credential(client_id)
            encrypted_secret = await self.encrypt_credential(client_secret)
            
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO ocs_oauth_tokens (
                        tenant_id,
                        client_id_encrypted,
                        client_secret_encrypted,
                        created_at,
                        updated_at
                    ) VALUES ($1, $2, $3, NOW(), NOW())
                    ON CONFLICT (tenant_id) 
                    DO UPDATE SET
                        client_id_encrypted = EXCLUDED.client_id_encrypted,
                        client_secret_encrypted = EXCLUDED.client_secret_encrypted,
                        updated_at = NOW()
                """, tenant_id, encrypted_client_id, encrypted_secret)
                
            logger.info(f"Stored OCS credentials for tenant {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing OCS credentials for tenant {tenant_id}: {e}")
            return False
    
    async def get_access_token(self, tenant_id: str) -> Optional[str]:
        """
        Get valid access token for tenant (from cache or by requesting new one)
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            str: Valid access token or None if failed
        """
        try:
            # Check if we have a valid cached token
            cached_token = await self._get_cached_token(tenant_id)
            if cached_token and not cached_token.is_expired():
                logger.debug(f"Using cached token for tenant {tenant_id}")
                return cached_token.access_token
            
            # Request new token
            logger.info(f"Requesting new OCS token for tenant {tenant_id}")
            new_token = await self._request_new_token(tenant_id)
            
            if new_token:
                # Cache the new token
                await self._cache_token(tenant_id, new_token)
                return new_token.access_token
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting access token for tenant {tenant_id}: {e}")
            return None
    
    async def _get_cached_token(self, tenant_id: str) -> Optional[OCSToken]:
        """Get cached token from database"""
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT 
                        access_token_encrypted,
                        token_expires_at
                    FROM ocs_oauth_tokens
                    WHERE tenant_id = $1
                    AND access_token_encrypted IS NOT NULL
                """, tenant_id)
                
                if not row:
                    return None
                
                # Note: In production, you'd decrypt the token here
                # For now, we'll store tokens encrypted but decrypt on retrieval
                # This requires storing the encryption key securely
                return OCSToken(
                    access_token=row['access_token_encrypted'],  # TODO: Decrypt
                    expires_at=row['token_expires_at']
                )
                
        except Exception as e:
            logger.error(f"Error getting cached token for tenant {tenant_id}: {e}")
            return None
    
    async def _request_new_token(self, tenant_id: str) -> Optional[OCSToken]:
        """Request new token from OCS OAuth server"""
        try:
            # Get credentials (note: in production, decrypt these)
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT 
                        client_id_encrypted,
                        client_secret_encrypted
                    FROM ocs_oauth_tokens
                    WHERE tenant_id = $1
                """, tenant_id)
                
                if not row:
                    logger.error(f"No OCS credentials found for tenant {tenant_id}")
                    return None
                
                # TODO: Decrypt credentials in production
                client_id = row['client_id_encrypted']
                client_secret = row['client_secret_encrypted']
            
            # Request token from OCS
            async with aiohttp.ClientSession() as session:
                data = {
                    'grant_type': 'client_credentials',
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'scope': 'inventory.write inventory.read asn.read'
                }
                
                async with session.post(self.token_url, data=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"OCS token request failed: {response.status} - {error_text}")
                        return None
                    
                    token_data = await response.json()
                    
                    # Calculate expiration time
                    expires_in = token_data.get('expires_in', 3600)
                    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                    
                    return OCSToken(
                        access_token=token_data['access_token'],
                        expires_at=expires_at,
                        token_type=token_data.get('token_type', 'Bearer')
                    )
                    
        except Exception as e:
            logger.error(f"Error requesting new token for tenant {tenant_id}: {e}")
            return None
    
    async def _cache_token(self, tenant_id: str, token: OCSToken) -> bool:
        """Cache token in database"""
        try:
            # TODO: Encrypt token before storing
            encrypted_token = token.access_token  # In production: await self.encrypt_credential(token.access_token)
            
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE ocs_oauth_tokens
                    SET 
                        access_token_encrypted = $1,
                        token_expires_at = $2,
                        updated_at = NOW()
                    WHERE tenant_id = $3
                """, encrypted_token, token.expires_at, tenant_id)
                
            logger.info(f"Cached new token for tenant {tenant_id}, expires at {token.expires_at}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching token for tenant {tenant_id}: {e}")
            return False
    
    async def revoke_token(self, tenant_id: str) -> bool:
        """
        Revoke cached token (forces refresh on next request)
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            bool: True if successful
        """
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE ocs_oauth_tokens
                    SET 
                        access_token_encrypted = NULL,
                        token_expires_at = NULL,
                        updated_at = NOW()
                    WHERE tenant_id = $1
                """, tenant_id)
                
            logger.info(f"Revoked token for tenant {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking token for tenant {tenant_id}: {e}")
            return False
    
    async def validate_credentials(
        self,
        client_id: str,
        client_secret: str
    ) -> bool:
        """
        Validate OCS credentials by attempting to get a token
        
        Args:
            client_id: OCS OAuth client ID
            client_secret: OCS OAuth client secret
            
        Returns:
            bool: True if credentials are valid
        """
        try:
            async with aiohttp.ClientSession() as session:
                data = {
                    'grant_type': 'client_credentials',
                    'client_id': client_id,
                    'client_secret': client_secret
                }
                
                async with session.post(self.token_url, data=data) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"Error validating OCS credentials: {e}")
            return False
