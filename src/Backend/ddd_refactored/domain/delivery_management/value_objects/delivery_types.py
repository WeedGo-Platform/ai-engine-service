"""
Delivery Management Value Objects
Following DDD Architecture Document Section 2.10
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Tuple

from ....shared.domain_base import ValueObject


class DeliveryStatus(str, Enum):
    """Delivery status"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    ARRIVED = "arrived"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class DeliveryPriority(str, Enum):
    """Delivery priority level"""
    STANDARD = "standard"
    EXPRESS = "express"
    SAME_DAY = "same_day"
    SCHEDULED = "scheduled"


class DriverStatus(str, Enum):
    """Driver availability status"""
    AVAILABLE = "available"
    ON_DELIVERY = "on_delivery"
    BREAK = "break"
    OFFLINE = "offline"


class VehicleType(str, Enum):
    """Delivery vehicle type"""
    CAR = "car"
    BIKE = "bike"
    SCOOTER = "scooter"
    WALKING = "walking"
    VAN = "van"


@dataclass(frozen=True)
class GeoCoordinates(ValueObject):
    """
    Geographic coordinates (latitude/longitude)
    """
    latitude: Decimal
    longitude: Decimal

    def __post_init__(self):
        """Validate coordinates"""
        if self.latitude < -90 or self.latitude > 90:
            raise ValueError("Latitude must be between -90 and 90")

        if self.longitude < -180 or self.longitude > 180:
            raise ValueError("Longitude must be between -180 and 180")

    def distance_to(self, other: 'GeoCoordinates') -> Decimal:
        """
        Calculate distance to another point using Haversine formula
        Returns distance in kilometers
        """
        from math import radians, sin, cos, sqrt, atan2

        # Earth radius in kilometers
        R = Decimal("6371")

        lat1 = radians(float(self.latitude))
        lon1 = radians(float(self.longitude))
        lat2 = radians(float(other.latitude))
        lon2 = radians(float(other.longitude))

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance = R * Decimal(str(c))
        return distance

    def to_tuple(self) -> Tuple[float, float]:
        """Convert to tuple (lat, lon)"""
        return (float(self.latitude), float(self.longitude))

    def __str__(self) -> str:
        return f"({self.latitude}, {self.longitude})"


@dataclass(frozen=True)
class DeliveryAddress(ValueObject):
    """
    Complete delivery address with geocoding
    """
    street_address: str
    city: str
    province: str
    postal_code: str
    country: str = "Canada"

    # Unit/apartment
    unit: Optional[str] = None

    # Geocoded coordinates
    coordinates: Optional[GeoCoordinates] = None

    # Delivery instructions
    delivery_instructions: Optional[str] = None
    buzzer_code: Optional[str] = None

    def __post_init__(self):
        """Validate address"""
        if not self.street_address:
            raise ValueError("Street address is required")

        if not self.city:
            raise ValueError("City is required")

        if not self.province:
            raise ValueError("Province is required")

        if not self.postal_code:
            raise ValueError("Postal code is required")

        # Validate Canadian postal code format
        if self.country == "Canada":
            import re
            postal_pattern = r"^[A-Z]\d[A-Z]\s?\d[A-Z]\d$"
            if not re.match(postal_pattern, self.postal_code.upper().replace(" ", "")):
                raise ValueError("Invalid Canadian postal code format")

    def get_full_address(self) -> str:
        """Get formatted full address"""
        parts = [self.street_address]

        if self.unit:
            parts[0] = f"{self.unit} - {parts[0]}"

        parts.extend([
            self.city,
            f"{self.province} {self.postal_code}",
            self.country
        ])

        return ", ".join(parts)

    def get_short_address(self) -> str:
        """Get short address for display"""
        return f"{self.street_address}, {self.city}"

    def is_geocoded(self) -> bool:
        """Check if address has coordinates"""
        return self.coordinates is not None

    def with_coordinates(self, coordinates: GeoCoordinates) -> 'DeliveryAddress':
        """Create new address with geocoded coordinates"""
        return DeliveryAddress(
            street_address=self.street_address,
            city=self.city,
            province=self.province,
            postal_code=self.postal_code,
            country=self.country,
            unit=self.unit,
            coordinates=coordinates,
            delivery_instructions=self.delivery_instructions,
            buzzer_code=self.buzzer_code
        )


