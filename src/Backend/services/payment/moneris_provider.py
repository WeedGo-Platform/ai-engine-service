"""
Moneris Payment Provider Implementation
Canada's leading payment processor integration
"""

import aiohttp
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from datetime import datetime
from uuid import UUID
import logging
import hashlib
import asyncio
from enum import Enum

from services.payment.base import (
    BasePaymentProvider, PaymentRequest, PaymentResponse,
    PaymentStatus, PaymentError
)

logger = logging.getLogger(__name__)


class MonerisEnvironment(Enum):
    TEST = "https://esqa.moneris.com/gateway2/servlet/MpgRequest"
    PRODUCTION = "https://www3.moneris.com/gateway2/servlet/MpgRequest"


class MonerisResponseCode:
    """Moneris response code mappings"""
    APPROVED_CODES = ['000', '001', '002', '003', '004', '005', '006', '007', '008', '009', '010', '023', '024', '025', '026', '027', '028', '029']
    DECLINED_CODES = ['050', '051', '052', '053', '054', '055', '056', '057', '058', '059', '060', '061', '062', '063', '064', '065', '066', '067', '068', '069', '070', '071', '072', '073', '074', '075', '076', '077', '078', '079', '080', '081', '082', '083', '084', '085', '086', '087', '088', '089', '090', '091', '092', '093', '094', '095', '096', '097', '098', '099']
    
    RESPONSE_MESSAGES = {
        '000': 'Approved',
        '001': 'Approved with ID',
        '050': 'Declined',
        '051': 'Expired card',
        '052': 'Insufficient funds',
        '053': 'Card reported lost',
        '054': 'Card reported stolen',
        '055': 'Transaction not permitted',
        '056': 'Card not accepted',
        '057': 'Invalid amount',
        '058': 'Invalid card number',
        '059': 'Invalid expiry date',
        '060': 'Invalid CVV',
        '476': 'Declined - Account closed',
        '481': 'Declined - Cancelled card',
        '482': 'Declined - Blocked card',
        '483': 'Declined - Fraudulent',
        '484': 'Declined - Pick up card',
        '485': 'Declined - Refer to issuer',
        '486': 'Declined - System error',
        '487': 'Declined - Contact acquirer',
        '489': 'Declined - Do not honour',
        '490': 'Declined - Invalid PIN',
        '800': 'Bad request',
        '801': 'Internal error',
        '802': 'Invalid request',
        '877': 'Invalid response',
        '878': 'Timeout',
        '879': 'System unavailable',
        '880': 'Invalid transaction',
        '881': 'Transaction failed',
        '900': 'Global error'
    }


