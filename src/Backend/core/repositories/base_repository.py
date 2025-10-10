"""
Base Repository Interface and Implementation
Following SOLID principles and DDD patterns
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Dict, Any, Union
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

# Generic type for entities
T = TypeVar('T')


class IRepository(ABC, Generic[T]):
    """
    Base repository interface following Interface Segregation Principle
    Defines standard CRUD operations for all repositories
    """

    @abstractmethod
    async def get_by_id(self, entity_id: Union[UUID, str, int]) -> Optional[T]:
        """
        Retrieve an entity by its identifier

        Args:
            entity_id: The unique identifier of the entity

        Returns:
            The entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        Retrieve all entities with pagination support

        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip

        Returns:
            List of entities
        """
        pass

    @abstractmethod
    async def find_by(self, criteria: Dict[str, Any]) -> List[T]:
        """
        Find entities matching specific criteria

        Args:
            criteria: Dictionary of field-value pairs to match

        Returns:
            List of matching entities
        """
        pass

    @abstractmethod
    async def add(self, entity: T) -> T:
        """
        Add a new entity to the repository

        Args:
            entity: The entity to add

        Returns:
            The added entity (with generated ID if applicable)
        """
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """
        Update an existing entity

        Args:
            entity: The entity with updated values

        Returns:
            The updated entity
        """
        pass

    @abstractmethod
    async def delete(self, entity_id: Union[UUID, str, int]) -> bool:
        """
        Delete an entity by its identifier

        Args:
            entity_id: The unique identifier of the entity

        Returns:
            True if deleted successfully, False otherwise
        """
        pass

    @abstractmethod
    async def exists(self, entity_id: Union[UUID, str, int]) -> bool:
        """
        Check if an entity exists

        Args:
            entity_id: The unique identifier to check

        Returns:
            True if entity exists, False otherwise
        """
        pass


class IReadOnlyRepository(ABC, Generic[T]):
    """
    Read-only repository interface for query operations
    Following Interface Segregation Principle
    """

    @abstractmethod
    async def get_by_id(self, entity_id: Union[UUID, str, int]) -> Optional[T]:
        """Retrieve an entity by its identifier"""
        pass

    @abstractmethod
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Retrieve all entities with pagination"""
        pass

    @abstractmethod
    async def find_by(self, criteria: Dict[str, Any]) -> List[T]:
        """Find entities matching criteria"""
        pass

    @abstractmethod
    async def exists(self, entity_id: Union[UUID, str, int]) -> bool:
        """Check if entity exists"""
        pass


