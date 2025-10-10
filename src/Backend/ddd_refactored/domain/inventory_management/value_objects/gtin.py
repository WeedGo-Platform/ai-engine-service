"""
GTIN Value Object
Following DDD Architecture Document Section 2.4
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
import re

from ....shared.domain_base import ValueObject


class GTINType(str, Enum):
    """Types of GTIN (Global Trade Item Number)"""
    GTIN8 = "GTIN-8"    # EAN-8
    GTIN12 = "GTIN-12"  # UPC-A
    GTIN13 = "GTIN-13"  # EAN-13
    GTIN14 = "GTIN-14"  # ITF-14
    INVALID = "INVALID"


@dataclass(frozen=True)
class GTIN(ValueObject):
    """
    GTIN Value Object - Global Trade Item Number for product identification
    Supports GTIN-8, GTIN-12 (UPC-A), GTIN-13 (EAN-13), and GTIN-14 formats
    """
    value: str
    type: GTINType

    def __post_init__(self):
        """Validate GTIN format and checksum"""
        # Remove any spaces or dashes
        clean_value = re.sub(r'[\s\-]', '', self.value)

        # Check if it contains only digits
        if not clean_value.isdigit():
            raise ValueError(f"GTIN must contain only digits: {self.value}")

        # Validate based on length
        if len(clean_value) not in [8, 12, 13, 14]:
            raise ValueError(f"Invalid GTIN length: {len(clean_value)}")

        # Validate checksum
        if not self._validate_checksum(clean_value):
            raise ValueError(f"Invalid GTIN checksum: {self.value}")

        # Verify type matches length
        expected_type = self._determine_type(clean_value)
        if self.type != expected_type and self.type != GTINType.INVALID:
            raise ValueError(f"GTIN type {self.type} doesn't match length {len(clean_value)}")

    @classmethod
    def from_string(cls, gtin_string: str) -> 'GTIN':
        """Create GTIN from string, auto-detecting type"""
        # Clean the input
        clean_value = re.sub(r'[\s\-]', '', gtin_string)

        # Determine type
        gtin_type = cls._determine_type(clean_value)

        return cls(value=clean_value, type=gtin_type)

    @staticmethod
    def _determine_type(clean_value: str) -> GTINType:
        """Determine GTIN type from cleaned value"""
        length = len(clean_value)
        if length == 8:
            return GTINType.GTIN8
        elif length == 12:
            return GTINType.GTIN12
        elif length == 13:
            return GTINType.GTIN13
        elif length == 14:
            return GTINType.GTIN14
        else:
            return GTINType.INVALID

    @staticmethod
    def _validate_checksum(gtin: str) -> bool:
        """
        Validate GTIN checksum using the standard algorithm
        The last digit is the check digit
        """
        if not gtin or len(gtin) < 8:
            return False

        # Extract check digit
        check_digit = int(gtin[-1])
        digits = gtin[:-1]

        # Calculate checksum
        total = 0
        for i, digit in enumerate(reversed(digits)):
            if i % 2 == 0:  # Odd positions (from right)
                total += int(digit) * 3
            else:  # Even positions (from right)
                total += int(digit)

        # Calculate expected check digit
        calculated_check = (10 - (total % 10)) % 10

        return calculated_check == check_digit

    @classmethod
    def generate_check_digit(cls, partial_gtin: str) -> str:
        """Generate check digit for a partial GTIN"""
        # Remove any non-digits
        clean = re.sub(r'\D', '', partial_gtin)

        if len(clean) not in [7, 11, 12, 13]:
            raise ValueError(f"Invalid partial GTIN length: {len(clean)}")

        # Calculate checksum
        total = 0
        for i, digit in enumerate(reversed(clean)):
            if i % 2 == 0:  # Odd positions (from right)
                total += int(digit) * 3
            else:  # Even positions (from right)
                total += int(digit)

        # Calculate check digit
        check_digit = (10 - (total % 10)) % 10

        return clean + str(check_digit)

    def to_ean13(self) -> str:
        """Convert to EAN-13 format (if applicable)"""
        clean = re.sub(r'\D', '', self.value)

        if self.type == GTINType.GTIN13:
            return clean
        elif self.type == GTINType.GTIN12:
            # Add leading zero to UPC-A to make EAN-13
            return '0' + clean
        elif self.type == GTINType.GTIN8:
            # Add 5 leading zeros
            return '00000' + clean
        else:
            raise ValueError(f"Cannot convert {self.type} to EAN-13")

    def to_gtin14(self, packaging_level: int = 0) -> str:
        """Convert to GTIN-14 format"""
        if packaging_level < 0 or packaging_level > 8:
            raise ValueError("Packaging level must be between 0 and 8")

        clean = re.sub(r'\D', '', self.value)

        if self.type == GTINType.GTIN14:
            return clean
        elif self.type == GTINType.GTIN13:
            # Add packaging level digit and recalculate check digit
            partial = str(packaging_level) + clean[:-1]
            return self.generate_check_digit(partial)
        elif self.type == GTINType.GTIN12:
            # Add packaging level and leading zero
            partial = str(packaging_level) + '0' + clean[:-1]
            return self.generate_check_digit(partial)
        else:
            raise ValueError(f"Cannot convert {self.type} to GTIN-14")

    def get_company_prefix(self) -> str:
        """Extract company prefix from GTIN"""
        clean = re.sub(r'\D', '', self.value)

        # For simplicity, assume standard prefix lengths
        # In reality, this varies by GS1 member organization
        if self.type in [GTINType.GTIN13, GTINType.GTIN12]:
            return clean[:7]  # First 7 digits typically
        elif self.type == GTINType.GTIN14:
            return clean[1:8]  # Skip packaging indicator
        else:
            return clean[:5]  # GTIN-8

    def get_item_reference(self) -> str:
        """Extract item reference from GTIN"""
        clean = re.sub(r'\D', '', self.value)

        if self.type in [GTINType.GTIN13, GTINType.GTIN12]:
            return clean[7:-1]  # After company prefix, before check digit
        elif self.type == GTINType.GTIN14:
            return clean[8:-1]
        else:
            return clean[5:-1]  # GTIN-8

    def format_for_display(self) -> str:
        """Format GTIN for display with appropriate separators"""
        clean = re.sub(r'\D', '', self.value)

        if self.type == GTINType.GTIN8:
            # Format as XXXX-XXXX
            return f"{clean[:4]}-{clean[4:]}"
        elif self.type == GTINType.GTIN12:
            # Format as X-XXXXX-XXXXX-X
            return f"{clean[0]}-{clean[1:6]}-{clean[6:11]}-{clean[11]}"
        elif self.type == GTINType.GTIN13:
            # Format as XXX-XXXX-XXXX-X
            return f"{clean[:3]}-{clean[3:7]}-{clean[7:11]}-{clean[11:]}"
        elif self.type == GTINType.GTIN14:
            # Format as X-XXX-XXXX-XXXX-X
            return f"{clean[0]}-{clean[1:4]}-{clean[4:8]}-{clean[8:12]}-{clean[12:]}"
        else:
            return clean

    def format_for_barcode(self) -> str:
        """Format GTIN for barcode generation"""
        # Remove all non-digits for barcode
        return re.sub(r'\D', '', self.value)

    def is_case_code(self) -> bool:
        """Check if this is a case-level GTIN (GTIN-14 with packaging indicator > 0)"""
        if self.type != GTINType.GTIN14:
            return False

        clean = re.sub(r'\D', '', self.value)
        packaging_indicator = int(clean[0])
        return packaging_indicator > 0

    def get_packaging_level(self) -> Optional[int]:
        """Get packaging level for GTIN-14"""
        if self.type != GTINType.GTIN14:
            return None

        clean = re.sub(r'\D', '', self.value)
        return int(clean[0])

    def __str__(self) -> str:
        return self.format_for_display()