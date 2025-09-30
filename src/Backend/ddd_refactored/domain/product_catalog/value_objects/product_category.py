"""
Product Category Value Objects
Following DDD Architecture Document Section 2.3
"""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

from ....shared.domain_base import ValueObject


class CategoryType(str, Enum):
    """Main product categories"""
    CANNABIS = "cannabis"
    ACCESSORIES = "accessories"
    MERCHANDISE = "merchandise"
    WELLNESS = "wellness"


@dataclass(frozen=True)
class Category(ValueObject):
    """
    Category Value Object - Main product category
    Immutable value object for product categorization
    """
    name: str
    code: str
    type: CategoryType
    description: Optional[str] = None

    @classmethod
    def cannabis(cls, name: str, code: str, description: Optional[str] = None) -> 'Category':
        """Create a cannabis category"""
        return cls(
            name=name,
            code=code,
            type=CategoryType.CANNABIS,
            description=description
        )

    @classmethod
    def accessories(cls, name: str, code: str, description: Optional[str] = None) -> 'Category':
        """Create an accessories category"""
        return cls(
            name=name,
            code=code,
            type=CategoryType.ACCESSORIES,
            description=description
        )

    def is_cannabis(self) -> bool:
        """Check if this is a cannabis category"""
        return self.type == CategoryType.CANNABIS

    def is_accessories(self) -> bool:
        """Check if this is an accessories category"""
        return self.type == CategoryType.ACCESSORIES

    def get_display_name(self) -> str:
        """Get formatted display name"""
        return self.name.title()

    def matches_code(self, code: str) -> bool:
        """Check if category matches the given code"""
        return self.code.lower() == code.lower()

    def __str__(self) -> str:
        return self.get_display_name()


@dataclass(frozen=True)
class SubCategory(ValueObject):
    """
    SubCategory Value Object - Product subcategory
    Immutable value object for secondary categorization
    """
    name: str
    code: str
    parent_category: Category
    description: Optional[str] = None
    sort_order: int = 0

    @classmethod
    def create_cannabis_subcategory(
        cls,
        name: str,
        code: str,
        parent_category: Category,
        description: Optional[str] = None,
        sort_order: int = 0
    ) -> 'SubCategory':
        """Create a cannabis subcategory"""
        if not parent_category.is_cannabis():
            raise ValueError("Parent category must be a cannabis category")
        return cls(
            name=name,
            code=code,
            parent_category=parent_category,
            description=description,
            sort_order=sort_order
        )

    def get_full_path(self) -> str:
        """Get full category path"""
        return f"{self.parent_category.code}/{self.code}"

    def get_display_name(self) -> str:
        """Get formatted display name"""
        return self.name.title()

    def matches_code(self, code: str) -> bool:
        """Check if subcategory matches the given code"""
        return self.code.lower() == code.lower()

    def is_flower_category(self) -> bool:
        """Check if this is a flower-related subcategory"""
        flower_codes = ['dried_flower', 'pre_roll', 'milled', 'shake']
        return self.code.lower() in flower_codes

    def is_extract_category(self) -> bool:
        """Check if this is an extract/concentrate subcategory"""
        extract_codes = ['oil', 'concentrate', 'extract', 'resin', 'rosin', 'hash']
        return self.code.lower() in extract_codes

    def is_edible_category(self) -> bool:
        """Check if this is an edible subcategory"""
        edible_codes = ['edible', 'beverage', 'chocolate', 'gummy', 'candy', 'baked']
        return any(code in self.code.lower() for code in edible_codes)

    def is_vape_category(self) -> bool:
        """Check if this is a vape subcategory"""
        vape_codes = ['vape', 'cartridge', 'pod', 'pen']
        return any(code in self.code.lower() for code in vape_codes)

    def __str__(self) -> str:
        return f"{self.parent_category} > {self.get_display_name()}"


