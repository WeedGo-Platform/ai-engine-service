"""
Base Domain Building Blocks
Following Domain-Driven Design patterns
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar, Generic
from uuid import UUID, uuid4
import hashlib
import json


class DomainEvent(ABC):
    """Base class for all domain events"""

    def __init__(self, aggregate_id: UUID, occurred_at: Optional[datetime] = None):
        self.event_id = uuid4()
        self.aggregate_id = aggregate_id
        self.occurred_at = occurred_at or datetime.utcnow()
        self.event_type = self.__class__.__name__

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        return {
            'event_id': str(self.event_id),
            'event_type': self.event_type,
            'aggregate_id': str(self.aggregate_id),
            'occurred_at': self.occurred_at.isoformat()
        }


class ValueObject(ABC):
    """
    Base class for Value Objects
    Value objects are immutable and compared by value
    """

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __hash__(self):
        """Generate hash based on all attributes"""
        values = tuple(sorted(self.__dict__.items()))
        return hash(values)

    def __repr__(self):
        attrs = ', '.join(f"{k}={v}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({attrs})"


class Entity(ABC):
    """
    Base class for Entities
    Entities have identity and are compared by ID
    """

    def __init__(self, entity_id: Optional[UUID] = None):
        self.id = entity_id or uuid4()
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self._domain_events: List[DomainEvent] = []

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def add_domain_event(self, event: DomainEvent):
        """Add a domain event to be dispatched"""
        self._domain_events.append(event)

    def clear_domain_events(self):
        """Clear all domain events after dispatching"""
        self._domain_events.clear()

    def get_domain_events(self) -> List[DomainEvent]:
        """Get all pending domain events"""
        return self._domain_events.copy()

    def mark_as_modified(self):
        """Update the updated_at timestamp"""
        self.updated_at = datetime.utcnow()


class AggregateRoot(Entity):
    """
    Base class for Aggregate Roots
    Aggregate roots are the entry point to the aggregate
    """

    def __init__(self, aggregate_id: Optional[UUID] = None):
        super().__init__(aggregate_id)
        self._version = 0

    def increment_version(self):
        """Increment version for optimistic locking"""
        self._version += 1

    def get_version(self) -> int:
        """Get current version"""
        return self._version

    def apply_event(self, event: DomainEvent):
        """Apply domain event and add to events list"""
        handler_name = f"_handle_{event.__class__.__name__}"
        handler = getattr(self, handler_name, None)
        if handler:
            handler(event)
        self.add_domain_event(event)
        self.increment_version()


class Specification(ABC):
    """
    Base class for Specifications (business rules)
    Used for complex business rule validation
    """

    @abstractmethod
    def is_satisfied_by(self, candidate: Any) -> bool:
        """Check if the candidate satisfies the specification"""
        pass

    def and_(self, other: 'Specification') -> 'AndSpecification':
        """Combine specifications with AND logic"""
        return AndSpecification(self, other)

    def or_(self, other: 'Specification') -> 'OrSpecification':
        """Combine specifications with OR logic"""
        return OrSpecification(self, other)

    def not_(self) -> 'NotSpecification':
        """Negate the specification"""
        return NotSpecification(self)


class AndSpecification(Specification):
    """Specification that combines two specifications with AND logic"""

    def __init__(self, left: Specification, right: Specification):
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: Any) -> bool:
        return self.left.is_satisfied_by(candidate) and self.right.is_satisfied_by(candidate)


class OrSpecification(Specification):
    """Specification that combines two specifications with OR logic"""

    def __init__(self, left: Specification, right: Specification):
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: Any) -> bool:
        return self.left.is_satisfied_by(candidate) or self.right.is_satisfied_by(candidate)


class NotSpecification(Specification):
    """Specification that negates another specification"""

    def __init__(self, specification: Specification):
        self.specification = specification

    def is_satisfied_by(self, candidate: Any) -> bool:
        return not self.specification.is_satisfied_by(candidate)


T = TypeVar('T')


class Repository(ABC, Generic[T]):
    """
    Base repository interface
    Repositories provide access to aggregates
    """

    @abstractmethod
    async def get_by_id(self, entity_id: UUID) -> Optional[T]:
        """Get entity by ID"""
        pass

    @abstractmethod
    async def save(self, entity: T) -> T:
        """Save entity"""
        pass

    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """Delete entity by ID"""
        pass

    @abstractmethod
    async def exists(self, entity_id: UUID) -> bool:
        """Check if entity exists"""
        pass


class DomainService(ABC):
    """
    Base class for Domain Services
    Domain services contain business logic that doesn't belong to a single entity
    """
    pass


class DomainException(Exception):
    """Base exception for domain errors"""

    def __init__(self, message: str, code: Optional[str] = None):
        super().__init__(message)
        self.code = code or self.__class__.__name__
        self.message = message


class BusinessRuleViolation(DomainException):
    """Exception raised when a business rule is violated"""
    pass


class EntityNotFound(DomainException):
    """Exception raised when an entity is not found"""

    def __init__(self, entity_type: str, entity_id: UUID):
        super().__init__(
            f"{entity_type} with id {entity_id} not found",
            code="ENTITY_NOT_FOUND"
        )
        self.entity_type = entity_type
        self.entity_id = entity_id


class ConcurrencyException(DomainException):
    """Exception raised when there's a concurrency conflict"""

    def __init__(self, entity_type: str, entity_id: UUID, expected_version: int, actual_version: int):
        super().__init__(
            f"Concurrency conflict for {entity_type} {entity_id}. Expected version {expected_version}, got {actual_version}",
            code="CONCURRENCY_CONFLICT"
        )