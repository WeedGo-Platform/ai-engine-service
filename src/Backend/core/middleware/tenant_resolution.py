"""
Tenant Resolution Middleware
Resolves tenant context from various sources following the Chain of Responsibility pattern
"""

import os
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from abc import ABC, abstractmethod
from urllib.parse import urlparse
import asyncpg
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import json

logger = logging.getLogger(__name__)


@dataclass
class TenantContext:
    """Value object for tenant context"""
    tenant_id: str
    tenant_code: str
    tenant_name: str
    subdomain: Optional[str] = None
    template_id: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    store_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "tenant_id": self.tenant_id,
            "tenant_code": self.tenant_code,
            "tenant_name": self.tenant_name,
            "subdomain": self.subdomain,
            "template_id": self.template_id,
            "settings": self.settings,
            "store_id": self.store_id
        }


class TenantResolver(ABC):
    """Abstract base class for tenant resolution strategies"""
    
    @abstractmethod
    async def resolve(self, request: Request) -> Optional[TenantContext]:
        """Resolve tenant from request"""
        pass


class SubdomainTenantResolver(TenantResolver):
    """Resolves tenant from subdomain"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.base_domain = os.getenv("BASE_DOMAIN", "weedgo.com")
    
    async def resolve(self, request: Request) -> Optional[TenantContext]:
        """Extract tenant from subdomain"""
        try:
            host = request.headers.get("host", "")
            
            # Parse the host
            if ":" in host:
                hostname = host.split(":")[0]
            else:
                hostname = host
            
            # Check if it's a subdomain
            if hostname.endswith(self.base_domain):
                # Remove base domain to get subdomain
                subdomain_part = hostname.replace(f".{self.base_domain}", "")
                if subdomain_part and subdomain_part != hostname:
                    # We have a subdomain, look it up
                    return await self._lookup_tenant_by_subdomain(subdomain_part)
            
            return None
            
        except Exception as e:
            logger.error(f"Error resolving tenant from subdomain: {e}")
            return None
    
    async def _lookup_tenant_by_subdomain(self, subdomain: str) -> Optional[TenantContext]:
        """Look up tenant by subdomain in database"""
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT 
                        t.id,
                        t.code,
                        t.name,
                        t.subdomain,
                        t.default_template_id,
                        t.settings,
                        tt.template_id,
                        tt.configuration as template_config
                    FROM tenants t
                    LEFT JOIN tenant_templates tt ON t.id = tt.tenant_id AND tt.is_default = true
                    WHERE t.subdomain = $1 AND t.status = 'active'
                """, subdomain)
                
                if row:
                    return TenantContext(
                        tenant_id=str(row['id']),
                        tenant_code=row['code'],
                        tenant_name=row['name'],
                        subdomain=row['subdomain'],
                        template_id=row['template_id'] or row['default_template_id'],
                        settings=json.loads(row['settings']) if row['settings'] else {}
                    )
            return None
            
        except Exception as e:
            logger.error(f"Database error looking up tenant: {e}")
            return None


