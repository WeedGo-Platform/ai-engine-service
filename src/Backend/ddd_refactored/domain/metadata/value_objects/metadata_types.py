"""
Metadata Value Objects
Following DDD Architecture Document Section 2.15
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any, List

from ....shared.domain_base import ValueObject


class DataType(str, Enum):
    """Field data type"""
    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    JSON = "json"
    LIST = "list"


class ValidationRule(str, Enum):
    """Validation rule type"""
    REQUIRED = "required"
    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    MIN_VALUE = "min_value"
    MAX_VALUE = "max_value"
    REGEX = "regex"
    ENUM = "enum"


@dataclass(frozen=True)
class FieldDefinition(ValueObject):
    """
    Definition of a custom field
    """
    field_name: str
    field_label: str
    data_type: DataType

    # Validation
    is_required: bool = False
    default_value: Optional[Any] = None

    # Constraints
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[tuple[str, ...]] = None  # For enum fields

    # UI hints
    help_text: Optional[str] = None
    placeholder: Optional[str] = None

    def __post_init__(self):
        """Validate field definition"""
        if not self.field_name:
            raise ValueError("Field name is required")

        if not self.field_label:
            raise ValueError("Field label is required")

        # Validate field name format
        if not self.field_name.replace('_', '').isalnum():
            raise ValueError("Field name must be alphanumeric with underscores")

        # Validate constraints
        if self.min_length is not None and self.min_length < 0:
            raise ValueError("Min length cannot be negative")

        if self.max_length is not None and self.max_length < 0:
            raise ValueError("Max length cannot be negative")

        if self.min_length and self.max_length and self.max_length < self.min_length:
            raise ValueError("Max length must be >= min length")

    def validate_value(self, value: Any) -> tuple[bool, Optional[str]]:
        """Validate a value against this field definition"""
        # Check required
        if self.is_required and value is None:
            return False, f"{self.field_label} is required"

        # If value is None and not required, it's valid
        if value is None:
            return True, None

        # Type validation
        if self.data_type == DataType.STRING:
            if not isinstance(value, str):
                return False, f"{self.field_label} must be a string"

            if self.min_length and len(value) < self.min_length:
                return False, f"{self.field_label} must be at least {self.min_length} characters"

            if self.max_length and len(value) > self.max_length:
                return False, f"{self.field_label} must be at most {self.max_length} characters"

        elif self.data_type == DataType.INTEGER:
            if not isinstance(value, int):
                return False, f"{self.field_label} must be an integer"

            if self.min_value is not None and value < self.min_value:
                return False, f"{self.field_label} must be at least {self.min_value}"

            if self.max_value is not None and value > self.max_value:
                return False, f"{self.field_label} must be at most {self.max_value}"

        # Enum validation
        if self.allowed_values and value not in self.allowed_values:
            return False, f"{self.field_label} must be one of: {', '.join(self.allowed_values)}"

        return True, None


@dataclass(frozen=True)
class MetadataValue(ValueObject):
    """
    Value for a metadata field
    """
    field_name: str
    value: Any
    data_type: DataType

    def __post_init__(self):
        """Validate metadata value"""
        if not self.field_name:
            raise ValueError("Field name is required")

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'field_name': self.field_name,
            'value': self.value,
            'data_type': self.data_type.value
        }