@dataclass(frozen=True)
class DeliveryZone(ValueObject):
    """
    Delivery zone with boundaries
    """
    zone_name: str
    zone_code: str

    # Delivery fee for this zone
    delivery_fee: Decimal

    # Estimated delivery time
    estimated_minutes_min: int
    estimated_minutes_max: int

    # Zone boundaries (list of postal code prefixes or coordinates)
    postal_code_prefixes: Optional[List[str]] = None
    boundary_coordinates: Optional[List[GeoCoordinates]] = None

    # Zone limits
    max_deliveries_per_hour: Optional[int] = None
    is_active: bool = True

    def __post_init__(self):
        """Validate delivery zone"""
        if not self.zone_name:
            raise ValueError("Zone name is required")

        if not self.zone_code:
            raise ValueError("Zone code is required")

        if self.delivery_fee < 0:
            raise ValueError("Delivery fee cannot be negative")

        if self.estimated_minutes_min <= 0:
            raise ValueError("Estimated min minutes must be positive")

        if self.estimated_minutes_max < self.estimated_minutes_min:
            raise ValueError("Estimated max must be >= min")

        if not self.postal_code_prefixes and not self.boundary_coordinates:
            raise ValueError("Must specify either postal codes or boundary coordinates")

    def contains_postal_code(self, postal_code: str) -> bool:
        """Check if postal code is in this zone"""
        if not self.postal_code_prefixes:
            return False

        # Normalize postal code
        normalized = postal_code.upper().replace(" ", "")

        for prefix in self.postal_code_prefixes:
            if normalized.startswith(prefix.upper()):
                return True

        return False

    def contains_coordinates(self, coordinates: GeoCoordinates) -> bool:
        """
        Check if coordinates are within zone boundary
        Uses ray-casting algorithm for point-in-polygon test
        """
        if not self.boundary_coordinates or len(self.boundary_coordinates) < 3:
            return False

        # Ray-casting algorithm
        x, y = float(coordinates.latitude), float(coordinates.longitude)
        n = len(self.boundary_coordinates)
        inside = False

        p1 = self.boundary_coordinates[0]
        for i in range(1, n + 1):
            p2 = self.boundary_coordinates[i % n]

            x1, y1 = float(p1.latitude), float(p1.longitude)
            x2, y2 = float(p2.latitude), float(p2.longitude)

            if y > min(y1, y2):
                if y <= max(y1, y2):
                    if x <= max(x1, x2):
                        if y1 != y2:
                            xinters = (y - y1) * (x2 - x1) / (y2 - y1) + x1
                        if x1 == x2 or x <= xinters:
                            inside = not inside
            p1 = p2

        return inside

    def get_estimated_time_range(self) -> str:
        """Get formatted time estimate"""
        return f"{self.estimated_minutes_min}-{self.estimated_minutes_max} minutes"


@dataclass(frozen=True)
class DeliveryTimeWindow(ValueObject):
    """
    Scheduled delivery time window
    """
    window_start: datetime
    window_end: datetime
    is_guaranteed: bool = False

    def __post_init__(self):
        """Validate time window"""
        if self.window_end <= self.window_start:
            raise ValueError("Window end must be after window start")

        # Window should be at least 30 minutes
        duration = (self.window_end - self.window_start).total_seconds() / 60
        if duration < 30:
            raise ValueError("Time window must be at least 30 minutes")

    def get_duration_minutes(self) -> int:
        """Get window duration in minutes"""
        return int((self.window_end - self.window_start).total_seconds() / 60)

    def is_current(self) -> bool:
        """Check if current time is within window"""
        now = datetime.utcnow()
        return self.window_start <= now <= self.window_end

    def is_past(self) -> bool:
        """Check if window has passed"""
        return datetime.utcnow() > self.window_end

    def is_future(self) -> bool:
        """Check if window is in the future"""
        return datetime.utcnow() < self.window_start

    def get_display_text(self) -> str:
        """Get formatted time window"""
        start_time = self.window_start.strftime("%I:%M %p")
        end_time = self.window_end.strftime("%I:%M %p")

        window_text = f"{start_time} - {end_time}"

        if self.is_guaranteed:
            window_text += " (Guaranteed)"

        return window_text


@dataclass(frozen=True)
class RouteStop(ValueObject):
    """
    Individual stop in a delivery route
    """
    delivery_id: str  # UUID as string
    address: DeliveryAddress
    sequence: int  # Order in route
    estimated_arrival: datetime
    estimated_duration_minutes: int = 5  # Time spent at location

    def __post_init__(self):
        """Validate route stop"""
        if self.sequence < 1:
            raise ValueError("Sequence must be positive")

        if self.estimated_duration_minutes <= 0:
            raise ValueError("Duration must be positive")

        if not self.address.is_geocoded():
            raise ValueError("Address must be geocoded for routing")


@dataclass(frozen=True)
class OptimizedRoute(ValueObject):
    """
    Optimized delivery route
    """
    stops: Tuple[RouteStop, ...]
    total_distance_km: Decimal
    total_duration_minutes: int
    optimized_at: datetime

    def __post_init__(self):
        """Validate route"""
        if not self.stops:
            raise ValueError("Route must have at least one stop")

        if self.total_distance_km < 0:
            raise ValueError("Distance cannot be negative")

        if self.total_duration_minutes < 0:
            raise ValueError("Duration cannot be negative")

        # Validate sequence numbers
        for i, stop in enumerate(self.stops, 1):
            if stop.sequence != i:
                raise ValueError(f"Stop sequence mismatch at position {i}")

    def get_stop_count(self) -> int:
        """Get number of stops"""
        return len(self.stops)

    def get_estimated_completion_time(self) -> datetime:
        """Get estimated route completion time"""
        if not self.stops:
            return self.optimized_at

        last_stop = self.stops[-1]
        return last_stop.estimated_arrival + timedelta(minutes=last_stop.estimated_duration_minutes)

    def get_next_stop(self, current_sequence: int) -> Optional[RouteStop]:
        """Get next stop after current sequence"""
        for stop in self.stops:
            if stop.sequence == current_sequence + 1:
                return stop
        return None
