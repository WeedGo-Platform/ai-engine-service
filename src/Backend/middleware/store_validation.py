"""
Store Validation Middleware
Handles store context validation and access control for multi-tenant operations
Follows SOLID principles and clean architecture patterns
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import asyncpg
import logging
from functools import wraps
from enum import Enum

from database import get_db_pool

logger = logging.getLogger(__name__)


class StoreAccessLevel(Enum):
    """Store access permission levels"""
    OWNER = "owner"
    MANAGER = "manager"
    STAFF = "staff"
    VIEWER = "viewer"
    NO_ACCESS = "no_access"


class StoreValidationMiddleware:
    """
    Middleware for validating store context and access permissions
    Implements store isolation and multi-tenant security
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize store validation middleware
        
        Args:
            db_pool: Database connection pool
        """
        self.db_pool = db_pool
    
    async def validate_store_exists(self, store_id: UUID) -> bool:
        """
        Validate that a store exists and is active
        
        Args:
            store_id: UUID of the store
            
        Returns:
            True if store exists and is active
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(
                    "SELECT id, status FROM stores WHERE id = $1",
                    store_id
                )
                
                if not result:
                    return False
                
                return result['status'] == 'active'
                
        except Exception as e:
            logger.error(f"Error validating store existence: {str(e)}")
            return False
    
    async def get_user_store_access(
        self, 
        user_id: UUID, 
        store_id: UUID
    ) -> StoreAccessLevel:
        """
        Get user's access level for a specific store
        
        Args:
            user_id: UUID of the user
            store_id: UUID of the store
            
        Returns:
            Access level enum
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Check user-store permissions
                result = await conn.fetchrow("""
                    SELECT 
                        usp.role,
                        usp.permissions,
                        s.tenant_id,
                        u.tenant_id as user_tenant_id,
                        u.role as user_role
                    FROM user_store_permissions usp
                    JOIN stores s ON usp.store_id = s.id
                    JOIN users u ON usp.user_id = u.id
                    WHERE usp.user_id = $1 AND usp.store_id = $2
                    AND usp.is_active = true
                """, user_id, store_id)
                
                if not result:
                    # Check if user has tenant-level access
                    tenant_result = await conn.fetchrow("""
                        SELECT 
                            u.tenant_id,
                            u.role as user_role,
                            s.tenant_id as store_tenant_id
                        FROM users u, stores s
                        WHERE u.id = $1 AND s.id = $2
                    """, user_id, store_id)
                    
                    if tenant_result and tenant_result['tenant_id'] == tenant_result['store_tenant_id']:
                        # User belongs to same tenant as store
                        if tenant_result['user_role'] in ['admin', 'super_admin']:
                            return StoreAccessLevel.OWNER
                        elif tenant_result['user_role'] == 'manager':
                            return StoreAccessLevel.MANAGER
                        else:
                            return StoreAccessLevel.VIEWER
                    
                    return StoreAccessLevel.NO_ACCESS
                
                # Map database role to access level
                role = result['role']
                if role in ['owner', 'admin']:
                    return StoreAccessLevel.OWNER
                elif role == 'manager':
                    return StoreAccessLevel.MANAGER
                elif role == 'staff':
                    return StoreAccessLevel.STAFF
                elif role == 'viewer':
                    return StoreAccessLevel.VIEWER
                else:
                    return StoreAccessLevel.NO_ACCESS
                    
        except Exception as e:
            logger.error(f"Error getting user store access: {str(e)}")
            return StoreAccessLevel.NO_ACCESS
    
    async def validate_store_operation(
        self,
        user_id: UUID,
        store_id: UUID,
        operation: str,
        required_level: StoreAccessLevel = StoreAccessLevel.STAFF
    ) -> bool:
        """
        Validate if user can perform operation on store
        
        Args:
            user_id: UUID of the user
            store_id: UUID of the store
            operation: Operation name for logging
            required_level: Minimum access level required
            
        Returns:
            True if operation is allowed
            
        Raises:
            HTTPException if validation fails
        """
        # Validate store exists
        if not await self.validate_store_exists(store_id):
            raise HTTPException(
                status_code=404,
                detail=f"Store {store_id} not found or inactive"
            )
        
        # Get user access level
        access_level = await self.get_user_store_access(user_id, store_id)
        
        # Check access hierarchy
        access_hierarchy = {
            StoreAccessLevel.NO_ACCESS: 0,
            StoreAccessLevel.VIEWER: 1,
            StoreAccessLevel.STAFF: 2,
            StoreAccessLevel.MANAGER: 3,
            StoreAccessLevel.OWNER: 4
        }
        
        if access_hierarchy[access_level] < access_hierarchy[required_level]:
            logger.warning(
                f"Access denied for user {user_id} to store {store_id} "
                f"for operation {operation}. Required: {required_level}, Has: {access_level}"
            )
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions for {operation}"
            )
        
        # Log successful validation
        logger.info(
            f"Access granted for user {user_id} to store {store_id} "
            f"for operation {operation}"
        )
        
        return True
    
    async def get_user_accessible_stores(
        self, 
        user_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get list of stores accessible to user
        
        Args:
            user_id: UUID of the user
            
        Returns:
            List of store information with access levels
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Get stores with direct permissions
                direct_stores = await conn.fetch("""
                    SELECT 
                        s.*,
                        usp.role as user_role,
                        usp.permissions,
                        'direct' as access_type
                    FROM stores s
                    JOIN user_store_permissions usp ON s.id = usp.store_id
                    WHERE usp.user_id = $1 
                    AND usp.is_active = true
                    AND s.status = 'active'
                """, user_id)
                
                # Get stores through tenant membership
                tenant_stores = await conn.fetch("""
                    SELECT 
                        s.*,
                        u.role as user_role,
                        NULL as permissions,
                        'tenant' as access_type
                    FROM stores s
                    JOIN users u ON s.tenant_id = u.tenant_id
                    WHERE u.id = $1
                    AND s.status = 'active'
                    AND s.id NOT IN (
                        SELECT store_id FROM user_store_permissions
                        WHERE user_id = $1
                    )
                """, user_id)
                
                # Combine and return results
                all_stores = []
                for store in direct_stores:
                    all_stores.append(dict(store))
                for store in tenant_stores:
                    all_stores.append(dict(store))
                
                return all_stores
                
        except Exception as e:
            logger.error(f"Error getting user accessible stores: {str(e)}")
            return []


# =====================================================
# Dependency Injection Functions
# =====================================================

async def get_store_validator() -> StoreValidationMiddleware:
    """
    Dependency to get store validation middleware instance
    
    Returns:
        StoreValidationMiddleware instance
    """
    db_pool = await get_db_pool()
    return StoreValidationMiddleware(db_pool)


async def validate_store_context(
    request: Request,
    validator: StoreValidationMiddleware = Depends(get_store_validator)
) -> UUID:
    """
    Extract and validate store context from request
    
    Args:
        request: FastAPI request object
        validator: Store validation middleware
        
    Returns:
        Validated store UUID
        
    Raises:
        HTTPException if no valid store context
    """
    # Try to get store ID from header
    store_id_header = request.headers.get("X-Store-ID")
    
    # Try to get from query parameter
    store_id_query = request.query_params.get("store_id")
    
    # Try to get from path parameter
    store_id_path = request.path_params.get("store_id") if hasattr(request, 'path_params') else None
    
    # Priority: path > query > header
    store_id_str = store_id_path or store_id_query or store_id_header
    
    if not store_id_str:
        raise HTTPException(
            status_code=400,
            detail="Store context required. Provide store_id parameter or X-Store-ID header"
        )
    
    try:
        store_id = UUID(store_id_str)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid store ID format: {store_id_str}"
        )
    
    # Validate store exists
    if not await validator.validate_store_exists(store_id):
        raise HTTPException(
            status_code=404,
            detail=f"Store {store_id} not found or inactive"
        )
    
    return store_id


def require_store_access(
    required_level: StoreAccessLevel = StoreAccessLevel.STAFF
):
    """
    Decorator for endpoints requiring store access validation
    
    Args:
        required_level: Minimum access level required
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request and dependencies
            request = kwargs.get('request')
            if not request:
                raise HTTPException(
                    status_code=500,
                    detail="Request object not found in endpoint"
                )
            
            # Get store ID and user ID
            store_id = kwargs.get('store_id')
            user_id = kwargs.get('current_user_id')  # Assumes auth middleware provides this
            
            if not store_id or not user_id:
                raise HTTPException(
                    status_code=400,
                    detail="Store and user context required"
                )
            
            # Validate access
            validator = await get_store_validator()
            await validator.validate_store_operation(
                user_id=user_id,
                store_id=store_id,
                operation=func.__name__,
                required_level=required_level
            )
            
            # Call original function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# =====================================================
