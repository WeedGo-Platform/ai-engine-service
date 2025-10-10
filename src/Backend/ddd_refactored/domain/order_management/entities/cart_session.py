"""
CartSession Aggregate Root
Following DDD Architecture Document Section 2.6
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from ....shared.domain_base import AggregateRoot, DomainEvent, BusinessRuleViolation


# Domain Events
class CartCreated(DomainEvent):
    cart_id: UUID
    session_id: str
    store_id: UUID


class ItemAddedToCart(DomainEvent):
    cart_id: UUID
    session_id: str
    sku: str
    quantity: int


class CartConverted(DomainEvent):
    cart_id: UUID
    session_id: str
    order_id: UUID


class CartAbandoned(DomainEvent):
    cart_id: UUID
    session_id: str
    total_value: Decimal


@dataclass
class CartItem:
    """Cart Item - entity within CartSession aggregate"""
    sku: str
    product_name: str
    product_type: str
    quantity: int
    unit_price: Decimal
    discount_amount: Decimal = Decimal("0")
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_subtotal(self) -> Decimal:
        """Calculate item subtotal"""
        return self.unit_price * Decimal(self.quantity) - self.discount_amount


@dataclass
class CartSession(AggregateRoot):
    """
    CartSession Aggregate Root - Shopping cart management
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.6
    """
    # Identifiers
    session_id: str = ""  # Browser/device session ID
    store_id: UUID = field(default_factory=uuid4)
    customer_id: Optional[UUID] = None

    # Status
    status: str = "active"  # active, abandoned, converted

    # Items
    items: List[CartItem] = field(default_factory=list)

    # Financial
    subtotal: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")
    delivery_fee: Decimal = Decimal("0")
    total: Decimal = Decimal("0")

    # Conversion
    converted_to_order_id: Optional[UUID] = None
    converted_at: Optional[datetime] = None

    # Expiry
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(hours=24))
    last_activity_at: datetime = field(default_factory=datetime.utcnow)

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        session_id: str,
        store_id: UUID,
        customer_id: Optional[UUID] = None,
        expiry_hours: int = 24
    ) -> 'CartSession':
        """Factory method to create new cart session"""
        if not session_id:
            raise BusinessRuleViolation("Session ID is required")

        cart = cls(
            session_id=session_id,
            store_id=store_id,
            customer_id=customer_id,
            status="active",
            expires_at=datetime.utcnow() + timedelta(hours=expiry_hours)
        )

        # Raise creation event
        cart.add_domain_event(CartCreated(
            cart_id=cart.id,
            session_id=session_id,
            store_id=store_id
        ))

        return cart

    def add_item(
        self,
        sku: str,
        product_name: str,
        product_type: str,
        quantity: int,
        unit_price: Decimal
    ):
        """Add item to cart or update quantity if exists"""
        if self.status != "active":
            raise BusinessRuleViolation(f"Cannot add items to {self.status} cart")

        if self.is_expired():
            raise BusinessRuleViolation("Cart has expired")

        if quantity <= 0:
            raise BusinessRuleViolation("Quantity must be positive")

        if unit_price < 0:
            raise BusinessRuleViolation("Unit price cannot be negative")

        # Check if item already exists
        existing_item = next((item for item in self.items if item.sku == sku), None)

        if existing_item:
            # Update quantity
            existing_item.quantity += quantity
        else:
            # Add new item
            cart_item = CartItem(
                sku=sku,
                product_name=product_name,
                product_type=product_type,
                quantity=quantity,
                unit_price=unit_price
            )
            self.items.append(cart_item)

        self._recalculate_totals()
        self._update_activity()

        # Raise event
        self.add_domain_event(ItemAddedToCart(
            cart_id=self.id,
            session_id=self.session_id,
            sku=sku,
            quantity=quantity
        ))

        self.mark_as_modified()

    def remove_item(self, sku: str):
        """Remove item from cart"""
        if self.status != "active":
            raise BusinessRuleViolation(f"Cannot remove items from {self.status} cart")

        self.items = [item for item in self.items if item.sku != sku]
        self._recalculate_totals()
        self._update_activity()
        self.mark_as_modified()

    def update_item_quantity(self, sku: str, new_quantity: int):
        """Update item quantity"""
        if self.status != "active":
            raise BusinessRuleViolation(f"Cannot update items in {self.status} cart")

        if new_quantity < 0:
            raise BusinessRuleViolation("Quantity cannot be negative")

        if new_quantity == 0:
            self.remove_item(sku)
            return

        for item in self.items:
            if item.sku == sku:
                item.quantity = new_quantity
                self._recalculate_totals()
                self._update_activity()
                self.mark_as_modified()
                return

        raise BusinessRuleViolation(f"Item {sku} not found in cart")

    def apply_discount(self, discount_amount: Decimal):
        """Apply discount to cart"""
        if discount_amount < 0:
            raise BusinessRuleViolation("Discount amount cannot be negative")

        if discount_amount > self.subtotal:
            raise BusinessRuleViolation("Discount cannot exceed subtotal")

        self.discount_amount = discount_amount
        self._recalculate_totals()
        self._update_activity()
        self.mark_as_modified()

    def set_delivery_fee(self, fee: Decimal):
        """Set delivery fee"""
        if fee < 0:
            raise BusinessRuleViolation("Delivery fee cannot be negative")

        self.delivery_fee = fee
        self._recalculate_totals()
        self._update_activity()
        self.mark_as_modified()

    def associate_customer(self, customer_id: UUID):
        """Associate cart with customer (for anonymous to logged-in transition)"""
        if self.customer_id and self.customer_id != customer_id:
            raise BusinessRuleViolation("Cart already associated with different customer")

        self.customer_id = customer_id
        self._update_activity()
        self.mark_as_modified()

    def convert_to_order(self, order_id: UUID):
        """Convert cart to order"""
        if self.status != "active":
            raise BusinessRuleViolation(f"Cannot convert {self.status} cart")

        if len(self.items) == 0:
            raise BusinessRuleViolation("Cannot convert empty cart")

        if self.is_expired():
            raise BusinessRuleViolation("Cannot convert expired cart")

        self.status = "converted"
        self.converted_to_order_id = order_id
        self.converted_at = datetime.utcnow()

        # Raise event
        self.add_domain_event(CartConverted(
            cart_id=self.id,
            session_id=self.session_id,
            order_id=order_id
        ))

        self.mark_as_modified()

    def abandon(self):
        """Mark cart as abandoned"""
        if self.status != "active":
            return  # Already abandoned or converted

        self.status = "abandoned"

        # Raise event
        self.add_domain_event(CartAbandoned(
            cart_id=self.id,
            session_id=self.session_id,
            total_value=self.total
        ))

        self.mark_as_modified()

    def extend_expiry(self, hours: int = 24):
        """Extend cart expiry"""
        if hours <= 0:
            raise BusinessRuleViolation("Extension hours must be positive")

        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        self._update_activity()
        self.mark_as_modified()

    def clear(self):
        """Clear all items from cart"""
        if self.status != "active":
            raise BusinessRuleViolation(f"Cannot clear {self.status} cart")

        self.items = []
        self._recalculate_totals()
        self._update_activity()
        self.mark_as_modified()

    def _recalculate_totals(self):
        """Recalculate cart totals"""
        self.subtotal = sum(item.get_subtotal() for item in self.items)

        # Calculate tax (simplified - 13% HST)
        taxable_amount = self.subtotal - self.discount_amount
        self.tax_amount = taxable_amount * Decimal("0.13")

        self.total = (
            self.subtotal +
            self.tax_amount +
            self.delivery_fee -
            self.discount_amount
        )

    def _update_activity(self):
        """Update last activity timestamp"""
        self.last_activity_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def is_expired(self) -> bool:
        """Check if cart has expired"""
        return datetime.utcnow() > self.expires_at

    def is_empty(self) -> bool:
        """Check if cart is empty"""
        return len(self.items) == 0

    def get_item_count(self) -> int:
        """Get total number of items"""
        return sum(item.quantity for item in self.items)

    def has_item(self, sku: str) -> bool:
        """Check if cart contains item"""
        return any(item.sku == sku for item in self.items)

    def get_item(self, sku: str) -> Optional[CartItem]:
        """Get cart item by SKU"""
        return next((item for item in self.items if item.sku == sku), None)

    def validate(self) -> List[str]:
        """Validate cart data"""
        errors = []

        if not self.session_id:
            errors.append("Session ID is required")

        if not self.store_id:
            errors.append("Store ID is required")

        if self.subtotal < 0:
            errors.append("Subtotal cannot be negative")

        if self.total < 0:
            errors.append("Total cannot be negative")

        if self.expires_at <= self.created_at:
            errors.append("Expiry date must be after creation date")

        return errors
