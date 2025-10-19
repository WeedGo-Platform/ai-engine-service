"""
Payment Processing Value Objects
Following DDD Architecture Document Section 2.9
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional
from datetime import datetime

from ....shared.domain_base import ValueObject


class PaymentMethod(str, Enum):
    """Payment method type"""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    CASH = "cash"
    INTERAC = "interac"
    E_TRANSFER = "e_transfer"
    GIFT_CARD = "gift_card"
    STORE_CREDIT = "store_credit"
    CRYPTO = "crypto"


class PaymentStatus(str, Enum):
    """Payment transaction status"""
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    PARTIALLY_REFUNDED = "partially_refunded"
    REFUNDED = "refunded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PaymentProvider(str, Enum):
    """Payment gateway/processor"""
    STRIPE = "stripe"
    SQUARE = "square"
    MONERIS = "moneris"
    BAMBORA = "bambora"
    PAYPAL = "paypal"
    MANUAL = "manual"  # Cash, in-store
    INTERNAL = "internal"  # Store credit, gift cards


class RefundReason(str, Enum):
    """Reason for refund"""
    CUSTOMER_REQUEST = "customer_request"
    OUT_OF_STOCK = "out_of_stock"
    DUPLICATE_CHARGE = "duplicate_charge"
    FRAUDULENT = "fraudulent"
    ORDER_CANCELLED = "order_cancelled"
    PRODUCT_DEFECT = "product_defect"
    PRICING_ERROR = "pricing_error"
    OTHER = "other"


class CardType(str, Enum):
    """Credit/debit card type"""
    VISA = "visa"
    MASTERCARD = "mastercard"
    AMEX = "amex"
    DISCOVER = "discover"
    INTERAC = "interac"
    OTHER = "other"


@dataclass(frozen=True)
class Money(ValueObject):
    """
    Money value object with currency
    """
    amount: Decimal
    currency: str = "CAD"

    def __post_init__(self):
        """Validate money"""
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")

        if not self.currency:
            raise ValueError("Currency is required")

        # Ensure proper decimal precision
        if self.amount.as_tuple().exponent < -2:
            raise ValueError("Amount can have at most 2 decimal places")

    def add(self, other: 'Money') -> 'Money':
        """Add two money amounts"""
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")

        return Money(amount=self.amount + other.amount, currency=self.currency)

    def subtract(self, other: 'Money') -> 'Money':
        """Subtract money amounts"""
        if self.currency != other.currency:
            raise ValueError("Cannot subtract different currencies")

        result = self.amount - other.amount
        if result < 0:
            raise ValueError("Result cannot be negative")

        return Money(amount=result, currency=self.currency)

    def multiply(self, multiplier: Decimal) -> 'Money':
        """Multiply money amount"""
        return Money(amount=self.amount * multiplier, currency=self.currency)

    def is_zero(self) -> bool:
        """Check if amount is zero"""
        return self.amount == Decimal("0")

    def is_positive(self) -> bool:
        """Check if amount is positive"""
        return self.amount > Decimal("0")

    def __str__(self) -> str:
        return f"{self.currency} {self.amount:.2f}"


@dataclass(frozen=True)
class CardDetails(ValueObject):
    """
    Credit/debit card details (PCI-compliant - store only tokenized data)
    Never store full card numbers or CVV!
    """
    # Tokenized card reference from payment gateway
    card_token: str

    # Safe to store
    last_four_digits: str
    card_type: CardType
    expiry_month: int
    expiry_year: int
    cardholder_name: str

    # Billing address
    billing_postal_code: str

    def __post_init__(self):
        """Validate card details"""
        if not self.card_token:
            raise ValueError("Card token is required")

        if len(self.last_four_digits) != 4 or not self.last_four_digits.isdigit():
            raise ValueError("Last four digits must be exactly 4 digits")

        if self.expiry_month < 1 or self.expiry_month > 12:
            raise ValueError("Expiry month must be between 1 and 12")

        current_year = datetime.utcnow().year
        if self.expiry_year < current_year:
            raise ValueError("Card is expired")

        if not self.cardholder_name:
            raise ValueError("Cardholder name is required")

    def is_expired(self) -> bool:
        """Check if card is expired"""
        now = datetime.utcnow()
        if self.expiry_year < now.year:
            return True

        if self.expiry_year == now.year and self.expiry_month < now.month:
            return True

        return False

    def get_masked_number(self) -> str:
        """Get masked card number for display"""
        return f"**** **** **** {self.last_four_digits}"

    def get_expiry_display(self) -> str:
        """Get formatted expiry date"""
        return f"{self.expiry_month:02d}/{self.expiry_year}"


@dataclass(frozen=True)
class PaymentGatewayResponse(ValueObject):
    """
    Response from payment gateway
    """
    gateway_transaction_id: str
    status_code: str
    status_message: str
    is_success: bool

    # Authorization details
    authorization_code: Optional[str] = None
    avs_result: Optional[str] = None  # Address Verification System
    cvv_result: Optional[str] = None  # CVV check result

    # Timestamps
    processed_at: datetime = None

    # Raw response (for debugging/audit)
    raw_response: Optional[dict] = None

    def __post_init__(self):
        """Set default processed_at if not provided"""
        if self.processed_at is None:
            # Can't use field default_factory with frozen dataclass
            # This is a workaround
            object.__setattr__(self, 'processed_at', datetime.utcnow())


@dataclass(frozen=True)
class RefundDetails(ValueObject):
    """
    Details about a refund
    """
    refund_amount: Money
    refund_reason: RefundReason
    refund_notes: Optional[str] = None
    requested_by: Optional[str] = None
    requested_at: datetime = None

    def __post_init__(self):
        """Validate refund details"""
        if not self.refund_amount.is_positive():
            raise ValueError("Refund amount must be positive")

        if self.refund_notes and len(self.refund_notes) > 500:
            raise ValueError("Refund notes cannot exceed 500 characters")

        if self.requested_at is None:
            object.__setattr__(self, 'requested_at', datetime.utcnow())


@dataclass(frozen=True)
class PaymentMethodDetails(ValueObject):
    """
    Details about the payment method used
    """
    payment_method: PaymentMethod
    provider: PaymentProvider

    # Card details (if applicable)
    card_details: Optional[CardDetails] = None

    # Other payment method details
    reference_number: Optional[str] = None
    email: Optional[str] = None  # For PayPal, e-transfer

    def __post_init__(self):
        """Validate payment method details"""
        # Card payments must have card details
        if self.payment_method in [PaymentMethod.CREDIT_CARD, PaymentMethod.DEBIT_CARD]:
            if not self.card_details:
                raise ValueError("Card details required for card payments")

        # Validate card is not expired
        if self.card_details and self.card_details.is_expired():
            raise ValueError("Card is expired")

    def get_display_name(self) -> str:
        """Get human-readable payment method name"""
        if self.card_details:
            return f"{self.card_details.card_type.value.title()} {self.card_details.get_masked_number()}"

        return self.payment_method.value.replace('_', ' ').title()


@dataclass(frozen=True)
class SplitPayment(ValueObject):
    """
    Represents a split payment (e.g., partial card, partial cash)
    """
    payment_method: PaymentMethod
    amount: Money
    sequence: int  # Order of payment in split

    def __post_init__(self):
        """Validate split payment"""
        if not self.amount.is_positive():
            raise ValueError("Split payment amount must be positive")

        if self.sequence < 1:
            raise ValueError("Split payment sequence must be positive")
