"""
PostgreSQL Data Adapter
Implementation of DataAdapter interface for PostgreSQL
"""
import asyncpg
import json
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import sys

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.interfaces.data_adapter import (
    DataAdapter, QuerySpec, QueryFilter, QueryOperator, 
    SchemaMapping, DataAdapterFactory
)

logger = logging.getLogger(__name__)

class PostgreSQLAdapter(DataAdapter):
    """PostgreSQL implementation of the DataAdapter interface"""
    
    def __init__(self, connection_config: Dict):
        """Initialize PostgreSQL adapter"""
        self.config = connection_config
        self.pool = None
        self.schema_mappings: Dict[str, SchemaMapping] = {}
        
    async def connect(self) -> bool:
        """Establish connection pool to PostgreSQL"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 5432),
                database=self.config.get('database'),
                user=self.config.get('user'),
                password=self.config.get('password'),
                min_size=self.config.get('min_connections', 2),
                max_size=self.config.get('max_connections', 10),
                command_timeout=self.config.get('timeout', 60)
            )
            logger.info("PostgreSQL connection pool established")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed")
    
    async def search(self, query: QuerySpec) -> List[Dict]:
        """Execute a search query"""
        if not self.pool:
            raise ConnectionError("Not connected to database")
        
        # Build SQL query
        sql, params = self._build_sql_query(query)
        
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(sql, *params)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Search query failed: {e}")
            raise
    
    async def get_by_id(self, entity: str, id: Union[str, int]) -> Optional[Dict]:
        """Get a single record by ID"""
        if not self.pool:
            raise ConnectionError("Not connected to database")
        
        # Get mapped table name
        table = self._get_table_name(entity)
        
        sql = f"SELECT * FROM {table} WHERE id = $1"
        
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(sql, id)
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Get by ID failed: {e}")
            raise
    
    async def create(self, entity: str, data: Dict) -> Dict:
        """Create a new record"""
        if not self.pool:
            raise ConnectionError("Not connected to database")
        
        table = self._get_table_name(entity)
        
        # Prepare columns and values
        columns = list(data.keys())
        values = list(data.values())
        placeholders = [f"${i+1}" for i in range(len(values))]
        
        sql = f"""
            INSERT INTO {table} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING *
        """
        
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(sql, *values)
                return dict(row)
        except Exception as e:
            logger.error(f"Create failed: {e}")
            raise
    
    async def update(self, entity: str, id: Union[str, int], data: Dict) -> Dict:
        """Update an existing record"""
        if not self.pool:
            raise ConnectionError("Not connected to database")
        
        table = self._get_table_name(entity)
        
        # Prepare SET clause
        set_clauses = [f"{col} = ${i+2}" for i, col in enumerate(data.keys())]
        values = [id] + list(data.values())
        
        sql = f"""
            UPDATE {table}
            SET {', '.join(set_clauses)}
            WHERE id = $1
            RETURNING *
        """
        
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(sql, *values)
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Update failed: {e}")
            raise
    
    async def delete(self, entity: str, id: Union[str, int]) -> bool:
        """Delete a record"""
        if not self.pool:
            raise ConnectionError("Not connected to database")
        
        table = self._get_table_name(entity)
        
        sql = f"DELETE FROM {table} WHERE id = $1"
        
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(sql, id)
                return result != "DELETE 0"
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            raise
    
    async def execute_raw(self, query: str, params: Dict = None) -> List[Dict]:
        """Execute a raw SQL query"""
        if not self.pool:
            raise ConnectionError("Not connected to database")
        
        try:
            async with self.pool.acquire() as conn:
                if params:
                    # Convert dict params to list
                    param_values = list(params.values())
                    rows = await conn.fetch(query, *param_values)
                else:
                    rows = await conn.fetch(query)
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Raw query failed: {e}")
            raise
    
    def map_schema(self, mapping: SchemaMapping) -> None:
        """Register a schema mapping"""
        self.schema_mappings[mapping.domain_entity] = mapping
    
    def translate_query(self, domain_query: Dict) -> str:
        """Translate domain query to SQL"""
        # This would translate a high-level domain query to SQL
        # For now, returning a simple example
        entity = domain_query.get('entity')
        conditions = domain_query.get('conditions', {})
        
        table = self._get_table_name(entity)
        where_clauses = []
        
        for field, value in conditions.items():
            mapped_field = self._get_field_name(entity, field)
            where_clauses.append(f"{mapped_field} = '{value}'")
        
        sql = f"SELECT * FROM {table}"
        if where_clauses:
            sql += f" WHERE {' AND '.join(where_clauses)}"
        
        return sql
    
    def _build_sql_query(self, query: QuerySpec) -> tuple:
        """Build SQL query from QuerySpec"""
        table = self._get_table_name(query.entity)
        
        # SELECT clause
        if query.select_fields:
            select = ", ".join(query.select_fields)
        else:
            select = "*"
        
        sql_parts = [f"SELECT {select} FROM {table}"]
        params = []
        param_count = 0
        
        # WHERE clause
        if query.filters:
            where_clauses = []
            for filter in query.filters:
                param_count += 1
                operator_sql = self._get_operator_sql(filter.operator, param_count)
                where_clauses.append(f"{filter.field} {operator_sql}")
                
                if filter.operator not in [QueryOperator.IS_NULL, QueryOperator.NOT_NULL]:
                    params.append(filter.value)
            
            sql_parts.append(f"WHERE {' AND '.join(where_clauses)}")
        
        # ORDER BY clause
        if query.order_by:
            order_clauses = [f"{field} {direction}" for field, direction in query.order_by]
            sql_parts.append(f"ORDER BY {', '.join(order_clauses)}")
        
        # LIMIT and OFFSET
        if query.limit:
            sql_parts.append(f"LIMIT {query.limit}")
        if query.offset:
            sql_parts.append(f"OFFSET {query.offset}")
        
        sql = " ".join(sql_parts)
        return sql, params
    
    def _get_operator_sql(self, operator: QueryOperator, param_num: int) -> str:
        """Convert QueryOperator to SQL operator"""
        operator_map = {
            QueryOperator.EQUALS: f"= ${param_num}",
            QueryOperator.NOT_EQUALS: f"!= ${param_num}",
            QueryOperator.GREATER_THAN: f"> ${param_num}",
            QueryOperator.LESS_THAN: f"< ${param_num}",
            QueryOperator.GREATER_EQUAL: f">= ${param_num}",
            QueryOperator.LESS_EQUAL: f"<= ${param_num}",
            QueryOperator.LIKE: f"LIKE ${param_num}",
            QueryOperator.ILIKE: f"ILIKE ${param_num}",
            QueryOperator.CONTAINS: f"@> ${param_num}",
            QueryOperator.IN: f"= ANY(${param_num})",
            QueryOperator.NOT_IN: f"!= ALL(${param_num})",
            QueryOperator.IS_NULL: "IS NULL",
            QueryOperator.NOT_NULL: "IS NOT NULL",
        }
        return operator_map.get(operator, f"= ${param_num}")
    
    def _get_table_name(self, entity: str) -> str:
        """Get database table name for entity"""
        if entity in self.schema_mappings:
            return self.schema_mappings[entity].db_entity
        return entity  # Default to entity name
    
    def _get_field_name(self, entity: str, field: str) -> str:
        """Get database field name for domain field"""
        if entity in self.schema_mappings:
            mapping = self.schema_mappings[entity]
            if field in mapping.field_mappings:
                return mapping.field_mappings[field]
        return field  # Default to field name
    
    def get_capabilities(self) -> Dict[str, bool]:
        """Get PostgreSQL capabilities"""
        return {
            "transactions": True,
            "joins": True,
            "aggregations": True,
            "full_text_search": True,
            "vector_search": True,  # With pgvector extension
            "real_time": True,  # With LISTEN/NOTIFY
            "json_support": True,
            "array_support": True
        }
    
    async def search_products(self, criteria: Dict) -> List[Dict]:
        """Cannabis-specific product search"""
        sql = """
            SELECT p.*, i.quantity_available
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            WHERE 1=1
        """
        
        params = []
        param_count = 0
        
        # Add filters
        if criteria.get('type'):
            param_count += 1
            sql += f" AND p.plant_type = ${param_count}"
            params.append(criteria['type'])
        
        if criteria.get('min_thc'):
            param_count += 1
            sql += f" AND p.thc_percentage >= ${param_count}"
            params.append(criteria['min_thc'])
        
        if criteria.get('max_thc'):
            param_count += 1
            sql += f" AND p.thc_percentage <= ${param_count}"
            params.append(criteria['max_thc'])
        
        if criteria.get('effects'):
            param_count += 1
            sql += f" AND p.effects @> ${param_count}::jsonb"
            params.append(json.dumps(criteria['effects']))
        
        sql += " ORDER BY p.thc_percentage DESC LIMIT 10"
        
        return await self.execute_raw(sql, dict(enumerate(params, 1)))

# Register the adapter
DataAdapterFactory.register('postgresql', PostgreSQLAdapter)