class MonerisProvider(BasePaymentProvider):
    """Moneris payment provider implementation"""
    
    def __init__(self, provider_config: Dict[str, Any]):
        super().__init__(provider_config)
        self.store_id = provider_config.get('store_id')
        self.api_token = provider_config.get('api_token')
        self.country_code = provider_config.get('country_code', 'CA')
        self.processing_country = provider_config.get('processing_country', 'CA')
        self.environment_url = (
            MonerisEnvironment.PRODUCTION.value 
            if self.environment == 'production' 
            else MonerisEnvironment.TEST.value
        )
        self.timeout = provider_config.get('timeout', 30)
        self.max_retries = provider_config.get('max_retries', 3)
        self.session = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with connection pooling"""
        if not self.session:
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                ttl_dns_cache=300
            )
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self.session
    
    def _build_xml_request(self, transaction_type: str, params: Dict[str, Any]) -> str:
        """Build XML request for Moneris API"""
        root = ET.Element('request')
        
        # Add store credentials
        ET.SubElement(root, 'store_id').text = self.store_id
        ET.SubElement(root, 'api_token').text = self.api_token
        
        # Add transaction
        transaction = ET.SubElement(root, transaction_type)
        for key, value in params.items():
            if value is not None:
                ET.SubElement(transaction, key).text = str(value)
        
        # Add processing country
        ET.SubElement(transaction, 'crypt_type').text = '7'  # SSL enabled merchant
        
        return ET.tostring(root, encoding='unicode')
    
    def _parse_xml_response(self, xml_response: str) -> Dict[str, Any]:
        """Parse XML response from Moneris API"""
        try:
            root = ET.fromstring(xml_response)
            receipt = root.find('receipt')
            
            if receipt is None:
                return {'error': 'Invalid response format'}
            
            response = {}
            for child in receipt:
                response[child.tag] = child.text
            
            return response
        except ET.ParseError as e:
            logger.error(f"Failed to parse Moneris response: {e}")
            return {'error': 'Failed to parse response'}
    
    async def _send_request(self, transaction_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send request to Moneris API with retry logic"""
        session = await self._get_session()
        xml_request = self._build_xml_request(transaction_type, params)
        
        # Log request (without sensitive data)
        safe_params = {k: v for k, v in params.items() if k not in ['pan', 'cvd', 'api_token']}
        logger.info(f"Moneris request - Type: {transaction_type}, Params: {safe_params}")
        
        for attempt in range(self.max_retries):
            try:
                async with session.post(
                    self.environment_url,
                    data=xml_request,
                    headers={'Content-Type': 'text/xml'},
                    ssl=True
                ) as response:
                    if response.status == 200:
                        xml_response = await response.text()
                        return self._parse_xml_response(xml_response)
                    else:
                        logger.warning(f"Moneris API returned status {response.status}")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                        
            except asyncio.TimeoutError:
                logger.warning(f"Moneris request timeout (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                continue
            except Exception as e:
                logger.error(f"Moneris request error: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                continue
        
        return {'error': 'Failed after maximum retries'}
    
    def _validate_response(self, response: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate Moneris response and return success status, error code, and message"""
        if 'error' in response:
            return False, 'SYSTEM_ERROR', response['error']
        
        response_code = response.get('ResponseCode', '999')
        
        if response_code in MonerisResponseCode.APPROVED_CODES:
            return True, None, None
        
        error_message = MonerisResponseCode.RESPONSE_MESSAGES.get(
            response_code,
            f'Transaction declined (Code: {response_code})'
        )
        
        return False, response_code, error_message
    
    async def charge(self, request: PaymentRequest) -> PaymentResponse:
        """Process a payment charge through Moneris"""
        try:
            # Generate unique order ID for Moneris (max 50 chars)
            order_id = f"WG-{request.order_id or UUID()}"[:50]
            
            # Build purchase request
            params = {
                'order_id': order_id,
                'amount': self.format_amount(request.amount),
                'pan': request.metadata.get('card_number'),  # Should be tokenized in production
                'expdate': request.metadata.get('exp_date'),  # YYMM format
                'crypt_type': '7',
                'dynamic_descriptor': request.description[:20] if request.description else 'WeedGo Purchase'
            }
            
            # Add CVV if provided
            if request.metadata.get('cvv'):
                params['cvd_indicator'] = '1'
                params['cvd_value'] = request.metadata.get('cvv')
            
            # Add customer info if available
            if request.billing_address:
                params['billing'] = {
                    'first_name': request.billing_address.get('first_name', ''),
                    'last_name': request.billing_address.get('last_name', ''),
                    'address': request.billing_address.get('street', ''),
                    'city': request.billing_address.get('city', ''),
                    'province': request.billing_address.get('province', ''),
                    'postal_code': request.billing_address.get('postal_code', ''),
                    'country': request.billing_address.get('country', 'Canada')
                }
            
            # Send purchase request
            response = await self._send_request('purchase', params)
            
            # Validate response
            success, error_code, error_message = self._validate_response(response)
            
            # Map to standard response
            return PaymentResponse(
                transaction_id=order_id,
                status=PaymentStatus.COMPLETED if success else PaymentStatus.FAILED,
                amount=request.amount,
                currency=request.currency,
                provider_transaction_id=response.get('ReferenceNum'),
                error_code=error_code,
                error_message=error_message,
                metadata={
                    'auth_code': response.get('AuthCode'),
                    'response_code': response.get('ResponseCode'),
                    'iso_code': response.get('ISO'),
                    'card_type': response.get('CardType'),
                    'transaction_time': response.get('TransTime'),
                    'transaction_date': response.get('TransDate')
                }
            )
            
        except Exception as e:
            logger.error(f"Moneris charge error: {e}")
            raise PaymentError(
                message="Payment processing failed",
                error_code="PROVIDER_ERROR",
                provider_error=str(e)
            )
    
    async def refund(
        self, 
        transaction_id: str, 
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> PaymentResponse:
        """Process a refund through Moneris"""
        try:
            # Build refund request
            params = {
                'order_id': transaction_id,
                'amount': self.format_amount(amount) if amount else None,
                'crypt_type': '7'
            }
            
            # For Moneris, we need the original transaction reference
            # This should be stored from the original transaction
            # For now, we'll use the transaction_id
            params['txn_number'] = transaction_id
            
            # Send refund request
            response = await self._send_request('refund', params)
            
            # Validate response
            success, error_code, error_message = self._validate_response(response)
            
            return PaymentResponse(
                transaction_id=f"REF-{transaction_id}",
                status=PaymentStatus.REFUNDED if success else PaymentStatus.FAILED,
                amount=amount or Decimal('0'),
                currency='CAD',
                provider_transaction_id=response.get('ReferenceNum'),
                error_code=error_code,
                error_message=error_message,
                metadata={
                    'response_code': response.get('ResponseCode'),
                    'auth_code': response.get('AuthCode')
                }
            )
            
        except Exception as e:
            logger.error(f"Moneris refund error: {e}")
            raise PaymentError(
                message="Refund processing failed",
                error_code="PROVIDER_ERROR",
                provider_error=str(e)
            )
    
    async def void(self, transaction_id: str) -> PaymentResponse:
        """Void a transaction through Moneris"""
        try:
            params = {
                'order_id': transaction_id,
                'txn_number': transaction_id,
                'crypt_type': '7'
            }
            
            response = await self._send_request('purchasecorrection', params)
            
            success, error_code, error_message = self._validate_response(response)
            
            return PaymentResponse(
                transaction_id=f"VOID-{transaction_id}",
                status=PaymentStatus.CANCELLED if success else PaymentStatus.FAILED,
                amount=Decimal('0'),
                currency='CAD',
                provider_transaction_id=response.get('ReferenceNum'),
                error_code=error_code,
                error_message=error_message
            )
            
        except Exception as e:
            logger.error(f"Moneris void error: {e}")
            raise PaymentError(
                message="Void processing failed",
                error_code="PROVIDER_ERROR",
                provider_error=str(e)
            )
    
    async def get_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """Get transaction details from Moneris"""
        try:
            params = {
                'order_id': transaction_id,
                'txn_number': transaction_id
            }
            
            response = await self._send_request('txn_inquiry', params)
            
            return {
                'transaction_id': transaction_id,
                'status': response.get('ResponseCode'),
                'amount': self.parse_amount(int(response.get('TransAmount', 0))),
                'card_type': response.get('CardType'),
                'auth_code': response.get('AuthCode'),
                'reference_number': response.get('ReferenceNum'),
                'response_message': MonerisResponseCode.RESPONSE_MESSAGES.get(
                    response.get('ResponseCode', ''),
                    'Unknown'
                )
            }
            
        except Exception as e:
            logger.error(f"Moneris transaction inquiry error: {e}")
            return {'error': str(e)}
    
    async def tokenize_payment_method(
        self, 
        payment_data: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Tokenize payment method using Moneris Vault"""
        try:
            # Generate data key for Moneris Vault
            data_key = f"WG-{UUID()}"[:50]
            
            params = {
                'data_key': data_key,
                'pan': payment_data['card_number'],
                'expdate': payment_data['exp_date'],  # YYMM format
                'crypt_type': '7'
            }
            
            # Add customer info if available
            if payment_data.get('billing_address'):
                params.update({
                    'avs_street_number': payment_data['billing_address'].get('street_number', ''),
                    'avs_street_name': payment_data['billing_address'].get('street', ''),
                    'avs_zipcode': payment_data['billing_address'].get('postal_code', '')
                })
            
            # Send vault add request
            response = await self._send_request('res_add_cc', params)
            
            success, error_code, error_message = self._validate_response(response)
            
            if not success:
                raise PaymentError(
                    message="Failed to tokenize payment method",
                    error_code=error_code,
                    provider_error=error_message
                )
            
            # Return token and metadata
            metadata = {
                'data_key': data_key,
                'card_type': response.get('CardType'),
                'masked_pan': response.get('MaskedPan'),
                'exp_date': payment_data['exp_date']
            }
            
            return data_key, metadata
            
        except Exception as e:
            logger.error(f"Moneris tokenization error: {e}")
            raise PaymentError(
                message="Failed to save payment method",
                error_code="TOKENIZATION_ERROR",
                provider_error=str(e)
            )
    
    async def delete_payment_method(self, token: str) -> bool:
        """Delete tokenized payment method from Moneris Vault"""
        try:
            params = {
                'data_key': token
            }
            
            response = await self._send_request('res_delete', params)
            
            success, _, _ = self._validate_response(response)
            
            return success
            
        except Exception as e:
            logger.error(f"Moneris vault delete error: {e}")
            return False
    
    async def pre_authorize(self, request: PaymentRequest) -> PaymentResponse:
        """Pre-authorize a payment (hold funds)"""
        try:
            order_id = f"WG-{request.order_id or UUID()}"[:50]
            
            params = {
                'order_id': order_id,
                'amount': self.format_amount(request.amount),
                'pan': request.metadata.get('card_number'),
                'expdate': request.metadata.get('exp_date'),
                'crypt_type': '7'
            }
            
            response = await self._send_request('preauth', params)
            
            success, error_code, error_message = self._validate_response(response)
            
            return PaymentResponse(
                transaction_id=order_id,
                status=PaymentStatus.PENDING if success else PaymentStatus.FAILED,
                amount=request.amount,
                currency=request.currency,
                provider_transaction_id=response.get('ReferenceNum'),
                error_code=error_code,
                error_message=error_message,
                metadata={
                    'auth_code': response.get('AuthCode'),
                    'response_code': response.get('ResponseCode')
                }
            )
            
        except Exception as e:
            logger.error(f"Moneris pre-auth error: {e}")
            raise PaymentError(
                message="Pre-authorization failed",
                error_code="PROVIDER_ERROR",
                provider_error=str(e)
            )
    
    async def capture(
        self, 
        transaction_id: str, 
        amount: Optional[Decimal] = None
    ) -> PaymentResponse:
        """Capture a pre-authorized payment"""
        try:
            params = {
                'order_id': transaction_id,
                'comp_amount': self.format_amount(amount) if amount else None,
                'txn_number': transaction_id,
                'crypt_type': '7'
            }
            
            response = await self._send_request('completion', params)
            
            success, error_code, error_message = self._validate_response(response)
            
            return PaymentResponse(
                transaction_id=f"CAP-{transaction_id}",
                status=PaymentStatus.COMPLETED if success else PaymentStatus.FAILED,
                amount=amount or Decimal('0'),
                currency='CAD',
                provider_transaction_id=response.get('ReferenceNum'),
                error_code=error_code,
                error_message=error_message
            )
            
        except Exception as e:
            logger.error(f"Moneris capture error: {e}")
            raise PaymentError(
                message="Capture failed",
                error_code="PROVIDER_ERROR",
                provider_error=str(e)
            )
    
    async def validate_webhook(
        self, 
        payload: bytes, 
        signature: str
    ) -> bool:
        """Validate webhook signature from Moneris"""
        # Moneris uses HMAC-SHA256 for webhook signatures
        expected = hashlib.sha256(
            f"{self.webhook_secret}{payload.decode()}".encode()
        ).hexdigest()
        
        return expected == signature
    
    async def process_webhook(
        self, 
        event_type: str, 
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process webhook event from Moneris"""
        logger.info(f"Processing Moneris webhook: {event_type}")
        
        # Map Moneris events to standard events
        event_mapping = {
            'payment_success': 'payment.completed',
            'payment_failed': 'payment.failed',
            'refund_success': 'refund.completed',
            'chargeback': 'dispute.created'
        }
        
        standard_event = event_mapping.get(event_type, event_type)
        
        return {
            'event': standard_event,
            'transaction_id': payload.get('order_id'),
            'amount': self.parse_amount(int(payload.get('amount', 0))),
            'status': payload.get('status'),
            'metadata': payload
        }
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    def __del__(self):
        """Cleanup on deletion"""
        if self.session and not self.session.closed:
            asyncio.create_task(self.close())