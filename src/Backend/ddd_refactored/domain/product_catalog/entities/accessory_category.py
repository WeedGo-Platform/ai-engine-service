"""
AccessoryCategory Entity
Following DDD Architecture Document Section 2.3
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from ....shared.domain_base import Entity, BusinessRuleViolation


@dataclass
class AccessoryCategory(Entity):
    """
    AccessoryCategory Entity - Categories for accessories
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.3
    """
    # Identifiers
    name: str = ""
    slug: str = ""  # URL-friendly identifier

    # Hierarchy
    parent_category_id: Optional[UUID] = None  # For hierarchical categories
    level: int = 0  # 0 for root, 1 for child, etc.
    path: str = ""  # Full path like "accessories/vaporizers/portable"

    # Display
    description: Optional[str] = None
    image_url: Optional[str] = None
    icon: Optional[str] = None  # Icon class or SVG
    color: Optional[str] = None  # Color theme for UI

    # Organization
    sort_order: int = 0
    display_in_menu: bool = True
    display_in_sidebar: bool = True
    display_on_homepage: bool = False

    # Status
    is_active: bool = True
    is_featured: bool = False

    # Product Management
    product_count: int = 0  # Cached count of products
    min_age_requirement: Optional[int] = None  # Age requirement if any

    # SEO
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    seo_keywords: List[str] = field(default_factory=list)

    # Attributes
    required_attributes: List[str] = field(default_factory=list)  # Required product attributes
    optional_attributes: List[str] = field(default_factory=list)  # Optional product attributes
    filter_attributes: List[str] = field(default_factory=list)  # Attributes for filtering

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create_root(
        cls,
        name: str,
        description: Optional[str] = None,
        sort_order: int = 0
    ) -> 'AccessoryCategory':
        """Factory method to create root category"""
        if not name:
            raise BusinessRuleViolation("Category name is required")

        category = cls(
            name=name,
            description=description,
            sort_order=sort_order,
            level=0
        )

        category.slug = category.generate_slug(name)
        category.path = category.slug

        return category

    @classmethod
    def create_child(
        cls,
        name: str,
        parent_category_id: UUID,
        parent_path: str,
        parent_level: int,
        description: Optional[str] = None,
        sort_order: int = 0
    ) -> 'AccessoryCategory':
        """Factory method to create child category"""
        if not name:
            raise BusinessRuleViolation("Category name is required")
        if not parent_category_id:
            raise BusinessRuleViolation("Parent category is required for child categories")

        category = cls(
            name=name,
            parent_category_id=parent_category_id,
            description=description,
            sort_order=sort_order,
            level=parent_level + 1
        )

        category.slug = category.generate_slug(name)
        category.path = f"{parent_path}/{category.slug}"

        return category

    @staticmethod
    def generate_slug(name: str) -> str:
        """Generate URL-friendly slug from name"""
        import re
        slug = name.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')

    def update_info(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        image_url: Optional[str] = None,
        icon: Optional[str] = None
    ):
        """Update category information"""
        if name and name != self.name:
            self.name = name
            self.slug = self.generate_slug(name)
            # Update path if name changed
            if self.parent_category_id:
                path_parts = self.path.split('/')
                path_parts[-1] = self.slug
                self.path = '/'.join(path_parts)
            else:
                self.path = self.slug

        if description is not None:
            self.description = description

        if image_url is not None:
            self.image_url = image_url

        if icon is not None:
            self.icon = icon

        self.mark_as_modified()

    def update_display_settings(
        self,
        display_in_menu: Optional[bool] = None,
        display_in_sidebar: Optional[bool] = None,
        display_on_homepage: Optional[bool] = None,
        sort_order: Optional[int] = None
    ):
        """Update display settings"""
        if display_in_menu is not None:
            self.display_in_menu = display_in_menu

        if display_in_sidebar is not None:
            self.display_in_sidebar = display_in_sidebar

        if display_on_homepage is not None:
            self.display_on_homepage = display_on_homepage

        if sort_order is not None:
            if sort_order < 0:
                raise BusinessRuleViolation("Sort order cannot be negative")
            self.sort_order = sort_order

        self.mark_as_modified()

    def add_required_attribute(self, attribute: str):
        """Add required attribute for products in this category"""
        normalized = attribute.lower().strip()
        if normalized and normalized not in self.required_attributes:
            self.required_attributes.append(normalized)
            self.mark_as_modified()

    def remove_required_attribute(self, attribute: str):
        """Remove required attribute"""
        normalized = attribute.lower().strip()
        if normalized in self.required_attributes:
            self.required_attributes.remove(normalized)
            self.mark_as_modified()

    def add_optional_attribute(self, attribute: str):
        """Add optional attribute for products in this category"""
        normalized = attribute.lower().strip()
        if normalized and normalized not in self.optional_attributes:
            self.optional_attributes.append(normalized)
            self.mark_as_modified()

    def remove_optional_attribute(self, attribute: str):
        """Remove optional attribute"""
        normalized = attribute.lower().strip()
        if normalized in self.optional_attributes:
            self.optional_attributes.remove(normalized)
            self.mark_as_modified()

    def add_filter_attribute(self, attribute: str):
        """Add attribute for filtering"""
        normalized = attribute.lower().strip()
        if normalized and normalized not in self.filter_attributes:
            self.filter_attributes.append(normalized)
            self.mark_as_modified()

    def remove_filter_attribute(self, attribute: str):
        """Remove filter attribute"""
        normalized = attribute.lower().strip()
        if normalized in self.filter_attributes:
            self.filter_attributes.remove(normalized)
            self.mark_as_modified()

    def update_seo(
        self,
        seo_title: Optional[str] = None,
        seo_description: Optional[str] = None,
        seo_keywords: Optional[List[str]] = None
    ):
        """Update SEO metadata"""
        if seo_title is not None:
            self.seo_title = seo_title

        if seo_description is not None:
            self.seo_description = seo_description

        if seo_keywords is not None:
            self.seo_keywords = seo_keywords

        self.mark_as_modified()

    def set_age_requirement(self, min_age: Optional[int]):
        """Set minimum age requirement"""
        if min_age is not None and min_age < 0:
            raise BusinessRuleViolation("Minimum age cannot be negative")
        self.min_age_requirement = min_age
        self.mark_as_modified()

    def feature(self):
        """Mark category as featured"""
        self.is_featured = True
        self.mark_as_modified()

    def unfeature(self):
        """Remove featured status"""
        self.is_featured = False
        self.mark_as_modified()

    def activate(self):
        """Activate the category"""
        self.is_active = True
        self.mark_as_modified()

    def deactivate(self):
        """Deactivate the category"""
        self.is_active = False
        self.mark_as_modified()

    def increment_product_count(self):
        """Increment product count"""
        self.product_count += 1
        self.mark_as_modified()

    def decrement_product_count(self):
        """Decrement product count"""
        if self.product_count > 0:
            self.product_count -= 1
            self.mark_as_modified()

    def update_product_count(self, count: int):
        """Update product count"""
        if count < 0:
            raise BusinessRuleViolation("Product count cannot be negative")
        self.product_count = count
        self.mark_as_modified()

    def get_breadcrumb(self) -> List[str]:
        """Get category breadcrumb trail"""
        return self.path.split('/')

    def get_depth(self) -> int:
        """Get category depth in hierarchy"""
        return self.level

    def is_root(self) -> bool:
        """Check if this is a root category"""
        return self.parent_category_id is None

    def is_leaf(self) -> bool:
        """Check if this is a leaf category (no children)"""
        # This would need to be determined by checking if any categories have this as parent
        return True  # Placeholder

    def get_full_name(self) -> str:
        """Get full category name with hierarchy"""
        breadcrumb = self.get_breadcrumb()
        return ' > '.join(breadcrumb)

    def matches_search(self, search_term: str) -> bool:
        """Check if category matches search term"""
        search_lower = search_term.lower()
        searchable_fields = [
            self.name,
            self.description,
            self.path
        ]
        searchable_fields.extend(self.seo_keywords)

        return any(
            field and search_lower in field.lower()
            for field in searchable_fields
        )

    def validate(self) -> List[str]:
        """Validate category data"""
        errors = []

        if not self.name:
            errors.append("Category name is required")

        if not self.slug:
            errors.append("Category slug is required")

        if self.level < 0:
            errors.append("Category level cannot be negative")

        if self.sort_order < 0:
            errors.append("Sort order cannot be negative")

        if self.product_count < 0:
            errors.append("Product count cannot be negative")

        if self.min_age_requirement and self.min_age_requirement < 0:
            errors.append("Minimum age cannot be negative")

        # Validate hierarchy
        if self.level > 0 and not self.parent_category_id:
            errors.append("Child categories must have a parent")

        if self.level == 0 and self.parent_category_id:
            errors.append("Root categories cannot have a parent")

        return errors

    def to_menu_item(self) -> Dict[str, Any]:
        """Convert to menu item format"""
        return {
            'id': str(self.id),
            'name': self.name,
            'slug': self.slug,
            'path': self.path,
            'icon': self.icon,
            'color': self.color,
            'level': self.level,
            'parent_category_id': str(self.parent_category_id) if self.parent_category_id else None,
            'product_count': self.product_count,
            'featured': self.is_featured,
            'active': self.is_active
        }