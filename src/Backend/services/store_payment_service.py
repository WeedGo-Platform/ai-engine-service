"""
Store-Specific Payment Provider Service
Manages payment configurations per store with multi-tenant isolation
Follows SOLID principles and clean architecture patterns
"""

from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID, uuid4
from datetime import datetime
import asyncpg
import logging
import json
from enum import Enum
from cryptography.fernet import Fernet
import os

logger = logging.getLogger(__name__)


class PaymentProviderType(Enum):
    """Supported payment provider types"""
    STRIPE = "stripe"
    SQUARE = "square"
    CLOVER = "clover"
    PAYPAL = "paypal"
    MONERIS = "moneris"
    CUSTOM = "custom"


class PaymentMethodType(Enum):
    """Supported payment method types"""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    DIGITAL_WALLET = "digital_wallet"
    CRYPTO = "crypto"
    STORE_CREDIT = "store_credit"


class StorePaymentService:
    """
    Service for managing store-specific payment configurations
    Implements secure credential storage and provider management
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize store payment service
        
        Args:
            db_pool: Database connection pool
        """
        self.db_pool = db_pool
        self._init_encryption()
    
    def _init_encryption(self):
        """Initialize encryption for sensitive data"""
        # Get or generate encryption key
        encryption_key = os.environ.get('PAYMENT_MASTER_KEY')
        if not encryption_key:
            logger.warning("PAYMENT_MASTER_KEY not set, using default (NOT FOR PRODUCTION)")
            encryption_key = Fernet.generate_key().decode()
        
        self.cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
    
    def _encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """
        Encrypt payment credentials
        
        Args:
            credentials: Plain text credentials
            
        Returns:
            Encrypted credentials string
        """
        json_str = json.dumps(credentials)
        encrypted = self.cipher.encrypt(json_str.encode())
        return encrypted.decode()
    
    def _decrypt_credentials(self, encrypted: str) -> Dict[str, Any]:
        """
        Decrypt payment credentials
        
        Args:
            encrypted: Encrypted credentials string
            
        Returns:
            Decrypted credentials dictionary
        """
        try:
            decrypted = self.cipher.decrypt(encrypted.encode())
            return json.loads(decrypted.decode())
        except Exception as e:
            logger.error(f"Failed to decrypt credentials: {str(e)}")
            return {}
    
    # =====================================================
    # Store Payment Provider Management
    # =====================================================
    
    async def create_store_payment_provider(
        self,
        store_id: UUID,
        provider_type: PaymentProviderType,
        credentials: Dict[str, Any],
        settings: Optional[Dict[str, Any]] = None,
        is_primary: bool = False
    ) -> UUID:
        """
        Create payment provider configuration for a store
        
        Args:
            store_id: UUID of the store
            provider_type: Type of payment provider
            credentials: Provider credentials (will be encrypted)
            settings: Additional provider settings
            is_primary: Whether this is the primary provider
            
        Returns:
            UUID of created configuration
        """
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    # Encrypt credentials
                    encrypted_credentials = self._encrypt_credentials(credentials)
                    
                    # If setting as primary, unset other primaries
                    if is_primary:
                        await conn.execute("""
                            UPDATE store_payment_providers
                            SET is_primary = false
                            WHERE store_id = $1 AND is_primary = true
                        """, store_id)
                    
                    # Create provider configuration
                    provider_id = await conn.fetchval("""
                        INSERT INTO store_payment_providers
                        (store_id, provider_type, encrypted_credentials, 
                         settings, is_primary, is_active)
                        VALUES ($1, $2, $3, $4, $5, true)
                        RETURNING id
                    """, store_id, provider_type.value, encrypted_credentials,
                        json.dumps(settings or {}), is_primary)
                    
                    # Log configuration
                    await conn.execute("""
                        INSERT INTO payment_audit_log
                        (store_id, action, entity_type, entity_id, details)
                        VALUES ($1, 'create', 'payment_provider', $2, $3)
                    """, store_id, provider_id, json.dumps({
                        'provider_type': provider_type.value,
                        'is_primary': is_primary
                    }))
                    
                    logger.info(f"Created payment provider {provider_type.value} for store {store_id}")
                    return provider_id
                    
        except Exception as e:
            logger.error(f"Error creating store payment provider: {str(e)}")
            raise
    
    async def get_store_payment_providers(
        self,
        store_id: UUID,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get payment providers for a store
        
        Args:
            store_id: UUID of the store
            active_only: Return only active providers
            
        Returns:
            List of provider configurations (credentials excluded)
        """
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    SELECT 
                        id,
                        provider_type,
                        settings,
                        is_primary,
                        is_active,
                        supported_methods,
                        fee_structure,
                        created_at,
                        updated_at
                    FROM store_payment_providers
                    WHERE store_id = $1
                """
                
                if active_only:
                    query += " AND is_active = true"
                
                query += " ORDER BY is_primary DESC, created_at DESC"
                
                results = await conn.fetch(query, store_id)
                
                return [dict(r) for r in results]
                
        except Exception as e:
            logger.error(f"Error getting store payment providers: {str(e)}")
            raise
    
    async def get_store_payment_credentials(
        self,
        store_id: UUID,
        provider_id: UUID
    ) -> Dict[str, Any]:
        """
        Get decrypted payment credentials for a provider
        CAUTION: Use only when needed for payment processing
        
        Args:
            store_id: UUID of the store
            provider_id: UUID of the provider configuration
            
        Returns:
            Decrypted credentials
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT encrypted_credentials
                    FROM store_payment_providers
                    WHERE store_id = $1 AND id = $2 AND is_active = true
                """, store_id, provider_id)
                
                if not result:
                    raise ValueError(f"Payment provider {provider_id} not found for store {store_id}")
                
                # Decrypt and return credentials
                return self._decrypt_credentials(result['encrypted_credentials'])
                
        except Exception as e:
            logger.error(f"Error getting payment credentials: {str(e)}")
            raise
    
    async def update_store_payment_provider(
        self,
        store_id: UUID,
        provider_id: UUID,
        credentials: Optional[Dict[str, Any]] = None,
        settings: Optional[Dict[str, Any]] = None,
        is_primary: Optional[bool] = None,
        is_active: Optional[bool] = None
    ) -> bool:
        """
        Update payment provider configuration
        
        Args:
            store_id: UUID of the store
            provider_id: UUID of the provider
            credentials: New credentials (will be encrypted)
            settings: New settings
            is_primary: Update primary status
            is_active: Update active status
            
        Returns:
            True if updated successfully
        """
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    # Build update query
                    updates = []
                    params = [store_id, provider_id]
                    param_counter = 3
                    
                    if credentials is not None:
                        encrypted = self._encrypt_credentials(credentials)
                        updates.append(f"encrypted_credentials = ${param_counter}")
                        params.append(encrypted)
                        param_counter += 1
                    
                    if settings is not None:
                        updates.append(f"settings = ${param_counter}")
                        params.append(json.dumps(settings))
                        param_counter += 1
                    
                    if is_primary is not None:
                        if is_primary:
                            # Unset other primaries
                            await conn.execute("""
                                UPDATE store_payment_providers
                                SET is_primary = false
                                WHERE store_id = $1 AND is_primary = true
                            """, store_id)
                        updates.append(f"is_primary = ${param_counter}")
                        params.append(is_primary)
                        param_counter += 1
                    
                    if is_active is not None:
                        updates.append(f"is_active = ${param_counter}")
                        params.append(is_active)
                        param_counter += 1
                    
                    if not updates:
                        return True
                    
                    updates.append("updated_at = CURRENT_TIMESTAMP")
                    
                    query = f"""
                        UPDATE store_payment_providers
                        SET {', '.join(updates)}
                        WHERE store_id = $1 AND id = $2
                    """
                    
                    await conn.execute(query, *params)
                    
                    # Log update
                    await conn.execute("""
                        INSERT INTO payment_audit_log
                        (store_id, action, entity_type, entity_id, details)
                        VALUES ($1, 'update', 'payment_provider', $2, $3)
                    """, store_id, provider_id, json.dumps({
                        'updated_fields': list(updates)
                    }))
                    
                    return True
                    
        except Exception as e:
            logger.error(f"Error updating store payment provider: {str(e)}")
            raise
    
    # =====================================================
    # Payment Method Configuration
    # =====================================================
    
    async def configure_store_payment_methods(
        self,
        store_id: UUID,
        provider_id: UUID,
        enabled_methods: List[PaymentMethodType],
        method_settings: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Configure enabled payment methods for a store provider
        
        Args:
            store_id: UUID of the store
            provider_id: UUID of the provider
            enabled_methods: List of enabled payment methods
            method_settings: Settings per method
            
        Returns:
            True if configured successfully
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Update supported methods
                methods_list = [m.value for m in enabled_methods]
                
                await conn.execute("""
                    UPDATE store_payment_providers
                    SET supported_methods = $3,
                        method_settings = $4,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE store_id = $1 AND id = $2
                """, store_id, provider_id, methods_list,
                    json.dumps(method_settings or {}))
                
                return True
                
        except Exception as e:
            logger.error(f"Error configuring payment methods: {str(e)}")
            raise
    
    # =====================================================
    # Fee Structure Management
    # =====================================================
    
    async def set_store_fee_structure(
        self,
        store_id: UUID,
        provider_id: UUID,
        fee_structure: Dict[str, Any]
    ) -> bool:
        """
        Set fee structure for a store's payment provider
        
        Args:
            store_id: UUID of the store
            provider_id: UUID of the provider
            fee_structure: Fee configuration
                {
                    "transaction_fee_percent": 2.9,
                    "transaction_fee_fixed": 0.30,
                    "monthly_fee": 0,
                    "setup_fee": 0,
                    "chargeback_fee": 15.00,
                    "refund_fee": 0
                }
        
        Returns:
            True if set successfully
        """
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE store_payment_providers
                    SET fee_structure = $3,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE store_id = $1 AND id = $2
                """, store_id, provider_id, json.dumps(fee_structure))
                
                return True
                
        except Exception as e:
            logger.error(f"Error setting fee structure: {str(e)}")
            raise
    
    # =====================================================
    # Payment Processing
    # =====================================================
    
    async def get_store_primary_provider(
        self,
        store_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get primary payment provider for a store
        
        Args:
            store_id: UUID of the store
            
        Returns:
            Primary provider configuration or None
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT 
                        id,
                        provider_type,
                        settings,
                        supported_methods,
                        fee_structure
                    FROM store_payment_providers
                    WHERE store_id = $1 
                    AND is_primary = true 
                    AND is_active = true
                """, store_id)
                
                if result:
                    return dict(result)
                
                # Fall back to first active provider
                result = await conn.fetchrow("""
                    SELECT 
                        id,
                        provider_type,
                        settings,
                        supported_methods,
                        fee_structure
                    FROM store_payment_providers
                    WHERE store_id = $1 
                    AND is_active = true
                    ORDER BY created_at
                    LIMIT 1
                """, store_id)
                
                return dict(result) if result else None
                
        except Exception as e:
            logger.error(f"Error getting primary provider: {str(e)}")
            raise
    
    async def process_store_payment(
        self,
        store_id: UUID,
        amount: float,
        payment_method: PaymentMethodType,
        payment_details: Dict[str, Any],
        provider_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Process payment for a store
        
        Args:
            store_id: UUID of the store
            amount: Payment amount
            payment_method: Type of payment method
            payment_details: Payment details (card info, etc.)
            provider_id: Optional specific provider to use
            
        Returns:
            Payment result
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Get provider
                if provider_id:
                    provider = await conn.fetchrow("""
                        SELECT * FROM store_payment_providers
                        WHERE store_id = $1 AND id = $2 AND is_active = true
                    """, store_id, provider_id)
                else:
                    # Use primary provider
                    provider = await conn.fetchrow("""
                        SELECT * FROM store_payment_providers
                        WHERE store_id = $1 AND is_primary = true AND is_active = true
                    """, store_id)
                
                if not provider:
                    raise ValueError(f"No active payment provider for store {store_id}")
                
                # Get credentials
                credentials = self._decrypt_credentials(provider['encrypted_credentials'])
                
                # Process based on provider type
                provider_type = PaymentProviderType(provider['provider_type'])
                
                if provider_type == PaymentProviderType.STRIPE:
                    result = await self._process_stripe_payment(
                        credentials, amount, payment_method, payment_details
                    )
                elif provider_type == PaymentProviderType.SQUARE:
                    result = await self._process_square_payment(
                        credentials, amount, payment_method, payment_details
                    )
                elif provider_type == PaymentProviderType.CLOVER:
                    result = await self._process_clover_payment(
                        credentials, amount, payment_method, payment_details
                    )
                else:
                    raise ValueError(f"Unsupported provider type: {provider_type}")
                
                # Record transaction
                await conn.execute("""
                    INSERT INTO payment_transactions
                    (store_id, provider_id, amount, payment_method, 
                     status, provider_response, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP)
                """, store_id, provider['id'], amount, payment_method.value,
                    result.get('status'), json.dumps(result))
                
                return result
                
        except Exception as e:
            logger.error(f"Error processing store payment: {str(e)}")
            raise
    
    async def _process_stripe_payment(
        self,
        credentials: Dict[str, Any],
        amount: float,
        payment_method: PaymentMethodType,
        payment_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process payment through Stripe"""
        # Implementation would use Stripe SDK
        # This is a placeholder
        return {
            'status': 'success',
            'transaction_id': str(uuid4()),
            'provider': 'stripe',
            'amount': amount
        }
    
    async def _process_square_payment(
        self,
        credentials: Dict[str, Any],
        amount: float,
        payment_method: PaymentMethodType,
        payment_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process payment through Square"""
        # Implementation would use Square SDK
        # This is a placeholder
        return {
            'status': 'success',
            'transaction_id': str(uuid4()),
            'provider': 'square',
            'amount': amount
        }
    
    async def _process_clover_payment(
        self,
        credentials: Dict[str, Any],
        amount: float,
        payment_method: PaymentMethodType,
        payment_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process payment through Clover"""
        # Implementation would use Clover SDK
        # This is a placeholder
        return {
            'status': 'success',
            'transaction_id': str(uuid4()),
            'provider': 'clover',
            'amount': amount
        }
    
    # =====================================================
    # Reporting and Analytics
    # =====================================================
    
    async def get_store_payment_stats(
        self,
        store_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get payment statistics for a store
        
        Args:
            store_id: UUID of the store
            start_date: Start date for stats
            end_date: End date for stats
            
        Returns:
            Payment statistics
        """
        try:
            async with self.db_pool.acquire() as conn:
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_transactions,
                        SUM(amount) as total_amount,
                        AVG(amount) as average_amount,
                        COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_transactions,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_transactions,
                        COUNT(DISTINCT payment_method) as payment_methods_used
                    FROM payment_transactions
                    WHERE store_id = $1
                    AND created_at BETWEEN $2 AND $3
                """, store_id, start_date, end_date)
                
                # Get breakdown by payment method
                method_breakdown = await conn.fetch("""
                    SELECT 
                        payment_method,
                        COUNT(*) as count,
                        SUM(amount) as total
                    FROM payment_transactions
                    WHERE store_id = $1
                    AND created_at BETWEEN $2 AND $3
                    GROUP BY payment_method
                """, store_id, start_date, end_date)
                
                return {
                    'summary': dict(stats),
                    'by_method': [dict(r) for r in method_breakdown]
                }
                
        except Exception as e:
            logger.error(f"Error getting payment stats: {str(e)}")
            raise


# =====================================================
# Factory Function
# =====================================================

def create_store_payment_service(db_pool: asyncpg.Pool) -> StorePaymentService:
    """
    Factory function to create store payment service
    
    Args:
        db_pool: Database connection pool
        
    Returns:
        StorePaymentService instance
    """
    return StorePaymentService(db_pool)