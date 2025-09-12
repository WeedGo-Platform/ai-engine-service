"""
Simplified RBAC Service
Provides role-based access control using the new simplified 4-role system
"""

from typing import Dict, List, Optional, Union, Any
from uuid import UUID
from enum import Enum
import asyncpg
import logging
import json

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """Simplified user roles"""
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin" 
    STORE_MANAGER = "store_manager"
    STAFF = "staff"


class RBACService:
    """Service for role-based access control operations"""
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
    
    async def get_user_context(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get complete user context including permissions"""
        async with self.db_pool.acquire() as conn:
            # Use the database function we created
            result = await conn.fetchval(
                "SELECT get_user_context($1)",
                user_id
            )
            return result if result else None
    
    async def has_permission(
        self, 
        user_id: UUID, 
        resource_type: str, 
        action: str
    ) -> bool:
        """Check if user has permission for specific resource and action"""
        async with self.db_pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT user_has_permission($1, $2, $3)",
                user_id, resource_type, action
            )
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email with role and context"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT 
                    u.id,
                    u.email,
                    u.password_hash,
                    u.first_name,
                    u.last_name,
                    u.role,
                    u.tenant_id,
                    u.store_id,
                    u.active,
                    u.email_verified,
                    t.name as tenant_name,
                    s.name as store_name,
                    s.store_code
                FROM users u
                LEFT JOIN tenants t ON u.tenant_id = t.id
                LEFT JOIN stores s ON u.store_id = s.id
                WHERE u.email = $1 AND u.active = true
            """, email)
            
            return dict(row) if row else None
    
    async def create_user(
        self,
        email: str,
        password_hash: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        role: UserRole = UserRole.STAFF,
        tenant_id: Optional[UUID] = None,
        store_id: Optional[UUID] = None
    ) -> UUID:
        """Create a new user with simplified role system"""
        async with self.db_pool.acquire() as conn:
            # Validate tenant requirement for non-super-admin users
            if role != UserRole.SUPER_ADMIN and not tenant_id:
                raise ValueError("Non-super-admin users must belong to a tenant")
            
            # Super admins cannot have tenant restrictions
            if role == UserRole.SUPER_ADMIN:
                tenant_id = None
                store_id = None
            
            user_id = await conn.fetchval("""
                INSERT INTO users (
                    email, password_hash, first_name, last_name, 
                    role, tenant_id, store_id
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """, email, password_hash, first_name, last_name, 
                role.value, tenant_id, store_id)
            
            logger.info(f"Created user {email} with role {role.value}")
            return user_id
    
    async def update_user_role(
        self,
        user_id: UUID,
        new_role: UserRole,
        tenant_id: Optional[UUID] = None,
        store_id: Optional[UUID] = None
    ) -> bool:
        """Update user's role and context"""
        async with self.db_pool.acquire() as conn:
            # Validate role constraints
            if new_role != UserRole.SUPER_ADMIN and not tenant_id:
                raise ValueError("Non-super-admin users must belong to a tenant")
            
            if new_role == UserRole.SUPER_ADMIN:
                tenant_id = None
                store_id = None
            
            result = await conn.execute("""
                UPDATE users 
                SET role = $2, tenant_id = $3, store_id = $4, updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
            """, user_id, new_role.value, tenant_id, store_id)
            
            return result == "UPDATE 1"
    
    async def get_users_by_tenant(
        self, 
        tenant_id: UUID, 
        role: Optional[UserRole] = None
    ) -> List[Dict[str, Any]]:
        """Get all users for a tenant, optionally filtered by role"""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT 
                    u.id,
                    u.email,
                    u.first_name,
                    u.last_name,
                    u.role,
                    u.tenant_id,
                    u.store_id,
                    u.active,
                    u.created_at,
                    s.name as store_name,
                    s.store_code
                FROM users u
                LEFT JOIN stores s ON u.store_id = s.id
                WHERE u.tenant_id = $1
            """
            params = [tenant_id]
            
            if role:
                query += " AND u.role = $2"
                params.append(role.value)
            
            query += " ORDER BY u.role, u.email"
            
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    async def get_users_by_store(self, store_id: UUID) -> List[Dict[str, Any]]:
        """Get all users assigned to a specific store"""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    u.id,
                    u.email,
                    u.first_name,
                    u.last_name,
                    u.role,
                    u.tenant_id,
                    u.store_id,
                    u.active,
                    u.created_at
                FROM users u
                WHERE u.store_id = $1
                ORDER BY u.role, u.email
            """, store_id)
            
            return [dict(row) for row in rows]
    
    async def assign_user_to_store(
        self, 
        user_id: UUID, 
        store_id: UUID
    ) -> bool:
        """Assign user to a specific store"""
        async with self.db_pool.acquire() as conn:
            # Verify store exists and get its tenant
            store_info = await conn.fetchrow(
                "SELECT tenant_id FROM stores WHERE id = $1",
                store_id
            )
            
            if not store_info:
                raise ValueError("Store not found")
            
            # Verify user belongs to same tenant
            user_tenant = await conn.fetchval(
                "SELECT tenant_id FROM users WHERE id = $1",
                user_id
            )
            
            if user_tenant != store_info['tenant_id']:
                raise ValueError("User must belong to same tenant as store")
            
            result = await conn.execute("""
                UPDATE users 
                SET store_id = $2, updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
            """, user_id, store_id)
            
            return result == "UPDATE 1"
    
    async def get_role_permissions(self, role: UserRole) -> List[Dict[str, Any]]:
        """Get all permissions for a specific role"""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT resource_type, action, granted
                FROM role_permissions
                WHERE role = $1
                ORDER BY resource_type, action
            """, role.value)
            
            return [dict(row) for row in rows]
    
    async def grant_permission_override(
        self,
        user_id: UUID,
        resource_type: str,
        action: str,
        granted: bool = True
    ) -> bool:
        """Grant or revoke specific permission override for a user"""
        async with self.db_pool.acquire() as conn:
            permission_key = f"{resource_type}:{action}"
            
            # Get current overrides
            current_overrides_raw = await conn.fetchval(
                "SELECT permissions_override FROM users WHERE id = $1",
                user_id
            )
            
            # Handle JSON parsing
            if isinstance(current_overrides_raw, str):
                current_overrides = json.loads(current_overrides_raw)
            else:
                current_overrides = current_overrides_raw or {}
            
            # Update overrides
            current_overrides[permission_key] = granted
            
            result = await conn.execute("""
                UPDATE users 
                SET permissions_override = $2, updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
            """, user_id, json.dumps(current_overrides))
            
            return result == "UPDATE 1"
    
    def get_role_hierarchy(self) -> Dict[UserRole, int]:
        """Get role hierarchy for permission inheritance"""
        return {
            UserRole.SUPER_ADMIN: 100,
            UserRole.TENANT_ADMIN: 50,
            UserRole.STORE_MANAGER: 25,
            UserRole.STAFF: 10
        }
    
    def can_manage_user(self, manager_role: UserRole, target_role: UserRole) -> bool:
        """Check if manager can manage target user based on role hierarchy"""
        hierarchy = self.get_role_hierarchy()
        return hierarchy[manager_role] > hierarchy[target_role]


class RBACMiddleware:
    """Middleware for API route protection"""
    
    def __init__(self, rbac_service: RBACService):
        self.rbac_service = rbac_service
    
    async def require_permission(
        self,
        user_id: UUID,
        resource_type: str,
        action: str
    ) -> bool:
        """Middleware function to check permissions"""
        has_perm = await self.rbac_service.has_permission(
            user_id, resource_type, action
        )
        
        if not has_perm:
            logger.warning(f"Permission denied: user {user_id} cannot {action} {resource_type}")
        
        return has_perm
    
    async def require_role(self, user_id: UUID, required_role: UserRole) -> bool:
        """Check if user has required role or higher"""
        context = await self.rbac_service.get_user_context(user_id)
        if not context:
            return False
        
        user_role = UserRole(context['user']['role'])
        hierarchy = self.rbac_service.get_role_hierarchy()
        
        return hierarchy[user_role] >= hierarchy[required_role]
    
    async def require_same_tenant(
        self, 
        user_id: UUID, 
        resource_tenant_id: UUID
    ) -> bool:
        """Check if user belongs to same tenant as resource"""
        context = await self.rbac_service.get_user_context(user_id)
        if not context:
            return False
        
        # Super admins can access any tenant
        if context['user']['role'] == UserRole.SUPER_ADMIN.value:
            return True
        
        user_tenant_id = context['user'].get('tenant_id')
        return user_tenant_id == str(resource_tenant_id)


# Helper functions for FastAPI dependencies
async def get_rbac_service(db_pool) -> RBACService:
    """Dependency injection for RBAC service"""
    return RBACService(db_pool)


async def get_rbac_middleware(rbac_service: RBACService) -> RBACMiddleware:
    """Dependency injection for RBAC middleware"""
    return RBACMiddleware(rbac_service)