"""
Tenant Management V2 API

DDD-powered tenant and store management endpoints using the Tenant Management bounded context.

Features:
- Multi-tenant subscription management
- Store creation and management
- License tracking and compliance
- Operating hours and channel configuration
- Store context for multi-store operations
- Geographic location and delivery radius
"""

from .tenant_endpoints import router

__all__ = ["router"]
