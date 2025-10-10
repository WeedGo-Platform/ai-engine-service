"""
Order Management V2 API

DDD-powered order endpoints using the Order Management bounded context.

Features:
- Create and manage orders
- Add/update/remove items
- Order status lifecycle
- Payment integration
- Delivery/pickup scheduling
"""

from .order_endpoints import router

__all__ = ["router"]

