"""
Shared Value Objects
Following the DDD Architecture Document
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Any, Optional
from ..shared.domain_base import ValueObject


@dataclass(frozen=True)
class Address(ValueObject):
    """Address value object"""
    street: str
    city: str
    province: str
    postal_code: str
    country: str = "Canada"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "street": self.street,
            "city": self.city,
            "province": self.province,
            "postal_code": self.postal_code,
            "country": self.country
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Address':
        return cls(
            street=data.get("street", ""),
            city=data.get("city", ""),
            province=data.get("province", ""),
            postal_code=data.get("postal_code", ""),
            country=data.get("country", "Canada")
        )

    def validate(self) -> bool:
        """Validate address fields"""
        return all([
            self.street,
            self.city,
            self.province,
            self.postal_code,
            self.country
        ])


@dataclass(frozen=True)
class GeoLocation(ValueObject):
    """Geographic location value object"""
    latitude: Decimal
    longitude: Decimal

    def to_dict(self) -> Dict[str, Any]:
        return {
            "latitude": float(self.latitude),
            "longitude": float(self.longitude)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GeoLocation':
        return cls(
            latitude=Decimal(str(data.get("latitude", 0))),
            longitude=Decimal(str(data.get("longitude", 0)))
        )

    def validate(self) -> bool:
        """Validate coordinates are within valid ranges"""
        return (
            -90 <= self.latitude <= 90 and
            -180 <= self.longitude <= 180
        )

    def distance_to(self, other: 'GeoLocation') -> Decimal:
        """Calculate distance to another location (simplified)"""
        # This is a simplified calculation - in production use haversine formula
        lat_diff = abs(self.latitude - other.latitude)
        lon_diff = abs(self.longitude - other.longitude)
        return Decimal((lat_diff ** 2 + lon_diff ** 2) ** 0.5)


@dataclass(frozen=True)
class TaxInfo(ValueObject):
    """Tax information value object"""
    rate: Decimal

    @property
    def total_rate(self) -> Decimal:
        return self.rate

    def calculate_tax(self, amount: Decimal) -> Decimal:
        """Calculate tax amount for given base amount"""
        return (amount * self.rate / 100).quantize(Decimal('0.01'))

    def add_tax(self, amount: Decimal) -> Decimal:
        """Add tax to base amount"""
        return amount + self.calculate_tax(amount)

    def validate(self) -> bool:
        """Validate tax rate is reasonable"""
        return Decimal('0') <= self.rate <= Decimal('100')


@dataclass(frozen=True)
class Money(ValueObject):
    """Money value object with currency"""
    amount: Decimal
    currency: str = "CAD"

    def __add__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError(f"Cannot add money with different currencies: {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract money with different currencies: {self.currency} and {other.currency}")
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, scalar: Decimal) -> 'Money':
        return Money(self.amount * scalar, self.currency)

    def __truediv__(self, scalar: Decimal) -> 'Money':
        return Money(self.amount / scalar, self.currency)

    def __lt__(self, other: 'Money') -> bool:
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare money with different currencies: {self.currency} and {other.currency}")
        return self.amount < other.amount

    def __le__(self, other: 'Money') -> bool:
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare money with different currencies: {self.currency} and {other.currency}")
        return self.amount <= other.amount

    def __gt__(self, other: 'Money') -> bool:
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare money with different currencies: {self.currency} and {other.currency}")
        return self.amount > other.amount

    def __ge__(self, other: 'Money') -> bool:
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare money with different currencies: {self.currency} and {other.currency}")
        return self.amount >= other.amount

    def is_positive(self) -> bool:
        return self.amount > 0

    def is_negative(self) -> bool:
        return self.amount < 0

    def is_zero(self) -> bool:
        return self.amount == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "amount": float(self.amount),
            "currency": self.currency
        }

    @classmethod
    def zero(cls, currency: str = "CAD") -> 'Money':
        return cls(Decimal('0'), currency)


@dataclass(frozen=True)
class DateRange(ValueObject):
    """Date range value object"""
    from datetime import datetime

    start_date: datetime
    end_date: Optional[datetime] = None

    def is_active(self, check_date: Optional[datetime] = None) -> bool:
        """Check if date range is active at given date"""
        check_date = check_date or datetime.utcnow()

        if check_date < self.start_date:
            return False

        if self.end_date and check_date > self.end_date:
            return False

        return True

    def overlaps_with(self, other: 'DateRange') -> bool:
        """Check if this date range overlaps with another"""
        if not self.end_date or not other.end_date:
            # If either range is open-ended, check if start dates conflict
            return self.start_date <= other.start_date if not self.end_date else other.start_date <= self.start_date

        return not (self.end_date < other.start_date or other.end_date < self.start_date)

    def contains(self, date: datetime) -> bool:
        """Check if a date falls within this range"""
        if date < self.start_date:
            return False

        if self.end_date and date > self.end_date:
            return False

        return True

    def duration_days(self) -> Optional[int]:
        """Get duration in days if end date is set"""
        if not self.end_date:
            return None
        return (self.end_date - self.start_date).days


@dataclass(frozen=True)
class ContactInfo(ValueObject):
    """Contact information value object"""
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None

    def validate_email(self) -> bool:
        """Basic email validation"""
        if not self.email:
            return True
        return '@' in self.email and '.' in self.email.split('@')[1]

    def validate_phone(self) -> bool:
        """Basic phone validation for Canadian numbers"""
        if not self.phone:
            return True
        # Remove common separators
        digits = ''.join(c for c in self.phone if c.isdigit())
        return len(digits) == 10 or (len(digits) == 11 and digits[0] == '1')

    def to_dict(self) -> Dict[str, Any]:
        return {
            "email": self.email,
            "phone": self.phone,
            "website": self.website
        }