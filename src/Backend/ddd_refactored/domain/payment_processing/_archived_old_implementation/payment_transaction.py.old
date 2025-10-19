"""
PaymentTransaction Aggregate Root
Following DDD Architecture Document Section 2.9
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from ....shared.domain_base import AggregateRoot, DomainEvent, BusinessRuleViolation
from ..value_objects.payment_types import (
    PaymentMethod,
    PaymentStatus,
    PaymentProvider,
    RefundReason,
    Money,
    CardDetails,
    PaymentGatewayResponse,
    RefundDetails,
    PaymentMethodDetails,
    SplitPayment
)


# Domain Events
class PaymentInitiated(DomainEvent):
    payment_id: UUID
    order_id: UUID
    amount: Decimal
    payment_method: PaymentMethod


class PaymentAuthorized(DomainEvent):
    payment_id: UUID
    order_id: UUID
    amount: Decimal
    authorization_code: str
    authorized_at: datetime


class PaymentCaptured(DomainEvent):
    payment_id: UUID
    order_id: UUID
    amount: Decimal
    captured_at: datetime


class PaymentFailed(DomainEvent):
    payment_id: UUID
    order_id: UUID
    failure_reason: str
    failed_at: datetime


class PaymentCancelled(DomainEvent):
    payment_id: UUID
    order_id: UUID
    cancelled_at: datetime
    reason: str


class RefundIssued(DomainEvent):
    payment_id: UUID
    order_id: UUID
    refund_amount: Decimal
    refund_reason: RefundReason
    refunded_at: datetime


class RefundCompleted(DomainEvent):
    payment_id: UUID
    refund_id: UUID
    refund_amount: Decimal
    completed_at: datetime


@dataclass
class Refund:
    """Refund entity within PaymentTransaction aggregate"""
    id: UUID = field(default_factory=uuid4)
    refund_amount: Money = None
    refund_reason: RefundReason = RefundReason.CUSTOMER_REQUEST
    refund_notes: Optional[str] = None

    # Status
    status: str = "pending"  # pending, processing, completed, failed

    # Gateway details
    gateway_refund_id: Optional[str] = None
    gateway_response: Optional[PaymentGatewayResponse] = None

    # Timestamps
    requested_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Who requested
    requested_by: Optional[UUID] = None

    def complete(self, gateway_response: PaymentGatewayResponse):
        """Mark refund as completed"""
        if self.status == "completed":
            raise BusinessRuleViolation("Refund already completed")

        self.status = "completed"
        self.gateway_response = gateway_response
        self.gateway_refund_id = gateway_response.gateway_transaction_id
        self.completed_at = datetime.utcnow()

    def fail(self, reason: str):
        """Mark refund as failed"""
        if self.status == "completed":
            raise BusinessRuleViolation("Cannot fail completed refund")

        self.status = "failed"
        self.refund_notes = f"{self.refund_notes or ''} | Failed: {reason}".strip()
        self.processed_at = datetime.utcnow()


@dataclass
class PaymentTransaction(AggregateRoot):
    """
    PaymentTransaction Aggregate Root - Payment processing
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.9
    """
    # Identifiers
    order_id: UUID = field(default_factory=uuid4)
    store_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    customer_id: Optional[UUID] = None

    # Payment details
    payment_amount: Money = None
    payment_status: PaymentStatus = PaymentStatus.PENDING

    # Payment method
    payment_method_details: Optional[PaymentMethodDetails] = None

    # Split payments (for orders paid with multiple methods)
    split_payments: List[SplitPayment] = field(default_factory=list)
    is_split_payment: bool = False

    # Gateway integration
    payment_provider: PaymentProvider = PaymentProvider.STRIPE
    gateway_transaction_id: Optional[str] = None
    authorization_code: Optional[str] = None

    # Gateway responses
    gateway_responses: List[PaymentGatewayResponse] = field(default_factory=list)

    # Refunds
    refunds: List[Refund] = field(default_factory=list)
    refunded_amount: Money = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    authorized_at: Optional[datetime] = None
    captured_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    # Failure details
    failure_reason: Optional[str] = None
    retry_count: int = 0

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize default values"""
        super().__post_init__()
        if self.refunded_amount is None:
            self.refunded_amount = Money(amount=Decimal("0"), currency="CAD")

    @classmethod
    def create(
        cls,
        order_id: UUID,
        store_id: UUID,
        tenant_id: UUID,
        payment_amount: Money,
        payment_method_details: PaymentMethodDetails,
        customer_id: Optional[UUID] = None
    ) -> 'PaymentTransaction':
        """Factory method to create new payment transaction"""
        if not payment_amount.is_positive():
            raise BusinessRuleViolation("Payment amount must be positive")

        payment = cls(
            order_id=order_id,
            store_id=store_id,
            tenant_id=tenant_id,
            customer_id=customer_id,
            payment_amount=payment_amount,
            payment_method_details=payment_method_details,
            payment_provider=payment_method_details.provider,
            payment_status=PaymentStatus.PENDING
        )

        # Raise creation event
        payment.add_domain_event(PaymentInitiated(
            payment_id=payment.id,
            order_id=order_id,
            amount=payment_amount.amount,
            payment_method=payment_method_details.payment_method
        ))

        return payment

    def authorize(
        self,
        authorization_code: str,
        gateway_response: PaymentGatewayResponse
    ):
        """Authorize the payment (pre-authorization)"""
        if self.payment_status != PaymentStatus.PENDING:
            raise BusinessRuleViolation(f"Cannot authorize {self.payment_status} payment")

        if not gateway_response.is_success:
            raise BusinessRuleViolation("Cannot authorize with failed gateway response")

        self.payment_status = PaymentStatus.AUTHORIZED
        self.authorization_code = authorization_code
        self.gateway_transaction_id = gateway_response.gateway_transaction_id
        self.authorized_at = datetime.utcnow()
        self.gateway_responses.append(gateway_response)

        # Raise event
        self.add_domain_event(PaymentAuthorized(
            payment_id=self.id,
            order_id=self.order_id,
            amount=self.payment_amount.amount,
            authorization_code=authorization_code,
            authorized_at=self.authorized_at
        ))

        self.mark_as_modified()

    def capture(self, gateway_response: PaymentGatewayResponse):
        """Capture the payment (complete the transaction)"""
        if self.payment_status not in [PaymentStatus.PENDING, PaymentStatus.AUTHORIZED]:
            raise BusinessRuleViolation(f"Cannot capture {self.payment_status} payment")

        if not gateway_response.is_success:
            raise BusinessRuleViolation("Cannot capture with failed gateway response")

        self.payment_status = PaymentStatus.CAPTURED
        self.gateway_transaction_id = gateway_response.gateway_transaction_id
        self.captured_at = datetime.utcnow()
        self.gateway_responses.append(gateway_response)

        # Raise event
        self.add_domain_event(PaymentCaptured(
            payment_id=self.id,
            order_id=self.order_id,
            amount=self.payment_amount.amount,
            captured_at=self.captured_at
        ))

        self.mark_as_modified()

    def fail(self, failure_reason: str):
        """Mark payment as failed"""
        if self.payment_status in [PaymentStatus.CAPTURED, PaymentStatus.REFUNDED]:
            raise BusinessRuleViolation(f"Cannot fail {self.payment_status} payment")

        self.payment_status = PaymentStatus.FAILED
        self.failure_reason = failure_reason
        self.failed_at = datetime.utcnow()
        self.retry_count += 1

        # Raise event
        self.add_domain_event(PaymentFailed(
            payment_id=self.id,
            order_id=self.order_id,
            failure_reason=failure_reason,
            failed_at=self.failed_at
        ))

        self.mark_as_modified()

    def cancel(self, reason: str = ""):
        """Cancel the payment"""
        if self.payment_status in [PaymentStatus.CAPTURED, PaymentStatus.REFUNDED]:
            raise BusinessRuleViolation(f"Cannot cancel {self.payment_status} payment")

        self.payment_status = PaymentStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()

        # Raise event
        self.add_domain_event(PaymentCancelled(
            payment_id=self.id,
            order_id=self.order_id,
            cancelled_at=self.cancelled_at,
            reason=reason
        ))

        self.mark_as_modified()

    def initiate_refund(
        self,
        refund_amount: Money,
        refund_reason: RefundReason,
        refund_notes: Optional[str] = None,
        requested_by: Optional[UUID] = None
    ) -> UUID:
        """Initiate a refund"""
        if self.payment_status != PaymentStatus.CAPTURED:
            raise BusinessRuleViolation("Can only refund captured payments")

        # Validate refund amount
        total_refunded = self.get_total_refunded()
        remaining_amount = self.payment_amount.subtract(total_refunded)

        if refund_amount.amount > remaining_amount.amount:
            raise BusinessRuleViolation(
                f"Refund amount {refund_amount} exceeds remaining amount {remaining_amount}"
            )

        # Create refund
        refund = Refund(
            refund_amount=refund_amount,
            refund_reason=refund_reason,
            refund_notes=refund_notes,
            requested_by=requested_by,
            status="pending"
        )

        self.refunds.append(refund)

        # Raise event
        self.add_domain_event(RefundIssued(
            payment_id=self.id,
            order_id=self.order_id,
            refund_amount=refund_amount.amount,
            refund_reason=refund_reason,
            refunded_at=datetime.utcnow()
        ))

        self.mark_as_modified()
        return refund.id

    def complete_refund(
        self,
        refund_id: UUID,
        gateway_response: PaymentGatewayResponse
    ):
        """Complete a refund"""
        refund = self.get_refund(refund_id)
        if not refund:
            raise BusinessRuleViolation(f"Refund {refund_id} not found")

        if not gateway_response.is_success:
            refund.fail(gateway_response.status_message)
            self.mark_as_modified()
            return

        refund.complete(gateway_response)

        # Update refunded amount
        self.refunded_amount = self.refunded_amount.add(refund.refund_amount)

        # Update payment status
        if self.refunded_amount.amount >= self.payment_amount.amount:
            self.payment_status = PaymentStatus.REFUNDED
        else:
            self.payment_status = PaymentStatus.PARTIALLY_REFUNDED

        # Raise event
        self.add_domain_event(RefundCompleted(
            payment_id=self.id,
            refund_id=refund_id,
            refund_amount=refund.refund_amount.amount,
            completed_at=refund.completed_at
        ))

        self.mark_as_modified()

    def add_split_payment(self, split_payment: SplitPayment):
        """Add a split payment"""
        if not self.is_split_payment:
            self.is_split_payment = True

        self.split_payments.append(split_payment)
        self.mark_as_modified()

    def get_refund(self, refund_id: UUID) -> Optional[Refund]:
        """Get refund by ID"""
        return next((r for r in self.refunds if r.id == refund_id), None)

    def get_total_refunded(self) -> Money:
        """Get total amount refunded"""
        return self.refunded_amount

    def get_remaining_amount(self) -> Money:
        """Get remaining amount after refunds"""
        return self.payment_amount.subtract(self.refunded_amount)

    def is_fully_refunded(self) -> bool:
        """Check if payment is fully refunded"""
        return self.payment_status == PaymentStatus.REFUNDED

    def is_partially_refunded(self) -> bool:
        """Check if payment is partially refunded"""
        return self.payment_status == PaymentStatus.PARTIALLY_REFUNDED

    def can_be_refunded(self) -> bool:
        """Check if payment can be refunded"""
        if self.payment_status != PaymentStatus.CAPTURED:
            return False

        remaining = self.get_remaining_amount()
        return remaining.is_positive()

    def validate(self) -> List[str]:
        """Validate payment transaction"""
        errors = []

        if not self.order_id:
            errors.append("Order ID is required")

        if not self.store_id:
            errors.append("Store ID is required")

        if not self.tenant_id:
            errors.append("Tenant ID is required")

        if not self.payment_amount or not self.payment_amount.is_positive():
            errors.append("Payment amount must be positive")

        if not self.payment_method_details:
            errors.append("Payment method details are required")

        # Validate split payments sum to total
        if self.is_split_payment:
            total_split = Money(amount=Decimal("0"), currency=self.payment_amount.currency)
            for split in self.split_payments:
                total_split = total_split.add(split.amount)

            if total_split.amount != self.payment_amount.amount:
                errors.append("Split payments must sum to total payment amount")

        # Validate refunds
        total_refunded = self.get_total_refunded()
        if total_refunded.amount > self.payment_amount.amount:
            errors.append("Total refunded exceeds payment amount")

        return errors
