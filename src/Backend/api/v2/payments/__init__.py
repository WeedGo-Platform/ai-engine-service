"""
Payment Processing V2 API

DDD-powered payment endpoints using the Payment Processing bounded context.

Features:
- Process payments (authorize, capture)
- Refund transactions
- Query transaction history
- Payment event publishing
- Multi-provider support
- Provider configuration management
"""

from fastapi import APIRouter
from .payment_endpoints import router as payment_router
from .payment_provider_endpoints import router as provider_router

# Combine routers into single payments V2 router
router = APIRouter()
router.include_router(payment_router)
router.include_router(provider_router)

__all__ = ["router"]
