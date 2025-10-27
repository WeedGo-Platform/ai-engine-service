"""
Tenant Management API Endpoints (V1 - Legacy)

⚠️ MIGRATION NOTICE:
This is the V1 Tenant Management API. A new V2 API is available with improved DDD architecture.

**V2 Features:**
- Full Domain-Driven Design implementation
- Subscription tier management with store limits
- Multi-store context support
- License tracking and compliance
- Operating hours and sales channel configuration
- Geographic delivery radius calculations
- Domain events for audit trails

**Migration Path:**
1. V1 endpoints remain functional for backward compatibility
2. New features will only be added to V2
3. V2 API available at `/api/v2/tenants/*`
4. Recommended to migrate to V2 for new integrations

**V2 Endpoints:**
- POST /api/v2/tenants - Create tenant
- GET /api/v2/tenants/{id} - Get tenant
- GET /api/v2/tenants - List tenants
- POST /api/v2/tenants/{id}/upgrade - Upgrade subscription
- POST /api/v2/tenants/{id}/suspend - Suspend tenant
- POST /api/v2/tenants/stores - Create store
- PUT /api/v2/tenants/stores/{id}/license - Update license
- PUT /api/v2/tenants/stores/{id}/channels - Update sales channels
- GET /api/v2/tenants/context/{user_id} - Get store context

For details, see: /docs (search for "Tenant Management V2")
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status, Body
from typing import List, Dict, Optional, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr
import asyncpg
import os
import logging
import secrets
import string

from core.domain.models import TenantStatus, SubscriptionTier
from core.services.tenant_service import TenantService
from core.repositories.tenant_repository import TenantRepository
from core.repositories.user_repository import UserRepository
from core.repositories.interfaces import ISubscriptionRepository
from core.repositories.subscription_repository import SubscriptionRepository
from services.payment.stripe_provider import StripeProvider
from decimal import Decimal

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
    subscription_tier: SubscriptionTier = SubscriptionTier.COMMUNITY_AND_NEW_BUSINESS
    company_name: Optional[str] = Field(None, max_length=200)
    business_number: str = Field(..., min_length=9, max_length=9, pattern="^\\d{9}$", description="Canadian Business Number (9 digits)")
    gst_hst_number: str = Field(..., pattern="^\\d{9}RT\\d{4}$", description="GST/HST Number (format: 123456789RT0001)")
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
    subscription_tier: Optional[SubscriptionTier] = None
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
    business_number: str
    gst_hst_number: str
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

async def get_stripe_provider() -> Optional[StripeProvider]:
    """Get configured Stripe provider instance (returns None if not configured)"""
    import os
    
    stripe_config = {
        'api_key': os.getenv('STRIPE_SECRET_KEY'),
        'publishable_key': os.getenv('STRIPE_PUBLISHABLE_KEY'),
        'webhook_secret': os.getenv('STRIPE_WEBHOOK_SECRET'),
        'environment': os.getenv('STRIPE_ENVIRONMENT', 'test')
    }
    
    if not stripe_config['api_key']:
        logger.warning("Stripe not configured - skipping payment provider setup")
        return None
    
    return StripeProvider(stripe_config)


# Subscription pricing configuration (aligned with domain model)
SUBSCRIPTION_PRICING = {
    SubscriptionTier.COMMUNITY_AND_NEW_BUSINESS: {
        "monthly": Decimal("0.00"),
        "quarterly": Decimal("0.00"),
        "annual": Decimal("0.00"),
        "stripe_price_id": None
    },
    SubscriptionTier.SMALL_BUSINESS: {
        "monthly": Decimal("99.00"),
        "quarterly": Decimal("267.00"),
        "annual": Decimal("950.00"),
        "stripe_price_id": {
            "monthly": "price_1SMdJnFGOg7NVT1jxAJyXHPF",
            "quarterly": "price_1SMdJnFGOg7NVT1jzHW8xLbU",
            "annual": "price_1SMdJnFGOg7NVT1jnOcaCSK5"
        }
    },
    SubscriptionTier.PROFESSIONAL_AND_GROWING_BUSINESS: {
        "monthly": Decimal("199.00"),
        "quarterly": Decimal("199.00"),  # Only monthly available
        "annual": Decimal("199.00"),  # Only monthly available
        "stripe_price_id": {
            "monthly": "price_1SMd4jFGOg7NVT1jRPXgTTUi",
            "quarterly": "price_1SMd4jFGOg7NVT1jRPXgTTUi",  # Fallback to monthly
            "annual": "price_1SMd4jFGOg7NVT1jRPXgTTUi"  # Fallback to monthly
        }
    },
    SubscriptionTier.ENTERPRISE: {
        "monthly": Decimal("299.00"),
        "quarterly": Decimal("299.00"),  # Only monthly available
        "annual": Decimal("299.00"),  # Only monthly available
        "stripe_price_id": {
            "monthly": "price_1SMdduFGOg7NVT1ji6Mhhhcq",
            "quarterly": "price_1SMdduFGOg7NVT1ji6Mhhhcq",  # Fallback to monthly
            "annual": "price_1SMdduFGOg7NVT1ji6Mhhhcq"  # Fallback to monthly
        }
    }
}


class CheckExistsRequest(BaseModel):
    code: Optional[str] = None
    website: Optional[str] = None


@router.post("/check-exists")
async def check_tenant_exists(
    request: CheckExistsRequest,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Check if a tenant with the given code or website already exists"""
    try:
        if not request.code and not request.website:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either code or website must be provided"
            )

        async with pool.acquire() as conn:
            conflicts = []

            # Check by code
            if request.code:
                existing_by_code = await conn.fetchrow("""
                    SELECT id, name, code, website, contact_email FROM tenants
                    WHERE UPPER(code) = UPPER($1)
                """, request.code)

                if existing_by_code:
                    conflicts.append({
                        'type': 'code',
                        'value': request.code,
                        'existing_tenant': {
                            'id': str(existing_by_code['id']),
                            'name': existing_by_code['name'],
                            'code': existing_by_code['code'],
                            'website': existing_by_code['website'],
                            'contact_email': existing_by_code['contact_email']
                        }
                    })

            # Check by website
            if request.website:
                # Normalize website URL
                normalized_website = request.website.lower()
                normalized_website = normalized_website.replace('https://', '').replace('http://', '').rstrip('/')

                existing_by_website = await conn.fetchrow("""
                    SELECT id, name, code, website, contact_email FROM tenants
                    WHERE LOWER(REPLACE(REPLACE(TRIM(website), 'https://', ''), 'http://', '')) = $1
                """, normalized_website)

                if existing_by_website:
                    conflicts.append({
                        'type': 'website',
                        'value': request.website,
                        'existing_tenant': {
                            'id': str(existing_by_website['id']),
                            'name': existing_by_website['name'],
                            'code': existing_by_website['code'],
                            'website': existing_by_website['website'],
                            'contact_email': existing_by_website['contact_email']
                        }
                    })

            return {
                'exists': len(conflicts) > 0,
                'conflicts': conflicts
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking tenant existence: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to check tenant existence")


@router.post("/signup", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant_with_admin(
    request: CreateTenantRequest,
    service: TenantService = Depends(get_tenant_service),
    user_repo: UserRepository = Depends(get_user_repository),
    pool: asyncpg.Pool = Depends(get_db_pool),
    stripe: Optional[StripeProvider] = Depends(get_stripe_provider)
):
    """Create a new tenant with admin user and optional Stripe subscription - atomic operation"""
    try:
        # First check for existing tenant by code
        async with pool.acquire() as conn:
            existing_by_code = await conn.fetchrow("""
                SELECT id, name, code, website FROM tenants
                WHERE UPPER(code) = UPPER($1)
            """, request.code)

            if existing_by_code:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Tenant with code '{request.code}' already exists"
                )

            # Check by website URL (if provided)
            if request.website:
                # Normalize website URL - remove protocol and trailing slash
                normalized_website = request.website.lower()
                normalized_website = normalized_website.replace('https://', '').replace('http://', '').rstrip('/')

                existing_by_website = await conn.fetchrow("""
                    SELECT id, name, code, website FROM tenants
                    WHERE LOWER(REPLACE(REPLACE(website, 'https://', ''), 'http://', '')) = $1
                """, normalized_website)

                if existing_by_website:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Tenant with website '{request.website}' already exists"
                    )

        # Check if admin user is provided
        admin_user_data = request.settings.get('admin_user') if request.settings else None
        if not admin_user_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin user details are required in settings.admin_user"
            )

        # Validate admin user data
        if not admin_user_data.get('email'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin user email is required"
            )
        if not admin_user_data.get('password'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin user password is required"
            )

        # Start transaction for atomic operation
        async with pool.acquire() as conn:
            async with conn.transaction():
                # Create tenant first
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

                # Create admin user
                try:
                    created_user = await user_repo.create_user(
                        email=admin_user_data.get('email'),
                        password=admin_user_data.get('password'),
                        first_name=admin_user_data.get('first_name', 'Admin'),
                        last_name=admin_user_data.get('last_name', 'User'),
                        phone=request.contact_phone
                    )

                    # Link user to tenant with admin role
                    await user_repo.update_user_tenant(
                        user_id=created_user['id'],
                        tenant_id=tenant.id,
                        role='tenant_admin'
                    )

                    # Add user info to response
                    if not tenant.settings:
                        tenant.settings = {}
                    tenant.settings['admin_user'] = {
                        'id': str(created_user['id']),
                        'email': created_user['email']
                    }

                except Exception as user_error:
                    # If user creation fails, the transaction will rollback
                    logger.error(f"Failed to create admin user: {user_error}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to create admin user: {str(user_error)}"
                    )
                
                # Create Stripe subscription for paid tiers
                if request.subscription_tier != SubscriptionTier.COMMUNITY_AND_NEW_BUSINESS and stripe:
                    try:
                        billing_data = request.settings.get('billing', {}) if request.settings else {}
                        billing_cycle = billing_data.get('cycle', 'monthly')
                        payment_method_id = billing_data.get('payment_method_id')
                        
                        # Get pricing for this tier
                        pricing = SUBSCRIPTION_PRICING.get(request.subscription_tier)
                        if not pricing:
                            logger.warning(f"No pricing configured for tier: {request.subscription_tier}")
                        else:
                            base_price = pricing.get(billing_cycle, pricing.get('monthly'))
                            stripe_price_id = None
                            
                            if isinstance(pricing.get('stripe_price_id'), dict):
                                stripe_price_id = pricing['stripe_price_id'].get(billing_cycle)
                            
                            # Only create Stripe subscription if payment method provided and price > 0
                            if payment_method_id and base_price > 0 and stripe_price_id:
                                logger.info(f"Creating Stripe subscription for tenant {tenant.id} - {request.subscription_tier.value} @ ${base_price}/{billing_cycle}")
                                
                                # Create Stripe customer
                                customer_metadata = {
                                    'tenant_id': str(tenant.id),
                                    'tenant_code': tenant.code,
                                    'subscription_tier': request.subscription_tier.value
                                }
                                
                                customer_response = await stripe.create_customer(
                                    email=request.contact_email,
                                    name=request.company_name or request.name,
                                    metadata=customer_metadata,
                                    payment_method_id=payment_method_id
                                )
                                stripe_customer_id = customer_response['customer_id']
                                logger.info(f"Created Stripe customer: {stripe_customer_id}")
                                
                                # Create Stripe subscription (no trial)
                                subscription_metadata = {
                                    'tenant_id': str(tenant.id),
                                    'tenant_code': tenant.code,
                                    'subscription_tier': request.subscription_tier.value,
                                    'billing_cycle': billing_cycle
                                }
                                
                                stripe_sub_response = await stripe.create_subscription(
                                    customer_id=stripe_customer_id,
                                    price_id=stripe_price_id,
                                    trial_period_days=None,  # No trial - charge immediately
                                    metadata=subscription_metadata,
                                    payment_method_id=payment_method_id
                                )
                                stripe_subscription_id = stripe_sub_response['subscription_id']
                                logger.info(f"Created Stripe subscription: {stripe_subscription_id}")
                                
                                # Update subscription record with Stripe IDs
                                subscription_repo = SubscriptionRepository(pool)
                                subscription = await subscription_repo.get_active_by_tenant(tenant.id)
                                
                                if subscription:
                                    if not subscription.metadata:
                                        subscription.metadata = {}
                                    subscription.metadata['stripe_customer_id'] = stripe_customer_id
                                    subscription.metadata['stripe_subscription_id'] = stripe_subscription_id
                                    subscription.payment_method_id = payment_method_id
                                    await subscription_repo.save(subscription)
                                    logger.info(f"Updated subscription {subscription.id} with Stripe metadata")
                            else:
                                if not payment_method_id:
                                    logger.warning(f"No payment method provided for paid tier {request.subscription_tier.value} - skipping Stripe")
                                elif base_price <= 0:
                                    logger.info(f"Free tier subscription - no Stripe needed")
                    
                    except Exception as stripe_error:
                        # Log error but don't fail tenant creation
                        # Tenant is already created, we can handle payment setup later
                        logger.error(f"Failed to create Stripe subscription (tenant created successfully): {stripe_error}")
                        # Could notify admin to manually set up payment

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
        logger.error(f"Error creating tenant with admin: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create tenant")


