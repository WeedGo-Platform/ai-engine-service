"""
Pricing & Promotions V2 API

DDD-powered pricing and promotional campaign management using the Pricing & Promotions bounded context.

Features:
- Dynamic pricing strategies (cost-plus, competitive, value-based, dynamic, tiered)
- Bulk/volume discounts with multi-tier pricing
- Time-based pricing schedules (happy hour, weekend specials)
- Promotional campaigns with discount codes
- BOGO (Buy One Get One) promotions
- Customer segmentation and targeting
- Discount code generation and tracking
- Promotion stacking controls
- Usage limits and analytics
"""

from .pricing_promotions_endpoints import router

__all__ = ["router"]
