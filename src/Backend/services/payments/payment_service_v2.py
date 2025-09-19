"""
Payment Service V2
Enhanced payment service that uses store-level payment provider configuration
"""

import os
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
import uuid
import asyncpg

# Import payment providers
from services.payment.clover_provider import CloverProvider
from services.payment.moneris_provider import MonerisProvider
from services.payment.interac_provider import InteracProvider
from services.payment.base import PaymentRequest, PaymentError

logger = logging.getLogger(__name__)


class PaymentServiceV2:
    """
    Payment service for processing transactions with store-level configuration
    """

    def __init__(self, db_pool: asyncpg.Pool):
        """Initialize payment service with database pool"""
        self.db_pool = db_pool
        logger.info("PaymentServiceV2 initialized with store-level support")

    async def get_store_payment_provider(
        self,
        store_id: str,
        provider_type: Optional[str] = None
    ) -> Optional[Any]:
        """
        Get payment provider configured for a specific store

        Args:
            store_id: Store ID
            provider_type: Optional specific provider type to use

        Returns:
            Configured payment provider instance or None
        """
        async with self.db_pool.acquire() as conn:
            # Get store's online payment configuration
            store_config = await conn.fetchrow("""
                SELECT settings->'onlinePayment' as online_payment
                FROM stores
                WHERE id = $1
            """, uuid.UUID(store_id))

            if not store_config or not store_config['online_payment']:
                logger.warning(f"No online payment configuration for store {store_id}")
                return None

            online_payment = store_config['online_payment']
            if isinstance(online_payment, str):
                online_payment = json.loads(online_payment)

            if not online_payment.get('enabled'):
                logger.warning(f"Online payment disabled for store {store_id}")
                return None

            if not online_payment.get('access_token'):
                logger.warning(f"No access token configured for store {store_id}")
                return None

            # Use specified provider or store's configured provider
            configured_provider = online_payment.get('provider', 'clover')
            if provider_type and provider_type != configured_provider:
                logger.warning(f"Requested provider {provider_type} does not match store's provider {configured_provider}")
                return None

            provider_type = configured_provider

            # Build provider configuration
            provider_config = {
                'access_token': online_payment.get('access_token'),
                'merchant_id': online_payment.get('merchant_id'),
                'environment': online_payment.get('environment', 'sandbox'),
                'store_id': str(store_id)
            }

            # Instantiate the appropriate provider
            if provider_type == 'clover':
                return CloverProvider(provider_config)
            elif provider_type == 'moneris':
                # Add Moneris-specific config if needed
                provider_config['store_id'] = online_payment.get('moneris_store_id', provider_config['store_id'])
                provider_config['api_token'] = online_payment.get('api_token', provider_config['access_token'])
                return MonerisProvider(provider_config)
            elif provider_type == 'interac':
                return InteracProvider(provider_config)
            else:
                logger.error(f"Unknown provider type: {provider_type}")
                return None

    async def process_payment(
        self,
        tenant_id: str,
        amount: float,
        currency: str = 'CAD',
        payment_method: str = 'card',
        metadata: Optional[Dict[str, Any]] = None,
        store_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a payment using store-specific configuration

        Args:
            tenant_id: Tenant ID
            amount: Amount to charge
            currency: Currency code (default: CAD)
            payment_method: Payment method type
            metadata: Additional metadata for the payment
            store_id: Store ID for store-specific configuration

        Returns:
            Payment processing result
        """
        try:
            # Get store ID from metadata if not provided
            if not store_id and metadata and 'store_id' in metadata:
                store_id = metadata['store_id']

            # Get store from cart session if available
            if not store_id and metadata and 'cart_session_id' in metadata:
                async with self.db_pool.acquire() as conn:
                    cart = await conn.fetchrow("""
                        SELECT store_id FROM cart_sessions
                        WHERE id = $1
                    """, uuid.UUID(metadata['cart_session_id']))
                    if cart:
                        store_id = str(cart['store_id'])

            if not store_id:
                # Try to get default store for tenant
                async with self.db_pool.acquire() as conn:
                    default_store = await conn.fetchrow("""
                        SELECT id FROM stores
                        WHERE tenant_id = $1
                        ORDER BY created_at
                        LIMIT 1
                    """, uuid.UUID(tenant_id))
                    if default_store:
                        store_id = str(default_store['id'])

            if not store_id:
                logger.error("No store ID available for payment processing")
                return {
                    'success': False,
                    'error': 'Store configuration not found',
                    'error_code': 'STORE_NOT_FOUND'
                }

            # Get store-specific payment provider
            provider = await self.get_store_payment_provider(store_id)

            if not provider:
                logger.error(f"No payment provider configured for store {store_id}")

                # Fallback to mock payment for development
                if os.getenv('ENVIRONMENT', 'development') == 'development':
                    logger.warning("Using mock payment in development mode")
                    return await self._mock_payment(amount, currency, payment_method, metadata)

                return {
                    'success': False,
                    'error': 'Payment provider not configured for this store',
                    'error_code': 'PROVIDER_NOT_CONFIGURED'
                }

            # Create payment request
            payment_request = PaymentRequest(
                amount=Decimal(str(amount)),
                currency=currency,
                description=f"Order payment for store {store_id}",
                metadata=metadata or {}
            )

            # Process payment through provider
            logger.info(f"Processing payment for store {store_id} using {provider.__class__.__name__}")
            payment_response = await provider.charge(payment_request)

            # Format response
            return {
                'success': payment_response.status.value == 'completed',
                'transaction_id': payment_response.provider_transaction_id,
                'status': payment_response.status.value,
                'amount': float(amount),
                'currency': currency,
                'provider': provider.__class__.__name__.replace('Provider', '').lower(),
                'message': payment_response.error_message or 'Payment processed successfully',
                'error_code': payment_response.error_code
            }

        except PaymentError as e:
            logger.error(f"Payment error: {e}")
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

    async def _mock_payment(
        self,
        amount: float,
        currency: str,
        payment_method: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Mock payment for development/testing"""
        return {
            'success': True,
            'transaction_id': f'mock_txn_{uuid.uuid4().hex[:12]}',
            'status': 'completed',
            'amount': amount,
            'currency': currency,
            'provider': 'mock',
            'message': 'Mock payment successful (development mode)',
            'error_code': None
        }

    async def create_payment_intent(
        self,
        amount: float,
        currency: str = 'CAD',
        metadata: Optional[Dict[str, Any]] = None,
        store_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a payment intent for processing payment

        Args:
            amount: Amount to charge
            currency: Currency code (default: CAD)
            metadata: Additional metadata for the payment
            store_id: Store ID for store-specific configuration

        Returns:
            Payment intent details
        """
        try:
            if store_id:
                provider = await self.get_store_payment_provider(store_id)
                if provider and hasattr(provider, 'create_payment_intent'):
                    return await provider.create_payment_intent(
                        amount=Decimal(str(amount)),
                        currency=currency,
                        metadata=metadata
                    )

            # Fallback to mock intent
            payment_intent = {
                'id': f'pi_{uuid.uuid4().hex[:24]}',
                'amount': int(amount * 100),  # Convert to cents
                'currency': currency,
                'status': 'requires_payment_method',
                'client_secret': f'pi_{uuid.uuid4().hex[:24]}_secret_{uuid.uuid4().hex[:16]}',
                'created': datetime.utcnow().isoformat(),
                'metadata': metadata or {}
            }

            logger.info(f"Created payment intent: {payment_intent['id']}")
            return payment_intent

        except Exception as e:
            logger.error(f"Error creating payment intent: {e}")
            raise

    async def confirm_payment(
        self,
        payment_intent_id: str,
        payment_method: str,
        store_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Confirm a payment with the provided payment method

        Args:
            payment_intent_id: ID of the payment intent
            payment_method: Payment method to use
            store_id: Store ID for store-specific configuration

        Returns:
            Payment confirmation details
        """
        try:
            if store_id:
                provider = await self.get_store_payment_provider(store_id)
                if provider and hasattr(provider, 'confirm_payment'):
                    return await provider.confirm_payment(
                        payment_intent_id=payment_intent_id,
                        payment_method=payment_method
                    )

            # Fallback to mock confirmation
            result = {
                'id': payment_intent_id,
                'status': 'succeeded',
                'payment_method': payment_method,
                'confirmed_at': datetime.utcnow().isoformat()
            }

            logger.info(f"Payment confirmed: {payment_intent_id}")
            return result

        except Exception as e:
            logger.error(f"Error confirming payment: {e}")
            raise

    async def refund_payment(
        self,
        payment_intent_id: str,
        amount: Optional[float] = None,
        reason: Optional[str] = None,
        store_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Refund a payment

        Args:
            payment_intent_id: ID of the payment to refund
            amount: Amount to refund (None for full refund)
            reason: Reason for refund
            store_id: Store ID for store-specific configuration

        Returns:
            Refund details
        """
        try:
            if store_id:
                provider = await self.get_store_payment_provider(store_id)
                if provider and hasattr(provider, 'refund'):
                    return await provider.refund(
                        transaction_id=payment_intent_id,
                        amount=Decimal(str(amount)) if amount else None,
                        reason=reason
                    )

            # Fallback to mock refund
            refund = {
                'id': f'rf_{uuid.uuid4().hex[:24]}',
                'payment_intent': payment_intent_id,
                'amount': amount,
                'status': 'succeeded',
                'reason': reason or 'requested_by_customer',
                'created': datetime.utcnow().isoformat()
            }

            logger.info(f"Refund processed: {refund['id']}")
            return refund

        except Exception as e:
            logger.error(f"Error processing refund: {e}")
            raise

    async def validate_payment_method(
        self,
        payment_method: str
    ) -> bool:
        """
        Validate if a payment method is acceptable

        Args:
            payment_method: Payment method to validate

        Returns:
            True if valid, False otherwise
        """
        valid_methods = ['card', 'cash', 'debit', 'credit', 'apple_pay', 'google_pay']
        return payment_method.lower() in valid_methods