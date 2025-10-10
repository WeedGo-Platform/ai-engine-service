"""
Accessory Entity
Following DDD Architecture Document Section 2.3
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from ....shared.domain_base import AggregateRoot, DomainEvent, BusinessRuleViolation


class AccessoryCreated(DomainEvent):
    """Event raised when accessory is created"""
    accessory_id: UUID
    sku: str
    name: str
    category_id: UUID


class AccessoryUpdated(DomainEvent):
    """Event raised when accessory is updated"""
    accessory_id: UUID
    changes: Dict[str, Any]


class AccessoryCategorized(DomainEvent):
    """Event raised when accessory is categorized"""
    accessory_id: UUID
    category_id: UUID
    old_category_id: Optional[UUID]


class AccessoryPriceChanged(DomainEvent):
    """Event raised when accessory price changes"""
    accessory_id: UUID
    old_price: Decimal
    new_price: Decimal


@dataclass
class Accessory(AggregateRoot):
    """
    Accessory Aggregate Root - Non-cannabis products
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.3
    """
    # Identifiers
    sku: str = ""
    barcode: Optional[str] = None

    # Product Information
    name: str = ""
    brand: Optional[str] = None
    description: Optional[str] = None

    # Categorization
    category_id: UUID = field(default_factory=uuid4)
    tags: List[str] = field(default_factory=list)

    # Pricing
    unit_cost: Decimal = Decimal("0")
    retail_price: Decimal = Decimal("0")
    discount_price: Optional[Decimal] = None
    wholesale_price: Optional[Decimal] = None

    # Physical Attributes
    weight_g: Optional[Decimal] = None
    dimensions_cm: Optional[Dict[str, Decimal]] = None  # {"length": x, "width": y, "height": z}
    color: Optional[str] = None
    material: Optional[str] = None

    # Media
    image_url: Optional[str] = None
    additional_images: List[str] = field(default_factory=list)
    video_url: Optional[str] = None

    # Inventory
    track_inventory: bool = True
    low_stock_threshold: int = 10
    reorder_point: int = 20
    reorder_quantity: int = 50

    # Status
    is_active: bool = True
    is_featured: bool = False
    is_new: bool = False
    discontinued: bool = False
    discontinued_date: Optional[datetime] = None

    # Supplier Information
    supplier_id: Optional[UUID] = None
    supplier_sku: Optional[str] = None
    supplier_name: Optional[str] = None

    # SEO
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    seo_keywords: List[str] = field(default_factory=list)
    slug: Optional[str] = None

    # Compatibility
    compatible_with: List[str] = field(default_factory=list)  # List of product SKUs
    requires_age_verification: bool = False

    # Warranty
    warranty_months: Optional[int] = None
    warranty_description: Optional[str] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        sku: str,
        name: str,
        category_id: UUID,
        unit_cost: Decimal,
        retail_price: Decimal,
        **kwargs
    ) -> 'Accessory':
        """Factory method to create new accessory"""
        if not sku:
            raise BusinessRuleViolation("SKU is required")
        if not name:
            raise BusinessRuleViolation("Name is required")
        if unit_cost < 0:
            raise BusinessRuleViolation("Unit cost cannot be negative")
        if retail_price < 0:
            raise BusinessRuleViolation("Retail price cannot be negative")

        accessory = cls(
            sku=sku,
            name=name,
            category_id=category_id,
            unit_cost=unit_cost,
            retail_price=retail_price
        )

        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(accessory, key):
                setattr(accessory, key, value)

        # Generate slug if not provided
        if not accessory.slug:
            accessory.slug = accessory.generate_slug()

        # Raise creation event
        accessory.add_domain_event(AccessoryCreated(
            accessory_id=accessory.id,
            sku=sku,
            name=name,
            category_id=category_id
        ))

        return accessory

    def generate_slug(self) -> str:
        """Generate URL-friendly slug from name"""
        import re
        slug = self.name.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')

    def update_pricing(
        self,
        retail_price: Optional[Decimal] = None,
        unit_cost: Optional[Decimal] = None,
        discount_price: Optional[Decimal] = None,
        wholesale_price: Optional[Decimal] = None
    ):
        """Update accessory pricing"""
        changes = {}

        if retail_price is not None:
            if retail_price < 0:
                raise BusinessRuleViolation("Retail price cannot be negative")
            old_price = self.retail_price
            self.retail_price = retail_price
            changes['retail_price'] = {'old': old_price, 'new': retail_price}

            # Raise price change event
            self.add_domain_event(AccessoryPriceChanged(
                accessory_id=self.id,
                old_price=old_price,
                new_price=retail_price
            ))

        if unit_cost is not None:
            if unit_cost < 0:
                raise BusinessRuleViolation("Unit cost cannot be negative")
            changes['unit_cost'] = {'old': self.unit_cost, 'new': unit_cost}
            self.unit_cost = unit_cost

        if discount_price is not None:
            if discount_price < 0:
                raise BusinessRuleViolation("Discount price cannot be negative")
            if discount_price >= self.retail_price:
                raise BusinessRuleViolation("Discount price must be less than retail price")
            changes['discount_price'] = {'old': self.discount_price, 'new': discount_price}
            self.discount_price = discount_price

        if wholesale_price is not None:
            if wholesale_price < 0:
                raise BusinessRuleViolation("Wholesale price cannot be negative")
            changes['wholesale_price'] = {'old': self.wholesale_price, 'new': wholesale_price}
            self.wholesale_price = wholesale_price

        if changes:
            self.add_domain_event(AccessoryUpdated(
                accessory_id=self.id,
                changes=changes
            ))
            self.mark_as_modified()

    def categorize(self, category_id: UUID):
        """Change accessory category"""
        if category_id == self.category_id:
            return

        old_category = self.category_id
        self.category_id = category_id

        self.add_domain_event(AccessoryCategorized(
            accessory_id=self.id,
            category_id=category_id,
            old_category_id=old_category
        ))
        self.mark_as_modified()

    def add_tag(self, tag: str):
        """Add a tag to the accessory"""
        normalized_tag = tag.lower().strip()
        if normalized_tag and normalized_tag not in self.tags:
            self.tags.append(normalized_tag)
            self.mark_as_modified()

    def remove_tag(self, tag: str):
        """Remove a tag from the accessory"""
        normalized_tag = tag.lower().strip()
        if normalized_tag in self.tags:
            self.tags.remove(normalized_tag)
            self.mark_as_modified()

    def add_image(self, image_url: str, is_primary: bool = False):
        """Add product image"""
        if is_primary:
            self.image_url = image_url
        elif image_url not in self.additional_images:
            self.additional_images.append(image_url)
        self.mark_as_modified()

    def remove_image(self, image_url: str):
        """Remove product image"""
        if image_url == self.image_url:
            # If removing primary, promote first additional
            if self.additional_images:
                self.image_url = self.additional_images.pop(0)
            else:
                self.image_url = None
        elif image_url in self.additional_images:
            self.additional_images.remove(image_url)
        self.mark_as_modified()

    def add_compatibility(self, product_sku: str):
        """Add compatible product"""
        if product_sku not in self.compatible_with:
            self.compatible_with.append(product_sku)
            self.mark_as_modified()

    def remove_compatibility(self, product_sku: str):
        """Remove compatible product"""
        if product_sku in self.compatible_with:
            self.compatible_with.remove(product_sku)
            self.mark_as_modified()

    def set_inventory_tracking(
        self,
        track_inventory: bool,
        low_stock_threshold: Optional[int] = None,
        reorder_point: Optional[int] = None,
        reorder_quantity: Optional[int] = None
    ):
        """Configure inventory tracking"""
        self.track_inventory = track_inventory

        if low_stock_threshold is not None:
            if low_stock_threshold < 0:
                raise BusinessRuleViolation("Low stock threshold cannot be negative")
            self.low_stock_threshold = low_stock_threshold

        if reorder_point is not None:
            if reorder_point < 0:
                raise BusinessRuleViolation("Reorder point cannot be negative")
            self.reorder_point = reorder_point

        if reorder_quantity is not None:
            if reorder_quantity <= 0:
                raise BusinessRuleViolation("Reorder quantity must be positive")
            self.reorder_quantity = reorder_quantity

        self.mark_as_modified()

    def update_supplier_info(
        self,
        supplier_id: Optional[UUID] = None,
        supplier_sku: Optional[str] = None,
        supplier_name: Optional[str] = None
    ):
        """Update supplier information"""
        if supplier_id is not None:
            self.supplier_id = supplier_id
        if supplier_sku is not None:
            self.supplier_sku = supplier_sku
        if supplier_name is not None:
            self.supplier_name = supplier_name
        self.mark_as_modified()

    def set_warranty(self, months: int, description: Optional[str] = None):
        """Set warranty information"""
        if months < 0:
            raise BusinessRuleViolation("Warranty months cannot be negative")
        self.warranty_months = months
        self.warranty_description = description
        self.mark_as_modified()

    def feature(self):
        """Mark accessory as featured"""
        self.is_featured = True
        self.mark_as_modified()

    def unfeature(self):
        """Remove featured status"""
        self.is_featured = False
        self.mark_as_modified()

    def mark_as_new(self):
        """Mark accessory as new"""
        self.is_new = True
        self.mark_as_modified()

    def unmark_as_new(self):
        """Remove new status"""
        self.is_new = False
        self.mark_as_modified()

    def activate(self):
        """Activate the accessory"""
        self.is_active = True
        self.discontinued = False
        self.discontinued_date = None
        self.mark_as_modified()

    def deactivate(self):
        """Deactivate the accessory"""
        self.is_active = False
        self.mark_as_modified()

    def discontinue(self):
        """Mark accessory as discontinued"""
        self.discontinued = True
        self.discontinued_date = datetime.utcnow()
        self.is_active = False
        self.mark_as_modified()

    def get_effective_price(self) -> Decimal:
        """Get the effective selling price (considering discounts)"""
        if self.discount_price and self.discount_price < self.retail_price:
            return self.discount_price
        return self.retail_price

    def get_margin(self) -> Decimal:
        """Calculate profit margin"""
        if self.unit_cost == 0:
            return Decimal("100")
        effective_price = self.get_effective_price()
        margin = ((effective_price - self.unit_cost) / effective_price) * 100
        return margin.quantize(Decimal("0.01"))

    def get_markup(self) -> Decimal:
        """Calculate markup percentage"""
        if self.unit_cost == 0:
            return Decimal("0")
        effective_price = self.get_effective_price()
        markup = ((effective_price - self.unit_cost) / self.unit_cost) * 100
        return markup.quantize(Decimal("0.01"))

    def is_on_sale(self) -> bool:
        """Check if accessory is on sale"""
        return self.discount_price is not None and self.discount_price < self.retail_price

    def get_discount_percentage(self) -> Optional[Decimal]:
        """Calculate discount percentage"""
        if not self.is_on_sale():
            return None
        discount_amount = self.retail_price - self.discount_price
        percentage = (discount_amount / self.retail_price) * 100
        return percentage.quantize(Decimal("0.01"))

    def matches_search(self, search_term: str) -> bool:
        """Check if accessory matches search term"""
        search_lower = search_term.lower()
        searchable_fields = [
            self.sku,
            self.name,
            self.brand,
            self.description
        ]
        searchable_fields.extend(self.tags)

        return any(
            field and search_lower in field.lower()
            for field in searchable_fields
        )

    def validate(self) -> List[str]:
        """Validate accessory data"""
        errors = []

        if not self.sku:
            errors.append("SKU is required")

        if not self.name:
            errors.append("Name is required")

        if not self.category_id:
            errors.append("Category ID is required")

        if self.unit_cost < 0:
            errors.append("Unit cost cannot be negative")

        if self.retail_price < 0:
            errors.append("Retail price cannot be negative")

        if self.discount_price and self.discount_price >= self.retail_price:
            errors.append("Discount price must be less than retail price")

        if self.low_stock_threshold < 0:
            errors.append("Low stock threshold cannot be negative")

        if self.reorder_point < 0:
            errors.append("Reorder point cannot be negative")

        if self.reorder_quantity <= 0:
            errors.append("Reorder quantity must be positive")

        return errors

    def to_catalog_display(self) -> Dict[str, Any]:
        """Convert to catalog display format"""
        return {
            'id': str(self.id),
            'sku': self.sku,
            'name': self.name,
            'brand': self.brand,
            'category_id': str(self.category_id),
            'price': float(self.retail_price),
            'sale_price': float(self.discount_price) if self.discount_price else None,
            'on_sale': self.is_on_sale(),
            'discount_percentage': float(self.get_discount_percentage()) if self.is_on_sale() else None,
            'image': self.image_url,
            'images': self.additional_images,
            'description': self.description,
            'featured': self.is_featured,
            'new': self.is_new,
            'active': self.is_active,
            'discontinued': self.discontinued,
            'tags': self.tags,
            'warranty_months': self.warranty_months
        }