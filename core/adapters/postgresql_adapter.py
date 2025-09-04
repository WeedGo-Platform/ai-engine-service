"""
PostgreSQL Data Adapter
Implements DataAdapter interface for PostgreSQL databases
"""
import asyncio
import asyncpg
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
import sys

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.interfaces.data_adapter import (
    DataAdapter, QuerySpec, QueryFilter, QueryOperator, SchemaMapping
)

logger = logging.getLogger(__name__)

class PostgreSQLAdapter(DataAdapter):
    """PostgreSQL implementation of DataAdapter"""
    
    def __init__(self, connection_config: Dict):
        """Initialize PostgreSQL adapter"""
        self.config = connection_config
        self.pool = None
        self.schema_mappings = {}
        
        # Extract connection parameters
        self.host = connection_config.get('host', 'localhost')
        self.port = connection_config.get('port', 5432)
        self.database = connection_config.get('database', 'weedgo')
        self.user = connection_config.get('user', 'weedgo_user')
        self.password = connection_config.get('password', 'ai_password')
        self.min_connections = connection_config.get('min_connections', 2)
        self.max_connections = connection_config.get('max_connections', 10)
    
    async def connect(self) -> bool:
        """Establish connection pool to PostgreSQL"""
        try:
            # Connect to the real database - no mock fallback
            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                min_size=self.min_connections,
                max_size=self.max_connections,
                command_timeout=60
            )
            logger.info(f"Connected to PostgreSQL at {self.host}:{self.port}/{self.database}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Disconnected from PostgreSQL")
    
    async def search(self, query: QuerySpec) -> List[Dict]:
        """Execute a search query"""
        if not self.pool:
            raise ConnectionError("Database connection not available")
        
        try:
            # Build SQL query
            sql, params = self._build_search_query(query)
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(sql, *params)
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Search query failed: {e}")
            return []
    
    async def get_by_id(self, entity: str, id: Union[str, int]) -> Optional[Dict]:
        """Get a single record by ID"""
        if not self.pool:
            raise ConnectionError("Database connection not available")
        
        try:
            sql = f"SELECT * FROM {entity} WHERE id = $1"
            
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(sql, id)
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"Get by ID failed: {e}")
            return None
    
    async def create(self, entity: str, data: Dict) -> Dict:
        """Create a new record"""
        if not self.pool:
            raise ConnectionError("Database connection not available")
        
        try:
            # Build INSERT query
            columns = list(data.keys())
            values = list(data.values())
            placeholders = [f"${i+1}" for i in range(len(values))]
            
            sql = f"""
                INSERT INTO {entity} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                RETURNING *
            """
            
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(sql, *values)
                return dict(row)
                
        except Exception as e:
            logger.error(f"Create failed: {e}")
            raise
    
    async def update(self, entity: str, id: Union[str, int], data: Dict) -> Dict:
        """Update an existing record"""
        if not self.pool:
            raise ConnectionError("Database connection not available")
        
        try:
            # Build UPDATE query
            set_clauses = []
            values = []
            for i, (key, value) in enumerate(data.items(), 1):
                set_clauses.append(f"{key} = ${i}")
                values.append(value)
            values.append(id)
            
            sql = f"""
                UPDATE {entity}
                SET {', '.join(set_clauses)}
                WHERE id = ${len(values)}
                RETURNING *
            """
            
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(sql, *values)
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"Update failed: {e}")
            raise
    
    async def delete(self, entity: str, id: Union[str, int]) -> bool:
        """Delete a record"""
        if not self.pool:
            raise ConnectionError("Database connection not available")
        
        try:
            sql = f"DELETE FROM {entity} WHERE id = $1"
            
            async with self.pool.acquire() as conn:
                result = await conn.execute(sql, id)
                return result != "DELETE 0"
                
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False
    
    async def execute_raw(self, query: str, params: Dict = None) -> List[Dict]:
        """Execute a raw SQL query"""
        if not self.pool:
            return []
        
        try:
            async with self.pool.acquire() as conn:
                if params:
                    rows = await conn.fetch(query, *params.values())
                else:
                    rows = await conn.fetch(query)
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Raw query failed: {e}")
            return []
    
    def map_schema(self, mapping: SchemaMapping) -> None:
        """Register a schema mapping"""
        self.schema_mappings[mapping.domain_entity] = mapping
    
    def translate_query(self, domain_query: Dict) -> str:
        """Translate a domain-level query to SQL"""
        # Basic translation logic
        entity = domain_query.get('entity', 'products')
        conditions = domain_query.get('conditions', [])
        
        where_clauses = []
        for cond in conditions:
            field = cond.get('field')
            operator = cond.get('operator', '=')
            value = cond.get('value')
            
            if operator == 'contains':
                where_clauses.append(f"{field} ILIKE '%{value}%'")
            else:
                where_clauses.append(f"{field} {operator} '{value}'")
        
        sql = f"SELECT * FROM {entity}"
        if where_clauses:
            sql += f" WHERE {' AND '.join(where_clauses)}"
        
        return sql
    
    def _build_search_query(self, query: QuerySpec) -> Tuple[str, List]:
        """Build SQL query from QuerySpec"""
        sql_parts = []
        params = []
        param_count = 0
        
        # SELECT clause
        if query.select_fields:
            fields = ', '.join(query.select_fields)
        else:
            fields = '*'
        sql_parts.append(f"SELECT {fields} FROM {query.entity}")
        
        # WHERE clause
        if query.filters:
            where_clauses = []
            for filter in query.filters:
                param_count += 1
                param_placeholder = f"${param_count}"
                
                if filter.operator == QueryOperator.EQUALS:
                    where_clauses.append(f"{filter.field} = {param_placeholder}")
                    params.append(filter.value)
                elif filter.operator == QueryOperator.CONTAINS:
                    where_clauses.append(f"{filter.field} ILIKE {param_placeholder}")
                    params.append(f"%{filter.value}%")
                elif filter.operator == QueryOperator.IN:
                    where_clauses.append(f"{filter.field} = ANY({param_placeholder})")
                    params.append(filter.value)
                # Add more operators as needed
            
            if where_clauses:
                sql_parts.append(f"WHERE {' AND '.join(where_clauses)}")
        
        # ORDER BY clause
        if query.order_by:
            order_parts = [f"{field} {direction}" for field, direction in query.order_by]
            sql_parts.append(f"ORDER BY {', '.join(order_parts)}")
        
        # LIMIT and OFFSET
        if query.limit:
            sql_parts.append(f"LIMIT {query.limit}")
        if query.offset:
            sql_parts.append(f"OFFSET {query.offset}")
        
        return ' '.join(sql_parts), params
    
    
    def get_capabilities(self) -> Dict[str, bool]:
        """Get adapter capabilities"""
        return {
            "transactions": True,
            "joins": True,
            "aggregations": True,
            "full_text_search": True,
            "vector_search": False,  # Unless using pgvector
            "real_time": True
        }

# Register the adapter
from core.interfaces.data_adapter import DataAdapterFactory
DataAdapterFactory.register('postgresql', PostgreSQLAdapter)