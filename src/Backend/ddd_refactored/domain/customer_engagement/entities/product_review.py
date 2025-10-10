"""
ProductReview Aggregate Root
Following DDD Architecture Document Section 2.12
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from ....shared.domain_base import AggregateRoot, DomainEvent, BusinessRuleViolation
from ..value_objects.review_types import (
    ReviewStatus,
    ReviewSource,
    FlagReason,
    StarRating,
    ReviewRatings,
    ReviewerInfo,
    ReviewModeration,
    ReviewResponse
)


# Domain Events
class ReviewSubmitted(DomainEvent):
    review_id: UUID
    product_sku: str
    customer_id: str
    rating: int


class ReviewApproved(DomainEvent):
    review_id: UUID
    product_sku: str
    approved_at: datetime
    approved_by: str


class ReviewRejected(DomainEvent):
    review_id: UUID
    product_sku: str
    rejected_at: datetime
    rejected_by: str
    reason: str


class ReviewFlagged(DomainEvent):
    review_id: UUID
    product_sku: str
    flagged_by: str
    flag_reason: FlagReason
    flagged_at: datetime


class ReviewMarkedHelpful(DomainEvent):
    review_id: UUID
    product_sku: str
    marked_by: str
    marked_at: datetime


class StoreResponded(DomainEvent):
    review_id: UUID
    product_sku: str
    responder_name: str
    responded_at: datetime


@dataclass
class HelpfulVote:
    """Helpful vote entity within ProductReview aggregate"""
    voter_id: str
    voted_at: datetime = field(default_factory=datetime.utcnow)
    is_helpful: bool = True  # Can also track "not helpful" votes


@dataclass
class ProductReview(AggregateRoot):
    """
    ProductReview Aggregate Root - Customer product reviews
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.12
    """
    # Product reference
    product_sku: str = ""
    product_name: str = ""
    product_type: Optional[str] = None  # cannabis, accessory

    # Reviewer
    reviewer: Optional[ReviewerInfo] = None

    # Ratings
    ratings: Optional[ReviewRatings] = None

    # Review content
    title: str = ""
    review_text: str = ""
    review_source: ReviewSource = ReviewSource.WEBSITE

    # Media
    photo_urls: List[str] = field(default_factory=list)
    video_urls: List[str] = field(default_factory=list)

    # Moderation
    moderation: Optional[ReviewModeration] = None

    # Engagement
    helpful_votes: List[HelpfulVote] = field(default_factory=list)
    not_helpful_votes: List[HelpfulVote] = field(default_factory=list)

    # Store response
    store_response: Optional[ReviewResponse] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        product_sku: str,
        product_name: str,
        reviewer: ReviewerInfo,
        ratings: ReviewRatings,
        title: str,
        review_text: str,
        review_source: ReviewSource = ReviewSource.WEBSITE,
        photo_urls: Optional[List[str]] = None,
        video_urls: Optional[List[str]] = None
    ) -> 'ProductReview':
        """Factory method to create new review"""
        if not product_sku:
            raise BusinessRuleViolation("Product SKU is required")

        if not title:
            raise BusinessRuleViolation("Review title is required")

        if not review_text:
            raise BusinessRuleViolation("Review text is required")

        if len(title) > 200:
            raise BusinessRuleViolation("Review title too long (max 200 characters)")

        if len(review_text) > 5000:
            raise BusinessRuleViolation("Review text too long (max 5000 characters)")

        # Initialize moderation as pending
        moderation = ReviewModeration(
            status=ReviewStatus.PENDING,
            flag_count=0
        )

        review = cls(
            product_sku=product_sku,
            product_name=product_name,
            reviewer=reviewer,
            ratings=ratings,
            title=title,
            review_text=review_text,
            review_source=review_source,
            photo_urls=photo_urls or [],
            video_urls=video_urls or [],
            moderation=moderation
        )

        # Raise creation event
        review.add_domain_event(ReviewSubmitted(
            review_id=review.id,
            product_sku=product_sku,
            customer_id=reviewer.customer_id,
            rating=ratings.overall.rating
        ))

        return review

    def approve(self, approved_by: str, notes: Optional[str] = None):
        """Approve the review"""
        if not self.moderation:
            raise BusinessRuleViolation("Review has no moderation info")

        if self.moderation.status == ReviewStatus.APPROVED:
            raise BusinessRuleViolation("Review is already approved")

        # Update moderation
        self.moderation = ReviewModeration(
            status=ReviewStatus.APPROVED,
            moderated_at=datetime.utcnow(),
            moderated_by=approved_by,
            moderation_notes=notes,
            flag_count=self.moderation.flag_count,
            flag_reasons=self.moderation.flag_reasons
        )

        self.published_at = datetime.utcnow()

        # Raise event
        self.add_domain_event(ReviewApproved(
            review_id=self.id,
            product_sku=self.product_sku,
            approved_at=self.moderation.moderated_at,
            approved_by=approved_by
        ))

        self.mark_as_modified()

    def reject(self, rejected_by: str, reason: str):
        """Reject the review"""
        if not self.moderation:
            raise BusinessRuleViolation("Review has no moderation info")

        if self.moderation.status == ReviewStatus.REJECTED:
            raise BusinessRuleViolation("Review is already rejected")

        if not reason:
            raise BusinessRuleViolation("Rejection reason is required")

        # Update moderation
        self.moderation = ReviewModeration(
            status=ReviewStatus.REJECTED,
            moderated_at=datetime.utcnow(),
            moderated_by=rejected_by,
            moderation_notes=reason,
            flag_count=self.moderation.flag_count,
            flag_reasons=self.moderation.flag_reasons
        )

        # Raise event
        self.add_domain_event(ReviewRejected(
            review_id=self.id,
            product_sku=self.product_sku,
            rejected_at=self.moderation.moderated_at,
            rejected_by=rejected_by,
            reason=reason
        ))

        self.mark_as_modified()

    def flag(self, flagged_by: str, flag_reason: FlagReason):
        """Flag review for moderation"""
        if not self.moderation:
            raise BusinessRuleViolation("Review has no moderation info")

        # Add to flag reasons
        current_reasons = list(self.moderation.flag_reasons or [])
        if flag_reason not in current_reasons:
            current_reasons.append(flag_reason)

        # Update moderation
        self.moderation = ReviewModeration(
            status=ReviewStatus.FLAGGED,
            moderated_at=self.moderation.moderated_at,
            moderated_by=self.moderation.moderated_by,
            moderation_notes=self.moderation.moderation_notes,
            flag_count=self.moderation.flag_count + 1,
            flag_reasons=tuple(current_reasons)
        )

        # Raise event
        self.add_domain_event(ReviewFlagged(
            review_id=self.id,
            product_sku=self.product_sku,
            flagged_by=flagged_by,
            flag_reason=flag_reason,
            flagged_at=datetime.utcnow()
        ))

        self.mark_as_modified()

    def hide(self, hidden_by: str, reason: str):
        """Hide review from public view"""
        if not self.moderation:
            raise BusinessRuleViolation("Review has no moderation info")

        self.moderation = ReviewModeration(
            status=ReviewStatus.HIDDEN,
            moderated_at=datetime.utcnow(),
            moderated_by=hidden_by,
            moderation_notes=reason,
            flag_count=self.moderation.flag_count,
            flag_reasons=self.moderation.flag_reasons
        )

        self.mark_as_modified()

    def mark_helpful(self, voter_id: str):
        """Mark review as helpful"""
        if not self.is_published():
            raise BusinessRuleViolation("Cannot vote on unpublished review")

        # Check if user already voted
        if self.has_voted(voter_id):
            raise BusinessRuleViolation("User has already voted on this review")

        vote = HelpfulVote(
            voter_id=voter_id,
            is_helpful=True
        )

        self.helpful_votes.append(vote)

        # Raise event
        self.add_domain_event(ReviewMarkedHelpful(
            review_id=self.id,
            product_sku=self.product_sku,
            marked_by=voter_id,
            marked_at=vote.voted_at
        ))

        self.mark_as_modified()

    def mark_not_helpful(self, voter_id: str):
        """Mark review as not helpful"""
        if not self.is_published():
            raise BusinessRuleViolation("Cannot vote on unpublished review")

        # Check if user already voted
        if self.has_voted(voter_id):
            raise BusinessRuleViolation("User has already voted on this review")

        vote = HelpfulVote(
            voter_id=voter_id,
            is_helpful=False
        )

        self.not_helpful_votes.append(vote)
        self.mark_as_modified()

    def add_store_response(
        self,
        response_text: str,
        responder_name: str,
        responder_role: str
    ):
        """Add store response to review"""
        if not self.is_published():
            raise BusinessRuleViolation("Cannot respond to unpublished review")

        if self.store_response:
            raise BusinessRuleViolation("Review already has a store response")

        response = ReviewResponse(
            response_text=response_text,
            responder_name=responder_name,
            responder_role=responder_role,
            responded_at=datetime.utcnow()
        )

        self.store_response = response

        # Raise event
        self.add_domain_event(StoreResponded(
            review_id=self.id,
            product_sku=self.product_sku,
            responder_name=responder_name,
            responded_at=response.responded_at
        ))

        self.mark_as_modified()

    def update_review_text(self, new_title: str, new_text: str):
        """Update review text (within allowed timeframe)"""
        if not self.is_published():
            raise BusinessRuleViolation("Cannot update unpublished review")

        # Check if review is too old to edit (e.g., 7 days)
        if self.published_at:
            days_since_publish = (datetime.utcnow() - self.published_at).days
            if days_since_publish > 7:
                raise BusinessRuleViolation("Review is too old to edit")

        if len(new_title) > 200:
            raise BusinessRuleViolation("Review title too long (max 200 characters)")

        if len(new_text) > 5000:
            raise BusinessRuleViolation("Review text too long (max 5000 characters)")

        self.title = new_title
        self.review_text = new_text
        self.updated_at = datetime.utcnow()
        self.mark_as_modified()

    def has_voted(self, voter_id: str) -> bool:
        """Check if user has already voted"""
        helpful = any(v.voter_id == voter_id for v in self.helpful_votes)
        not_helpful = any(v.voter_id == voter_id for v in self.not_helpful_votes)
        return helpful or not_helpful

    def get_helpful_count(self) -> int:
        """Get count of helpful votes"""
        return len(self.helpful_votes)

    def get_not_helpful_count(self) -> int:
        """Get count of not helpful votes"""
        return len(self.not_helpful_votes)

    def get_helpfulness_ratio(self) -> float:
        """Get ratio of helpful votes"""
        total_votes = self.get_helpful_count() + self.get_not_helpful_count()
        if total_votes == 0:
            return 0.0

        return (self.get_helpful_count() / total_votes) * 100

    def is_published(self) -> bool:
        """Check if review is published"""
        return (
            self.moderation and
            self.moderation.status == ReviewStatus.APPROVED and
            self.published_at is not None
        )

    def is_verified_purchase(self) -> bool:
        """Check if review is from verified purchaser"""
        return self.reviewer and self.reviewer.is_verified_purchaser

    def has_media(self) -> bool:
        """Check if review has photos or videos"""
        return len(self.photo_urls) > 0 or len(self.video_urls) > 0

    def validate(self) -> List[str]:
        """Validate product review"""
        errors = []

        if not self.product_sku:
            errors.append("Product SKU is required")

        if not self.reviewer:
            errors.append("Reviewer information is required")

        if not self.ratings:
            errors.append("Ratings are required")

        if not self.title:
            errors.append("Review title is required")

        if not self.review_text:
            errors.append("Review text is required")

        if len(self.title) > 200:
            errors.append("Review title too long (max 200 characters)")

        if len(self.review_text) > 5000:
            errors.append("Review text too long (max 5000 characters)")

        if not self.moderation:
            errors.append("Moderation information is required")

        return errors
