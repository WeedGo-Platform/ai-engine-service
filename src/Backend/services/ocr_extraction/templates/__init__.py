"""
OCR Extraction Templates

Pre-built extraction templates for common document types.

Available Templates:
- AccessoryTemplate: Extract product details from accessory photos
- OrderTemplate: Extract purchase order details from documents

Usage:
    from services.ocr_extraction.templates import (
        ACCESSORY_TEMPLATE,
        ORDER_TEMPLATE,
        template_registry
    )

    # Use pre-built template
    result = await strategy.extract(document, ACCESSORY_TEMPLATE, options)

    # Or get from registry
    template = template_registry.get_by_name('accessory_extraction')

    # Register custom template
    template_registry.register(my_custom_template)
"""

from .accessory_template import ACCESSORY_TEMPLATE, create_accessory_template
from .order_template import ORDER_TEMPLATE, create_order_template
from .template_registry import TemplateRegistry, template_registry

__all__ = [
    # Pre-built template instances
    'ACCESSORY_TEMPLATE',
    'ORDER_TEMPLATE',

    # Template factory functions
    'create_accessory_template',
    'create_order_template',

    # Registry
    'TemplateRegistry',
    'template_registry',
]
