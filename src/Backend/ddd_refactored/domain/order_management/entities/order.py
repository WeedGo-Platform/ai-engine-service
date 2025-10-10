"""
Order Aggregate Root
Following DDD Architecture Document Section 2.6
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from ....shared.domain_base import AggregateRoot, DomainEvent, BusinessRuleViolation
from ..value_objects.order_status import (
    OrderStatus,
    OrderType,
    DeliveryMethod,
    PaymentStatus,
    FulfillmentStatus,
    OrderStatusTransition,
    OrderTotals
)


# Domain Events
class OrderCreated(DomainEvent):
    order_id: UUID
    order_number: str
    store_id: UUID
    customer_id: Optional[UUID]
    total_amount: Decimal


class OrderConfirmed(DomainEvent):
    order_id: UUID
    order_number: str
    confirmed_at: datetime


class OrderCancelled(DomainEvent):
    order_id: UUID
    order_number: str
    cancelled_by: Optional[UUID]
    reason: str


class OrderCompleted(DomainEvent):
    order_id: UUID
    order_number: str
    completed_at: datetime


@dataclass
class OrderLine:
    """Order Line Item - entity within Order aggregate"""
    line_number: int
    sku: str
    product_name: str
    product_type: str  # cannabis, accessory
    quantity: int
    unit_price: Decimal
    discount_amount: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    line_total: Decimal = Decimal("0")

    # Cannabis Specific
    thc_percentage: Optional[Decimal] = None
    cbd_percentage: Optional[Decimal] = None
    product_category: Optional[str] = None

    # Fulfillment
    fulfilled_quantity: int = 0
    is_fulfilled: bool = False

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate line total"""
        subtotal = self.unit_price * Decimal(self.quantity)
        self.line_total = subtotal - self.discount_amount + self.tax_amount

    def calculate_total(self) -> Decimal:
        """Recalculate line total"""
        subtotal = self.unit_price * Decimal(self.quantity)
        self.line_total = subtotal - self.discount_amount + self.tax_amount
        return self.line_total


