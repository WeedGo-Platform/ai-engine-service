"""
Database setup and management for AGI system
"""

import asyncio
import asyncpg
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime
import json

from agi.config.agi_config import get_config

logger = logging.getLogger(__name__)

class AGIDatabaseManager:
    """Manages database connections and schema for AGI system"""

    def __init__(self):
        self.config = get_config().database
        self.pool: Optional[asyncpg.Pool] = None

    async def initialize(self) -> None:
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                min_size=self.config.pool_min_size,
                max_size=self.config.pool_max_size
            )
            logger.info(f"Database pool initialized with {self.config.pool_min_size}-{self.config.pool_max_size} connections")

            # Create schema if not exists
            await self._create_schema()

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    async def _create_schema(self) -> None:
        """Create AGI schema and tables"""
        async with self.pool.acquire() as conn:
            # Create schema
            await conn.execute(f"""
                CREATE SCHEMA IF NOT EXISTS {self.config.schema_prefix}
            """)

            # Create tables with agi prefix
            await self._create_tables(conn)

            logger.info(f"Database schema '{self.config.schema_prefix}' initialized")

    async def _create_tables(self, conn: asyncpg.Connection) -> None:
        """Create all required tables"""

        # Sessions table
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.config.schema_prefix}.sessions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id VARCHAR(255),
                user_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                metadata JSONB DEFAULT '{{}}'::jsonb,
                is_active BOOLEAN DEFAULT true
            )
        """)

        # Conversations table
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.config.schema_prefix}.conversations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id UUID REFERENCES {self.config.schema_prefix}.sessions(id) ON DELETE CASCADE,
                role VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT NOW(),
                metadata JSONB DEFAULT '{{}}'::jsonb,
                embedding JSONB,
                tokens_used INTEGER DEFAULT 0
            )
        """)

        # Agents table
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.config.schema_prefix}.agents (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) UNIQUE NOT NULL,
                type VARCHAR(50) NOT NULL,
                configuration JSONB NOT NULL,
                capabilities JSONB DEFAULT '[]'::jsonb,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Tools table
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.config.schema_prefix}.tools (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) UNIQUE NOT NULL,
                description TEXT,
                parameters JSONB NOT NULL,
                category VARCHAR(100),
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Tool executions table
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.config.schema_prefix}.tool_executions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id UUID REFERENCES {self.config.schema_prefix}.sessions(id) ON DELETE CASCADE,
                tool_id UUID REFERENCES {self.config.schema_prefix}.tools(id),
                input_params JSONB,
                output JSONB,
                success BOOLEAN,
                error_message TEXT,
                execution_time_ms INTEGER,
                executed_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Knowledge documents table
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.config.schema_prefix}.knowledge_documents (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id VARCHAR(255),
                title VARCHAR(500),
                content TEXT NOT NULL,
                source VARCHAR(500),
                metadata JSONB DEFAULT '{{}}'::jsonb,
                embedding JSONB,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Episodic memory table
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.config.schema_prefix}.episodic_memory (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id UUID REFERENCES {self.config.schema_prefix}.sessions(id) ON DELETE CASCADE,
                episode_type VARCHAR(100),
                content JSONB NOT NULL,
                importance_score FLOAT DEFAULT 0.5,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Model registry table
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.config.schema_prefix}.model_registry (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                model_name VARCHAR(255) UNIQUE NOT NULL,
                model_path VARCHAR(500),
                model_size VARCHAR(50),
                context_length INTEGER,
                capabilities JSONB DEFAULT '[]'::jsonb,
                performance_metrics JSONB DEFAULT '{{}}'::jsonb,
                is_active BOOLEAN DEFAULT true,
                loaded BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Metrics table
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.config.schema_prefix}.metrics (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                metric_type VARCHAR(100) NOT NULL,
                operation VARCHAR(255),
                value FLOAT,
                metadata JSONB DEFAULT '{{}}'::jsonb,
                timestamp TIMESTAMP DEFAULT NOW()
            )
        """)

        # Agent configurations table
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.config.schema_prefix}.agent_configurations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id VARCHAR(255),
                agent_name VARCHAR(255) NOT NULL,
                personality JSONB,
                tools JSONB DEFAULT '[]'::jsonb,
                knowledge_sources JSONB DEFAULT '[]'::jsonb,
                constraints JSONB DEFAULT '{{}}'::jsonb,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(tenant_id, agent_name)
            )
        """)

        # Create indexes
        await self._create_indexes(conn)

    async def _create_indexes(self, conn: asyncpg.Connection) -> None:
        """Create database indexes for performance"""

        # Session indexes
        await conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_sessions_tenant_user
            ON {self.config.schema_prefix}.sessions(tenant_id, user_id)
        """)

        # Conversation indexes
        await conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_conversations_session
            ON {self.config.schema_prefix}.conversations(session_id)
        """)

        await conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_conversations_timestamp
            ON {self.config.schema_prefix}.conversations(timestamp DESC)
        """)

        # Knowledge document indexes
        await conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_knowledge_tenant
            ON {self.config.schema_prefix}.knowledge_documents(tenant_id)
        """)

        # Episodic memory indexes
        await conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_episodic_session
            ON {self.config.schema_prefix}.episodic_memory(session_id)
        """)

        await conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_episodic_importance
            ON {self.config.schema_prefix}.episodic_memory(importance_score DESC)
        """)

        # Metrics indexes
        await conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_metrics_type_timestamp
            ON {self.config.schema_prefix}.metrics(metric_type, timestamp DESC)
        """)

    async def get_connection(self) -> asyncpg.Connection:
        """Get a database connection from the pool"""
        if not self.pool:
            await self.initialize()
        return await self.pool.acquire()

    async def release_connection(self, conn: asyncpg.Connection) -> None:
        """Release a connection back to the pool"""
        if self.pool:
            await self.pool.release(conn)

    async def close(self) -> None:
        """Close the database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")

    # Helper methods for common operations
    async def create_session(
        self,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new session"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(f"""
                INSERT INTO {self.config.schema_prefix}.sessions
                (tenant_id, user_id, metadata)
                VALUES ($1, $2, $3)
                RETURNING id
            """, tenant_id, user_id, json.dumps(metadata or {}))
            return str(result['id'])

    async def add_conversation_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        tokens_used: int = 0
    ) -> str:
        """Add a message to conversation history"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(f"""
                INSERT INTO {self.config.schema_prefix}.conversations
                (session_id, role, content, metadata, tokens_used)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, session_id, role, content, json.dumps(metadata or {}), tokens_used)
            return str(result['id'])

    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(f"""
                SELECT role, content, timestamp, metadata
                FROM {self.config.schema_prefix}.conversations
                WHERE session_id = $1
                ORDER BY timestamp DESC
                LIMIT $2
            """, session_id, limit)

            return [
                {
                    'role': row['role'],
                    'content': row['content'],
                    'timestamp': row['timestamp'].isoformat(),
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {}
                }
                for row in reversed(rows)  # Reverse to get chronological order
            ]

    async def register_model(
        self,
        model_name: str,
        model_path: str,
        model_size: str,
        context_length: int,
        capabilities: List[str] = None
    ) -> str:
        """Register a model in the registry"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(f"""
                INSERT INTO {self.config.schema_prefix}.model_registry
                (model_name, model_path, model_size, context_length, capabilities)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (model_name)
                DO UPDATE SET
                    model_path = EXCLUDED.model_path,
                    model_size = EXCLUDED.model_size,
                    context_length = EXCLUDED.context_length,
                    capabilities = EXCLUDED.capabilities,
                    updated_at = NOW()
                RETURNING id
            """, model_name, model_path, model_size, context_length,
                json.dumps(capabilities or []))
            return str(result['id'])

    async def get_active_models(self) -> List[Dict[str, Any]]:
        """Get all active models from registry"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(f"""
                SELECT model_name, model_path, model_size, context_length,
                       capabilities, loaded
                FROM {self.config.schema_prefix}.model_registry
                WHERE is_active = true
                ORDER BY model_size, model_name
            """)

            return [
                {
                    'name': row['model_name'],
                    'path': row['model_path'],
                    'size': row['model_size'],
                    'context_length': row['context_length'],
                    'capabilities': json.loads(row['capabilities']) if row['capabilities'] else [],
                    'loaded': row['loaded']
                }
                for row in rows
            ]

    async def record_metric(
        self,
        metric_type: str,
        operation: str,
        value: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a metric"""
        async with self.pool.acquire() as conn:
            await conn.execute(f"""
                INSERT INTO {self.config.schema_prefix}.metrics
                (metric_type, operation, value, metadata)
                VALUES ($1, $2, $3, $4)
            """, metric_type, operation, value, json.dumps(metadata or {}))

    async def execute(self, query: str, *args) -> None:
        """Execute a query without returning results"""
        async with self.pool.acquire() as conn:
            await conn.execute(query, *args)

    async def fetchone(self, query: str, *args) -> Optional[asyncpg.Record]:
        """Execute a query and fetch one result"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchall(self, query: str, *args) -> List[asyncpg.Record]:
        """Execute a query and fetch all results"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

# Singleton instance
_db_manager: Optional[AGIDatabaseManager] = None

async def get_db_manager() -> AGIDatabaseManager:
    """Get the singleton database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = AGIDatabaseManager()
        await _db_manager.initialize()
    return _db_manager