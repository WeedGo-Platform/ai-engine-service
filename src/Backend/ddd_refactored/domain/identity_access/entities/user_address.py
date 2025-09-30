"""
UserAddress Entity
Following DDD Architecture Document Section 2.2
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from enum import Enum

from ....shared.domain_base import Entity, BusinessRuleViolation
from ....shared.value_objects import Address, GeoLocation


class AddressType(str, Enum):
    """Types of addresses"""
    BILLING = "billing"
    DELIVERY = "delivery"
    BOTH = "both"


class AddressStatus(str, Enum):
    """Address verification status"""
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    INVALID = "invalid"


@dataclass
class UserAddress(Entity):
    """
    UserAddress Entity - User's saved addresses
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.2
    """
    user_id: UUID = field(default_factory=uuid4)

    # Address Information
    label: str = ""  # e.g., "Home", "Work", "Mom's House"
    address: Optional[Address] = None
    location: Optional[GeoLocation] = None

    # Address Type and Usage
    address_type: AddressType = AddressType.BOTH
    is_default: bool = False

    # Verification
    verification_status: AddressStatus = AddressStatus.UNVERIFIED
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None  # System that verified (e.g., "canada_post", "manual")

    # Delivery Information
    delivery_instructions: Optional[str] = None
    buzzer_code: Optional[str] = None
    safe_drop_enabled: bool = False
    safe_drop_location: Optional[str] = None  # e.g., "Behind planter on porch"

    # Contact for this address
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None

    # Usage Statistics
    times_used: int = 0
    last_used_at: Optional[datetime] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

    @classmethod
    def create(
        cls,
        user_id: UUID,
        label: str,
        address: Address,
        address_type: AddressType = AddressType.BOTH
    ) -> 'UserAddress':
        """Factory method to create a new user address"""
        user_address = cls(
            user_id=user_id,
            label=label,
            address=address,
            address_type=address_type
        )
        return user_address

    def update_address(self, new_address: Address):
        """Update the address"""
        self.address = new_address
        self.verification_status = AddressStatus.UNVERIFIED
        self.verified_at = None
        self.verified_by = None
        self.updated_at = datetime.utcnow()
        self.mark_as_modified()

    def verify(self, verified_by: str = "manual"):
        """Mark address as verified"""
        if self.verification_status == AddressStatus.VERIFIED:
            raise BusinessRuleViolation("Address is already verified")

        self.verification_status = AddressStatus.VERIFIED
        self.verified_at = datetime.utcnow()
        self.verified_by = verified_by
        self.mark_as_modified()

    def mark_invalid(self, reason: Optional[str] = None):
        """Mark address as invalid"""
        self.verification_status = AddressStatus.INVALID
        if reason:
            self.notes = f"Invalid: {reason}"
        self.mark_as_modified()

    def set_as_default(self):
        """Set this as the default address"""
        self.is_default = True
        self.mark_as_modified()

    def unset_default(self):
        """Remove default status"""
        self.is_default = False
        self.mark_as_modified()

    def update_delivery_instructions(
        self,
        instructions: Optional[str] = None,
        buzzer_code: Optional[str] = None,
        safe_drop_enabled: Optional[bool] = None,
        safe_drop_location: Optional[str] = None
    ):
        """Update delivery instructions"""
        if instructions is not None:
            if len(instructions) > 500:
                raise BusinessRuleViolation("Delivery instructions must be 500 characters or less")
            self.delivery_instructions = instructions

        if buzzer_code is not None:
            self.buzzer_code = buzzer_code

        if safe_drop_enabled is not None:
            self.safe_drop_enabled = safe_drop_enabled

        if safe_drop_location is not None:
            if len(safe_drop_location) > 200:
                raise BusinessRuleViolation("Safe drop location must be 200 characters or less")
            self.safe_drop_location = safe_drop_location

        self.mark_as_modified()

    def update_contact(self, name: Optional[str] = None, phone: Optional[str] = None):
        """Update contact information for this address"""
        if name is not None:
            self.contact_name = name
        if phone is not None:
            self.contact_phone = phone
        self.mark_as_modified()

    def record_usage(self):
        """Record that this address was used"""
        self.times_used += 1
        self.last_used_at = datetime.utcnow()
        self.mark_as_modified()

    def update_location(self, location: GeoLocation):
        """Update geographic location"""
        self.location = location
        self.mark_as_modified()

    def is_verified(self) -> bool:
        """Check if address is verified"""
        return self.verification_status == AddressStatus.VERIFIED

    def can_deliver(self) -> bool:
        """Check if this address can be used for delivery"""
        return (
            self.address_type in [AddressType.DELIVERY, AddressType.BOTH] and
            self.verification_status != AddressStatus.INVALID
        )

    def can_bill(self) -> bool:
        """Check if this address can be used for billing"""
        return self.address_type in [AddressType.BILLING, AddressType.BOTH]

    def is_within_delivery_zone(self, store_location: GeoLocation, radius_km: float) -> bool:
        """Check if address is within delivery zone"""
        if not self.location:
            return False

        distance = self.location.distance_to(store_location)
        return float(distance) <= radius_km

    def get_full_address(self) -> str:
        """Get formatted full address"""
        if not self.address:
            return ""

        parts = [
            self.address.street,
            self.address.city,
            self.address.province,
            self.address.postal_code,
            self.address.country
        ]
        return ", ".join(filter(None, parts))

    def validate(self) -> List[str]:
        """Validate user address data"""
        errors = []

        if not self.label:
            errors.append("Address label is required")

        if not self.address:
            errors.append("Address is required")

        if self.delivery_instructions and len(self.delivery_instructions) > 500:
            errors.append("Delivery instructions must be 500 characters or less")

        if self.safe_drop_location and len(self.safe_drop_location) > 200:
            errors.append("Safe drop location must be 200 characters or less")

        if self.contact_phone and not self.contact_phone.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            errors.append("Invalid phone number format")

        return errors