"""
Pricing & Promotions Bounded Context

This context handles:
- Product pricing rules and markup strategies
- Bulk discounts and tiered pricing
- Time-based pricing schedules (happy hour, weekend specials)
- Promotional campaigns and discount codes
- Customer segment targeting
"""

from .entities import (
    PricingRule,
    ProductPrice,
    Promotion,
    DiscountCode,
    PricingRuleCreated,
    PricingRuleActivated,
    PricingRuleDeactivated,
    PriceUpdated,
    PromotionCreated,
    PromotionActivated,
    PromotionDeactivated,
    DiscountCodeGenerated,
    DiscountCodeApplied,
    PromotionExpired
)

from .value_objects import (
    DiscountType,
    PricingStrategy,
    PromotionStatus,
    CustomerSegment,
    ApplicableProducts,
    PricingTier,
    DiscountCondition,
    PriceSchedule,
    BulkDiscountRule
)

__all__ = [
    # Entities
    'PricingRule',
    'ProductPrice',
    'Promotion',
    'DiscountCode',

    # Events
    'PricingRuleCreated',
    'PricingRuleActivated',
    'PricingRuleDeactivated',
    'PriceUpdated',
    'PromotionCreated',
    'PromotionActivated',
    'PromotionDeactivated',
    'DiscountCodeGenerated',
    'DiscountCodeApplied',
    'PromotionExpired',

    # Value Objects
    'DiscountType',
    'PricingStrategy',
    'PromotionStatus',
    'CustomerSegment',
    'ApplicableProducts',
    'PricingTier',
    'DiscountCondition',
    'PriceSchedule',
    'BulkDiscountRule'
]
