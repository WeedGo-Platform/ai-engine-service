"""
Payment Domain Exceptions

Business rule violations and payment-specific errors.
"""

from typing import Optional
from uuid import UUID


class PaymentError(Exception):
    """Base exception for all payment-related errors."""

    def __init__(self, message: str, error_code: Optional[str] = None):
        """
        Initialize payment error.

        Args:
            message: Human-readable error message
            error_code: Optional machine-readable error code
        """
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"


class InvalidTransactionStateError(PaymentError):
    """
    Raised when attempting an invalid state transition.

    Example: Trying to complete a transaction that's already failed.
    """

    def __init__(self, message: str, current_state: Optional[str] = None, attempted_state: Optional[str] = None):
        """
        Initialize state error.

        Args:
            message: Error description
            current_state: Current transaction status
            attempted_state: Attempted new status
        """
        self.current_state = current_state
        self.attempted_state = attempted_state
        super().__init__(message, "INVALID_TRANSACTION_STATE")


class InsufficientFundsError(PaymentError):
    """
    Raised when payment fails due to insufficient funds.

    This is a business error, not a technical error.
    """

    def __init__(self, message: str = "Insufficient funds for transaction"):
        super().__init__(message, "INSUFFICIENT_FUNDS")


class RefundAmountExceededError(PaymentError):
    """
    Raised when refund amount exceeds original transaction amount.

    Business rule: Cannot refund more than was charged.
    """

    def __init__(self, refund_amount: float, transaction_amount: float):
        message = (
            f"Refund amount ${refund_amount:.2f} exceeds "
            f"transaction amount ${transaction_amount:.2f}"
        )
        self.refund_amount = refund_amount
        self.transaction_amount = transaction_amount
        super().__init__(message, "REFUND_AMOUNT_EXCEEDED")


class DuplicateTransactionError(PaymentError):
    """
    Raised when attempting to create duplicate transaction.

    Used with idempotency key validation.
    """

    def __init__(self, idempotency_key: str, existing_transaction_id: Optional[UUID] = None):
        message = f"Transaction with idempotency key '{idempotency_key}' already exists"
        self.idempotency_key = idempotency_key
        self.existing_transaction_id = existing_transaction_id
        super().__init__(message, "DUPLICATE_TRANSACTION")


class TransactionNotFoundError(PaymentError):
    """Raised when transaction cannot be found."""

    def __init__(self, transaction_id: Optional[UUID] = None, transaction_reference: Optional[str] = None):
        if transaction_id:
            message = f"Transaction not found: {transaction_id}"
        elif transaction_reference:
            message = f"Transaction not found: {transaction_reference}"
        else:
            message = "Transaction not found"

        self.transaction_id = transaction_id
        self.transaction_reference = transaction_reference
        super().__init__(message, "TRANSACTION_NOT_FOUND")


class PaymentMethodNotFoundError(PaymentError):
    """Raised when payment method cannot be found."""

    def __init__(self, payment_method_id: UUID):
        message = f"Payment method not found: {payment_method_id}"
        self.payment_method_id = payment_method_id
        super().__init__(message, "PAYMENT_METHOD_NOT_FOUND")


class InvalidPaymentMethodError(PaymentError):
    """
    Raised when payment method is invalid or expired.

    Example: Expired credit card, inactive payment method.
    """

    def __init__(self, message: str, payment_method_id: Optional[UUID] = None):
        self.payment_method_id = payment_method_id
        super().__init__(message, "INVALID_PAYMENT_METHOD")


class PaymentDeclinedError(PaymentError):
    """
    Raised when payment is declined by processor.

    This wraps provider-specific decline reasons.
    """

    def __init__(self, message: str, decline_code: Optional[str] = None):
        self.decline_code = decline_code
        super().__init__(message, "PAYMENT_DECLINED")


class RefundNotAllowedError(PaymentError):
    """
    Raised when refund is not allowed for transaction.

    Example: Transaction not completed, already fully refunded.
    """

    def __init__(self, message: str, transaction_id: Optional[UUID] = None):
        self.transaction_id = transaction_id
        super().__init__(message, "REFUND_NOT_ALLOWED")


class VoidNotAllowedError(PaymentError):
    """
    Raised when void is not allowed for transaction.

    Example: Transaction already completed or failed.
    """

    def __init__(self, message: str, transaction_id: Optional[UUID] = None):
        self.transaction_id = transaction_id
        super().__init__(message, "VOID_NOT_ALLOWED")


class InvalidAmountError(PaymentError):
    """
    Raised when payment amount is invalid.

    Example: Negative amount, zero amount for charge.
    """

    def __init__(self, message: str, amount: Optional[float] = None):
        self.amount = amount
        super().__init__(message, "INVALID_AMOUNT")


class CurrencyMismatchError(PaymentError):
    """
    Raised when currencies don't match.

    Example: Trying to refund USD when transaction was CAD.
    """

    def __init__(self, expected_currency: str, actual_currency: str):
        message = f"Currency mismatch: expected {expected_currency}, got {actual_currency}"
        self.expected_currency = expected_currency
        self.actual_currency = actual_currency
        super().__init__(message, "CURRENCY_MISMATCH")


class StoreNotConfiguredError(PaymentError):
    """
    Raised when store doesn't have payment provider configured.

    This is a configuration error that should be resolved by admin.
    """

    def __init__(self, store_id: UUID, provider_type: Optional[str] = None):
        if provider_type:
            message = f"Store {store_id} does not have {provider_type} provider configured"
        else:
            message = f"Store {store_id} does not have any payment providers configured"

        self.store_id = store_id
        self.provider_type = provider_type
        super().__init__(message, "STORE_NOT_CONFIGURED")


class ProviderNotActiveError(PaymentError):
    """Raised when attempting to use inactive payment provider."""

    def __init__(self, provider_id: UUID, provider_name: Optional[str] = None):
        if provider_name:
            message = f"Payment provider '{provider_name}' is not active"
        else:
            message = f"Payment provider {provider_id} is not active"

        self.provider_id = provider_id
        self.provider_name = provider_name
        super().__init__(message, "PROVIDER_NOT_ACTIVE")
