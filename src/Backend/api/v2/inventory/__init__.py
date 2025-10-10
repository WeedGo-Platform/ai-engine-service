"""
Inventory Management V2 API

DDD-powered inventory endpoints using the Inventory Management bounded context.

Features:
- Stock level management
- Reserve/release operations
- Receive and consume stock
- Pricing and margin calculations
- Reorder level management
- Cycle counting
- Inventory valuation
"""

from .inventory_endpoints import router

__all__ = ["router"]
