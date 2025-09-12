"""
Secure Database Query Builder
Prevents SQL injection attacks through parameterized queries
"""

import asyncpg
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from contextlib import asynccontextmanager
import re
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Allowed query types"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


@dataclass
class QueryResult:
    """Query execution result"""
    success: bool
    data: Optional[List[Dict]] = None
    affected_rows: int = 0
    error: Optional[str] = None


class SecureDatabaseConnection:
    """
    Secure database connection manager with SQL injection prevention
    """
    
    # Whitelisted table names (prevent table injection)
    ALLOWED_TABLES = {
        'products',
        'users', 
        'orders',
        'ai_conversations',
        'context_sessions',
        'chat_interactions',
        'model_versions',
        'agent_states',
        'skip_words'
    }
    
    # Whitelisted column names per table
    ALLOWED_COLUMNS = {
        'products': {
            'id', 'name', 'category', 'strain_type', 'thc_content',
            'cbd_content', 'price', 'description', 'effects', 
            'terpenes', 'brand', 'quantity_available'
        },
        'users': {
            'id', 'email', 'first_name', 'last_name', 'created_at',
            'updated_at', 'is_active', 'role'
        },
        'orders': {
            'id', 'user_id', 'total', 'status', 'created_at',
            'updated_at', 'items', 'delivery_address'
        },
        'ai_conversations': {
            'id', 'session_id', 'user_id', 'messages', 
            'created_at', 'updated_at'
        },
        'context_sessions': {
            'id', 'session_id', 'user_id', 'context_data',
            'expires_at'
        }
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with database configuration"""
        self.config = config
        self.pool = None
        self._identifier_pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
    
    async def initialize(self):
        """Create connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 5434),
                database=self.config.get('database', 'ai_engine'),
                user=self.config.get('user', 'weedgo'),
                password=self.config.get('password'),
                min_size=self.config.get('pool_min_size', 5),
                max_size=self.config.get('pool_max_size', 20),
                command_timeout=self.config.get('command_timeout', 60)
            )
            logger.info("Secure database connection pool created")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise
    
    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    def _validate_identifier(self, identifier: str, identifier_type: str) -> bool:
        """
        Validate SQL identifier (table/column name)
        Prevents SQL injection through identifier manipulation
        """
        # Check against regex pattern
        if not self._identifier_pattern.match(identifier):
            logger.error(f"Invalid {identifier_type}: {identifier}")
            return False
        
        # Additional length check
        if len(identifier) > 64:  # PostgreSQL identifier limit
            logger.error(f"{identifier_type} too long: {identifier}")
            return False
        
        return True
    
    def _validate_table(self, table: str) -> bool:
        """Validate table name against whitelist"""
        if table not in self.ALLOWED_TABLES:
            logger.error(f"Table not in whitelist: {table}")
            return False
        return self._validate_identifier(table, "table")
    
    def _validate_columns(self, table: str, columns: List[str]) -> bool:
        """Validate column names against whitelist"""
        if table not in self.ALLOWED_COLUMNS:
            logger.error(f"No column whitelist for table: {table}")
            return False
        
        allowed = self.ALLOWED_COLUMNS[table]
        for column in columns:
            if column not in allowed:
                logger.error(f"Column not in whitelist: {column} for table {table}")
                return False
            if not self._validate_identifier(column, "column"):
                return False
        
        return True
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire connection from pool"""
        async with self.pool.acquire() as connection:
            yield connection
    
    async def select(
        self,
        table: str,
        columns: List[str] = None,
        where: Dict[str, Any] = None,
        order_by: str = None,
        limit: int = None,
        offset: int = None
    ) -> QueryResult:
        """
        Execute secure SELECT query
        
        Args:
            table: Table name (validated against whitelist)
            columns: List of columns to select (validated)
            where: WHERE conditions as dict
            order_by: Column to order by (validated)
            limit: Result limit
            offset: Result offset
        
        Returns:
            QueryResult with data or error
        """
        try:
            # Validate table
            if not self._validate_table(table):
                return QueryResult(success=False, error=f"Invalid table: {table}")
            
            # Validate columns
            if columns:
                if not self._validate_columns(table, columns):
                    return QueryResult(success=False, error="Invalid columns")
                column_str = ", ".join(columns)
            else:
                column_str = "*"
            
            # Build query with parameters
            query = f"SELECT {column_str} FROM {table}"
            params = []
            param_counter = 1
            
            # Add WHERE clause with parameterized values
            if where:
                conditions = []
                for column, value in where.items():
                    if not self._validate_columns(table, [column]):
                        return QueryResult(success=False, error=f"Invalid column: {column}")
                    
                    if value is None:
                        conditions.append(f"{column} IS NULL")
                    elif isinstance(value, (list, tuple)):
                        # Handle IN clause
                        placeholders = ", ".join([f"${i}" for i in range(param_counter, param_counter + len(value))])
                        conditions.append(f"{column} IN ({placeholders})")
                        params.extend(value)
                        param_counter += len(value)
                    else:
                        conditions.append(f"{column} = ${param_counter}")
                        params.append(value)
                        param_counter += 1
                
                query += " WHERE " + " AND ".join(conditions)
            
            # Add ORDER BY (validated)
            if order_by:
                # Extract column name and direction
                parts = order_by.split()
                order_column = parts[0]
                order_direction = parts[1] if len(parts) > 1 else "ASC"
                
                if not self._validate_columns(table, [order_column]):
                    return QueryResult(success=False, error=f"Invalid order column: {order_column}")
                
                if order_direction.upper() not in ("ASC", "DESC"):
                    order_direction = "ASC"
                
                query += f" ORDER BY {order_column} {order_direction}"
            
            # Add LIMIT and OFFSET
            if limit:
                query += f" LIMIT ${param_counter}"
                params.append(limit)
                param_counter += 1
            
            if offset:
                query += f" OFFSET ${param_counter}"
                params.append(offset)
                param_counter += 1
            
            # Execute query
            async with self.acquire() as connection:
                rows = await connection.fetch(query, *params)
                data = [dict(row) for row in rows]
                
                return QueryResult(
                    success=True,
                    data=data,
                    affected_rows=len(data)
                )
        
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return QueryResult(success=False, error=str(e))
    
    async def insert(
        self,
        table: str,
        data: Dict[str, Any],
        returning: List[str] = None
    ) -> QueryResult:
        """
        Execute secure INSERT query
        
        Args:
            table: Table name (validated)
            data: Data to insert as dict
            returning: Columns to return after insert
        
        Returns:
            QueryResult with inserted data or error
        """
        try:
            # Validate table
            if not self._validate_table(table):
                return QueryResult(success=False, error=f"Invalid table: {table}")
            
            # Validate columns
            columns = list(data.keys())
            if not self._validate_columns(table, columns):
                return QueryResult(success=False, error="Invalid columns")
            
            # Build INSERT query
            column_str = ", ".join(columns)
            placeholders = ", ".join([f"${i+1}" for i in range(len(columns))])
            values = list(data.values())
            
            query = f"INSERT INTO {table} ({column_str}) VALUES ({placeholders})"
            
            # Add RETURNING clause
            if returning:
                if not self._validate_columns(table, returning):
                    return QueryResult(success=False, error="Invalid returning columns")
                query += " RETURNING " + ", ".join(returning)
            
            # Execute query
            async with self.acquire() as connection:
                if returning:
                    rows = await connection.fetch(query, *values)
                    data = [dict(row) for row in rows]
                    return QueryResult(success=True, data=data, affected_rows=len(rows))
                else:
                    result = await connection.execute(query, *values)
                    # Parse affected rows from result string
                    affected = int(result.split()[-1]) if result else 0
                    return QueryResult(success=True, affected_rows=affected)
        
        except Exception as e:
            logger.error(f"Insert failed: {e}")
            return QueryResult(success=False, error=str(e))
    
    async def update(
        self,
        table: str,
        data: Dict[str, Any],
        where: Dict[str, Any]
    ) -> QueryResult:
        """
        Execute secure UPDATE query
        
        Args:
            table: Table name (validated)
            data: Data to update as dict
            where: WHERE conditions as dict
        
        Returns:
            QueryResult with affected rows or error
        """
        try:
            # Validate table
            if not self._validate_table(table):
                return QueryResult(success=False, error=f"Invalid table: {table}")
            
            # Validate columns
            update_columns = list(data.keys())
            where_columns = list(where.keys())
            
            if not self._validate_columns(table, update_columns + where_columns):
                return QueryResult(success=False, error="Invalid columns")
            
            # Build UPDATE query
            params = []
            param_counter = 1
            
            # SET clause
            set_clauses = []
            for column, value in data.items():
                set_clauses.append(f"{column} = ${param_counter}")
                params.append(value)
                param_counter += 1
            
            query = f"UPDATE {table} SET " + ", ".join(set_clauses)
            
            # WHERE clause
            where_clauses = []
            for column, value in where.items():
                if value is None:
                    where_clauses.append(f"{column} IS NULL")
                else:
                    where_clauses.append(f"{column} = ${param_counter}")
                    params.append(value)
                    param_counter += 1
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            else:
                # Prevent accidental full-table updates
                return QueryResult(success=False, error="WHERE clause required for UPDATE")
            
            # Execute query
            async with self.acquire() as connection:
                result = await connection.execute(query, *params)
                affected = int(result.split()[-1]) if result else 0
                return QueryResult(success=True, affected_rows=affected)
        
        except Exception as e:
            logger.error(f"Update failed: {e}")
            return QueryResult(success=False, error=str(e))
    
    async def delete(
        self,
        table: str,
        where: Dict[str, Any]
    ) -> QueryResult:
        """
        Execute secure DELETE query
        
        Args:
            table: Table name (validated)
            where: WHERE conditions as dict
        
        Returns:
            QueryResult with affected rows or error
        """
        try:
            # Validate table
            if not self._validate_table(table):
                return QueryResult(success=False, error=f"Invalid table: {table}")
            
            # Require WHERE clause to prevent accidental full-table deletion
            if not where:
                return QueryResult(success=False, error="WHERE clause required for DELETE")
            
            # Validate columns
            where_columns = list(where.keys())
            if not self._validate_columns(table, where_columns):
                return QueryResult(success=False, error="Invalid columns")
            
            # Build DELETE query
            params = []
            param_counter = 1
            where_clauses = []
            
            for column, value in where.items():
                if value is None:
                    where_clauses.append(f"{column} IS NULL")
                else:
                    where_clauses.append(f"{column} = ${param_counter}")
                    params.append(value)
                    param_counter += 1
            
            query = f"DELETE FROM {table} WHERE " + " AND ".join(where_clauses)
            
            # Execute query
            async with self.acquire() as connection:
                result = await connection.execute(query, *params)
                affected = int(result.split()[-1]) if result else 0
                return QueryResult(success=True, affected_rows=affected)
        
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return QueryResult(success=False, error=str(e))
    
    async def execute_raw(
        self,
        query: str,
        params: List[Any] = None,
        fetch: bool = False
    ) -> QueryResult:
        """
        Execute raw query (use with caution)
        Only for queries that can't be built with safe methods
        Always use parameterized queries!
        
        Args:
            query: SQL query with $1, $2... placeholders
            params: Query parameters
            fetch: Whether to fetch results
        
        Returns:
            QueryResult
        """
        # Log raw queries for audit
        logger.warning(f"Executing raw query: {query[:100]}...")
        
        try:
            async with self.acquire() as connection:
                if fetch:
                    rows = await connection.fetch(query, *(params or []))
                    data = [dict(row) for row in rows]
                    return QueryResult(success=True, data=data, affected_rows=len(data))
                else:
                    result = await connection.execute(query, *(params or []))
                    affected = int(result.split()[-1]) if result and 'INSERT' in result or 'UPDATE' in result or 'DELETE' in result else 0
                    return QueryResult(success=True, affected_rows=affected)
        
        except Exception as e:
            logger.error(f"Raw query failed: {e}")
            return QueryResult(success=False, error=str(e))
    
    async def execute(self, query: str, *params):
        """Execute query with parameters and return as list of dicts"""
        async with self.acquire() as connection:
            rows = await connection.fetch(query, *params)
            return [dict(row) for row in rows] if rows else []


class SecureTransactionManager:
    """Manage database transactions securely"""
    
    def __init__(self, db: SecureDatabaseConnection):
        self.db = db
    
    @asynccontextmanager
    async def transaction(self):
        """Execute operations in a transaction"""
        async with self.db.acquire() as connection:
            async with connection.transaction():
                yield SecureQueryExecutor(connection)


class SecureQueryExecutor:
    """Execute queries within a transaction"""
    
    def __init__(self, connection):
        self.connection = connection
    
    async def execute(self, query: str, *params):
        """Execute query with parameters"""
        return await self.connection.execute(query, *params)
    
    async def fetch(self, query: str, *params):
        """Fetch results with parameters"""
        rows = await self.connection.fetch(query, *params)
        return [dict(row) for row in rows] if rows else []
    
    async def fetchrow(self, query: str, *params):
        """Fetch single row with parameters"""
        row = await self.connection.fetchrow(query, *params)
        return dict(row) if row else None


# Example usage
async def example_usage():
    """Example of secure database usage"""
    config = {
        'host': 'localhost',
        'port': 5434,
        'database': 'ai_engine',
        'user': 'weedgo',
        'password': 'secure_password'
    }
    
    db = SecureDatabaseConnection(config)
    await db.initialize()
    
    try:
        # Safe SELECT
        result = await db.select(
            table='products',
            columns=['id', 'name', 'price'],
            where={'category': 'flower', 'thc_content': 20},
            order_by='price DESC',
            limit=10
        )
        
        if result.success:
            print(f"Found {len(result.data)} products")
        
        # Safe INSERT
        result = await db.insert(
            table='orders',
            data={
                'user_id': 123,
                'total': 99.99,
                'status': 'pending'
            },
            returning=['id', 'created_at']
        )
        
        if result.success:
            print(f"Order created: {result.data}")
        
        # Safe UPDATE
        result = await db.update(
            table='orders',
            data={'status': 'completed'},
            where={'id': 456}
        )
        
        if result.success:
            print(f"Updated {result.affected_rows} orders")
        
        # Safe DELETE
        result = await db.delete(
            table='orders',
            where={'status': 'cancelled', 'created_at': '2024-01-01'}
        )
        
        if result.success:
            print(f"Deleted {result.affected_rows} orders")
    
    finally:
        await db.close()

# Backward compatibility alias
SecureDatabase = SecureDatabaseConnection