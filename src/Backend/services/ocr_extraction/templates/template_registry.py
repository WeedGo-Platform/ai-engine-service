"""
Template Registry

Centralized registry for all extraction templates.
Following DRY: Single source of truth for templates.
Following SRP: Only manages template collection.
"""

import logging
from typing import Dict, List, Optional

from ..domain.value_objects import Template
from ..domain.enums import TemplateType
from ..domain.exceptions import TemplateNotFoundError

logger = logging.getLogger(__name__)


class TemplateRegistry:
    """
    Registry for extraction templates

    Provides centralized access to all pre-built templates.
    Templates can be looked up by name or type.

    Usage:
        from templates.template_registry import template_registry

        # Get template by name
        template = template_registry.get_by_name('accessory_extraction')

        # Get all templates of a type
        templates = template_registry.get_by_type(TemplateType.ORDER)

        # Register custom template
        template_registry.register(my_custom_template)
    """

    def __init__(self):
        """Initialize empty registry"""
        self._templates: Dict[str, Template] = {}
        logger.info("Template registry initialized")

    def register(self, template: Template):
        """
        Register a template

        Args:
            template: Template to register

        Raises:
            ValueError: If template name already registered
        """
        if template.name in self._templates:
            raise ValueError(
                f"Template '{template.name}' already registered. "
                f"Use a different name or unregister first."
            )

        self._templates[template.name] = template
        logger.info(f"Registered template: {template.name} ({template.template_type.value})")

    def unregister(self, template_name: str):
        """
        Unregister a template

        Args:
            template_name: Name of template to remove
        """
        if template_name in self._templates:
            del self._templates[template_name]
            logger.info(f"Unregistered template: {template_name}")

    def get_by_name(self, name: str) -> Template:
        """
        Get template by name

        Args:
            name: Template name

        Returns:
            Template instance

        Raises:
            TemplateNotFoundError: If template not found
        """
        if name not in self._templates:
            raise TemplateNotFoundError(
                f"Template '{name}' not found. "
                f"Available: {', '.join(self._templates.keys())}"
            )

        return self._templates[name]

    def get_by_type(self, template_type: TemplateType) -> List[Template]:
        """
        Get all templates of a specific type

        Args:
            template_type: Type to filter by

        Returns:
            List of templates (may be empty)
        """
        return [
            template
            for template in self._templates.values()
            if template.template_type == template_type
        ]

    def get_all(self) -> List[Template]:
        """
        Get all registered templates

        Returns:
            List of all templates
        """
        return list(self._templates.values())

    def get_names(self) -> List[str]:
        """
        Get all template names

        Returns:
            List of template names
        """
        return list(self._templates.keys())

    def has_template(self, name: str) -> bool:
        """
        Check if template exists

        Args:
            name: Template name

        Returns:
            True if exists, False otherwise
        """
        return name in self._templates

    def count(self) -> int:
        """
        Get count of registered templates

        Returns:
            Number of templates
        """
        return len(self._templates)

    def get_stats(self) -> Dict[str, any]:
        """
        Get registry statistics

        Returns:
            Dictionary with stats
        """
        type_counts = {}
        for template in self._templates.values():
            type_name = template.template_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        return {
            'total_templates': self.count(),
            'templates_by_type': type_counts,
            'template_names': self.get_names(),
        }

    def __repr__(self):
        return f"TemplateRegistry(templates={self.count()})"


# Global registry instance
template_registry = TemplateRegistry()


def load_builtin_templates():
    """
    Load all built-in templates into global registry

    This is called automatically when module is imported.
    """
    from .accessory_template import ACCESSORY_TEMPLATE
    from .order_template import ORDER_TEMPLATE

    # Register built-in templates
    if not template_registry.has_template('accessory_extraction'):
        template_registry.register(ACCESSORY_TEMPLATE)

    if not template_registry.has_template('order_extraction'):
        template_registry.register(ORDER_TEMPLATE)

    logger.info(
        f"Loaded {template_registry.count()} built-in templates: "
        f"{', '.join(template_registry.get_names())}"
    )


# Auto-load on import
load_builtin_templates()
