"""
InventoryReservation Entity
Following DDD Architecture Document Section 2.4
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from enum import Enum

from ....shared.domain_base import Entity, BusinessRuleViolation


class ReservationType(str, Enum):
    """Types of inventory reservations"""
    ORDER = "order"  # Customer order reservation
    TRANSFER = "transfer"  # Inter-store transfer
    HOLD = "hold"  # Manual hold
    ALLOCATION = "allocation"  # Pre-allocation for expected orders
    PICK = "pick"  # Picking in progress
    ASSEMBLY = "assembly"  # Reserved for product assembly/bundling


class ReservationStatus(str, Enum):
    """Status of inventory reservation"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PARTIALLY_FULFILLED = "partially_fulfilled"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class InventoryReservation(Entity):
    """
    InventoryReservation Entity - Track reserved inventory
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.4
    """
    # Identifiers
    store_id: UUID = field(default_factory=uuid4)
    inventory_id: UUID = field(default_factory=uuid4)
    sku: str = ""

    # Reservation Details
    reservation_type: ReservationType = ReservationType.ORDER
    reservation_status: ReservationStatus = ReservationStatus.PENDING

    # Reference Information
    order_id: Optional[UUID] = None  # Link to order
    order_line_id: Optional[UUID] = None  # Specific order line
    transfer_id: Optional[UUID] = None  # For transfers
    customer_id: Optional[UUID] = None

    # Quantities
    quantity_reserved: int = 0
    quantity_fulfilled: int = 0
    quantity_cancelled: int = 0
    quantity_remaining: int = 0  # Calculated: reserved - fulfilled - cancelled

    # Pricing (captured at reservation time)
    unit_price: Decimal = Decimal("0")
    total_value: Decimal = Decimal("0")

    # Location Information
    location_id: Optional[UUID] = None  # Specific shelf location if assigned
    location_code: Optional[str] = None
    batch_lot: Optional[str] = None  # For batch-tracked items

    # Time Management
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    fulfilled_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    # Priority and Processing
    priority: int = 5  # 1-10, 1 being highest priority
    processing_notes: Optional[str] = None
    cancellation_reason: Optional[str] = None

    # User Tracking
    reserved_by: Optional[UUID] = None
    fulfilled_by: Optional[UUID] = None
    cancelled_by: Optional[UUID] = None

    # Channel Information
    sales_channel: Optional[str] = None  # web, pos, mobile, api

    # Metadata
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize calculated fields"""
        super().__post_init__()
        self._update_remaining_quantity()

    def _update_remaining_quantity(self):
        """Update remaining quantity calculation"""
        self.quantity_remaining = self.quantity_reserved - self.quantity_fulfilled - self.quantity_cancelled

    @classmethod
    def create(
        cls,
        store_id: UUID,
        inventory_id: UUID,
        sku: str,
        quantity: int,
        reservation_type: ReservationType = ReservationType.ORDER,
        order_id: Optional[UUID] = None,
        customer_id: Optional[UUID] = None,
        expires_in_minutes: int = 60,
        priority: int = 5,
        unit_price: Optional[Decimal] = None
    ) -> 'InventoryReservation':
        """Factory method to create new reservation"""
        if quantity <= 0:
            raise BusinessRuleViolation("Reservation quantity must be positive")

        if priority < 1 or priority > 10:
            raise BusinessRuleViolation("Priority must be between 1 and 10")

        expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes) if expires_in_minutes > 0 else None

        reservation = cls(
            store_id=store_id,
            inventory_id=inventory_id,
            sku=sku,
            quantity_reserved=quantity,
            quantity_remaining=quantity,
            reservation_type=reservation_type,
            reservation_status=ReservationStatus.PENDING,
            order_id=order_id,
            customer_id=customer_id,
            expires_at=expires_at,
            priority=priority,
            unit_price=unit_price or Decimal("0"),
            total_value=(unit_price or Decimal("0")) * Decimal(quantity)
        )

        return reservation

    def confirm(self):
        """Confirm the reservation"""
        if self.reservation_status != ReservationStatus.PENDING:
            raise BusinessRuleViolation(f"Cannot confirm reservation in {self.reservation_status} status")

        self.reservation_status = ReservationStatus.CONFIRMED
        self.mark_as_modified()

    def fulfill(self, quantity: Optional[int] = None, fulfilled_by: Optional[UUID] = None):
        """Fulfill the reservation partially or fully"""
        if self.reservation_status in [ReservationStatus.CANCELLED, ReservationStatus.EXPIRED]:
            raise BusinessRuleViolation(f"Cannot fulfill {self.reservation_status} reservation")

        if quantity is None:
            quantity = self.quantity_remaining

        if quantity <= 0:
            raise BusinessRuleViolation("Fulfillment quantity must be positive")

        if quantity > self.quantity_remaining:
            raise BusinessRuleViolation(f"Cannot fulfill {quantity}, only {self.quantity_remaining} remaining")

        self.quantity_fulfilled += quantity
        self._update_remaining_quantity()

        if self.quantity_remaining == 0:
            self.reservation_status = ReservationStatus.FULFILLED
            self.fulfilled_at = datetime.utcnow()
        else:
            self.reservation_status = ReservationStatus.PARTIALLY_FULFILLED

        if fulfilled_by:
            self.fulfilled_by = fulfilled_by

        self.mark_as_modified()

    def cancel(self, quantity: Optional[int] = None, reason: Optional[str] = None, cancelled_by: Optional[UUID] = None):
        """Cancel the reservation partially or fully"""
        if self.reservation_status in [ReservationStatus.FULFILLED, ReservationStatus.CANCELLED]:
            raise BusinessRuleViolation(f"Cannot cancel {self.reservation_status} reservation")

        if quantity is None:
            quantity = self.quantity_remaining

        if quantity <= 0:
            raise BusinessRuleViolation("Cancellation quantity must be positive")

        if quantity > self.quantity_remaining:
            raise BusinessRuleViolation(f"Cannot cancel {quantity}, only {self.quantity_remaining} remaining")

        self.quantity_cancelled += quantity
        self._update_remaining_quantity()

        if self.quantity_remaining == 0:
            self.reservation_status = ReservationStatus.CANCELLED
            self.cancelled_at = datetime.utcnow()

        if reason:
            self.cancellation_reason = reason

        if cancelled_by:
            self.cancelled_by = cancelled_by

        self.mark_as_modified()

    def extend_expiration(self, additional_minutes: int):
        """Extend reservation expiration time"""
        if self.reservation_status in [ReservationStatus.FULFILLED, ReservationStatus.CANCELLED, ReservationStatus.EXPIRED]:
            raise BusinessRuleViolation(f"Cannot extend {self.reservation_status} reservation")

        if additional_minutes <= 0:
            raise BusinessRuleViolation("Extension time must be positive")

        if self.expires_at:
            self.expires_at += timedelta(minutes=additional_minutes)
        else:
            self.expires_at = datetime.utcnow() + timedelta(minutes=additional_minutes)

        self.mark_as_modified()

    def assign_to_location(self, location_id: UUID, location_code: str):
        """Assign reservation to specific shelf location"""
        self.location_id = location_id
        self.location_code = location_code
        self.mark_as_modified()

    def assign_to_batch(self, batch_lot: str):
        """Assign reservation to specific batch/lot"""
        self.batch_lot = batch_lot
        self.mark_as_modified()

    def update_priority(self, new_priority: int):
        """Update reservation priority"""
        if new_priority < 1 or new_priority > 10:
            raise BusinessRuleViolation("Priority must be between 1 and 10")

        self.priority = new_priority
        self.mark_as_modified()

    def is_expired(self) -> bool:
        """Check if reservation has expired"""
        if not self.expires_at:
            return False

        if datetime.utcnow() > self.expires_at:
            if self.reservation_status not in [ReservationStatus.FULFILLED, ReservationStatus.CANCELLED, ReservationStatus.EXPIRED]:
                self.reservation_status = ReservationStatus.EXPIRED
                self.mark_as_modified()
            return True

        return False

    def is_active(self) -> bool:
        """Check if reservation is active"""
        return (
            self.reservation_status in [ReservationStatus.PENDING, ReservationStatus.CONFIRMED, ReservationStatus.PARTIALLY_FULFILLED] and
            not self.is_expired() and
            self.quantity_remaining > 0
        )

    def can_fulfill(self, quantity: int) -> bool:
        """Check if reservation can fulfill requested quantity"""
        return self.is_active() and quantity <= self.quantity_remaining

    def get_time_until_expiry(self) -> Optional[timedelta]:
        """Get time remaining until expiration"""
        if not self.expires_at:
            return None

        if self.is_expired():
            return timedelta(0)

        return self.expires_at - datetime.utcnow()

    def get_fulfillment_rate(self) -> Decimal:
        """Calculate fulfillment percentage"""
        if self.quantity_reserved == 0:
            return Decimal("0")

        rate = (Decimal(self.quantity_fulfilled) / Decimal(self.quantity_reserved)) * 100
        return rate.quantize(Decimal("0.01"))

    def get_age_minutes(self) -> int:
        """Get age of reservation in minutes"""
        age = datetime.utcnow() - self.created_at
        return int(age.total_seconds() / 60)

    def needs_urgent_processing(self) -> bool:
        """Check if reservation needs urgent processing"""
        # High priority
        if self.priority <= 2:
            return True

        # Expiring soon (within 15 minutes)
        time_left = self.get_time_until_expiry()
        if time_left and time_left.total_seconds() < 900:
            return True

        # Old pending reservation (> 2 hours)
        if self.get_age_minutes() > 120 and self.reservation_status == ReservationStatus.PENDING:
            return True

        return False

    def split(self, split_quantity: int) -> 'InventoryReservation':
        """Split reservation into two"""
        if split_quantity <= 0:
            raise BusinessRuleViolation("Split quantity must be positive")

        if split_quantity >= self.quantity_remaining:
            raise BusinessRuleViolation(f"Split quantity must be less than remaining quantity {self.quantity_remaining}")

        # Reduce current reservation
        self.quantity_reserved -= split_quantity
        self._update_remaining_quantity()

        # Create new reservation for split quantity
        new_reservation = InventoryReservation.create(
            store_id=self.store_id,
            inventory_id=self.inventory_id,
            sku=self.sku,
            quantity=split_quantity,
            reservation_type=self.reservation_type,
            order_id=self.order_id,
            customer_id=self.customer_id,
            expires_in_minutes=0,  # Will set expires_at directly
            priority=self.priority,
            unit_price=self.unit_price
        )

        # Copy relevant fields
        new_reservation.expires_at = self.expires_at
        new_reservation.location_id = self.location_id
        new_reservation.location_code = self.location_code
        new_reservation.batch_lot = self.batch_lot
        new_reservation.sales_channel = self.sales_channel

        self.mark_as_modified()
        return new_reservation

    def merge_with(self, other: 'InventoryReservation'):
        """Merge another reservation into this one"""
        if other.inventory_id != self.inventory_id:
            raise BusinessRuleViolation("Cannot merge reservations for different inventory items")

        if other.reservation_type != self.reservation_type:
            raise BusinessRuleViolation("Cannot merge reservations of different types")

        if other.customer_id != self.customer_id:
            raise BusinessRuleViolation("Cannot merge reservations for different customers")

        # Merge quantities
        self.quantity_reserved += other.quantity_reserved
        self.quantity_fulfilled += other.quantity_fulfilled
        self.quantity_cancelled += other.quantity_cancelled
        self._update_remaining_quantity()

        # Update priority to highest (lowest number)
        self.priority = min(self.priority, other.priority)

        # Update expiration to earliest
        if other.expires_at:
            if not self.expires_at or other.expires_at < self.expires_at:
                self.expires_at = other.expires_at

        # Update value
        self.total_value += other.total_value

        self.mark_as_modified()

    def validate(self) -> List[str]:
        """Validate reservation data"""
        errors = []

        if not self.store_id:
            errors.append("Store ID is required")

        if not self.inventory_id:
            errors.append("Inventory ID is required")

        if not self.sku:
            errors.append("SKU is required")

        if self.quantity_reserved < 0:
            errors.append("Reserved quantity cannot be negative")

        if self.quantity_fulfilled < 0:
            errors.append("Fulfilled quantity cannot be negative")

        if self.quantity_cancelled < 0:
            errors.append("Cancelled quantity cannot be negative")

        if self.quantity_fulfilled > self.quantity_reserved:
            errors.append("Fulfilled quantity cannot exceed reserved quantity")

        if self.quantity_cancelled > self.quantity_reserved:
            errors.append("Cancelled quantity cannot exceed reserved quantity")

        if (self.quantity_fulfilled + self.quantity_cancelled) > self.quantity_reserved:
            errors.append("Sum of fulfilled and cancelled cannot exceed reserved quantity")

        if self.priority < 1 or self.priority > 10:
            errors.append("Priority must be between 1 and 10")

        if self.unit_price < 0:
            errors.append("Unit price cannot be negative")

        expected_remaining = self.quantity_reserved - self.quantity_fulfilled - self.quantity_cancelled
        if self.quantity_remaining != expected_remaining:
            errors.append(f"Remaining quantity calculation error: {self.quantity_remaining} != {expected_remaining}")

        return errors