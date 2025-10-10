"""
StockLevel Value Object
Following DDD Architecture Document Section 2.4
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from ....shared.domain_base import ValueObject


class StockStatus(str, Enum):
    """Stock availability status"""
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    BACKORDERED = "backordered"
    DISCONTINUED = "discontinued"
    RESERVED = "reserved"
    PENDING = "pending"


@dataclass(frozen=True)
class StockLevel(ValueObject):
    """
    StockLevel Value Object - Inventory stock levels and thresholds
    Immutable value object for stock management

    Note on database mapping:
    - quantity_on_hand → maps to 'quantity' column in database
    - min_stock_level → for low stock alerts (distinct from reorder_point)
    - reorder_point → threshold for triggering purchase orders
    """
    quantity_on_hand: int  # DB column: 'quantity'
    quantity_available: int
    quantity_reserved: int
    reorder_point: int  # DB column: 'reorder_point' (primary threshold)
    reorder_quantity: int
    min_stock_level: int  # For low stock status (may map to reorder_point if DB simplified)
    max_stock_level: int

    def __post_init__(self):
        """Validate stock levels"""
        if self.quantity_on_hand < 0:
            raise ValueError("Quantity on hand cannot be negative")
        if self.quantity_available < 0:
            raise ValueError("Quantity available cannot be negative")
        if self.quantity_reserved < 0:
            raise ValueError("Quantity reserved cannot be negative")
        if self.min_stock_level < 0:
            raise ValueError("Min stock level cannot be negative")
        if self.max_stock_level < self.min_stock_level:
            raise ValueError("Max stock level must be >= min stock level")
        if self.reorder_point < 0:
            raise ValueError("Reorder point cannot be negative")
        if self.reorder_quantity <= 0:
            raise ValueError("Reorder quantity must be positive")

        # Verify consistency
        if self.quantity_available != (self.quantity_on_hand - self.quantity_reserved):
            raise ValueError("Quantity available must equal on_hand minus reserved")

    def get_status(self) -> StockStatus:
        """Determine stock status based on levels"""
        if self.quantity_available == 0:
            return StockStatus.OUT_OF_STOCK
        elif self.quantity_available <= self.min_stock_level:
            return StockStatus.LOW_STOCK
        else:
            return StockStatus.IN_STOCK

    def needs_reorder(self) -> bool:
        """Check if stock needs reordering"""
        return self.quantity_available <= self.reorder_point

    def get_reorder_amount(self) -> int:
        """Calculate amount to reorder to reach max stock"""
        if not self.needs_reorder():
            return 0

        # Order enough to reach max stock level
        target = self.max_stock_level
        current = self.quantity_on_hand
        needed = target - current

        # Round up to reorder quantity multiple
        if needed % self.reorder_quantity != 0:
            needed = ((needed // self.reorder_quantity) + 1) * self.reorder_quantity

        return max(needed, self.reorder_quantity)

    def can_reserve(self, quantity: int) -> bool:
        """Check if quantity can be reserved"""
        return quantity > 0 and quantity <= self.quantity_available

    def reserve(self, quantity: int) -> 'StockLevel':
        """Create new stock level with reserved quantity"""
        if not self.can_reserve(quantity):
            raise ValueError(f"Cannot reserve {quantity} items")

        return StockLevel(
            quantity_on_hand=self.quantity_on_hand,
            quantity_available=self.quantity_available - quantity,
            quantity_reserved=self.quantity_reserved + quantity,
            reorder_point=self.reorder_point,
            reorder_quantity=self.reorder_quantity,
            min_stock_level=self.min_stock_level,
            max_stock_level=self.max_stock_level
        )

    def release_reservation(self, quantity: int) -> 'StockLevel':
        """Create new stock level with released reservation"""
        if quantity > self.quantity_reserved:
            raise ValueError(f"Cannot release {quantity}, only {self.quantity_reserved} reserved")

        return StockLevel(
            quantity_on_hand=self.quantity_on_hand,
            quantity_available=self.quantity_available + quantity,
            quantity_reserved=self.quantity_reserved - quantity,
            reorder_point=self.reorder_point,
            reorder_quantity=self.reorder_quantity,
            min_stock_level=self.min_stock_level,
            max_stock_level=self.max_stock_level
        )

    def adjust_stock(self, adjustment: int) -> 'StockLevel':
        """Create new stock level with adjusted quantity"""
        new_on_hand = self.quantity_on_hand + adjustment
        if new_on_hand < 0:
            raise ValueError("Adjustment would result in negative stock")

        # If reducing stock, ensure we don't go below reserved
        if adjustment < 0 and new_on_hand < self.quantity_reserved:
            raise ValueError("Cannot reduce stock below reserved quantity")

        return StockLevel(
            quantity_on_hand=new_on_hand,
            quantity_available=new_on_hand - self.quantity_reserved,
            quantity_reserved=self.quantity_reserved,
            reorder_point=self.reorder_point,
            reorder_quantity=self.reorder_quantity,
            min_stock_level=self.min_stock_level,
            max_stock_level=self.max_stock_level
        )

    def receive_stock(self, quantity: int) -> 'StockLevel':
        """Create new stock level after receiving stock"""
        if quantity <= 0:
            raise ValueError("Receive quantity must be positive")

        return self.adjust_stock(quantity)

    def consume_stock(self, quantity: int) -> 'StockLevel':
        """Create new stock level after consuming stock"""
        if quantity <= 0:
            raise ValueError("Consume quantity must be positive")

        # First release from reserved if it was reserved
        if quantity <= self.quantity_reserved:
            # All consumed from reserved
            return StockLevel(
                quantity_on_hand=self.quantity_on_hand - quantity,
                quantity_available=self.quantity_available,
                quantity_reserved=self.quantity_reserved - quantity,
                reorder_point=self.reorder_point,
                reorder_quantity=self.reorder_quantity,
                min_stock_level=self.min_stock_level,
                max_stock_level=self.max_stock_level
            )
        else:
            # Consume from both reserved and available
            return self.adjust_stock(-quantity)

    def get_stock_percentage(self) -> float:
        """Get stock level as percentage of max"""
        if self.max_stock_level == 0:
            return 0.0
        return (self.quantity_on_hand / self.max_stock_level) * 100

    def get_availability_percentage(self) -> float:
        """Get availability as percentage of on hand"""
        if self.quantity_on_hand == 0:
            return 0.0
        return (self.quantity_available / self.quantity_on_hand) * 100

    def is_overstocked(self) -> bool:
        """Check if inventory is overstocked"""
        return self.quantity_on_hand > self.max_stock_level

    def __str__(self) -> str:
        return f"Stock: {self.quantity_available}/{self.quantity_on_hand} (Reserved: {self.quantity_reserved})"