@dataclass
class Order(AggregateRoot):
    """
    Order Aggregate Root - Customer orders
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.6
    """
    # Identifiers
    store_id: UUID = field(default_factory=uuid4)
    customer_id: Optional[UUID] = None
    order_number: str = ""  # ORD-YYYY-MM-XXXXX

    # Status
    status: OrderStatus = OrderStatus.PENDING
    payment_status: PaymentStatus = PaymentStatus.PENDING
    fulfillment_status: FulfillmentStatus = FulfillmentStatus.UNFULFILLED

    # Order Details
    order_type: OrderType = OrderType.ONLINE
    delivery_method: DeliveryMethod = DeliveryMethod.PICKUP

    # Line Items
    items: List[OrderLine] = field(default_factory=list)

    # Financial
    subtotal: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")
    delivery_fee: Decimal = Decimal("0")
    tip_amount: Decimal = Decimal("0")
    total_amount: Decimal = Decimal("0")

    # Payment
    payment_method: Optional[str] = None
    payment_transaction_id: Optional[UUID] = None

    # Delivery
    delivery_address: Optional[Dict[str, Any]] = None
    delivery_instructions: Optional[str] = None
    pickup_time: Optional[datetime] = None
    estimated_delivery_time: Optional[datetime] = None
    actual_delivery_time: Optional[datetime] = None

    # Customer Info
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None

    # Notes
    customer_notes: Optional[str] = None
    internal_notes: Optional[str] = None
    cancellation_reason: Optional[str] = None

    # Status History
    status_history: List[OrderStatusTransition] = field(default_factory=list)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    confirmed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        store_id: UUID,
        order_type: OrderType = OrderType.ONLINE,
        delivery_method: DeliveryMethod = DeliveryMethod.PICKUP,
        customer_id: Optional[UUID] = None
    ) -> 'Order':
        """Factory method to create new order"""
        # Generate order number
        now = datetime.utcnow()
        order_number = f"ORD-{now.year}-{now.month:02d}-{uuid4().hex[:5].upper()}"

        order = cls(
            store_id=store_id,
            order_number=order_number,
            order_type=order_type,
            delivery_method=delivery_method,
            customer_id=customer_id,
            status=OrderStatus.PENDING
        )

        # Raise creation event
        order.add_domain_event(OrderCreated(
            order_id=order.id,
            order_number=order_number,
            store_id=store_id,
            customer_id=customer_id,
            total_amount=Decimal("0")
        ))

        return order

    def add_item(
        self,
        sku: str,
        product_name: str,
        product_type: str,
        quantity: int,
        unit_price: Decimal,
        tax_rate: Decimal = Decimal("13")
    ):
        """Add item to order"""
        if self.status not in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
            raise BusinessRuleViolation(f"Cannot add items to {self.status} order")

        if quantity <= 0:
            raise BusinessRuleViolation("Quantity must be positive")

        if unit_price < 0:
            raise BusinessRuleViolation("Unit price cannot be negative")

        # Create line item
        line_number = len(self.items) + 1
        subtotal = unit_price * Decimal(quantity)
        tax_amount = subtotal * (tax_rate / 100)

        line = OrderLine(
            line_number=line_number,
            sku=sku,
            product_name=product_name,
            product_type=product_type,
            quantity=quantity,
            unit_price=unit_price,
            tax_amount=tax_amount
        )

        self.items.append(line)
        self._recalculate_totals()
        self.mark_as_modified()

    def remove_item(self, sku: str):
        """Remove item from order"""
        if self.status not in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
            raise BusinessRuleViolation(f"Cannot remove items from {self.status} order")

        self.items = [item for item in self.items if item.sku != sku]
        self._recalculate_totals()
        self.mark_as_modified()

    def update_item_quantity(self, sku: str, new_quantity: int):
        """Update item quantity"""
        if self.status not in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
            raise BusinessRuleViolation(f"Cannot update items in {self.status} order")

        if new_quantity < 0:
            raise BusinessRuleViolation("Quantity cannot be negative")

        for item in self.items:
            if item.sku == sku:
                if new_quantity == 0:
                    self.remove_item(sku)
                else:
                    item.quantity = new_quantity
                    item.calculate_total()
                    self._recalculate_totals()
                    self.mark_as_modified()
                return

        raise BusinessRuleViolation(f"Item {sku} not found in order")

    def apply_discount(self, discount_amount: Decimal):
        """Apply discount to order"""
        if discount_amount < 0:
            raise BusinessRuleViolation("Discount amount cannot be negative")

        if discount_amount > self.subtotal:
            raise BusinessRuleViolation("Discount cannot exceed subtotal")

        self.discount_amount = discount_amount
        self._recalculate_totals()
        self.mark_as_modified()

    def set_delivery_fee(self, fee: Decimal):
        """Set delivery fee"""
        if fee < 0:
            raise BusinessRuleViolation("Delivery fee cannot be negative")

        self.delivery_fee = fee
        self._recalculate_totals()
        self.mark_as_modified()

    def add_tip(self, tip: Decimal):
        """Add tip amount"""
        if tip < 0:
            raise BusinessRuleViolation("Tip cannot be negative")

        self.tip_amount = tip
        self._recalculate_totals()
        self.mark_as_modified()

    def _recalculate_totals(self):
        """Recalculate order totals"""
        self.subtotal = sum(item.unit_price * Decimal(item.quantity) for item in self.items)
        self.tax_amount = sum(item.tax_amount for item in self.items)

        self.total_amount = (
            self.subtotal +
            self.tax_amount +
            self.delivery_fee +
            self.tip_amount -
            self.discount_amount
        )

    def set_delivery_address(self, address: Dict[str, Any]):
        """Set delivery address"""
        if self.delivery_method != DeliveryMethod.DELIVERY:
            raise BusinessRuleViolation("Cannot set delivery address for non-delivery order")

        self.delivery_address = address
        self.mark_as_modified()

    def set_pickup_time(self, pickup_time: datetime):
        """Set pickup time"""
        if self.delivery_method != DeliveryMethod.PICKUP:
            raise BusinessRuleViolation("Cannot set pickup time for non-pickup order")

        if pickup_time <= datetime.utcnow():
            raise BusinessRuleViolation("Pickup time must be in the future")

        self.pickup_time = pickup_time
        self.mark_as_modified()

    def confirm(self):
        """Confirm the order"""
        if self.status != OrderStatus.PENDING:
            raise BusinessRuleViolation(f"Cannot confirm {self.status} order")

        if len(self.items) == 0:
            raise BusinessRuleViolation("Cannot confirm empty order")

        self._transition_status(OrderStatus.CONFIRMED, "Order confirmed")
        self.confirmed_at = datetime.utcnow()

        # Raise event
        self.add_domain_event(OrderConfirmed(
            order_id=self.id,
            order_number=self.order_number,
            confirmed_at=self.confirmed_at
        ))

        self.mark_as_modified()

    def start_processing(self):
        """Start processing the order"""
        if self.status != OrderStatus.CONFIRMED:
            raise BusinessRuleViolation(f"Cannot process {self.status} order")

        self._transition_status(OrderStatus.PROCESSING, "Processing started")
        self.mark_as_modified()

    def mark_ready_for_pickup(self):
        """Mark order ready for pickup"""
        if self.delivery_method != DeliveryMethod.PICKUP:
            raise BusinessRuleViolation("Cannot mark non-pickup order ready for pickup")

        if self.status != OrderStatus.PROCESSING:
            raise BusinessRuleViolation(f"Cannot mark {self.status} order ready")

        self._transition_status(OrderStatus.READY_FOR_PICKUP, "Ready for pickup")
        self.mark_as_modified()

    def mark_out_for_delivery(self):
        """Mark order out for delivery"""
        if self.delivery_method != DeliveryMethod.DELIVERY:
            raise BusinessRuleViolation("Cannot mark non-delivery order out for delivery")

        if self.status != OrderStatus.PROCESSING:
            raise BusinessRuleViolation(f"Cannot mark {self.status} order out for delivery")

        self._transition_status(OrderStatus.OUT_FOR_DELIVERY, "Out for delivery")
        self.mark_as_modified()

    def complete(self):
        """Complete the order"""
        if self.status not in [OrderStatus.READY_FOR_PICKUP, OrderStatus.DELIVERED]:
            raise BusinessRuleViolation(f"Cannot complete {self.status} order")

        self._transition_status(OrderStatus.COMPLETED, "Order completed")
        self.completed_at = datetime.utcnow()
        self.fulfillment_status = FulfillmentStatus.FULFILLED

        # Raise event
        self.add_domain_event(OrderCompleted(
            order_id=self.id,
            order_number=self.order_number,
            completed_at=self.completed_at
        ))

        self.mark_as_modified()

    def cancel(self, cancelled_by: Optional[UUID] = None, reason: str = ""):
        """Cancel the order"""
        if self.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
            raise BusinessRuleViolation(f"Cannot cancel {self.status} order")

        self._transition_status(OrderStatus.CANCELLED, f"Cancelled: {reason}")
        self.cancelled_at = datetime.utcnow()
        self.cancellation_reason = reason
        self.fulfillment_status = FulfillmentStatus.CANCELLED

        # Raise event
        self.add_domain_event(OrderCancelled(
            order_id=self.id,
            order_number=self.order_number,
            cancelled_by=cancelled_by,
            reason=reason
        ))

        self.mark_as_modified()

    def update_payment_status(self, new_status: PaymentStatus, transaction_id: Optional[UUID] = None):
        """Update payment status"""
        self.payment_status = new_status
        if transaction_id:
            self.payment_transaction_id = transaction_id
        self.mark_as_modified()

    def _transition_status(self, new_status: OrderStatus, reason: Optional[str] = None):
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
        self.updated_at = datetime.utcnow()

    def get_totals(self) -> OrderTotals:
        """Get order totals as value object"""
        return OrderTotals(
            subtotal=self.subtotal,
            tax_amount=self.tax_amount,
            discount_amount=self.discount_amount,
            delivery_fee=self.delivery_fee,
            tip_amount=self.tip_amount
        )

    def is_cancellable(self) -> bool:
        """Check if order can be cancelled"""
        return self.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.PROCESSING]

    def is_modifiable(self) -> bool:
        """Check if order can be modified"""
        return self.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED]

    def validate(self) -> List[str]:
        """Validate order data"""
        errors = []

        if not self.order_number:
            errors.append("Order number is required")

        if not self.store_id:
            errors.append("Store ID is required")

        if len(self.items) == 0 and self.status != OrderStatus.PENDING:
            errors.append("Order must have items")

        if self.subtotal < 0:
            errors.append("Subtotal cannot be negative")

        if self.total_amount < 0:
            errors.append("Total amount cannot be negative")

        if self.delivery_method == DeliveryMethod.DELIVERY and not self.delivery_address:
            errors.append("Delivery address required for delivery orders")

        if self.delivery_method == DeliveryMethod.PICKUP and not self.pickup_time:
            errors.append("Pickup time required for pickup orders")

        return errors