class HeaderTenantResolver(TenantResolver):
    """Resolves tenant from X-Tenant-Id or X-Tenant-Code header"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
    
    async def resolve(self, request: Request) -> Optional[TenantContext]:
        """Extract tenant from headers"""
        try:
            # Check X-Tenant-Id header
            tenant_id = request.headers.get("X-Tenant-Id")
            if tenant_id:
                return await self._lookup_tenant_by_id(tenant_id)
            
            # Check X-Tenant-Code header
            tenant_code = request.headers.get("X-Tenant-Code")
            if tenant_code:
                return await self._lookup_tenant_by_code(tenant_code)
            
            return None
            
        except Exception as e:
            logger.error(f"Error resolving tenant from headers: {e}")
            return None
    
    async def _lookup_tenant_by_id(self, tenant_id: str) -> Optional[TenantContext]:
        """Look up tenant by ID"""
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT 
                        t.id,
                        t.code,
                        t.name,
                        t.subdomain,
                        t.default_template_id,
                        t.settings,
                        tt.template_id,
                        tt.configuration as template_config
                    FROM tenants t
                    LEFT JOIN tenant_templates tt ON t.id = tt.tenant_id AND tt.is_default = true
                    WHERE t.id = $1::uuid AND t.status = 'active'
                """, tenant_id)
                
                if row:
                    return TenantContext(
                        tenant_id=str(row['id']),
                        tenant_code=row['code'],
                        tenant_name=row['name'],
                        subdomain=row['subdomain'],
                        template_id=row['template_id'] or row['default_template_id'],
                        settings=json.loads(row['settings']) if row['settings'] else {}
                    )
            return None
            
        except Exception as e:
            logger.error(f"Database error looking up tenant by ID: {e}")
            return None
    
    async def _lookup_tenant_by_code(self, tenant_code: str) -> Optional[TenantContext]:
        """Look up tenant by code"""
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT 
                        t.id,
                        t.code,
                        t.name,
                        t.subdomain,
                        t.default_template_id,
                        t.settings,
                        tt.template_id,
                        tt.configuration as template_config
                    FROM tenants t
                    LEFT JOIN tenant_templates tt ON t.id = tt.tenant_id AND tt.is_default = true
                    WHERE t.code = $1 AND t.status = 'active'
                """, tenant_code)
                
                if row:
                    return TenantContext(
                        tenant_id=str(row['id']),
                        tenant_code=row['code'],
                        tenant_name=row['name'],
                        subdomain=row['subdomain'],
                        template_id=row['template_id'] or row['default_template_id'],
                        settings=json.loads(row['settings']) if row['settings'] else {}
                    )
            return None
            
        except Exception as e:
            logger.error(f"Database error looking up tenant by code: {e}")
            return None


class PortMappingTenantResolver(TenantResolver):
    """Resolves tenant from port mapping (for development)"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.port_mapping = self._load_port_mapping()
    
    def _load_port_mapping(self) -> Dict[int, str]:
        """Load port to tenant mapping from environment or config"""
        # Default mapping for development
        mapping = {
            5173: "default",
            5174: "pot-palace",
            5175: "modern-minimal",
            5176: "dark-tech",
            5177: "rasta-vibes",
            5178: "weedgo",
            5179: "vintage",
            5180: "dirty",
            5181: "metal"
        }
        
        # Override from environment if available
        env_mapping = os.getenv("TENANT_PORT_MAPPING")
        if env_mapping:
            try:
                mapping = json.loads(env_mapping)
            except json.JSONDecodeError:
                logger.warning("Invalid TENANT_PORT_MAPPING environment variable")
        
        return mapping
    
    async def resolve(self, request: Request) -> Optional[TenantContext]:
        """Extract tenant from port mapping"""
        try:
            # Get the port from the host header
            host = request.headers.get("host", "")
            if ":" in host:
                port = int(host.split(":")[1])
                tenant_code = self.port_mapping.get(port)
                
                if tenant_code:
                    return await self._lookup_tenant_by_code(tenant_code)
            
            return None
            
        except Exception as e:
            logger.error(f"Error resolving tenant from port: {e}")
            return None
    
    async def _lookup_tenant_by_code(self, tenant_code: str) -> Optional[TenantContext]:
        """Look up tenant by code"""
        # For development, we might not have all tenants in DB
        # Create a mock tenant context
        if tenant_code == "default":
            return TenantContext(
                tenant_id="00000000-0000-0000-0000-000000000000",
                tenant_code="default",
                tenant_name="Default Tenant",
                template_id="modern-minimal"
            )
        
        # Otherwise look up in database
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT 
                        t.id,
                        t.code,
                        t.name,
                        t.subdomain,
                        t.default_template_id,
                        t.settings
                    FROM tenants t
                    WHERE t.code = $1 AND t.status = 'active'
                """, tenant_code)
                
                if row:
                    return TenantContext(
                        tenant_id=str(row['id']),
                        tenant_code=row['code'],
                        tenant_name=row['name'],
                        subdomain=row['subdomain'],
                        template_id=row['default_template_id'] or tenant_code,
                        settings=json.loads(row['settings']) if row['settings'] else {}
                    )
                    
        except Exception as e:
            logger.error(f"Database error looking up tenant: {e}")
        
        # Return mock tenant for development
        return TenantContext(
            tenant_id=f"{tenant_code}-id",
            tenant_code=tenant_code,
            tenant_name=tenant_code.replace("-", " ").title(),
            template_id=tenant_code
        )


class QueryParamTenantResolver(TenantResolver):
    """Resolves tenant from query parameter (fallback)"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
    
    async def resolve(self, request: Request) -> Optional[TenantContext]:
        """Extract tenant from query parameters"""
        try:
            # Parse query parameters
            tenant_param = request.query_params.get("tenant")
            if not tenant_param:
                return None
            
            # Try to resolve as ID or code
            return await self._lookup_tenant(tenant_param)
            
        except Exception as e:
            logger.error(f"Error resolving tenant from query params: {e}")
            return None
    
    async def _lookup_tenant(self, identifier: str) -> Optional[TenantContext]:
        """Look up tenant by ID or code"""
        try:
            async with self.db_pool.acquire() as conn:
                # Try both ID and code
                row = await conn.fetchrow("""
                    SELECT 
                        t.id,
                        t.code,
                        t.name,
                        t.subdomain,
                        t.default_template_id,
                        t.settings
                    FROM tenants t
                    WHERE (t.id::text = $1 OR t.code = $1) 
                      AND t.status = 'active'
                """, identifier)
                
                if row:
                    return TenantContext(
                        tenant_id=str(row['id']),
                        tenant_code=row['code'],
                        tenant_name=row['name'],
                        subdomain=row['subdomain'],
                        template_id=row['default_template_id'],
                        settings=json.loads(row['settings']) if row['settings'] else {}
                    )
            return None
            
        except Exception as e:
            logger.error(f"Database error looking up tenant: {e}")
            return None


