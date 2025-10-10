"""
Promotion Aggregate Root
Following DDD Architecture Document Section 2.8
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from ....shared.domain_base import AggregateRoot, DomainEvent, BusinessRuleViolation
from ..value_objects.pricing_types import (
    DiscountType,
    PromotionStatus,
    CustomerSegment,
    ApplicableProducts,
    DiscountCondition
)


# Domain Events
class PromotionCreated(DomainEvent):
    promotion_id: UUID
    promotion_name: str
    store_id: UUID
    tenant_id: UUID


class PromotionActivated(DomainEvent):
    promotion_id: UUID
    promotion_name: str
    activated_at: datetime


class PromotionDeactivated(DomainEvent):
    promotion_id: UUID
    promotion_name: str
    deactivated_at: datetime


class DiscountCodeGenerated(DomainEvent):
    promotion_id: UUID
    code: str
    max_uses: int


class DiscountCodeApplied(DomainEvent):
    promotion_id: UUID
    code: str
    order_id: UUID
    customer_id: Optional[UUID]
    discount_amount: Decimal
    applied_at: datetime


class PromotionExpired(DomainEvent):
    promotion_id: UUID
    promotion_name: str
    expired_at: datetime


@dataclass
class DiscountCode:
    """Discount code entity within Promotion aggregate"""
    code: str
    max_uses: Optional[int] = None
    current_uses: int = 0
    is_active: bool = True

    # Customer restrictions
    customer_segment: Optional[CustomerSegment] = None
    specific_customer_id: Optional[UUID] = None  # For personalized codes

    # Tracking
    created_at: datetime = field(default_factory=datetime.utcnow)
    first_used_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None

    def can_be_used(self, customer_id: Optional[UUID] = None) -> bool:
        """Check if code can be used"""
        if not self.is_active:
            return False

        # Check max uses
        if self.max_uses and self.current_uses >= self.max_uses:
            return False

        # Check customer restriction
        if self.specific_customer_id and customer_id != self.specific_customer_id:
            return False

        return True

    def record_use(self, customer_id: Optional[UUID] = None):
        """Record code usage"""
        if not self.can_be_used(customer_id):
            raise BusinessRuleViolation(f"Discount code {self.code} cannot be used")

        self.current_uses += 1

        if not self.first_used_at:
            self.first_used_at = datetime.utcnow()

        self.last_used_at = datetime.utcnow()

    def deactivate(self):
        """Deactivate the code"""
        self.is_active = False

    def get_remaining_uses(self) -> Optional[int]:
        """Get remaining uses (None if unlimited)"""
        if not self.max_uses:
            return None

        return max(0, self.max_uses - self.current_uses)


@dataclass
class Promotion(AggregateRoot):
    """
    Promotion Aggregate Root - Marketing promotions and discounts
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.8
    """
    # Identifiers
    store_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    promotion_name: str = ""
    description: Optional[str] = None

    # Status
    status: PromotionStatus = PromotionStatus.DRAFT

    # Discount details
    discount_type: DiscountType = DiscountType.PERCENTAGE
    discount_value: Decimal = Decimal("0")  # Percentage or fixed amount

    # BOGO details (for Buy X Get Y free)
    bogo_buy_quantity: Optional[int] = None
    bogo_get_quantity: Optional[int] = None

    # Applicability
    applicable_to: ApplicableProducts = ApplicableProducts.ALL_PRODUCTS
    product_skus: List[str] = field(default_factory=list)
    product_category: Optional[str] = None
    product_type: Optional[str] = None

    # Conditions
    conditions: List[DiscountCondition] = field(default_factory=list)

    # Customer targeting
    customer_segment: CustomerSegment = CustomerSegment.ALL

    # Usage limits
    max_uses_per_customer: Optional[int] = None
    max_total_uses: Optional[int] = None
    current_total_uses: int = 0

    # Discount codes
    discount_codes: List[DiscountCode] = field(default_factory=list)
    requires_code: bool = False

    # Validity period
    valid_from: datetime = field(default_factory=datetime.utcnow)
    valid_until: Optional[datetime] = None

    # Priority (higher number = higher priority when stacking)
    priority: int = 0
    can_stack: bool = False  # Can be combined with other promotions

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    activated_at: Optional[datetime] = None

    # Metadata
    created_by: Optional[UUID] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        store_id: UUID,
        tenant_id: UUID,
        promotion_name: str,
        discount_type: DiscountType,
        discount_value: Decimal,
        valid_from: datetime,
        valid_until: Optional[datetime] = None,
        created_by: Optional[UUID] = None
    ) -> 'Promotion':
        """Factory method to create new promotion"""
        if not promotion_name:
            raise BusinessRuleViolation("Promotion name is required")

        if discount_value < 0:
            raise BusinessRuleViolation("Discount value cannot be negative")

        if discount_type == DiscountType.PERCENTAGE and discount_value > 100:
            raise BusinessRuleViolation("Percentage discount cannot exceed 100%")

        if valid_until and valid_until <= valid_from:
            raise BusinessRuleViolation("Valid until must be after valid from")

        promotion = cls(
            store_id=store_id,
            tenant_id=tenant_id,
            promotion_name=promotion_name,
            discount_type=discount_type,
            discount_value=discount_value,
            valid_from=valid_from,
            valid_until=valid_until,
            created_by=created_by,
            status=PromotionStatus.DRAFT
        )

        # Raise creation event
        promotion.add_domain_event(PromotionCreated(
            promotion_id=promotion.id,
            promotion_name=promotion_name,
            store_id=store_id,
            tenant_id=tenant_id
        ))

        return promotion

    def add_condition(self, condition: DiscountCondition):
        """Add condition to promotion"""
        if self.status not in [PromotionStatus.DRAFT, PromotionStatus.SCHEDULED]:
            raise BusinessRuleViolation("Cannot add conditions to active promotion")

        self.conditions.append(condition)
        self.mark_as_modified()

    def remove_condition(self, condition_type: str):
        """Remove condition from promotion"""
        if self.status not in [PromotionStatus.DRAFT, PromotionStatus.SCHEDULED]:
            raise BusinessRuleViolation("Cannot remove conditions from active promotion")

        self.conditions = [c for c in self.conditions if c.condition_type != condition_type]
        self.mark_as_modified()

    def generate_discount_code(
        self,
        code: str,
        max_uses: Optional[int] = None,
        customer_segment: Optional[CustomerSegment] = None,
        specific_customer_id: Optional[UUID] = None
    ):
        """Generate a discount code for this promotion"""
        if not code:
            raise BusinessRuleViolation("Discount code is required")

        # Check if code already exists
        if self.get_discount_code(code):
            raise BusinessRuleViolation(f"Discount code {code} already exists")

        discount_code = DiscountCode(
            code=code.upper(),
            max_uses=max_uses,
            customer_segment=customer_segment,
            specific_customer_id=specific_customer_id
        )

        self.discount_codes.append(discount_code)
        self.requires_code = True

        # Raise event
        self.add_domain_event(DiscountCodeGenerated(
            promotion_id=self.id,
            code=code.upper(),
            max_uses=max_uses or 0
        ))

        self.mark_as_modified()

    def apply_discount_code(
        self,
        code: str,
        order_id: UUID,
        customer_id: Optional[UUID] = None
    ):
        """Apply a discount code to an order"""
        if not self.is_active():
            raise BusinessRuleViolation("Promotion is not active")

        discount_code = self.get_discount_code(code)
        if not discount_code:
            raise BusinessRuleViolation(f"Invalid discount code: {code}")

        if not discount_code.can_be_used(customer_id):
            raise BusinessRuleViolation(f"Discount code {code} cannot be used")

        # Record usage
        discount_code.record_use(customer_id)
        self.current_total_uses += 1

        # Raise event
        self.add_domain_event(DiscountCodeApplied(
            promotion_id=self.id,
            code=code,
            order_id=order_id,
            customer_id=customer_id,
            discount_amount=Decimal("0"),  # Calculated by application layer
            applied_at=datetime.utcnow()
        ))

        self.mark_as_modified()

    def calculate_discount(
        self,
        base_amount: Decimal,
        quantity: int = 1
    ) -> Decimal:
        """Calculate discount amount"""
        if self.discount_type == DiscountType.PERCENTAGE:
            return base_amount * (self.discount_value / Decimal("100"))

        elif self.discount_type == DiscountType.FIXED_AMOUNT:
            return min(self.discount_value, base_amount)

        elif self.discount_type == DiscountType.BOGO:
            if not self.bogo_buy_quantity or not self.bogo_get_quantity:
                raise BusinessRuleViolation("BOGO quantities not configured")

            # Calculate how many free items
            qualifying_sets = quantity // self.bogo_buy_quantity
            free_items = qualifying_sets * self.bogo_get_quantity

            # Discount is the value of free items
            unit_price = base_amount / Decimal(quantity) if quantity > 0 else Decimal("0")
            return unit_price * Decimal(free_items)

        return Decimal("0")

    def activate(self):
        """Activate the promotion"""
        if self.status == PromotionStatus.ACTIVE:
            raise BusinessRuleViolation("Promotion is already active")

        if self.status in [PromotionStatus.CANCELLED, PromotionStatus.EXPIRED]:
            raise BusinessRuleViolation(f"Cannot activate {self.status} promotion")

        # Validate before activation
        validation_errors = self.validate()
        if validation_errors:
            raise BusinessRuleViolation(f"Cannot activate invalid promotion: {', '.join(validation_errors)}")

        # Check if should be scheduled or immediate
        now = datetime.utcnow()
        if self.valid_from > now:
            self.status = PromotionStatus.SCHEDULED
        else:
            self.status = PromotionStatus.ACTIVE
            self.activated_at = now

            # Raise event
            self.add_domain_event(PromotionActivated(
                promotion_id=self.id,
                promotion_name=self.promotion_name,
                activated_at=self.activated_at
            ))

        self.mark_as_modified()

    def deactivate(self):
        """Deactivate the promotion"""
        if self.status not in [PromotionStatus.ACTIVE, PromotionStatus.SCHEDULED]:
            raise BusinessRuleViolation(f"Cannot deactivate {self.status} promotion")

        self.status = PromotionStatus.PAUSED

        # Raise event
        self.add_domain_event(PromotionDeactivated(
            promotion_id=self.id,
            promotion_name=self.promotion_name,
            deactivated_at=datetime.utcnow()
        ))

        self.mark_as_modified()

    def cancel(self):
        """Cancel the promotion"""
        if self.status == PromotionStatus.CANCELLED:
            raise BusinessRuleViolation("Promotion is already cancelled")

        self.status = PromotionStatus.CANCELLED
        self.mark_as_modified()

    def check_and_expire(self):
        """Check if promotion should expire"""
        if not self.valid_until:
            return

        if datetime.utcnow() > self.valid_until and self.status == PromotionStatus.ACTIVE:
            self.status = PromotionStatus.EXPIRED

            # Raise event
            self.add_domain_event(PromotionExpired(
                promotion_id=self.id,
                promotion_name=self.promotion_name,
                expired_at=datetime.utcnow()
            ))

            self.mark_as_modified()

    def is_active(self) -> bool:
        """Check if promotion is currently active"""
        now = datetime.utcnow()

        # Check status
        if self.status != PromotionStatus.ACTIVE:
            return False

        # Check date range
        if now < self.valid_from:
            return False

        if self.valid_until and now > self.valid_until:
            return False

        # Check usage limits
        if self.max_total_uses and self.current_total_uses >= self.max_total_uses:
            return False

        return True

    def applies_to_product(self, product_sku: str, product_category: Optional[str] = None) -> bool:
        """Check if promotion applies to product"""
        if self.applicable_to == ApplicableProducts.ALL_PRODUCTS:
            return True

        if self.applicable_to == ApplicableProducts.SPECIFIC_SKUS:
            return product_sku in self.product_skus

        if self.applicable_to == ApplicableProducts.CATEGORY:
            return product_category == self.product_category

        return False

    def get_discount_code(self, code: str) -> Optional[DiscountCode]:
        """Get discount code by code string"""
        return next((dc for dc in self.discount_codes if dc.code == code.upper()), None)

    def get_active_discount_codes(self) -> List[DiscountCode]:
        """Get all active discount codes"""
        return [dc for dc in self.discount_codes if dc.is_active]

    def validate(self) -> List[str]:
        """Validate promotion"""
        errors = []

        if not self.promotion_name:
            errors.append("Promotion name is required")

        if not self.store_id:
            errors.append("Store ID is required")

        if not self.tenant_id:
            errors.append("Tenant ID is required")

        if self.discount_value < 0:
            errors.append("Discount value cannot be negative")

        if self.discount_type == DiscountType.PERCENTAGE and self.discount_value > 100:
            errors.append("Percentage discount cannot exceed 100%")

        if self.discount_type == DiscountType.BOGO:
            if not self.bogo_buy_quantity or self.bogo_buy_quantity <= 0:
                errors.append("BOGO buy quantity must be positive")
            if not self.bogo_get_quantity or self.bogo_get_quantity <= 0:
                errors.append("BOGO get quantity must be positive")

        if self.valid_until and self.valid_until <= self.valid_from:
            errors.append("Valid until must be after valid from")

        if self.applicable_to == ApplicableProducts.SPECIFIC_SKUS and not self.product_skus:
            errors.append("Must specify product SKUs when applicable_to is SPECIFIC_SKUS")

        if self.applicable_to == ApplicableProducts.CATEGORY and not self.product_category:
            errors.append("Must specify product category when applicable_to is CATEGORY")

        if self.requires_code and not self.discount_codes:
            errors.append("Must have at least one discount code when requires_code is True")

        return errors