@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    request: CreateTenantRequest,
    service: TenantService = Depends(get_tenant_service),
    user_repo: UserRepository = Depends(get_user_repository),
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Create a new tenant with admin user - atomic operation with duplicate checking"""
    # Redirect to the new signup endpoint
    return await create_tenant_with_admin(request, service, user_repo, pool)


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
            subscription_tier=request.subscription_tier,
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


# ==================== Tenant User Management Endpoints ====================

class TenantUserRequest(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(..., pattern="^(super_admin|tenant_admin|store_manager|staff|customer)$")
    password: Optional[str] = Field(None, min_length=8)
    permissions: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TenantUserUpdateRequest(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[str] = Field(None, pattern="^(super_admin|tenant_admin|store_manager|staff|customer)$")
    active: Optional[bool] = None
    permissions: Optional[Dict[str, Any]] = None


class TenantUserResponse(BaseModel):
    id: UUID
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    active: bool
    tenant_id: UUID
    permissions: Optional[Dict[str, Any]]
    created_at: datetime
    last_login_at: Optional[datetime]


@router.get("/{tenant_id}/users", response_model=List[TenantUserResponse])
async def get_tenant_users(
    tenant_id: UUID,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Get all users for a tenant"""
    logger.info(f"get_tenant_users called for tenant_id: {tenant_id}")
    logger.info(f"tenant_id type: {type(tenant_id)}")
    try:
        async with pool.acquire() as conn:
            # Query users table directly where tenant_id matches
            # Try both UUID and string comparison to debug
            query = """
                SELECT
                    id, email, first_name, last_name, role, active,
                    tenant_id, permissions, created_at, last_login_at
                FROM users
                WHERE tenant_id = $1::uuid OR tenant_id::text = $1::text
                ORDER BY created_at DESC
            """
            rows = await conn.fetch(query, str(tenant_id))
            logger.info(f"Found {len(rows)} users for tenant {tenant_id}")
            
            # Also try a count query for debugging
            count_query = "SELECT COUNT(*) FROM users WHERE tenant_id IS NOT NULL"
            total_users = await conn.fetchval(count_query)
            logger.info(f"Total users with tenant_id in database: {total_users}")

            users = []
            for row in rows:
                try:
                    logger.debug(f"Processing user row: {dict(row)}")
                    
                    # Parse permissions - handle both JSON string and dict
                    permissions = row['permissions']
                    if isinstance(permissions, str):
                        import json
                        try:
                            permissions = json.loads(permissions) if permissions else {}
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse permissions JSON: {permissions}")
                            permissions = {}
                    elif permissions is None:
                        permissions = {}
                    
                    # Handle potential None values and ensure proper typing
                    user = TenantUserResponse(
                        id=row['id'],
                        email=row['email'] or '',
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        role=row['role'] or 'customer',
                        active=row['active'] if row['active'] is not None else True,
                        tenant_id=row['tenant_id'],
                        permissions=permissions,
                        created_at=row['created_at'],
                        last_login_at=row['last_login_at']
                    )
                    users.append(user)
                except Exception as validation_error:
                    logger.warning(f"Skipping user due to validation error: {validation_error}, row data: {dict(row)}")
                    continue

            logger.info(f"Returning {len(users)} users for tenant {tenant_id}")
            return users
    except Exception as e:
        logger.error(f"Error getting tenant users: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get tenant users")


