"""
Profile Entity
Following DDD Architecture Document Section 2.2
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from enum import Enum

from ....shared.domain_base import Entity, BusinessRuleViolation
from ....shared.value_objects import Address


class ProfileVisibility(str, Enum):
    """Profile visibility settings"""
    PUBLIC = "public"
    FRIENDS = "friends"
    PRIVATE = "private"


class MedicalCardStatus(str, Enum):
    """Medical card status"""
    NOT_APPLICABLE = "not_applicable"
    PENDING = "pending"
    VERIFIED = "verified"
    EXPIRED = "expired"
    REJECTED = "rejected"


@dataclass
class Profile(Entity):
    """
    Profile Entity - Extended user information
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.2
    """
    user_id: UUID = field(default_factory=uuid4)

    # Profile Information
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    cover_image_url: Optional[str] = None

    # Personal Preferences
    favorite_strains: List[str] = field(default_factory=list)
    preferred_consumption_methods: List[str] = field(default_factory=list)  # flower, edibles, concentrates, etc.
    preferred_effects: List[str] = field(default_factory=list)  # relaxation, creativity, energy, etc.
    allergens: List[str] = field(default_factory=list)

    # Medical Information (optional)
    is_medical_user: bool = False
    medical_card_number: Optional[str] = None
    medical_card_expiry: Optional[date] = None
    medical_card_status: MedicalCardStatus = MedicalCardStatus.NOT_APPLICABLE
    medical_conditions: List[str] = field(default_factory=list)
    prescribing_doctor: Optional[str] = None

    # Cannabis Experience
    experience_level: str = "beginner"  # beginner, intermediate, expert
    tolerance_level: str = "low"  # low, medium, high
    daily_consumption_g: Optional[float] = None

    # Social Features
    visibility: ProfileVisibility = ProfileVisibility.PRIVATE
    allow_messages: bool = True
    allow_friend_requests: bool = True
    show_purchase_history: bool = False
    show_reviews: bool = True

    # Loyalty & Rewards
    loyalty_points: int = 0
    loyalty_tier: str = "bronze"  # bronze, silver, gold, platinum
    lifetime_spend: float = 0.0
    referral_code: Optional[str] = None
    referred_by: Optional[UUID] = None

    # Statistics
    total_orders: int = 0
    total_reviews: int = 0
    average_rating_given: Optional[float] = None
    favorite_store_id: Optional[UUID] = None
    last_order_date: Optional[datetime] = None

    # Preferences
    preferred_delivery_method: str = "delivery"  # delivery, pickup
    preferred_payment_method: str = "credit_card"
    auto_reorder_enabled: bool = False
    auto_reorder_items: List[Dict[str, Any]] = field(default_factory=list)

    # Privacy Settings
    data_sharing_consent: bool = False
    analytics_consent: bool = True
    marketing_consent: bool = False

    # Metadata
    profile_completed_percentage: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, user_id: UUID) -> 'Profile':
        """Factory method to create a new profile"""
        profile = cls(user_id=user_id)
        profile._calculate_completion_percentage()
        return profile

    def update_display_info(
        self,
        display_name: Optional[str] = None,
        bio: Optional[str] = None,
        avatar_url: Optional[str] = None
    ):
        """Update display information"""
        if display_name is not None:
            if len(display_name) > 50:
                raise BusinessRuleViolation("Display name must be 50 characters or less")
            self.display_name = display_name

        if bio is not None:
            if len(bio) > 500:
                raise BusinessRuleViolation("Bio must be 500 characters or less")
            self.bio = bio

        if avatar_url is not None:
            self.avatar_url = avatar_url

        self.last_updated = datetime.utcnow()
        self._calculate_completion_percentage()
        self.mark_as_modified()

    def add_favorite_strain(self, strain: str):
        """Add a favorite strain"""
        if strain not in self.favorite_strains:
            self.favorite_strains.append(strain)
            self.mark_as_modified()

    def remove_favorite_strain(self, strain: str):
        """Remove a favorite strain"""
        if strain in self.favorite_strains:
            self.favorite_strains.remove(strain)
            self.mark_as_modified()

    def update_medical_card(
        self,
        card_number: str,
        expiry_date: date,
        doctor: Optional[str] = None
    ):
        """Update medical card information"""
        if expiry_date <= date.today():
            raise BusinessRuleViolation("Medical card expiry date must be in the future")

        self.is_medical_user = True
        self.medical_card_number = card_number
        self.medical_card_expiry = expiry_date
        self.medical_card_status = MedicalCardStatus.PENDING
        self.prescribing_doctor = doctor
        self.mark_as_modified()

    def verify_medical_card(self):
        """Mark medical card as verified"""
        if not self.medical_card_number:
            raise BusinessRuleViolation("No medical card to verify")

        if self.medical_card_expiry and self.medical_card_expiry <= date.today():
            raise BusinessRuleViolation("Cannot verify expired medical card")

        self.medical_card_status = MedicalCardStatus.VERIFIED
        self.mark_as_modified()

    def add_medical_condition(self, condition: str):
        """Add a medical condition"""
        if not self.is_medical_user:
            raise BusinessRuleViolation("Must be a medical user to add conditions")

        if condition not in self.medical_conditions:
            self.medical_conditions.append(condition)
            self.mark_as_modified()

    def update_experience(
        self,
        experience_level: Optional[str] = None,
        tolerance_level: Optional[str] = None,
        daily_consumption: Optional[float] = None
    ):
        """Update cannabis experience information"""
        valid_experience = ["beginner", "intermediate", "expert"]
        valid_tolerance = ["low", "medium", "high"]

        if experience_level and experience_level in valid_experience:
            self.experience_level = experience_level

        if tolerance_level and tolerance_level in valid_tolerance:
            self.tolerance_level = tolerance_level

        if daily_consumption is not None:
            if daily_consumption < 0 or daily_consumption > 30:
                raise BusinessRuleViolation("Daily consumption must be between 0 and 30 grams")
            self.daily_consumption_g = daily_consumption

        self.mark_as_modified()

    def add_loyalty_points(self, points: int):
        """Add loyalty points"""
        if points <= 0:
            raise BusinessRuleViolation("Points must be positive")

        self.loyalty_points += points
        self._update_loyalty_tier()
        self.mark_as_modified()

    def redeem_loyalty_points(self, points: int):
        """Redeem loyalty points"""
        if points <= 0:
            raise BusinessRuleViolation("Points must be positive")

        if points > self.loyalty_points:
            raise BusinessRuleViolation("Insufficient loyalty points")

        self.loyalty_points -= points
        self.mark_as_modified()

    def _update_loyalty_tier(self):
        """Update loyalty tier based on lifetime spend"""
        if self.lifetime_spend >= 10000:
            self.loyalty_tier = "platinum"
        elif self.lifetime_spend >= 5000:
            self.loyalty_tier = "gold"
        elif self.lifetime_spend >= 1000:
            self.loyalty_tier = "silver"
        else:
            self.loyalty_tier = "bronze"

    def record_purchase(self, amount: float):
        """Record a purchase for statistics"""
        self.total_orders += 1
        self.lifetime_spend += amount
        self.last_order_date = datetime.utcnow()
        self._update_loyalty_tier()
        self.mark_as_modified()

    def update_privacy_settings(
        self,
        visibility: Optional[ProfileVisibility] = None,
        allow_messages: Optional[bool] = None,
        data_sharing: Optional[bool] = None,
        analytics: Optional[bool] = None,
        marketing: Optional[bool] = None
    ):
        """Update privacy settings"""
        if visibility:
            self.visibility = visibility
        if allow_messages is not None:
            self.allow_messages = allow_messages
        if data_sharing is not None:
            self.data_sharing_consent = data_sharing
        if analytics is not None:
            self.analytics_consent = analytics
        if marketing is not None:
            self.marketing_consent = marketing

        self.mark_as_modified()

    def set_auto_reorder(self, items: List[Dict[str, Any]], enabled: bool = True):
        """Set auto-reorder items"""
        self.auto_reorder_enabled = enabled
        self.auto_reorder_items = items
        self.mark_as_modified()

    def _calculate_completion_percentage(self):
        """Calculate profile completion percentage"""
        total_fields = 10  # Number of important fields to complete
        completed = 0

        if self.display_name:
            completed += 1
        if self.bio:
            completed += 1
        if self.avatar_url:
            completed += 1
        if self.favorite_strains:
            completed += 1
        if self.preferred_consumption_methods:
            completed += 1
        if self.preferred_effects:
            completed += 1
        if self.experience_level != "beginner":
            completed += 1
        if self.allergens is not None:
            completed += 1
        if self.preferred_delivery_method:
            completed += 1
        if self.preferred_payment_method:
            completed += 1

        self.profile_completed_percentage = int((completed / total_fields) * 100)

    def is_medical_card_valid(self) -> bool:
        """Check if medical card is valid"""
        if not self.is_medical_user:
            return False

        if self.medical_card_status != MedicalCardStatus.VERIFIED:
            return False

        if self.medical_card_expiry and self.medical_card_expiry <= date.today():
            self.medical_card_status = MedicalCardStatus.EXPIRED
            return False

        return True

    def get_discount_eligibility(self) -> Dict[str, bool]:
        """Get eligibility for various discounts"""
        return {
            'medical': self.is_medical_card_valid(),
            'loyalty': self.loyalty_tier in ['gold', 'platinum'],
            'bulk': self.daily_consumption_g and self.daily_consumption_g > 5,
            'veteran': 'veteran' in self.metadata.get('tags', []),
            'senior': 'senior' in self.metadata.get('tags', []),
            'first_time': self.total_orders == 0
        }

    def validate(self) -> List[str]:
        """Validate profile data"""
        errors = []

        if self.display_name and len(self.display_name) > 50:
            errors.append("Display name must be 50 characters or less")

        if self.bio and len(self.bio) > 500:
            errors.append("Bio must be 500 characters or less")

        if self.daily_consumption_g and (self.daily_consumption_g < 0 or self.daily_consumption_g > 30):
            errors.append("Daily consumption must be between 0 and 30 grams")

        if self.medical_card_expiry and self.medical_card_expiry <= date.today():
            errors.append("Medical card has expired")

        if self.loyalty_points < 0:
            errors.append("Loyalty points cannot be negative")

        return errors