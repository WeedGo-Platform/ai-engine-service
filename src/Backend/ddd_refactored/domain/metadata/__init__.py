"""
Metadata Bounded Context

This context handles:
- Dynamic schema definitions
- Custom field management
- Field validation rules
- Entity metadata configuration
"""

from .entities import (
    MetadataSchema,
    SchemaCreated,
    FieldAdded,
    SchemaPublished
)

from .value_objects import (
    DataType,
    ValidationRule,
    FieldDefinition,
    MetadataValue
)

__all__ = [
    'MetadataSchema',
    'SchemaCreated',
    'FieldAdded',
    'SchemaPublished',
    'DataType',
    'ValidationRule',
    'FieldDefinition',
    'MetadataValue'
]
