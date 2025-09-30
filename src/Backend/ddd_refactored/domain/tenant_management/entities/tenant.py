"""
Tenant Aggregate Root
Following DDD Architecture Document Section 2.1
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from enum import Enum

from ....shared.domain_base import AggregateRoot, BusinessRuleViolation, DomainEvent
from ....shared.value_objects import Address, ContactInfo


class TenantStatus(str, Enum):
    """Tenant account status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    TRIAL = "trial"


class SubscriptionTier(str, Enum):
    """Subscription tier levels"""
    COMMUNITY_AND_NEW_BUSINESS = "community_and_new_business"
    SMALL_BUSINESS = "small_business"
    PROFESSIONAL_AND_GROWING_BUSINESS = "professional_and_growing_business"
    ENTERPRISE = "enterprise"


class BillingCycle(str, Enum):
    """Billing cycle options"""
    MONTHLY = "monthly"
    ANNUAL = "annual"


# Domain Events
class TenantCreated(DomainEvent):
    def __init__(self, tenant_id: UUID, name: str, code: str, subscription_tier: str):
        super().__init__(tenant_id)
        self.name = name
        self.code = code
        self.subscription_tier = subscription_tier

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'name': self.name,
            'code': self.code,
            'subscription_tier': self.subscription_tier
        })
        return data


class TenantStatusChanged(DomainEvent):
    def __init__(self, tenant_id: UUID, old_status: str, new_status: str):
        super().__init__(tenant_id)
        self.old_status = old_status
        self.new_status = new_status

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'old_status': self.old_status,
            'new_status': self.new_status
        })
        return data


class SubscriptionUpgraded(DomainEvent):
    def __init__(self, tenant_id: UUID, old_tier: str, new_tier: str):
        super().__init__(tenant_id)
        self.old_tier = old_tier
        self.new_tier = new_tier

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'old_tier': self.old_tier,
            'new_tier': self.new_tier
        })
        return data


