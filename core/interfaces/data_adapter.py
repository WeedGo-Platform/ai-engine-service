"""
Data Adapter Interface
Abstract interface for data source adapters
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum

class QueryOperator(Enum):
    """Common query operators"""
    EQUALS = "eq"
    NOT_EQUALS = "neq"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    GREATER_EQUAL = "gte"
    LESS_EQUAL = "lte"
    CONTAINS = "contains"
    IN = "in"
    NOT_IN = "not_in"
    LIKE = "like"
    ILIKE = "ilike"
    BETWEEN = "between"
    IS_NULL = "is_null"
    NOT_NULL = "not_null"

@dataclass
class QueryFilter:
    """A single query filter"""
    field: str
    operator: QueryOperator
    value: Any

@dataclass
class QuerySpec:
    """Specification for a data query"""
    entity: str  # Table/collection name
    filters: List[QueryFilter] = None
    select_fields: List[str] = None
    order_by: List[Tuple[str, str]] = None  # [(field, 'asc'|'desc')]
    limit: Optional[int] = None
    offset: Optional[int] = None
    joins: List[Dict] = None
    aggregations: Dict[str, str] = None  # {field: function}

@dataclass
class SchemaMapping:
    """Maps domain concepts to database schema"""
    domain_entity: str
    db_entity: str  # Actual table/collection name
    field_mappings: Dict[str, str]  # {domain_field: db_field}
    relationships: Dict[str, Dict] = None  # Related entities
    computed_fields: Dict[str, str] = None  # Fields that need computation

class DataAdapter(ABC):
    """
    Abstract interface for data adapters
    Allows AI engine to work with different data sources
    """
    
    @abstractmethod
    def __init__(self, connection_config: Dict):
        """Initialize adapter with connection configuration"""
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to data source"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to data source"""
        pass
    
    @abstractmethod
    async def search(self, query: QuerySpec) -> List[Dict]:
        """
        Execute a search query
        
        Args:
            query: Query specification
            
        Returns:
            List of matching records
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, entity: str, id: Union[str, int]) -> Optional[Dict]:
        """
        Get a single record by ID
        
        Args:
            entity: Entity/table name
            id: Record ID
            
        Returns:
            Record dictionary or None
        """
        pass
    
    @abstractmethod
    async def create(self, entity: str, data: Dict) -> Dict:
        """
        Create a new record
        
        Args:
            entity: Entity/table name
            data: Record data
            
        Returns:
            Created record with ID
        """
        pass
    
    @abstractmethod
    async def update(self, entity: str, id: Union[str, int], data: Dict) -> Dict:
        """
        Update an existing record
        
        Args:
            entity: Entity/table name
            id: Record ID
            data: Update data
            
        Returns:
            Updated record
        """
        pass
    
    @abstractmethod
    async def delete(self, entity: str, id: Union[str, int]) -> bool:
        """
        Delete a record
        
        Args:
            entity: Entity/table name
            id: Record ID
            
        Returns:
            Success status
        """
        pass
    
    @abstractmethod
    async def execute_raw(self, query: str, params: Dict = None) -> List[Dict]:
        """
        Execute a raw query (SQL, MongoDB query, etc.)
        
        Args:
            query: Raw query string
            params: Query parameters
            
        Returns:
            Query results
        """
        pass
    
    @abstractmethod
    def map_schema(self, mapping: SchemaMapping) -> None:
        """
        Register a schema mapping
        
        Args:
            mapping: Schema mapping configuration
        """
        pass
    
    @abstractmethod
    def translate_query(self, domain_query: Dict) -> str:
        """
        Translate a domain-level query to database-specific query
        
        Args:
            domain_query: High-level domain query
            
        Returns:
            Database-specific query string
        """
        pass
    
    # Optional methods with default implementations
    
    async def bulk_create(self, entity: str, records: List[Dict]) -> List[Dict]:
        """Bulk create records"""
        results = []
        for record in records:
            results.append(await self.create(entity, record))
        return results
    
    async def count(self, query: QuerySpec) -> int:
        """Count matching records"""
        results = await self.search(query)
        return len(results)
    
    async def exists(self, entity: str, filters: List[QueryFilter]) -> bool:
        """Check if any records match filters"""
        query = QuerySpec(entity=entity, filters=filters, limit=1)
        results = await self.search(query)
        return len(results) > 0
    
    def get_capabilities(self) -> Dict[str, bool]:
        """Get adapter capabilities"""
        return {
            "transactions": False,
            "joins": False,
            "aggregations": False,
            "full_text_search": False,
            "vector_search": False,
            "real_time": False
        }

class DataAdapterFactory:
    """Factory for creating data adapters"""
    
    _adapters: Dict[str, type] = {}
    
    @classmethod
    def register(cls, name: str, adapter_class: type):
        """Register a data adapter implementation"""
        cls._adapters[name] = adapter_class
    
    @classmethod
    def create(cls, adapter_type: str, config: Dict) -> DataAdapter:
        """Create a data adapter instance"""
        if adapter_type not in cls._adapters:
            raise ValueError(f"Unknown adapter type: {adapter_type}")
        
        adapter_class = cls._adapters[adapter_type]
        return adapter_class(config)