"""
StoreSettings Value Object
Following DDD Architecture Document Section 2.1
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from decimal import Decimal

from ....shared.domain_base import ValueObject


@dataclass(frozen=True)
class StoreSettings(ValueObject):
    """
    Store settings value object
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.1
    """
    # Display Settings
    show_out_of_stock: bool = True
    show_coming_soon: bool = True
    show_prices_with_tax: bool = False
    currency_symbol: str = "$"
    currency_position: str = "before"  # before/after

    # Inventory Settings
    track_inventory: bool = True
    allow_backorders: bool = False
    low_stock_threshold: int = 10
    auto_hide_out_of_stock: bool = False

    # Checkout Settings
    require_age_verification: bool = True
    minimum_age: int = 19
    require_id_upload: bool = False
    enable_guest_checkout: bool = False

    # Order Settings
    min_order_value: Decimal = Decimal("0.00")
    max_order_value: Optional[Decimal] = None
    order_prefix: str = "ORD"
    auto_confirm_orders: bool = False

    # Delivery Settings
    delivery_fee: Decimal = Decimal("5.00")
    free_delivery_threshold: Decimal = Decimal("50.00")
    delivery_time_slots: Dict[str, Any] = None
    express_delivery_enabled: bool = False
    express_delivery_fee: Decimal = Decimal("10.00")

    # Pickup Settings
    pickup_time_slots: Dict[str, Any] = None
    curbside_pickup_enabled: bool = False
    pickup_notification_method: str = "sms"  # sms/email/both

    # Payment Settings
    accepted_payment_methods: Dict[str, bool] = None
    capture_payment_immediately: bool = True
    enable_tips: bool = True
    tip_suggestions: list = None  # [10, 15, 20, 25] percentages

    # Tax Settings
    tax_included_in_prices: bool = False
    tax_calculation_method: str = "per_line"  # per_line/per_total

    # Notification Settings
    order_confirmation_email: bool = True
    order_confirmation_sms: bool = False
    order_ready_notification: bool = True
    delivery_notification: bool = True

    # Marketing Settings
    enable_reviews: bool = True
    enable_wishlist: bool = True
    enable_recommendations: bool = True
    enable_loyalty_program: bool = False

    # POS Settings
    pos_receipt_header: Optional[str] = None
    pos_receipt_footer: Optional[str] = None
    print_receipt_automatically: bool = True
    email_receipt_option: bool = True

    # Kiosk Settings
    kiosk_idle_timeout: int = 300  # seconds
    kiosk_welcome_message: Optional[str] = None
    kiosk_language_options: list = None  # ['en', 'fr']

    # Custom Settings
    custom_settings: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize default values for complex types"""
        object.__setattr__(self, 'delivery_time_slots', self.delivery_time_slots or {})
        object.__setattr__(self, 'pickup_time_slots', self.pickup_time_slots or {})
        object.__setattr__(self, 'accepted_payment_methods', self.accepted_payment_methods or {
            'credit_card': True,
            'debit_card': True,
            'cash': True,
            'e_transfer': False
        })
        object.__setattr__(self, 'tip_suggestions', self.tip_suggestions or [10, 15, 20, 25])
        object.__setattr__(self, 'kiosk_language_options', self.kiosk_language_options or ['en'])
        object.__setattr__(self, 'custom_settings', self.custom_settings or {})

    def with_delivery_settings(
        self,
        delivery_fee: Optional[Decimal] = None,
        free_delivery_threshold: Optional[Decimal] = None,
        express_enabled: Optional[bool] = None
    ) -> 'StoreSettings':
        """Create new instance with updated delivery settings"""
        return StoreSettings(
            **{**self.__dict__,
               'delivery_fee': delivery_fee or self.delivery_fee,
               'free_delivery_threshold': free_delivery_threshold or self.free_delivery_threshold,
               'express_delivery_enabled': express_enabled if express_enabled is not None else self.express_delivery_enabled}
        )

    def with_payment_settings(
        self,
        accepted_methods: Optional[Dict[str, bool]] = None,
        enable_tips: Optional[bool] = None,
        tip_suggestions: Optional[list] = None
    ) -> 'StoreSettings':
        """Create new instance with updated payment settings"""
        return StoreSettings(
            **{**self.__dict__,
               'accepted_payment_methods': accepted_methods or self.accepted_payment_methods,
               'enable_tips': enable_tips if enable_tips is not None else self.enable_tips,
               'tip_suggestions': tip_suggestions or self.tip_suggestions}
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'display': {
                'show_out_of_stock': self.show_out_of_stock,
                'show_coming_soon': self.show_coming_soon,
                'show_prices_with_tax': self.show_prices_with_tax,
                'currency_symbol': self.currency_symbol,
                'currency_position': self.currency_position
            },
            'inventory': {
                'track_inventory': self.track_inventory,
                'allow_backorders': self.allow_backorders,
                'low_stock_threshold': self.low_stock_threshold,
                'auto_hide_out_of_stock': self.auto_hide_out_of_stock
            },
            'checkout': {
                'require_age_verification': self.require_age_verification,
                'minimum_age': self.minimum_age,
                'require_id_upload': self.require_id_upload,
                'enable_guest_checkout': self.enable_guest_checkout
            },
            'orders': {
                'min_order_value': str(self.min_order_value),
                'max_order_value': str(self.max_order_value) if self.max_order_value else None,
                'order_prefix': self.order_prefix,
                'auto_confirm_orders': self.auto_confirm_orders
            },
            'delivery': {
                'delivery_fee': str(self.delivery_fee),
                'free_delivery_threshold': str(self.free_delivery_threshold),
                'delivery_time_slots': self.delivery_time_slots,
                'express_delivery_enabled': self.express_delivery_enabled,
                'express_delivery_fee': str(self.express_delivery_fee)
            },
            'pickup': {
                'pickup_time_slots': self.pickup_time_slots,
                'curbside_pickup_enabled': self.curbside_pickup_enabled,
                'pickup_notification_method': self.pickup_notification_method
            },
            'payment': {
                'accepted_payment_methods': self.accepted_payment_methods,
                'capture_payment_immediately': self.capture_payment_immediately,
                'enable_tips': self.enable_tips,
                'tip_suggestions': self.tip_suggestions
            },
            'tax': {
                'tax_included_in_prices': self.tax_included_in_prices,
                'tax_calculation_method': self.tax_calculation_method
            },
            'notifications': {
                'order_confirmation_email': self.order_confirmation_email,
                'order_confirmation_sms': self.order_confirmation_sms,
                'order_ready_notification': self.order_ready_notification,
                'delivery_notification': self.delivery_notification
            },
            'marketing': {
                'enable_reviews': self.enable_reviews,
                'enable_wishlist': self.enable_wishlist,
                'enable_recommendations': self.enable_recommendations,
                'enable_loyalty_program': self.enable_loyalty_program
            },
            'pos': {
                'receipt_header': self.pos_receipt_header,
                'receipt_footer': self.pos_receipt_footer,
                'print_receipt_automatically': self.print_receipt_automatically,
                'email_receipt_option': self.email_receipt_option
            },
            'kiosk': {
                'idle_timeout': self.kiosk_idle_timeout,
                'welcome_message': self.kiosk_welcome_message,
                'language_options': self.kiosk_language_options
            },
            'custom': self.custom_settings
        }