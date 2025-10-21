"""
OCR Extraction System

Complete OCR extraction system with runtime provider discovery,
multiple extraction strategies, and template-based data extraction.

Following Design Principles:
- DDD (Domain-Driven Design): Layered architecture
- DRY (Don't Repeat Yourself): Reusable components
- KISS (Keep It Simple, Stupid): Clean interfaces
- SRP (Single Responsibility Principle): Focused classes

Quick Start:
    from services.ocr_extraction import (
        ocr_service,
        accessory_extractor,
        ACCESSORY_TEMPLATE
    )

    # Initialize (auto-discovers models and providers)
    await ocr_service.initialize()

    # Extract accessory details from photo
    result = await accessory_extractor.extract_from_file('/path/to/photo.jpg')

    print(f"Product: {result.extracted_data['product_name']}")
    print(f"Brand: {result.extracted_data['brand']}")
    print(f"Confidence: {result.get_overall_confidence():.2f}")

Advanced Usage:
    from services.ocr_extraction import (
        ocr_service,
        Document,
        ExtractionOptions,
        ORDER_TEMPLATE
    )

    # Create document
    document = Document(file_path='/path/to/po.pdf')

    # Custom extraction options
    options = ExtractionOptions(
        strategy='hybrid',  # Use hybrid strategy
        max_retries=3,
        timeout_seconds=60
    )

    # Extract using specific template
    result = await ocr_service.extract(document, ORDER_TEMPLATE, options)

Architecture Layers:
    1. Domain Layer (enums, exceptions, value objects, entities)
    2. Infrastructure Layer (providers, model discovery)
    3. Strategy Layer (local, cloud, hybrid strategies)
    4. Application Layer (services, templates, extractors)

Free Providers Only:
    - Ollama (local, unlimited)
    - Hugging Face Transformers (local, unlimited)
    - Google Gemini 2.0 Flash (cloud, 1500/day free tier)
"""

# Domain layer
from .domain.enums import (
    TemplateType,
    FieldType,
    ProviderType,
    StrategyType,
    ConfidenceLevel,
    ValidationSeverity
)
from .domain.exceptions import (
    OCRExtractionError,
    ExtractionError,
    ProviderError,
    ProviderUnavailableError,
    RateLimitError,
    ValidationError,
    FieldValidationError,
    TemplateNotFoundError,
    AllProvidersExhaustedError
)
from .domain.value_objects import (
    Field,
    Template,
    ExtractionOptions,
    VisionProviderConfig
)
from .domain.entities import (
    Document,
    ExtractionResult,
    AvailableModel
)

# Templates
from .templates import (
    ACCESSORY_TEMPLATE,
    ORDER_TEMPLATE,
    template_registry
)

# Services
from .services import (
    ocr_service,
    OCRExtractionService,
    ModelDiscoveryService,
    ValidationService
)

# Extractors (Application Layer)
from .extractors import (
    accessory_extractor,
    order_extractor,
    AccessoryExtractor,
    OrderExtractor
)

# Version
__version__ = '1.0.0'

__all__ = [
    # === HIGH-LEVEL API (most users need only these) ===

    # Main service (auto-discovery + orchestration)
    'ocr_service',

    # Domain-specific extractors
    'accessory_extractor',
    'order_extractor',

    # Pre-built templates
    'ACCESSORY_TEMPLATE',
    'ORDER_TEMPLATE',

    # === DOMAIN LAYER ===

    # Entities
    'Document',
    'ExtractionResult',
    'AvailableModel',

    # Value Objects
    'Field',
    'Template',
    'ExtractionOptions',
    'VisionProviderConfig',

    # Enums
    'TemplateType',
    'FieldType',
    'ProviderType',
    'StrategyType',
    'ConfidenceLevel',
    'ValidationSeverity',

    # Exceptions
    'OCRExtractionError',
    'ExtractionError',
    'ProviderError',
    'ProviderUnavailableError',
    'RateLimitError',
    'ValidationError',
    'FieldValidationError',
    'TemplateNotFoundError',
    'AllProvidersExhaustedError',

    # === SERVICES ===

    'OCRExtractionService',
    'ModelDiscoveryService',
    'ValidationService',

    # === EXTRACTORS ===

    'AccessoryExtractor',
    'OrderExtractor',

    # === TEMPLATES ===

    'template_registry',

    # === METADATA ===

    '__version__',
]
