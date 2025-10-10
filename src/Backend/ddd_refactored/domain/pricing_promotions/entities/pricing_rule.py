"""
PricingRule Aggregate Root
Following DDD Architecture Document Section 2.8
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from ....shared.domain_base import AggregateRoot, DomainEvent, BusinessRuleViolation
from ..value_objects.pricing_types import (
    PricingStrategy,
    PricingTier,
    BulkDiscountRule,
    PriceSchedule,
    ApplicableProducts
)


# Domain Events
class PricingRuleCreated(DomainEvent):
    pricing_rule_id: UUID
    store_id: UUID
    tenant_id: UUID
    rule_name: str
    strategy: PricingStrategy


class PricingRuleActivated(DomainEvent):
    pricing_rule_id: UUID
    activated_at: datetime


class PricingRuleDeactivated(DomainEvent):
    pricing_rule_id: UUID
    deactivated_at: datetime
    reason: str


class PriceUpdated(DomainEvent):
    pricing_rule_id: UUID
    product_sku: str
    old_price: Decimal
    new_price: Decimal
    updated_at: datetime


@dataclass
class ProductPrice:
    """Product price within pricing rule - entity"""
    product_sku: str
    product_name: str
    cost_price: Decimal
    base_price: Decimal
    markup_percentage: Decimal

    # Optional overrides
    override_price: Optional[Decimal] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None

    # Bulk discounts
    bulk_discount_rule: Optional[BulkDiscountRule] = None

    # Time-based pricing
    price_schedules: List[PriceSchedule] = field(default_factory=list)

    # Metadata
    last_updated: datetime = field(default_factory=datetime.utcnow)
    updated_by: Optional[UUID] = None

    def get_effective_price(self,
                           quantity: Decimal = Decimal("1"),
                           current_time: Optional[datetime] = None) -> Decimal:
        """Calculate effective price considering all rules"""
        current_time = current_time or datetime.utcnow()

        # Start with override or base price
        if self.override_price:
            price = self.override_price
        else:
            price = self.base_price

        # Apply bulk discount if applicable
        if self.bulk_discount_rule and quantity > Decimal("1"):
            price = self.bulk_discount_rule.get_price_for_quantity(quantity)

        # Apply active price schedules
        for schedule in self.price_schedules:
            if schedule.is_active(current_time):
                discount = schedule.calculate_discount(price)
                price = price - discount

        # Enforce min/max constraints
        if self.min_price and price < self.min_price:
            price = self.min_price

        if self.max_price and price > self.max_price:
            price = self.max_price

        return price

    def calculate_markup(self) -> Decimal:
        """Calculate actual markup amount"""
        return self.base_price - self.cost_price

    def get_margin_percentage(self) -> Decimal:
        """Calculate profit margin percentage"""
        if self.base_price == 0:
            return Decimal("0")

        margin = self.calculate_markup()
        return (margin / self.base_price) * Decimal("100")


@dataclass
class PricingRule(AggregateRoot):
    """
    PricingRule Aggregate Root - Product pricing management
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.8
    """
    # Identifiers
    store_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    rule_name: str = ""
    description: Optional[str] = None

    # Strategy
    pricing_strategy: PricingStrategy = PricingStrategy.COST_PLUS

    # Default markup (for COST_PLUS strategy)
    default_markup_percentage: Decimal = Decimal("50")

    # Product scope
    applicable_to: ApplicableProducts = ApplicableProducts.ALL_PRODUCTS
    product_category: Optional[str] = None
    product_type: Optional[str] = None

    # Product prices
    product_prices: List[ProductPrice] = field(default_factory=list)

    # Status
    is_active: bool = True

    # Priority (higher number = higher priority)
    priority: int = 0

    # Validity period
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    activated_at: Optional[datetime] = None
    deactivated_at: Optional[datetime] = None

    # Metadata
    created_by: Optional[UUID] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        store_id: UUID,
        tenant_id: UUID,
        rule_name: str,
        pricing_strategy: PricingStrategy = PricingStrategy.COST_PLUS,
        default_markup_percentage: Decimal = Decimal("50"),
        created_by: Optional[UUID] = None
    ) -> 'PricingRule':
        """Factory method to create new pricing rule"""
        if not rule_name:
            raise BusinessRuleViolation("Rule name is required")

        if default_markup_percentage < 0:
            raise BusinessRuleViolation("Markup percentage cannot be negative")

        pricing_rule = cls(
            store_id=store_id,
            tenant_id=tenant_id,
            rule_name=rule_name,
            pricing_strategy=pricing_strategy,
            default_markup_percentage=default_markup_percentage,
            created_by=created_by,
            is_active=False  # Start inactive
        )

        # Raise creation event
        pricing_rule.add_domain_event(PricingRuleCreated(
            pricing_rule_id=pricing_rule.id,
            store_id=store_id,
            tenant_id=tenant_id,
            rule_name=rule_name,
            strategy=pricing_strategy
        ))

        return pricing_rule

    def add_product_price(
        self,
        product_sku: str,
        product_name: str,
        cost_price: Decimal,
        markup_percentage: Optional[Decimal] = None
    ):
        """Add product price to rule"""
        if not self.is_active:
            raise BusinessRuleViolation("Cannot add prices to inactive rule")

        if cost_price < 0:
            raise BusinessRuleViolation("Cost price cannot be negative")

        # Check if product already exists
        existing = self.get_product_price(product_sku)
        if existing:
            raise BusinessRuleViolation(f"Product {product_sku} already has pricing")

        # Use default markup if not specified
        markup = markup_percentage or self.default_markup_percentage

        # Calculate base price
        base_price = cost_price * (Decimal("1") + markup / Decimal("100"))

        product_price = ProductPrice(
            product_sku=product_sku,
            product_name=product_name,
            cost_price=cost_price,
            base_price=base_price,
            markup_percentage=markup
        )

        self.product_prices.append(product_price)
        self.mark_as_modified()

    def update_product_price(
        self,
        product_sku: str,
        new_cost_price: Optional[Decimal] = None,
        new_markup_percentage: Optional[Decimal] = None,
        override_price: Optional[Decimal] = None,
        updated_by: Optional[UUID] = None
    ):
        """Update product pricing"""
        if not self.is_active:
            raise BusinessRuleViolation("Cannot update prices in inactive rule")

        product_price = self.get_product_price(product_sku)
        if not product_price:
            raise BusinessRuleViolation(f"Product {product_sku} not found")

        old_price = product_price.base_price

        # Update cost price
        if new_cost_price is not None:
            if new_cost_price < 0:
                raise BusinessRuleViolation("Cost price cannot be negative")
            product_price.cost_price = new_cost_price

        # Update markup
        if new_markup_percentage is not None:
            if new_markup_percentage < 0:
                raise BusinessRuleViolation("Markup percentage cannot be negative")
            product_price.markup_percentage = new_markup_percentage

        # Recalculate base price if cost or markup changed
        if new_cost_price is not None or new_markup_percentage is not None:
            product_price.base_price = product_price.cost_price * (
                Decimal("1") + product_price.markup_percentage / Decimal("100")
            )

        # Apply override
        if override_price is not None:
            if override_price < 0:
                raise BusinessRuleViolation("Override price cannot be negative")
            product_price.override_price = override_price

        product_price.last_updated = datetime.utcnow()
        product_price.updated_by = updated_by

        # Raise event
        self.add_domain_event(PriceUpdated(
            pricing_rule_id=self.id,
            product_sku=product_sku,
            old_price=old_price,
            new_price=product_price.base_price,
            updated_at=datetime.utcnow()
        ))

        self.mark_as_modified()

    def add_bulk_discount(
        self,
        product_sku: str,
        tiers: List[PricingTier]
    ):
        """Add bulk discount rule to product"""
        product_price = self.get_product_price(product_sku)
        if not product_price:
            raise BusinessRuleViolation(f"Product {product_sku} not found")

        if not tiers:
            raise BusinessRuleViolation("Must provide at least one pricing tier")

        bulk_rule = BulkDiscountRule(
            product_sku=product_sku,
            base_price=product_price.base_price,
            tiers=tuple(tiers)
        )

        product_price.bulk_discount_rule = bulk_rule
        self.mark_as_modified()

    def add_price_schedule(
        self,
        product_sku: str,
        schedule: PriceSchedule
    ):
        """Add time-based price schedule to product"""
        product_price = self.get_product_price(product_sku)
        if not product_price:
            raise BusinessRuleViolation(f"Product {product_sku} not found")

        product_price.price_schedules.append(schedule)
        self.mark_as_modified()

    def remove_price_schedule(
        self,
        product_sku: str,
        schedule_name: str
    ):
        """Remove price schedule from product"""
        product_price = self.get_product_price(product_sku)
        if not product_price:
            raise BusinessRuleViolation(f"Product {product_sku} not found")

        product_price.price_schedules = [
            s for s in product_price.price_schedules if s.name != schedule_name
        ]
        self.mark_as_modified()

    def activate(self):
        """Activate pricing rule"""
        if self.is_active:
            raise BusinessRuleViolation("Rule is already active")

        if len(self.product_prices) == 0:
            raise BusinessRuleViolation("Cannot activate rule with no products")

        self.is_active = True
        self.activated_at = datetime.utcnow()

        # Raise event
        self.add_domain_event(PricingRuleActivated(
            pricing_rule_id=self.id,
            activated_at=self.activated_at
        ))

        self.mark_as_modified()

    def deactivate(self, reason: str = ""):
        """Deactivate pricing rule"""
        if not self.is_active:
            raise BusinessRuleViolation("Rule is already inactive")

        self.is_active = False
        self.deactivated_at = datetime.utcnow()

        # Raise event
        self.add_domain_event(PricingRuleDeactivated(
            pricing_rule_id=self.id,
            deactivated_at=self.deactivated_at,
            reason=reason
        ))

        self.mark_as_modified()

    def get_product_price(self, product_sku: str) -> Optional[ProductPrice]:
        """Get product price by SKU"""
        return next((p for p in self.product_prices if p.product_sku == product_sku), None)

    def get_effective_price(
        self,
        product_sku: str,
        quantity: Decimal = Decimal("1"),
        current_time: Optional[datetime] = None
    ) -> Optional[Decimal]:
        """Get effective price for product"""
        product_price = self.get_product_price(product_sku)
        if not product_price:
            return None

        return product_price.get_effective_price(quantity, current_time)

    def is_valid_now(self) -> bool:
        """Check if rule is currently valid"""
        if not self.is_active:
            return False

        now = datetime.utcnow()

        if self.valid_from and now < self.valid_from:
            return False

        if self.valid_until and now > self.valid_until:
            return False

        return True

    def validate(self) -> List[str]:
        """Validate pricing rule"""
        errors = []

        if not self.rule_name:
            errors.append("Rule name is required")

        if not self.store_id:
            errors.append("Store ID is required")

        if not self.tenant_id:
            errors.append("Tenant ID is required")

        if self.default_markup_percentage < 0:
            errors.append("Markup percentage cannot be negative")

        if self.valid_from and self.valid_until and self.valid_until <= self.valid_from:
            errors.append("Valid until must be after valid from")

        # Validate product prices
        for product_price in self.product_prices:
            if product_price.cost_price < 0:
                errors.append(f"Product {product_price.product_sku}: Cost price cannot be negative")

            if product_price.base_price < 0:
                errors.append(f"Product {product_price.product_sku}: Base price cannot be negative")

        return errors
