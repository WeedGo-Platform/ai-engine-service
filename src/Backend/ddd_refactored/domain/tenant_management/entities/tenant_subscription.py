"""
TenantSubscription Entity
Following DDD Architecture Document Section 2.1
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from enum import Enum

from ....shared.domain_base import Entity, BusinessRuleViolation, DomainEvent


class SubscriptionStatus(str, Enum):
    """Subscription status"""
    ACTIVE = "active"
    TRIAL = "trial"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


class PaymentStatus(str, Enum):
    """Payment status"""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class BillingFrequency(str, Enum):
    """Billing frequency"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


# Domain Events
class SubscriptionCreated(DomainEvent):
    def __init__(self, subscription_id: UUID, tenant_id: UUID, tier: str):
        super().__init__(subscription_id)
        self.tenant_id = tenant_id
        self.tier = tier

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'tenant_id': str(self.tenant_id),
            'tier': self.tier
        })
        return data


class SubscriptionRenewed(DomainEvent):
    def __init__(self, subscription_id: UUID, renewal_date: date, next_billing_date: date):
        super().__init__(subscription_id)
        self.renewal_date = renewal_date
        self.next_billing_date = next_billing_date

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'renewal_date': self.renewal_date.isoformat(),
            'next_billing_date': self.next_billing_date.isoformat()
        })
        return data


class PaymentFailed(DomainEvent):
    def __init__(self, subscription_id: UUID, amount: Decimal, reason: str):
        super().__init__(subscription_id)
        self.amount = amount
        self.reason = reason

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'amount': str(self.amount),
            'reason': self.reason
        })
        return data