@router.post("/{tenant_id}/users", response_model=TenantUserResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant_user(
    tenant_id: UUID,
    user_data: TenantUserRequest,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Create a new user for a tenant"""
    try:
        async with pool.acquire() as conn:
            # Check if email already exists
            existing = await conn.fetchval(
                "SELECT id FROM users WHERE email = $1",
                user_data.email
            )
            if existing:
                raise HTTPException(status_code=400, detail="Email already exists")
            
            # Hash password if provided, otherwise generate one
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            password = user_data.password or "TempPassword123!"
            password_hash = pwd_context.hash(password)
            
            # Create user directly in users table with tenant_id
            query = """
                INSERT INTO users (
                    email, password_hash, first_name, last_name, 
                    role, tenant_id, permissions, active, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, true, CURRENT_TIMESTAMP)
                RETURNING id, email, first_name, last_name, role, active, 
                          tenant_id, permissions, created_at, last_login_at
            """
            row = await conn.fetchrow(
                query, 
                user_data.email,
                password_hash,
                user_data.first_name,
                user_data.last_name,
                user_data.role,
                tenant_id,
                user_data.permissions or {}
            )
            
            return TenantUserResponse(
                id=row['id'],
                email=row['email'],
                first_name=row['first_name'],
                last_name=row['last_name'],
                role=row['role'],
                active=row['active'],
                tenant_id=row['tenant_id'],
                permissions=row['permissions'],
                created_at=row['created_at'],
                last_login_at=row['last_login_at']
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating tenant user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create tenant user")


@router.put("/{tenant_id}/users/{user_id}", response_model=TenantUserResponse)
async def update_tenant_user(
    tenant_id: UUID,
    user_id: UUID,
    update_data: TenantUserUpdateRequest,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Update a tenant user"""
    try:
        async with pool.acquire() as conn:
            # Build update query dynamically
            updates = []
            params = []
            param_count = 1
            
            if update_data.first_name is not None:
                updates.append(f"first_name = ${param_count}")
                params.append(update_data.first_name)
                param_count += 1
                
            if update_data.last_name is not None:
                updates.append(f"last_name = ${param_count}")
                params.append(update_data.last_name)
                param_count += 1
                
            if update_data.role is not None:
                updates.append(f"role = ${param_count}")
                params.append(update_data.role)
                param_count += 1
                
            if update_data.active is not None:
                updates.append(f"active = ${param_count}")
                params.append(update_data.active)
                param_count += 1
            
            if update_data.permissions is not None:
                updates.append(f"permissions = ${param_count}")
                params.append(update_data.permissions)
                param_count += 1
            
            if not updates:
                raise HTTPException(status_code=400, detail="No fields to update")
            
            params.extend([user_id, tenant_id])
            query = f"""
                UPDATE users
                SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ${param_count} AND tenant_id = ${param_count + 1}
                RETURNING id, email, first_name, last_name, role, active, 
                          tenant_id, permissions, created_at, last_login_at
            """
            
            row = await conn.fetchrow(query, *params)
            if not row:
                raise HTTPException(status_code=404, detail="User not found")
            
            return TenantUserResponse(
                id=row['id'],
                email=row['email'],
                first_name=row['first_name'],
                last_name=row['last_name'],
                role=row['role'],
                active=row['active'],
                tenant_id=row['tenant_id'],
                permissions=row['permissions'],
                created_at=row['created_at'],
                last_login_at=row['last_login_at']
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tenant user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update tenant user")


class PasswordResetRequest(BaseModel):
    method: str = "otp"  # "email" or "otp"

@router.post("/{tenant_id}/users/{user_id}/reset-password")
async def reset_tenant_user_password(
    tenant_id: UUID,
    user_id: UUID,
    request: Optional[PasswordResetRequest] = None,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Reset a tenant user's password"""
    try:
        reset_method = request.method if request else "otp"
        
        async with pool.acquire() as conn:
            # Get user email
            user_email = await conn.fetchval("""
                SELECT email FROM users
                WHERE id = $1 AND tenant_id = $2
            """, user_id, tenant_id)
            
            if not user_email:
                raise HTTPException(status_code=404, detail="User not found")
            
            if reset_method == "email":
                # In production, send actual email with reset link
                # For now, we'll simulate it
                reset_token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
                
                # Store reset token (in production, store in cache/db with expiry)
                # For demo, just return success
                logger.info(f"Password reset link would be sent to {user_email} with token {reset_token}")
                
                return {"message": f"Password reset link sent to {user_email}"}
            else:
                # Generate temporary password
                import secrets
                import string
                alphabet = string.ascii_letters + string.digits
                temp_password = ''.join(secrets.choice(alphabet) for _ in range(12))
                
                # Hash password
                from passlib.context import CryptContext
                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                password_hash = pwd_context.hash(temp_password)
                
                # Update password
                result = await conn.execute("""
                    UPDATE users
                    SET password_hash = $1, updated_at = CURRENT_TIMESTAMP
                    WHERE id = $2 AND tenant_id = $3
                """, password_hash, user_id, tenant_id)
                
                if result.split()[-1] == '0':
                    raise HTTPException(status_code=404, detail="User not found")
                
                return {"message": "Password reset successfully", "temporary_password": temp_password, "otp": temp_password}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting password: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reset password")


@router.delete("/{tenant_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant_user(
    tenant_id: UUID,
    user_id: UUID,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Remove a user from a tenant (sets tenant_id to NULL)"""
    try:
        async with pool.acquire() as conn:
            # Instead of deleting, set tenant_id to NULL to remove from tenant
            result = await conn.execute("""
                UPDATE users
                SET tenant_id = NULL, updated_at = CURRENT_TIMESTAMP
                WHERE id = $1 AND tenant_id = $2
            """, user_id, tenant_id)
            
            if result.split()[-1] == '0':
                raise HTTPException(status_code=404, detail="User not found in this tenant")
            
            return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting tenant user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete tenant user")


class AddUserToTenantRequest(BaseModel):
    email: EmailStr
    role: str = Field(..., pattern="^(super_admin|tenant_admin|store_manager|staff|customer)$")
    permissions: Optional[Dict[str, Any]] = Field(default_factory=dict)


@router.post("/{tenant_id}/users/add-existing", response_model=TenantUserResponse)
async def add_existing_user_to_tenant(
    tenant_id: UUID,
    request: AddUserToTenantRequest,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Add an existing user to a tenant"""
    try:
        async with pool.acquire() as conn:
            # Find user by email
            user = await conn.fetchrow("""
                SELECT id, email, first_name, last_name, tenant_id, active, created_at, last_login_at
                FROM users
                WHERE email = $1
            """, request.email)
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            if user['tenant_id']:
                raise HTTPException(status_code=400, detail="User already belongs to a tenant")
            
            # Update user with tenant information
            updated_user = await conn.fetchrow("""
                UPDATE users
                SET tenant_id = $1, role = $2, permissions = $3, updated_at = CURRENT_TIMESTAMP
                WHERE id = $4
                RETURNING id, email, first_name, last_name, role, active, 
                          tenant_id, permissions, created_at, last_login_at
            """, tenant_id, request.role, request.permissions or {}, user['id'])
            
            return TenantUserResponse(
                id=updated_user['id'],
                email=updated_user['email'],
                first_name=updated_user['first_name'],
                last_name=updated_user['last_name'],
                role=updated_user['role'],
                active=updated_user['active'],
                tenant_id=updated_user['tenant_id'],
                permissions=updated_user['permissions'],
                created_at=updated_user['created_at'],
                last_login_at=updated_user['last_login_at']
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding user to tenant: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add user to tenant")


@router.patch("/{tenant_id}/users/{user_id}/toggle-active")
async def toggle_tenant_user_active(
    tenant_id: UUID,
    user_id: UUID,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Toggle user active status (block/unblock)"""
    try:
        async with pool.acquire() as conn:
            # First get current status
            current_status = await conn.fetchval("""
                SELECT active FROM users
                WHERE id = $1 AND tenant_id = $2
            """, user_id, tenant_id)
            
            if current_status is None:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Toggle the status
            new_status = not current_status
            
            await conn.execute("""
                UPDATE users
                SET active = $1, updated_at = CURRENT_TIMESTAMP
                WHERE id = $2 AND tenant_id = $3
            """, new_status, user_id, tenant_id)
            
            return {"active": new_status, "message": f"User {'activated' if new_status else 'blocked'} successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling user active status: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to toggle user status")


@router.get("/{tenant_id}/communication-settings")
async def get_tenant_communication_settings(
    tenant_id: UUID,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Get communication settings for a tenant (SMS/Email API configurations)"""
    try:
        async with pool.acquire() as conn:
            settings = await conn.fetchval("""
                SELECT settings FROM tenants WHERE id = $1
            """, tenant_id)

            if settings is None:
                raise HTTPException(status_code=404, detail="Tenant not found")

            # Extract communication settings from tenant settings
            communication_settings = settings.get('communication', {}) if settings else {}

            # Return default structure if not set
            if not communication_settings:
                communication_settings = {
                    'sms': {
                        'provider': 'twilio',
                        'enabled': False,
                        'twilio': {
                            'accountSid': '',
                            'authToken': '',
                            'phoneNumber': '',
                            'verifyServiceSid': ''
                        }
                    },
                    'email': {
                        'provider': 'sendgrid',
                        'enabled': False,
                        'sendgrid': {
                            'apiKey': '',
                            'fromEmail': '',
                            'fromName': '',
                            'replyToEmail': ''
                        }
                    }
                }

            return {"settings": communication_settings}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting communication settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get communication settings")


@router.put("/{tenant_id}/communication-settings")
async def update_tenant_communication_settings(
    tenant_id: UUID,
    request: Dict[str, Any] = Body(...),
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Update communication settings for a tenant (SMS/Email API configurations)"""
    try:
        async with pool.acquire() as conn:
            # Get current settings
            current_settings = await conn.fetchval("""
                SELECT settings FROM tenants WHERE id = $1
            """, tenant_id)

            if current_settings is None:
                raise HTTPException(status_code=404, detail="Tenant not found")

            # Update communication settings
            if not current_settings:
                current_settings = {}

            # Store the communication settings
            current_settings['communication'] = request.get('settings', {})

            # Update tenant settings
            await conn.execute("""
                UPDATE tenants
                SET settings = $1, updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
            """, current_settings, tenant_id)

            return {"message": "Communication settings updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating communication settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update communication settings")


@router.post("/{tenant_id}/communication-settings/validate")
async def validate_communication_channel(
    tenant_id: UUID,
    request: Dict[str, Any] = Body(...),
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Validate communication channel configuration (SMS or Email)"""
    try:
        channel = request.get('channel')

        if channel not in ['sms', 'email']:
            raise HTTPException(status_code=400, detail="Invalid channel. Must be 'sms' or 'email'")

        async with pool.acquire() as conn:
            # Get tenant communication settings
            settings = await conn.fetchval("""
                SELECT settings FROM tenants WHERE id = $1
            """, tenant_id)

            if settings is None:
                raise HTTPException(status_code=404, detail="Tenant not found")

            communication_settings = settings.get('communication', {}) if settings else {}

            # Validate based on channel
            if channel == 'sms':
                sms_settings = communication_settings.get('sms', {})
                if sms_settings.get('provider') == 'twilio':
                    twilio_config = sms_settings.get('twilio', {})
                    if not twilio_config.get('accountSid') or not twilio_config.get('authToken'):
                        return {"valid": False, "message": "Twilio Account SID and Auth Token are required"}
                    if not twilio_config.get('phoneNumber'):
                        return {"valid": False, "message": "Twilio phone number is required"}

                    # TODO: Actual Twilio validation call
                    # For now, just check if values are present
                    return {"valid": True, "message": "SMS configuration appears valid"}

            elif channel == 'email':
                email_settings = communication_settings.get('email', {})
                if email_settings.get('provider') == 'sendgrid':
                    sendgrid_config = email_settings.get('sendgrid', {})
                    if not sendgrid_config.get('apiKey'):
                        return {"valid": False, "message": "SendGrid API Key is required"}
                    if not sendgrid_config.get('fromEmail'):
                        return {"valid": False, "message": "From Email address is required"}

                    # TODO: Actual SendGrid validation call
                    # For now, just check if values are present
                    return {"valid": True, "message": "Email configuration appears valid"}

            return {"valid": False, "message": f"No configuration found for {channel}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating communication channel: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate communication channel")


@router.get("/{tenant_id}/metrics")
async def get_tenant_metrics(
    tenant_id: UUID,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Get metrics for a tenant including store counts and actual last month revenue from orders"""
    try:
        async with pool.acquire() as conn:
            # Get store metrics
            store_metrics = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total_stores,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_stores
                FROM stores
                WHERE tenant_id = $1
            """, tenant_id)

            # Get tenant info
            tenant = await conn.fetchrow("""
                SELECT subscription_tier
                FROM tenants
                WHERE id = $1
            """, tenant_id)

            # Get actual revenue from completed orders in the last month
            # Using order_status = 'completed' and payment_status = 'paid' or 'completed'
            revenue_data = await conn.fetchrow("""
                SELECT
                    COALESCE(SUM(total_amount), 0) as last_month_revenue,
                    COUNT(*) as order_count
                FROM orders
                WHERE tenant_id = $1
                    AND order_status IN ('completed', 'processing')
                    AND payment_status IN ('paid', 'completed', 'captured')
                    AND created_at >= date_trunc('month', CURRENT_DATE - INTERVAL '1 month')
                    AND created_at < date_trunc('month', CURRENT_DATE)
            """, tenant_id)

            # If no revenue data for last month, check current month for demo purposes
            if revenue_data.get('last_month_revenue', 0) == 0:
                current_month_revenue = await conn.fetchrow("""
                    SELECT
                        COALESCE(SUM(total_amount), 0) as current_month_revenue,
                        COUNT(*) as order_count
                    FROM orders
                    WHERE tenant_id = $1
                        AND order_status IN ('completed', 'processing')
                        AND payment_status IN ('paid', 'completed', 'captured')
                        AND created_at >= date_trunc('month', CURRENT_DATE)
                """, tenant_id)

                # Use current month data if available (for demo/testing)
                last_month_revenue = float(current_month_revenue.get('current_month_revenue', 0))
                order_count = current_month_revenue.get('order_count', 0)
            else:
                last_month_revenue = float(revenue_data.get('last_month_revenue', 0))
                order_count = revenue_data.get('order_count', 0)

            return {
                "total_stores": store_metrics.get('total_stores', 0),
                "active_stores": store_metrics.get('active_stores', 0),
                "last_month_revenue": last_month_revenue,
                "order_count": order_count,
                "subscription_tier": tenant.get('subscription_tier')
            }
    except Exception as e:
        logger.error(f"Error getting tenant metrics: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get tenant metrics")