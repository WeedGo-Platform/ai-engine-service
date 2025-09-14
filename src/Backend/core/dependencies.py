"""
Dependency injection for FastAPI endpoints
"""

from typing import AsyncGenerator
from core.services.tenant_service import TenantService
from core.repositories.tenant_repository import TenantRepository
from core.repositories.subscription_repository import SubscriptionRepository
from database.connection import get_db_pool


async def get_tenant_service() -> AsyncGenerator[TenantService, None]:
    """
    Dependency to get TenantService instance
    """
    # Get database pool
    pool = await get_db_pool()
    
    # Create repositories
    tenant_repo = TenantRepository(pool)
    subscription_repo = SubscriptionRepository(pool)
    
    # Create and yield service
    service = TenantService(tenant_repo, subscription_repo)
    yield service