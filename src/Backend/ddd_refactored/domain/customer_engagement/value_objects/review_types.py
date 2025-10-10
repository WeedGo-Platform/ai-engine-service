"""
Customer Engagement Value Objects
Following DDD Architecture Document Section 2.12
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from ....shared.domain_base import ValueObject


class ReviewStatus(str, Enum):
    """Review moderation status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"
    HIDDEN = "hidden"


class ReviewSource(str, Enum):
    """Where the review came from"""
    WEBSITE = "website"
    MOBILE_APP = "mobile_app"
    EMAIL = "email"
    THIRD_PARTY = "third_party"


class FlagReason(str, Enum):
    """Reason for flagging review"""
    INAPPROPRIATE = "inappropriate"
    SPAM = "spam"
    FAKE = "fake"
    OFFENSIVE = "offensive"
    OFF_TOPIC = "off_topic"
    DUPLICATE = "duplicate"
    OTHER = "other"


@dataclass(frozen=True)
class StarRating(ValueObject):
    """
    Star rating value object (1-5 stars)
    """
    rating: int

    def __post_init__(self):
        """Validate star rating"""
        if self.rating < 1 or self.rating > 5:
            raise ValueError("Rating must be between 1 and 5 stars")

    def to_decimal(self) -> Decimal:
        """Convert to decimal for calculations"""
        return Decimal(str(self.rating))

    def is_positive(self) -> bool:
        """Check if rating is positive (4-5 stars)"""
        return self.rating >= 4

    def is_negative(self) -> bool:
        """Check if rating is negative (1-2 stars)"""
        return self.rating <= 2

    def is_neutral(self) -> bool:
        """Check if rating is neutral (3 stars)"""
        return self.rating == 3

    def __str__(self) -> str:
        return f"{'★' * self.rating}{'☆' * (5 - self.rating)}"


@dataclass(frozen=True)
class ReviewRatings(ValueObject):
    """
    Detailed product ratings breakdown
    """
    overall: StarRating
    quality: Optional[StarRating] = None
    value: Optional[StarRating] = None
    potency: Optional[StarRating] = None  # Cannabis specific
    flavor: Optional[StarRating] = None  # Cannabis specific

    def get_average_rating(self) -> Decimal:
        """Calculate average of all provided ratings"""
        ratings = [self.overall.to_decimal()]

        if self.quality:
            ratings.append(self.quality.to_decimal())
        if self.value:
            ratings.append(self.value.to_decimal())
        if self.potency:
            ratings.append(self.potency.to_decimal())
        if self.flavor:
            ratings.append(self.flavor.to_decimal())

        return sum(ratings) / Decimal(len(ratings))


@dataclass(frozen=True)
class ReviewerInfo(ValueObject):
    """
    Information about the reviewer
    """
    customer_id: str
    display_name: str

    # Verification
    is_verified_purchaser: bool = False
    purchase_date: Optional[datetime] = None

    # Profile
    total_reviews: int = 0
    helpful_votes_received: int = 0

    # Privacy
    show_full_name: bool = False

    def __post_init__(self):
        """Validate reviewer info"""
        if not self.customer_id:
            raise ValueError("Customer ID is required")

        if not self.display_name:
            raise ValueError("Display name is required")

        if len(self.display_name) > 100:
            raise ValueError("Display name too long (max 100 characters)")

        if self.total_reviews < 0:
            raise ValueError("Total reviews cannot be negative")

        if self.helpful_votes_received < 0:
            raise ValueError("Helpful votes cannot be negative")

    def get_display_name(self) -> str:
        """Get formatted display name"""
        verified_badge = " ✓" if self.is_verified_purchaser else ""
        return f"{self.display_name}{verified_badge}"

    def get_reviewer_badge(self) -> Optional[str]:
        """Get reviewer badge based on activity"""
        if self.total_reviews >= 50:
            return "Top Reviewer"
        elif self.total_reviews >= 20:
            return "Frequent Reviewer"
        elif self.total_reviews >= 10:
            return "Regular Reviewer"
        return None


