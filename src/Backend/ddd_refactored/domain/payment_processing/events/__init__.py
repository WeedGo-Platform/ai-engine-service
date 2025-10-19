"""
Payment Processing Domain Events

Events that represent significant business occurrences in the payment domain.
These events can trigger side effects like notifications, analytics, webhooks, etc.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from ..value_objects import Money, PaymentStatus


# Base domain event
@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """Base class for all domain events."""

    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    event_type: str = field(init=False, default="")

    def __post_init__(self):
        """Set event_type from class name."""
        object.__setattr__(self, 'event_type', self.__class__.__name__)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'occurred_at': self.occurred_at.isoformat(),
        }


# Payment Transaction Events

@dataclass(frozen=True)
class PaymentCreated(DomainEvent):
    """
    Raised when a new payment transaction is created.

    Triggers:
    - Analytics tracking
    - Audit logging
    - Real-time dashboard updates
    """

    # Required fields must have defaults to avoid dataclass ordering issues
    transaction_id: UUID = None  # type: ignore
    transaction_reference: str = None  # type: ignore
    store_id: UUID = None  # type: ignore
    amount: Money = None  # type: ignore
    order_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    provider_type: Optional[str] = None

    def __post_init__(self):
        """Validate required fields and set event_type."""
        # Validate required fields
        if not self.transaction_id:
            raise ValueError("transaction_id is required")
        if not self.transaction_reference:
            raise ValueError("transaction_reference is required")
        if not self.store_id:
            raise ValueError("store_id is required")
        if not self.amount:
            raise ValueError("amount is required")

        # Call parent post_init
        super().__post_init__()

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'transaction_id': str(self.transaction_id),
            'transaction_reference': self.transaction_reference,
            'store_id': str(self.store_id),
            'amount': self.amount.to_dict(),
            'order_id': str(self.order_id) if self.order_id else None,
            'user_id': str(self.user_id) if self.user_id else None,
            'provider_type': self.provider_type,
        })
        return base


@dataclass(frozen=True)
class PaymentProcessing(DomainEvent):
    """
    Raised when payment is submitted to processor.

    Triggers:
    - Update transaction status UI
    - Start timeout monitoring
    """

    transaction_id: UUID
    provider_type: str
    provider_transaction_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'transaction_id': str(self.transaction_id),
            'provider_type': self.provider_type,
            'provider_transaction_id': self.provider_transaction_id,
        })
        return base


@dataclass(frozen=True)
class PaymentCompleted(DomainEvent):
    """
    Raised when payment successfully completes.

    Triggers:
    - Order fulfillment
    - Receipt generation
    - Customer notification
    - Analytics tracking
    - Inventory update
    """

    transaction_id: UUID
    transaction_reference: str
    provider_transaction_id: str
    amount: Money
    store_id: UUID
    order_id: Optional[UUID] = None
    completed_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'transaction_id': str(self.transaction_id),
            'transaction_reference': self.transaction_reference,
            'provider_transaction_id': self.provider_transaction_id,
            'amount': self.amount.to_dict(),
            'store_id': str(self.store_id),
            'order_id': str(self.order_id) if self.order_id else None,
            'completed_at': self.completed_at.isoformat(),
        })
        return base


@dataclass(frozen=True)
class PaymentFailed(DomainEvent):
    """
    Raised when payment fails.

    Triggers:
    - Customer notification
    - Retry suggestion (if transient error)
    - Analytics tracking
    - Fraud monitoring (if suspicious)
    """

    transaction_id: UUID
    transaction_reference: str
    error_code: str
    error_message: str
    amount: Money
    store_id: UUID
    order_id: Optional[UUID] = None
    failed_at: datetime = field(default_factory=datetime.utcnow)
    is_retryable: bool = False

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'transaction_id': str(self.transaction_id),
            'transaction_reference': self.transaction_reference,
            'error_code': self.error_code,
            'error_message': self.error_message,
            'amount': self.amount.to_dict(),
            'store_id': str(self.store_id),
            'order_id': str(self.order_id) if self.order_id else None,
            'failed_at': self.failed_at.isoformat(),
            'is_retryable': self.is_retryable,
        })
        return base


@dataclass(frozen=True)
class PaymentVoided(DomainEvent):
    """
    Raised when payment is voided (cancelled before completion).

    Triggers:
    - Order cancellation
    - Inventory release
    - Customer notification
    """

    transaction_id: UUID
    transaction_reference: str
    amount: Money
    store_id: UUID
    voided_by: Optional[UUID] = None
    voided_at: datetime = field(default_factory=datetime.utcnow)
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'transaction_id': str(self.transaction_id),
            'transaction_reference': self.transaction_reference,
            'amount': self.amount.to_dict(),
            'store_id': str(self.store_id),
            'voided_by': str(self.voided_by) if self.voided_by else None,
            'voided_at': self.voided_at.isoformat(),
            'reason': self.reason,
        })
        return base


# Refund Events

@dataclass(frozen=True)
class RefundRequested(DomainEvent):
    """
    Raised when refund is requested.

    Triggers:
    - Refund approval workflow (if required)
    - Notification to manager
    """

    refund_id: UUID
    transaction_id: UUID
    amount: Money
    reason: Optional[str] = None
    requested_by: Optional[UUID] = None

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'refund_id': str(self.refund_id),
            'transaction_id': str(self.transaction_id),
            'amount': self.amount.to_dict(),
            'reason': self.reason,
            'requested_by': str(self.requested_by) if self.requested_by else None,
        })
        return base


@dataclass(frozen=True)
class RefundProcessed(DomainEvent):
    """
    Raised when refund is successfully processed.

    Triggers:
    - Customer notification
    - Inventory adjustment
    - Analytics tracking
    - Financial reporting update
    """

    refund_id: UUID
    refund_reference: str
    transaction_id: UUID
    amount: Money
    provider_refund_id: str
    processed_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'refund_id': str(self.refund_id),
            'refund_reference': self.refund_reference,
            'transaction_id': str(self.transaction_id),
            'amount': self.amount.to_dict(),
            'provider_refund_id': self.provider_refund_id,
            'processed_at': self.processed_at.isoformat(),
        })
        return base


@dataclass(frozen=True)
class RefundFailed(DomainEvent):
    """
    Raised when refund processing fails.

    Triggers:
    - Manual intervention notification
    - Customer notification
    """

    refund_id: UUID
    transaction_id: UUID
    amount: Money
    error_code: str
    error_message: str
    failed_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'refund_id': str(self.refund_id),
            'transaction_id': str(self.transaction_id),
            'amount': self.amount.to_dict(),
            'error_code': self.error_code,
            'error_message': self.error_message,
            'failed_at': self.failed_at.isoformat(),
        })
        return base


# Webhook Events

@dataclass(frozen=True)
class WebhookReceived(DomainEvent):
    """
    Raised when webhook is received from provider.

    Triggers:
    - Webhook processing queue
    - Signature verification
    """

    webhook_id: UUID
    provider_type: str
    event_type: str
    payload: Dict[str, Any]
    signature: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'webhook_id': str(self.webhook_id),
            'provider_type': self.provider_type,
            'event_type': self.event_type,
            'payload': self.payload,
            'signature': self.signature,
        })
        return base


@dataclass(frozen=True)
class WebhookProcessed(DomainEvent):
    """
    Raised when webhook is successfully processed.

    Triggers:
    - Analytics tracking
    - Monitoring/alerting
    """

    webhook_id: UUID
    provider_type: str
    event_type: str
    transaction_id: Optional[UUID] = None
    processed_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'webhook_id': str(self.webhook_id),
            'provider_type': self.provider_type,
            'event_type': self.event_type,
            'transaction_id': str(self.transaction_id) if self.transaction_id else None,
            'processed_at': self.processed_at.isoformat(),
        })
        return base


# Payment Method Events

@dataclass(frozen=True)
class PaymentMethodAdded(DomainEvent):
    """
    Raised when new payment method is added.

    Triggers:
    - Customer notification
    - Analytics tracking
    """

    payment_method_id: UUID
    user_id: UUID
    payment_type: str
    is_default: bool = False

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'payment_method_id': str(self.payment_method_id),
            'user_id': str(self.user_id),
            'payment_type': self.payment_type,
            'is_default': self.is_default,
        })
        return base


@dataclass(frozen=True)
class PaymentMethodRemoved(DomainEvent):
    """
    Raised when payment method is removed.

    Triggers:
    - Customer notification
    - Analytics tracking
    """

    payment_method_id: UUID
    user_id: UUID
    removed_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'payment_method_id': str(self.payment_method_id),
            'user_id': str(self.user_id),
            'removed_at': self.removed_at.isoformat(),
        })
        return base


__all__ = [
    # Base
    'DomainEvent',

    # Payment transaction events
    'PaymentCreated',
    'PaymentProcessing',
    'PaymentCompleted',
    'PaymentFailed',
    'PaymentVoided',

    # Refund events
    'RefundRequested',
    'RefundProcessed',
    'RefundFailed',

    # Webhook events
    'WebhookReceived',
    'WebhookProcessed',

    # Payment method events
    'PaymentMethodAdded',
    'PaymentMethodRemoved',
]
