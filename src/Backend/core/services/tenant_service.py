"""
Tenant Service - Business Logic Layer
"""

from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
import logging

from core.domain.models import (
    Tenant, TenantStatus, SubscriptionTier, Address,
    TenantSubscription, BillingCycle
)
from core.repositories.interfaces import ITenantRepository, ISubscriptionRepository

logger = logging.getLogger(__name__)


class TenantService:
    """Service for managing tenants"""
    
    def __init__(
        self, 
        tenant_repository: ITenantRepository,
        subscription_repository: ISubscriptionRepository
    ):
        self.tenant_repo = tenant_repository
        self.subscription_repo = subscription_repository
    
    async def create_tenant(
        self,
        name: str,
        code: str,
        contact_email: str,
        subscription_tier: SubscriptionTier = SubscriptionTier.COMMUNITY_AND_NEW_BUSINESS,
        company_name: Optional[str] = None,
        business_number: Optional[str] = None,
        gst_hst_number: Optional[str] = None,
        address: Optional[Dict[str, Any]] = None,
        contact_phone: Optional[str] = None,
        website: Optional[str] = None,
        logo_url: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Tenant:
        """Create a new tenant with subscription"""
        try:
            # Validate unique code
            existing = await self.tenant_repo.get_by_code(code)
            if existing:
                raise ValueError(f"Tenant with code '{code}' already exists")
            
            # Create address if provided
            address_obj = None
            if address:
                address_obj = Address(
                    street=address.get('street', ''),
                    city=address.get('city', ''),
                    province=address.get('province', ''),
                    postal_code=address.get('postal_code', ''),
                    country=address.get('country', 'Canada')
                )
            
            # Determine store limits based on subscription
            store_limits = {
                SubscriptionTier.COMMUNITY_AND_NEW_BUSINESS: 1,
                SubscriptionTier.SMALL_BUSINESS: 5,
                SubscriptionTier.PROFESSIONAL_AND_GROWING_BUSINESS: 12,
                SubscriptionTier.ENTERPRISE: 999  # Effectively unlimited
            }
            
            # Create tenant entity
            tenant = Tenant(
                id=uuid4(),
                name=name,
                code=code,
                company_name=company_name,
                business_number=business_number,
                gst_hst_number=gst_hst_number,
                address=address_obj,
                contact_email=contact_email,
                contact_phone=contact_phone,
                website=website,
                logo_url=logo_url,
                status=TenantStatus.ACTIVE,
                subscription_tier=subscription_tier,
                max_stores=store_limits.get(subscription_tier, 1),
                billing_info={},
                currency="CAD",
                settings=settings or {},
                metadata={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Save tenant
            saved_tenant = await self.tenant_repo.create(tenant)
            
            # Create subscription
            subscription = TenantSubscription(
                id=uuid4(),
                tenant_id=saved_tenant.id,
                tier=subscription_tier,
                store_limit=saved_tenant.max_stores,
                ai_personalities_per_store=saved_tenant.get_ai_personality_limit(),
                billing_cycle=BillingCycle.MONTHLY if subscription_tier != SubscriptionTier.COMMUNITY_AND_NEW_BUSINESS else None,
                price_cad=TenantSubscription().get_monthly_price(),
                features=self._get_tier_features(subscription_tier),
                status="active",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            await self.subscription_repo.create(subscription)
            
            logger.info(f"Created tenant '{name}' with code '{code}' and {subscription_tier.value} subscription")
            return saved_tenant
            
        except Exception as e:
            logger.error(f"Error creating tenant: {e}")
            raise
    
    async def get_tenant(self, tenant_id: UUID) -> Optional[Tenant]:
        """Get tenant by ID"""
        return await self.tenant_repo.get_by_id(tenant_id)
    
    async def get_tenant_by_code(self, code: str) -> Optional[Tenant]:
        """Get tenant by unique code"""
        return await self.tenant_repo.get_by_code(code)
    
    async def update_tenant(
        self,
        tenant_id: UUID,
        name: Optional[str] = None,
        company_name: Optional[str] = None,
        business_number: Optional[str] = None,
        gst_hst_number: Optional[str] = None,
        address: Optional[Dict[str, Any]] = None,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None,
        website: Optional[str] = None,
        logo_url: Optional[str] = None,
        subscription_tier: Optional[SubscriptionTier] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Tenant:
        """Update tenant information"""
        try:
            tenant = await self.tenant_repo.get_by_id(tenant_id)
            if not tenant:
                raise ValueError(f"Tenant {tenant_id} not found")
            
            # Update fields if provided
            if name is not None:
                tenant.name = name
            if company_name is not None:
                tenant.company_name = company_name
            if business_number is not None:
                tenant.business_number = business_number
            if gst_hst_number is not None:
                tenant.gst_hst_number = gst_hst_number
            if address is not None:
                tenant.address = Address(
                    street=address.get('street', ''),
                    city=address.get('city', ''),
                    province=address.get('province', ''),
                    postal_code=address.get('postal_code', ''),
                    country=address.get('country', 'Canada')
                )
            if contact_email is not None:
                tenant.contact_email = contact_email
            if contact_phone is not None:
                tenant.contact_phone = contact_phone
            if website is not None:
                tenant.website = website
            if logo_url is not None:
                tenant.logo_url = logo_url
            if subscription_tier is not None:
                # Update subscription tier and related fields
                tenant.subscription_tier = subscription_tier
                # Update max_stores based on new tier
                store_limit = self._get_store_limit(subscription_tier)
                tenant.max_stores = store_limit if store_limit else 999
            if settings is not None:
                tenant.settings = settings
            
            return await self.tenant_repo.update(tenant)
            
        except Exception as e:
            logger.error(f"Error updating tenant {tenant_id}: {e}")
            raise
    
    async def upgrade_subscription(
        self,
        tenant_id: UUID,
        new_tier: SubscriptionTier
    ) -> Tenant:
        """Upgrade tenant subscription tier"""
        try:
            tenant = await self.tenant_repo.get_by_id(tenant_id)
            if not tenant:
                raise ValueError(f"Tenant {tenant_id} not found")
            
            # Prevent downgrade if stores exceed new limit
            current_stores = await self.tenant_repo.count_stores(tenant_id)
            new_limit = self._get_store_limit(new_tier)
            
            if new_limit and current_stores > new_limit:
                raise ValueError(
                    f"Cannot downgrade to {new_tier.value}. "
                    f"Current stores ({current_stores}) exceed limit ({new_limit})"
                )
            
            # Update tenant
            tenant.subscription_tier = new_tier
            tenant.max_stores = new_limit or 999
            
            updated_tenant = await self.tenant_repo.update(tenant)
            
            # Update subscription
            subscription = await self.subscription_repo.get_by_tenant(tenant_id)
            if subscription:
                subscription.tier = new_tier
                subscription.store_limit = updated_tenant.max_stores
                subscription.ai_personalities_per_store = updated_tenant.get_ai_personality_limit()
                subscription.price_cad = subscription.get_monthly_price()
                subscription.features = self._get_tier_features(new_tier)
                await self.subscription_repo.update(subscription)
            
            logger.info(f"Upgraded tenant {tenant_id} to {new_tier.value}")
            return updated_tenant
            
        except Exception as e:
            logger.error(f"Error upgrading subscription for tenant {tenant_id}: {e}")
            raise
    
    async def suspend_tenant(self, tenant_id: UUID, reason: str) -> Tenant:
        """Suspend a tenant account"""
        try:
            tenant = await self.tenant_repo.get_by_id(tenant_id)
            if not tenant:
                raise ValueError(f"Tenant {tenant_id} not found")
            
            tenant.status = TenantStatus.SUSPENDED
            tenant.metadata['suspension_reason'] = reason
            tenant.metadata['suspended_at'] = datetime.utcnow().isoformat()
            
            updated_tenant = await self.tenant_repo.update(tenant)
            
            logger.warning(f"Suspended tenant {tenant_id}: {reason}")
            return updated_tenant
            
        except Exception as e:
            logger.error(f"Error suspending tenant {tenant_id}: {e}")
            raise
    
    async def reactivate_tenant(self, tenant_id: UUID) -> Tenant:
        """Reactivate a suspended tenant"""
        try:
            tenant = await self.tenant_repo.get_by_id(tenant_id)
            if not tenant:
                raise ValueError(f"Tenant {tenant_id} not found")
            
            if tenant.status != TenantStatus.SUSPENDED:
                raise ValueError(f"Tenant {tenant_id} is not suspended")
            
            tenant.status = TenantStatus.ACTIVE
            tenant.metadata['reactivated_at'] = datetime.utcnow().isoformat()
            
            updated_tenant = await self.tenant_repo.update(tenant)
            
            logger.info(f"Reactivated tenant {tenant_id}")
            return updated_tenant
            
        except Exception as e:
            logger.error(f"Error reactivating tenant {tenant_id}: {e}")
            raise
    
    async def list_tenants(
        self,
        status: Optional[TenantStatus] = None,
        subscription_tier: Optional[SubscriptionTier] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Tenant]:
        """List tenants with optional filters"""
        return await self.tenant_repo.list(
            status=status,
            subscription_tier=subscription_tier,
            limit=limit,
            offset=offset
        )
    
    async def can_add_store(self, tenant_id: UUID) -> bool:
        """Check if tenant can add more stores"""
        try:
            tenant = await self.tenant_repo.get_by_id(tenant_id)
            if not tenant:
                return False
            
            current_stores = await self.tenant_repo.count_stores(tenant_id)
            return tenant.can_add_store(current_stores)
            
        except Exception as e:
            logger.error(f"Error checking store limit for tenant {tenant_id}: {e}")
            return False
    
    def _get_store_limit(self, tier: SubscriptionTier) -> Optional[int]:
        """Get store limit for subscription tier"""
        limits = {
            SubscriptionTier.COMMUNITY_AND_NEW_BUSINESS: 1,
            SubscriptionTier.SMALL_BUSINESS: 5,
            SubscriptionTier.PROFESSIONAL_AND_GROWING_BUSINESS: 12,
            SubscriptionTier.ENTERPRISE: None  # Unlimited
        }
        return limits.get(tier)
    
    def _get_tier_features(self, tier: SubscriptionTier) -> Dict[str, Any]:
        """Get features for subscription tier"""
        features = {
            SubscriptionTier.COMMUNITY_AND_NEW_BUSINESS: {
                "stores": 1,
                "ai_personalities": 1,
                "support": "community",
                "analytics": "basic",
                "api_access": False
            },
            SubscriptionTier.SMALL_BUSINESS: {
                "stores": 5,
                "ai_personalities": 2,
                "support": "email",
                "analytics": "standard",
                "api_access": True
            },
            SubscriptionTier.PROFESSIONAL_AND_GROWING_BUSINESS: {
                "stores": 12,
                "ai_personalities": 3,
                "support": "priority",
                "analytics": "advanced",
                "api_access": True,
                "custom_branding": True
            },
            SubscriptionTier.ENTERPRISE: {
                "stores": "unlimited",
                "ai_personalities": 5,
                "support": "dedicated",
                "analytics": "enterprise",
                "api_access": True,
                "custom_branding": True,
                "sla": True,
                "training": True
            }
        }
        return features.get(tier, {})