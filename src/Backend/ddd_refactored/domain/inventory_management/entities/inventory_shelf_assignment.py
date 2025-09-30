"""
InventoryShelfAssignment Entity
Following DDD Architecture Document Section 2.4
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from ....shared.domain_base import Entity, BusinessRuleViolation


@dataclass
class InventoryShelfAssignment(Entity):
    """
    InventoryShelfAssignment Entity - Junction between Inventory and ShelfLocation
    Maps products to their physical warehouse locations
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.4
    """
    # Identifiers
    inventory_id: UUID = field(default_factory=uuid4)
    location_id: UUID = field(default_factory=uuid4)
    store_id: UUID = field(default_factory=uuid4)

    # Product Information
    sku: str = ""
    product_name: Optional[str] = None

    # Batch Information
    batch_lot: Optional[str] = None  # Optional batch/lot number
    batch_id: Optional[UUID] = None  # Link to BatchTracking

    # Quantities
    quantity_at_location: int = 0
    quantity_reserved: int = 0  # Reserved at this specific location
    quantity_available: int = 0  # Available at this location

    # Location Details
    location_code: str = ""  # Denormalized for quick access
    zone: Optional[str] = None
    aisle: Optional[str] = None
    shelf: Optional[str] = None
    bin: Optional[str] = None

    # Assignment Type
    assignment_type: str = "primary"  # primary, overflow, temporary, returns
    is_primary_location: bool = True

    # Picking Information
    picking_priority: int = 1  # Lower number = higher priority
    picking_notes: Optional[str] = None

    # Physical Constraints
    max_quantity: Optional[int] = None  # Max units at this location
    min_quantity: Optional[int] = None  # Min units to maintain

    # Status
    is_active: bool = True
    is_available_for_picking: bool = True

    # Dates
    assigned_date: datetime = field(default_factory=datetime.utcnow)
    last_picked_date: Optional[datetime] = None
    last_restocked_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None  # For batch-tracked items

    # Performance Metrics
    pick_count: int = 0  # Number of picks from this location
    restock_count: int = 0  # Number of restocks

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        inventory_id: UUID,
        location_id: UUID,
        store_id: UUID,
        sku: str,
        quantity: int,
        location_code: str,
        assignment_type: str = "primary",
        batch_lot: Optional[str] = None
    ) -> 'InventoryShelfAssignment':
        """Factory method to create new assignment"""
        if quantity < 0:
            raise BusinessRuleViolation("Quantity cannot be negative")

        if assignment_type not in ['primary', 'overflow', 'temporary', 'returns']:
            raise BusinessRuleViolation(f"Invalid assignment type: {assignment_type}")

        assignment = cls(
            inventory_id=inventory_id,
            location_id=location_id,
            store_id=store_id,
            sku=sku,
            quantity_at_location=quantity,
            quantity_available=quantity,
            quantity_reserved=0,
            location_code=location_code,
            assignment_type=assignment_type,
            is_primary_location=(assignment_type == "primary"),
            batch_lot=batch_lot
        )

        return assignment

    def assign_quantity(self, quantity: int) -> bool:
        """Assign additional quantity to this location"""
        if quantity <= 0:
            raise BusinessRuleViolation("Assign quantity must be positive")

        if self.max_quantity and (self.quantity_at_location + quantity) > self.max_quantity:
            return False

        self.quantity_at_location += quantity
        self.quantity_available += quantity
        self.last_restocked_date = datetime.utcnow()
        self.restock_count += 1
        self.mark_as_modified()
        return True

    def pick_quantity(self, quantity: int) -> bool:
        """Pick quantity from this location"""
        if quantity <= 0:
            raise BusinessRuleViolation("Pick quantity must be positive")

        if quantity > self.quantity_available:
            return False

        self.quantity_at_location -= quantity
        self.quantity_available -= quantity
        self.last_picked_date = datetime.utcnow()
        self.pick_count += 1

        # Check if we're below minimum
        if self.min_quantity and self.quantity_at_location < self.min_quantity:
            self.metadata['needs_restock'] = True
            self.metadata['below_min_since'] = datetime.utcnow().isoformat()

        self.mark_as_modified()
        return True

    def reserve_quantity(self, quantity: int) -> bool:
        """Reserve quantity at this location"""
        if quantity <= 0:
            raise BusinessRuleViolation("Reserve quantity must be positive")

        if quantity > self.quantity_available:
            return False

        self.quantity_reserved += quantity
        self.quantity_available -= quantity
        self.mark_as_modified()
        return True

    def release_reservation(self, quantity: int):
        """Release reserved quantity"""
        if quantity <= 0:
            raise BusinessRuleViolation("Release quantity must be positive")

        if quantity > self.quantity_reserved:
            raise BusinessRuleViolation(f"Cannot release {quantity}, only {self.quantity_reserved} reserved")

        self.quantity_reserved -= quantity
        self.quantity_available += quantity
        self.mark_as_modified()

    def transfer_to_location(self, new_location_id: UUID, new_location_code: str, quantity: int) -> 'InventoryShelfAssignment':
        """Transfer quantity to another location"""
        if quantity <= 0:
            raise BusinessRuleViolation("Transfer quantity must be positive")

        if quantity > self.quantity_available:
            raise BusinessRuleViolation(f"Cannot transfer {quantity}, only {self.quantity_available} available")

        # Reduce quantity at current location
        self.quantity_at_location -= quantity
        self.quantity_available -= quantity

        # Create new assignment for target location
        new_assignment = InventoryShelfAssignment.create(
            inventory_id=self.inventory_id,
            location_id=new_location_id,
            store_id=self.store_id,
            sku=self.sku,
            quantity=quantity,
            location_code=new_location_code,
            assignment_type="temporary",
            batch_lot=self.batch_lot
        )

        self.mark_as_modified()
        return new_assignment

    def set_location_details(
        self,
        zone: Optional[str] = None,
        aisle: Optional[str] = None,
        shelf: Optional[str] = None,
        bin: Optional[str] = None
    ):
        """Set location component details"""
        if zone:
            self.zone = zone
        if aisle:
            self.aisle = aisle
        if shelf:
            self.shelf = shelf
        if bin:
            self.bin = bin

        self.mark_as_modified()

    def set_constraints(
        self,
        max_quantity: Optional[int] = None,
        min_quantity: Optional[int] = None
    ):
        """Set quantity constraints for this location"""
        if max_quantity is not None:
            if max_quantity < 0:
                raise BusinessRuleViolation("Max quantity cannot be negative")
            if max_quantity < self.quantity_at_location:
                raise BusinessRuleViolation("Max quantity cannot be less than current quantity")
            self.max_quantity = max_quantity

        if min_quantity is not None:
            if min_quantity < 0:
                raise BusinessRuleViolation("Min quantity cannot be negative")
            if max_quantity and min_quantity > max_quantity:
                raise BusinessRuleViolation("Min quantity cannot exceed max quantity")
            self.min_quantity = min_quantity

        self.mark_as_modified()

    def update_picking_priority(self, priority: int):
        """Update picking priority"""
        if priority < 1:
            raise BusinessRuleViolation("Picking priority must be >= 1")

        self.picking_priority = priority
        self.mark_as_modified()

    def mark_as_primary(self):
        """Mark this as the primary location for the product"""
        self.is_primary_location = True
        self.assignment_type = "primary"
        self.picking_priority = 1
        self.mark_as_modified()

    def mark_as_overflow(self):
        """Mark this as an overflow location"""
        self.is_primary_location = False
        self.assignment_type = "overflow"
        self.picking_priority = 2
        self.mark_as_modified()

    def deactivate(self):
        """Deactivate this assignment"""
        self.is_active = False
        self.is_available_for_picking = False
        self.mark_as_modified()

    def activate(self):
        """Activate this assignment"""
        self.is_active = True
        self.is_available_for_picking = True
        self.mark_as_modified()

    def needs_restock(self) -> bool:
        """Check if location needs restocking"""
        if not self.is_active:
            return False

        if self.min_quantity and self.quantity_at_location < self.min_quantity:
            return True

        # Check metadata for restock flag
        return self.metadata.get('needs_restock', False)

    def is_empty(self) -> bool:
        """Check if location is empty"""
        return self.quantity_at_location == 0

    def is_full(self) -> bool:
        """Check if location is at capacity"""
        if not self.max_quantity:
            return False
        return self.quantity_at_location >= self.max_quantity

    def get_fill_rate(self) -> Decimal:
        """Calculate location fill rate percentage"""
        if not self.max_quantity or self.max_quantity == 0:
            return Decimal("0")

        rate = (Decimal(self.quantity_at_location) / Decimal(self.max_quantity)) * 100
        return rate.quantize(Decimal("0.01"))

    def get_pick_efficiency(self) -> Decimal:
        """Calculate pick efficiency based on pick count and time"""
        if self.pick_count == 0:
            return Decimal("0")

        # Simple efficiency metric - can be enhanced with time-based calculations
        if not self.assigned_date:
            return Decimal("0")

        days_active = (datetime.utcnow() - self.assigned_date).days or 1
        picks_per_day = Decimal(self.pick_count) / Decimal(days_active)
        return picks_per_day.quantize(Decimal("0.01"))

    def validate(self) -> list[str]:
        """Validate assignment data"""
        errors = []

        if not self.inventory_id:
            errors.append("Inventory ID is required")

        if not self.location_id:
            errors.append("Location ID is required")

        if not self.store_id:
            errors.append("Store ID is required")

        if not self.sku:
            errors.append("SKU is required")

        if self.quantity_at_location < 0:
            errors.append("Quantity at location cannot be negative")

        if self.quantity_reserved < 0:
            errors.append("Reserved quantity cannot be negative")

        if self.quantity_available < 0:
            errors.append("Available quantity cannot be negative")

        if self.quantity_available != (self.quantity_at_location - self.quantity_reserved):
            errors.append("Available quantity must equal quantity at location minus reserved")

        if self.picking_priority < 1:
            errors.append("Picking priority must be >= 1")

        if self.max_quantity and self.quantity_at_location > self.max_quantity:
            errors.append("Current quantity exceeds maximum")

        if self.min_quantity and self.max_quantity and self.min_quantity > self.max_quantity:
            errors.append("Min quantity cannot exceed max quantity")

        return errors