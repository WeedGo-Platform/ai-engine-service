"""
Base Repository - Abstract base class for repositories
Implements common database operations
"""

import logging
from typing import Dict, Any, List, Optional
import asyncpg
from contextlib import asynccontextmanager

from config import settings

logger = logging.getLogger(__name__)

class BaseRepository:
    """
    Base repository with common database operations
    Template Method Pattern: Common operations with customization points
    """
    
    def __init__(self, table_name: str):
        """Initialize repository with table name"""
        self.table_name = table_name
        self._pool: Optional[asyncpg.Pool] = None
    
    async def get_pool(self) -> asyncpg.Pool:
        """Get or create connection pool"""
        if not self._pool:
            self._pool = await asyncpg.create_pool(
                settings.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
        return self._pool
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool"""
        pool = await self.get_pool()
        async with pool.acquire() as connection:
            yield connection
    
    async def execute(self, query: str, *args) -> str:
        """Execute a query without returning results"""
        async with self.get_connection() as conn:
            return await conn.execute(query, *args)
    
    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Fetch single row as dictionary"""
        async with self.get_connection() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None
    
    async def fetch_many(self, query: str, *args) -> List[Dict[str, Any]]:
        """Fetch multiple rows as list of dictionaries"""
        async with self.get_connection() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
    
    async def insert(self, data: Dict[str, Any]) -> Any:
        """Insert record and return ID"""
        columns = ", ".join(data.keys())
        placeholders = ", ".join(f"${i+1}" for i in range(len(data)))
        
        query = f"""
            INSERT INTO {self.table_name} ({columns})
            VALUES ({placeholders})
            RETURNING id
        """
        
        async with self.get_connection() as conn:
            result = await conn.fetchval(query, *data.values())
            return result
    
    async def update(self, id: Any, data: Dict[str, Any]) -> bool:
        """Update record by ID"""
        set_clause = ", ".join(
            f"{key} = ${i+2}" for i, key in enumerate(data.keys())
        )
        
        query = f"""
            UPDATE {self.table_name}
            SET {set_clause}
            WHERE id = $1
        """
        
        async with self.get_connection() as conn:
            result = await conn.execute(query, id, *data.values())
            return result != "UPDATE 0"
    
    async def delete(self, id: Any) -> bool:
        """Delete record by ID"""
        query = f"DELETE FROM {self.table_name} WHERE id = $1"
        
        async with self.get_connection() as conn:
            result = await conn.execute(query, id)
            return result != "DELETE 0"
    
    async def exists(self, **kwargs) -> bool:
        """Check if record exists with given conditions"""
        conditions = " AND ".join(
            f"{key} = ${i+1}" for i, key in enumerate(kwargs.keys())
        )
        
        query = f"""
            SELECT EXISTS(
                SELECT 1 FROM {self.table_name}
                WHERE {conditions}
            )
        """
        
        async with self.get_connection() as conn:
            return await conn.fetchval(query, *kwargs.values())
    
    async def count(self, **kwargs) -> int:
        """Count records with given conditions"""
        if kwargs:
            conditions = " AND ".join(
                f"{key} = ${i+1}" for i, key in enumerate(kwargs.keys())
            )
            query = f"""
                SELECT COUNT(*) FROM {self.table_name}
                WHERE {conditions}
            """
            values = list(kwargs.values())
        else:
            query = f"SELECT COUNT(*) FROM {self.table_name}"
            values = []
        
        async with self.get_connection() as conn:
            return await conn.fetchval(query, *values)
    
    async def cleanup(self):
        """Clean up resources"""
        if self._pool:
            await self._pool.close()
            self._pool = None