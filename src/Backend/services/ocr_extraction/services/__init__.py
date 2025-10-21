"""
OCR Extraction Services

Core services for the OCR extraction system.

Available Services:
- OCRExtractionService: Main orchestrator (use this!)
- ModelDiscoveryService: Runtime model discovery
- ValidationService: Data validation

Usage:
    from services.ocr_extraction.services import ocr_service

    # Initialize (auto-discovers models and providers)
    await ocr_service.initialize()

    # Extract data
    result = await ocr_service.extract(document, template, options)
"""

from .model_discovery import ModelDiscoveryService, DiscoveryResult
from .validation_service import ValidationService, ValidationResult
from .ocr_extraction_service import OCRExtractionService, ocr_service

__all__ = [
    # Main service (primary interface)
    'OCRExtractionService',
    'ocr_service',  # Global instance

    # Supporting services
    'ModelDiscoveryService',
    'ValidationService',

    # Result types
    'DiscoveryResult',
    'ValidationResult',
]
