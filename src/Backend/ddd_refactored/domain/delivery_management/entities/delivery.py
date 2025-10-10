"""
Delivery Aggregate Root
Following DDD Architecture Document Section 2.10
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from ....shared.domain_base import AggregateRoot, DomainEvent, BusinessRuleViolation
from ..value_objects.delivery_types import (
    DeliveryStatus,
    DeliveryPriority,
    DriverStatus,
    VehicleType,
    GeoCoordinates,
    DeliveryAddress,
    DeliveryZone,
    DeliveryTimeWindow,
    OptimizedRoute,
    RouteStop
)


# Domain Events
class DeliveryCreated(DomainEvent):
    delivery_id: UUID
    order_id: UUID
    store_id: UUID
    delivery_address: str


class DriverAssigned(DomainEvent):
    delivery_id: UUID
    driver_id: UUID
    driver_name: str
    assigned_at: datetime


class DeliveryPickedUp(DomainEvent):
    delivery_id: UUID
    driver_id: UUID
    picked_up_at: datetime


class DeliveryStarted(DomainEvent):
    delivery_id: UUID
    driver_id: UUID
    started_at: datetime


class LocationUpdated(DomainEvent):
    delivery_id: UUID
    driver_id: UUID
    current_location: GeoCoordinates
    updated_at: datetime


class DeliveryArrived(DomainEvent):
    delivery_id: UUID
    driver_id: UUID
    arrived_at: datetime


class DeliveryCompleted(DomainEvent):
    delivery_id: UUID
    order_id: UUID
    driver_id: UUID
    completed_at: datetime
    signature: Optional[str]


class DeliveryFailed(DomainEvent):
    delivery_id: UUID
    order_id: UUID
    driver_id: Optional[UUID]
    failure_reason: str
    failed_at: datetime


class DeliveryCancelled(DomainEvent):
    delivery_id: UUID
    order_id: UUID
    cancelled_at: datetime
    reason: str


@dataclass
class DeliveryDriver:
    """Driver entity within delivery context"""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    phone: str = ""
    email: str = ""

    # Status
    status: DriverStatus = DriverStatus.AVAILABLE

    # Vehicle
    vehicle_type: VehicleType = VehicleType.CAR
    vehicle_plate: Optional[str] = None

    # Current location
    current_location: Optional[GeoCoordinates] = None
    last_location_update: Optional[datetime] = None

    # Stats
    total_deliveries: int = 0
    rating: Decimal = Decimal("5.0")

    # License info (for compliance)
    drivers_license: Optional[str] = None
    license_expiry: Optional[datetime] = None

    def is_available(self) -> bool:
        """Check if driver is available for assignment"""
        return self.status == DriverStatus.AVAILABLE

    def update_location(self, coordinates: GeoCoordinates):
        """Update driver's current location"""
        self.current_location = coordinates
        self.last_location_update = datetime.utcnow()

    def start_delivery(self):
        """Mark driver as on delivery"""
        if not self.is_available():
            raise BusinessRuleViolation(f"Driver is {self.status}")

        self.status = DriverStatus.ON_DELIVERY

    def complete_delivery(self):
        """Mark driver as available after delivery"""
        self.status = DriverStatus.AVAILABLE
        self.total_deliveries += 1


