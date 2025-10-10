"""
Order Status Value Objects
Following DDD Architecture Document Section 2.6
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime

from ....shared.domain_base import ValueObject


class OrderStatus(str, Enum):
    """Order Status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    READY_FOR_PICKUP = "ready_for_pickup"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class OrderType(str, Enum):
    """Order Type enumeration"""
    ONLINE = "online"
    IN_STORE = "in_store"
    KIOSK = "kiosk"
    PHONE = "phone"
    MOBILE_APP = "mobile_app"


class DeliveryMethod(str, Enum):
    """Delivery Method enumeration"""
    PICKUP = "pickup"
    DELIVERY = "delivery"
    CURBSIDE = "curbside"
    IN_STORE = "in_store"


class PaymentStatus(str, Enum):
    """Payment Status enumeration"""
    PENDING = "pending"
    AUTHORIZED = "authorized"
    PAID = "paid"
    PARTIALLY_REFUNDED = "partially_refunded"
    REFUNDED = "refunded"
    FAILED = "failed"


class FulfillmentStatus(str, Enum):
    """Fulfillment Status enumeration"""
    UNFULFILLED = "unfulfilled"
    PARTIALLY_FULFILLED = "partially_fulfilled"
    FULFILLED = "fulfilled"
    RETURNED = "returned"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class OrderStatusTransition(ValueObject):
    """
    Value Object for tracking order status transitions
    """
    from_status: OrderStatus
    to_status: OrderStatus
    transitioned_at: datetime
    transitioned_by: Optional[str] = None
    reason: Optional[str] = None
    metadata: Optional[dict] = None

    def __post_init__(self):
        """Validate status transition"""
        if not self._is_valid_transition():
            raise ValueError(f"Invalid transition from {self.from_status} to {self.to_status}")

    def _is_valid_transition(self) -> bool:
        """Check if the status transition is valid"""
        valid_transitions = {
            OrderStatus.PENDING: [
                OrderStatus.CONFIRMED,
                OrderStatus.CANCELLED
            ],
            OrderStatus.CONFIRMED: [
                OrderStatus.PROCESSING,
                OrderStatus.CANCELLED
            ],
            OrderStatus.PROCESSING: [
                OrderStatus.READY_FOR_PICKUP,
                OrderStatus.OUT_FOR_DELIVERY,
                OrderStatus.CANCELLED
            ],
            OrderStatus.READY_FOR_PICKUP: [
                OrderStatus.COMPLETED,
                OrderStatus.CANCELLED
            ],
            OrderStatus.OUT_FOR_DELIVERY: [
                OrderStatus.DELIVERED,
                OrderStatus.CANCELLED
            ],
            OrderStatus.DELIVERED: [
                OrderStatus.COMPLETED,
                OrderStatus.REFUNDED
            ],
            OrderStatus.COMPLETED: [
                OrderStatus.REFUNDED
            ],
            OrderStatus.CANCELLED: [],
            OrderStatus.REFUNDED: []
        }

        return self.to_status in valid_transitions.get(self.from_status, [])


@dataclass(frozen=True)
class OrderTotals(ValueObject):
    """
    Value Object for order financial totals
    """
    from decimal import Decimal

    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    delivery_fee: Decimal
    tip_amount: Decimal = Decimal("0")

    def __post_init__(self):
        """Validate totals"""
        if self.subtotal < 0:
            raise ValueError("Subtotal cannot be negative")
        if self.tax_amount < 0:
            raise ValueError("Tax amount cannot be negative")
        if self.discount_amount < 0:
            raise ValueError("Discount amount cannot be negative")
        if self.delivery_fee < 0:
            raise ValueError("Delivery fee cannot be negative")
        if self.tip_amount < 0:
            raise ValueError("Tip amount cannot be negative")

    @property
    def total_amount(self) -> Decimal:
        """Calculate total amount"""
        return (
            self.subtotal +
            self.tax_amount +
            self.delivery_fee +
            self.tip_amount -
            self.discount_amount
        )

    @property
    def amount_before_tax(self) -> Decimal:
        """Calculate amount before tax"""
        return self.subtotal + self.delivery_fee + self.tip_amount - self.discount_amount

    def with_tip(self, tip: Decimal) -> 'OrderTotals':
        """Create new OrderTotals with tip"""
        from decimal import Decimal
        return OrderTotals(
            subtotal=self.subtotal,
            tax_amount=self.tax_amount,
            discount_amount=self.discount_amount,
            delivery_fee=self.delivery_fee,
            tip_amount=tip
        )
