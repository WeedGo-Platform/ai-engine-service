"""
Store Entity
Following DDD Architecture Document Section 2.1
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from enum import Enum

from ....shared.domain_base import Entity, BusinessRuleViolation, DomainEvent
from ....shared.value_objects import Address, GeoLocation


class StoreStatus(str, Enum):
    """Store operational status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


# Domain Events
class StoreCreated(DomainEvent):
    def __init__(self, store_id: UUID, tenant_id: UUID, name: str, store_code: str):
        super().__init__(store_id)
        self.tenant_id = tenant_id
        self.name = name
        self.store_code = store_code

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'tenant_id': str(self.tenant_id),
            'name': self.name,
            'store_code': self.store_code
        })
        return data


class StoreStatusChanged(DomainEvent):
    def __init__(self, store_id: UUID, old_status: str, new_status: str):
        super().__init__(store_id)
        self.old_status = old_status
        self.new_status = new_status

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'old_status': self.old_status,
            'new_status': self.new_status
        })
        return data


class StoreLicenseExpiring(DomainEvent):
    def __init__(self, store_id: UUID, license_number: str, expiry_date: date):
        super().__init__(store_id)
        self.license_number = license_number
        self.expiry_date = expiry_date

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'license_number': self.license_number,
            'expiry_date': self.expiry_date.isoformat()
        })
        return data


