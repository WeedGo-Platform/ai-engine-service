"""
Base Payment Service Abstraction
Provides a unified interface for all payment providers
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from datetime import datetime
from uuid import UUID
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PaymentStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentMethodType(Enum):
    CARD = "card"
    BANK_ACCOUNT = "bank_account"
    INTERAC = "interac"
    WALLET = "wallet"


class TransactionType(Enum):
    CHARGE = "charge"
    REFUND = "refund"
    PARTIAL_REFUND = "partial_refund"
    VOID = "void"
    PRE_AUTH = "pre_auth"
    CAPTURE = "capture"


class PaymentError(Exception):
    """Base exception for payment errors"""
    def __init__(self, message: str, error_code: Optional[str] = None, provider_error: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        self.provider_error = provider_error
        super().__init__(self.message)


class PaymentRequest:
    """Standard payment request structure"""
    def __init__(
        self,
        amount: Decimal,
        currency: str = "CAD",
        description: Optional[str] = None,
        order_id: Optional[UUID] = None,
        customer_id: Optional[UUID] = None,
        payment_method_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
        billing_address: Optional[Dict[str, str]] = None,
        shipping_address: Optional[Dict[str, str]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        self.amount = amount
        self.currency = currency
        self.description = description
        self.order_id = order_id
        self.customer_id = customer_id
        self.payment_method_id = payment_method_id
        self.metadata = metadata or {}
        self.billing_address = billing_address
        self.shipping_address = shipping_address
        self.ip_address = ip_address
        self.user_agent = user_agent


class PaymentResponse:
    """Standard payment response structure"""
    def __init__(
        self,
        transaction_id: str,
        status: PaymentStatus,
        amount: Decimal,
        currency: str = "CAD",
        provider_transaction_id: Optional[str] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None
    ):
        self.transaction_id = transaction_id
        self.status = status
        self.amount = amount
        self.currency = currency
        self.provider_transaction_id = provider_transaction_id
        self.error_code = error_code
        self.error_message = error_message
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.utcnow()


class PaymentMethod:
    """Payment method information"""
    def __init__(
        self,
        id: UUID,
        type: PaymentMethodType,
        display_name: str,
        is_default: bool = False,
        card_brand: Optional[str] = None,
        card_last_four: Optional[str] = None,
        exp_month: Optional[int] = None,
        exp_year: Optional[int] = None,
        bank_name: Optional[str] = None,
        account_last_four: Optional[str] = None
    ):
        self.id = id
        self.type = type
        self.display_name = display_name
        self.is_default = is_default
        self.card_brand = card_brand
        self.card_last_four = card_last_four
        self.exp_month = exp_month
        self.exp_year = exp_year
        self.bank_name = bank_name
        self.account_last_four = account_last_four


class BasePaymentProvider(ABC):
    """Abstract base class for payment providers"""
    
    def __init__(self, provider_config: Dict[str, Any]):
        self.provider_name = self.__class__.__name__.replace('Provider', '')
        self.config = provider_config
        self.api_key = provider_config.get('api_key')
        self.merchant_id = provider_config.get('merchant_id')
        self.environment = provider_config.get('environment', 'sandbox')
        self.webhook_secret = provider_config.get('webhook_secret')
        self.logger = logging.getLogger(f"{__name__}.{self.provider_name}")
    
    @abstractmethod
    async def charge(
        self,
        amount: float,
        currency: str = "CAD",
        payment_method_token: str = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a payment charge.

        Args:
            amount: Payment amount (as float)
            currency: Currency code (default: CAD)
            payment_method_token: Tokenized payment method
            metadata: Additional metadata

        Returns:
            Dict with transaction_id, status, and provider response
        """
        pass

    @abstractmethod
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
            transaction_id: Provider's original transaction ID
            amount: Refund amount (as float)
            currency: Currency code (default: CAD)
            reason: Reason for refund

        Returns:
            Dict with refund_id, status, and provider response
        """
        pass
    
    @abstractmethod
    async def void(self, transaction_id: str) -> PaymentResponse:
        """Void a transaction"""
        pass
    
    @abstractmethod
    async def get_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """Get transaction details"""
        pass
    
    @abstractmethod
    async def tokenize_payment_method(
        self, 
        payment_data: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Tokenize payment method and return token + metadata"""
        pass
    
    @abstractmethod
    async def delete_payment_method(self, token: str) -> bool:
        """Delete a tokenized payment method"""
        pass
    
    @abstractmethod
    async def validate_webhook(
        self, 
        payload: bytes, 
        signature: str
    ) -> bool:
        """Validate webhook signature"""
        pass
    
    @abstractmethod
    async def process_webhook(
        self, 
        event_type: str, 
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process webhook event"""
        pass
    
    # Optional methods with default implementations
    
    async def pre_authorize(self, request: PaymentRequest) -> PaymentResponse:
        """Pre-authorize a payment (hold funds)"""
        raise NotImplementedError(f"{self.provider_name} does not support pre-authorization")
    
    async def capture(
        self, 
        transaction_id: str, 
        amount: Optional[Decimal] = None
    ) -> PaymentResponse:
        """Capture a pre-authorized payment"""
        raise NotImplementedError(f"{self.provider_name} does not support capture")
    
    async def create_subscription(
        self,
        customer_id: UUID,
        plan_id: str,
        payment_method_id: UUID
    ) -> Dict[str, Any]:
        """Create a recurring subscription"""
        raise NotImplementedError(f"{self.provider_name} does not support subscriptions")
    
    async def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel a subscription"""
        raise NotImplementedError(f"{self.provider_name} does not support subscriptions")
    
    async def get_settlement_report(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get settlement/batch report"""
        raise NotImplementedError(f"{self.provider_name} does not support settlement reports")
    
    def format_amount(self, amount: Decimal) -> int:
        """Convert decimal amount to provider's expected format (usually cents)"""
        return int(amount * 100)
    
    def parse_amount(self, amount: int) -> Decimal:
        """Convert provider's amount format back to decimal"""
        return Decimal(amount) / 100
    
    def get_supported_currencies(self) -> List[str]:
        """Get list of supported currencies"""
        return self.config.get('supported_currencies', ['CAD'])
    
    def get_supported_card_types(self) -> List[str]:
        """Get list of supported card types"""
        return self.config.get('supported_card_types', ['visa', 'mastercard', 'amex'])
    
    def is_test_mode(self) -> bool:
        """Check if provider is in test mode"""
        return self.environment != 'production'
    
    def get_dashboard_url(self, transaction_id: str) -> str:
        """Get URL to view transaction in provider's dashboard"""
        return f"https://{self.provider_name.lower()}.com/dashboard/transactions/{transaction_id}"