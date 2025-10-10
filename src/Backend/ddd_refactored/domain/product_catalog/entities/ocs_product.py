"""
OcsProduct Entity
Following DDD Architecture Document Section 2.3
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from ....shared.domain_base import AggregateRoot, DomainEvent, BusinessRuleViolation
from ..value_objects import (
    PlantType,
    ProductForm,
    ProductAttributes,
    CannabinoidRange,
    TerpeneProfile,
    Category,
    SubCategory,
    SubSubCategory
)


class OcsProductImported(DomainEvent):
    """Event raised when OCS product is imported"""
    ocs_variant_number: str
    product_name: str
    brand_name: str


class OcsProductUpdated(DomainEvent):
    """Event raised when OCS product is updated"""
    ocs_variant_number: str
    changes: Dict[str, Any]


class OcsProductActivated(DomainEvent):
    """Event raised when OCS product is activated"""
    ocs_variant_number: str


class OcsProductDeactivated(DomainEvent):
    """Event raised when OCS product is deactivated"""
    ocs_variant_number: str
    reason: str


@dataclass
class OcsProduct(AggregateRoot):
    """
    OcsProduct Aggregate Root - Provincial cannabis product catalog
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.3
    """
    # Primary Identifiers
    ocs_variant_number: str = ""  # Primary SKU from OCS

    # Product Information
    ocs_product_name: str = ""  # Official OCS product name
    product_name: str = ""  # Display name
    brand_name: str = ""

    # Categorization
    subcategory: Optional[str] = None
    category: Optional[Category] = None
    sub_category: Optional[SubCategory] = None
    sub_sub_category: Optional[SubSubCategory] = None

    # Cannabis Attributes
    plant_type: Optional[PlantType] = None
    product_form: Optional[ProductForm] = None
    product_attributes: Optional[ProductAttributes] = None

    # Cannabinoid Content
    total_mg: Optional[Decimal] = None
    cbd_min: Optional[Decimal] = None
    cbd_max: Optional[Decimal] = None
    thc_min: Optional[Decimal] = None
    thc_max: Optional[Decimal] = None

    # Terpenes
    terpene_profile: Optional[TerpeneProfile] = None

    # Physical Attributes
    volume_ml: Optional[Decimal] = None
    pieces: Optional[int] = None
    unit_of_measure: Optional[str] = None

    # Pricing
    price_per_unit: Optional[Decimal] = None
    msrp_price: Optional[Decimal] = None

    # Product Details
    image_url: Optional[str] = None
    description: Optional[str] = None
    allergens: Optional[str] = None
    ingredients: Optional[str] = None

    # Status
    is_active: bool = True
    is_available: bool = True
    discontinued: bool = False
    discontinued_date: Optional[datetime] = None

    # Import Tracking
    last_import_date: Optional[datetime] = None
    import_source: Optional[str] = None  # e.g., "OCS_API", "MANUAL", "CSV"

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def import_from_ocs(
        cls,
        ocs_variant_number: str,
        ocs_product_name: str,
        product_name: str,
        brand_name: str,
        **kwargs
    ) -> 'OcsProduct':
        """Factory method to import product from OCS"""
        product = cls(
            ocs_variant_number=ocs_variant_number,
            ocs_product_name=ocs_product_name,
            product_name=product_name,
            brand_name=brand_name,
            last_import_date=datetime.utcnow(),
            import_source="OCS_API"
        )

        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(product, key):
                setattr(product, key, value)

        # Create cannabinoid range if THC/CBD values provided
        if any(k in kwargs for k in ['thc_min', 'thc_max', 'cbd_min', 'cbd_max']):
            product.set_cannabinoid_content(
                thc_min=kwargs.get('thc_min'),
                thc_max=kwargs.get('thc_max'),
                cbd_min=kwargs.get('cbd_min'),
                cbd_max=kwargs.get('cbd_max')
            )

        # Raise import event
        product.add_domain_event(OcsProductImported(
            ocs_variant_number=ocs_variant_number,
            product_name=product_name,
            brand_name=brand_name
        ))

        return product

    def set_cannabinoid_content(
        self,
        thc_min: Optional[Decimal] = None,
        thc_max: Optional[Decimal] = None,
        cbd_min: Optional[Decimal] = None,
        cbd_max: Optional[Decimal] = None
    ):
        """Set cannabinoid content ranges"""
        self.thc_min = thc_min
        self.thc_max = thc_max
        self.cbd_min = cbd_min
        self.cbd_max = cbd_max

        # Create cannabinoid range value object
        cannabinoid_range = CannabinoidRange(
            thc_min=thc_min,
            thc_max=thc_max,
            cbd_min=cbd_min,
            cbd_max=cbd_max
        )

        # Update product attributes
        if self.product_attributes:
            self.product_attributes = ProductAttributes(
                product_form=self.product_attributes.product_form,
                cannabinoid_range=cannabinoid_range,
                terpene_profile=self.product_attributes.terpene_profile,
                volume_ml=self.product_attributes.volume_ml,
                pieces=self.product_attributes.pieces,
                unit_of_measure=self.product_attributes.unit_of_measure,
                allergens=self.product_attributes.allergens,
                ingredients=self.product_attributes.ingredients
            )

        self.mark_as_modified()

    def set_terpene_profile(
        self,
        primary_terpenes: List[str],
        terpene_percentages: Optional[Dict[str, Decimal]] = None,
        aroma_notes: Optional[List[str]] = None,
        flavor_notes: Optional[List[str]] = None
    ):
        """Set terpene profile"""
        self.terpene_profile = TerpeneProfile(
            primary_terpenes=primary_terpenes,
            terpene_percentages=terpene_percentages,
            aroma_notes=aroma_notes,
            flavor_notes=flavor_notes
        )
        self.mark_as_modified()

    def set_plant_type(self, plant_type_str: str):
        """Set plant type from string"""
        self.plant_type = PlantType.from_string(plant_type_str)
        self.mark_as_modified()

    def update_pricing(
        self,
        price_per_unit: Optional[Decimal] = None,
        msrp_price: Optional[Decimal] = None
    ):
        """Update product pricing"""
        changes = {}

        if price_per_unit is not None:
            if price_per_unit < 0:
                raise BusinessRuleViolation("Price per unit cannot be negative")
            changes['price_per_unit'] = {'old': self.price_per_unit, 'new': price_per_unit}
            self.price_per_unit = price_per_unit

        if msrp_price is not None:
            if msrp_price < 0:
                raise BusinessRuleViolation("MSRP cannot be negative")
            changes['msrp_price'] = {'old': self.msrp_price, 'new': msrp_price}
            self.msrp_price = msrp_price

        if changes:
            self.add_domain_event(OcsProductUpdated(
                ocs_variant_number=self.ocs_variant_number,
                changes=changes
            ))
            self.mark_as_modified()

    def update_availability(self, is_available: bool):
        """Update product availability"""
        if self.is_available != is_available:
            self.is_available = is_available
            self.mark_as_modified()

    def activate(self):
        """Activate the product"""
        if not self.is_active:
            self.is_active = True
            self.discontinued = False
            self.discontinued_date = None
            self.add_domain_event(OcsProductActivated(
                ocs_variant_number=self.ocs_variant_number
            ))
            self.mark_as_modified()

    def deactivate(self, reason: str = ""):
        """Deactivate the product"""
        if self.is_active:
            self.is_active = False
            self.add_domain_event(OcsProductDeactivated(
                ocs_variant_number=self.ocs_variant_number,
                reason=reason
            ))
            self.mark_as_modified()

    def discontinue(self):
        """Mark product as discontinued"""
        self.discontinued = True
        self.discontinued_date = datetime.utcnow()
        self.is_active = False
        self.is_available = False
        self.add_domain_event(OcsProductDeactivated(
            ocs_variant_number=self.ocs_variant_number,
            reason="Product discontinued"
        ))
        self.mark_as_modified()

    def update_from_import(self, import_data: Dict[str, Any]):
        """Update product from import data"""
        changes = {}

        # Update fields that have changed
        updateable_fields = [
            'ocs_product_name', 'product_name', 'brand_name', 'subcategory',
            'thc_min', 'thc_max', 'cbd_min', 'cbd_max', 'total_mg',
            'volume_ml', 'pieces', 'unit_of_measure', 'price_per_unit',
            'msrp_price', 'description', 'image_url', 'allergens', 'ingredients'
        ]

        for field in updateable_fields:
            if field in import_data and hasattr(self, field):
                old_value = getattr(self, field)
                new_value = import_data[field]
                if old_value != new_value:
                    changes[field] = {'old': old_value, 'new': new_value}
                    setattr(self, field, new_value)

        if changes:
            self.last_import_date = datetime.utcnow()
            self.add_domain_event(OcsProductUpdated(
                ocs_variant_number=self.ocs_variant_number,
                changes=changes
            ))
            self.mark_as_modified()

    def is_high_thc(self) -> bool:
        """Check if this is a high-THC product"""
        return self.thc_max is not None and self.thc_max > Decimal("20")

    def is_high_cbd(self) -> bool:
        """Check if this is a high-CBD product"""
        return self.cbd_max is not None and self.cbd_max > Decimal("10")

    def is_balanced(self) -> bool:
        """Check if THC:CBD ratio is balanced"""
        if not (self.thc_max and self.cbd_max and self.cbd_max > 0):
            return False
        ratio = self.thc_max / self.cbd_max
        return Decimal("0.5") <= ratio <= Decimal("2")

    def get_potency_level(self) -> str:
        """Get potency level description"""
        if self.thc_max is None:
            return "Unknown"
        if self.thc_max < Decimal("10"):
            return "Mild"
        elif self.thc_max < Decimal("17"):
            return "Medium"
        elif self.thc_max < Decimal("22"):
            return "Strong"
        else:
            return "Very Strong"

    def get_price_per_gram(self) -> Optional[Decimal]:
        """Calculate price per gram"""
        if not self.price_per_unit or not self.unit_of_measure:
            return None

        if self.unit_of_measure.lower() == 'g':
            return self.price_per_unit
        elif self.unit_of_measure.lower() == 'unit' and self.volume_ml:
            # Assume 1g = 1ml for oils (approximate)
            return self.price_per_unit / self.volume_ml

        return None

    def matches_search(self, search_term: str) -> bool:
        """Check if product matches search term"""
        search_lower = search_term.lower()
        searchable_fields = [
            self.ocs_variant_number,
            self.ocs_product_name,
            self.product_name,
            self.brand_name,
            self.subcategory,
            self.description
        ]

        return any(
            field and search_lower in field.lower()
            for field in searchable_fields
        )

    def validate(self) -> List[str]:
        """Validate product data"""
        errors = []

        if not self.ocs_variant_number:
            errors.append("OCS variant number is required")

        if not self.product_name and not self.ocs_product_name:
            errors.append("Product name is required")

        if not self.brand_name:
            errors.append("Brand name is required")

        if self.thc_min and self.thc_max:
            if self.thc_min > self.thc_max:
                errors.append("THC min cannot be greater than THC max")

        if self.cbd_min and self.cbd_max:
            if self.cbd_min > self.cbd_max:
                errors.append("CBD min cannot be greater than CBD max")

        if self.price_per_unit and self.price_per_unit < 0:
            errors.append("Price per unit cannot be negative")

        if self.msrp_price and self.msrp_price < 0:
            errors.append("MSRP cannot be negative")

        if self.pieces and self.pieces < 0:
            errors.append("Pieces count cannot be negative")

        if self.volume_ml and self.volume_ml < 0:
            errors.append("Volume cannot be negative")

        return errors

    def to_catalog_display(self) -> Dict[str, Any]:
        """Convert to catalog display format"""
        return {
            'sku': self.ocs_variant_number,
            'name': self.product_name or self.ocs_product_name,
            'brand': self.brand_name,
            'category': self.subcategory,
            'plant_type': self.plant_type.to_display_string() if self.plant_type else None,
            'thc_range': f"{self.thc_min or 0}-{self.thc_max or 0}%",
            'cbd_range': f"{self.cbd_min or 0}-{self.cbd_max or 0}%",
            'potency': self.get_potency_level(),
            'price': float(self.price_per_unit) if self.price_per_unit else None,
            'msrp': float(self.msrp_price) if self.msrp_price else None,
            'image': self.image_url,
            'available': self.is_available,
            'discontinued': self.discontinued
        }