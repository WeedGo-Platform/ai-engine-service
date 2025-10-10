"""
ShelfLocation Entity
Following DDD Architecture Document Section 2.4
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from ....shared.domain_base import Entity, BusinessRuleViolation
from ..value_objects import LocationCode, LocationType


@dataclass
class ShelfLocation(Entity):
    """
    ShelfLocation Entity - Physical warehouse locations
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.4
    """
    # Identifiers
    store_id: UUID = field(default_factory=uuid4)

    # Location Components
    zone: Optional[str] = None  # Warehouse zone
    aisle: Optional[str] = None
    shelf: Optional[str] = None
    bin: Optional[str] = None
    location_code: str = ""  # Generated: "ZONE-AISLE-SHELF-BIN"

    # Location Type
    location_type: LocationType = LocationType.STANDARD

    # Physical Constraints
    max_weight_kg: Optional[Decimal] = None
    max_volume_m3: Optional[Decimal] = None
    current_weight_kg: Decimal = Decimal("0")
    current_volume_m3: Decimal = Decimal("0")

    # Environmental Requirements
    temperature_range: Optional[str] = None  # e.g., "2-8°C", "15-25°C"
    humidity_range: Optional[str] = None  # e.g., "40-60%"
    requires_security: bool = False

    # Capacity
    max_items: Optional[int] = None  # Max number of items/SKUs
    current_items: int = 0

    # Status
    is_active: bool = True
    is_available: bool = True
    is_blocked: bool = False  # Temporarily blocked for maintenance, etc.
    block_reason: Optional[str] = None

    # Usage Tracking
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    last_inventory_date: Optional[datetime] = None

    # Location Value Object
    _location_code_obj: Optional[LocationCode] = None

    # Notes
    notes: Optional[str] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize location code value object"""
        super().__post_init__()
        if self.location_code:
            self._location_code_obj = LocationCode.from_string(
                self.location_code,
                self.location_type
            )

    @classmethod
    def create(
        cls,
        store_id: UUID,
        zone: Optional[str] = None,
        aisle: Optional[str] = None,
        shelf: Optional[str] = None,
        bin: Optional[str] = None,
        location_type: LocationType = LocationType.STANDARD,
        max_weight_kg: Optional[Decimal] = None,
        max_volume_m3: Optional[Decimal] = None
    ) -> 'ShelfLocation':
        """Factory method to create new shelf location"""
        # Create location code
        location_code_obj = LocationCode.create(
            zone=zone,
            aisle=aisle,
            shelf=shelf,
            bin=bin,
            location_type=location_type
        )

        location = cls(
            store_id=store_id,
            zone=zone,
            aisle=aisle,
            shelf=shelf,
            bin=bin,
            location_code=location_code_obj.code,
            location_type=location_type,
            max_weight_kg=max_weight_kg,
            max_volume_m3=max_volume_m3,
            _location_code_obj=location_code_obj
        )

        return location

    def set_environmental_requirements(
        self,
        temperature_range: Optional[str] = None,
        humidity_range: Optional[str] = None,
        requires_security: Optional[bool] = None
    ):
        """Set environmental requirements for the location"""
        if temperature_range:
            self.temperature_range = temperature_range
            # Update location type if cold storage
            if any(cold in temperature_range.lower() for cold in ['2-8', '0-4', 'freezer', 'cold']):
                self.location_type = LocationType.COLD_STORAGE
                self._update_location_code()

        if humidity_range:
            self.humidity_range = humidity_range

        if requires_security is not None:
            self.requires_security = requires_security
            if requires_security and self.location_type == LocationType.STANDARD:
                self.location_type = LocationType.SECURE
                self._update_location_code()

        self.mark_as_modified()

    def _update_location_code(self):
        """Update location code object with new type"""
        self._location_code_obj = LocationCode.create(
            zone=self.zone,
            aisle=self.aisle,
            shelf=self.shelf,
            bin=self.bin,
            location_type=self.location_type
        )
        self.location_code = self._location_code_obj.code

    def set_capacity(
        self,
        max_weight_kg: Optional[Decimal] = None,
        max_volume_m3: Optional[Decimal] = None,
        max_items: Optional[int] = None
    ):
        """Set capacity constraints"""
        if max_weight_kg is not None:
            if max_weight_kg < 0:
                raise BusinessRuleViolation("Max weight cannot be negative")
            self.max_weight_kg = max_weight_kg

        if max_volume_m3 is not None:
            if max_volume_m3 < 0:
                raise BusinessRuleViolation("Max volume cannot be negative")
            self.max_volume_m3 = max_volume_m3

        if max_items is not None:
            if max_items < 0:
                raise BusinessRuleViolation("Max items cannot be negative")
            self.max_items = max_items

        self.mark_as_modified()

    def add_item(
        self,
        weight_kg: Optional[Decimal] = None,
        volume_m3: Optional[Decimal] = None,
        count: int = 1
    ) -> bool:
        """Add item to location"""
        # Check if location is available
        if not self.is_available or self.is_blocked:
            return False

        # Check weight constraint
        if weight_kg and self.max_weight_kg:
            new_weight = self.current_weight_kg + weight_kg
            if new_weight > self.max_weight_kg:
                return False

        # Check volume constraint
        if volume_m3 and self.max_volume_m3:
            new_volume = self.current_volume_m3 + volume_m3
            if new_volume > self.max_volume_m3:
                return False

        # Check item count constraint
        if self.max_items:
            new_count = self.current_items + count
            if new_count > self.max_items:
                return False

        # Update current usage
        if weight_kg:
            self.current_weight_kg += weight_kg
        if volume_m3:
            self.current_volume_m3 += volume_m3
        self.current_items += count

        self.record_access()
        return True

    def remove_item(
        self,
        weight_kg: Optional[Decimal] = None,
        volume_m3: Optional[Decimal] = None,
        count: int = 1
    ):
        """Remove item from location"""
        if weight_kg:
            self.current_weight_kg = max(Decimal("0"), self.current_weight_kg - weight_kg)
        if volume_m3:
            self.current_volume_m3 = max(Decimal("0"), self.current_volume_m3 - volume_m3)
        self.current_items = max(0, self.current_items - count)

        self.record_access()

    def record_access(self):
        """Record location access"""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1
        self.mark_as_modified()

    def block(self, reason: str):
        """Block location temporarily"""
        self.is_blocked = True
        self.is_available = False
        self.block_reason = reason
        self.mark_as_modified()

    def unblock(self):
        """Unblock location"""
        self.is_blocked = False
        self.is_available = True
        self.block_reason = None
        self.mark_as_modified()

    def deactivate(self):
        """Deactivate location permanently"""
        self.is_active = False
        self.is_available = False
        self.mark_as_modified()

    def activate(self):
        """Activate location"""
        self.is_active = True
        self.is_available = True
        self.mark_as_modified()

    def perform_inventory(self):
        """Mark location as inventoried"""
        self.last_inventory_date = datetime.utcnow()
        self.mark_as_modified()

    def clear(self):
        """Clear all items from location"""
        self.current_weight_kg = Decimal("0")
        self.current_volume_m3 = Decimal("0")
        self.current_items = 0
        self.mark_as_modified()

    def get_utilization_weight(self) -> Decimal:
        """Get weight utilization percentage"""
        if not self.max_weight_kg or self.max_weight_kg == 0:
            return Decimal("0")
        utilization = (self.current_weight_kg / self.max_weight_kg) * 100
        return utilization.quantize(Decimal("0.01"))

    def get_utilization_volume(self) -> Decimal:
        """Get volume utilization percentage"""
        if not self.max_volume_m3 or self.max_volume_m3 == 0:
            return Decimal("0")
        utilization = (self.current_volume_m3 / self.max_volume_m3) * 100
        return utilization.quantize(Decimal("0.01"))

    def get_utilization_items(self) -> Decimal:
        """Get item count utilization percentage"""
        if not self.max_items or self.max_items == 0:
            return Decimal("0")
        utilization = (Decimal(self.current_items) / Decimal(self.max_items)) * 100
        return utilization.quantize(Decimal("0.01"))

    def get_overall_utilization(self) -> Decimal:
        """Get overall utilization percentage"""
        utilizations = []

        if self.max_weight_kg:
            utilizations.append(self.get_utilization_weight())
        if self.max_volume_m3:
            utilizations.append(self.get_utilization_volume())
        if self.max_items:
            utilizations.append(self.get_utilization_items())

        if not utilizations:
            return Decimal("0")

        # Return the highest utilization
        return max(utilizations)

    def is_full(self) -> bool:
        """Check if location is at capacity"""
        if self.max_weight_kg and self.current_weight_kg >= self.max_weight_kg:
            return True
        if self.max_volume_m3 and self.current_volume_m3 >= self.max_volume_m3:
            return True
        if self.max_items and self.current_items >= self.max_items:
            return True
        return False

    def is_empty(self) -> bool:
        """Check if location is empty"""
        return self.current_items == 0

    def can_accommodate(
        self,
        weight_kg: Optional[Decimal] = None,
        volume_m3: Optional[Decimal] = None,
        count: int = 1
    ) -> bool:
        """Check if location can accommodate additional items"""
        if not self.is_available or self.is_blocked:
            return False

        if weight_kg and self.max_weight_kg:
            if self.current_weight_kg + weight_kg > self.max_weight_kg:
                return False

        if volume_m3 and self.max_volume_m3:
            if self.current_volume_m3 + volume_m3 > self.max_volume_m3:
                return False

        if self.max_items:
            if self.current_items + count > self.max_items:
                return False

        return True

    def requires_special_handling(self) -> bool:
        """Check if location requires special handling"""
        return self._location_code_obj.requires_special_handling() if self._location_code_obj else False

    def get_access_requirements(self) -> List[str]:
        """Get access requirements for the location"""
        return self._location_code_obj.get_access_requirements() if self._location_code_obj else []

    def get_picking_priority(self) -> int:
        """Get picking priority for warehouse optimization"""
        return self._location_code_obj.get_picking_path() if self._location_code_obj else 999999

    def validate(self) -> List[str]:
        """Validate location data"""
        errors = []

        if not self.location_code:
            errors.append("Location code is required")

        if self.current_weight_kg < 0:
            errors.append("Current weight cannot be negative")

        if self.current_volume_m3 < 0:
            errors.append("Current volume cannot be negative")

        if self.current_items < 0:
            errors.append("Current items cannot be negative")

        if self.max_weight_kg and self.current_weight_kg > self.max_weight_kg:
            errors.append("Current weight exceeds maximum")

        if self.max_volume_m3 and self.current_volume_m3 > self.max_volume_m3:
            errors.append("Current volume exceeds maximum")

        if self.max_items and self.current_items > self.max_items:
            errors.append("Current item count exceeds maximum")

        return errors