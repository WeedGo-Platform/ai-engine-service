"""
Pricing & Promotions Value Objects
Following DDD Architecture Document Section 2.8
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional
from datetime import datetime

from ....shared.domain_base import ValueObject


class DiscountType(str, Enum):
    """Type of discount"""
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    BOGO = "buy_one_get_one"  # Buy X Get Y free
    BULK_DISCOUNT = "bulk_discount"  # Volume-based discounts
    BUNDLE = "bundle"  # Package deals


class PricingStrategy(str, Enum):
    """Pricing strategy type"""
    COST_PLUS = "cost_plus"  # Cost + markup percentage
    COMPETITIVE = "competitive"  # Market-based pricing
    VALUE_BASED = "value_based"  # Customer perception
    DYNAMIC = "dynamic"  # Time/demand-based
    TIERED = "tiered"  # Volume-based pricing


class PromotionStatus(str, Enum):
    """Promotion lifecycle status"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class CustomerSegment(str, Enum):
    """Customer segment for targeted promotions"""
    ALL = "all"
    NEW_CUSTOMER = "new_customer"
    RETURNING = "returning"
    VIP = "vip"
    MEDICAL = "medical"
    RECREATIONAL = "recreational"


class ApplicableProducts(str, Enum):
    """Which products the pricing/promotion applies to"""
    ALL_PRODUCTS = "all_products"
    SPECIFIC_SKUS = "specific_skus"
    CATEGORY = "category"
    BRAND = "brand"
    PRODUCT_TYPE = "product_type"  # cannabis, accessory, etc.


@dataclass(frozen=True)
class PricingTier(ValueObject):
    """
    Pricing tier for volume/bulk discounts
    Example: Buy 3.5g get 10% off, buy 7g get 15% off
    """
    min_quantity: Decimal
    max_quantity: Optional[Decimal]
    discount_percentage: Optional[Decimal] = None
    fixed_price: Optional[Decimal] = None

    def __post_init__(self):
        """Validate pricing tier"""
        if self.min_quantity < 0:
            raise ValueError("Min quantity cannot be negative")

        if self.max_quantity and self.max_quantity < self.min_quantity:
            raise ValueError("Max quantity must be greater than min quantity")

        # Must have either discount or fixed price
        if not self.discount_percentage and not self.fixed_price:
            raise ValueError("Must specify either discount_percentage or fixed_price")

        if self.discount_percentage and (self.discount_percentage < 0 or self.discount_percentage > 100):
            raise ValueError("Discount percentage must be between 0 and 100")

        if self.fixed_price and self.fixed_price < 0:
            raise ValueError("Fixed price cannot be negative")

    def calculate_price(self, base_price: Decimal) -> Decimal:
        """Calculate price for this tier"""
        if self.fixed_price:
            return self.fixed_price

        if self.discount_percentage:
            discount_amount = base_price * (self.discount_percentage / Decimal("100"))
            return base_price - discount_amount

        return base_price

    def applies_to_quantity(self, quantity: Decimal) -> bool:
        """Check if this tier applies to given quantity"""
        if quantity < self.min_quantity:
            return False

        if self.max_quantity and quantity > self.max_quantity:
            return False

        return True


@dataclass(frozen=True)
class DiscountCondition(ValueObject):
    """
    Condition that must be met for discount to apply
    """
    condition_type: str  # "min_purchase", "specific_products", "customer_segment"

    # Purchase amount conditions
    min_purchase_amount: Optional[Decimal] = None
    max_purchase_amount: Optional[Decimal] = None

    # Quantity conditions
    min_quantity: Optional[int] = None
    max_quantity: Optional[int] = None

    # Product conditions
    required_skus: Optional[list[str]] = None
    required_category: Optional[str] = None

    # Customer conditions
    customer_segment: Optional[CustomerSegment] = None
    first_purchase_only: bool = False

    # Time conditions
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

    def __post_init__(self):
        """Validate discount condition"""
        if self.min_purchase_amount and self.min_purchase_amount < 0:
            raise ValueError("Min purchase amount cannot be negative")

        if self.max_purchase_amount and self.max_purchase_amount < 0:
            raise ValueError("Max purchase amount cannot be negative")

        if (self.min_purchase_amount and self.max_purchase_amount and
            self.max_purchase_amount < self.min_purchase_amount):
            raise ValueError("Max purchase must be greater than min purchase")

    def is_satisfied(self,
                    purchase_amount: Decimal,
                    quantity: int,
                    customer_segment: CustomerSegment,
                    current_time: datetime) -> bool:
        """Check if condition is satisfied"""
        # Check purchase amount
        if self.min_purchase_amount and purchase_amount < self.min_purchase_amount:
            return False

        if self.max_purchase_amount and purchase_amount > self.max_purchase_amount:
            return False

        # Check quantity
        if self.min_quantity and quantity < self.min_quantity:
            return False

        if self.max_quantity and quantity > self.max_quantity:
            return False

        # Check customer segment
        if self.customer_segment and customer_segment != self.customer_segment:
            return False

        # Check time validity
        if self.valid_from and current_time < self.valid_from:
            return False

        if self.valid_until and current_time > self.valid_until:
            return False

        return True


