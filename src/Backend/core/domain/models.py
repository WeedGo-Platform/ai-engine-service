"""
Domain Models for Multi-Tenancy
Following Domain-Driven Design (DDD) principles
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from enum import Enum


# =====================================================
# ENUMS
# =====================================================

class TenantStatus(str, Enum):
    """Tenant account status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    TRIAL = "trial"


class SubscriptionTier(str, Enum):
    """Subscription tier levels"""
    COMMUNITY = "community"
    BASIC = "basic"
    SMALL_BUSINESS = "small_business"
    ENTERPRISE = "enterprise"


class StoreStatus(str, Enum):
    """Store operational status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class ProvinceType(str, Enum):
    """Canadian jurisdiction types"""
    PROVINCE = "province"
    TERRITORY = "territory"


class TenantRole(str, Enum):
    """Tenant-level user roles"""
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"


class StoreRole(str, Enum):
    """Store-level user roles"""
    MANAGER = "manager"
    SUPERVISOR = "supervisor"
    STAFF = "staff"
    CASHIER = "cashier"


class AgentType(str, Enum):
    """AI agent types"""
    BUDTENDER = "budtender"
    SUPPORT = "support"
    ANALYTICS = "analytics"
    INVENTORY = "inventory"


class ComplianceStatus(str, Enum):
    """Compliance status types"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING = "pending"


class BillingCycle(str, Enum):
    """Billing cycle options"""
    MONTHLY = "monthly"
    ANNUAL = "annual"


# =====================================================
# VALUE OBJECTS
# =====================================================

@dataclass(frozen=True)
class Address:
    """Address value object"""
    street: str
    city: str
    province: str
    postal_code: str
    country: str = "Canada"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "street": self.street,
            "city": self.city,
            "province": self.province,
            "postal_code": self.postal_code,
            "country": self.country
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Address':
        return cls(
            street=data.get("street", ""),
            city=data.get("city", ""),
            province=data.get("province", ""),
            postal_code=data.get("postal_code", ""),
            country=data.get("country", "Canada")
        )


@dataclass(frozen=True)
class GeoLocation:
    """Geographic location value object"""
    latitude: Decimal
    longitude: Decimal
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "latitude": float(self.latitude),
            "longitude": float(self.longitude)
        }


@dataclass(frozen=True)
class TaxInfo:
    """Tax information value object"""
    rate: Decimal
    cannabis_tax_rate: Optional[Decimal] = None
    
    @property
    def total_rate(self) -> Decimal:
        if self.cannabis_tax_rate:
            return self.rate + self.cannabis_tax_rate
        return self.rate


# =====================================================
# ENTITIES
# =====================================================

@dataclass
class ProvinceTerritory:
    """Province or Territory entity"""
    id: UUID = field(default_factory=uuid4)
    code: str = ""
    name: str = ""
    type: ProvinceType = ProvinceType.PROVINCE
    tax_rate: Decimal = Decimal("13.00")
    cannabis_tax_rate: Optional[Decimal] = None
    min_age: int = 19
    regulatory_body: Optional[str] = None
    license_prefix: Optional[str] = None
    delivery_allowed: bool = True
    pickup_allowed: bool = True
    settings: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Tenant:
    """Tenant aggregate root"""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    code: str = ""
    company_name: Optional[str] = None
    business_number: Optional[str] = None
    gst_hst_number: Optional[str] = None
    address: Optional[Address] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    status: TenantStatus = TenantStatus.ACTIVE
    subscription_tier: SubscriptionTier = SubscriptionTier.COMMUNITY
    max_stores: int = 1
    billing_info: Dict[str, Any] = field(default_factory=dict)
    payment_provider_settings: Dict[str, Any] = field(default_factory=dict)
    currency: str = "CAD"
    settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def can_add_store(self, current_store_count: int) -> bool:
        """Check if tenant can add more stores based on subscription"""
        if self.subscription_tier == SubscriptionTier.ENTERPRISE:
            return True  # Unlimited stores
        return current_store_count < self.max_stores
    
    def get_store_limit(self) -> Optional[int]:
        """Get store limit based on subscription tier"""
        limits = {
            SubscriptionTier.COMMUNITY: 1,
            SubscriptionTier.BASIC: 5,
            SubscriptionTier.SMALL_BUSINESS: 12,
            SubscriptionTier.ENTERPRISE: None  # Unlimited
        }
        return limits.get(self.subscription_tier)
    
    def get_ai_personality_limit(self) -> int:
        """Get AI personality limit per store based on subscription"""
        limits = {
            SubscriptionTier.COMMUNITY: 1,
            SubscriptionTier.BASIC: 2,
            SubscriptionTier.SMALL_BUSINESS: 3,
            SubscriptionTier.ENTERPRISE: 5
        }
        return limits.get(self.subscription_tier, 1)


