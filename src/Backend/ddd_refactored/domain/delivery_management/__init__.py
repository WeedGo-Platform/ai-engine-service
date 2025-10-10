"""
Delivery Management Bounded Context

This context handles:
- Delivery creation and tracking
- Driver assignment and management
- Real-time location updates
- Delivery zones and fees
- Route optimization
- Time window scheduling
- Proof of delivery (signature, photos)
"""

from .entities import (
    Delivery,
    DeliveryDriver,
    DeliveryCreated,
    DriverAssigned,
    DeliveryPickedUp,
    DeliveryStarted,
    LocationUpdated,
    DeliveryArrived,
    DeliveryCompleted,
    DeliveryFailed,
    DeliveryCancelled
)

from .value_objects import (
    DeliveryStatus,
    DeliveryPriority,
    DriverStatus,
    VehicleType,
    GeoCoordinates,
    DeliveryAddress,
    DeliveryZone,
    DeliveryTimeWindow,
    RouteStop,
    OptimizedRoute
)

__all__ = [
    # Entities
    'Delivery',
    'DeliveryDriver',

    # Events
    'DeliveryCreated',
    'DriverAssigned',
    'DeliveryPickedUp',
    'DeliveryStarted',
    'LocationUpdated',
    'DeliveryArrived',
    'DeliveryCompleted',
    'DeliveryFailed',
    'DeliveryCancelled',

    # Value Objects
    'DeliveryStatus',
    'DeliveryPriority',
    'DriverStatus',
    'VehicleType',
    'GeoCoordinates',
    'DeliveryAddress',
    'DeliveryZone',
    'DeliveryTimeWindow',
    'RouteStop',
    'OptimizedRoute'
]
