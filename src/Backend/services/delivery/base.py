"""
Base classes and interfaces for delivery system
Following SOLID principles and clean architecture
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID


class DeliveryStatus(Enum):
    """Delivery status enumeration"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    ACCEPTED = "accepted"
    PREPARING = "preparing"
    READY_FOR_PICKUP = "ready_for_pickup"
    PICKED_UP = "picked_up"
    EN_ROUTE = "en_route"
    ARRIVED = "arrived"
    DELIVERING = "delivering"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @classmethod
    def active_statuses(cls) -> List['DeliveryStatus']:
        """Get list of active delivery statuses"""
        return [
            cls.ASSIGNED, cls.ACCEPTED, cls.PREPARING,
            cls.READY_FOR_PICKUP, cls.PICKED_UP,
            cls.EN_ROUTE, cls.ARRIVED, cls.DELIVERING
        ]

    @classmethod
    def terminal_statuses(cls) -> List['DeliveryStatus']:
        """Get list of terminal delivery statuses"""
        return [cls.COMPLETED, cls.FAILED, cls.CANCELLED]


class StaffStatus(Enum):
    """Staff availability status"""
    OFFLINE = "offline"
    AVAILABLE = "available"
    BUSY = "busy"
    BREAK = "break"


@dataclass
class Location:
    """GPS location representation"""
    latitude: float
    longitude: float
    accuracy_meters: Optional[float] = None
    altitude_meters: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def distance_to(self, other: 'Location') -> float:
        """Calculate distance to another location in kilometers"""
        from math import radians, sin, cos, sqrt, atan2

        R = 6371  # Earth radius in kilometers
        lat1, lon1 = radians(self.latitude), radians(self.longitude)
        lat2, lon2 = radians(other.latitude), radians(other.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        return R * c

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'accuracy_meters': self.accuracy_meters,
            'altitude_meters': self.altitude_meters,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class Address:
    """Delivery address representation"""
    street: str
    city: str
    state: str
    postal_code: str
    country: str = "Canada"
    unit: Optional[str] = None
    notes: Optional[str] = None
    location: Optional[Location] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON storage"""
        return {
            'street': self.street,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'country': self.country,
            'unit': self.unit,
            'notes': self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Address':
        """Create Address from dictionary"""
        return cls(
            street=data['street'],
            city=data['city'],
            state=data.get('state', data.get('province', '')),
            postal_code=data['postal_code'],
            country=data.get('country', 'Canada'),
            unit=data.get('unit'),
            notes=data.get('notes')
        )


@dataclass
class ProofOfDelivery:
    """Proof of delivery data"""
    signature_data: Optional[str] = None
    photo_urls: List[str] = field(default_factory=list)
    id_verified: bool = False
    id_verification_type: Optional[str] = None
    id_verification_data: Optional[Dict] = None
    age_verified: bool = False
    notes: Optional[str] = None
    captured_at: Optional[datetime] = None


@dataclass
class DeliveryMetrics:
    """Delivery performance metrics"""
    estimated_time: Optional[datetime] = None
    actual_time: Optional[datetime] = None
    distance_km: Optional[float] = None
    delivery_fee: Decimal = Decimal("0")
    tip_amount: Decimal = Decimal("0")
    rating: Optional[int] = None
    feedback: Optional[str] = None


@dataclass
class Delivery:
    """Complete delivery entity"""
    id: UUID
    order_id: UUID
    store_id: UUID
    status: DeliveryStatus
    customer_id: UUID
    customer_name: str
    customer_phone: str
    customer_email: Optional[str]
    delivery_address: Address
    assigned_to: Optional[UUID] = None
    batch_id: Optional[UUID] = None
    batch_sequence: Optional[int] = None
    proof: Optional[ProofOfDelivery] = None
    metrics: Optional[DeliveryMetrics] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class StaffMember:
    """Delivery staff member"""
    id: UUID
    name: str
    phone: str
    email: str
    status: StaffStatus
    current_location: Optional[Location] = None
    current_deliveries: int = 0
    max_deliveries: int = 5
    is_available: bool = False
    deliveries_today: int = 0
    deliveries_completed: int = 0

    @property
    def can_accept_delivery(self) -> bool:
        """Check if staff can accept new delivery"""
        return (
            self.is_available and
            self.status == StaffStatus.AVAILABLE and
            self.current_deliveries < self.max_deliveries
        )


@dataclass
class DeliveryBatch:
    """Batch of deliveries for optimization"""
    id: UUID
    batch_number: str
    store_id: UUID
    assigned_to: Optional[UUID]
    deliveries: List[Delivery]
    optimized_route: Optional[List[UUID]] = None
    total_distance_km: Optional[float] = None
    estimated_duration_minutes: Optional[int] = None
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def total_deliveries(self) -> int:
        """Get total number of deliveries in batch"""
        return len(self.deliveries)

    @property
    def completed_deliveries(self) -> int:
        """Get number of completed deliveries"""
        return sum(
            1 for d in self.deliveries
            if d.status == DeliveryStatus.COMPLETED
        )


# ====================================
# Abstract interfaces (SOLID - Interface Segregation)
# ====================================

class IDeliveryRepository(ABC):
    """Interface for delivery data persistence"""

    @abstractmethod
    async def create(self, delivery: Delivery) -> Delivery:
        """Create a new delivery"""
        pass

    @abstractmethod
    async def get(self, delivery_id: UUID) -> Optional[Delivery]:
        """Get delivery by ID"""
        pass

    @abstractmethod
    async def update(self, delivery: Delivery) -> Delivery:
        """Update delivery"""
        pass

    @abstractmethod
    async def list_active(self, store_id: UUID) -> List[Delivery]:
        """List active deliveries for a store"""
        pass

    @abstractmethod
    async def list_by_status(self, status: DeliveryStatus, store_id: UUID) -> List[Delivery]:
        """List deliveries by status"""
        pass

    @abstractmethod
    async def list_by_staff(self, staff_id: UUID, active_only: bool = True) -> List[Delivery]:
        """List deliveries assigned to staff member"""
        pass


class ITrackingService(ABC):
    """Interface for GPS tracking service"""

    @abstractmethod
    async def update_location(self, delivery_id: UUID, location: Location) -> bool:
        """Update delivery location"""
        pass

    @abstractmethod
    async def get_current_location(self, delivery_id: UUID) -> Optional[Location]:
        """Get current location of delivery"""
        pass

    @abstractmethod
    async def get_location_history(
        self,
        delivery_id: UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Location]:
        """Get location history for delivery"""
        pass


class INotificationService(ABC):
    """Interface for notification service"""

    @abstractmethod
    async def notify_assignment(self, delivery: Delivery, staff: StaffMember) -> bool:
        """Notify staff of new assignment"""
        pass

    @abstractmethod
    async def notify_customer(self, delivery: Delivery, message: str) -> bool:
        """Send notification to customer"""
        pass

    @abstractmethod
    async def notify_arrival(self, delivery: Delivery) -> bool:
        """Notify customer of driver arrival"""
        pass


class IGeofenceService(ABC):
    """Interface for geofencing service"""

    @abstractmethod
    async def check_arrival(self, location: Location, delivery: Delivery) -> bool:
        """Check if driver has arrived at delivery location"""
        pass

    @abstractmethod
    async def create_geofence(
        self,
        delivery_id: UUID,
        center: Location,
        radius_meters: int = 100
    ) -> UUID:
        """Create geofence for delivery"""
        pass

    @abstractmethod
    async def check_geofence(self, location: Location, geofence_id: UUID) -> bool:
        """Check if location is within geofence"""
        pass


class IETAService(ABC):
    """Interface for ETA calculation service"""

    @abstractmethod
    async def calculate_eta(
        self,
        origin: Location,
        destination: Location,
        mode: str = "driving"
    ) -> Tuple[datetime, float]:
        """Calculate ETA and distance"""
        pass

    @abstractmethod
    async def update_eta(self, delivery_id: UUID) -> datetime:
        """Update delivery ETA based on current location"""
        pass


class IAssignmentService(ABC):
    """Interface for delivery assignment service"""

    @abstractmethod
    async def assign_to_staff(self, delivery_id: UUID, staff_id: UUID) -> bool:
        """Manually assign delivery to staff member"""
        pass

    @abstractmethod
    async def batch_assign(
        self,
        delivery_ids: List[UUID],
        staff_id: UUID
    ) -> List[UUID]:
        """Assign multiple deliveries to staff"""
        pass

    @abstractmethod
    async def get_available_staff(self, store_id: UUID) -> List[StaffMember]:
        """Get list of available staff members"""
        pass


class DeliveryException(Exception):
    """Base exception for delivery system"""
    pass


class DeliveryNotFound(DeliveryException):
    """Delivery not found exception"""
    pass


class StaffNotAvailable(DeliveryException):
    """Staff member not available exception"""
    pass


class InvalidStatusTransition(DeliveryException):
    """Invalid delivery status transition"""
    pass