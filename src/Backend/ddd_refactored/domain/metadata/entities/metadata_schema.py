"""
MetadataSchema Aggregate Root
Following DDD Architecture Document Section 2.15
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from ....shared.domain_base import AggregateRoot, DomainEvent, BusinessRuleViolation
from ..value_objects.metadata_types import (
    DataType,
    FieldDefinition,
    MetadataValue
)


# Domain Events
class SchemaCreated(DomainEvent):
    schema_id: UUID
    schema_name: str
    entity_type: str


class FieldAdded(DomainEvent):
    schema_id: UUID
    field_name: str
    data_type: DataType


class SchemaPublished(DomainEvent):
    schema_id: UUID
    schema_name: str
    published_at: datetime


@dataclass
class MetadataSchema(AggregateRoot):
    """
    MetadataSchema Aggregate Root - Custom field schemas
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.15
    """
    # Schema details
    schema_name: str = ""
    entity_type: str = ""  # product, customer, order, etc.
    description: Optional[str] = None

    # Fields
    fields: List[FieldDefinition] = field(default_factory=list)

    # Status
    is_active: bool = True
    is_published: bool = False

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None

    # Tracking
    created_by: Optional[UUID] = None
    version: int = 1

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        schema_name: str,
        entity_type: str,
        description: Optional[str] = None,
        created_by: Optional[UUID] = None
    ) -> 'MetadataSchema':
        """Factory method to create new schema"""
        if not schema_name:
            raise BusinessRuleViolation("Schema name is required")

        if not entity_type:
            raise BusinessRuleViolation("Entity type is required")

        schema = cls(
            schema_name=schema_name,
            entity_type=entity_type,
            description=description,
            created_by=created_by,
            is_active=True,
            is_published=False
        )

        # Raise creation event
        schema.add_domain_event(SchemaCreated(
            schema_id=schema.id,
            schema_name=schema_name,
            entity_type=entity_type
        ))

        return schema

    def add_field(self, field_definition: FieldDefinition):
        """Add field to schema"""
        if self.is_published:
            raise BusinessRuleViolation("Cannot modify published schema")

        # Check for duplicate field names
        if self.has_field(field_definition.field_name):
            raise BusinessRuleViolation(f"Field {field_definition.field_name} already exists")

        self.fields.append(field_definition)
        self.updated_at = datetime.utcnow()

        # Raise event
        self.add_domain_event(FieldAdded(
            schema_id=self.id,
            field_name=field_definition.field_name,
            data_type=field_definition.data_type
        ))

        self.mark_as_modified()

    def remove_field(self, field_name: str):
        """Remove field from schema"""
        if self.is_published:
            raise BusinessRuleViolation("Cannot modify published schema")

        self.fields = [f for f in self.fields if f.field_name != field_name]
        self.updated_at = datetime.utcnow()
        self.mark_as_modified()

    def publish(self):
        """Publish the schema"""
        if self.is_published:
            raise BusinessRuleViolation("Schema is already published")

        if len(self.fields) == 0:
            raise BusinessRuleViolation("Cannot publish schema with no fields")

        self.is_published = True
        self.published_at = datetime.utcnow()

        # Raise event
        self.add_domain_event(SchemaPublished(
            schema_id=self.id,
            schema_name=self.schema_name,
            published_at=self.published_at
        ))

        self.mark_as_modified()

    def create_new_version(self) -> 'MetadataSchema':
        """Create a new version of the schema"""
        if not self.is_published:
            raise BusinessRuleViolation("Can only version published schemas")

        new_schema = MetadataSchema(
            schema_name=self.schema_name,
            entity_type=self.entity_type,
            description=self.description,
            fields=self.fields.copy(),
            created_by=self.created_by,
            version=self.version + 1,
            is_active=True,
            is_published=False
        )

        return new_schema

    def get_field(self, field_name: str) -> Optional[FieldDefinition]:
        """Get field by name"""
        return next((f for f in self.fields if f.field_name == field_name), None)

    def has_field(self, field_name: str) -> bool:
        """Check if field exists"""
        return self.get_field(field_name) is not None

    def validate_values(self, values: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate a set of values against this schema"""
        errors = []

        # Check required fields
        for field_def in self.fields:
            if field_def.is_required and field_def.field_name not in values:
                errors.append(f"{field_def.field_label} is required")
                continue

            # Validate each provided value
            if field_def.field_name in values:
                is_valid, error = field_def.validate_value(values[field_def.field_name])
                if not is_valid:
                    errors.append(error)

        return len(errors) == 0, errors

    def get_required_fields(self) -> List[FieldDefinition]:
        """Get list of required fields"""
        return [f for f in self.fields if f.is_required]

    def get_optional_fields(self) -> List[FieldDefinition]:
        """Get list of optional fields"""
        return [f for f in self.fields if not f.is_required]

    def validate(self) -> List[str]:
        """Validate metadata schema"""
        errors = []

        if not self.schema_name:
            errors.append("Schema name is required")

        if not self.entity_type:
            errors.append("Entity type is required")

        # Check for duplicate field names
        field_names = [f.field_name for f in self.fields]
        duplicates = [name for name in field_names if field_names.count(name) > 1]
        if duplicates:
            errors.append(f"Duplicate field names: {', '.join(set(duplicates))}")

        return errors