@dataclass
class Store(Entity):
    """
    Store Entity
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.1
    """
    tenant_id: UUID = field(default_factory=uuid4)
    province_territory_id: UUID = field(default_factory=uuid4)
    store_code: str = ""  # Unique store identifier
    name: str = ""
    address: Optional[Address] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    hours: Dict[str, Any] = field(default_factory=dict)  # Operating hours
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

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        province_territory_id: UUID,
        store_code: str,
        name: str,
        address: Optional[Address] = None,
        license_number: Optional[str] = None,
        tax_rate: Decimal = Decimal("13.00")
    ) -> 'Store':
        """Factory method to create a new store"""
        store = cls(
            tenant_id=tenant_id,
            province_territory_id=province_territory_id,
            store_code=store_code,
            name=name,
            address=address,
            license_number=license_number,
            tax_rate=tax_rate
        )

        # Raise domain event
        store.add_domain_event(StoreCreated(
            store_id=store.id,
            tenant_id=tenant_id,
            name=name,
            store_code=store_code
        ))

        return store

    def is_operational(self) -> bool:
        """Check if store is operational"""
        return self.status == StoreStatus.ACTIVE and self.is_license_valid()

    def is_license_valid(self) -> bool:
        """Check if store license is valid"""
        if not self.license_expiry:
            return False
        return self.license_expiry > date.today()

    def is_license_expiring_soon(self, days: int = 30) -> bool:
        """Check if license is expiring within specified days"""
        if not self.license_expiry:
            return False

        days_until_expiry = (self.license_expiry - date.today()).days

        if days_until_expiry <= days:
            # Raise domain event if expiring soon
            self.add_domain_event(StoreLicenseExpiring(
                store_id=self.id,
                license_number=self.license_number or "",
                expiry_date=self.license_expiry
            ))
            return True

        return False

    def update_license(self, license_number: str, license_expiry: date):
        """Update store license information"""
        if license_expiry <= date.today():
            raise BusinessRuleViolation("License expiry date must be in the future")

        self.license_number = license_number
        self.license_expiry = license_expiry
        self.mark_as_modified()

    def activate(self):
        """Activate the store"""
        if self.status == StoreStatus.ACTIVE:
            raise BusinessRuleViolation("Store is already active")

        if not self.is_license_valid():
            raise BusinessRuleViolation("Cannot activate store with invalid license")

        old_status = self.status
        self.status = StoreStatus.ACTIVE
        self.mark_as_modified()

        self.add_domain_event(StoreStatusChanged(
            store_id=self.id,
            old_status=old_status.value,
            new_status=self.status.value
        ))

    def deactivate(self, reason: Optional[str] = None):
        """Deactivate the store"""
        if self.status == StoreStatus.INACTIVE:
            raise BusinessRuleViolation("Store is already inactive")

        old_status = self.status
        self.status = StoreStatus.INACTIVE
        self.mark_as_modified()

        if reason:
            self.settings['deactivation_reason'] = reason
            self.settings['deactivation_date'] = datetime.utcnow().isoformat()

        self.add_domain_event(StoreStatusChanged(
            store_id=self.id,
            old_status=old_status.value,
            new_status=self.status.value
        ))

    def suspend(self, reason: str):
        """Suspend the store"""
        if self.status == StoreStatus.SUSPENDED:
            raise BusinessRuleViolation("Store is already suspended")

        old_status = self.status
        self.status = StoreStatus.SUSPENDED
        self.mark_as_modified()

        self.settings['suspension_reason'] = reason
        self.settings['suspension_date'] = datetime.utcnow().isoformat()

        self.add_domain_event(StoreStatusChanged(
            store_id=self.id,
            old_status=old_status.value,
            new_status=self.status.value
        ))

    def update_operating_hours(self, hours: Dict[str, Any]):
        """Update store operating hours"""
        # Expected format: {"monday": {"open": "09:00", "close": "21:00"}, ...}
        valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

        for day in hours:
            if day.lower() not in valid_days:
                raise BusinessRuleViolation(f"Invalid day: {day}")

        self.hours = hours
        self.mark_as_modified()

    def update_delivery_settings(
        self,
        delivery_enabled: Optional[bool] = None,
        delivery_radius_km: Optional[int] = None
    ):
        """Update delivery settings"""
        if delivery_enabled is not None:
            self.delivery_enabled = delivery_enabled

        if delivery_radius_km is not None:
            if delivery_radius_km <= 0:
                raise BusinessRuleViolation("Delivery radius must be positive")
            self.delivery_radius_km = delivery_radius_km

        self.mark_as_modified()

    def update_channel_settings(
        self,
        pickup_enabled: Optional[bool] = None,
        kiosk_enabled: Optional[bool] = None,
        pos_enabled: Optional[bool] = None,
        ecommerce_enabled: Optional[bool] = None
    ):
        """Update sales channel settings"""
        if pickup_enabled is not None:
            self.pickup_enabled = pickup_enabled

        if kiosk_enabled is not None:
            self.kiosk_enabled = kiosk_enabled

        if pos_enabled is not None:
            self.pos_enabled = pos_enabled

        if ecommerce_enabled is not None:
            self.ecommerce_enabled = ecommerce_enabled

        # Ensure at least one channel is enabled
        if not any([
            self.pickup_enabled,
            self.delivery_enabled,
            self.kiosk_enabled,
            self.pos_enabled,
            self.ecommerce_enabled
        ]):
            raise BusinessRuleViolation("At least one sales channel must be enabled")

        self.mark_as_modified()

    def configure_pos_integration(self, provider: str, settings: Dict[str, Any]):
        """Configure POS integration settings"""
        self.pos_integration = {
            'provider': provider,
            'settings': settings,
            'configured_at': datetime.utcnow().isoformat()
        }
        self.mark_as_modified()

    def configure_payment_terminal(self, settings: Dict[str, Any]):
        """Configure payment terminal settings"""
        self.pos_payment_terminal_settings = settings
        self.mark_as_modified()

    def update_seo_config(self, seo_config: Dict[str, Any]):
        """Update SEO configuration"""
        self.seo_config.update(seo_config)
        self.mark_as_modified()

    def update_location(self, location: GeoLocation):
        """Update store geographic location"""
        self.location = location
        self.mark_as_modified()

    def can_deliver_to_location(self, customer_location: GeoLocation) -> bool:
        """Check if store can deliver to a specific location"""
        if not self.delivery_enabled or not self.location:
            return False

        distance = self.location.distance_to(customer_location)
        return float(distance) <= self.delivery_radius_km

    def validate(self) -> List[str]:
        """Validate store data"""
        errors = []

        if not self.name:
            errors.append("Store name is required")

        if not self.store_code:
            errors.append("Store code is required")

        if not self.tenant_id:
            errors.append("Tenant ID is required")

        if not self.province_territory_id:
            errors.append("Province/Territory ID is required")

        if self.tax_rate < 0 or self.tax_rate > 100:
            errors.append("Tax rate must be between 0 and 100")

        if self.delivery_radius_km < 0:
            errors.append("Delivery radius cannot be negative")

        return errors