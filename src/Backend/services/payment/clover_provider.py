"""
Clover Payment Provider Implementation
Handles payment processing through Clover's REST API
"""

import asyncio
import aiohttp
import hmac
import hashlib
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from datetime import datetime, timezone
from uuid import UUID, uuid4
from enum import Enum

from .base import (
    BasePaymentProvider,
    PaymentRequest,
    PaymentResponse,
    PaymentStatus,
    PaymentError,
    TransactionType
)

logger = logging.getLogger(__name__)


class CloverEnvironment(Enum):
    SANDBOX = "sandbox"
    PRODUCTION = "production"


class CloverEndpoints:
    """Clover API endpoints"""
    
    @staticmethod
    def get_base_url(environment: CloverEnvironment) -> str:
        if environment == CloverEnvironment.SANDBOX:
            return "https://apisandbox.dev.clover.com"
        return "https://api.clover.com"
    
    # Transaction endpoints
    CHARGES = "/v1/charges"
    REFUNDS = "/v1/refunds"
    ORDERS = "/v3/merchants/{merchant_id}/orders"
    PAYMENTS = "/v3/merchants/{merchant_id}/orders/{order_id}/payments"
    
    # Customer & card endpoints
    CUSTOMERS = "/v3/merchants/{merchant_id}/customers"
    CARDS = "/v3/merchants/{merchant_id}/customers/{customer_id}/cards"
    
    # Tokenization
    TOKENIZE = "/v1/tokens"


