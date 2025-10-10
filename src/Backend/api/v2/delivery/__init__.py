"""
Delivery Management V2 API

DDD-powered delivery and driver management using the Delivery Management bounded context.

Features:
- Delivery lifecycle management (create, assign, track, complete)
- Real-time driver location tracking
- Delivery zones with geographic boundaries
- Time window scheduling
- Route optimization for multi-stop deliveries
- Proof of delivery (signature and photos)
- Driver management and availability tracking
- Retry logic for failed deliveries
- Status transitions and business rule enforcement
"""

from .delivery_endpoints import router

__all__ = ["router"]
