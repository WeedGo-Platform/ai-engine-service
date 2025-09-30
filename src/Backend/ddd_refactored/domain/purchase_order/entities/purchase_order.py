"""
PurchaseOrder Aggregate Root
Following DDD Architecture Document Section 2.5
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from ....shared.domain_base import AggregateRoot, DomainEvent, BusinessRuleViolation
from ..value_objects import (
    PurchaseOrderStatus,
    ApprovalStatus,
    PaymentTerms,
    OrderStatusTransition,
    ShippingMethod,
    DeliverySchedule
)


class PurchaseOrderCreated(DomainEvent):
    """Event raised when purchase order is created"""
    purchase_order_id: UUID
    order_number: str
    supplier_id: UUID
    store_id: UUID


class PurchaseOrderSubmitted(DomainEvent):
    """Event raised when purchase order is submitted for approval"""
    purchase_order_id: UUID
    order_number: str
    submitted_by: UUID
    total_amount: Decimal


class PurchaseOrderApproved(DomainEvent):
    """Event raised when purchase order is approved"""
    purchase_order_id: UUID
    order_number: str
    approved_by: UUID
    approved_at: datetime


class PurchaseOrderSentToSupplier(DomainEvent):
    """Event raised when PO is sent to supplier"""
    purchase_order_id: UUID
    order_number: str
    supplier_id: UUID
    sent_at: datetime


class PurchaseOrderReceived(DomainEvent):
    """Event raised when goods are received"""
    purchase_order_id: UUID
    order_number: str
    received_quantity: int
    received_by: UUID
    is_fully_received: bool


@dataclass
class PurchaseOrder(AggregateRoot):
    """
    PurchaseOrder Aggregate Root - Manages supplier orders
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.5
    """
    # Identifiers
    store_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    supplier_id: UUID = field(default_factory=uuid4)
    order_number: str = ""  # PO-YYYY-MM-XXXXX

    # Status
    status: PurchaseOrderStatus = PurchaseOrderStatus.DRAFT
    approval_status: ApprovalStatus = ApprovalStatus.PENDING

    # Dates
    order_date: datetime = field(default_factory=datetime.utcnow)
    expected_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    due_date: Optional[datetime] = None  # Payment due date

    # Financial
    subtotal: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    shipping_cost: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")
    total_amount: Decimal = Decimal("0")
    currency: str = "CAD"

    # Payment
    payment_terms: PaymentTerms = PaymentTerms.NET_30
    payment_method: Optional[str] = None
    prepaid_amount: Decimal = Decimal("0")
    amount_due: Decimal = Decimal("0")

    # Shipping
    shipping_method: Optional[ShippingMethod] = None
    delivery_schedule: Optional[DeliverySchedule] = None
    shipping_address_id: Optional[UUID] = None
    billing_address_id: Optional[UUID] = None

    # Supplier Information
    supplier_name: str = ""
    supplier_contact: Optional[str] = None
    supplier_email: Optional[str] = None
    supplier_phone: Optional[str] = None
    supplier_order_number: Optional[str] = None  # Supplier's reference

    # Tracking
    tracking_number: Optional[str] = None
    carrier_name: Optional[str] = None

    # Line Items Count
    total_line_items: int = 0
    total_units_ordered: int = 0
    total_units_received: int = 0

    # User Tracking
    created_by: Optional[UUID] = None
    submitted_by: Optional[UUID] = None
    approved_by: Optional[UUID] = None
    received_by: Optional[UUID] = None
    cancelled_by: Optional[UUID] = None

    # Timestamps
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    received_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    # Notes
    internal_notes: Optional[str] = None
    supplier_notes: Optional[str] = None
    receiving_notes: Optional[str] = None
    cancellation_reason: Optional[str] = None

    # Status History
    status_history: List[OrderStatusTransition] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        store_id: UUID,
        tenant_id: UUID,
        supplier_id: UUID,
        supplier_name: str,
        payment_terms: PaymentTerms = PaymentTerms.NET_30,
        created_by: Optional[UUID] = None
    ) -> 'PurchaseOrder':
        """Factory method to create new purchase order"""
        # Generate order number
        now = datetime.utcnow()
        order_number = f"PO-{now.year}-{now.month:02d}-{uuid4().hex[:5].upper()}"

        po = cls(
            store_id=store_id,
            tenant_id=tenant_id,
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            order_number=order_number,
            status=PurchaseOrderStatus.DRAFT,
            approval_status=ApprovalStatus.PENDING,
            payment_terms=payment_terms,
            created_by=created_by
        )

        # Raise creation event
        po.add_domain_event(PurchaseOrderCreated(
            purchase_order_id=po.id,
            order_number=order_number,
            supplier_id=supplier_id,
            store_id=store_id
        ))

        return po

    def add_line_item(self, quantity: int, unit_price: Decimal):
        """Add a line item to the order"""
        if self.status != PurchaseOrderStatus.DRAFT:
            raise BusinessRuleViolation("Cannot add items to non-draft purchase order")

        if quantity <= 0:
            raise BusinessRuleViolation("Quantity must be positive")

        if unit_price < 0:
            raise BusinessRuleViolation("Unit price cannot be negative")

        self.total_line_items += 1
        self.total_units_ordered += quantity

        # Update totals
        line_total = Decimal(quantity) * unit_price
        self.subtotal += line_total
        self._recalculate_totals()

        self.mark_as_modified()

    def remove_line_item(self, quantity: int, unit_price: Decimal):
        """Remove a line item from the order"""
        if self.status != PurchaseOrderStatus.DRAFT:
            raise BusinessRuleViolation("Cannot remove items from non-draft purchase order")

        self.total_line_items = max(0, self.total_line_items - 1)
        self.total_units_ordered = max(0, self.total_units_ordered - quantity)

        # Update totals
        line_total = Decimal(quantity) * unit_price
        self.subtotal = max(Decimal("0"), self.subtotal - line_total)
        self._recalculate_totals()

        self.mark_as_modified()

    def _recalculate_totals(self):
        """Recalculate order totals"""
        self.total_amount = self.subtotal + self.tax_amount + self.shipping_cost - self.discount_amount
        self.amount_due = self.total_amount - self.prepaid_amount

    def set_financial_details(
        self,
        tax_amount: Optional[Decimal] = None,
        shipping_cost: Optional[Decimal] = None,
        discount_amount: Optional[Decimal] = None
    ):
        """Set financial details"""
        if tax_amount is not None:
            if tax_amount < 0:
                raise BusinessRuleViolation("Tax amount cannot be negative")
            self.tax_amount = tax_amount

        if shipping_cost is not None:
            if shipping_cost < 0:
                raise BusinessRuleViolation("Shipping cost cannot be negative")
            self.shipping_cost = shipping_cost

        if discount_amount is not None:
            if discount_amount < 0:
                raise BusinessRuleViolation("Discount amount cannot be negative")
            self.discount_amount = discount_amount

        self._recalculate_totals()
        self.mark_as_modified()

    def set_delivery_details(
        self,
        expected_delivery_date: Optional[datetime] = None,
        shipping_method: Optional[ShippingMethod] = None,
        delivery_schedule: Optional[DeliverySchedule] = None
    ):
        """Set delivery details"""
        if expected_delivery_date:
            if expected_delivery_date <= datetime.utcnow():
                raise BusinessRuleViolation("Expected delivery date must be in the future")
            self.expected_delivery_date = expected_delivery_date

        if shipping_method:
            self.shipping_method = shipping_method

        if delivery_schedule:
            self.delivery_schedule = delivery_schedule

        self.mark_as_modified()

    def set_supplier_contact(
        self,
        contact_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None
    ):
        """Set supplier contact information"""
        if contact_name:
            self.supplier_contact = contact_name
        if email:
            self.supplier_email = email
        if phone:
            self.supplier_phone = phone

        self.mark_as_modified()

    def submit_for_approval(self, submitted_by: UUID):
        """Submit purchase order for approval"""
        if self.status != PurchaseOrderStatus.DRAFT:
            raise BusinessRuleViolation(f"Cannot submit {self.status} purchase order")

        if self.total_line_items == 0:
            raise BusinessRuleViolation("Cannot submit empty purchase order")

        if self.total_amount <= 0:
            raise BusinessRuleViolation("Total amount must be greater than zero")

        # Update status
        self._transition_status(PurchaseOrderStatus.SUBMITTED, "Submitted for approval")
        self.submitted_by = submitted_by
        self.submitted_at = datetime.utcnow()

        # Raise event
        self.add_domain_event(PurchaseOrderSubmitted(
            purchase_order_id=self.id,
            order_number=self.order_number,
            submitted_by=submitted_by,
            total_amount=self.total_amount
        ))

        self.mark_as_modified()

    def approve(self, approved_by: UUID):
        """Approve purchase order"""
        if self.status != PurchaseOrderStatus.SUBMITTED:
            raise BusinessRuleViolation(f"Cannot approve {self.status} purchase order")

        # Update status
        self._transition_status(PurchaseOrderStatus.APPROVED, "Approved")
        self.approval_status = ApprovalStatus.APPROVED
        self.approved_by = approved_by
        self.approved_at = datetime.utcnow()

        # Raise event
        self.add_domain_event(PurchaseOrderApproved(
            purchase_order_id=self.id,
            order_number=self.order_number,
            approved_by=approved_by,
            approved_at=self.approved_at
        ))

        self.mark_as_modified()

    def reject(self, rejected_by: UUID, reason: str):
        """Reject purchase order"""
        if self.status != PurchaseOrderStatus.SUBMITTED:
            raise BusinessRuleViolation(f"Cannot reject {self.status} purchase order")

        # Return to draft
        self._transition_status(PurchaseOrderStatus.DRAFT, f"Rejected: {reason}")
        self.approval_status = ApprovalStatus.REJECTED
        self.metadata['rejection_reason'] = reason
        self.metadata['rejected_by'] = str(rejected_by)
        self.metadata['rejected_at'] = datetime.utcnow().isoformat()

        self.mark_as_modified()

    def send_to_supplier(self, sent_by: Optional[UUID] = None):
        """Send purchase order to supplier"""
        if self.status != PurchaseOrderStatus.APPROVED:
            raise BusinessRuleViolation(f"Cannot send {self.status} purchase order to supplier")

        # Update status
        self._transition_status(PurchaseOrderStatus.SENT_TO_SUPPLIER, "Sent to supplier")
        self.sent_at = datetime.utcnow()

        # Calculate payment due date
        if self.payment_terms == PaymentTerms.NET_15:
            self.due_date = self.sent_at + timedelta(days=15)
        elif self.payment_terms == PaymentTerms.NET_30:
            self.due_date = self.sent_at + timedelta(days=30)
        elif self.payment_terms == PaymentTerms.NET_45:
            self.due_date = self.sent_at + timedelta(days=45)
        elif self.payment_terms == PaymentTerms.NET_60:
            self.due_date = self.sent_at + timedelta(days=60)
        elif self.payment_terms == PaymentTerms.NET_90:
            self.due_date = self.sent_at + timedelta(days=90)
        elif self.payment_terms == PaymentTerms.DUE_ON_RECEIPT:
            self.due_date = self.sent_at

        # Raise event
        self.add_domain_event(PurchaseOrderSentToSupplier(
            purchase_order_id=self.id,
            order_number=self.order_number,
            supplier_id=self.supplier_id,
            sent_at=self.sent_at
        ))

        self.mark_as_modified()

    def confirm_by_supplier(self, supplier_order_number: Optional[str] = None):
        """Confirm receipt by supplier"""
        if self.status != PurchaseOrderStatus.SENT_TO_SUPPLIER:
            raise BusinessRuleViolation(f"Cannot confirm {self.status} purchase order")

        self._transition_status(PurchaseOrderStatus.CONFIRMED, "Confirmed by supplier")
        self.confirmed_at = datetime.utcnow()

        if supplier_order_number:
            self.supplier_order_number = supplier_order_number

        self.mark_as_modified()

    def receive_items(self, quantity_received: int, received_by: UUID, notes: Optional[str] = None):
        """Receive items from the order"""
        if self.status not in [PurchaseOrderStatus.CONFIRMED, PurchaseOrderStatus.PARTIALLY_RECEIVED]:
            raise BusinessRuleViolation(f"Cannot receive items for {self.status} purchase order")

        if quantity_received <= 0:
            raise BusinessRuleViolation("Received quantity must be positive")

        # Update quantities
        self.total_units_received += quantity_received

        # Check if fully received
        is_fully_received = self.total_units_received >= self.total_units_ordered

        if is_fully_received:
            self._transition_status(PurchaseOrderStatus.FULLY_RECEIVED, "All items received")
            self.actual_delivery_date = datetime.utcnow()
        elif self.status != PurchaseOrderStatus.PARTIALLY_RECEIVED:
            self._transition_status(PurchaseOrderStatus.PARTIALLY_RECEIVED, f"Received {quantity_received} units")

        self.received_by = received_by
        self.received_at = datetime.utcnow()

        if notes:
            self.receiving_notes = notes

        # Raise event
        self.add_domain_event(PurchaseOrderReceived(
            purchase_order_id=self.id,
            order_number=self.order_number,
            received_quantity=quantity_received,
            received_by=received_by,
            is_fully_received=is_fully_received
        ))

        self.mark_as_modified()

    def close(self):
        """Close the purchase order"""
        if self.status not in [PurchaseOrderStatus.FULLY_RECEIVED, PurchaseOrderStatus.PARTIALLY_RECEIVED]:
            raise BusinessRuleViolation(f"Cannot close {self.status} purchase order")

        self._transition_status(PurchaseOrderStatus.CLOSED, "Order closed")
        self.closed_at = datetime.utcnow()
        self.mark_as_modified()

    def cancel(self, cancelled_by: UUID, reason: str):
        """Cancel the purchase order"""
        if self.status in [PurchaseOrderStatus.CLOSED, PurchaseOrderStatus.CANCELLED]:
            raise BusinessRuleViolation(f"Cannot cancel {self.status} purchase order")

        if self.status in [PurchaseOrderStatus.PARTIALLY_RECEIVED, PurchaseOrderStatus.FULLY_RECEIVED]:
            raise BusinessRuleViolation("Cannot cancel order with received items")

        self._transition_status(PurchaseOrderStatus.CANCELLED, f"Cancelled: {reason}")
        self.cancelled_by = cancelled_by
        self.cancelled_at = datetime.utcnow()
        self.cancellation_reason = reason
        self.mark_as_modified()

    def add_tracking_info(self, tracking_number: str, carrier: Optional[str] = None):
        """Add tracking information"""
        if not tracking_number:
            raise BusinessRuleViolation("Tracking number is required")

        self.tracking_number = tracking_number
        if carrier:
            self.carrier_name = carrier

        self.mark_as_modified()

    def _transition_status(self, new_status: PurchaseOrderStatus, reason: Optional[str] = None):
        """Transition to new status with history tracking"""
        # Create transition record
        transition = OrderStatusTransition(
            from_status=self.status,
            to_status=new_status,
            transitioned_at=datetime.utcnow(),
            reason=reason
        )

        # Update status
        self.status = new_status
        self.status_history.append(transition)

    def is_overdue_for_delivery(self) -> bool:
        """Check if order is overdue for delivery"""
        if not self.expected_delivery_date:
            return False

        if self.status in [PurchaseOrderStatus.FULLY_RECEIVED, PurchaseOrderStatus.CLOSED, PurchaseOrderStatus.CANCELLED]:
            return False

        return datetime.utcnow() > self.expected_delivery_date

    def is_payment_due(self) -> bool:
        """Check if payment is due"""
        if not self.due_date:
            return False

        if self.amount_due <= 0:
            return False

        return datetime.utcnow() >= self.due_date

    def get_received_percentage(self) -> Decimal:
        """Calculate percentage of items received"""
        if self.total_units_ordered == 0:
            return Decimal("0")

        percentage = (Decimal(self.total_units_received) / Decimal(self.total_units_ordered)) * 100
        return percentage.quantize(Decimal("0.01"))

    def can_be_edited(self) -> bool:
        """Check if order can be edited"""
        return self.status == PurchaseOrderStatus.DRAFT

    def requires_approval(self) -> bool:
        """Check if order requires approval based on amount"""
        # Business rule: Orders over $5000 require approval
        approval_threshold = Decimal("5000")
        return self.total_amount > approval_threshold

    def validate(self) -> List[str]:
        """Validate purchase order data"""
        errors = []

        if not self.order_number:
            errors.append("Order number is required")

        if not self.supplier_id:
            errors.append("Supplier is required")

        if not self.store_id:
            errors.append("Store is required")

        if self.total_amount < 0:
            errors.append("Total amount cannot be negative")

        if self.subtotal < 0:
            errors.append("Subtotal cannot be negative")

        if self.total_units_received > self.total_units_ordered:
            errors.append("Received units cannot exceed ordered units")

        if self.prepaid_amount > self.total_amount:
            errors.append("Prepaid amount cannot exceed total amount")

        if self.expected_delivery_date and self.order_date:
            if self.expected_delivery_date < self.order_date:
                errors.append("Expected delivery date cannot be before order date")

        return errors