class CloverProvider(BasePaymentProvider):
    """
    Clover payment provider implementation with multi-tenant support
    Supports: charges, refunds, tokenization, recurring payments
    Each instance is tenant-specific with isolated credentials and configuration
    """
    
    def __init__(self, provider_config: Dict[str, Any]):
        super().__init__(provider_config)
        
        # Tenant context
        self.tenant_id = provider_config.get('tenant_id')
        self.tenant_provider_id = provider_config.get('tenant_provider_id')
        
        # Clover specific configuration
        self.access_token = provider_config.get('access_token')
        self.merchant_id = provider_config.get('merchant_id')
        self.api_key = provider_config.get('api_key')
        self.secret = provider_config.get('secret')
        
        # OAuth tokens for Clover Connect
        self.oauth_access_token = provider_config.get('oauth_access_token')
        self.oauth_refresh_token = provider_config.get('oauth_refresh_token')
        self.oauth_expires_at = provider_config.get('oauth_expires_at')
        
        # Environment setup
        env_str = provider_config.get('environment', 'sandbox')
        self.environment = CloverEnvironment.SANDBOX if env_str == 'sandbox' else CloverEnvironment.PRODUCTION
        self.base_url = CloverEndpoints.get_base_url(self.environment)
        
        # Platform fee configuration
        self.platform_fee_percentage = provider_config.get('platform_fee_percentage', 0.02)
        self.platform_fee_fixed = provider_config.get('platform_fee_fixed', 0.0)
        
        # Transaction limits
        self.daily_limit = provider_config.get('daily_limit')
        self.transaction_limit = provider_config.get('transaction_limit')
        
        # HTTP client configuration
        self.session: Optional[aiohttp.ClientSession] = None
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # Initialize HTTP session
        asyncio.create_task(self._init_session())
    
    async def _init_session(self):
        """Initialize aiohttp session"""
        if not self.session:
            connector = aiohttp.TCPConnector(
                limit=100,
                ttl_dns_cache=300
            )
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout
            )
    
    async def _ensure_session(self):
        """Ensure HTTP session is initialized"""
        if not self.session:
            await self._init_session()
    
    def _get_headers(self, content_type: str = "application/json") -> Dict[str, str]:
        """Get request headers with authentication and tenant context"""
        # Use OAuth token if available, otherwise fall back to API key
        auth_token = self.oauth_access_token or self.access_token
        
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": content_type,
            "Accept": "application/json",
            "X-Clover-Merchant-Id": self.merchant_id
        }
        
        # Add tenant context for internal tracking
        if self.tenant_id:
            headers["X-Tenant-Id"] = str(self.tenant_id)
        
        return headers
    
    async def _send_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send HTTP request to Clover API with retry logic
        """
        await self._ensure_session()
        
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Clover API request: {method} {endpoint} (attempt {attempt + 1})")
                
                async with self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params
                ) as response:
                    response_text = await response.text()
                    
                    # Log response (without sensitive data)
                    self.logger.info(f"Clover API response: {response.status}")
                    
                    if response.status == 200:
                        return json.loads(response_text)
                    elif response.status == 201:
                        return json.loads(response_text)
                    elif response.status == 401:
                        raise PaymentError(
                            "Authentication failed",
                            error_code="AUTH_FAILED",
                            provider_error=response_text
                        )
                    elif response.status == 429:
                        # Rate limited, wait and retry
                        await asyncio.sleep(self.retry_delay * (2 ** attempt))
                        continue
                    elif response.status >= 500:
                        # Server error, retry with exponential backoff
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay * (2 ** attempt))
                            continue
                        raise PaymentError(
                            "Server error",
                            error_code="SERVER_ERROR",
                            provider_error=response_text
                        )
                    else:
                        # Client error, don't retry
                        error_data = json.loads(response_text) if response_text else {}
                        raise PaymentError(
                            error_data.get('message', 'Request failed'),
                            error_code=error_data.get('code', 'UNKNOWN_ERROR'),
                            provider_error=response_text
                        )
                        
            except aiohttp.ClientError as e:
                self.logger.error(f"Network error on attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                raise PaymentError(
                    "Network error",
                    error_code="NETWORK_ERROR",
                    provider_error=str(e)
                )
            except Exception as e:
                self.logger.error(f"Unexpected error: {str(e)}")
                raise PaymentError(
                    "Unexpected error",
                    error_code="SYSTEM_ERROR",
                    provider_error=str(e)
                )
        
        raise PaymentError(
            "Max retries exceeded",
            error_code="MAX_RETRIES",
            provider_error="Failed after maximum retry attempts"
        )
    
    def _parse_card_source(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse card information for Clover format"""
        source = {}
        
        if 'token' in payment_data:
            # Using tokenized card
            source['token'] = payment_data['token']
        elif 'card_number' in payment_data:
            # Using raw card data (PCI compliance required)
            source['card'] = {
                'number': payment_data['card_number'],
                'exp_month': str(payment_data['exp_month']),
                'exp_year': str(payment_data['exp_year']),
                'cvv': payment_data.get('cvv')
            }
            
            # Add cardholder name if provided
            if 'cardholder_name' in payment_data:
                source['card']['name'] = payment_data['cardholder_name']
        
        return source
    
    async def charge(self, request: PaymentRequest) -> PaymentResponse:
        """
        Process a payment charge through Clover
        """
        try:
            # Generate unique transaction ID
            transaction_id = str(uuid4())
            
            # Check transaction limits
            if self.transaction_limit and request.amount > self.transaction_limit:
                raise PaymentError(
                    f"Transaction amount exceeds limit of {self.transaction_limit}",
                    error_code="TRANSACTION_LIMIT_EXCEEDED"
                )
            
            # Calculate platform fees
            platform_fee = self._calculate_platform_fee(request.amount)
            
            # Prepare charge request
            charge_data = {
                'amount': self.format_amount(request.amount),
                'currency': request.currency.lower(),
                'description': request.description or f"Order {request.order_id}",
                'capture': True,  # Immediately capture the payment
                'metadata': {
                    'order_id': str(request.order_id) if request.order_id else None,
                    'customer_id': str(request.customer_id) if request.customer_id else None,
                    'transaction_id': transaction_id,
                    'tenant_id': str(self.tenant_id) if self.tenant_id else None,
                    'tenant_provider_id': str(self.tenant_provider_id) if self.tenant_provider_id else None,
                    'platform_fee': str(platform_fee)
                }
            }
            
            # Add payment source
            if request.payment_method_id:
                # Fetch stored payment method token
                charge_data['source'] = str(request.payment_method_id)
            elif request.metadata and 'payment_data' in request.metadata:
                # Parse payment data
                charge_data['source'] = self._parse_card_source(request.metadata['payment_data'])
            else:
                raise PaymentError(
                    "No payment method provided",
                    error_code="MISSING_PAYMENT_METHOD"
                )
            
            # Add customer email if available
            if request.metadata and 'customer_email' in request.metadata:
                charge_data['receipt_email'] = request.metadata['customer_email']
            
            # Add billing address
            if request.billing_address:
                charge_data['billing_details'] = {
                    'address': {
                        'line1': request.billing_address.get('line1'),
                        'line2': request.billing_address.get('line2'),
                        'city': request.billing_address.get('city'),
                        'state': request.billing_address.get('state'),
                        'postal_code': request.billing_address.get('postal_code'),
                        'country': request.billing_address.get('country', 'CA')
                    }
                }
            
            # Add 3D Secure if required
            if request.metadata and request.metadata.get('require_3ds'):
                charge_data['three_d_secure'] = {
                    'required': True
                }
            
            # Send charge request
            response = await self._send_request(
                method='POST',
                endpoint=CloverEndpoints.CHARGES,
                data=charge_data
            )
            
            # Parse response
            status = self._map_charge_status(response.get('status'))
            
            return PaymentResponse(
                transaction_id=transaction_id,
                status=status,
                amount=request.amount,
                currency=request.currency,
                provider_transaction_id=response.get('id'),
                error_code=response.get('failure_code'),
                error_message=response.get('failure_message'),
                metadata={
                    'source': response.get('source', {}),
                    'outcome': response.get('outcome', {}),
                    'paid': response.get('paid', False),
                    'captured': response.get('captured', False),
                    'refunded': response.get('refunded', False)
                }
            )
            
        except PaymentError:
            raise
        except Exception as e:
            self.logger.error(f"Charge failed: {str(e)}")
            raise PaymentError(
                "Charge processing failed",
                error_code="CHARGE_FAILED",
                provider_error=str(e)
            )
    
    async def refund(
        self,
        transaction_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> PaymentResponse:
        """
        Process a refund through Clover
        """
        try:
            # Get original transaction
            original_transaction = await self.get_transaction(transaction_id)
            
            if not original_transaction:
                raise PaymentError(
                    "Transaction not found",
                    error_code="TRANSACTION_NOT_FOUND"
                )
            
            # Prepare refund request
            refund_data = {
                'charge': original_transaction.get('provider_transaction_id'),
                'reason': reason or 'requested_by_customer',
                'metadata': {
                    'original_transaction_id': transaction_id,
                    'refund_reason': reason
                }
            }
            
            # Add refund amount if partial
            if amount:
                refund_data['amount'] = self.format_amount(amount)
            
            # Send refund request
            response = await self._send_request(
                method='POST',
                endpoint=CloverEndpoints.REFUNDS,
                data=refund_data
            )
            
            # Parse response
            status = PaymentStatus.REFUNDED if response.get('status') == 'succeeded' else PaymentStatus.FAILED
            
            return PaymentResponse(
                transaction_id=str(uuid4()),
                status=status,
                amount=self.parse_amount(response.get('amount', 0)),
                currency=response.get('currency', 'CAD').upper(),
                provider_transaction_id=response.get('id'),
                error_code=response.get('failure_code'),
                error_message=response.get('failure_message'),
                metadata={
                    'refund_id': response.get('id'),
                    'original_charge': response.get('charge'),
                    'reason': response.get('reason')
                }
            )
            
        except PaymentError:
            raise
        except Exception as e:
            self.logger.error(f"Refund failed: {str(e)}")
            raise PaymentError(
                "Refund processing failed",
                error_code="REFUND_FAILED",
                provider_error=str(e)
            )
    
    async def void(self, transaction_id: str) -> PaymentResponse:
        """
        Void a transaction (cancel before settlement)
        """
        try:
            # Clover handles voids as full refunds before settlement
            return await self.refund(transaction_id, reason="transaction_voided")
            
        except PaymentError:
            raise
        except Exception as e:
            self.logger.error(f"Void failed: {str(e)}")
            raise PaymentError(
                "Void processing failed",
                error_code="VOID_FAILED",
                provider_error=str(e)
            )
    
    async def get_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """
        Get transaction details from Clover
        """
        try:
            # This would typically query your database for the provider_transaction_id
            # then fetch from Clover API
            # For now, returning a placeholder structure
            return {
                'transaction_id': transaction_id,
                'provider_transaction_id': None,
                'status': 'unknown',
                'amount': 0,
                'currency': 'CAD'
            }
            
        except Exception as e:
            self.logger.error(f"Get transaction failed: {str(e)}")
            raise PaymentError(
                "Failed to retrieve transaction",
                error_code="TRANSACTION_RETRIEVAL_FAILED",
                provider_error=str(e)
            )
    
    async def tokenize_payment_method(
        self,
        payment_data: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Tokenize a payment method for secure storage
        """
        try:
            # Prepare tokenization request
            token_data = {
                'card': {
                    'number': payment_data['card_number'],
                    'exp_month': str(payment_data['exp_month']),
                    'exp_year': str(payment_data['exp_year']),
                    'cvv': payment_data.get('cvv'),
                    'name': payment_data.get('cardholder_name')
                }
            }
            
            # Add billing address if provided
            if 'billing_address' in payment_data:
                token_data['card']['address_line1'] = payment_data['billing_address'].get('line1')
                token_data['card']['address_zip'] = payment_data['billing_address'].get('postal_code')
            
            # Send tokenization request
            response = await self._send_request(
                method='POST',
                endpoint=CloverEndpoints.TOKENIZE,
                data=token_data
            )
            
            # Extract token and metadata
            token = response.get('id')
            metadata = {
                'card_brand': response.get('card', {}).get('brand'),
                'card_last_four': response.get('card', {}).get('last4'),
                'exp_month': response.get('card', {}).get('exp_month'),
                'exp_year': response.get('card', {}).get('exp_year'),
                'fingerprint': response.get('card', {}).get('fingerprint'),
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            return token, metadata
            
        except PaymentError:
            raise
        except Exception as e:
            self.logger.error(f"Tokenization failed: {str(e)}")
            raise PaymentError(
                "Failed to tokenize payment method",
                error_code="TOKENIZATION_FAILED",
                provider_error=str(e)
            )
    
    async def delete_payment_method(self, token: str) -> bool:
        """
        Delete a tokenized payment method
        """
        try:
            # Clover doesn't support direct token deletion
            # Tokens are typically deleted by removing the customer card
            # This would be handled at the customer management level
            self.logger.info(f"Token deletion requested for: {token[:8]}...")
            return True
            
        except Exception as e:
            self.logger.error(f"Delete payment method failed: {str(e)}")
            return False
    
    async def validate_webhook(
        self,
        payload: bytes,
        signature: str
    ) -> bool:
        """
        Validate webhook signature from Clover
        """
        try:
            # Clover uses HMAC-SHA256 for webhook signatures
            expected_signature = hmac.new(
                self.secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            self.logger.error(f"Webhook validation failed: {str(e)}")
            return False
    
    async def process_webhook(
        self,
        event_type: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process webhook event from Clover
        """
        try:
            self.logger.info(f"Processing Clover webhook: {event_type}")
            
            # Map Clover events to internal events
            event_mapping = {
                'payment.created': 'payment_completed',
                'payment.updated': 'payment_updated',
                'refund.created': 'refund_completed',
                'refund.updated': 'refund_updated',
                'charge.failed': 'payment_failed',
                'charge.succeeded': 'payment_succeeded',
                'charge.captured': 'payment_captured',
                'dispute.created': 'dispute_created',
                'dispute.updated': 'dispute_updated'
            }
            
            internal_event = event_mapping.get(event_type, event_type)
            
            # Extract relevant data based on event type
            if event_type.startswith('payment.'):
                return {
                    'event': internal_event,
                    'transaction_id': payload.get('id'),
                    'status': self._map_charge_status(payload.get('status')),
                    'amount': self.parse_amount(payload.get('amount', 0)),
                    'currency': payload.get('currency', 'CAD').upper(),
                    'metadata': payload.get('metadata', {})
                }
            elif event_type.startswith('refund.'):
                return {
                    'event': internal_event,
                    'refund_id': payload.get('id'),
                    'charge_id': payload.get('charge'),
                    'status': 'completed' if payload.get('status') == 'succeeded' else 'failed',
                    'amount': self.parse_amount(payload.get('amount', 0)),
                    'currency': payload.get('currency', 'CAD').upper(),
                    'reason': payload.get('reason')
                }
            elif event_type.startswith('dispute.'):
                return {
                    'event': internal_event,
                    'dispute_id': payload.get('id'),
                    'charge_id': payload.get('charge'),
                    'amount': self.parse_amount(payload.get('amount', 0)),
                    'currency': payload.get('currency', 'CAD').upper(),
                    'reason': payload.get('reason'),
                    'status': payload.get('status'),
                    'evidence_due_by': payload.get('evidence_details', {}).get('due_by')
                }
            else:
                return {
                    'event': internal_event,
                    'data': payload
                }
                
        except Exception as e:
            self.logger.error(f"Webhook processing failed: {str(e)}")
            raise PaymentError(
                "Failed to process webhook",
                error_code="WEBHOOK_PROCESSING_FAILED",
                provider_error=str(e)
            )
    
    async def pre_authorize(self, request: PaymentRequest) -> PaymentResponse:
        """
        Pre-authorize a payment (hold funds without capturing)
        """
        try:
            # Similar to charge but with capture=false
            transaction_id = str(uuid4())
            
            charge_data = {
                'amount': self.format_amount(request.amount),
                'currency': request.currency.lower(),
                'description': request.description or f"Pre-auth for Order {request.order_id}",
                'capture': False,  # Don't capture immediately
                'metadata': {
                    'order_id': str(request.order_id) if request.order_id else None,
                    'customer_id': str(request.customer_id) if request.customer_id else None,
                    'transaction_id': transaction_id
                }
            }
            
            # Add payment source
            if request.payment_method_id:
                charge_data['source'] = str(request.payment_method_id)
            elif request.metadata and 'payment_data' in request.metadata:
                charge_data['source'] = self._parse_card_source(request.metadata['payment_data'])
            else:
                raise PaymentError(
                    "No payment method provided",
                    error_code="MISSING_PAYMENT_METHOD"
                )
            
            # Send pre-auth request
            response = await self._send_request(
                method='POST',
                endpoint=CloverEndpoints.CHARGES,
                data=charge_data
            )
            
            status = PaymentStatus.PROCESSING if response.get('captured') is False else PaymentStatus.COMPLETED
            
            return PaymentResponse(
                transaction_id=transaction_id,
                status=status,
                amount=request.amount,
                currency=request.currency,
                provider_transaction_id=response.get('id'),
                metadata={
                    'captured': response.get('captured', False),
                    'capturable': True
                }
            )
            
        except PaymentError:
            raise
        except Exception as e:
            self.logger.error(f"Pre-authorization failed: {str(e)}")
            raise PaymentError(
                "Pre-authorization failed",
                error_code="PREAUTH_FAILED",
                provider_error=str(e)
            )
    
    async def capture(
        self,
        transaction_id: str,
        amount: Optional[Decimal] = None
    ) -> PaymentResponse:
        """
        Capture a pre-authorized payment
        """
        try:
            # Get original transaction to find provider_transaction_id
            original_transaction = await self.get_transaction(transaction_id)
            
            if not original_transaction:
                raise PaymentError(
                    "Transaction not found",
                    error_code="TRANSACTION_NOT_FOUND"
                )
            
            capture_data = {}
            if amount:
                capture_data['amount'] = self.format_amount(amount)
            
            # Send capture request
            endpoint = f"{CloverEndpoints.CHARGES}/{original_transaction['provider_transaction_id']}/capture"
            response = await self._send_request(
                method='POST',
                endpoint=endpoint,
                data=capture_data
            )
            
            return PaymentResponse(
                transaction_id=transaction_id,
                status=PaymentStatus.COMPLETED if response.get('captured') else PaymentStatus.FAILED,
                amount=self.parse_amount(response.get('amount_captured', 0)),
                currency=response.get('currency', 'CAD').upper(),
                provider_transaction_id=response.get('id'),
                metadata={
                    'captured': response.get('captured', False),
                    'captured_at': response.get('created')
                }
            )
            
        except PaymentError:
            raise
        except Exception as e:
            self.logger.error(f"Capture failed: {str(e)}")
            raise PaymentError(
                "Capture failed",
                error_code="CAPTURE_FAILED",
                provider_error=str(e)
            )
    
    def _calculate_platform_fee(self, amount: Decimal) -> Decimal:
        """Calculate platform fee for the transaction"""
        percentage_fee = amount * Decimal(str(self.platform_fee_percentage))
        total_fee = percentage_fee + Decimal(str(self.platform_fee_fixed))
        return round(total_fee, 2)
    
    def _map_charge_status(self, clover_status: str) -> PaymentStatus:
        """Map Clover charge status to internal PaymentStatus"""
        status_mapping = {
            'succeeded': PaymentStatus.COMPLETED,
            'pending': PaymentStatus.PENDING,
            'failed': PaymentStatus.FAILED,
            'canceled': PaymentStatus.CANCELLED,
            'processing': PaymentStatus.PROCESSING
        }
        return status_mapping.get(clover_status, PaymentStatus.PENDING)
    
    async def create_customer(
        self,
        customer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a customer profile in Clover
        """
        try:
            endpoint = CloverEndpoints.CUSTOMERS.format(merchant_id=self.merchant_id)
            
            customer_request = {
                'firstName': customer_data.get('first_name'),
                'lastName': customer_data.get('last_name'),
                'email': customer_data.get('email'),
                'phoneNumber': customer_data.get('phone'),
                'marketingAllowed': customer_data.get('marketing_allowed', False)
            }
            
            response = await self._send_request(
                method='POST',
                endpoint=endpoint,
                data=customer_request
            )
            
            return {
                'customer_id': response.get('id'),
                'created_at': response.get('createdTime'),
                'email': response.get('email')
            }
            
        except Exception as e:
            self.logger.error(f"Create customer failed: {str(e)}")
            raise PaymentError(
                "Failed to create customer",
                error_code="CUSTOMER_CREATION_FAILED",
                provider_error=str(e)
            )
    
    async def add_card_to_customer(
        self,
        customer_id: str,
        card_token: str
    ) -> Dict[str, Any]:
        """
        Add a tokenized card to a customer profile
        """
        try:
            endpoint = CloverEndpoints.CARDS.format(
                merchant_id=self.merchant_id,
                customer_id=customer_id
            )
            
            card_request = {
                'token': card_token
            }
            
            response = await self._send_request(
                method='POST',
                endpoint=endpoint,
                data=card_request
            )
            
            return {
                'card_id': response.get('id'),
                'last4': response.get('last4'),
                'brand': response.get('cardType'),
                'exp_month': response.get('expirationDate')[:2] if response.get('expirationDate') else None,
                'exp_year': response.get('expirationDate')[2:] if response.get('expirationDate') else None
            }
            
        except Exception as e:
            self.logger.error(f"Add card to customer failed: {str(e)}")
            raise PaymentError(
                "Failed to add card to customer",
                error_code="CARD_ADDITION_FAILED",
                provider_error=str(e)
            )
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self
    
    async def health_check(self) -> bool:
        """
        Perform health check on the Clover API connection
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Simple merchant info request to verify connectivity
            endpoint = f"/v3/merchants/{self.merchant_id}"
            response = await self._send_request(
                method='GET',
                endpoint=endpoint
            )
            return response is not None
        except Exception as e:
            self.logger.error(f"Health check failed for tenant {self.tenant_id}: {str(e)}")
            return False
    
    async def refresh_oauth_token(self) -> bool:
        """
        Refresh OAuth access token using refresh token
        
        Returns:
            True if refresh successful, False otherwise
        """
        if not self.oauth_refresh_token:
            return False
        
        try:
            # Clover OAuth token refresh endpoint
            refresh_data = {
                'client_id': self.api_key,
                'client_secret': self.secret,
                'refresh_token': self.oauth_refresh_token,
                'grant_type': 'refresh_token'
            }
            
            async with self.session.post(
                f"{self.base_url}/oauth/v2/token",
                data=refresh_data
            ) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.oauth_access_token = token_data.get('access_token')
                    self.oauth_refresh_token = token_data.get('refresh_token', self.oauth_refresh_token)
                    
                    # Calculate expiration time
                    expires_in = token_data.get('expires_in', 3600)
                    self.oauth_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                    
                    self.logger.info(f"OAuth token refreshed for tenant {self.tenant_id}")
                    return True
                else:
                    self.logger.error(f"OAuth refresh failed with status {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"OAuth token refresh failed: {str(e)}")
            return False
    
    def get_webhook_path(self) -> str:
        """
        Generate unique webhook path for this tenant's Clover provider
        
        Returns:
            Webhook path string
        """
        if self.tenant_id and self.tenant_provider_id:
            return f"/webhooks/clover/{self.tenant_id}/{self.tenant_provider_id}"
        return f"/webhooks/clover/default"
    
    async def register_webhook(self, webhook_url: str, events: List[str]) -> Optional[str]:
        """
        Register webhook endpoint with Clover
        
        Args:
            webhook_url: Full webhook URL
            events: List of events to subscribe to
            
        Returns:
            Webhook ID if successful, None otherwise
        """
        try:
            webhook_data = {
                'url': webhook_url,
                'events': events,
                'merchant_id': self.merchant_id
            }
            
            response = await self._send_request(
                method='POST',
                endpoint='/v3/webhooks',
                data=webhook_data
            )
            
            webhook_id = response.get('id')
            self.logger.info(f"Webhook registered for tenant {self.tenant_id}: {webhook_id}")
            return webhook_id
            
        except Exception as e:
            self.logger.error(f"Webhook registration failed: {str(e)}")
            return None
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()