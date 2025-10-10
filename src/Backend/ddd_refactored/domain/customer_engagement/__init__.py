"""
Customer Engagement Bounded Context

This context handles:
- Product reviews and ratings
- Review moderation and approval
- Helpful votes and engagement
- Verified purchase reviews
- Store responses to reviews
- Review analytics and statistics
"""

from .entities import (
    ProductReview,
    HelpfulVote,
    ReviewSubmitted,
    ReviewApproved,
    ReviewRejected,
    ReviewFlagged,
    ReviewMarkedHelpful,
    StoreResponded
)

from .value_objects import (
    ReviewStatus,
    ReviewSource,
    FlagReason,
    StarRating,
    ReviewRatings,
    ReviewerInfo,
    ReviewModeration,
    ReviewStatistics,
    ReviewResponse
)

__all__ = [
    # Entities
    'ProductReview',
    'HelpfulVote',

    # Events
    'ReviewSubmitted',
    'ReviewApproved',
    'ReviewRejected',
    'ReviewFlagged',
    'ReviewMarkedHelpful',
    'StoreResponded',

    # Value Objects
    'ReviewStatus',
    'ReviewSource',
    'FlagReason',
    'StarRating',
    'ReviewRatings',
    'ReviewerInfo',
    'ReviewModeration',
    'ReviewStatistics',
    'ReviewResponse'
]
