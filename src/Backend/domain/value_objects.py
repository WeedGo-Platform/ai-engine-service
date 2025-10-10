"""
Value Objects for Domain Model
Immutable objects that represent concepts with no identity
Following DDD principles
"""

from dataclasses import dataclass, field
from typing import Optional, Union
from decimal import Decimal
import re
from uuid import UUID


@dataclass(frozen=True)
class Money:
    """
    Value object representing monetary amount
    Immutable and self-validating
    """
    amount: Decimal
    currency: str = "CAD"

    def __post_init__(self):
        """Validate money values"""
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")
        if not self.currency or len(self.currency) != 3:
            raise ValueError("Currency must be a 3-letter code")

    def add(self, other: 'Money') -> 'Money':
        """Add money values"""
        if self.currency != other.currency:
            raise ValueError("Cannot add money with different currencies")
        return Money(self.amount + other.amount, self.currency)

    def subtract(self, other: 'Money') -> 'Money':
        """Subtract money values"""
        if self.currency != other.currency:
            raise ValueError("Cannot subtract money with different currencies")
        return Money(self.amount - other.amount, self.currency)

    def multiply(self, factor: Union[int, float, Decimal]) -> 'Money':
        """Multiply money by a factor"""
        return Money(self.amount * Decimal(str(factor)), self.currency)

    def __str__(self):
        return f"{self.currency} {self.amount:.2f}"


@dataclass(frozen=True)
class Quantity:
    """
    Value object representing product quantity
    """
    value: int
    unit: str = "unit"

    def __post_init__(self):
        """Validate quantity"""
        if self.value < 0:
            raise ValueError("Quantity cannot be negative")

    def add(self, other: 'Quantity') -> 'Quantity':
        """Add quantities"""
        if self.unit != other.unit:
            raise ValueError("Cannot add quantities with different units")
        return Quantity(self.value + other.value, self.unit)

    def subtract(self, other: 'Quantity') -> 'Quantity':
        """Subtract quantities"""
        if self.unit != other.unit:
            raise ValueError("Cannot subtract quantities with different units")
        return Quantity(self.value - other.value, self.unit)

    def is_available(self, requested: 'Quantity') -> bool:
        """Check if requested quantity is available"""
        return self.value >= requested.value and self.unit == requested.unit


@dataclass(frozen=True)
class Email:
    """
    Value object representing email address
    """
    value: str

    def __post_init__(self):
        """Validate email format"""
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, self.value):
            raise ValueError(f"Invalid email address: {self.value}")

    def __str__(self):
        return self.value


@dataclass(frozen=True)
class PhoneNumber:
    """
    Value object representing phone number
    """
    value: str
    country_code: str = "+1"

    def __post_init__(self):
        """Validate phone number"""
        # Remove all non-numeric characters for validation
        digits_only = ''.join(filter(str.isdigit, self.value))
        if len(digits_only) < 10:
            raise ValueError("Phone number must have at least 10 digits")

    def formatted(self) -> str:
        """Return formatted phone number"""
        digits = ''.join(filter(str.isdigit, self.value))
        if len(digits) == 10:
            return f"{self.country_code} ({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        return f"{self.country_code} {self.value}"

    def __str__(self):
        return self.formatted()


@dataclass(frozen=True)
class Address:
    """
    Value object representing physical address
    """
    street: str
    city: str
    province: str
    postal_code: str
    country: str = "Canada"
    unit: Optional[str] = None

    def __post_init__(self):
        """Validate address fields"""
        if not all([self.street, self.city, self.province, self.postal_code]):
            raise ValueError("Address must have street, city, province, and postal code")

        # Validate Canadian postal code format
        if self.country == "Canada":
            postal_regex = r'^[A-Z]\d[A-Z]\s?\d[A-Z]\d$'
            if not re.match(postal_regex, self.postal_code.upper()):
                raise ValueError(f"Invalid Canadian postal code: {self.postal_code}")

    def formatted(self) -> str:
        """Return formatted address"""
        lines = []
        if self.unit:
            lines.append(f"{self.unit} - {self.street}")
        else:
            lines.append(self.street)
        lines.append(f"{self.city}, {self.province} {self.postal_code}")
        lines.append(self.country)
        return "\n".join(lines)

    def __str__(self):
        return self.formatted()


@dataclass(frozen=True)
class SKU:
    """
    Value object representing Stock Keeping Unit
    """
    value: str

    def __post_init__(self):
        """Validate SKU"""
        if not self.value or len(self.value) < 3:
            raise ValueError("SKU must be at least 3 characters")
        # Normalize SKU - uppercase and no spaces
        object.__setattr__(self, 'value', self.value.upper().strip())

    def __str__(self):
        return self.value


