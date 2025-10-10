"""
LocationCode Value Object
Following DDD Architecture Document Section 2.4
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List
import re

from ....shared.domain_base import ValueObject


class LocationType(str, Enum):
    """Types of warehouse locations"""
    STANDARD = "standard"
    COLD_STORAGE = "cold_storage"
    SECURE = "secure"  # For high-value or controlled items
    BULK = "bulk"  # For large quantity storage
    DISPLAY = "display"  # Retail floor display
    QUARANTINE = "quarantine"  # For items awaiting inspection
    RETURNS = "returns"  # For returned items
    STAGING = "staging"  # Temporary holding for shipments
    PICKING = "picking"  # Primary picking locations


@dataclass(frozen=True)
class LocationCode(ValueObject):
    """
    LocationCode Value Object - Warehouse location identifier
    Format: ZONE-AISLE-SHELF-BIN (e.g., "A-01-03-B")
    """
    zone: Optional[str]  # Warehouse zone (e.g., A, B, C)
    aisle: Optional[str]  # Aisle number
    shelf: Optional[str]  # Shelf level
    bin: Optional[str]  # Bin position
    location_type: LocationType
    code: str  # Generated code

    def __post_init__(self):
        """Validate location code components"""
        # Validate that at least one component is provided
        if not any([self.zone, self.aisle, self.shelf, self.bin]):
            raise ValueError("At least one location component must be provided")

        # Validate code matches components
        expected_code = self.generate_code()
        if self.code != expected_code:
            raise ValueError(f"Location code '{self.code}' doesn't match components")

        # Validate component formats
        if self.zone and not re.match(r'^[A-Z]{1,3}$', self.zone):
            raise ValueError(f"Zone must be 1-3 uppercase letters: {self.zone}")

        if self.aisle and not re.match(r'^[0-9]{1,3}$', self.aisle):
            raise ValueError(f"Aisle must be 1-3 digits: {self.aisle}")

        if self.shelf and not re.match(r'^[0-9A-Z]{1,3}$', self.shelf):
            raise ValueError(f"Shelf must be 1-3 alphanumeric characters: {self.shelf}")

        if self.bin and not re.match(r'^[A-Z0-9]{1,4}$', self.bin):
            raise ValueError(f"Bin must be 1-4 alphanumeric characters: {self.bin}")

    @classmethod
    def create(
        cls,
        zone: Optional[str] = None,
        aisle: Optional[str] = None,
        shelf: Optional[str] = None,
        bin: Optional[str] = None,
        location_type: LocationType = LocationType.STANDARD
    ) -> 'LocationCode':
        """Factory method to create LocationCode"""
        # Normalize inputs
        zone = zone.upper() if zone else None
        aisle = aisle.zfill(2) if aisle else None  # Pad with zeros
        shelf = shelf.upper() if shelf else None
        bin = bin.upper() if bin else None

        # Generate code
        components = []
        if zone:
            components.append(zone)
        if aisle:
            components.append(aisle)
        if shelf:
            components.append(shelf)
        if bin:
            components.append(bin)

        code = '-'.join(components) if components else ""

        return cls(
            zone=zone,
            aisle=aisle,
            shelf=shelf,
            bin=bin,
            location_type=location_type,
            code=code
        )

    def generate_code(self) -> str:
        """Generate location code from components"""
        components = []
        if self.zone:
            components.append(self.zone)
        if self.aisle:
            components.append(self.aisle)
        if self.shelf:
            components.append(self.shelf)
        if self.bin:
            components.append(self.bin)

        return '-'.join(components) if components else ""

    @classmethod
    def from_string(cls, code_string: str, location_type: LocationType = LocationType.STANDARD) -> 'LocationCode':
        """Parse location code from string"""
        if not code_string:
            raise ValueError("Location code cannot be empty")

        # Split by common separators
        parts = re.split(r'[-_/\s]', code_string.upper())
        parts = [p for p in parts if p]  # Remove empty parts

        if len(parts) == 0 or len(parts) > 4:
            raise ValueError(f"Invalid location code format: {code_string}")

        # Map parts to components based on count
        zone = None
        aisle = None
        shelf = None
        bin = None

        if len(parts) >= 1:
            zone = parts[0] if re.match(r'^[A-Z]{1,3}$', parts[0]) else None
            if not zone:
                # First part might be aisle if numeric
                if re.match(r'^[0-9]{1,3}$', parts[0]):
                    aisle = parts[0]

        if len(parts) >= 2:
            if not aisle:
                aisle = parts[1] if re.match(r'^[0-9]{1,3}$', parts[1]) else None
            else:
                shelf = parts[1]

        if len(parts) >= 3:
            if not shelf:
                shelf = parts[2]
            else:
                bin = parts[2]

        if len(parts) == 4:
            bin = parts[3]

        return cls.create(zone, aisle, shelf, bin, location_type)

    def get_zone_section(self) -> str:
        """Get zone and aisle as section identifier"""
        parts = []
        if self.zone:
            parts.append(self.zone)
        if self.aisle:
            parts.append(self.aisle)
        return '-'.join(parts) if parts else "UNZONED"

    def get_picking_path(self) -> int:
        """
        Calculate picking path order for efficient warehouse navigation
        Returns an integer for sorting locations in picking order
        """
        # Zone priority (A=1, B=2, etc.)
        zone_value = ord(self.zone[0]) - ord('A') + 1 if self.zone else 999

        # Aisle number
        aisle_value = int(self.aisle) if self.aisle and self.aisle.isdigit() else 999

        # Shelf level (lower shelves first for ergonomics)
        shelf_value = 0
        if self.shelf:
            if self.shelf.isdigit():
                shelf_value = int(self.shelf)
            else:
                # Convert alphanumeric to number
                shelf_value = ord(self.shelf[0]) - ord('A') + 100

        # Bin position
        bin_value = 0
        if self.bin:
            if self.bin[0].isdigit():
                bin_value = int(self.bin[0])
            else:
                bin_value = ord(self.bin[0]) - ord('A') + 1

        # Combine into sortable integer
        # Format: ZZZAAASSSBB (Zone, Aisle, Shelf, Bin)
        return (zone_value * 1000000) + (aisle_value * 10000) + (shelf_value * 100) + bin_value

    def is_adjacent_to(self, other: 'LocationCode') -> bool:
        """Check if two locations are adjacent"""
        if self.zone != other.zone:
            return False

        # Check aisle adjacency
        if self.aisle and other.aisle:
            try:
                aisle_diff = abs(int(self.aisle) - int(other.aisle))
                if aisle_diff > 1:
                    return False
            except ValueError:
                return False

        # Check shelf adjacency (same aisle)
        if self.aisle == other.aisle and self.shelf and other.shelf:
            try:
                if self.shelf.isdigit() and other.shelf.isdigit():
                    shelf_diff = abs(int(self.shelf) - int(other.shelf))
                    return shelf_diff <= 1
            except ValueError:
                pass

        return False

    def is_in_zone(self, zone: str) -> bool:
        """Check if location is in specified zone"""
        return self.zone == zone.upper()

    def is_temperature_controlled(self) -> bool:
        """Check if location requires temperature control"""
        return self.location_type in [LocationType.COLD_STORAGE]

    def is_high_security(self) -> bool:
        """Check if location requires additional security"""
        return self.location_type in [LocationType.SECURE]

    def requires_special_handling(self) -> bool:
        """Check if location requires special handling procedures"""
        return self.location_type in [
            LocationType.COLD_STORAGE,
            LocationType.SECURE,
            LocationType.QUARANTINE,
            LocationType.RETURNS
        ]

    def get_access_requirements(self) -> List[str]:
        """Get access requirements for the location"""
        requirements = []

        if self.location_type == LocationType.SECURE:
            requirements.append("security_clearance")
            requirements.append("dual_custody")

        if self.location_type == LocationType.COLD_STORAGE:
            requirements.append("cold_storage_ppe")
            requirements.append("temperature_training")

        if self.location_type == LocationType.QUARANTINE:
            requirements.append("inspection_authority")

        return requirements

    def format_for_label(self) -> str:
        """Format location code for warehouse labels"""
        return self.code

    def format_for_display(self) -> str:
        """Format location code for user display"""
        type_indicator = ""
        if self.location_type != LocationType.STANDARD:
            type_indicator = f" [{self.location_type.value.replace('_', ' ').title()}]"

        return f"{self.code}{type_indicator}"

    def __str__(self) -> str:
        return self.format_for_display()