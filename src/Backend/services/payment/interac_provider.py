"""
Interac e-Transfer Payment Provider Implementation
Handles payment processing through Interac e-Transfer API
"""

import asyncio
import aiohttp
import hmac
import hashlib
import json
import logging
import secrets
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from datetime import datetime, timezone, timedelta
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


class InteracEnvironment(Enum):
    SANDBOX = "sandbox"
    PRODUCTION = "production"


class InteracTransferStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    DEPOSITED = "deposited"
    RECLAIMED = "reclaimed"


class InteracProvider(BasePaymentProvider):
    """
    Interac e-Transfer payment provider implementation
    
    Features:
    - Request Money: Send payment requests via email/SMS
    - Auto-Deposit: Automatic deposit for registered recipients
    - Security Questions: Optional security for transfers
    - Bulk Transfers: Multiple transfers in one request
    - Status Tracking: Real-time transfer status updates
    """
    
    def __init__(self, provider_config: Dict[str, Any]):
        super().__init__(provider_config)
        
        # Interac specific configuration
        self.contact_id = provider_config.get('contact_id')
        self.api_registration_key = provider_config.get('api_registration_key')
        self.secret_key = provider_config.get('secret_key')
        self.thirdparty_access_token = provider_config.get('thirdparty_access_token')
        
        # Business details
        self.business_name = provider_config.get('business_name', 'WeedGo')
        self.notification_email = provider_config.get('notification_email')
        
        # Environment setup
        env_str = provider_config.get('environment', 'sandbox')
        self.environment = InteracEnvironment.SANDBOX if env_str == 'sandbox' else InteracEnvironment.PRODUCTION
        
        # API endpoints
        if self.environment == InteracEnvironment.SANDBOX:
            self.base_url = "https://gateway-web.beta.interac.ca/publicapi/api/v2"
        else:
            self.base_url = "https://gateway-web.interac.ca/publicapi/api/v2"
        
        # HTTP client configuration
        self.session: Optional[aiohttp.ClientSession] = None
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # Transfer settings
        self.default_expiry_days = 30
        self.max_transfer_amount = Decimal('3000.00')  # Interac limit
        self.min_transfer_amount = Decimal('0.01')
        
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
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        return {
            "accessToken": self.thirdparty_access_token,
            "thirdPartyAccessId": self.contact_id,
            "requestId": str(uuid4()),
            "deviceId": "payment-server",
            "apiRegistrationKey": self.api_registration_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _generate_security_question(self) -> Tuple[str, str]:
        """Generate a secure question and answer for transfer"""
        # Generate a random security code
        answer = secrets.token_urlsafe(8)
        question = "Please enter your order security code"
        return question, answer
    
    async def _send_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send HTTP request to Interac API with retry logic
        """
        await self._ensure_session()
        
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Interac API request: {method} {endpoint} (attempt {attempt + 1})")
                
                async with self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params
                ) as response:
                    response_text = await response.text()
                    
                    # Log response (without sensitive data)
                    self.logger.info(f"Interac API response: {response.status}")
                    
                    if response.status in [200, 201, 202]:
                        return json.loads(response_text) if response_text else {}
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
    
    async def charge(self, request: PaymentRequest) -> PaymentResponse:
        """
        Process a payment charge through Interac e-Transfer
        This creates a "Request Money" transaction
        """
        try:
            # Validate amount
            if request.amount > self.max_transfer_amount:
                raise PaymentError(
                    f"Amount exceeds maximum transfer limit of ${self.max_transfer_amount}",
                    error_code="AMOUNT_TOO_HIGH"
                )
            
            if request.amount < self.min_transfer_amount:
                raise PaymentError(
                    f"Amount below minimum transfer limit of ${self.min_transfer_amount}",
                    error_code="AMOUNT_TOO_LOW"
                )
            
            # Generate transaction reference
            transaction_id = str(uuid4())
            reference_number = f"WG-{transaction_id[:8].upper()}"
            
            # Get customer email from metadata
            customer_email = request.metadata.get('customer_email') if request.metadata else None
            customer_phone = request.metadata.get('customer_phone') if request.metadata else None
            
            if not customer_email and not customer_phone:
                raise PaymentError(
                    "Customer email or phone required for Interac transfer",
                    error_code="MISSING_CONTACT"
                )
            
            # Generate security question if not auto-deposit
            use_auto_deposit = request.metadata.get('auto_deposit', False) if request.metadata else False
            security_question = None
            security_answer = None
            
            if not use_auto_deposit:
                security_question, security_answer = self._generate_security_question()
            
            # Prepare money request
            money_request = {
                "referenceNumber": reference_number,
                "sourceMoneyRequestId": transaction_id,
                "requestedFrom": {
                    "contactId": str(request.customer_id) if request.customer_id else None,
                    "contactName": request.metadata.get('customer_name', 'Customer') if request.metadata else 'Customer',
                    "contactEmail": customer_email,
                    "contactPhone": customer_phone,
                    "language": "en"
                },
                "amount": float(request.amount),
                "currency": "CAD",  # Interac only supports CAD
                "editableFulfillAmount": False,
                "requesterMessage": request.description or f"Payment for Order #{request.order_id}",
                "expiryDate": (datetime.now(timezone.utc) + timedelta(days=self.default_expiry_days)).isoformat(),
                "supressResponderNotifications": False,
                "returnUrl": request.metadata.get('return_url') if request.metadata else None,
                "creationDate": datetime.now(timezone.utc).isoformat(),
                "status": "REQUEST_PENDING"
            }
            
            # Add security question if not using auto-deposit
            if not use_auto_deposit:
                money_request["securityQuestion"] = security_question
                money_request["securityAnswer"] = security_answer
            
            # Add invoice details if available
            if request.metadata and 'invoice_number' in request.metadata:
                money_request["invoiceNumber"] = request.metadata['invoice_number']
            
            # Send money request
            response = await self._send_request(
                method='POST',
                endpoint='/money-requests/send',
                data=money_request
            )
            
            # Parse response
            status = self._map_transfer_status(response.get('status', 'REQUEST_PENDING'))
            
            return PaymentResponse(
                transaction_id=transaction_id,
                status=status,
                amount=request.amount,
                currency='CAD',
                provider_transaction_id=response.get('paymentGuid'),
                metadata={
                    'reference_number': reference_number,
                    'security_answer': security_answer if security_answer else None,
                    'expiry_date': money_request['expiryDate'],
                    'request_status': response.get('status'),
                    'auto_deposit': use_auto_deposit,
                    'contact_method': 'email' if customer_email else 'phone'
                }
            )
            
        except PaymentError:
            raise
        except Exception as e:
            self.logger.error(f"Charge failed: {str(e)}")
            raise PaymentError(
                "Interac transfer request failed",
                error_code="TRANSFER_FAILED",
                provider_error=str(e)
            )
    
    async def refund(
        self,
        transaction_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> PaymentResponse:
        """
        Process a refund through Interac e-Transfer
        Note: Interac doesn't support traditional refunds - this would cancel a pending request
        """
        try:
            # For accepted transfers, we need to create a new transfer back to the customer
            # For pending transfers, we can cancel them
            
            # Get original transaction
            original_transaction = await self.get_transaction(transaction_id)
            
            if not original_transaction:
                raise PaymentError(
                    "Transaction not found",
                    error_code="TRANSACTION_NOT_FOUND"
                )
            
            # Check if transfer is still pending
            if original_transaction.get('status') in ['REQUEST_PENDING', 'PENDING']:
                # Cancel the pending request
                cancel_response = await self._cancel_money_request(
                    original_transaction.get('provider_transaction_id')
                )
                
                return PaymentResponse(
                    transaction_id=str(uuid4()),
                    status=PaymentStatus.CANCELLED,
                    amount=amount or Decimal(str(original_transaction.get('amount', 0))),
                    currency='CAD',
                    provider_transaction_id=cancel_response.get('paymentGuid'),
                    metadata={
                        'action': 'cancelled',
                        'original_transaction': transaction_id,
                        'reason': reason
                    }
                )
            else:
                # For completed transfers, create a new transfer back
                # This would require implementing a send money function
                raise PaymentError(
                    "Completed Interac transfers cannot be refunded directly. Please initiate a new transfer.",
                    error_code="REFUND_NOT_SUPPORTED"
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
    
    async def _cancel_money_request(self, payment_guid: str) -> Dict[str, Any]:
        """Cancel a pending money request"""
        try:
            response = await self._send_request(
                method='PUT',
                endpoint=f'/money-requests/cancel/{payment_guid}',
                data={"cancellationReason": "Merchant initiated cancellation"}
            )
            return response
        except Exception as e:
            self.logger.error(f"Cancel request failed: {str(e)}")
            raise
    
    async def void(self, transaction_id: str) -> PaymentResponse:
        """
        Void a transaction (cancel pending transfer)
        """
        return await self.refund(transaction_id, reason="Transaction voided")
    
    async def get_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """
        Get transaction details from Interac
        """
        try:
            # Query for transaction by reference number
            response = await self._send_request(
                method='GET',
                endpoint=f'/money-requests/status',
                params={'referenceNumber': transaction_id}
            )
            
            return {
                'transaction_id': transaction_id,
                'provider_transaction_id': response.get('paymentGuid'),
                'status': response.get('status'),
                'amount': Decimal(str(response.get('amount', 0))),
                'currency': 'CAD',
                'created_at': response.get('creationDate'),
                'completed_at': response.get('completionDate')
            }
            
        except Exception as e:
            self.logger.error(f"Get transaction failed: {str(e)}")
            return {
                'transaction_id': transaction_id,
                'status': 'unknown',
                'amount': Decimal('0'),
                'currency': 'CAD'
            }
    
    async def tokenize_payment_method(
        self,
        payment_data: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Tokenize payment method for Interac
        Note: Interac uses contact information rather than card tokens
        """
        try:
            # For Interac, we store contact details as the "token"
            contact_id = str(uuid4())
            
            metadata = {
                'type': 'interac',
                'email': payment_data.get('email'),
                'phone': payment_data.get('phone'),
                'name': payment_data.get('name'),
                'auto_deposit_registered': payment_data.get('auto_deposit', False),
                'preferred_language': payment_data.get('language', 'en'),
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            # In production, you would store this in a secure contact registry
            return contact_id, metadata
            
        except Exception as e:
            self.logger.error(f"Tokenization failed: {str(e)}")
            raise PaymentError(
                "Failed to save contact information",
                error_code="TOKENIZATION_FAILED",
                provider_error=str(e)
            )
    
    async def delete_payment_method(self, token: str) -> bool:
        """
        Delete a stored contact
        """
        try:
            # In production, remove from contact registry
            self.logger.info(f"Contact deletion requested for: {token[:8]}...")
            return True
            
        except Exception as e:
            self.logger.error(f"Delete contact failed: {str(e)}")
            return False
    
    async def validate_webhook(
        self,
        payload: bytes,
        signature: str
    ) -> bool:
        """
        Validate webhook signature from Interac
        """
        try:
            # Interac uses HMAC-SHA256 for webhook signatures
            expected_signature = hmac.new(
                self.secret_key.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
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
        Process webhook event from Interac
        """
        try:
            self.logger.info(f"Processing Interac webhook: {event_type}")
            
            # Map Interac events to internal events
            event_mapping = {
                'moneyRequest.pending': 'transfer_pending',
                'moneyRequest.fulfilled': 'transfer_completed',
                'moneyRequest.cancelled': 'transfer_cancelled',
                'moneyRequest.expired': 'transfer_expired',
                'moneyRequest.declined': 'transfer_declined',
                'moneyRequest.reclaimed': 'transfer_reclaimed',
                'notification.sent': 'notification_sent',
                'notification.viewed': 'notification_viewed'
            }
            
            internal_event = event_mapping.get(event_type, event_type)
            
            # Extract relevant data
            return {
                'event': internal_event,
                'transaction_id': payload.get('referenceNumber'),
                'payment_guid': payload.get('paymentGuid'),
                'status': self._map_transfer_status(payload.get('status')),
                'amount': Decimal(str(payload.get('amount', 0))),
                'currency': 'CAD',
                'completed_at': payload.get('completionDate'),
                'metadata': {
                    'fulfillment_name': payload.get('fulfillmentName'),
                    'fulfillment_email': payload.get('fulfillmentEmail'),
                    'deposit_status': payload.get('depositStatus')
                }
            }
            
        except Exception as e:
            self.logger.error(f"Webhook processing failed: {str(e)}")
            raise PaymentError(
                "Failed to process webhook",
                error_code="WEBHOOK_PROCESSING_FAILED",
                provider_error=str(e)
            )
    
    def _map_transfer_status(self, interac_status: str) -> PaymentStatus:
        """Map Interac transfer status to internal PaymentStatus"""
        status_mapping = {
            'REQUEST_PENDING': PaymentStatus.PENDING,
            'PENDING': PaymentStatus.PENDING,
            'SENT': PaymentStatus.PROCESSING,
            'ACCEPTED': PaymentStatus.COMPLETED,
            'DEPOSITED': PaymentStatus.COMPLETED,
            'DECLINED': PaymentStatus.FAILED,
            'CANCELLED': PaymentStatus.CANCELLED,
            'EXPIRED': PaymentStatus.FAILED,
            'RECLAIMED': PaymentStatus.CANCELLED
        }
        return status_mapping.get(interac_status, PaymentStatus.PENDING)
    
    async def send_money(
        self,
        recipient_email: str,
        amount: Decimal,
        message: Optional[str] = None,
        auto_deposit: bool = False
    ) -> Dict[str, Any]:
        """
        Send money to a recipient (for refunds or payouts)
        """
        try:
            transfer_id = str(uuid4())
            reference_number = f"WG-OUT-{transfer_id[:8].upper()}"
            
            # Generate security if not auto-deposit
            security_question = None
            security_answer = None
            if not auto_deposit:
                security_question, security_answer = self._generate_security_question()
            
            transfer_request = {
                "referenceNumber": reference_number,
                "sourceMoneyTransferId": transfer_id,
                "amount": float(amount),
                "currency": "CAD",
                "recipientEmail": recipient_email,
                "recipientName": "Customer",
                "senderMessage": message or "Refund from WeedGo",
                "expiryDate": (datetime.now(timezone.utc) + timedelta(days=self.default_expiry_days)).isoformat()
            }
            
            if not auto_deposit:
                transfer_request["securityQuestion"] = security_question
                transfer_request["securityAnswer"] = security_answer
            
            response = await self._send_request(
                method='POST',
                endpoint='/money-transfers/send',
                data=transfer_request
            )
            
            return {
                'transfer_id': transfer_id,
                'reference_number': reference_number,
                'payment_guid': response.get('paymentGuid'),
                'status': response.get('status'),
                'security_answer': security_answer if security_answer else None,
                'expiry_date': transfer_request['expiryDate']
            }
            
        except Exception as e:
            self.logger.error(f"Send money failed: {str(e)}")
            raise PaymentError(
                "Failed to send money transfer",
                error_code="TRANSFER_SEND_FAILED",
                provider_error=str(e)
            )
    
    async def get_transfer_status(self, reference_number: str) -> Dict[str, Any]:
        """
        Get the status of a money transfer
        """
        try:
            response = await self._send_request(
                method='GET',
                endpoint='/money-transfers/status',
                params={'referenceNumber': reference_number}
            )
            
            return {
                'reference_number': reference_number,
                'status': response.get('status'),
                'payment_guid': response.get('paymentGuid'),
                'amount': Decimal(str(response.get('amount', 0))),
                'completion_date': response.get('completionDate'),
                'deposit_status': response.get('depositStatus')
            }
            
        except Exception as e:
            self.logger.error(f"Get transfer status failed: {str(e)}")
            raise PaymentError(
                "Failed to get transfer status",
                error_code="STATUS_CHECK_FAILED",
                provider_error=str(e)
            )
    
    async def validate_auto_deposit(self, email: str) -> bool:
        """
        Check if an email is registered for auto-deposit
        """
        try:
            response = await self._send_request(
                method='GET',
                endpoint='/auto-deposit/validate',
                params={'email': email}
            )
            
            return response.get('isRegistered', False)
            
        except Exception as e:
            self.logger.warning(f"Auto-deposit validation failed: {str(e)}")
            return False
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()