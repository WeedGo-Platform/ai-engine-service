"""
PaymentTransaction Aggregate Root

The core entity in the payment processing domain.
Enforces business rules and maintains transactional consistency.

Refactored for store-level payment providers and simplified architecture.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from ..value_objects import Money, PaymentStatus, TransactionReference
from ..events import (
    PaymentCreated,
    PaymentProcessing,
    PaymentCompleted,
    PaymentFailed,
    PaymentVoided,
    RefundRequested,
)
from ..exceptions import (
    InvalidTransactionStateError,
    RefundAmountExceededError,
    RefundNotAllowedError,
    VoidNotAllowedError,
    InvalidAmountError,
)


@dataclass
class PaymentTransaction:
    """
    Aggregate Root for payment transactions.

    Responsibilities:
    - Enforce payment business rules
    - Manage transaction lifecycle
    - Publish domain events
    - Ensure data consistency

    Business Invariants:
    - Transaction reference must be unique
    - Amount must be positive
    - Cannot refund more than transaction amount
    - Cannot void a completed transaction
    - Cannot complete a failed transaction
    - Status transitions must follow valid paths
    """

    # Identity
    id: UUID = field(default_factory=uuid4)
    transaction_reference: TransactionReference = field(default_factory=TransactionReference.generate)

    # Relationships (required)
    store_id: UUID = field(default=None)
    provider_id: UUID = field(default=None)
    store_provider_id: UUID = field(default=None)

    # Relationships (optional)
    order_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    payment_method_id: Optional[UUID] = None

    # Transaction details
    transaction_type: str = 'charge'  # 'charge', 'authorize', 'capture', 'void'
    amount: Money = field(default=None)
    status: PaymentStatus = PaymentStatus.PENDING

    # Provider details
    provider_transaction_id: Optional[str] = None
    provider_response: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    # Security
    idempotency_key: Optional[str] = None
    ip_address: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # Domain events (not persisted)
    _domain_events: List = field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        """Validate invariants after initialization."""
        # Validate required fields
        if self.store_id is None:
            raise ValueError("store_id is required")
        if self.provider_id is None:
            raise ValueError("provider_id is required")
        if self.store_provider_id is None:
            raise ValueError("store_provider_id is required")
        if self.amount is None:
            raise ValueError("amount is required")

        # Validate amount
        if self.amount.amount <= 0:
            raise InvalidAmountError(
                f"Transaction amount must be positive, got: {self.amount}",
                amount=float(self.amount.amount)
            )

        # Validate transaction type
        valid_types = ['charge', 'authorize', 'capture', 'void']
        if self.transaction_type not in valid_types:
            raise ValueError(
                f"Invalid transaction type: {self.transaction_type}. "
                f"Must be one of: {valid_types}"
            )

        # Raise creation event
        self._raise_event(
            PaymentCreated(
                transaction_id=self.id,
                transaction_reference=str(self.transaction_reference),
                store_id=self.store_id,
                amount=self.amount,
                order_id=self.order_id,
                user_id=self.user_id,
                provider_type=None  # Set by application layer
            )
        )

    def begin_processing(self, provider_type: str) -> None:
        """
        Mark transaction as processing (submitted to payment processor).

        Args:
            provider_type: Payment provider type (clover, moneris, interac)

        Raises:
            InvalidTransactionStateError: If transaction not in valid state
        """
        if not self.status.can_transition_to(PaymentStatus.PROCESSING):
            raise InvalidTransactionStateError(
                f"Cannot begin processing transaction in {self.status} status",
                current_state=self.status.value,
                attempted_state=PaymentStatus.PROCESSING.value
            )

        self.status = PaymentStatus.PROCESSING
        self.updated_at = datetime.utcnow()

        self._raise_event(
            PaymentProcessing(
                transaction_id=self.id,
                provider_type=provider_type,
                provider_transaction_id=self.provider_transaction_id
            )
        )

    def complete(
        self,
        provider_transaction_id: str,
        provider_response: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Mark transaction as successfully completed.

        Business rules:
        - Can only complete pending/processing transactions
        - Provider transaction ID is required
        - Sets completed_at timestamp

        Args:
            provider_transaction_id: Provider's transaction identifier
            provider_response: Full provider response for debugging

        Raises:
            InvalidTransactionStateError: If transaction cannot be completed
            ValueError: If provider_transaction_id is missing
        """
        if not provider_transaction_id:
            raise ValueError("provider_transaction_id is required to complete transaction")

        if not self.status.can_transition_to(PaymentStatus.COMPLETED):
            raise InvalidTransactionStateError(
                f"Cannot complete transaction in {self.status} status. "
                f"Only pending/processing transactions can be completed.",
                current_state=self.status.value,
                attempted_state=PaymentStatus.COMPLETED.value
            )

        # Update transaction state
        self.status = PaymentStatus.COMPLETED
        self.provider_transaction_id = provider_transaction_id
        self.provider_response = provider_response or {}
        self.completed_at = datetime.utcnow()
        self.updated_at = self.completed_at

        # Clear any previous error state
        self.error_code = None
        self.error_message = None

        # Raise domain event
        self._raise_event(
            PaymentCompleted(
                transaction_id=self.id,
                transaction_reference=str(self.transaction_reference),
                provider_transaction_id=provider_transaction_id,
                amount=self.amount,
                store_id=self.store_id,
                order_id=self.order_id,
                completed_at=self.completed_at
            )
        )

    def fail(
        self,
        error_code: str,
        error_message: str,
        provider_response: Optional[Dict[str, Any]] = None,
        is_retryable: bool = False
    ) -> None:
        """
        Mark transaction as failed.

        Business rules:
        - Cannot fail an already completed transaction
        - Error code and message are required

        Args:
            error_code: Machine-readable error code
            error_message: Human-readable error message
            provider_response: Full provider response for debugging
            is_retryable: Whether this failure can be retried

        Raises:
            InvalidTransactionStateError: If transaction cannot be failed
            ValueError: If error_code or error_message is missing
        """
        if not error_code:
            raise ValueError("error_code is required")
        if not error_message:
            raise ValueError("error_message is required")

        if not self.status.can_transition_to(PaymentStatus.FAILED):
            raise InvalidTransactionStateError(
                f"Cannot fail transaction in {self.status} status. "
                f"Already completed transactions cannot be marked as failed.",
                current_state=self.status.value,
                attempted_state=PaymentStatus.FAILED.value
            )

        # Update transaction state
        self.status = PaymentStatus.FAILED
        self.error_code = error_code
        self.error_message = error_message
        self.provider_response = provider_response or {}
        self.updated_at = datetime.utcnow()

        # Raise domain event
        self._raise_event(
            PaymentFailed(
                transaction_id=self.id,
                transaction_reference=str(self.transaction_reference),
                error_code=error_code,
                error_message=error_message,
                amount=self.amount,
                store_id=self.store_id,
                order_id=self.order_id,
                failed_at=self.updated_at,
                is_retryable=is_retryable
            )
        )

    def void(self, voided_by: Optional[UUID] = None, reason: Optional[str] = None) -> None:
        """
        Void (cancel) the transaction before completion.

        Business rules:
        - Can only void pending/processing transactions
        - Cannot void completed or failed transactions
        - Voiding is different from refunding (refund happens after completion)

        Args:
            voided_by: User who voided the transaction
            reason: Reason for voiding

        Raises:
            VoidNotAllowedError: If transaction cannot be voided
        """
        if not self.status.can_void():
            raise VoidNotAllowedError(
                f"Cannot void transaction in {self.status} status. "
                f"Only pending/processing transactions can be voided.",
                transaction_id=self.id
            )

        # Update transaction state
        self.status = PaymentStatus.VOIDED
        self.updated_at = datetime.utcnow()

        # Raise domain event
        self._raise_event(
            PaymentVoided(
                transaction_id=self.id,
                transaction_reference=str(self.transaction_reference),
                amount=self.amount,
                store_id=self.store_id,
                voided_by=voided_by,
                voided_at=self.updated_at,
                reason=reason
            )
        )

    def request_refund(
        self,
        refund_amount: Money,
        reason: Optional[str] = None,
        requested_by: Optional[UUID] = None
    ):
        """
        Create a refund request for this transaction.

        Business rules:
        - Can only refund completed transactions
        - Refund amount cannot exceed transaction amount
        - Partial refunds are allowed
        - Full refund changes transaction status to REFUNDED

        Args:
            refund_amount: Amount to refund
            reason: Reason for refund
            requested_by: User requesting the refund

        Returns:
            PaymentRefund entity (imported at runtime to avoid circular dependency)

        Raises:
            RefundNotAllowedError: If refund is not allowed
            RefundAmountExceededError: If refund amount exceeds transaction amount
        """
        # Validate refund is allowed
        if not self.status.can_refund():
            raise RefundNotAllowedError(
                f"Cannot refund transaction in {self.status} status. "
                f"Only completed transactions can be refunded.",
                transaction_id=self.id
            )

        # Validate refund amount
        if refund_amount > self.amount:
            raise RefundAmountExceededError(
                refund_amount=float(refund_amount.amount),
                transaction_amount=float(self.amount.amount)
            )

        # Import here to avoid circular dependency
        from .payment_refund import PaymentRefund

        # Create refund entity
        refund = PaymentRefund(
            transaction_id=self.id,
            amount=refund_amount,
            reason=reason,
            created_by=requested_by
        )

        # Raise domain event
        self._raise_event(
            RefundRequested(
                refund_id=refund.id,
                transaction_id=self.id,
                amount=refund_amount,
                reason=reason,
                requested_by=requested_by
            )
        )

        return refund

    def mark_as_refunded(self) -> None:
        """
        Mark transaction as fully refunded.

        This is called by the application layer after all refunds are processed.
        """
        if self.status != PaymentStatus.COMPLETED:
            raise InvalidTransactionStateError(
                f"Can only mark completed transactions as refunded, current status: {self.status}"
            )

        self.status = PaymentStatus.REFUNDED
        self.updated_at = datetime.utcnow()

    def update_metadata(self, key: str, value: Any) -> None:
        """
        Update transaction metadata.

        Metadata can store arbitrary data like:
        - Customer notes
        - Internal references
        - Custom fields

        Args:
            key: Metadata key
            value: Metadata value (must be JSON-serializable)
        """
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()

    def _raise_event(self, event) -> None:
        """Add domain event to internal event list."""
        self._domain_events.append(event)

    @property
    def domain_events(self) -> List:
        """
        Get domain events for this aggregate.

        Returns:
            Copy of domain events list
        """
        return self._domain_events.copy()

    def clear_events(self) -> None:
        """Clear domain events after they've been published."""
        self._domain_events.clear()

    @property
    def is_successful(self) -> bool:
        """Check if transaction was successful."""
        return self.status.is_successful()

    @property
    def is_in_progress(self) -> bool:
        """Check if transaction is still being processed."""
        return self.status.is_in_progress()

    @property
    def can_be_refunded(self) -> bool:
        """Check if transaction can be refunded."""
        return self.status.can_refund()

    @property
    def can_be_voided(self) -> bool:
        """Check if transaction can be voided."""
        return self.status.can_void()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation suitable for JSON serialization
        """
        return {
            'id': str(self.id),
            'transaction_reference': str(self.transaction_reference),
            'store_id': str(self.store_id),
            'provider_id': str(self.provider_id),
            'store_provider_id': str(self.store_provider_id),
            'order_id': str(self.order_id) if self.order_id else None,
            'user_id': str(self.user_id) if self.user_id else None,
            'payment_method_id': str(self.payment_method_id) if self.payment_method_id else None,
            'transaction_type': self.transaction_type,
            'amount': self.amount.to_dict(),
            'status': self.status.value,
            'provider_transaction_id': self.provider_transaction_id,
            'provider_response': self.provider_response,
            'error_code': self.error_code,
            'error_message': self.error_message,
            'idempotency_key': self.idempotency_key,
            'ip_address': str(self.ip_address) if self.ip_address else None,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }

    def __str__(self) -> str:
        """Human-readable string representation."""
        return (
            f"PaymentTransaction({self.transaction_reference}, "
            f"{self.amount}, {self.status})"
        )

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"PaymentTransaction("
            f"id={self.id}, "
            f"reference={self.transaction_reference}, "
            f"amount={self.amount}, "
            f"status={self.status}"
            f")"
        )
