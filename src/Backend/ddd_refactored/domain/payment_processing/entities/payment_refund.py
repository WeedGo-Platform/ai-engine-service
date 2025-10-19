"""
PaymentRefund Entity

Represents a refund transaction for a payment.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from ..value_objects import Money, PaymentStatus
from ..events import RefundProcessed, RefundFailed
from ..exceptions import InvalidTransactionStateError


@dataclass
class PaymentRefund:
    """
    Entity representing a payment refund.

    Business Rules:
    - Refund must be linked to an original transaction
    - Refund amount must be positive
    - Refund reference must be unique
    - Once processed, refund cannot be modified
    """

    # Identity
    id: UUID = field(default_factory=uuid4)
    refund_reference: str = field(default_factory=lambda: f"REF-{uuid4().hex[:12].upper()}")

    # Relationships
    transaction_id: UUID = field(default=None)

    # Refund details
    amount: Money = field(default=None)
    reason: Optional[str] = None
    status: str = 'pending'  # 'pending', 'processing', 'completed', 'failed'

    # Provider details
    provider_refund_id: Optional[str] = None
    provider_response: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    # Tracking
    created_by: Optional[UUID] = None
    notes: Optional[str] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Domain events (not persisted)
    _domain_events: list = field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        """Validate invariants after initialization."""
        if self.transaction_id is None:
            raise ValueError("transaction_id is required")
        if self.amount is None:
            raise ValueError("amount is required")
        if self.amount.amount <= 0:
            raise ValueError(f"Refund amount must be positive, got: {self.amount}")

    def mark_as_processing(self) -> None:
        """Mark refund as being processed."""
        if self.status not in ['pending']:
            raise InvalidTransactionStateError(
                f"Cannot mark refund as processing in {self.status} status"
            )

        self.status = 'processing'
        self.processed_at = datetime.utcnow()

    def complete(
        self,
        provider_refund_id: str,
        provider_response: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Mark refund as successfully completed.

        Args:
            provider_refund_id: Provider's refund identifier
            provider_response: Full provider response for debugging
        """
        if not provider_refund_id:
            raise ValueError("provider_refund_id is required")

        if self.status not in ['pending', 'processing']:
            raise InvalidTransactionStateError(
                f"Cannot complete refund in {self.status} status"
            )

        self.status = 'completed'
        self.provider_refund_id = provider_refund_id
        self.provider_response = provider_response or {}
        self.completed_at = datetime.utcnow()
        self.error_message = None

        # Raise domain event
        self._raise_event(
            RefundProcessed(
                refund_id=self.id,
                refund_reference=self.refund_reference,
                transaction_id=self.transaction_id,
                amount=self.amount,
                provider_refund_id=provider_refund_id,
                processed_at=self.completed_at
            )
        )

    def fail(
        self,
        error_message: str,
        provider_response: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Mark refund as failed.

        Args:
            error_message: Human-readable error message
            provider_response: Full provider response for debugging
        """
        if not error_message:
            raise ValueError("error_message is required")

        self.status = 'failed'
        self.error_message = error_message
        self.provider_response = provider_response or {}
        self.completed_at = datetime.utcnow()

        # Raise domain event
        self._raise_event(
            RefundFailed(
                refund_id=self.id,
                transaction_id=self.transaction_id,
                amount=self.amount,
                error_code='REFUND_FAILED',
                error_message=error_message,
                failed_at=self.completed_at
            )
        )

    def _raise_event(self, event) -> None:
        """Add domain event to internal event list."""
        self._domain_events.append(event)

    @property
    def domain_events(self) -> list:
        """Get domain events for this entity."""
        return self._domain_events.copy()

    def clear_events(self) -> None:
        """Clear domain events after they've been published."""
        self._domain_events.clear()

    @property
    def is_completed(self) -> bool:
        """Check if refund is completed."""
        return self.status == 'completed'

    @property
    def is_pending(self) -> bool:
        """Check if refund is pending."""
        return self.status == 'pending'

    @property
    def is_failed(self) -> bool:
        """Check if refund failed."""
        return self.status == 'failed'

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': str(self.id),
            'refund_reference': self.refund_reference,
            'transaction_id': str(self.transaction_id),
            'amount': self.amount.to_dict(),
            'reason': self.reason,
            'status': self.status,
            'provider_refund_id': self.provider_refund_id,
            'provider_response': self.provider_response,
            'error_message': self.error_message,
            'created_by': str(self.created_by) if self.created_by else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"PaymentRefund({self.refund_reference}, {self.amount}, {self.status})"

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"PaymentRefund("
            f"id={self.id}, "
            f"reference={self.refund_reference}, "
            f"amount={self.amount}, "
            f"status={self.status}"
            f")"
        )
