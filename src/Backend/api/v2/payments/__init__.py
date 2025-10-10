"""
Payment Processing V2 API

DDD-powered payment endpoints using the Payment Processing bounded context.

Features:
- Process payments (authorize, capture)
- Refund transactions
- Query transaction history
- Payment event publishing
- Multi-provider support
"""

from .payment_endpoints import router

__all__ = ["router"]