@dataclass(frozen=True)
class ReviewModeration(ValueObject):
    """
    Review moderation details
    """
    status: ReviewStatus
    moderated_at: Optional[datetime] = None
    moderated_by: Optional[str] = None
    moderation_notes: Optional[str] = None

    # Flagging
    flag_count: int = 0
    flag_reasons: Optional[tuple[FlagReason, ...]] = None

    def __post_init__(self):
        """Validate moderation"""
        if self.flag_count < 0:
            raise ValueError("Flag count cannot be negative")

        if self.status in [ReviewStatus.APPROVED, ReviewStatus.REJECTED]:
            if not self.moderated_at:
                raise ValueError(f"{self.status} reviews must have moderation timestamp")

    def is_flagged(self) -> bool:
        """Check if review has been flagged"""
        return self.flag_count > 0 or self.status == ReviewStatus.FLAGGED

    def needs_moderation(self) -> bool:
        """Check if review needs moderation"""
        return self.status in [ReviewStatus.PENDING, ReviewStatus.FLAGGED]


@dataclass(frozen=True)
class ReviewStatistics(ValueObject):
    """
    Aggregate review statistics for a product
    """
    total_reviews: int
    average_rating: Decimal

    # Rating distribution
    five_star_count: int = 0
    four_star_count: int = 0
    three_star_count: int = 0
    two_star_count: int = 0
    one_star_count: int = 0

    # Engagement
    total_helpful_votes: int = 0
    verified_purchase_count: int = 0

    def __post_init__(self):
        """Validate statistics"""
        if self.total_reviews < 0:
            raise ValueError("Total reviews cannot be negative")

        if self.average_rating < 0 or self.average_rating > 5:
            raise ValueError("Average rating must be between 0 and 5")

        # Verify counts add up
        total_counted = (
            self.five_star_count +
            self.four_star_count +
            self.three_star_count +
            self.two_star_count +
            self.one_star_count
        )

        if total_counted != self.total_reviews:
            raise ValueError("Rating distribution counts must equal total reviews")

    def get_rating_percentage(self, stars: int) -> Decimal:
        """Get percentage of reviews for given star rating"""
        if self.total_reviews == 0:
            return Decimal("0")

        count_map = {
            5: self.five_star_count,
            4: self.four_star_count,
            3: self.three_star_count,
            2: self.two_star_count,
            1: self.one_star_count
        }

        count = count_map.get(stars, 0)
        return (Decimal(count) / Decimal(self.total_reviews)) * Decimal("100")

    def get_positive_percentage(self) -> Decimal:
        """Get percentage of positive reviews (4-5 stars)"""
        if self.total_reviews == 0:
            return Decimal("0")

        positive_count = self.five_star_count + self.four_star_count
        return (Decimal(positive_count) / Decimal(self.total_reviews)) * Decimal("100")

    def get_verified_percentage(self) -> Decimal:
        """Get percentage of verified purchase reviews"""
        if self.total_reviews == 0:
            return Decimal("0")

        return (Decimal(self.verified_purchase_count) / Decimal(self.total_reviews)) * Decimal("100")


@dataclass(frozen=True)
class ReviewResponse(ValueObject):
    """
    Store's response to a review
    """
    response_text: str
    responder_name: str
    responder_role: str  # "Store Manager", "Owner", etc.
    responded_at: datetime

    def __post_init__(self):
        """Validate review response"""
        if not self.response_text:
            raise ValueError("Response text is required")

        if len(self.response_text) > 2000:
            raise ValueError("Response text too long (max 2000 characters)")

        if not self.responder_name:
            raise ValueError("Responder name is required")

        if not self.responder_role:
            raise ValueError("Responder role is required")

    def get_display_header(self) -> str:
        """Get formatted response header"""
        return f"Response from {self.responder_name} ({self.responder_role})"