@dataclass
class Store:
    """Store entity"""
    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    province_territory_id: UUID = field(default_factory=uuid4)
    store_code: str = ""
    name: str = ""
    address: Optional[Address] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    hours: Dict[str, Any] = field(default_factory=dict)
    timezone: str = "America/Toronto"
    license_number: Optional[str] = None
    license_expiry: Optional[date] = None
    tax_rate: Decimal = Decimal("13.00")
    delivery_radius_km: int = 10
    delivery_enabled: bool = True
    pickup_enabled: bool = True
    kiosk_enabled: bool = False
    pos_enabled: bool = True
    ecommerce_enabled: bool = True
    status: StoreStatus = StoreStatus.ACTIVE
    settings: Dict[str, Any] = field(default_factory=dict)
    pos_integration: Dict[str, Any] = field(default_factory=dict)
    pos_payment_terminal_settings: Dict[str, Any] = field(default_factory=dict)
    seo_config: Dict[str, Any] = field(default_factory=dict)
    location: Optional[GeoLocation] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def is_operational(self) -> bool:
        """Check if store is operational"""
        return self.status == StoreStatus.ACTIVE
    
    def is_license_valid(self) -> bool:
        """Check if store license is valid"""
        if not self.license_expiry:
            return False
        return self.license_expiry > date.today()


@dataclass
class TenantUser:
    """Tenant user association"""
    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    role: TenantRole = TenantRole.MANAGER
    permissions: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        if self.role == TenantRole.OWNER:
            return True  # Owners have all permissions
        return self.permissions.get(permission, False)


@dataclass
class StoreUser:
    """Store user association"""
    id: UUID = field(default_factory=uuid4)
    store_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    role: StoreRole = StoreRole.STAFF
    cannsell_certification: Optional[str] = None
    certification_expiry: Optional[date] = None
    permissions: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def is_certified(self) -> bool:
        """Check if user has valid CannSell certification"""
        if not self.cannsell_certification or not self.certification_expiry:
            return False
        return self.certification_expiry > date.today()
    
    def can_sell(self) -> bool:
        """Check if user can make sales"""
        return self.is_certified() and self.role in [
            StoreRole.MANAGER, 
            StoreRole.SUPERVISOR, 
            StoreRole.STAFF
        ]


@dataclass
class TenantSubscription:
    """Tenant subscription entity"""
    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    tier: SubscriptionTier = SubscriptionTier.COMMUNITY
    store_limit: Optional[int] = 1
    ai_personalities_per_store: int = 1
    billing_cycle: Optional[BillingCycle] = None
    price_cad: Decimal = Decimal("0.00")
    features: Dict[str, Any] = field(default_factory=dict)
    start_date: date = field(default_factory=date.today)
    end_date: Optional[date] = None
    next_billing_date: Optional[date] = None
    trial_ends_at: Optional[datetime] = None
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def is_active(self) -> bool:
        """Check if subscription is active"""
        return self.status == "active"
    
    def is_trial(self) -> bool:
        """Check if subscription is in trial period"""
        return self.status == "trial" and self.trial_ends_at and self.trial_ends_at > datetime.utcnow()
    
    def get_monthly_price(self) -> Decimal:
        """Get monthly price based on tier"""
        prices = {
            SubscriptionTier.COMMUNITY: Decimal("0.00"),
            SubscriptionTier.BASIC: Decimal("99.00"),
            SubscriptionTier.SMALL_BUSINESS: Decimal("149.00"),
            SubscriptionTier.ENTERPRISE: Decimal("299.00")
        }
        return prices.get(self.tier, Decimal("0.00"))


@dataclass
class AIPersonality:
    """AI Personality entity"""
    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    store_id: Optional[UUID] = None
    name: str = ""
    personality_type: Optional[str] = None
    avatar_url: Optional[str] = None
    voice_config: Dict[str, Any] = field(default_factory=dict)
    traits: Dict[str, Any] = field(default_factory=dict)
    greeting_message: Optional[str] = None
    is_active: bool = True
    is_default: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class StoreAIAgent:
    """Store AI Agent entity"""
    id: UUID = field(default_factory=uuid4)
    store_id: UUID = field(default_factory=uuid4)
    agent_type: AgentType = AgentType.BUDTENDER
    personality_id: Optional[UUID] = None
    is_active: bool = True
    settings: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class StoreCompliance:
    """Store compliance tracking entity"""
    id: UUID = field(default_factory=uuid4)
    store_id: UUID = field(default_factory=uuid4)
    compliance_type: str = ""
    status: ComplianceStatus = ComplianceStatus.PENDING
    last_inspection: Optional[date] = None
    next_inspection: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def is_compliant(self) -> bool:
        """Check if store is compliant"""
        return self.status == ComplianceStatus.COMPLIANT
    
    def needs_inspection(self) -> bool:
        """Check if inspection is due"""
        if not self.next_inspection:
            return True
        return self.next_inspection <= date.today()