class BaseRepository(IRepository[T]):
    """
    Base repository implementation with common functionality
    Following DRY principle
    """

    def __init__(self, connection_manager, table_name: str, entity_class: type):
        """
        Initialize base repository

        Args:
            connection_manager: Database connection manager
            table_name: Name of the database table
            entity_class: Class type for entity deserialization
        """
        self.connection_manager = connection_manager
        self.table_name = table_name
        self.entity_class = entity_class
        logger.info(f"BaseRepository initialized for table: {table_name}")

    def _build_where_clause(self, criteria: Dict[str, Any]) -> tuple:
        """
        Build SQL WHERE clause from criteria dictionary

        Args:
            criteria: Dictionary of field-value pairs

        Returns:
            Tuple of (where_clause_string, params_list)
        """
        if not criteria:
            return "", []

        conditions = []
        params = []

        for field, value in criteria.items():
            if value is None:
                conditions.append(f"{field} IS NULL")
            elif isinstance(value, (list, tuple)):
                placeholders = ','.join(['%s'] * len(value))
                conditions.append(f"{field} IN ({placeholders})")
                params.extend(value)
            elif isinstance(value, dict):
                # Handle complex conditions like {'$gte': 10, '$lte': 100}
                for operator, val in value.items():
                    if operator == '$gte':
                        conditions.append(f"{field} >= %s")
                        params.append(val)
                    elif operator == '$lte':
                        conditions.append(f"{field} <= %s")
                        params.append(val)
                    elif operator == '$gt':
                        conditions.append(f"{field} > %s")
                        params.append(val)
                    elif operator == '$lt':
                        conditions.append(f"{field} < %s")
                        params.append(val)
                    elif operator == '$like':
                        conditions.append(f"{field} LIKE %s")
                        params.append(val)
                    elif operator == '$ilike':
                        conditions.append(f"{field} ILIKE %s")
                        params.append(val)
            else:
                conditions.append(f"{field} = %s")
                params.append(value)

        where_clause = " AND ".join(conditions)
        return f"WHERE {where_clause}" if where_clause else "", params

    def _entity_to_dict(self, entity: T) -> Dict[str, Any]:
        """
        Convert entity to dictionary for database operations

        Args:
            entity: Entity to convert

        Returns:
            Dictionary representation of entity
        """
        if hasattr(entity, 'to_dict'):
            return entity.to_dict()
        elif hasattr(entity, '__dict__'):
            return entity.__dict__.copy()
        else:
            return dict(entity)

    def _dict_to_entity(self, data: Dict[str, Any]) -> T:
        """
        Convert dictionary to entity instance

        Args:
            data: Dictionary data from database

        Returns:
            Entity instance
        """
        if hasattr(self.entity_class, 'from_dict'):
            return self.entity_class.from_dict(data)
        else:
            return self.entity_class(**data)

    async def get_by_id(self, entity_id: Union[UUID, str, int]) -> Optional[T]:
        """
        Default implementation for get_by_id
        Assumes 'id' as primary key field
        """
        connection = None
        cursor = None

        try:
            from psycopg2.extras import RealDictCursor

            connection = self.connection_manager.get_connection()
            cursor = connection.cursor(cursor_factory=RealDictCursor)

            query = f"SELECT * FROM {self.table_name} WHERE id = %s"
            cursor.execute(query, (entity_id,))
            result = cursor.fetchone()

            if result:
                return self._dict_to_entity(dict(result))
            return None

        except Exception as e:
            logger.error(f"Failed to get entity by id {entity_id}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if connection:
                self.connection_manager.release_connection(connection)

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        Default implementation for get_all
        """
        connection = None
        cursor = None

        try:
            from psycopg2.extras import RealDictCursor

            connection = self.connection_manager.get_connection()
            cursor = connection.cursor(cursor_factory=RealDictCursor)

            query = f"SELECT * FROM {self.table_name} LIMIT %s OFFSET %s"
            cursor.execute(query, (limit, offset))
            results = cursor.fetchall()

            return [self._dict_to_entity(dict(row)) for row in results]

        except Exception as e:
            logger.error(f"Failed to get all entities: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                self.connection_manager.release_connection(connection)

    async def find_by(self, criteria: Dict[str, Any]) -> List[T]:
        """
        Default implementation for find_by
        """
        connection = None
        cursor = None

        try:
            from psycopg2.extras import RealDictCursor

            connection = self.connection_manager.get_connection()
            cursor = connection.cursor(cursor_factory=RealDictCursor)

            where_clause, params = self._build_where_clause(criteria)
            query = f"SELECT * FROM {self.table_name} {where_clause}"

            cursor.execute(query, params)
            results = cursor.fetchall()

            return [self._dict_to_entity(dict(row)) for row in results]

        except Exception as e:
            logger.error(f"Failed to find entities by criteria: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                self.connection_manager.release_connection(connection)

    async def add(self, entity: T) -> T:
        """
        Default implementation for add
        """
        connection = None
        cursor = None

        try:
            from psycopg2.extras import RealDictCursor

            connection = self.connection_manager.get_connection()
            cursor = connection.cursor(cursor_factory=RealDictCursor)

            entity_dict = self._entity_to_dict(entity)

            # Remove id if it's None (for auto-generated IDs)
            if 'id' in entity_dict and entity_dict['id'] is None:
                entity_dict.pop('id')

            fields = list(entity_dict.keys())
            values = list(entity_dict.values())
            placeholders = ','.join(['%s'] * len(values))

            query = f"""
                INSERT INTO {self.table_name} ({','.join(fields)})
                VALUES ({placeholders})
                RETURNING *
            """

            cursor.execute(query, values)
            result = cursor.fetchone()
            connection.commit()

            if result:
                return self._dict_to_entity(dict(result))
            return entity

        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Failed to add entity: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                self.connection_manager.release_connection(connection)

    async def update(self, entity: T) -> T:
        """
        Default implementation for update
        """
        connection = None
        cursor = None

        try:
            from psycopg2.extras import RealDictCursor

            connection = self.connection_manager.get_connection()
            cursor = connection.cursor(cursor_factory=RealDictCursor)

            entity_dict = self._entity_to_dict(entity)
            entity_id = entity_dict.pop('id')

            if not entity_dict:
                return entity

            set_clauses = [f"{field} = %s" for field in entity_dict.keys()]
            values = list(entity_dict.values())
            values.append(entity_id)

            query = f"""
                UPDATE {self.table_name}
                SET {','.join(set_clauses)}
                WHERE id = %s
                RETURNING *
            """

            cursor.execute(query, values)
            result = cursor.fetchone()
            connection.commit()

            if result:
                return self._dict_to_entity(dict(result))
            return entity

        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Failed to update entity: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                self.connection_manager.release_connection(connection)

    async def delete(self, entity_id: Union[UUID, str, int]) -> bool:
        """
        Default implementation for delete
        """
        connection = None
        cursor = None

        try:
            connection = self.connection_manager.get_connection()
            cursor = connection.cursor()

            query = f"DELETE FROM {self.table_name} WHERE id = %s"
            cursor.execute(query, (entity_id,))

            deleted_count = cursor.rowcount
            connection.commit()

            return deleted_count > 0

        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Failed to delete entity: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if connection:
                self.connection_manager.release_connection(connection)

    async def exists(self, entity_id: Union[UUID, str, int]) -> bool:
        """
        Default implementation for exists
        """
        connection = None
        cursor = None

        try:
            connection = self.connection_manager.get_connection()
            cursor = connection.cursor()

            query = f"SELECT 1 FROM {self.table_name} WHERE id = %s LIMIT 1"
            cursor.execute(query, (entity_id,))

            return cursor.fetchone() is not None

        except Exception as e:
            logger.error(f"Failed to check entity existence: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if connection:
                self.connection_manager.release_connection(connection)


class SpecificationBase(ABC):
    """
    Base class for specifications following DDD pattern
    Used for complex query criteria
    """

    @abstractmethod
    def is_satisfied_by(self, entity: T) -> bool:
        """Check if entity satisfies the specification"""
        pass

    @abstractmethod
    def to_sql_criteria(self) -> Dict[str, Any]:
        """Convert specification to SQL criteria"""
        pass

    def and_(self, other: 'SpecificationBase'):
        """Combine specifications with AND logic"""
        return AndSpecification(self, other)

    def or_(self, other: 'SpecificationBase'):
        """Combine specifications with OR logic"""
        return OrSpecification(self, other)

    def not_(self):
        """Negate the specification"""
        return NotSpecification(self)


class AndSpecification(SpecificationBase):
    """AND combination of specifications"""

    def __init__(self, left: SpecificationBase, right: SpecificationBase):
        self.left = left
        self.right = right

    def is_satisfied_by(self, entity: T) -> bool:
        return self.left.is_satisfied_by(entity) and self.right.is_satisfied_by(entity)

    def to_sql_criteria(self) -> Dict[str, Any]:
        left_criteria = self.left.to_sql_criteria()
        right_criteria = self.right.to_sql_criteria()
        # Merge criteria (simplified - real implementation would handle conflicts)
        return {**left_criteria, **right_criteria}


class OrSpecification(SpecificationBase):
    """OR combination of specifications"""

    def __init__(self, left: SpecificationBase, right: SpecificationBase):
        self.left = left
        self.right = right

    def is_satisfied_by(self, entity: T) -> bool:
        return self.left.is_satisfied_by(entity) or self.right.is_satisfied_by(entity)

    def to_sql_criteria(self) -> Dict[str, Any]:
        # This is simplified - real implementation would build OR conditions
        return {'$or': [self.left.to_sql_criteria(), self.right.to_sql_criteria()]}


class NotSpecification(SpecificationBase):
    """NOT specification"""

    def __init__(self, specification: SpecificationBase):
        self.specification = specification

    def is_satisfied_by(self, entity: T) -> bool:
        return not self.specification.is_satisfied_by(entity)

    def to_sql_criteria(self) -> Dict[str, Any]:
        # This is simplified - real implementation would negate conditions
        return {'$not': self.specification.to_sql_criteria()}