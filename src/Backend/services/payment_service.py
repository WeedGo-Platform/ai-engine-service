"""
Payment Service - Main payment orchestration service
Manages payment providers and routes transactions
"""

from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from datetime import datetime, timezone
from uuid import UUID, uuid4
import asyncpg
import logging
import json
import importlib
from enum import Enum

from services.payment.base import (
    BasePaymentProvider, PaymentRequest, PaymentResponse,
    PaymentStatus, PaymentMethodType, TransactionType,
    PaymentError, PaymentMethod
)

# Import payment providers
from services.payment.moneris_provider import MonerisProvider
from services.payment.clover_provider import CloverProvider
from services.payment.interac_provider import InteracProvider

logger = logging.getLogger(__name__)


class PaymentService:
    """Main payment service that manages all payment providers"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.providers: Dict[str, BasePaymentProvider] = {}
        self.logger = logger
        
    async def initialize(self):
        """Initialize payment providers from database configuration"""
        async with self.db_pool.acquire() as conn:
            providers = await conn.fetch("""
                SELECT * FROM payment_providers 
                WHERE is_active = true
                ORDER BY is_default DESC, name
            """)
            
            for provider in providers:
                await self._load_provider(provider)
    
    async def _load_provider(self, provider_config: dict):
        """Dynamically load a payment provider"""
        provider_type = provider_config['provider_type']
        provider_name = provider_config['name']
        
        try:
            # Parse configuration from JSON
            config = provider_config.get('configuration', {})
            if isinstance(config, str):
                config = json.loads(config)
            
            # Map provider types to their implementation classes
            provider_classes = {
                'moneris': MonerisProvider,
                'clover': CloverProvider,
                'interac': InteracProvider
            }
            
            if provider_type in provider_classes:
                # Instantiate the provider with its configuration
                provider_class = provider_classes[provider_type]
                provider_instance = provider_class(config)
                
                self.providers[provider_type] = {
                    'config': provider_config,
                    'instance': provider_instance
                }
                logger.info(f"Loaded payment provider: {provider_name} ({provider_type})")
            else:
                logger.warning(f"Provider type {provider_type} not implemented yet")
        except Exception as e:
            logger.error(f"Failed to load provider {provider_name}: {e}")
    
    async def process_payment(
        self,
        amount: Decimal,
        currency: str = "CAD",
        payment_method_id: Optional[UUID] = None,
        order_id: Optional[UUID] = None,
        customer_id: Optional[UUID] = None,
        provider_type: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        store_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Process a payment transaction"""
        
        transaction_ref = f"TXN-{uuid4().hex[:12].upper()}"
        
        async with self.db_pool.acquire() as conn:
            try:
                # Get payment method details if provided
                payment_method = None
                if payment_method_id:
                    payment_method = await conn.fetchrow("""
                        SELECT pm.*, pp.provider_type, pp.configuration
                        FROM payment_methods pm
                        JOIN payment_providers pp ON pm.provider_id = pp.id
                        WHERE pm.id = $1 AND pm.is_active = true
                    """, payment_method_id)
                    
                    if not payment_method:
                        raise PaymentError("Payment method not found or inactive")
                    
                    provider_type = payment_method['provider_type']
                
                # Get default provider if not specified
                if not provider_type:
                    default_provider = await conn.fetchrow("""
                        SELECT provider_type FROM payment_providers 
                        WHERE is_active = true AND is_default = true
                    """)
                    if default_provider:
                        provider_type = default_provider['provider_type']
                    else:
                        provider_type = 'moneris'  # Fallback to Moneris
                
                # Create transaction record
                transaction = await conn.fetchrow("""
                    INSERT INTO payment_transactions (
                        transaction_reference, order_id, tenant_id, 
                        payment_method_id, provider_id, type, status,
                        amount, currency, ip_address, user_agent, metadata
                    ) VALUES (
                        $1, $2, $3, $4,
                        (SELECT id FROM payment_providers WHERE provider_type = $5),
                        $6, $7, $8, $9, $10, $11, $12
                    ) RETURNING *
                """, transaction_ref, order_id, customer_id, payment_method_id,
                    provider_type, 'charge', 'pending', amount, currency,
                    ip_address, user_agent, json.dumps(metadata or {}))
                
                # Get provider instance - use store-specific config if store_id provided
                provider: BasePaymentProvider = None

                if store_id:
                    # Try to get store-specific online payment configuration
                    store_config = await conn.fetchrow("""
                        SELECT settings->'onlinePayment' as online_payment
                        FROM stores
                        WHERE id = $1
                    """, store_id)

                    if store_config and store_config['online_payment']:
                        online_payment = store_config['online_payment']
                        if isinstance(online_payment, str):
                            online_payment = json.loads(online_payment)

                        if online_payment.get('enabled') and online_payment.get('access_token'):
                            # Create provider instance with store-specific config
                            store_provider_type = online_payment.get('provider', 'clover')
                            if store_provider_type == provider_type or not provider_type:
                                provider_type = store_provider_type

                                # Build provider config from store settings
                                provider_config = {
                                    'access_token': online_payment.get('access_token'),
                                    'merchant_id': online_payment.get('merchant_id'),
                                    'environment': online_payment.get('environment', 'sandbox'),
                                    'store_id': str(store_id)
                                }

                                # Instantiate provider with store config
                                if provider_type == 'clover':
                                    provider = CloverProvider(provider_config)
                                elif provider_type == 'moneris':
                                    provider = MonerisProvider(provider_config)
                                elif provider_type == 'interac':
                                    provider = InteracProvider(provider_config)

                                logger.info(f"Using store-specific {provider_type} config for store {store_id}")

                # Fall back to system-level provider if no store config
                if not provider:
                    provider_info = self.providers.get(provider_type)
                    if not provider_info or not provider_info['instance']:
                        raise PaymentError(f"Provider {provider_type} not available")

                    provider = provider_info['instance']
                    logger.info(f"Using system-level {provider_type} config")
                
                # Create payment request
                payment_request = PaymentRequest(
                    amount=amount,
                    currency=currency,
                    description=description,
                    order_id=order_id,
                    customer_id=customer_id,
                    payment_method_id=payment_method_id,
                    metadata=metadata,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                # Add payment method token if available
                if payment_method and payment_method['payment_token']:
                    payment_request.metadata = payment_request.metadata or {}
                    payment_request.metadata['payment_token'] = payment_method['payment_token']
                
                # Process payment through provider
                payment_response = await provider.charge(payment_request)
                
                # Prepare provider response
                provider_response = {
                    'provider_transaction_id': payment_response.provider_transaction_id,
                    'status': payment_response.status.value,
                    'authorization_code': payment_response.metadata.get('authorization_code'),
                    'response_code': payment_response.error_code or '00',
                    'response_message': payment_response.error_message or 'Approved'
                }
                
                # Update transaction with provider response
                final_status = payment_response.status.value
                await conn.execute("""
                    UPDATE payment_transactions 
                    SET status = $1, provider_transaction_id = $2, 
                        provider_response = $3, processed_at = $4,
                        completed_at = $5, error_code = $6, error_message = $7
                    WHERE id = $8
                """, final_status, provider_response['provider_transaction_id'],
                    json.dumps(provider_response), datetime.now(timezone.utc),
                    datetime.now(timezone.utc) if final_status == 'completed' else None,
                    payment_response.error_code, payment_response.error_message,
                    transaction['id'])
                
                success = payment_response.status == PaymentStatus.COMPLETED
                return {
                    'success': success,
                    'transaction_id': str(transaction['id']),
                    'transaction_reference': transaction_ref,
                    'provider_transaction_id': provider_response['provider_transaction_id'],
                    'status': payment_response.status.value,
                    'amount': float(amount),
                    'currency': currency,
                    'authorization_code': provider_response.get('authorization_code'),
                    'message': payment_response.error_message if not success else 'Payment processed successfully',
                    'error_code': payment_response.error_code if not success else None
                }
                
            except PaymentError as e:
                # Update transaction as failed
                if 'transaction' in locals():
                    await conn.execute("""
                        UPDATE payment_transactions 
                        SET status = 'failed', error_code = $1, 
                            error_message = $2, failed_at = $3
                        WHERE id = $4
                    """, e.error_code, e.message, datetime.now(timezone.utc),
                        transaction['id'])
                
                logger.error(f"Payment failed: {e}")
                return {
                    'success': False,
                    'error': e.message,
                    'error_code': e.error_code
                }
            
            except Exception as e:
                logger.error(f"Unexpected payment error: {e}")
                return {
                    'success': False,
                    'error': 'Payment processing failed',
                    'error_code': 'SYSTEM_ERROR'
                }
    
    async def refund_transaction(
        self,
        transaction_id: UUID,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None,
        initiated_by: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Process a refund for a transaction"""
        
        async with self.db_pool.acquire() as conn:
            try:
                # Get original transaction
                transaction = await conn.fetchrow("""
                    SELECT t.*, pp.provider_type 
                    FROM payment_transactions t
                    JOIN payment_providers pp ON t.provider_id = pp.id
                    WHERE t.id = $1 AND t.status = 'completed'
                """, transaction_id)
                
                if not transaction:
                    raise PaymentError("Transaction not found or not eligible for refund")
                
                refund_amount = amount or transaction['amount']
                
                # Check if refund amount is valid
                if refund_amount > transaction['amount']:
                    raise PaymentError("Refund amount cannot exceed original transaction amount")
                
                # Check existing refunds
                existing_refunds = await conn.fetchval("""
                    SELECT COALESCE(SUM(amount), 0) 
                    FROM payment_refunds 
                    WHERE transaction_id = $1 AND status = 'completed'
                """, transaction_id)
                
                if existing_refunds + refund_amount > transaction['amount']:
                    raise PaymentError("Total refunds would exceed original transaction amount")
                
                # Create refund record
                refund = await conn.fetchrow("""
                    INSERT INTO payment_refunds (
                        transaction_id, amount, reason, status, initiated_by
                    ) VALUES ($1, $2, $3, $4, $5)
                    RETURNING *
                """, transaction_id, refund_amount, reason, 'pending', initiated_by)
                
                # Get provider instance
                provider_type = transaction['provider_type']
                provider_info = self.providers.get(provider_type)
                if not provider_info or not provider_info['instance']:
                    raise PaymentError(f"Provider {provider_type} not available")
                
                provider: BasePaymentProvider = provider_info['instance']
                
                # Process refund through provider
                refund_response = await provider.refund(
                    transaction_id=str(transaction_id),
                    amount=refund_amount,
                    reason=reason
                )
                
                provider_response = {
                    'refund_id': refund_response.provider_transaction_id,
                    'status': refund_response.status.value
                }
                
                # Create refund transaction
                refund_txn = await conn.fetchrow("""
                    INSERT INTO payment_transactions (
                        transaction_reference, order_id, tenant_id,
                        provider_id, type, status, amount, currency,
                        provider_transaction_id, metadata
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
                    ) RETURNING *
                """, f"REF-{uuid4().hex[:12].upper()}", transaction['order_id'],
                    transaction['tenant_id'], transaction['provider_id'],
                    'refund' if refund_amount == transaction['amount'] else 'partial_refund',
                    'completed', refund_amount, transaction['currency'],
                    provider_response['refund_id'],
                    json.dumps({'original_transaction_id': str(transaction_id)}))
                
                # Update refund record
                await conn.execute("""
                    UPDATE payment_refunds 
                    SET status = 'completed', refund_transaction_id = $1,
                        provider_refund_id = $2, processed_at = $3, completed_at = $4
                    WHERE id = $5
                """, refund_txn['id'], provider_response['refund_id'],
                    datetime.now(timezone.utc), datetime.now(timezone.utc), refund['id'])
                
                # Update original transaction status if fully refunded
                if refund_amount == transaction['amount']:
                    await conn.execute("""
                        UPDATE payment_transactions 
                        SET status = 'refunded' 
                        WHERE id = $1
                    """, transaction_id)
                
                return {
                    'success': True,
                    'refund_id': str(refund['id']),
                    'refund_transaction_id': str(refund_txn['id']),
                    'amount': float(refund_amount),
                    'status': 'completed',
                    'message': 'Refund processed successfully'
                }
                
            except PaymentError as e:
                logger.error(f"Refund failed: {e}")
                return {
                    'success': False,
                    'error': e.message,
                    'error_code': e.error_code
                }
    
    async def save_payment_method(
        self,
        customer_id: UUID,
        payment_data: Dict[str, Any],
        provider_type: str = 'moneris',
        set_as_default: bool = False
    ) -> Dict[str, Any]:
        """Save a payment method for future use"""
        
        async with self.db_pool.acquire() as conn:
            try:
                # Get provider
                provider = await conn.fetchrow("""
                    SELECT * FROM payment_providers 
                    WHERE provider_type = $1 AND is_active = true
                """, provider_type)
                
                if not provider:
                    raise PaymentError(f"Payment provider {provider_type} not available")
                
                # TODO: Tokenize with actual provider
                # For now, create a mock token
                token = f"TOK-{uuid4().hex[:16].upper()}"
                
                # Extract card details for display
                card_brand = payment_data.get('card_brand', 'visa')
                card_last_four = payment_data.get('card_number', '4242')[-4:]
                exp_month = payment_data.get('exp_month', 12)
                exp_year = payment_data.get('exp_year', 2025)
                
                display_name = f"{card_brand.title()} ending in {card_last_four}"
                
                # If setting as default, unset other defaults
                if set_as_default:
                    await conn.execute("""
                        UPDATE payment_methods 
                        SET is_default = false 
                        WHERE tenant_id = $1
                    """, customer_id)
                
                # Save payment method
                payment_method = await conn.fetchrow("""
                    INSERT INTO payment_methods (
                        tenant_id, provider_id, type, payment_token,
                        display_name, card_brand, card_last_four,
                        card_exp_month, card_exp_year, is_default,
                        billing_address, metadata
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
                    ) RETURNING *
                """, customer_id, provider['id'], 'card', token, display_name,
                    card_brand, card_last_four, exp_month, exp_year,
                    set_as_default, json.dumps(payment_data.get('billing_address', {})),
                    json.dumps({'masked_number': f"****-****-****-{card_last_four}"}))
                
                return {
                    'success': True,
                    'payment_method_id': str(payment_method['id']),
                    'display_name': display_name,
                    'card_brand': card_brand,
                    'card_last_four': card_last_four,
                    'is_default': set_as_default
                }
                
            except Exception as e:
                logger.error(f"Failed to save payment method: {e}")
                return {
                    'success': False,
                    'error': 'Failed to save payment method'
                }
    
    async def get_payment_methods(
        self,
        customer_id: UUID
    ) -> List[Dict[str, Any]]:
        """Get all payment methods for a customer"""
        
        async with self.db_pool.acquire() as conn:
            methods = await conn.fetch("""
                SELECT pm.*, pp.name as provider_name, pp.provider_type
                FROM payment_methods pm
                JOIN payment_providers pp ON pm.provider_id = pp.id
                WHERE pm.tenant_id = $1 AND pm.is_active = true
                ORDER BY pm.is_default DESC, pm.created_at DESC
            """, customer_id)
            
            return [
                {
                    'id': str(m['id']),
                    'type': m['type'],
                    'display_name': m['display_name'],
                    'card_brand': m['card_brand'],
                    'card_last_four': m['card_last_four'],
                    'exp_month': m['card_exp_month'],
                    'exp_year': m['card_exp_year'],
                    'is_default': m['is_default'],
                    'provider': m['provider_name']
                }
                for m in methods
            ]
    
    async def delete_payment_method(
        self,
        payment_method_id: UUID,
        customer_id: UUID
    ) -> bool:
        """Delete a payment method"""
        
        async with self.db_pool.acquire() as conn:
            # Soft delete the payment method
            result = await conn.execute("""
                UPDATE payment_methods 
                SET is_active = false, updated_at = $1
                WHERE id = $2 AND tenant_id = $3
            """, datetime.now(timezone.utc), payment_method_id, customer_id)
            
            return result.split()[-1] == '1'
    
    async def get_transaction_history(
        self,
        customer_id: Optional[UUID] = None,
        order_id: Optional[UUID] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get transaction history"""
        
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT t.*, pp.name as provider_name,
                       o.order_number, o.total_amount as order_total
                FROM payment_transactions t
                JOIN payment_providers pp ON t.provider_id = pp.id
                LEFT JOIN orders o ON t.order_id = o.id
                WHERE 1=1
            """
            params = []
            param_count = 0
            
            if customer_id:
                param_count += 1
                query += f" AND t.tenant_id = ${param_count}"
                params.append(customer_id)
            
            if order_id:
                param_count += 1
                query += f" AND t.order_id = ${param_count}"
                params.append(order_id)
            
            query += f" ORDER BY t.created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
            params.extend([limit, offset])
            
            transactions = await conn.fetch(query, *params)
            
            return [
                {
                    'id': str(t['id']),
                    'reference': t['transaction_reference'],
                    'type': t['type'],
                    'status': t['status'],
                    'amount': float(t['amount']),
                    'currency': t['currency'],
                    'provider': t['provider_name'],
                    'order_number': t['order_number'],
                    'created_at': t['created_at'].isoformat() if t['created_at'] else None,
                    'completed_at': t['completed_at'].isoformat() if t['completed_at'] else None
                }
                for t in transactions
            ]
    
    async def get_payment_analytics(
        self,
        start_date: datetime,
        end_date: datetime,
        provider_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get payment analytics for a date range"""
        
        async with self.db_pool.acquire() as conn:
            base_query = """
                SELECT 
                    COUNT(*) as total_transactions,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                    SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END) as total_amount,
                    SUM(CASE WHEN type = 'refund' THEN amount ELSE 0 END) as total_refunds,
                    AVG(CASE WHEN status = 'completed' THEN amount END) as avg_transaction
                FROM payment_transactions
                WHERE created_at BETWEEN $1 AND $2
            """
            
            params = [start_date, end_date]
            
            if provider_type:
                base_query += " AND provider_id = (SELECT id FROM payment_providers WHERE provider_type = $3)"
                params.append(provider_type)
            
            stats = await conn.fetchrow(base_query, *params)
            
            return {
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'metrics': {
                    'total_transactions': stats['total_transactions'] or 0,
                    'successful_transactions': stats['successful'] or 0,
                    'failed_transactions': stats['failed'] or 0,
                    'success_rate': (
                        (stats['successful'] / stats['total_transactions'] * 100)
                        if stats['total_transactions'] > 0 else 0
                    ),
                    'total_amount': float(stats['total_amount'] or 0),
                    'total_refunds': float(stats['total_refunds'] or 0),
                    'net_amount': float((stats['total_amount'] or 0) - (stats['total_refunds'] or 0)),
                    'average_transaction': float(stats['avg_transaction'] or 0)
                }
            }