class TenantResolutionChain:
    """Chain of Responsibility for tenant resolution"""
    
    def __init__(self, resolvers: List[TenantResolver]):
        self.resolvers = resolvers
    
    async def resolve(self, request: Request) -> Optional[TenantContext]:
        """Try each resolver in order until one succeeds"""
        for resolver in self.resolvers:
            tenant = await resolver.resolve(request)
            if tenant:
                logger.info(f"Tenant resolved: {tenant.tenant_code} using {resolver.__class__.__name__}")
                return tenant
        return None


class TenantResolutionMiddleware(BaseHTTPMiddleware):
    """
    Middleware for resolving tenant context
    Adds tenant information to request state for downstream use
    """
    
    def __init__(
        self, 
        app: ASGIApp,
        db_pool: asyncpg.Pool,
        require_tenant: bool = False,
        excluded_paths: Optional[List[str]] = None
    ):
        super().__init__(app)
        self.db_pool = db_pool
        self.require_tenant = require_tenant
        self.excluded_paths = excluded_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/metrics",
            "/api/tenants/resolve"
        ]
        
        # Initialize resolution chain
        self.resolution_chain = self._create_resolution_chain()
    
    def _create_resolution_chain(self) -> TenantResolutionChain:
        """Create the chain of resolvers based on environment"""
        resolvers = []
        
        # Determine environment
        env = os.getenv("ENVIRONMENT", "development")
        
        if env == "production":
            # Production: Subdomain -> Header -> Query
            resolvers.append(SubdomainTenantResolver(self.db_pool))
            resolvers.append(HeaderTenantResolver(self.db_pool))
            resolvers.append(QueryParamTenantResolver(self.db_pool))
        else:
            # Development: Port -> Header -> Query -> Subdomain
            resolvers.append(PortMappingTenantResolver(self.db_pool))
            resolvers.append(HeaderTenantResolver(self.db_pool))
            resolvers.append(QueryParamTenantResolver(self.db_pool))
            resolvers.append(SubdomainTenantResolver(self.db_pool))
        
        return TenantResolutionChain(resolvers)
    
    def _is_excluded_path(self, path: str) -> bool:
        """Check if path is excluded from tenant resolution"""
        for excluded in self.excluded_paths:
            if path.startswith(excluded):
                return True
        return False
    
    async def dispatch(self, request: Request, call_next):
        """Process the request and add tenant context"""
        # Check if path is excluded
        if self._is_excluded_path(request.url.path):
            return await call_next(request)
        
        try:
            # Resolve tenant
            tenant_context = await self.resolution_chain.resolve(request)
            
            # Check if tenant is required
            if self.require_tenant and not tenant_context:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Tenant context required but not found"}
                )
            
            # Add tenant context to request state
            if tenant_context:
                request.state.tenant = tenant_context
                
                # Add tenant headers to response
                response = await call_next(request)
                response.headers["X-Tenant-Id"] = tenant_context.tenant_id
                response.headers["X-Tenant-Code"] = tenant_context.tenant_code
                if tenant_context.template_id:
                    response.headers["X-Template-Id"] = tenant_context.template_id
                
                return response
            else:
                # No tenant found, but not required
                request.state.tenant = None
                return await call_next(request)
                
        except Exception as e:
            logger.error(f"Error in tenant resolution middleware: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error during tenant resolution"}
            )


# Utility function to get tenant from request
def get_tenant_context(request: Request) -> Optional[TenantContext]:
    """Get tenant context from request state"""
    return getattr(request.state, "tenant", None)


# Dependency for FastAPI routes
async def require_tenant(request: Request) -> TenantContext:
    """FastAPI dependency to require tenant context"""
    tenant = get_tenant_context(request)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required"
        )
    return tenant


async def optional_tenant(request: Request) -> Optional[TenantContext]:
    """FastAPI dependency for optional tenant context"""
    return get_tenant_context(request)