@dataclass(frozen=True)
class SubSubCategory(ValueObject):
    """
    SubSubCategory Value Object - Tertiary product categorization
    Immutable value object for detailed product classification
    """
    name: str
    code: str
    parent_subcategory: SubCategory
    description: Optional[str] = None
    attributes: Optional[List[str]] = None
    sort_order: int = 0

    def get_full_path(self) -> str:
        """Get full category path"""
        return f"{self.parent_subcategory.get_full_path()}/{self.code}"

    def get_display_name(self) -> str:
        """Get formatted display name"""
        return self.name.title()

    def get_breadcrumb(self) -> List[str]:
        """Get category breadcrumb trail"""
        return [
            self.parent_subcategory.parent_category.get_display_name(),
            self.parent_subcategory.get_display_name(),
            self.get_display_name()
        ]

    def matches_code(self, code: str) -> bool:
        """Check if sub-subcategory matches the given code"""
        return self.code.lower() == code.lower()

    def has_attribute(self, attribute: str) -> bool:
        """Check if category has a specific attribute"""
        if not self.attributes:
            return False
        return attribute.lower() in [attr.lower() for attr in self.attributes]

    def get_all_codes(self) -> List[str]:
        """Get all category codes in hierarchy"""
        return [
            self.parent_subcategory.parent_category.code,
            self.parent_subcategory.code,
            self.code
        ]

    def is_premium_category(self) -> bool:
        """Check if this is a premium product category"""
        premium_indicators = ['craft', 'premium', 'reserve', 'top-shelf', 'small-batch']
        return any(indicator in self.code.lower() for indicator in premium_indicators)

    def is_value_category(self) -> bool:
        """Check if this is a value/budget category"""
        value_indicators = ['value', 'budget', 'daily', 'economy']
        return any(indicator in self.code.lower() for indicator in value_indicators)

    def __str__(self) -> str:
        breadcrumb = " > ".join(self.get_breadcrumb())
        return breadcrumb


# Common predefined categories
class CommonCategories:
    """Commonly used product categories"""

    # Main Categories
    CANNABIS = Category.cannabis("Cannabis", "cannabis", "All cannabis products")
    ACCESSORIES = Category.accessories("Accessories", "accessories", "Smoking and vaping accessories")

    # Cannabis Subcategories
    DRIED_FLOWER = SubCategory(
        name="Dried Flower",
        code="dried_flower",
        parent_category=CANNABIS,
        description="Dried cannabis flower",
        sort_order=1
    )

    PRE_ROLLS = SubCategory(
        name="Pre-Rolls",
        code="pre_rolls",
        parent_category=CANNABIS,
        description="Pre-rolled joints",
        sort_order=2
    )

    OILS = SubCategory(
        name="Oils",
        code="oils",
        parent_category=CANNABIS,
        description="Cannabis oils and tinctures",
        sort_order=3
    )

    EDIBLES = SubCategory(
        name="Edibles",
        code="edibles",
        parent_category=CANNABIS,
        description="Cannabis-infused food products",
        sort_order=4
    )

    VAPES = SubCategory(
        name="Vapes",
        code="vapes",
        parent_category=CANNABIS,
        description="Vaporizer cartridges and disposables",
        sort_order=5
    )

    CONCENTRATES = SubCategory(
        name="Concentrates",
        code="concentrates",
        parent_category=CANNABIS,
        description="Cannabis concentrates and extracts",
        sort_order=6
    )

    # Accessory Subcategories
    VAPORIZERS = SubCategory(
        name="Vaporizers",
        code="vaporizers",
        parent_category=ACCESSORIES,
        description="Vaporizer devices",
        sort_order=1
    )

    PAPERS_WRAPS = SubCategory(
        name="Papers & Wraps",
        code="papers_wraps",
        parent_category=ACCESSORIES,
        description="Rolling papers and wraps",
        sort_order=2
    )

    GRINDERS = SubCategory(
        name="Grinders",
        code="grinders",
        parent_category=ACCESSORIES,
        description="Herb grinders",
        sort_order=3
    )

    STORAGE = SubCategory(
        name="Storage",
        code="storage",
        parent_category=ACCESSORIES,
        description="Storage containers and solutions",
        sort_order=4
    )