"""
Value Objects for OCR Extraction System

Immutable objects representing concepts without identity.
Following DDD: Value objects are compared by value, not identity.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Pattern
import re

from .enums import TemplateType, FieldType, ProviderType, StrategyType


@dataclass(frozen=True)
class Field:
    """
    Defines a single field to extract from document

    Value Object: Immutable specification of what to extract.
    Two fields with same values are considered equal.
    """
    name: str
    field_type: FieldType
    description: str
    required: bool = True
    example: Optional[str] = None
    validation_pattern: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[str]] = None

    def __post_init__(self):
        """Validate field definition"""
        if not self.name:
            raise ValueError("Field name cannot be empty")

        if not self.description:
            raise ValueError(f"Field '{self.name}' must have a description")

        # Validate pattern if provided
        if self.validation_pattern:
            try:
                re.compile(self.validation_pattern)
            except re.error as e:
                raise ValueError(
                    f"Invalid regex pattern for field '{self.name}': {e}"
                )

        # Validate min/max if provided
        if self.min_value is not None and self.max_value is not None:
            if self.min_value > self.max_value:
                raise ValueError(
                    f"Field '{self.name}': min_value ({self.min_value}) "
                    f"cannot be greater than max_value ({self.max_value})"
                )

    def validate_value(self, value: Any) -> tuple[bool, Optional[str]]:
        """
        Validate a value against this field's rules

        Args:
            value: Value to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required
        if self.required and value is None:
            return False, f"Field '{self.name}' is required"

        # If not required and None, it's valid
        if value is None:
            return True, None

        # Type-specific validation
        if self.field_type == FieldType.NUMBER:
            if not isinstance(value, (int, float)):
                return False, f"Expected number, got {type(value).__name__}"

            if self.min_value is not None and value < self.min_value:
                return False, f"Value {value} below minimum {self.min_value}"

            if self.max_value is not None and value > self.max_value:
                return False, f"Value {value} above maximum {self.max_value}"

        elif self.field_type == FieldType.PRICE:
            if not isinstance(value, (int, float)):
                return False, f"Price must be numeric, got {type(value).__name__}"
            if value < 0:
                return False, "Price cannot be negative"

        elif self.field_type in (FieldType.TEXT, FieldType.BARCODE, FieldType.CATEGORY):
            if not isinstance(value, str):
                return False, f"Expected string, got {type(value).__name__}"

        # Pattern validation
        if self.validation_pattern and isinstance(value, str):
            if not re.match(self.validation_pattern, value):
                return False, f"Value doesn't match pattern: {self.validation_pattern}"

        # Allowed values check
        if self.allowed_values and value not in self.allowed_values:
            return False, f"Value must be one of: {', '.join(map(str, self.allowed_values))}"

        return True, None


@dataclass(frozen=True)
class Template:
    """
    Defines extraction schema for a document type

    Value Object: Immutable template specifying what data to extract
    and how to validate it.
    """
    name: str
    template_type: TemplateType
    description: str
    fields: tuple[Field, ...]  # Tuple for immutability
    prompt_template: str
    output_schema: str  # JSON schema

    def __post_init__(self):
        """Validate template"""
        if not self.name:
            raise ValueError("Template name cannot be empty")

        if not self.fields:
            raise ValueError("Template must have at least one field")

        if not self.prompt_template:
            raise ValueError("Template must have a prompt template")

    @property
    def required_fields(self) -> List[Field]:
        """Get list of required fields"""
        return [f for f in self.fields if f.required]

    @property
    def optional_fields(self) -> List[Field]:
        """Get list of optional fields"""
        return [f for f in self.fields if not f.required]

    def get_field(self, name: str) -> Optional[Field]:
        """Get field by name"""
        for field_obj in self.fields:
            if field_obj.name == name:
                return field_obj
        return None

    def validate_data(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate extracted data against template

        Args:
            data: Extracted data dictionary

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check all fields
        for field_obj in self.fields:
            value = data.get(field_obj.name)
            is_valid, error_msg = field_obj.validate_value(value)

            if not is_valid:
                errors.append(error_msg)

        return len(errors) == 0, errors


@dataclass(frozen=True)
class ExtractionOptions:
    """
    Options for extraction process

    Value Object: Immutable configuration for a single extraction request.
    """
    # Provider selection
    strategy: StrategyType = StrategyType.AUTO
    preferred_provider: Optional[str] = None

    # Image processing
    resize_max_dimension: int = 1344  # MiniCPM-V max
    normalize: bool = True
    enhance_contrast: bool = False

    # Extraction behavior
    enable_cache: bool = True
    cache_ttl: int = 3600  # 1 hour
    max_retries: int = 3
    timeout_seconds: int = 30
    confidence_threshold: float = 0.75

    # Output formatting
    return_raw_text: bool = False
    return_confidence_scores: bool = True
    validate_output: bool = True

    # Debugging
    save_debug_info: bool = False
    debug_output_dir: Optional[str] = None

    def __post_init__(self):
        """Validate options"""
        if self.resize_max_dimension < 224:
            raise ValueError("resize_max_dimension must be at least 224")

        if self.cache_ttl < 0:
            raise ValueError("cache_ttl cannot be negative")

        if self.max_retries < 0:
            raise ValueError("max_retries cannot be negative")

        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise ValueError("confidence_threshold must be between 0.0 and 1.0")


@dataclass(frozen=True)
class VisionProviderConfig:
    """Configuration for a vision provider"""
    name: str
    provider_type: ProviderType
    model_name: str
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None

    # Capabilities
    supports_tables: bool = True
    supports_handwriting: bool = False
    supports_multilingual: bool = True
    max_languages: int = 1

    # Performance
    max_image_size_mb: int = 20
    cost_per_image: float = 0.0
    avg_latency_seconds: float = 5.0

    # Rate limits (free tier)
    max_requests_per_minute: Optional[int] = None
    max_requests_per_day: Optional[int] = None

    def __post_init__(self):
        """Validate configuration"""
        if not self.name:
            raise ValueError("Provider name cannot be empty")

        if not self.model_name:
            raise ValueError("Model name cannot be empty")

        if self.max_image_size_mb <= 0:
            raise ValueError("max_image_size_mb must be positive")

        if self.cost_per_image < 0:
            raise ValueError("cost_per_image cannot be negative")

    @property
    def is_free(self) -> bool:
        """Check if provider is free"""
        return self.cost_per_image == 0.0

    @property
    def has_rate_limits(self) -> bool:
        """Check if provider has rate limits"""
        return (
            self.max_requests_per_minute is not None or
            self.max_requests_per_day is not None
        )


@dataclass(frozen=True)
class ValidationRule:
    """
    Defines a validation rule for extracted data

    Value Object: Immutable rule specification.
    """
    field_name: str
    rule_type: str  # 'required', 'pattern', 'range', 'custom'
    rule_value: Any
    error_message: str
    severity: str = "error"  # 'error', 'warning', 'info'

    def __post_init__(self):
        """Validate rule"""
        if not self.field_name:
            raise ValueError("Validation rule must specify field_name")

        if not self.rule_type:
            raise ValueError("Validation rule must specify rule_type")

        if self.severity not in ('error', 'warning', 'info'):
            raise ValueError("Severity must be 'error', 'warning', or 'info'")
