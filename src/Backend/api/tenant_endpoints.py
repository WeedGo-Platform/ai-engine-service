"""
Tenant Management API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Dict, Optional, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr
import asyncpg
import os
import logging

from core.domain.models import TenantStatus, SubscriptionTier
from core.services.tenant_service import TenantService
from core.repositories.tenant_repository import TenantRepository
from core.repositories.user_repository import UserRepository
from core.repositories.interfaces import ISubscriptionRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tenants", tags=["tenants"])


# Pydantic Models for API
class AddressModel(BaseModel):
    street: str
    city: str
    province: str
    postal_code: str
    country: str = "Canada"


class CreateTenantRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=2, max_length=20, pattern="^[A-Z0-9_-]+$")
    contact_email: EmailStr
    subscription_tier: SubscriptionTier = SubscriptionTier.COMMUNITY
    company_name: Optional[str] = Field(None, max_length=200)
    business_number: Optional[str] = Field(None, max_length=50)
    gst_hst_number: Optional[str] = Field(None, max_length=50)
    address: Optional[AddressModel] = None
    contact_phone: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=200)
    logo_url: Optional[str] = Field(None, max_length=500)
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)


class UpdateTenantRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    company_name: Optional[str] = Field(None, max_length=200)
    business_number: Optional[str] = Field(None, max_length=50)
    gst_hst_number: Optional[str] = Field(None, max_length=50)
    address: Optional[AddressModel] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=200)
    logo_url: Optional[str] = Field(None, max_length=500)
    settings: Optional[Dict[str, Any]] = None


class UpgradeSubscriptionRequest(BaseModel):
    new_tier: SubscriptionTier


class SuspendTenantRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)


class TenantResponse(BaseModel):
    id: UUID
    name: str
    code: str
    company_name: Optional[str]
    business_number: Optional[str]
    gst_hst_number: Optional[str]
    address: Optional[Dict[str, Any]]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    website: Optional[str]
    logo_url: Optional[str]
    status: str
    subscription_tier: str
    max_stores: int
    currency: str
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


# Placeholder subscription repository - implement later
class SubscriptionRepository:
    def __init__(self, pool):
        self.pool = pool
    
    async def create(self, subscription):
        pass
    
    async def get_by_tenant(self, tenant_id):
        return None
    
    async def update(self, subscription):
        pass
    
    async def list_expiring(self, days_ahead):
        return []


# Database connection pool (singleton)
_db_pool = None

async def get_db_pool() -> asyncpg.Pool:
    """Get or create database connection pool"""
    global _db_pool
    if _db_pool is None:
        _db_pool = await asyncpg.create_pool(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5434)),
            database=os.getenv('DB_NAME', 'ai_engine'),
            user=os.getenv('DB_USER', 'weedgo'),
            password=os.getenv('DB_PASSWORD', 'your_password_here'),
            min_size=10,
            max_size=20
        )
    return _db_pool


async def get_tenant_service() -> TenantService:
    """Dependency to get tenant service"""
    pool = await get_db_pool()
    tenant_repo = TenantRepository(pool)
    subscription_repo = SubscriptionRepository(pool)
    return TenantService(tenant_repo, subscription_repo)

async def get_user_repository() -> UserRepository:
    """Dependency to get user repository"""
    pool = await get_db_pool()
    return UserRepository(pool)


@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    request: CreateTenantRequest,
    service: TenantService = Depends(get_tenant_service),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Create a new tenant with admin user"""
    try:
        # Start with tenant creation
        tenant = await service.create_tenant(
            name=request.name,
            code=request.code,
            contact_email=request.contact_email,
            subscription_tier=request.subscription_tier,
            company_name=request.company_name,
            business_number=request.business_number,
            gst_hst_number=request.gst_hst_number,
            address=request.address.dict() if request.address else None,
            contact_phone=request.contact_phone,
            website=request.website,
            logo_url=request.logo_url,
            settings=request.settings
        )
        
        # Check if admin user details are provided in settings
        admin_user_data = request.settings.get('admin_user') if request.settings else None
        created_user = None
        
        if admin_user_data:
            try:
                # Create the admin user
                created_user = await user_repo.create_user(
                    email=admin_user_data.get('email', request.contact_email),
                    password=admin_user_data.get('password'),
                    first_name=admin_user_data.get('first_name'),
                    last_name=admin_user_data.get('last_name'),
                    phone=request.contact_phone
                )
                
                # Link user to tenant with admin role
                await user_repo.create_tenant_user(
                    user_id=created_user['id'],
                    tenant_id=tenant.id,
                    role='admin',
                    permissions={'all': True}
                )
                
                # Add user ID to settings for response
                if not tenant.settings:
                    tenant.settings = {}
                tenant.settings['admin_user'] = {
                    'id': str(created_user['id']),
                    'email': created_user['email']
                }
                
            except ValueError as e:
                # If user creation fails, log but don't fail the whole operation
                logger.warning(f"Failed to create admin user for tenant {tenant.id}: {e}")
                # User might already exist, try to link them
                existing_user = await user_repo.get_user_by_email(
                    admin_user_data.get('email', request.contact_email)
                )
                if existing_user:
                    await user_repo.create_tenant_user(
                        user_id=existing_user['id'],
                        tenant_id=tenant.id,
                        role='admin',
                        permissions={'all': True}
                    )
        
        return TenantResponse(
            id=tenant.id,
            name=tenant.name,
            code=tenant.code,
            company_name=tenant.company_name,
            business_number=tenant.business_number,
            gst_hst_number=tenant.gst_hst_number,
            address=tenant.address.to_dict() if tenant.address else None,
            contact_email=tenant.contact_email,
            contact_phone=tenant.contact_phone,
            website=tenant.website,
            logo_url=tenant.logo_url,
            status=tenant.status.value,
            subscription_tier=tenant.subscription_tier.value,
            max_stores=tenant.max_stores,
            currency=tenant.currency,
            settings=tenant.settings,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating tenant: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create tenant")


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    service: TenantService = Depends(get_tenant_service)
):
    """Get tenant by ID"""
    try:
        tenant = await service.get_tenant(tenant_id)
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        
        return TenantResponse(
            id=tenant.id,
            name=tenant.name,
            code=tenant.code,
            company_name=tenant.company_name,
            business_number=tenant.business_number,
            gst_hst_number=tenant.gst_hst_number,
            address=tenant.address.to_dict() if tenant.address else None,
            contact_email=tenant.contact_email,
            contact_phone=tenant.contact_phone,
            website=tenant.website,
            logo_url=tenant.logo_url,
            status=tenant.status.value,
            subscription_tier=tenant.subscription_tier.value,
            max_stores=tenant.max_stores,
            currency=tenant.currency,
            settings=tenant.settings,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tenant: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get tenant")


@router.get("/by-code/{code}", response_model=TenantResponse)
async def get_tenant_by_code(
    code: str,
    service: TenantService = Depends(get_tenant_service)
):
    """Get tenant by unique code"""
    try:
        tenant = await service.get_tenant_by_code(code)
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        
        return TenantResponse(
            id=tenant.id,
            name=tenant.name,
            code=tenant.code,
            company_name=tenant.company_name,
            business_number=tenant.business_number,
            gst_hst_number=tenant.gst_hst_number,
            address=tenant.address.to_dict() if tenant.address else None,
            contact_email=tenant.contact_email,
            contact_phone=tenant.contact_phone,
            website=tenant.website,
            logo_url=tenant.logo_url,
            status=tenant.status.value,
            subscription_tier=tenant.subscription_tier.value,
            max_stores=tenant.max_stores,
            currency=tenant.currency,
            settings=tenant.settings,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tenant by code: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get tenant")


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: UUID,
    request: UpdateTenantRequest,
    service: TenantService = Depends(get_tenant_service)
):
    """Update tenant information"""
    try:
        tenant = await service.update_tenant(
            tenant_id=tenant_id,
            name=request.name,
            company_name=request.company_name,
            business_number=request.business_number,
            gst_hst_number=request.gst_hst_number,
            address=request.address.dict() if request.address else None,
            contact_email=request.contact_email,
            contact_phone=request.contact_phone,
            website=request.website,
            logo_url=request.logo_url,
            settings=request.settings
        )
        
        return TenantResponse(
            id=tenant.id,
            name=tenant.name,
            code=tenant.code,
            company_name=tenant.company_name,
            business_number=tenant.business_number,
            gst_hst_number=tenant.gst_hst_number,
            address=tenant.address.to_dict() if tenant.address else None,
            contact_email=tenant.contact_email,
            contact_phone=tenant.contact_phone,
            website=tenant.website,
            logo_url=tenant.logo_url,
            status=tenant.status.value,
            subscription_tier=tenant.subscription_tier.value,
            max_stores=tenant.max_stores,
            currency=tenant.currency,
            settings=tenant.settings,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating tenant: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update tenant")


@router.post("/{tenant_id}/upgrade", response_model=TenantResponse)
async def upgrade_subscription(
    tenant_id: UUID,
    request: UpgradeSubscriptionRequest,
    service: TenantService = Depends(get_tenant_service)
):
    """Upgrade tenant subscription tier"""
    try:
        tenant = await service.upgrade_subscription(tenant_id, request.new_tier)
        
        return TenantResponse(
            id=tenant.id,
            name=tenant.name,
            code=tenant.code,
            company_name=tenant.company_name,
            business_number=tenant.business_number,
            gst_hst_number=tenant.gst_hst_number,
            address=tenant.address.to_dict() if tenant.address else None,
            contact_email=tenant.contact_email,
            contact_phone=tenant.contact_phone,
            website=tenant.website,
            logo_url=tenant.logo_url,
            status=tenant.status.value,
            subscription_tier=tenant.subscription_tier.value,
            max_stores=tenant.max_stores,
            currency=tenant.currency,
            settings=tenant.settings,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error upgrading subscription: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upgrade subscription")


@router.post("/{tenant_id}/suspend", response_model=TenantResponse)
async def suspend_tenant(
    tenant_id: UUID,
    request: SuspendTenantRequest,
    service: TenantService = Depends(get_tenant_service)
):
    """Suspend a tenant account"""
    try:
        tenant = await service.suspend_tenant(tenant_id, request.reason)
        
        return TenantResponse(
            id=tenant.id,
            name=tenant.name,
            code=tenant.code,
            company_name=tenant.company_name,
            business_number=tenant.business_number,
            gst_hst_number=tenant.gst_hst_number,
            address=tenant.address.to_dict() if tenant.address else None,
            contact_email=tenant.contact_email,
            contact_phone=tenant.contact_phone,
            website=tenant.website,
            logo_url=tenant.logo_url,
            status=tenant.status.value,
            subscription_tier=tenant.subscription_tier.value,
            max_stores=tenant.max_stores,
            currency=tenant.currency,
            settings=tenant.settings,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error suspending tenant: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to suspend tenant")


@router.post("/{tenant_id}/reactivate", response_model=TenantResponse)
async def reactivate_tenant(
    tenant_id: UUID,
    service: TenantService = Depends(get_tenant_service)
):
    """Reactivate a suspended tenant"""
    try:
        tenant = await service.reactivate_tenant(tenant_id)
        
        return TenantResponse(
            id=tenant.id,
            name=tenant.name,
            code=tenant.code,
            company_name=tenant.company_name,
            business_number=tenant.business_number,
            gst_hst_number=tenant.gst_hst_number,
            address=tenant.address.to_dict() if tenant.address else None,
            contact_email=tenant.contact_email,
            contact_phone=tenant.contact_phone,
            website=tenant.website,
            logo_url=tenant.logo_url,
            status=tenant.status.value,
            subscription_tier=tenant.subscription_tier.value,
            max_stores=tenant.max_stores,
            currency=tenant.currency,
            settings=tenant.settings,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error reactivating tenant: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reactivate tenant")


@router.get("/", response_model=List[TenantResponse])
async def list_tenants(
    status: Optional[TenantStatus] = Query(None),
    subscription_tier: Optional[SubscriptionTier] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: TenantService = Depends(get_tenant_service)
):
    """List tenants with optional filters"""
    try:
        tenants = await service.list_tenants(
            status=status,
            subscription_tier=subscription_tier,
            limit=limit,
            offset=offset
        )
        
        return [
            TenantResponse(
                id=tenant.id,
                name=tenant.name,
                code=tenant.code,
                company_name=tenant.company_name,
                business_number=tenant.business_number,
                gst_hst_number=tenant.gst_hst_number,
                address=tenant.address.to_dict() if tenant.address else None,
                contact_email=tenant.contact_email,
                contact_phone=tenant.contact_phone,
                website=tenant.website,
                logo_url=tenant.logo_url,
                status=tenant.status.value,
                subscription_tier=tenant.subscription_tier.value,
                max_stores=tenant.max_stores,
                currency=tenant.currency,
                settings=tenant.settings,
                created_at=tenant.created_at,
                updated_at=tenant.updated_at
            )
            for tenant in tenants
        ]
        
    except Exception as e:
        logger.error(f"Error listing tenants: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list tenants")


@router.get("/{tenant_id}/can-add-store")
async def can_add_store(
    tenant_id: UUID,
    service: TenantService = Depends(get_tenant_service)
):
    """Check if tenant can add more stores"""
    try:
        can_add = await service.can_add_store(tenant_id)
        return {"can_add_store": can_add}
        
    except Exception as e:
        logger.error(f"Error checking store limit: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to check store limit")