@dataclass(frozen=True)
class Barcode:
    """
    Value object representing product barcode
    """
    value: str
    type: str = "GTIN"  # GTIN, UPC, EAN, etc.

    def __post_init__(self):
        """Validate barcode"""
        if not self.value:
            raise ValueError("Barcode cannot be empty")

        # Basic GTIN validation
        if self.type == "GTIN":
            if not self.value.isdigit() or len(self.value) not in [8, 12, 13, 14]:
                raise ValueError(f"Invalid GTIN barcode: {self.value}")

    def __str__(self):
        return f"{self.type}: {self.value}"


@dataclass(frozen=True)
class THCContent:
    """
    Value object representing THC content
    """
    percentage: Decimal
    mg_per_unit: Optional[Decimal] = None

    def __post_init__(self):
        """Validate THC content"""
        if self.percentage < 0 or self.percentage > 100:
            raise ValueError("THC percentage must be between 0 and 100")
        if self.mg_per_unit and self.mg_per_unit < 0:
            raise ValueError("THC mg per unit cannot be negative")

    def __str__(self):
        base = f"{self.percentage}% THC"
        if self.mg_per_unit:
            base += f" ({self.mg_per_unit}mg/unit)"
        return base


@dataclass(frozen=True)
class CBDContent:
    """
    Value object representing CBD content
    """
    percentage: Decimal
    mg_per_unit: Optional[Decimal] = None

    def __post_init__(self):
        """Validate CBD content"""
        if self.percentage < 0 or self.percentage > 100:
            raise ValueError("CBD percentage must be between 0 and 100")
        if self.mg_per_unit and self.mg_per_unit < 0:
            raise ValueError("CBD mg per unit cannot be negative")

    def __str__(self):
        base = f"{self.percentage}% CBD"
        if self.mg_per_unit:
            base += f" ({self.mg_per_unit}mg/unit)"
        return base


@dataclass(frozen=True)
class StrainType:
    """
    Value object representing cannabis strain type
    """
    value: str

    VALID_TYPES = ["Indica", "Sativa", "Hybrid", "CBD Dominant", "Balanced"]

    def __post_init__(self):
        """Validate strain type"""
        normalized = self.value.title()
        if normalized not in self.VALID_TYPES:
            # Try to match partial names
            for valid_type in self.VALID_TYPES:
                if normalized.lower() in valid_type.lower():
                    object.__setattr__(self, 'value', valid_type)
                    return
            raise ValueError(f"Invalid strain type: {self.value}. Must be one of {self.VALID_TYPES}")
        object.__setattr__(self, 'value', normalized)

    def __str__(self):
        return self.value


@dataclass(frozen=True)
class ProductCategory:
    """
    Value object representing product category hierarchy
    """
    category: str
    sub_category: Optional[str] = None
    sub_sub_category: Optional[str] = None

    VALID_CATEGORIES = [
        "Flower",
        "Pre-Rolls",
        "Edibles",
        "Concentrates",
        "Vapes",
        "Oils",
        "Topicals",
        "Accessories",
        "Seeds"
    ]

    def __post_init__(self):
        """Validate category"""
        normalized_category = self.category.title()

        # Allow flexibility in category matching
        matched = False
        for valid_cat in self.VALID_CATEGORIES:
            if normalized_category.lower() in valid_cat.lower() or valid_cat.lower() in normalized_category.lower():
                object.__setattr__(self, 'category', valid_cat)
                matched = True
                break

        if not matched:
            # Don't raise error, just normalize the category
            object.__setattr__(self, 'category', normalized_category)

    def full_path(self) -> str:
        """Get full category path"""
        parts = [self.category]
        if self.sub_category:
            parts.append(self.sub_category)
        if self.sub_sub_category:
            parts.append(self.sub_sub_category)
        return " > ".join(parts)

    def __str__(self):
        return self.full_path()


@dataclass(frozen=True)
class StoreCode:
    """
    Value object representing store code
    """
    value: str

    def __post_init__(self):
        """Validate store code"""
        if not self.value or len(self.value) < 2:
            raise ValueError("Store code must be at least 2 characters")
        # Normalize store code
        object.__setattr__(self, 'value', self.value.upper().strip())

    def __str__(self):
        return self.value


@dataclass(frozen=True)
class TenantId:
    """
    Value object representing tenant identifier
    """
    value: UUID

    def __str__(self):
        return str(self.value)