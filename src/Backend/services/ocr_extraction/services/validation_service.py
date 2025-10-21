"""
Validation Service

Validates extracted data against template requirements.
Following SRP: Only responsible for validation logic.
Following DRY: Centralized validation rules.
"""

import re
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime

from ..domain.value_objects import Template, Field
from ..domain.enums import FieldType, ValidationSeverity
from ..domain.exceptions import ValidationError, FieldValidationError

logger = logging.getLogger(__name__)


class ValidationResult:
    """
    Result of validation operation

    Contains validation status, errors, warnings, and field-level issues.
    """

    def __init__(self):
        """Initialize empty validation result"""
        self.is_valid = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.field_issues: Dict[str, List[str]] = {}

    def add_error(self, message: str, field_name: str = None):
        """Add a validation error"""
        self.is_valid = False
        self.errors.append(message)
        if field_name:
            if field_name not in self.field_issues:
                self.field_issues[field_name] = []
            self.field_issues[field_name].append(f"ERROR: {message}")

    def add_warning(self, message: str, field_name: str = None):
        """Add a validation warning (doesn't invalidate)"""
        self.warnings.append(message)
        if field_name:
            if field_name not in self.field_issues:
                self.field_issues[field_name] = []
            self.field_issues[field_name].append(f"WARNING: {message}")

    def has_issues(self) -> bool:
        """Check if there are any errors or warnings"""
        return len(self.errors) > 0 or len(self.warnings) > 0

    def get_summary(self) -> str:
        """Get human-readable summary"""
        if not self.has_issues():
            return "✅ Validation passed with no issues"

        summary = []
        if self.errors:
            summary.append(f"❌ {len(self.errors)} errors")
        if self.warnings:
            summary.append(f"⚠️ {len(self.warnings)} warnings")

        return ", ".join(summary)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'field_issues': self.field_issues,
            'summary': self.get_summary(),
        }


