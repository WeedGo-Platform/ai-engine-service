"""
OCR Extraction Domain Layer

Public API for domain objects.
Following DDD: Domain is the core of the system.
"""

from .enums import (
    TemplateType,
    FieldType,
    ProviderType,
    StrategyType,
    ConfidenceLevel,
    ValidationSeverity,
)

from .exceptions import (
    OCRExtractionError,
    ProviderError,
    ProviderUnavailableError,
    ProviderTimeoutError,
    RateLimitError,
    AllProvidersExhaustedError,
    TemplateError,
    TemplateNotFoundError,
    InvalidTemplateError,
    TemplateMismatchError,
    ValidationError,
    FieldValidationError,
    RequiredFieldMissingError,
    DocumentError,
    DocumentNotFoundError,
    InvalidDocumentError,
    UnsupportedDocumentTypeError,
    ExtractionError,
    ExtractionFailedError,
    LowConfidenceError,
    ImageProcessingError,
)

from .value_objects import (
    Field,
    Template,
    ExtractionOptions,
    VisionProviderConfig,
    ValidationRule,
)

from .entities import (
    Document,
    ExtractionResult,
    AvailableModel,
)

__all__ = [
    # Enums
    'TemplateType',
    'FieldType',
    'ProviderType',
    'StrategyType',
    'ConfidenceLevel',
    'ValidationSeverity',

    # Exceptions
    'OCRExtractionError',
    'ProviderError',
    'ProviderUnavailableError',
    'ProviderTimeoutError',
    'RateLimitError',
    'AllProvidersExhaustedError',
    'TemplateError',
    'TemplateNotFoundError',
    'InvalidTemplateError',
    'TemplateMismatchError',
    'ValidationError',
    'FieldValidationError',
    'RequiredFieldMissingError',
    'DocumentError',
    'DocumentNotFoundError',
    'InvalidDocumentError',
    'UnsupportedDocumentTypeError',
    'ExtractionError',
    'ExtractionFailedError',
    'LowConfidenceError',
    'ImageProcessingError',

    # Value Objects
    'Field',
    'Template',
    'ExtractionOptions',
    'VisionProviderConfig',
    'ValidationRule',

    # Entities
    'Document',
    'ExtractionResult',
    'AvailableModel',
]