# Store Context Manager
# =====================================================

class StoreContext:
    """
    Context manager for store operations
    Ensures proper store isolation and cleanup
    """
    
    def __init__(self, store_id: UUID, user_id: UUID):
        """
        Initialize store context
        
        Args:
            store_id: UUID of the store
            user_id: UUID of the user
        """
        self.store_id = store_id
        self.user_id = user_id
        self.validator = None
        self.access_level = None
    
    async def __aenter__(self):
        """Enter store context"""
        self.validator = await get_store_validator()
        self.access_level = await self.validator.get_user_store_access(
            self.user_id, self.store_id
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit store context"""
        # Log any exceptions
        if exc_type:
            logger.error(
                f"Error in store context {self.store_id} for user {self.user_id}: "
                f"{exc_type.__name__}: {exc_val}"
            )
        return False
    
    async def can_read(self) -> bool:
        """Check if user can read store data"""
        return self.access_level != StoreAccessLevel.NO_ACCESS
    
    async def can_write(self) -> bool:
        """Check if user can write store data"""
        return self.access_level in [
            StoreAccessLevel.STAFF,
            StoreAccessLevel.MANAGER,
            StoreAccessLevel.OWNER
        ]
    
    async def can_manage(self) -> bool:
        """Check if user can manage store settings"""
        return self.access_level in [
            StoreAccessLevel.MANAGER,
            StoreAccessLevel.OWNER
        ]
    
    async def can_admin(self) -> bool:
        """Check if user has admin access to store"""
        return self.access_level == StoreAccessLevel.OWNER