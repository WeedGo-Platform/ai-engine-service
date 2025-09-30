"""
Inventory Entity
Following DDD Architecture Document Section 2.4
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from ....shared.domain_base import AggregateRoot, DomainEvent, BusinessRuleViolation
from ..value_objects import StockLevel, StockStatus, GTIN


class StockAdjusted(DomainEvent):
    """Event raised when stock is adjusted"""
    inventory_id: UUID
    sku: str
    adjustment: int
    new_quantity: int
    reason: str


class StockReserved(DomainEvent):
    """Event raised when stock is reserved"""
    inventory_id: UUID
    sku: str
    quantity: int
    reservation_id: UUID


class StockReleased(DomainEvent):
    """Event raised when reserved stock is released"""
    inventory_id: UUID
    sku: str
    quantity: int
    reservation_id: UUID


class LowStockAlert(DomainEvent):
    """Event raised when stock reaches low level"""
    inventory_id: UUID
    sku: str
    current_quantity: int
    reorder_point: int


class StockReceived(DomainEvent):
    """Event raised when stock is received"""
    inventory_id: UUID
    sku: str
    quantity: int
    purchase_order_id: Optional[UUID]


@dataclass
class Inventory(AggregateRoot):
    """
    Inventory Aggregate Root - Stock management for products
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.4
    """
    # Identifiers
    store_id: UUID = field(default_factory=uuid4)
    sku: str = ""  # Product SKU

    # Stock Levels
    quantity_on_hand: int = 0
    quantity_available: int = 0
    quantity_reserved: int = 0

    # Pricing
    unit_cost: Decimal = Decimal("0")
    retail_price: Decimal = Decimal("0")  # Generated or override
    retail_price_dynamic: Optional[Decimal] = None  # Dynamic pricing
    override_price: Optional[Decimal] = None  # Manual price override

    # Stock Management
    reorder_point: int = 0
    reorder_quantity: int = 0
    min_stock_level: int = 0
    max_stock_level: int = 100

    # Product Information
    product_name: Optional[str] = None
    case_gtin: Optional[str] = None  # Global Trade Item Number for case
    each_gtin: Optional[str] = None  # GTIN for individual units

    # Status
    is_available: bool = True
    last_restock_date: Optional[datetime] = None
    last_sale_date: Optional[datetime] = None
    last_count_date: Optional[datetime] = None

    # Stock Level Value Object
    _stock_level: Optional[StockLevel] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize stock level value object"""
        super().__post_init__()
        self._update_stock_level()

    def _update_stock_level(self):
        """Update the stock level value object"""
        self._stock_level = StockLevel(
            quantity_on_hand=self.quantity_on_hand,
            quantity_available=self.quantity_available,
            quantity_reserved=self.quantity_reserved,
            reorder_point=self.reorder_point,
            reorder_quantity=self.reorder_quantity,
            min_stock_level=self.min_stock_level,
            max_stock_level=self.max_stock_level
        )

    @classmethod
    def create(
        cls,
        store_id: UUID,
        sku: str,
        product_name: str,
        initial_quantity: int = 0,
        unit_cost: Decimal = Decimal("0"),
        retail_price: Decimal = Decimal("0"),
        reorder_point: int = 10,
        reorder_quantity: int = 50,
        min_stock_level: int = 5,
        max_stock_level: int = 100
    ) -> 'Inventory':
        """Factory method to create new inventory item"""
        if not sku:
            raise BusinessRuleViolation("SKU is required")
        if initial_quantity < 0:
            raise BusinessRuleViolation("Initial quantity cannot be negative")
        if unit_cost < 0:
            raise BusinessRuleViolation("Unit cost cannot be negative")
        if retail_price < 0:
            raise BusinessRuleViolation("Retail price cannot be negative")

        inventory = cls(
            store_id=store_id,
            sku=sku,
            product_name=product_name,
            quantity_on_hand=initial_quantity,
            quantity_available=initial_quantity,
            quantity_reserved=0,
            unit_cost=unit_cost,
            retail_price=retail_price,
            reorder_point=reorder_point,
            reorder_quantity=reorder_quantity,
            min_stock_level=min_stock_level,
            max_stock_level=max_stock_level
        )

        return inventory

    def adjust_stock(self, adjustment: int, reason: str = "Manual adjustment"):
        """Adjust stock levels"""
        new_stock_level = self._stock_level.adjust_stock(adjustment)

        # Update quantities
        self.quantity_on_hand = new_stock_level.quantity_on_hand
        self.quantity_available = new_stock_level.quantity_available
        self._stock_level = new_stock_level

        # Raise event
        self.add_domain_event(StockAdjusted(
            inventory_id=self.id,
            sku=self.sku,
            adjustment=adjustment,
            new_quantity=self.quantity_on_hand,
            reason=reason
        ))

        # Check for low stock
        self._check_low_stock()

        self.mark_as_modified()

    def receive_stock(
        self,
        quantity: int,
        unit_cost: Optional[Decimal] = None,
        purchase_order_id: Optional[UUID] = None
    ):
        """Receive stock from purchase order"""
        if quantity <= 0:
            raise BusinessRuleViolation("Receive quantity must be positive")

        # Update stock levels
        new_stock_level = self._stock_level.receive_stock(quantity)
        self.quantity_on_hand = new_stock_level.quantity_on_hand
        self.quantity_available = new_stock_level.quantity_available
        self._stock_level = new_stock_level

        # Update cost if provided (weighted average)
        if unit_cost is not None:
            if unit_cost < 0:
                raise BusinessRuleViolation("Unit cost cannot be negative")

            # Calculate weighted average cost
            total_value = (self.unit_cost * Decimal(self.quantity_on_hand - quantity)) + (unit_cost * Decimal(quantity))
            self.unit_cost = total_value / Decimal(self.quantity_on_hand)

        self.last_restock_date = datetime.utcnow()

        # Raise event
        self.add_domain_event(StockReceived(
            inventory_id=self.id,
            sku=self.sku,
            quantity=quantity,
            purchase_order_id=purchase_order_id
        ))

        self.mark_as_modified()

    def reserve_stock(self, quantity: int, reservation_id: UUID) -> bool:
        """Reserve stock for an order"""
        if not self._stock_level.can_reserve(quantity):
            return False

        # Update stock levels
        new_stock_level = self._stock_level.reserve(quantity)
        self.quantity_available = new_stock_level.quantity_available
        self.quantity_reserved = new_stock_level.quantity_reserved
        self._stock_level = new_stock_level

        # Raise event
        self.add_domain_event(StockReserved(
            inventory_id=self.id,
            sku=self.sku,
            quantity=quantity,
            reservation_id=reservation_id
        ))

        self.mark_as_modified()
        return True

    def release_reservation(self, quantity: int, reservation_id: UUID):
        """Release reserved stock"""
        if quantity > self.quantity_reserved:
            raise BusinessRuleViolation(f"Cannot release {quantity}, only {self.quantity_reserved} reserved")

        # Update stock levels
        new_stock_level = self._stock_level.release_reservation(quantity)
        self.quantity_available = new_stock_level.quantity_available
        self.quantity_reserved = new_stock_level.quantity_reserved
        self._stock_level = new_stock_level

        # Raise event
        self.add_domain_event(StockReleased(
            inventory_id=self.id,
            sku=self.sku,
            quantity=quantity,
            reservation_id=reservation_id
        ))

        self.mark_as_modified()

    def consume_stock(self, quantity: int):
        """Consume stock for a sale"""
        if quantity <= 0:
            raise BusinessRuleViolation("Consume quantity must be positive")

        # Update stock levels
        new_stock_level = self._stock_level.consume_stock(quantity)
        self.quantity_on_hand = new_stock_level.quantity_on_hand
        self.quantity_available = new_stock_level.quantity_available
        self.quantity_reserved = new_stock_level.quantity_reserved
        self._stock_level = new_stock_level

        self.last_sale_date = datetime.utcnow()

        # Check for low stock
        self._check_low_stock()

        self.mark_as_modified()

    def update_pricing(
        self,
        retail_price: Optional[Decimal] = None,
        unit_cost: Optional[Decimal] = None,
        override_price: Optional[Decimal] = None,
        dynamic_price: Optional[Decimal] = None
    ):
        """Update pricing information"""
        if retail_price is not None:
            if retail_price < 0:
                raise BusinessRuleViolation("Retail price cannot be negative")
            self.retail_price = retail_price

        if unit_cost is not None:
            if unit_cost < 0:
                raise BusinessRuleViolation("Unit cost cannot be negative")
            self.unit_cost = unit_cost

        if override_price is not None:
            if override_price < 0:
                raise BusinessRuleViolation("Override price cannot be negative")
            self.override_price = override_price

        if dynamic_price is not None:
            if dynamic_price < 0:
                raise BusinessRuleViolation("Dynamic price cannot be negative")
            self.retail_price_dynamic = dynamic_price

        self.mark_as_modified()

    def update_reorder_levels(
        self,
        reorder_point: Optional[int] = None,
        reorder_quantity: Optional[int] = None,
        min_stock: Optional[int] = None,
        max_stock: Optional[int] = None
    ):
        """Update reorder levels and thresholds"""
        if reorder_point is not None:
            if reorder_point < 0:
                raise BusinessRuleViolation("Reorder point cannot be negative")
            self.reorder_point = reorder_point

        if reorder_quantity is not None:
            if reorder_quantity <= 0:
                raise BusinessRuleViolation("Reorder quantity must be positive")
            self.reorder_quantity = reorder_quantity

        if min_stock is not None:
            if min_stock < 0:
                raise BusinessRuleViolation("Min stock cannot be negative")
            self.min_stock_level = min_stock

        if max_stock is not None:
            if max_stock < min_stock or self.min_stock_level:
                raise BusinessRuleViolation("Max stock must be >= min stock")
            self.max_stock_level = max_stock

        # Update stock level value object
        self._update_stock_level()

        # Check if we need to reorder
        self._check_low_stock()

        self.mark_as_modified()

    def set_gtin(self, case_gtin: Optional[str] = None, each_gtin: Optional[str] = None):
        """Set GTIN codes for the inventory item"""
        if case_gtin:
            # Validate GTIN
            try:
                gtin = GTIN.from_string(case_gtin)
                self.case_gtin = gtin.format_for_barcode()
            except ValueError as e:
                raise BusinessRuleViolation(f"Invalid case GTIN: {e}")

        if each_gtin:
            # Validate GTIN
            try:
                gtin = GTIN.from_string(each_gtin)
                self.each_gtin = gtin.format_for_barcode()
            except ValueError as e:
                raise BusinessRuleViolation(f"Invalid each GTIN: {e}")

        self.mark_as_modified()

    def perform_cycle_count(self, counted_quantity: int, adjusted_by: UUID):
        """Perform cycle count and adjust if needed"""
        self.last_count_date = datetime.utcnow()

        # Calculate variance
        variance = counted_quantity - self.quantity_on_hand

        if variance != 0:
            # Adjust stock to match count
            self.adjust_stock(variance, f"Cycle count adjustment by {adjusted_by}")
        else:
            self.mark_as_modified()

    def _check_low_stock(self):
        """Check if stock is low and raise alert if needed"""
        if self._stock_level.needs_reorder():
            self.add_domain_event(LowStockAlert(
                inventory_id=self.id,
                sku=self.sku,
                current_quantity=self.quantity_available,
                reorder_point=self.reorder_point
            ))

    def get_stock_status(self) -> StockStatus:
        """Get current stock status"""
        return self._stock_level.get_status()

    def needs_reorder(self) -> bool:
        """Check if item needs reordering"""
        return self._stock_level.needs_reorder()

    def get_reorder_amount(self) -> int:
        """Calculate amount to reorder"""
        return self._stock_level.get_reorder_amount()

    def get_effective_price(self) -> Decimal:
        """Get the effective selling price"""
        if self.override_price is not None:
            return self.override_price
        elif self.retail_price_dynamic is not None:
            return self.retail_price_dynamic
        else:
            return self.retail_price

    def get_margin(self) -> Decimal:
        """Calculate profit margin"""
        if self.unit_cost == 0:
            return Decimal("100")
        effective_price = self.get_effective_price()
        margin = ((effective_price - self.unit_cost) / effective_price) * 100
        return margin.quantize(Decimal("0.01"))

    def get_inventory_value(self) -> Decimal:
        """Calculate total inventory value at cost"""
        return self.unit_cost * Decimal(self.quantity_on_hand)

    def get_retail_value(self) -> Decimal:
        """Calculate total inventory value at retail"""
        return self.get_effective_price() * Decimal(self.quantity_on_hand)

    def is_overstocked(self) -> bool:
        """Check if inventory is overstocked"""
        return self._stock_level.is_overstocked()

    def set_availability(self, is_available: bool):
        """Set product availability"""
        self.is_available = is_available
        self.mark_as_modified()

    def validate(self) -> List[str]:
        """Validate inventory data"""
        errors = []

        if not self.sku:
            errors.append("SKU is required")

        if not self.store_id:
            errors.append("Store ID is required")

        if self.quantity_on_hand < 0:
            errors.append("Quantity on hand cannot be negative")

        if self.quantity_available < 0:
            errors.append("Quantity available cannot be negative")

        if self.quantity_reserved < 0:
            errors.append("Quantity reserved cannot be negative")

        if self.quantity_available != (self.quantity_on_hand - self.quantity_reserved):
            errors.append("Quantity available must equal on_hand minus reserved")

        if self.unit_cost < 0:
            errors.append("Unit cost cannot be negative")

        if self.retail_price < 0:
            errors.append("Retail price cannot be negative")

        if self.min_stock_level < 0:
            errors.append("Min stock level cannot be negative")

        if self.max_stock_level < self.min_stock_level:
            errors.append("Max stock level must be >= min stock level")

        if self.reorder_point < 0:
            errors.append("Reorder point cannot be negative")

        if self.reorder_quantity <= 0:
            errors.append("Reorder quantity must be positive")

        return errors