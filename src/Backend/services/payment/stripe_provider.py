"""
Stripe Payment Provider Implementation
Comprehensive Stripe integration for payments and subscriptions
"""

import aiohttp
import json
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from datetime import datetime
from uuid import UUID
import logging
import hmac
import hashlib
from enum import Enum

from services.payment.base import (
    BasePaymentProvider, PaymentRequest, PaymentResponse,
    PaymentStatus, PaymentError
)

logger = logging.getLogger(__name__)


class StripeEnvironment(Enum):
    TEST = "https://api.stripe.com/v1"
    PRODUCTION = "https://api.stripe.com/v1"


class StripeProvider(BasePaymentProvider):
    """Stripe payment provider implementation with subscription support"""
    
    def __init__(self, provider_config: Dict[str, Any]):
        super().__init__(provider_config)
        self.api_key = provider_config.get('api_key')  # Secret key (sk_test_... or sk_live_...)
        self.publishable_key = provider_config.get('publishable_key')  # Public key for frontend
        self.webhook_secret = provider_config.get('webhook_secret')  # Webhook signing secret
        self.api_version = provider_config.get('api_version', '2023-10-16')
        self.base_url = StripeEnvironment.PRODUCTION.value
        self.timeout = provider_config.get('timeout', 30)
        self.session = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with connection pooling"""
        if not self.session:
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                ttl_dns_cache=300
            )
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Stripe-Version': self.api_version
                }
            )
        return self.session
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _encode_params(self, params: Dict[str, Any], prefix: str = '') -> str:
        """Encode nested parameters for Stripe's form-encoded format"""
        encoded = []
        for key, value in params.items():
            full_key = f"{prefix}[{key}]" if prefix else key
            
            if isinstance(value, dict):
                encoded.append(self._encode_params(value, full_key))
            elif isinstance(value, list):
                for item in value:
                    encoded.append(f"{full_key}[]={item}")
            elif value is not None:
                encoded.append(f"{full_key}={value}")
        
        return '&'.join(encoded)
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to Stripe API"""
        session = await self._get_session()
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method == 'GET':
                async with session.get(url, params=params) as response:
                    return await self._handle_response(response)
            elif method == 'POST':
                encoded_data = self._encode_params(data) if data else ''
                async with session.post(url, data=encoded_data) as response:
                    return await self._handle_response(response)
            elif method == 'DELETE':
                async with session.delete(url) as response:
                    return await self._handle_response(response)
        except aiohttp.ClientError as e:
            logger.error(f"Stripe API request failed: {str(e)}")
            raise PaymentError(f"Payment provider communication error: {str(e)}", error_code="NETWORK_ERROR")
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Handle Stripe API response"""
        response_text = await response.text()
        
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response from Stripe: {response_text}")
            raise PaymentError("Invalid response from payment provider", error_code="INVALID_RESPONSE")
        
        if response.status >= 400:
            error = data.get('error', {})
            error_message = error.get('message', 'Unknown error')
            error_code = error.get('code', 'UNKNOWN_ERROR')
            error_type = error.get('type', 'api_error')
            
            logger.error(f"Stripe API error: {error_type} - {error_message} ({error_code})")
            raise PaymentError(
                error_message,
                error_code=error_code,
                provider_error=error_type
            )
        
        return data
    
    # ===========================================
    # Payment Processing Methods
    # ===========================================
    
    async def charge(
        self,
        amount: float,
        currency: str = "CAD",
        payment_method_token: str = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a payment charge using Stripe Payment Intents.
        
        Args:
            amount: Payment amount in dollars (will be converted to cents)
            currency: Currency code (default: CAD)
            payment_method_token: Stripe payment method ID (pm_...)
            metadata: Additional metadata
        
        Returns:
            Dict with transaction_id, status, and provider response
        """
        amount_cents = int(Decimal(str(amount)) * 100)
        
        data = {
            'amount': amount_cents,
            'currency': currency.lower(),
            'payment_method': payment_method_token,
            'confirm': True,  # Automatically confirm the payment
            'metadata': metadata or {}
        }
        
        try:
            response = await self._make_request('POST', 'payment_intents', data=data)
            
            # Map Stripe status to our PaymentStatus
            stripe_status = response.get('status')
            status_map = {
                'succeeded': PaymentStatus.COMPLETED,
                'processing': PaymentStatus.PROCESSING,
                'requires_payment_method': PaymentStatus.FAILED,
                'requires_confirmation': PaymentStatus.PENDING,
                'requires_action': PaymentStatus.PENDING,
                'canceled': PaymentStatus.CANCELLED
            }
            
            status = status_map.get(stripe_status, PaymentStatus.PENDING)
            
            return {
                'transaction_id': response['id'],
                'status': status.value,
                'amount': amount,
                'currency': currency,
                'provider_transaction_id': response['id'],
                'provider_response': response,
                'created_at': datetime.fromtimestamp(response['created'])
            }
        except PaymentError as e:
            logger.error(f"Stripe charge failed: {e.message}")
            return {
                'transaction_id': None,
                'status': PaymentStatus.FAILED.value,
                'amount': amount,
                'currency': currency,
                'error_code': e.error_code,
                'error_message': e.message
            }
    
    async def refund(
        self,
        transaction_id: str,
        amount: float,
        currency: str = "CAD",
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a refund (full or partial).
        
        Args:
            transaction_id: Stripe payment intent ID
            amount: Refund amount in dollars
            currency: Currency code
            reason: Reason for refund
        
        Returns:
            Dict with refund_id, status, and provider response
        """
        amount_cents = int(Decimal(str(amount)) * 100)
        
        data = {
            'payment_intent': transaction_id,
            'amount': amount_cents
        }
        
        if reason:
            data['metadata'] = {'reason': reason}
        
        try:
            response = await self._make_request('POST', 'refunds', data=data)
            
            status = PaymentStatus.REFUNDED if response['status'] == 'succeeded' else PaymentStatus.PENDING
            
            return {
                'refund_id': response['id'],
                'status': status.value,
                'amount': amount,
                'currency': currency,
                'provider_response': response
            }
        except PaymentError as e:
            logger.error(f"Stripe refund failed: {e.message}")
            return {
                'refund_id': None,
                'status': PaymentStatus.FAILED.value,
                'error_code': e.error_code,
                'error_message': e.message
            }
    
    async def void(self, transaction_id: str) -> PaymentResponse:
        """
        Void/cancel a payment intent.
        
        Args:
            transaction_id: Stripe payment intent ID
        
        Returns:
            PaymentResponse with cancellation status
        """
        try:
            response = await self._make_request('POST', f'payment_intents/{transaction_id}/cancel')
            
            return PaymentResponse(
                transaction_id=response['id'],
                status=PaymentStatus.CANCELLED,
                amount=Decimal(response['amount']) / 100,
                currency=response['currency'].upper(),
                provider_transaction_id=response['id'],
                metadata=response.get('metadata', {})
            )
        except PaymentError as e:
            logger.error(f"Stripe void failed: {e.message}")
            raise
    
    async def get_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """
        Get payment intent details.
        
        Args:
            transaction_id: Stripe payment intent ID
        
        Returns:
            Dict with transaction details
        """
        response = await self._make_request('GET', f'payment_intents/{transaction_id}')
        
        return {
            'transaction_id': response['id'],
            'status': response['status'],
            'amount': Decimal(response['amount']) / 100,
            'currency': response['currency'].upper(),
            'created_at': datetime.fromtimestamp(response['created']),
            'metadata': response.get('metadata', {}),
            'provider_response': response
        }
    
    # ===========================================
    # Payment Method Management
    # ===========================================
    
    async def tokenize_payment_method(
        self,
        payment_data: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Create a Stripe payment method from card details.
        This is typically done on the frontend using Stripe Elements,
        but this method is available for server-side tokenization.
        
        Args:
            payment_data: Dict with card details (number, exp_month, exp_year, cvc)
        
        Returns:
            Tuple of (payment_method_id, payment_method_details)
        """
        data = {
            'type': 'card',
            'card': {
                'number': payment_data.get('card_number'),
                'exp_month': payment_data.get('exp_month'),
                'exp_year': payment_data.get('exp_year'),
                'cvc': payment_data.get('cvc')
            }
        }
        
        if payment_data.get('billing_address'):
            data['billing_details'] = {'address': payment_data['billing_address']}
        
        response = await self._make_request('POST', 'payment_methods', data=data)
        
        card_details = response.get('card', {})
        metadata = {
            'brand': card_details.get('brand'),
            'last4': card_details.get('last4'),
            'exp_month': card_details.get('exp_month'),
            'exp_year': card_details.get('exp_year'),
            'country': card_details.get('country')
        }
        
        return response['id'], metadata
    
    async def attach_payment_method_to_customer(
        self,
        payment_method_id: str,
        customer_id: str
    ) -> Dict[str, Any]:
        """
        Attach a payment method to a Stripe customer.
        
        Args:
            payment_method_id: Stripe payment method ID
            customer_id: Stripe customer ID
        
        Returns:
            Dict with attachment details
        """
        data = {'customer': customer_id}
        response = await self._make_request(
            'POST',
            f'payment_methods/{payment_method_id}/attach',
            data=data
        )
        return response
    
    async def delete_payment_method(self, token: str) -> bool:
        """
        Detach/delete a payment method.
        
        Args:
            token: Stripe payment method ID
        
        Returns:
            True if successful
        """
        try:
            await self._make_request('POST', f'payment_methods/{token}/detach')
            return True
        except PaymentError:
            return False
    
    # ===========================================
    # Customer Management
    # ===========================================
    
    async def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        payment_method_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe customer.
        
        Args:
            email: Customer email
            name: Customer name
            metadata: Additional metadata (e.g., tenant_id, internal_customer_id)
            payment_method_id: Optional payment method to attach
        
        Returns:
            Dict with customer_id and customer details
        """
        data = {
            'email': email,
            'metadata': metadata or {}
        }
        
        if name:
            data['name'] = name
        
        if payment_method_id:
            data['payment_method'] = payment_method_id
            data['invoice_settings'] = {
                'default_payment_method': payment_method_id
            }
        
        response = await self._make_request('POST', 'customers', data=data)
        
        return {
            'customer_id': response['id'],
            'email': response['email'],
            'name': response.get('name'),
            'created_at': datetime.fromtimestamp(response['created']),
            'metadata': response.get('metadata', {}),
            'provider_response': response
        }
    
    async def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """Get Stripe customer details"""
        response = await self._make_request('GET', f'customers/{customer_id}')
        
        return {
            'customer_id': response['id'],
            'email': response['email'],
            'name': response.get('name'),
            'metadata': response.get('metadata', {}),
            'default_payment_method': response.get('invoice_settings', {}).get('default_payment_method'),
            'provider_response': response
        }
    
    async def update_customer(
        self,
        customer_id: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update Stripe customer details"""
        data = {}
        if email:
            data['email'] = email
        if name:
            data['name'] = name
        if metadata:
            data['metadata'] = metadata
        
        response = await self._make_request('POST', f'customers/{customer_id}', data=data)
        return response
    
    # ===========================================
    # Subscription Management (Core Feature)
    # ===========================================
    
    async def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        trial_period_days: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        payment_method_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a recurring subscription for a customer.
        
        Args:
            customer_id: Stripe customer ID (cus_...)
            price_id: Stripe price ID (price_...) - defines the plan and billing frequency
            trial_period_days: Number of days for trial period (e.g., 14)
            metadata: Additional metadata (tenant_id, subscription_tier, etc.)
            payment_method_id: Payment method to use (if not customer's default)
        
        Returns:
            Dict with subscription_id, status, current_period_end, etc.
        """
        data = {
            'customer': customer_id,
            'items': [{'price': price_id}],
            'metadata': metadata or {}
        }
        
        if trial_period_days:
            data['trial_period_days'] = trial_period_days
        
        if payment_method_id:
            data['default_payment_method'] = payment_method_id
        
        # Enable automatic tax calculation if configured
        data['automatic_tax'] = {'enabled': True}
        
        # Payment behavior: default is to charge automatically
        data['payment_behavior'] = 'default_incomplete'
        
        response = await self._make_request('POST', 'subscriptions', data=data)
        
        return {
            'subscription_id': response['id'],
            'customer_id': response['customer'],
            'status': response['status'],  # trialing, active, past_due, canceled, etc.
            'current_period_start': datetime.fromtimestamp(response['current_period_start']),
            'current_period_end': datetime.fromtimestamp(response['current_period_end']),
            'trial_end': datetime.fromtimestamp(response['trial_end']) if response.get('trial_end') else None,
            'cancel_at_period_end': response['cancel_at_period_end'],
            'metadata': response.get('metadata', {}),
            'provider_response': response
        }
    
    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Get subscription details.
        
        Args:
            subscription_id: Stripe subscription ID
        
        Returns:
            Dict with subscription details
        """
        response = await self._make_request('GET', f'subscriptions/{subscription_id}')
        
        return {
            'subscription_id': response['id'],
            'customer_id': response['customer'],
            'status': response['status'],
            'current_period_start': datetime.fromtimestamp(response['current_period_start']),
            'current_period_end': datetime.fromtimestamp(response['current_period_end']),
            'trial_end': datetime.fromtimestamp(response['trial_end']) if response.get('trial_end') else None,
            'cancel_at_period_end': response['cancel_at_period_end'],
            'metadata': response.get('metadata', {}),
            'provider_response': response
        }
    
    async def update_subscription(
        self,
        subscription_id: str,
        new_price_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        cancel_at_period_end: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Update an existing subscription (e.g., upgrade/downgrade plan).
        
        Args:
            subscription_id: Stripe subscription ID
            new_price_id: New price ID to switch to (for plan changes)
            metadata: Updated metadata
            cancel_at_period_end: Whether to cancel at the end of the current period
        
        Returns:
            Dict with updated subscription details
        """
        data = {}
        
        if new_price_id:
            # Get current subscription items to update
            current_sub = await self.get_subscription(subscription_id)
            current_items = current_sub['provider_response']['items']['data']
            
            data['items'] = [{
                'id': current_items[0]['id'],
                'price': new_price_id
            }]
            
            # Prorate by default for upgrades
            data['proration_behavior'] = 'create_prorations'
        
        if metadata:
            data['metadata'] = metadata
        
        if cancel_at_period_end is not None:
            data['cancel_at_period_end'] = cancel_at_period_end
        
        response = await self._make_request('POST', f'subscriptions/{subscription_id}', data=data)
        
        return {
            'subscription_id': response['id'],
            'status': response['status'],
            'current_period_end': datetime.fromtimestamp(response['current_period_end']),
            'cancel_at_period_end': response['cancel_at_period_end'],
            'provider_response': response
        }
    
    async def cancel_subscription(
        self,
        subscription_id: str,
        cancel_immediately: bool = False
    ) -> bool:
        """
        Cancel a subscription.
        
        Args:
            subscription_id: Stripe subscription ID
            cancel_immediately: If True, cancel now. If False, cancel at period end.
        
        Returns:
            True if successful
        """
        try:
            if cancel_immediately:
                # Delete subscription immediately
                await self._make_request('DELETE', f'subscriptions/{subscription_id}')
            else:
                # Cancel at period end
                data = {'cancel_at_period_end': True}
                await self._make_request('POST', f'subscriptions/{subscription_id}', data=data)
            
            return True
        except PaymentError as e:
            logger.error(f"Failed to cancel subscription {subscription_id}: {e.message}")
            return False
    
    async def reactivate_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Reactivate a subscription that was set to cancel at period end.
        
        Args:
            subscription_id: Stripe subscription ID
        
        Returns:
            Dict with updated subscription details
        """
        data = {'cancel_at_period_end': False}
        response = await self._make_request('POST', f'subscriptions/{subscription_id}', data=data)
        
        return {
            'subscription_id': response['id'],
            'status': response['status'],
            'cancel_at_period_end': response['cancel_at_period_end'],
            'provider_response': response
        }
    
    # ===========================================
    # Price/Product Management
    # ===========================================
    
    async def create_price(
        self,
        product_id: str,
        unit_amount: float,
        currency: str = "CAD",
        recurring_interval: str = "month",  # month or year
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a recurring price for a product.
        
        Args:
            product_id: Stripe product ID
            unit_amount: Price in dollars per billing period
            currency: Currency code
            recurring_interval: Billing interval (month or year)
            metadata: Additional metadata
        
        Returns:
            Dict with price_id and price details
        """
        amount_cents = int(Decimal(str(unit_amount)) * 100)
        
        data = {
            'product': product_id,
            'unit_amount': amount_cents,
            'currency': currency.lower(),
            'recurring': {'interval': recurring_interval},
            'metadata': metadata or {}
        }
        
        response = await self._make_request('POST', 'prices', data=data)
        
        return {
            'price_id': response['id'],
            'product_id': response['product'],
            'unit_amount': unit_amount,
            'currency': currency,
            'recurring_interval': recurring_interval,
            'provider_response': response
        }
    
    async def create_product(
        self,
        name: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe product (represents a subscription plan).
        
        Args:
            name: Product name (e.g., "Professional Plan", "Enterprise Plan")
            description: Product description
            metadata: Additional metadata
        
        Returns:
            Dict with product_id and product details
        """
        data = {
            'name': name,
            'metadata': metadata or {}
        }
        
        if description:
            data['description'] = description
        
        response = await self._make_request('POST', 'products', data=data)
        
        return {
            'product_id': response['id'],
            'name': response['name'],
            'description': response.get('description'),
            'provider_response': response
        }
    
    # ===========================================
    # Webhook Management
    # ===========================================
    
    async def validate_webhook(
        self,
        payload: bytes,
        signature: str
    ) -> bool:
        """
        Validate Stripe webhook signature.
        
        Args:
            payload: Raw request body bytes
            signature: Stripe-Signature header value
        
        Returns:
            True if signature is valid
        """
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured, skipping signature validation")
            return True
        
        try:
            # Extract timestamp and signature from header
            signature_parts = {}
            for part in signature.split(','):
                key, value = part.split('=')
                signature_parts[key] = value
            
            timestamp = signature_parts.get('t')
            expected_signature = signature_parts.get('v1')
            
            if not timestamp or not expected_signature:
                logger.error("Invalid signature format")
                return False
            
            # Construct signed payload
            signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
            
            # Compute expected signature
            computed_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                signed_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(computed_signature, expected_signature)
        
        except Exception as e:
            logger.error(f"Webhook validation error: {str(e)}")
            return False
    
    async def process_webhook(
        self,
        event_type: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process Stripe webhook event.
        
        Args:
            event_type: Stripe event type (e.g., invoice.payment_succeeded)
            payload: Event payload
        
        Returns:
            Dict with processing result
        """
        event_object = payload.get('data', {}).get('object', {})
        
        result = {
            'event_type': event_type,
            'processed': True,
            'action': None,
            'data': {}
        }
        
        # Handle different event types
        if event_type == 'invoice.payment_succeeded':
            result['action'] = 'payment_succeeded'
            result['data'] = {
                'subscription_id': event_object.get('subscription'),
                'amount_paid': Decimal(event_object.get('amount_paid', 0)) / 100,
                'customer_id': event_object.get('customer'),
                'invoice_id': event_object.get('id')
            }
        
        elif event_type == 'invoice.payment_failed':
            result['action'] = 'payment_failed'
            result['data'] = {
                'subscription_id': event_object.get('subscription'),
                'amount_due': Decimal(event_object.get('amount_due', 0)) / 100,
                'customer_id': event_object.get('customer'),
                'invoice_id': event_object.get('id'),
                'attempt_count': event_object.get('attempt_count', 1)
            }
        
        elif event_type == 'customer.subscription.deleted':
            result['action'] = 'subscription_cancelled'
            result['data'] = {
                'subscription_id': event_object.get('id'),
                'customer_id': event_object.get('customer'),
                'canceled_at': datetime.fromtimestamp(event_object.get('canceled_at', 0))
            }
        
        elif event_type == 'customer.subscription.updated':
            result['action'] = 'subscription_updated'
            result['data'] = {
                'subscription_id': event_object.get('id'),
                'customer_id': event_object.get('customer'),
                'status': event_object.get('status'),
                'current_period_end': datetime.fromtimestamp(event_object.get('current_period_end', 0))
            }
        
        else:
            logger.info(f"Unhandled webhook event type: {event_type}")
            result['processed'] = False
        
        return result
    
    # ===========================================
    # Utility Methods
    # ===========================================
    
    def get_dashboard_url(self, transaction_id: str) -> str:
        """Get URL to view transaction in Stripe dashboard"""
        env = 'test' if self.is_test_mode() else ''
        return f"https://dashboard.stripe.com/{env}/payments/{transaction_id}"
    
    def is_test_mode(self) -> bool:
        """Check if using test API keys"""
        return self.api_key.startswith('sk_test_') if self.api_key else True