@dataclass
class Delivery(AggregateRoot):
    """
    Delivery Aggregate Root - Delivery tracking and management
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.10
    """
    # Identifiers
    order_id: UUID = field(default_factory=uuid4)
    store_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    customer_id: Optional[UUID] = None

    # Status
    status: DeliveryStatus = DeliveryStatus.PENDING
    priority: DeliveryPriority = DeliveryPriority.STANDARD

    # Delivery details
    delivery_address: DeliveryAddress = None
    pickup_address: Optional[DeliveryAddress] = None

    # Zone and fee
    delivery_zone: Optional[DeliveryZone] = None
    delivery_fee: Decimal = Decimal("0")

    # Time window
    delivery_time_window: Optional[DeliveryTimeWindow] = None
    estimated_delivery_time: Optional[datetime] = None
    actual_delivery_time: Optional[datetime] = None

    # Driver assignment
    assigned_driver_id: Optional[UUID] = None
    assigned_driver_name: Optional[str] = None

    # Tracking
    current_location: Optional[GeoCoordinates] = None
    route: Optional[OptimizedRoute] = None
    distance_to_destination_km: Optional[Decimal] = None

    # Completion
    signature: Optional[str] = None  # Base64 encoded signature image
    photo_proof: Optional[str] = None  # URL to delivery photo
    recipient_name: Optional[str] = None

    # Failure details
    failure_reason: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    assigned_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    arrived_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    # Notes
    delivery_notes: Optional[str] = None
    driver_notes: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        order_id: UUID,
        store_id: UUID,
        tenant_id: UUID,
        delivery_address: DeliveryAddress,
        pickup_address: Optional[DeliveryAddress] = None,
        customer_id: Optional[UUID] = None,
        priority: DeliveryPriority = DeliveryPriority.STANDARD
    ) -> 'Delivery':
        """Factory method to create new delivery"""
        if not delivery_address.is_geocoded():
            raise BusinessRuleViolation("Delivery address must be geocoded")

        delivery = cls(
            order_id=order_id,
            store_id=store_id,
            tenant_id=tenant_id,
            customer_id=customer_id,
            delivery_address=delivery_address,
            pickup_address=pickup_address,
            priority=priority,
            status=DeliveryStatus.PENDING
        )

        # Raise creation event
        delivery.add_domain_event(DeliveryCreated(
            delivery_id=delivery.id,
            order_id=order_id,
            store_id=store_id,
            delivery_address=delivery_address.get_full_address()
        ))

        return delivery

    def assign_driver(
        self,
        driver_id: UUID,
        driver_name: str,
        estimated_delivery_time: Optional[datetime] = None
    ):
        """Assign a driver to this delivery"""
        if self.status not in [DeliveryStatus.PENDING]:
            raise BusinessRuleViolation(f"Cannot assign driver to {self.status} delivery")

        if self.assigned_driver_id:
            raise BusinessRuleViolation("Delivery already has a driver assigned")

        self.assigned_driver_id = driver_id
        self.assigned_driver_name = driver_name
        self.assigned_at = datetime.utcnow()
        self.status = DeliveryStatus.ASSIGNED

        if estimated_delivery_time:
            self.estimated_delivery_time = estimated_delivery_time

        # Raise event
        self.add_domain_event(DriverAssigned(
            delivery_id=self.id,
            driver_id=driver_id,
            driver_name=driver_name,
            assigned_at=self.assigned_at
        ))

        self.mark_as_modified()

    def pick_up(self):
        """Mark delivery as picked up by driver"""
        if self.status != DeliveryStatus.ASSIGNED:
            raise BusinessRuleViolation(f"Cannot pick up {self.status} delivery")

        if not self.assigned_driver_id:
            raise BusinessRuleViolation("No driver assigned")

        self.status = DeliveryStatus.PICKED_UP
        self.picked_up_at = datetime.utcnow()

        # Raise event
        self.add_domain_event(DeliveryPickedUp(
            delivery_id=self.id,
            driver_id=self.assigned_driver_id,
            picked_up_at=self.picked_up_at
        ))

        self.mark_as_modified()

    def start_transit(self):
        """Mark delivery as in transit"""
        if self.status != DeliveryStatus.PICKED_UP:
            raise BusinessRuleViolation(f"Cannot start transit from {self.status}")

        self.status = DeliveryStatus.IN_TRANSIT
        self.started_at = datetime.utcnow()

        # Raise event
        self.add_domain_event(DeliveryStarted(
            delivery_id=self.id,
            driver_id=self.assigned_driver_id,
            started_at=self.started_at
        ))

        self.mark_as_modified()

    def update_location(self, current_location: GeoCoordinates):
        """Update current location of delivery"""
        if self.status not in [DeliveryStatus.PICKED_UP, DeliveryStatus.IN_TRANSIT]:
            raise BusinessRuleViolation(f"Cannot update location for {self.status} delivery")

        self.current_location = current_location

        # Calculate distance to destination
        if self.delivery_address.coordinates:
            self.distance_to_destination_km = current_location.distance_to(
                self.delivery_address.coordinates
            )

        # Raise event
        self.add_domain_event(LocationUpdated(
            delivery_id=self.id,
            driver_id=self.assigned_driver_id,
            current_location=current_location,
            updated_at=datetime.utcnow()
        ))

        self.mark_as_modified()

    def mark_arrived(self):
        """Mark delivery as arrived at destination"""
        if self.status != DeliveryStatus.IN_TRANSIT:
            raise BusinessRuleViolation(f"Cannot mark arrived from {self.status}")

        self.status = DeliveryStatus.ARRIVED
        self.arrived_at = datetime.utcnow()

        # Raise event
        self.add_domain_event(DeliveryArrived(
            delivery_id=self.id,
            driver_id=self.assigned_driver_id,
            arrived_at=self.arrived_at
        ))

        self.mark_as_modified()

    def complete(
        self,
        signature: Optional[str] = None,
        photo_proof: Optional[str] = None,
        recipient_name: Optional[str] = None
    ):
        """Complete the delivery"""
        if self.status != DeliveryStatus.ARRIVED:
            raise BusinessRuleViolation(f"Cannot complete {self.status} delivery")

        self.status = DeliveryStatus.DELIVERED
        self.completed_at = datetime.utcnow()
        self.actual_delivery_time = self.completed_at
        self.signature = signature
        self.photo_proof = photo_proof
        self.recipient_name = recipient_name

        # Raise event
        self.add_domain_event(DeliveryCompleted(
            delivery_id=self.id,
            order_id=self.order_id,
            driver_id=self.assigned_driver_id,
            completed_at=self.completed_at,
            signature=signature
        ))

        self.mark_as_modified()

    def fail(self, failure_reason: str):
        """Mark delivery as failed"""
        if self.status in [DeliveryStatus.DELIVERED, DeliveryStatus.CANCELLED]:
            raise BusinessRuleViolation(f"Cannot fail {self.status} delivery")

        self.status = DeliveryStatus.FAILED
        self.failure_reason = failure_reason
        self.retry_count += 1

        # Raise event
        self.add_domain_event(DeliveryFailed(
            delivery_id=self.id,
            order_id=self.order_id,
            driver_id=self.assigned_driver_id,
            failure_reason=failure_reason,
            failed_at=datetime.utcnow()
        ))

        self.mark_as_modified()

    def cancel(self, reason: str = ""):
        """Cancel the delivery"""
        if self.status in [DeliveryStatus.DELIVERED]:
            raise BusinessRuleViolation("Cannot cancel delivered order")

        self.status = DeliveryStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()

        # Raise event
        self.add_domain_event(DeliveryCancelled(
            delivery_id=self.id,
            order_id=self.order_id,
            cancelled_at=self.cancelled_at,
            reason=reason
        ))

        self.mark_as_modified()

    def retry(self):
        """Retry failed delivery"""
        if self.status != DeliveryStatus.FAILED:
            raise BusinessRuleViolation("Can only retry failed deliveries")

        if self.retry_count >= self.max_retries:
            raise BusinessRuleViolation(f"Max retries ({self.max_retries}) exceeded")

        # Reset to pending
        self.status = DeliveryStatus.PENDING
        self.assigned_driver_id = None
        self.assigned_driver_name = None
        self.assigned_at = None
        self.failure_reason = None

        self.mark_as_modified()

    def set_delivery_zone(self, zone: DeliveryZone):
        """Set delivery zone and fee"""
        if not zone.is_active:
            raise BusinessRuleViolation("Cannot assign inactive delivery zone")

        # Validate address is in zone
        if zone.postal_code_prefixes:
            if not zone.contains_postal_code(self.delivery_address.postal_code):
                raise BusinessRuleViolation("Address not in delivery zone")

        self.delivery_zone = zone
        self.delivery_fee = zone.delivery_fee
        self.mark_as_modified()

    def set_time_window(self, time_window: DeliveryTimeWindow):
        """Set delivery time window"""
        if time_window.is_past():
            raise BusinessRuleViolation("Cannot set past time window")

        self.delivery_time_window = time_window

        # Set estimated time to middle of window
        window_duration = time_window.get_duration_minutes()
        self.estimated_delivery_time = time_window.window_start + timedelta(
            minutes=window_duration // 2
        )

        self.mark_as_modified()

    def set_route(self, route: OptimizedRoute):
        """Set optimized delivery route"""
        if self.status not in [DeliveryStatus.ASSIGNED, DeliveryStatus.PICKED_UP]:
            raise BusinessRuleViolation(f"Cannot set route for {self.status} delivery")

        self.route = route
        self.mark_as_modified()

    def is_on_time(self) -> bool:
        """Check if delivery is on time"""
        if not self.delivery_time_window:
            return True

        if self.completed_at:
            return self.completed_at <= self.delivery_time_window.window_end

        if self.estimated_delivery_time:
            return self.estimated_delivery_time <= self.delivery_time_window.window_end

        return True

    def can_be_cancelled(self) -> bool:
        """Check if delivery can be cancelled"""
        return self.status in [
            DeliveryStatus.PENDING,
            DeliveryStatus.ASSIGNED,
            DeliveryStatus.PICKED_UP
        ]

    def get_elapsed_time_minutes(self) -> Optional[int]:
        """Get elapsed time since delivery started"""
        if not self.started_at:
            return None

        end_time = self.completed_at or datetime.utcnow()
        elapsed = (end_time - self.started_at).total_seconds() / 60
        return int(elapsed)

    def validate(self) -> List[str]:
        """Validate delivery"""
        errors = []

        if not self.order_id:
            errors.append("Order ID is required")

        if not self.store_id:
            errors.append("Store ID is required")

        if not self.tenant_id:
            errors.append("Tenant ID is required")

        if not self.delivery_address:
            errors.append("Delivery address is required")

        if self.delivery_address and not self.delivery_address.is_geocoded():
            errors.append("Delivery address must be geocoded")

        if self.delivery_fee < 0:
            errors.append("Delivery fee cannot be negative")

        if self.retry_count > self.max_retries:
            errors.append(f"Retry count exceeds maximum ({self.max_retries})")

        return errors
