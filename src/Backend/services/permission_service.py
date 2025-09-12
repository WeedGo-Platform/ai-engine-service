"""
Permission Service
Handles user permission checks for tenants and stores
"""

from typing import Dict, List, Optional, Set
from uuid import UUID
import asyncpg
import logging
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class SystemRole(Enum):
    """System-wide roles"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    USER = "user"


class TenantRole(Enum):
    """Tenant-level roles"""
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"


class StoreRole(Enum):
    """Store-level roles"""
    MANAGER = "manager"
    SUPERVISOR = "supervisor"
    STAFF = "staff"
    CASHIER = "cashier"


@dataclass
class UserPermissions:
    """User permission structure"""
    user_id: UUID
    system_role: str
    is_super_admin: bool
    tenant_permissions: List[Dict]  # List of {tenant_id, tenant_name, role, permissions}
    store_permissions: List[Dict]   # List of {store_id, store_name, tenant_id, role, permissions}
    accessible_tenant_ids: Set[UUID]
    accessible_store_ids: Set[UUID]


class PermissionService:
    """Service for managing user permissions"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
    
    async def get_user_permissions(self, user_id: UUID) -> UserPermissions:
        """
        Get comprehensive user permissions including system, tenant, and store levels
        """
        async with self.db_pool.acquire() as conn:
            # Get user's system role
            user_data = await conn.fetchrow("""
                SELECT role, tenant_id, default_store_id
                FROM users
                WHERE id = $1 AND active = true
            """, user_id)
            
            if not user_data:
                raise ValueError(f"User {user_id} not found or inactive")
            
            system_role = user_data['role'] or 'user'
            is_super_admin = system_role in ['super_admin', 'admin']
            
            # Initialize permission sets
            accessible_tenant_ids = set()
            accessible_store_ids = set()
            tenant_permissions = []
            store_permissions = []
            
            if is_super_admin:
                # Super admin has access to all tenants and stores
                all_tenants = await conn.fetch("""
                    SELECT id, name, code
                    FROM tenants
                    WHERE status = 'active'
                """)
                
                for tenant in all_tenants:
                    accessible_tenant_ids.add(tenant['id'])
                    tenant_permissions.append({
                        'tenant_id': tenant['id'],
                        'tenant_name': tenant['name'],
                        'tenant_code': tenant['code'],
                        'role': 'admin',
                        'permissions': ['all']
                    })
                
                # Get all stores
                all_stores = await conn.fetch("""
                    SELECT s.id, s.name, s.store_code, s.tenant_id, t.name as tenant_name
                    FROM stores s
                    JOIN tenants t ON s.tenant_id = t.id
                    WHERE s.status = 'active'
                """)
                
                for store in all_stores:
                    accessible_store_ids.add(store['id'])
                    store_permissions.append({
                        'store_id': store['id'],
                        'store_name': store['name'],
                        'store_code': store['store_code'],
                        'tenant_id': store['tenant_id'],
                        'tenant_name': store['tenant_name'],
                        'role': 'admin',
                        'permissions': ['all']
                    })
            else:
                # Removed tenant_users table references
                # Permissions now come directly from user roles
                
                # Removed store_users table references
                # Store permissions handled differently
                store_roles = []
                
                for sr in store_roles:
                    accessible_store_ids.add(sr['store_id'])
                    # Check if we already have this store from tenant permissions
                    existing = next(
                        (sp for sp in store_permissions if sp['store_id'] == sr['store_id']),
                        None
                    )
                    
                    if not existing:
                        store_permissions.append({
                            'store_id': sr['store_id'],
                            'store_name': sr['store_name'],
                            'store_code': sr['store_code'],
                            'tenant_id': sr['tenant_id'],
                            'tenant_name': sr['tenant_name'],
                            'role': sr['role'],
                            'permissions': sr['permissions'] or {}
                        })
                    elif sr['role'] in ['manager', 'supervisor']:
                        # Direct store role might have higher permissions than inherited
                        existing['role'] = sr['role']
                        existing['permissions'] = sr['permissions'] or {}
            
            return UserPermissions(
                user_id=user_id,
                system_role=system_role,
                is_super_admin=is_super_admin,
                tenant_permissions=tenant_permissions,
                store_permissions=store_permissions,
                accessible_tenant_ids=accessible_tenant_ids,
                accessible_store_ids=accessible_store_ids
            )
    
    async def can_access_tenant(self, user_id: UUID, tenant_id: UUID) -> bool:
        """Check if user can access a specific tenant"""
        permissions = await self.get_user_permissions(user_id)
        return permissions.is_super_admin or tenant_id in permissions.accessible_tenant_ids
    
    async def can_access_store(self, user_id: UUID, store_id: UUID) -> bool:
        """Check if user can access a specific store"""
        permissions = await self.get_user_permissions(user_id)
        return permissions.is_super_admin or store_id in permissions.accessible_store_ids
    
    async def get_user_tenant_role(self, user_id: UUID, tenant_id: UUID) -> Optional[str]:
        """Get user's role for a specific tenant"""
        permissions = await self.get_user_permissions(user_id)
        
        if permissions.is_super_admin:
            return 'admin'
        
        for tp in permissions.tenant_permissions:
            if tp['tenant_id'] == tenant_id:
                return tp['role']
        
        return None
    
    async def get_user_store_role(self, user_id: UUID, store_id: UUID) -> Optional[str]:
        """Get user's role for a specific store"""
        permissions = await self.get_user_permissions(user_id)
        
        if permissions.is_super_admin:
            return 'admin'
        
        for sp in permissions.store_permissions:
            if sp['store_id'] == store_id:
                return sp['role']
        
        return None
    
    async def filter_accessible_stores(
        self, 
        user_id: UUID, 
        store_ids: List[UUID]
    ) -> List[UUID]:
        """Filter a list of store IDs to only those the user can access"""
        permissions = await self.get_user_permissions(user_id)
        
        if permissions.is_super_admin:
            return store_ids
        
        return [sid for sid in store_ids if sid in permissions.accessible_store_ids]
    
    async def filter_accessible_tenants(
        self, 
        user_id: UUID, 
        tenant_ids: List[UUID]
    ) -> List[UUID]:
        """Filter a list of tenant IDs to only those the user can access"""
        permissions = await self.get_user_permissions(user_id)
        
        if permissions.is_super_admin:
            return tenant_ids
        
        return [tid for tid in tenant_ids if tid in permissions.accessible_tenant_ids]