"""
OCR Extraction - Application Layer Extractors

Domain-specific extractors with convenient interfaces.

Available Extractors:
- AccessoryExtractor: Extract product details from accessory photos
- OrderExtractor: Extract purchase order details from documents

Usage:
    from services.ocr_extraction.extractors import (
        accessory_extractor,
        order_extractor
    )

    # Initialize OCR service first
    from services.ocr_extraction import ocr_service
    await ocr_service.initialize()

    # Extract accessory details
    result = await accessory_extractor.extract_from_file('/path/to/photo.jpg')

    # Extract order details
    result = await order_extractor.extract_from_file('/path/to/po.pdf')
"""

from .accessory_extractor import AccessoryExtractor, accessory_extractor
from .order_extractor import OrderExtractor, order_extractor

__all__ = [
    # Extractor classes
    'AccessoryExtractor',
    'OrderExtractor',

    # Global instances (use these!)
    'accessory_extractor',
    'order_extractor',
]