@dataclass
class TenantSubscription(Entity):
    """
    TenantSubscription Entity - Manages tenant subscription and billing
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.1
    """
    tenant_id: UUID = field(default_factory=uuid4)
    tier: str = "community_and_new_business"
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE

    # Billing Information
    billing_frequency: BillingFrequency = BillingFrequency.MONTHLY
    base_price: Decimal = Decimal("0.00")
    discount_percentage: Decimal = Decimal("0.00")
    final_price: Decimal = Decimal("0.00")
    currency: str = "CAD"

    # Subscription Dates
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    trial_end_date: Optional[date] = None
    next_billing_date: Optional[date] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None

    # Payment Information
    last_payment_date: Optional[date] = None
    last_payment_amount: Optional[Decimal] = None
    last_payment_status: Optional[PaymentStatus] = None
    failed_payment_count: int = 0
    total_paid: Decimal = Decimal("0.00")

    # Usage Limits
    max_stores: int = 1
    max_users: int = 5
    max_products: int = 1000
    max_orders_per_month: int = 500
    max_api_calls_per_month: int = 10000
    max_ai_personalities: int = 1

    # Current Usage
    current_stores: int = 0
    current_users: int = 0
    current_products: int = 0
    current_orders_this_month: int = 0
    current_api_calls_this_month: int = 0

    # Features
    features: Dict[str, bool] = field(default_factory=dict)
    add_ons: List[str] = field(default_factory=list)

    # Payment Method
    payment_method_id: Optional[str] = None  # Stripe/payment provider ID
    payment_method_type: Optional[str] = None  # credit_card, bank_account, etc
    auto_renew: bool = True

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        tier: str,
        billing_frequency: BillingFrequency = BillingFrequency.MONTHLY,
        trial_days: int = 14
    ) -> 'TenantSubscription':
        """Factory method to create a new subscription"""
        subscription = cls(
            tenant_id=tenant_id,
            tier=tier,
            billing_frequency=billing_frequency,
            status=SubscriptionStatus.TRIAL if trial_days > 0 else SubscriptionStatus.ACTIVE,
            start_date=date.today()
        )

        # Set trial period
        if trial_days > 0:
            subscription.trial_end_date = date.today() + timedelta(days=trial_days)
            subscription.next_billing_date = subscription.trial_end_date
        else:
            subscription.next_billing_date = subscription._calculate_next_billing_date()

        # Set tier limits and pricing
        subscription._apply_tier_settings(tier)

        # Set default features
        subscription._set_default_features()

        # Raise domain event
        subscription.add_domain_event(SubscriptionCreated(
            subscription_id=subscription.id,
            tenant_id=tenant_id,
            tier=tier
        ))

        return subscription

    def _apply_tier_settings(self, tier: str):
        """Apply tier-specific settings"""
        tier_settings = {
            'community_and_new_business': {
                'base_price': Decimal("0.00"),
                'max_stores': 1,
                'max_users': 5,
                'max_products': 1000,
                'max_orders_per_month': 500,
                'max_api_calls_per_month': 10000,
                'max_ai_personalities': 1
            },
            'small_business': {
                'base_price': Decimal("99.00"),
                'max_stores': 5,
                'max_users': 15,
                'max_products': 5000,
                'max_orders_per_month': 2000,
                'max_api_calls_per_month': 50000,
                'max_ai_personalities': 2
            },
            'professional_and_growing_business': {
                'base_price': Decimal("299.00"),
                'max_stores': 12,
                'max_users': 50,
                'max_products': 20000,
                'max_orders_per_month': 10000,
                'max_api_calls_per_month': 200000,
                'max_ai_personalities': 3
            },
            'enterprise': {
                'base_price': Decimal("999.00"),
                'max_stores': 999,  # Unlimited
                'max_users': 999,  # Unlimited
                'max_products': 999999,  # Unlimited
                'max_orders_per_month': 999999,  # Unlimited
                'max_api_calls_per_month': 999999,  # Unlimited
                'max_ai_personalities': 5
            }
        }

        settings = tier_settings.get(tier, tier_settings['community_and_new_business'])

        self.base_price = settings['base_price']
        self.max_stores = settings['max_stores']
        self.max_users = settings['max_users']
        self.max_products = settings['max_products']
        self.max_orders_per_month = settings['max_orders_per_month']
        self.max_api_calls_per_month = settings['max_api_calls_per_month']
        self.max_ai_personalities = settings['max_ai_personalities']

        self._calculate_final_price()

    def _set_default_features(self):
        """Set default features based on tier"""
        tier_features = {
            'community_and_new_business': {
                'ecommerce': True,
                'pos': False,
                'kiosk': False,
                'delivery': True,
                'pickup': True,
                'inventory_management': True,
                'basic_reporting': True,
                'advanced_reporting': False,
                'api_access': False,
                'custom_domain': False,
                'priority_support': False,
                'ai_chat': True,
                'ai_voice': False,
                'marketing_tools': False,
                'loyalty_program': False
            },
            'small_business': {
                'ecommerce': True,
                'pos': True,
                'kiosk': False,
                'delivery': True,
                'pickup': True,
                'inventory_management': True,
                'basic_reporting': True,
                'advanced_reporting': True,
                'api_access': True,
                'custom_domain': False,
                'priority_support': False,
                'ai_chat': True,
                'ai_voice': False,
                'marketing_tools': True,
                'loyalty_program': False
            },
            'professional_and_growing_business': {
                'ecommerce': True,
                'pos': True,
                'kiosk': True,
                'delivery': True,
                'pickup': True,
                'inventory_management': True,
                'basic_reporting': True,
                'advanced_reporting': True,
                'api_access': True,
                'custom_domain': True,
                'priority_support': True,
                'ai_chat': True,
                'ai_voice': True,
                'marketing_tools': True,
                'loyalty_program': True
            },
            'enterprise': {
                'ecommerce': True,
                'pos': True,
                'kiosk': True,
                'delivery': True,
                'pickup': True,
                'inventory_management': True,
                'basic_reporting': True,
                'advanced_reporting': True,
                'api_access': True,
                'custom_domain': True,
                'priority_support': True,
                'ai_chat': True,
                'ai_voice': True,
                'marketing_tools': True,
                'loyalty_program': True,
                'white_label': True,
                'dedicated_support': True,
                'custom_integrations': True
            }
        }

        self.features = tier_features.get(self.tier, tier_features['community_and_new_business'])

    def _calculate_final_price(self):
        """Calculate final price with discounts"""
        discount_amount = self.base_price * (self.discount_percentage / 100)
        self.final_price = self.base_price - discount_amount

    def _calculate_next_billing_date(self) -> date:
        """Calculate next billing date based on frequency"""
        if not self.start_date:
            return date.today()

        if self.billing_frequency == BillingFrequency.MONTHLY:
            return self.start_date + timedelta(days=30)
        elif self.billing_frequency == BillingFrequency.QUARTERLY:
            return self.start_date + timedelta(days=90)
        elif self.billing_frequency == BillingFrequency.ANNUAL:
            return self.start_date + timedelta(days=365)
        else:
            return self.start_date + timedelta(days=30)

    def can_add_store(self) -> bool:
        """Check if can add more stores"""
        return self.current_stores < self.max_stores

    def can_add_user(self) -> bool:
        """Check if can add more users"""
        return self.current_users < self.max_users

    def can_add_product(self) -> bool:
        """Check if can add more products"""
        return self.current_products < self.max_products

    def can_process_order(self) -> bool:
        """Check if can process more orders this month"""
        return self.current_orders_this_month < self.max_orders_per_month

    def can_make_api_call(self) -> bool:
        """Check if can make more API calls this month"""
        return self.current_api_calls_this_month < self.max_api_calls_per_month

    def has_feature(self, feature: str) -> bool:
        """Check if subscription includes a feature"""
        return self.features.get(feature, False)

    def has_addon(self, addon: str) -> bool:
        """Check if subscription has an add-on"""
        return addon in self.add_ons

    def activate_trial(self, trial_days: int = 14):
        """Activate trial period"""
        if self.status != SubscriptionStatus.ACTIVE:
            raise BusinessRuleViolation("Can only start trial for new subscriptions")

        self.status = SubscriptionStatus.TRIAL
        self.trial_end_date = date.today() + timedelta(days=trial_days)
        self.next_billing_date = self.trial_end_date
        self.mark_as_modified()

    def end_trial(self):
        """End trial period and activate subscription"""
        if self.status != SubscriptionStatus.TRIAL:
            raise BusinessRuleViolation("Subscription is not in trial")

        self.status = SubscriptionStatus.ACTIVE
        self.trial_end_date = None
        self.next_billing_date = self._calculate_next_billing_date()
        self.mark_as_modified()

    def renew(self):
        """Renew subscription for next billing period"""
        if self.status not in [SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE]:
            raise BusinessRuleViolation("Cannot renew subscription in current status")

        old_billing_date = self.next_billing_date
        self.next_billing_date = self._calculate_next_billing_date()
        self.status = SubscriptionStatus.ACTIVE
        self.failed_payment_count = 0
        self.mark_as_modified()

        self.add_domain_event(SubscriptionRenewed(
            subscription_id=self.id,
            renewal_date=date.today(),
            next_billing_date=self.next_billing_date
        ))

    def record_payment(self, amount: Decimal, status: PaymentStatus = PaymentStatus.PAID):
        """Record a payment"""
        self.last_payment_date = date.today()
        self.last_payment_amount = amount
        self.last_payment_status = status

        if status == PaymentStatus.PAID:
            self.total_paid += amount
            self.failed_payment_count = 0
            if self.status == SubscriptionStatus.PAST_DUE:
                self.status = SubscriptionStatus.ACTIVE
        elif status == PaymentStatus.FAILED:
            self.failed_payment_count += 1
            if self.failed_payment_count >= 3:
                self.status = SubscriptionStatus.PAST_DUE

            self.add_domain_event(PaymentFailed(
                subscription_id=self.id,
                amount=amount,
                reason="Payment failed"
            ))

        self.mark_as_modified()

    def apply_discount(self, percentage: Decimal):
        """Apply discount to subscription"""
        if percentage < 0 or percentage > 100:
            raise BusinessRuleViolation("Discount percentage must be between 0 and 100")

        self.discount_percentage = percentage
        self._calculate_final_price()
        self.mark_as_modified()

    def add_addon(self, addon: str, price: Optional[Decimal] = None):
        """Add an add-on to subscription"""
        if addon not in self.add_ons:
            self.add_ons.append(addon)
            if price:
                self.final_price += price
            self.mark_as_modified()

    def remove_addon(self, addon: str, price: Optional[Decimal] = None):
        """Remove an add-on from subscription"""
        if addon in self.add_ons:
            self.add_ons.remove(addon)
            if price:
                self.final_price -= price
            self.mark_as_modified()

    def cancel(self, reason: Optional[str] = None, immediate: bool = False):
        """Cancel subscription"""
        if self.status == SubscriptionStatus.CANCELLED:
            raise BusinessRuleViolation("Subscription is already cancelled")

        self.status = SubscriptionStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()
        self.cancellation_reason = reason
        self.auto_renew = False

        if immediate:
            self.end_date = date.today()
        else:
            # Cancel at end of billing period
            self.end_date = self.next_billing_date

        self.mark_as_modified()

    def suspend(self, reason: Optional[str] = None):
        """Suspend subscription"""
        if self.status == SubscriptionStatus.SUSPENDED:
            raise BusinessRuleViolation("Subscription is already suspended")

        self.status = SubscriptionStatus.SUSPENDED
        if reason:
            self.metadata['suspension_reason'] = reason
            self.metadata['suspension_date'] = datetime.utcnow().isoformat()

        self.mark_as_modified()

    def reactivate(self):
        """Reactivate a cancelled or suspended subscription"""
        if self.status not in [SubscriptionStatus.CANCELLED, SubscriptionStatus.SUSPENDED]:
            raise BusinessRuleViolation("Can only reactivate cancelled or suspended subscriptions")

        self.status = SubscriptionStatus.ACTIVE
        self.cancelled_at = None
        self.cancellation_reason = None
        self.auto_renew = True

        # Clear suspension metadata
        self.metadata.pop('suspension_reason', None)
        self.metadata.pop('suspension_date', None)

        self.mark_as_modified()

    def update_usage(
        self,
        stores: Optional[int] = None,
        users: Optional[int] = None,
        products: Optional[int] = None,
        orders: Optional[int] = None,
        api_calls: Optional[int] = None
    ):
        """Update current usage metrics"""
        if stores is not None:
            self.current_stores = stores
        if users is not None:
            self.current_users = users
        if products is not None:
            self.current_products = products
        if orders is not None:
            self.current_orders_this_month = orders
        if api_calls is not None:
            self.current_api_calls_this_month = api_calls

        self.mark_as_modified()

    def reset_monthly_usage(self):
        """Reset monthly usage counters"""
        self.current_orders_this_month = 0
        self.current_api_calls_this_month = 0
        self.mark_as_modified()

    def is_active(self) -> bool:
        """Check if subscription is active"""
        return self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]

    def is_expired(self) -> bool:
        """Check if subscription is expired"""
        if self.end_date:
            return date.today() > self.end_date
        return False

    def days_until_renewal(self) -> int:
        """Get days until next renewal"""
        if self.next_billing_date:
            return (self.next_billing_date - date.today()).days
        return 0

    def validate(self) -> List[str]:
        """Validate subscription data"""
        errors = []

        if not self.tenant_id:
            errors.append("Tenant ID is required")

        if not self.tier:
            errors.append("Subscription tier is required")

        if self.base_price < 0:
            errors.append("Base price cannot be negative")

        if self.discount_percentage < 0 or self.discount_percentage > 100:
            errors.append("Discount percentage must be between 0 and 100")

        if self.current_stores > self.max_stores:
            errors.append("Current stores exceeds maximum allowed")

        if self.current_users > self.max_users:
            errors.append("Current users exceeds maximum allowed")

        return errors