@dataclass(frozen=True)
class PriceSchedule(ValueObject):
    """
    Time-based pricing schedule
    Example: Happy hour pricing, weekend specials
    """
    name: str
    discount_type: DiscountType
    discount_value: Decimal  # Percentage or fixed amount

    # Time range
    start_time: datetime
    end_time: datetime

    # Recurrence
    days_of_week: Optional[list[int]] = None  # 0=Monday, 6=Sunday
    start_hour: Optional[int] = None  # Hour of day (0-23)
    end_hour: Optional[int] = None

    def __post_init__(self):
        """Validate price schedule"""
        if self.end_time <= self.start_time:
            raise ValueError("End time must be after start time")

        if self.discount_value < 0:
            raise ValueError("Discount value cannot be negative")

        if self.discount_type == DiscountType.PERCENTAGE and self.discount_value > 100:
            raise ValueError("Percentage discount cannot exceed 100%")

        if self.start_hour is not None and (self.start_hour < 0 or self.start_hour > 23):
            raise ValueError("Start hour must be between 0 and 23")

        if self.end_hour is not None and (self.end_hour < 0 or self.end_hour > 23):
            raise ValueError("End hour must be between 0 and 23")

    def is_active(self, current_time: datetime) -> bool:
        """Check if schedule is currently active"""
        # Check date range
        if current_time < self.start_time or current_time > self.end_time:
            return False

        # Check day of week
        if self.days_of_week and current_time.weekday() not in self.days_of_week:
            return False

        # Check hour range
        if self.start_hour is not None and current_time.hour < self.start_hour:
            return False

        if self.end_hour is not None and current_time.hour >= self.end_hour:
            return False

        return True

    def calculate_discount(self, base_price: Decimal) -> Decimal:
        """Calculate discount amount"""
        if self.discount_type == DiscountType.PERCENTAGE:
            return base_price * (self.discount_value / Decimal("100"))
        else:  # FIXED_AMOUNT
            return self.discount_value


@dataclass(frozen=True)
class BulkDiscountRule(ValueObject):
    """
    Bulk discount rule with multiple tiers
    Example: Buy 1g at $10, 3.5g at $30 (save $5), 7g at $55 (save $15)
    """
    product_sku: str
    base_price: Decimal
    tiers: tuple[PricingTier, ...]

    def __post_init__(self):
        """Validate bulk discount rule"""
        if self.base_price < 0:
            raise ValueError("Base price cannot be negative")

        if not self.tiers:
            raise ValueError("Must have at least one pricing tier")

        # Validate tiers don't overlap
        sorted_tiers = sorted(self.tiers, key=lambda t: t.min_quantity)
        for i in range(len(sorted_tiers) - 1):
            current = sorted_tiers[i]
            next_tier = sorted_tiers[i + 1]

            if current.max_quantity and next_tier.min_quantity <= current.max_quantity:
                raise ValueError("Pricing tiers cannot overlap")

    def get_price_for_quantity(self, quantity: Decimal) -> Decimal:
        """Get price for given quantity"""
        # Find applicable tier
        for tier in self.tiers:
            if tier.applies_to_quantity(quantity):
                return tier.calculate_price(self.base_price)

        # No tier applies, return base price
        return self.base_price
