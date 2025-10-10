"""
Customer Engagement V2 API

DDD-powered product review and rating management using the Customer Engagement bounded context.

Features:
- Product reviews with 5-star ratings and detailed breakdowns
- Review moderation workflow (pending → approved/rejected/flagged → published)
- Helpful vote tracking and engagement metrics
- Store responses to customer reviews
- Reviewer badges and reputation system
- Cannabis-specific ratings (potency, flavor)
- Photo and video attachments
- Review editing within 7-day window
- Aggregate review statistics and distribution
- Domain event tracking for audit trails
"""

from .customer_engagement_endpoints import router

__all__ = ["router"]