class ValidationService:
    """
    Service for validating extracted data

    Validates data against template field requirements:
    - Required fields present
    - Field types correct
    - Validation patterns match
    - Business rules satisfied
    """

    def validate(
        self,
        extracted_data: Dict[str, Any],
        template: Template
    ) -> ValidationResult:
        """
        Validate extracted data against template

        Args:
            extracted_data: Data extracted from document
            template: Template with field requirements

        Returns:
            ValidationResult with status and issues
        """
        result = ValidationResult()

        logger.info(f"Validating extracted data against template: {template.name}")

        # Validate each field in template
        for field in template.fields:
            self._validate_field(
                field=field,
                value=extracted_data.get(field.name),
                result=result
            )

        # Check for extra fields (not in template)
        template_field_names = {f.name for f in template.fields}
        extra_fields = set(extracted_data.keys()) - template_field_names

        if extra_fields:
            result.add_warning(
                f"Extra fields not in template: {', '.join(extra_fields)}"
            )

        logger.info(f"Validation complete: {result.get_summary()}")

        return result

    def _validate_field(
        self,
        field: Field,
        value: Any,
        result: ValidationResult
    ):
        """
        Validate a single field

        Args:
            field: Field definition
            value: Extracted value
            result: ValidationResult to update
        """
        # Check if required field is missing
        if field.required and (value is None or value == ""):
            result.add_error(
                f"Required field '{field.name}' is missing",
                field_name=field.name
            )
            return

        # If optional and missing, skip further validation
        if value is None or value == "":
            return

        # Type-specific validation
        if field.field_type == FieldType.NUMBER:
            self._validate_number(field, value, result)

        elif field.field_type == FieldType.PRICE:
            self._validate_price(field, value, result)

        elif field.field_type == FieldType.DATE:
            self._validate_date(field, value, result)

        elif field.field_type == FieldType.BARCODE:
            self._validate_barcode(field, value, result)

        elif field.field_type == FieldType.EMAIL:
            self._validate_email(field, value, result)

        elif field.field_type == FieldType.PHONE:
            self._validate_phone(field, value, result)

        elif field.field_type == FieldType.URL:
            self._validate_url(field, value, result)

        elif field.field_type == FieldType.TABLE:
            self._validate_table(field, value, result)

        elif field.field_type == FieldType.TEXT:
            self._validate_text(field, value, result)

        # Check validation pattern if specified
        if field.validation_pattern:
            self._validate_pattern(field, value, result)

    def _validate_number(self, field: Field, value: Any, result: ValidationResult):
        """Validate number field"""
        try:
            # Try to convert to int or float
            if isinstance(value, str):
                if '.' in value:
                    float(value)
                else:
                    int(value)
            elif not isinstance(value, (int, float)):
                result.add_error(
                    f"Field '{field.name}' must be a number, got {type(value).__name__}",
                    field_name=field.name
                )
        except ValueError:
            result.add_error(
                f"Field '{field.name}' has invalid number format: {value}",
                field_name=field.name
            )

    def _validate_price(self, field: Field, value: Any, result: ValidationResult):
        """Validate price field"""
        try:
            # Price should be string or number
            if isinstance(value, str):
                # Remove currency symbols and commas
                cleaned = value.replace('$', '').replace(',', '').strip()
                price = float(cleaned)
            elif isinstance(value, (int, float)):
                price = float(value)
            else:
                result.add_error(
                    f"Field '{field.name}' must be a price, got {type(value).__name__}",
                    field_name=field.name
                )
                return

            # Price should be non-negative
            if price < 0:
                result.add_warning(
                    f"Field '{field.name}' has negative price: {price}",
                    field_name=field.name
                )

        except ValueError:
            result.add_error(
                f"Field '{field.name}' has invalid price format: {value}",
                field_name=field.name
            )

    def _validate_date(self, field: Field, value: Any, result: ValidationResult):
        """Validate date field"""
        if not isinstance(value, str):
            result.add_error(
                f"Field '{field.name}' must be a date string, got {type(value).__name__}",
                field_name=field.name
            )
            return

        # Try to parse as ISO date (YYYY-MM-DD)
        try:
            datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            result.add_error(
                f"Field '{field.name}' has invalid date format: {value} (expected YYYY-MM-DD)",
                field_name=field.name
            )

    def _validate_barcode(self, field: Field, value: Any, result: ValidationResult):
        """Validate barcode field"""
        if not isinstance(value, str):
            result.add_error(
                f"Field '{field.name}' must be a barcode string, got {type(value).__name__}",
                field_name=field.name
            )
            return

        # Barcode should be 8-14 digits
        if not value.isdigit():
            result.add_error(
                f"Field '{field.name}' barcode must contain only digits, got: {value}",
                field_name=field.name
            )
        elif len(value) < 8 or len(value) > 14:
            result.add_warning(
                f"Field '{field.name}' barcode length unusual: {len(value)} digits (expected 8-14)",
                field_name=field.name
            )

    def _validate_email(self, field: Field, value: Any, result: ValidationResult):
        """Validate email field"""
        if not isinstance(value, str):
            result.add_error(
                f"Field '{field.name}' must be an email string, got {type(value).__name__}",
                field_name=field.name
            )
            return

        # Simple email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            result.add_error(
                f"Field '{field.name}' has invalid email format: {value}",
                field_name=field.name
            )

    def _validate_phone(self, field: Field, value: Any, result: ValidationResult):
        """Validate phone field"""
        if not isinstance(value, str):
            result.add_error(
                f"Field '{field.name}' must be a phone string, got {type(value).__name__}",
                field_name=field.name
            )
            return

        # Phone should have at least 10 digits
        digits = re.sub(r'\D', '', value)  # Remove non-digits
        if len(digits) < 10:
            result.add_error(
                f"Field '{field.name}' has too few digits for phone: {value}",
                field_name=field.name
            )

    def _validate_url(self, field: Field, value: Any, result: ValidationResult):
        """Validate URL field"""
        if not isinstance(value, str):
            result.add_error(
                f"Field '{field.name}' must be a URL string, got {type(value).__name__}",
                field_name=field.name
            )
            return

        # Simple URL validation
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, value, re.IGNORECASE):
            result.add_error(
                f"Field '{field.name}' has invalid URL format: {value}",
                field_name=field.name
            )

    def _validate_table(self, field: Field, value: Any, result: ValidationResult):
        """Validate table field (array of objects)"""
        if not isinstance(value, list):
            result.add_error(
                f"Field '{field.name}' must be an array, got {type(value).__name__}",
                field_name=field.name
            )
            return

        if len(value) == 0:
            result.add_warning(
                f"Field '{field.name}' is an empty table",
                field_name=field.name
            )

    def _validate_text(self, field: Field, value: Any, result: ValidationResult):
        """Validate text field"""
        if not isinstance(value, str):
            result.add_warning(
                f"Field '{field.name}' expected string, got {type(value).__name__}: {value}",
                field_name=field.name
            )

    def _validate_pattern(self, field: Field, value: Any, result: ValidationResult):
        """Validate against regex pattern"""
        if not isinstance(value, str):
            return  # Type validation happens elsewhere

        try:
            if not re.match(field.validation_pattern, str(value)):
                result.add_error(
                    f"Field '{field.name}' doesn't match required pattern: {value}",
                    field_name=field.name
                )
        except re.error as e:
            logger.error(f"Invalid regex pattern in field '{field.name}': {e}")
            result.add_warning(
                f"Field '{field.name}' has invalid validation pattern",
                field_name=field.name
            )


# Convenience instance
validation_service = ValidationService()