@dataclass
class Tenant(AggregateRoot):
    """
    Tenant aggregate root
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.1
    """
    name: str = ""
    code: str = ""  # Unique tenant code
    company_name: Optional[str] = None
    business_number: Optional[str] = None
    gst_hst_number: Optional[str] = None
    address: Optional[Address] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    status: TenantStatus = TenantStatus.ACTIVE
    subscription_tier: SubscriptionTier = SubscriptionTier.COMMUNITY_AND_NEW_BUSINESS
    max_stores: int = 1
    billing_info: Dict[str, Any] = field(default_factory=dict)
    payment_provider_settings: Dict[str, Any] = field(default_factory=dict)
    currency: str = "CAD"
    settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        name: str,
        code: str,
        company_name: Optional[str] = None,
        contact_email: Optional[str] = None,
        subscription_tier: SubscriptionTier = SubscriptionTier.COMMUNITY_AND_NEW_BUSINESS
    ) -> 'Tenant':
        """Factory method to create a new tenant"""
        tenant = cls(
            name=name,
            code=code,
            company_name=company_name,
            contact_email=contact_email,
            subscription_tier=subscription_tier,
            max_stores=cls._get_store_limit(subscription_tier)
        )

        # Raise domain event
        tenant.add_domain_event(TenantCreated(
            tenant_id=tenant.id,
            name=name,
            code=code,
            subscription_tier=subscription_tier.value
        ))

        return tenant

    def can_add_store(self, current_store_count: int) -> bool:
        """Check if tenant can add more stores based on subscription"""
        if self.subscription_tier == SubscriptionTier.ENTERPRISE:
            return True  # Unlimited stores
        return current_store_count < self.max_stores

    def get_store_limit(self) -> Optional[int]:
        """Get store limit based on subscription tier"""
        return self._get_store_limit(self.subscription_tier)

    @staticmethod
    def _get_store_limit(tier: SubscriptionTier) -> Optional[int]:
        """Get store limit for a given subscription tier"""
        limits = {
            SubscriptionTier.COMMUNITY_AND_NEW_BUSINESS: 1,
            SubscriptionTier.SMALL_BUSINESS: 5,
            SubscriptionTier.PROFESSIONAL_AND_GROWING_BUSINESS: 12,
            SubscriptionTier.ENTERPRISE: None  # Unlimited
        }
        return limits.get(tier)

    def get_ai_personality_limit(self) -> int:
        """Get AI personality limit per store based on subscription"""
        limits = {
            SubscriptionTier.COMMUNITY_AND_NEW_BUSINESS: 1,
            SubscriptionTier.SMALL_BUSINESS: 2,
            SubscriptionTier.PROFESSIONAL_AND_GROWING_BUSINESS: 3,
            SubscriptionTier.ENTERPRISE: 5
        }
        return limits.get(self.subscription_tier, 1)

    def suspend(self, reason: Optional[str] = None):
        """Suspend the tenant account"""
        if self.status == TenantStatus.SUSPENDED:
            raise BusinessRuleViolation("Tenant is already suspended")

        old_status = self.status
        self.status = TenantStatus.SUSPENDED
        self.mark_as_modified()

        if reason:
            self.metadata['suspension_reason'] = reason
            self.metadata['suspension_date'] = datetime.utcnow().isoformat()

        self.add_domain_event(TenantStatusChanged(
            tenant_id=self.id,
            old_status=old_status.value,
            new_status=self.status.value
        ))

    def reactivate(self):
        """Reactivate a suspended tenant"""
        if self.status == TenantStatus.ACTIVE:
            raise BusinessRuleViolation("Tenant is already active")

        if self.status == TenantStatus.CANCELLED:
            raise BusinessRuleViolation("Cannot reactivate a cancelled tenant")

        old_status = self.status
        self.status = TenantStatus.ACTIVE
        self.mark_as_modified()

        # Clear suspension metadata
        self.metadata.pop('suspension_reason', None)
        self.metadata.pop('suspension_date', None)

        self.add_domain_event(TenantStatusChanged(
            tenant_id=self.id,
            old_status=old_status.value,
            new_status=self.status.value
        ))

    def upgrade_subscription(self, new_tier: SubscriptionTier):
        """Upgrade subscription tier"""
        if new_tier == self.subscription_tier:
            raise BusinessRuleViolation("Already on this subscription tier")

        # Validate upgrade path
        tier_order = [
            SubscriptionTier.COMMUNITY_AND_NEW_BUSINESS,
            SubscriptionTier.SMALL_BUSINESS,
            SubscriptionTier.PROFESSIONAL_AND_GROWING_BUSINESS,
            SubscriptionTier.ENTERPRISE
        ]

        current_index = tier_order.index(self.subscription_tier)
        new_index = tier_order.index(new_tier)

        if new_index < current_index:
            # This is a downgrade, might have different rules
            pass

        old_tier = self.subscription_tier
        self.subscription_tier = new_tier
        self.max_stores = self._get_store_limit(new_tier) or 999
        self.mark_as_modified()

        self.add_domain_event(SubscriptionUpgraded(
            tenant_id=self.id,
            old_tier=old_tier.value,
            new_tier=new_tier.value
        ))

    def update_contact_info(
        self,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None,
        website: Optional[str] = None
    ):
        """Update tenant contact information"""
        if contact_email:
            self.contact_email = contact_email
        if contact_phone:
            self.contact_phone = contact_phone
        if website:
            self.website = website

        self.mark_as_modified()

    def update_billing_info(self, billing_info: Dict[str, Any]):
        """Update billing information"""
        self.billing_info.update(billing_info)
        self.mark_as_modified()

    def configure_payment_provider(self, provider: str, settings: Dict[str, Any]):
        """Configure payment provider settings"""
        if provider not in self.payment_provider_settings:
            self.payment_provider_settings[provider] = {}

        self.payment_provider_settings[provider].update(settings)
        self.mark_as_modified()

    def is_active(self) -> bool:
        """Check if tenant is active"""
        return self.status == TenantStatus.ACTIVE

    def is_trial(self) -> bool:
        """Check if tenant is in trial period"""
        return self.status == TenantStatus.TRIAL

    def validate(self) -> List[str]:
        """Validate tenant data"""
        errors = []

        if not self.name:
            errors.append("Tenant name is required")

        if not self.code:
            errors.append("Tenant code is required")

        if not self.contact_email:
            errors.append("Contact email is required")

        # Validate email format
        if self.contact_email and '@' not in self.contact_email:
            errors.append("Invalid email format")

        return errors