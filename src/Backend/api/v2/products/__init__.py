"""
Product Catalog V2 API

DDD-powered product endpoints using the Product Catalog bounded context.

Features:
- OCS product import and management
- Cannabis-specific attributes (THC/CBD, terpenes, plant types)
- Product categorization and search
- Pricing management
- Potency and effect information
- Availability and inventory integration
"""

from .product_endpoints import router

__all__ = ["router"]
