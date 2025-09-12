"""
Payment Service V2 - Multi-tenant Payment Orchestration Service
Manages tenant-specific payment providers with routing, failover, and fee splitting
Following SOLID principles and clean architecture
"""

from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4
import asyncpg
import logging
import json
import hashlib
from enum import Enum

from services.payment.base import (
    BasePaymentProvider, PaymentRequest, PaymentResponse,
    PaymentStatus, PaymentMethodType, TransactionType,
    PaymentError, PaymentMethod
)
from services.payment.provider_factory import PaymentProviderFactory, ProviderType
from services.security.credential_manager import CredentialManager

logger = logging.getLogger(__name__)


class PaymentServiceV2:
    """
    Enhanced payment service with multi-tenant support
    Handles routing, failover, idempotency, and platform fee splitting
    """
    
    def __init__(
        self,
        db_pool: asyncpg.Pool,
        provider_factory: PaymentProviderFactory,
        credential_manager: CredentialManager
    ):
        self.db_pool = db_pool
        self.provider_factory = provider_factory
        self.credential_manager = credential_manager
        self.logger = logger
        
        # Circuit breaker configuration
        self.circuit_breaker_threshold = 5  # failures before opening
        self.circuit_breaker_timeout = timedelta(minutes=5)
        self._circuit_breakers: Dict[str, Dict] = {}
    
    async def process_payment(
        self,
        tenant_id: UUID,
        amount: Decimal,
        currency: str = "CAD",
        payment_method_id: Optional[UUID] = None,
        order_id: Optional[UUID] = None,
        customer_id: Optional[UUID] = None,
        provider_type: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        store_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Process a payment transaction with tenant-specific routing
        
        Args:
            tenant_id: Tenant UUID
            amount: Transaction amount
            currency: Currency code
            payment_method_id: Stored payment method ID
            order_id: Associated order ID
            customer_id: Customer ID
            provider_type: Specific provider to use (optional)
            description: Transaction description
            metadata: Additional metadata
            idempotency_key: Idempotency key for duplicate prevention
            ip_address: Customer IP address
            user_agent: Customer user agent
            store_id: Store ID for the transaction
            
        Returns:
            Transaction result dictionary
        """
        try:
            # Generate transaction reference
            transaction_ref = f"TXN-{uuid4().hex[:12].upper()}"
            
            # Check idempotency
            if idempotency_key:
                cached_response = await self._check_idempotency(
                    tenant_id, idempotency_key, 
                    self._hash_request(amount, currency, order_id)
                )
                if cached_response:
                    self.logger.info(f"Returning cached response for idempotency key: {idempotency_key}")
                    return cached_response
            
            # Get payment provider for tenant
            provider = await self._get_provider_with_failover(
                tenant_id, provider_type
            )
            
            if not provider:
                raise PaymentError(
                    "No available payment provider for tenant",
                    error_code="NO_PROVIDER_AVAILABLE"
                )
            
            # Check daily limits
            await self._check_daily_limits(tenant_id, provider, amount)
            
            # Retrieve payment method details if provided
            payment_data = None
            if payment_method_id:
                payment_data = await self._get_payment_method(payment_method_id, tenant_id)
            
            # Create payment request
            request = PaymentRequest(
                amount=amount,
                currency=currency,
                payment_method_id=payment_method_id,
                order_id=order_id,
                customer_id=customer_id,
                description=description or f"Payment for order {order_id}",
                metadata={
                    **(metadata or {}),
                    'tenant_id': str(tenant_id),
                    'store_id': str(store_id) if store_id else None,
                    'transaction_ref': transaction_ref,
                    'payment_data': payment_data
                }
            )
            
            # Process payment with retry logic
            response = await self._process_with_retry(provider, request)
            
            # Record transaction
            transaction_id = await self._record_transaction(
                tenant_id=tenant_id,
                store_id=store_id,
                provider=provider,
                request=request,
                response=response,
                transaction_ref=transaction_ref,
                ip_address=ip_address,
                user_agent=user_agent,
                idempotency_key=idempotency_key
            )
            
            # Calculate and record fee split
            await self._record_fee_split(
                transaction_id=transaction_id,
                tenant_id=tenant_id,
                provider=provider,
                amount=amount
            )
            
            # Prepare result
            result = {
                'transaction_id': str(transaction_id),
                'transaction_ref': transaction_ref,
                'status': response.status.value,
                'amount': float(response.amount),
                'currency': response.currency,
                'provider': provider.__class__.__name__.replace('Provider', '').lower(),
                'provider_transaction_id': response.provider_transaction_id,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Cache result for idempotency
            if idempotency_key:
                await self._cache_idempotency_result(
                    tenant_id, idempotency_key, result
                )
            
            # Log audit entry
            await self._log_audit(
                tenant_id=tenant_id,
                action='payment_processed',
                entity_type='transaction',
                entity_id=str(transaction_id),
                details=result
            )
            
            return result
            
        except PaymentError:
            raise
        except Exception as e:
            self.logger.error(f"Payment processing failed: {str(e)}")
            raise PaymentError(
                "Payment processing failed",
                error_code="PROCESSING_ERROR",
                provider_error=str(e)
            )
    
    async def refund_payment(
        self,
        tenant_id: UUID,
        transaction_id: UUID,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a refund for a payment transaction
        
        Args:
            tenant_id: Tenant UUID
            transaction_id: Original transaction ID
            amount: Refund amount (None for full refund)
            reason: Refund reason
            idempotency_key: Idempotency key
            
        Returns:
            Refund result dictionary
        """
        try:
            # Check idempotency
            if idempotency_key:
                cached_response = await self._check_idempotency(
                    tenant_id, idempotency_key,
                    self._hash_request(transaction_id, amount)
                )
                if cached_response:
                    return cached_response
            
            # Get original transaction
            async with self.db_pool.acquire() as conn:
                transaction = await conn.fetchrow("""
                    SELECT * FROM payment_transactions
                    WHERE id = $1 AND tenant_id = $2
                """, transaction_id, tenant_id)
                
                if not transaction:
                    raise PaymentError(
                        "Transaction not found",
                        error_code="TRANSACTION_NOT_FOUND"
                    )
                
                # Validate refund amount
                original_amount = Decimal(str(transaction['amount']))
                refund_amount = amount or original_amount
                
                if refund_amount > original_amount:
                    raise PaymentError(
                        "Refund amount exceeds original transaction",
                        error_code="INVALID_REFUND_AMOUNT"
                    )
                
                # Check existing refunds
                existing_refunds = await conn.fetchval("""
                    SELECT COALESCE(SUM(amount), 0)
                    FROM payment_refunds
                    WHERE transaction_id = $1 AND status = 'completed'
                """, transaction_id)
                
                if existing_refunds + refund_amount > original_amount:
                    raise PaymentError(
                        "Total refunds would exceed original amount",
                        error_code="REFUND_LIMIT_EXCEEDED"
                    )
            
            # Get the provider used for original transaction
            provider_type = transaction['provider']
            provider = await self.provider_factory.get_provider(
                str(tenant_id), provider_type
            )
            
            # Process refund
            refund_response = await provider.refund(
                transaction['provider_transaction_id'],
                refund_amount,
                reason
            )
            
            # Record refund
            refund_id = await self._record_refund(
                transaction_id=transaction_id,
                amount=refund_amount,
                reason=reason,
                status=refund_response.status,
                provider_refund_id=refund_response.provider_transaction_id
            )
            
            # Adjust fee split for partial refund
            if refund_amount < original_amount:
                await self._adjust_fee_split_for_refund(
                    transaction_id, refund_amount
                )
            
            result = {
                'refund_id': str(refund_id),
                'transaction_id': str(transaction_id),
                'amount': float(refund_amount),
                'status': refund_response.status.value,
                'reason': reason,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Cache for idempotency
            if idempotency_key:
                await self._cache_idempotency_result(
                    tenant_id, idempotency_key, result
                )
            
            # Log audit
            await self._log_audit(
                tenant_id=tenant_id,
                action='payment_refunded',
                entity_type='refund',
                entity_id=str(refund_id),
                details=result
            )
            
            return result
            
        except PaymentError:
            raise
        except Exception as e:
            self.logger.error(f"Refund processing failed: {str(e)}")
            raise PaymentError(
                "Refund processing failed",
                error_code="REFUND_ERROR",
                provider_error=str(e)
            )
    
    async def _get_provider_with_failover(
        self,
        tenant_id: UUID,
        preferred_type: Optional[str] = None
    ) -> Optional[BasePaymentProvider]:
        """Get provider with circuit breaker and failover logic"""
        
        # Check circuit breaker
        if preferred_type:
            breaker_key = f"{tenant_id}:{preferred_type}"
            if self._is_circuit_open(breaker_key):
                self.logger.warning(f"Circuit breaker open for {breaker_key}")
                preferred_type = None  # Force failover
        
        try:
            # Try to get preferred provider
            provider = await self.provider_factory.get_provider(
                str(tenant_id), preferred_type, prefer_primary=True
            )
            
            # Reset circuit breaker on success
            if preferred_type:
                self._reset_circuit_breaker(f"{tenant_id}:{preferred_type}")
            
            return provider
            
        except Exception as e:
            self.logger.error(f"Failed to get provider: {str(e)}")
            
            # Record circuit breaker failure
            if preferred_type:
                self._record_circuit_failure(f"{tenant_id}:{preferred_type}")
            
            # Try failover
            if preferred_type:
                return await self.provider_factory.get_failover_provider(
                    str(tenant_id), preferred_type
                )
            
            return None
    
    async def _process_with_retry(
        self,
        provider: BasePaymentProvider,
        request: PaymentRequest,
        max_retries: int = 3
    ) -> PaymentResponse:
        """Process payment with exponential backoff retry"""
        import asyncio
        
        last_error = None
        for attempt in range(max_retries):
            try:
                return await provider.charge(request)
            except PaymentError as e:
                last_error = e
                if e.error_code in ['NETWORK_ERROR', 'TIMEOUT']:
                    # Retryable error
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 1  # Exponential backoff
                        self.logger.warning(f"Retrying payment after {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                raise
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise
        
        raise PaymentError(
            "Payment failed after retries",
            error_code="MAX_RETRIES_EXCEEDED",
            provider_error=str(last_error)
        )
    
    async def _check_daily_limits(
        self,
        tenant_id: UUID,
        provider: BasePaymentProvider,
        amount: Decimal
    ):
        """Check if transaction exceeds daily limits"""
        if not hasattr(provider, 'daily_limit') or not provider.daily_limit:
            return
        
        async with self.db_pool.acquire() as conn:
            today_total = await conn.fetchval("""
                SELECT COALESCE(SUM(amount), 0)
                FROM payment_transactions
                WHERE tenant_id = $1
                AND DATE(created_at) = CURRENT_DATE
                AND status = 'completed'
            """, tenant_id)
            
            if today_total + amount > provider.daily_limit:
                raise PaymentError(
                    f"Daily transaction limit exceeded",
                    error_code="DAILY_LIMIT_EXCEEDED"
                )
    
    async def _get_payment_method(
        self,
        payment_method_id: UUID,
        tenant_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Retrieve payment method details"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM payment_methods
                WHERE id = $1 AND tenant_id = $2 AND is_active = true
            """, payment_method_id, tenant_id)
            
            if row:
                return dict(row)
            return None
    
    async def _record_transaction(
        self,
        tenant_id: UUID,
        store_id: Optional[UUID],
        provider: BasePaymentProvider,
        request: PaymentRequest,
        response: PaymentResponse,
        transaction_ref: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
        idempotency_key: Optional[str]
    ) -> UUID:
        """Record transaction in database"""
        transaction_id = uuid4()
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO payment_transactions (
                    id, transaction_reference, provider_transaction_id,
                    order_id, tenant_id, store_id, payment_method_id,
                    tenant_provider_id, provider, type, status,
                    amount, currency, tax_amount, provider_fee,
                    platform_fee, net_amount, provider_response,
                    error_code, error_message, ip_address, user_agent,
                    metadata, idempotency_key, created_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11,
                    $12, $13, $14, $15, $16, $17, $18, $19, $20,
                    $21, $22, $23, $24, CURRENT_TIMESTAMP
                )
            """, transaction_id, transaction_ref, response.provider_transaction_id,
                request.order_id, tenant_id, store_id, request.payment_method_id,
                provider.tenant_provider_id if hasattr(provider, 'tenant_provider_id') else None,
                provider.__class__.__name__.replace('Provider', '').lower(),
                'charge', response.status.value, request.amount, request.currency,
                0, 0, 0, request.amount, json.dumps(response.metadata or {}),
                response.error_code, response.error_message,
                ip_address, user_agent, json.dumps(request.metadata or {}),
                idempotency_key)
        
        return transaction_id
    
    async def _record_fee_split(
        self,
        transaction_id: UUID,
        tenant_id: UUID,
        provider: BasePaymentProvider,
        amount: Decimal
    ):
        """Record platform fee split"""
        platform_percentage = getattr(provider, 'platform_fee_percentage', 0.02)
        platform_fixed = getattr(provider, 'platform_fee_fixed', 0)
        
        platform_fee = (amount * Decimal(str(platform_percentage))) + Decimal(str(platform_fixed))
        tenant_net = amount - platform_fee
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO payment_fee_splits (
                    transaction_id, tenant_id, gross_amount,
                    platform_fee, platform_percentage_fee,
                    platform_fixed_fee, tenant_net_amount
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, transaction_id, tenant_id, amount, platform_fee,
                amount * Decimal(str(platform_percentage)),
                Decimal(str(platform_fixed)), tenant_net)
    
    async def _record_refund(
        self,
        transaction_id: UUID,
        amount: Decimal,
        reason: Optional[str],
        status: PaymentStatus,
        provider_refund_id: Optional[str]
    ) -> UUID:
        """Record refund in database"""
        refund_id = uuid4()
        
        async with self.db_pool.acquire() as conn:
            # Create refund transaction
            refund_txn_id = uuid4()
            await conn.execute("""
                INSERT INTO payment_transactions (
                    id, type, status, amount, provider_transaction_id
                ) VALUES ($1, 'refund', $2, $3, $4)
            """, refund_txn_id, status.value, amount, provider_refund_id)
            
            # Create refund record
            await conn.execute("""
                INSERT INTO payment_refunds (
                    id, transaction_id, refund_transaction_id,
                    amount, reason, status, provider_refund_id
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, refund_id, transaction_id, refund_txn_id,
                amount, reason, status.value, provider_refund_id)
        
        return refund_id
    
    async def _adjust_fee_split_for_refund(
        self,
        transaction_id: UUID,
        refund_amount: Decimal
    ):
        """Adjust fee split for partial refund"""
        async with self.db_pool.acquire() as conn:
            # Get original fee split
            fee_split = await conn.fetchrow("""
                SELECT * FROM payment_fee_splits
                WHERE transaction_id = $1
            """, transaction_id)
            
            if fee_split:
                # Calculate proportional fee adjustment
                refund_ratio = refund_amount / fee_split['gross_amount']
                platform_fee_refund = fee_split['platform_fee'] * refund_ratio
                
                # Update fee split
                await conn.execute("""
                    UPDATE payment_fee_splits
                    SET platform_fee = platform_fee - $1,
                        tenant_net_amount = tenant_net_amount - ($2 - $1)
                    WHERE transaction_id = $3
                """, platform_fee_refund, refund_amount, transaction_id)
    
    async def _check_idempotency(
        self,
        tenant_id: UUID,
        key: str,
        request_hash: str
    ) -> Optional[Dict[str, Any]]:
        """Check for idempotent request"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT response, request_hash, status
                FROM payment_idempotency_keys
                WHERE idempotency_key = $1 AND tenant_id = $2
                AND expires_at > CURRENT_TIMESTAMP
            """, key, tenant_id)
            
            if row:
                if row['request_hash'] != request_hash:
                    raise PaymentError(
                        "Idempotency key used with different request",
                        error_code="IDEMPOTENCY_MISMATCH"
                    )
                if row['status'] == 'completed':
                    return json.loads(row['response']) if row['response'] else None
            
            # Insert placeholder
            await conn.execute("""
                INSERT INTO payment_idempotency_keys (
                    idempotency_key, tenant_id, request_hash, status
                ) VALUES ($1, $2, $3, 'processing')
                ON CONFLICT (idempotency_key) DO NOTHING
            """, key, tenant_id, request_hash)
            
            return None
    
    async def _cache_idempotency_result(
        self,
        tenant_id: UUID,
        key: str,
        result: Dict[str, Any]
    ):
        """Cache idempotency result"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE payment_idempotency_keys
                SET response = $1, status = 'completed'
                WHERE idempotency_key = $2 AND tenant_id = $3
            """, json.dumps(result), key, tenant_id)
    
    def _hash_request(self, *args) -> str:
        """Generate hash of request parameters"""
        data = json.dumps(args, sort_keys=True, default=str)
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _is_circuit_open(self, key: str) -> bool:
        """Check if circuit breaker is open"""
        if key not in self._circuit_breakers:
            return False
        
        breaker = self._circuit_breakers[key]
        if breaker['failures'] >= self.circuit_breaker_threshold:
            if datetime.now(timezone.utc) - breaker['last_failure'] < self.circuit_breaker_timeout:
                return True
            else:
                # Reset after timeout
                self._circuit_breakers[key] = {'failures': 0, 'last_failure': None}
        
        return False
    
    def _record_circuit_failure(self, key: str):
        """Record circuit breaker failure"""
        if key not in self._circuit_breakers:
            self._circuit_breakers[key] = {'failures': 0, 'last_failure': None}
        
        self._circuit_breakers[key]['failures'] += 1
        self._circuit_breakers[key]['last_failure'] = datetime.now(timezone.utc)
    
    def _reset_circuit_breaker(self, key: str):
        """Reset circuit breaker"""
        if key in self._circuit_breakers:
            self._circuit_breakers[key] = {'failures': 0, 'last_failure': None}
    
    async def _log_audit(
        self,
        tenant_id: UUID,
        action: str,
        entity_type: str,
        entity_id: str,
        details: Dict[str, Any]
    ):
        """Log audit entry"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO payment_audit_log (
                    tenant_id, action, entity_type, entity_id,
                    details, created_at
                ) VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
            """, tenant_id, action, entity_type, entity_id, json.dumps(details))