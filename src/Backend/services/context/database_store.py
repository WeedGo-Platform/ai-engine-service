"""
Database-backed Context Storage Implementation
Provides persistent storage for conversation context using PostgreSQL
Follows SOLID principles with interface segregation and dependency injection
"""

import json
import logging
import uuid
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import asyncpg
from asyncpg.pool import Pool

logger = logging.getLogger(__name__)


class DatabaseContextStore:
    """
    PostgreSQL-backed context storage implementation
    Single Responsibility: Persistent context storage and retrieval
    """
    
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 5434,
                 database: str = "ai_engine",
                 user: str = "weedgo",
                 password: str = "weedgo123",
                 min_connections: int = 2,
                 max_connections: int = 10):
        """
        Initialize database context store with connection pooling
        
        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
            min_connections: Minimum pool connections
            max_connections: Maximum pool connections
        """
        self.connection_config = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password,
            'min_size': min_connections,
            'max_size': max_connections
        }
        self.pool: Optional[Pool] = None
        self._lock = asyncio.Lock()
        
    async def initialize(self):
        """Initialize database connection pool"""
        if not self.pool:
            async with self._lock:
                if not self.pool:
                    try:
                        self.pool = await asyncpg.create_pool(**self.connection_config)
                        logger.info("Database connection pool initialized")
                    except Exception as e:
                        logger.error(f"Failed to initialize database pool: {e}")
                        raise
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Database connection pool closed")
    
    @asynccontextmanager
    async def acquire_connection(self):
        """Context manager for acquiring database connection"""
        if not self.pool:
            await self.initialize()
        
        async with self.pool.acquire() as connection:
            yield connection
    
    async def get_conversation(self, session_id: str) -> Optional[Dict]:
        """
        Get conversation context from database
        
        Args:
            session_id: Session identifier
            
        Returns:
            Conversation context dictionary or None
        """
        try:
            async with self.acquire_connection() as conn:
                row = await conn.fetchrow("""
                    SELECT conversation_id, session_id, customer_id, 
                           messages, context, created_at, updated_at
                    FROM ai_conversations
                    WHERE session_id = $1
                    ORDER BY created_at DESC
                    LIMIT 1
                """, session_id)
                
                if row:
                    return {
                        'conversation_id': str(row['conversation_id']),
                        'session_id': row['session_id'],
                        'customer_id': row['customer_id'],
                        'messages': row['messages'] or [],
                        'context': row['context'] or {},
                        'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                        'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None
                    }
                return None
                
        except Exception as e:
            logger.error(f"Failed to get conversation for session {session_id}: {e}")
            return None
    
    async def save_conversation(self, 
                                session_id: str,
                                messages: List[Dict],
                                context: Dict,
                                customer_id: Optional[str] = None) -> bool:
        """
        Save or update conversation in database
        
        Args:
            session_id: Session identifier
            messages: List of message dictionaries
            context: Context dictionary
            customer_id: Optional customer identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            async with self.acquire_connection() as conn:
                # Check if conversation exists
                existing = await self.get_conversation(session_id)
                
                if existing:
                    # Update existing conversation
                    await conn.execute("""
                        UPDATE ai_conversations
                        SET messages = $1,
                            context = $2,
                            customer_id = COALESCE($3, customer_id),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE session_id = $4
                    """, json.dumps(messages), json.dumps(context), customer_id, session_id)
                else:
                    # Create new conversation
                    await conn.execute("""
                        INSERT INTO ai_conversations 
                        (conversation_id, session_id, customer_id, messages, context)
                        VALUES ($1, $2, $3, $4, $5)
                    """, uuid.uuid4(), session_id, customer_id, 
                        json.dumps(messages), json.dumps(context))
                
                logger.debug(f"Saved conversation for session {session_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save conversation for session {session_id}: {e}")
            return False
    
    async def add_interaction(self,
                              session_id: str,
                              user_message: str,
                              ai_response: str,
                              intent: Optional[str] = None,
                              response_time: Optional[float] = None,
                              metadata: Optional[Dict] = None,
                              customer_id: Optional[str] = None) -> bool:
        """
        Add a chat interaction to the database
        
        Args:
            session_id: Session identifier
            user_message: User's message
            ai_response: AI's response
            intent: Detected intent
            response_time: Response time in seconds
            metadata: Additional metadata
            customer_id: Optional customer identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            async with self.acquire_connection() as conn:
                await conn.execute("""
                    INSERT INTO chat_interactions 
                    (session_id, customer_id, user_message, ai_response, 
                     intent, response_time, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, session_id, customer_id, user_message, ai_response,
                    intent, response_time, json.dumps(metadata) if metadata else None)
                
                logger.debug(f"Added interaction for session {session_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to add interaction for session {session_id}: {e}")
            return False
    
    async def get_customer_profile(self, customer_id: str) -> Optional[Dict]:
        """
        Get customer profile from database
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            Customer profile dictionary or None
        """
        try:
            async with self.acquire_connection() as conn:
                row = await conn.fetchrow("""
                    SELECT id::text as customer_id, preferences, purchase_history,
                           interaction_count, last_interaction, created_at, updated_at
                    FROM profiles
                    WHERE id::text = $1
                """, customer_id)
                
                if row:
                    return {
                        'customer_id': row['customer_id'],
                        'preferences': row['preferences'] or {},
                        'purchase_history': row['purchase_history'] or [],
                        'interaction_count': row['interaction_count'],
                        'last_interaction': row['last_interaction'].isoformat() if row['last_interaction'] else None,
                        'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                        'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None
                    }
                return None
                
        except Exception as e:
            logger.error(f"Failed to get profile for customer {customer_id}: {e}")
            return None
    
    async def update_customer_profile(self,
                                     customer_id: str,
                                     preferences: Optional[Dict] = None,
                                     purchase_history: Optional[List] = None,
                                     increment_interaction: bool = True) -> bool:
        """
        Update customer profile in database
        
        Args:
            customer_id: Customer identifier
            preferences: Updated preferences
            purchase_history: Updated purchase history
            increment_interaction: Whether to increment interaction count
            
        Returns:
            True if successful, False otherwise
        """
        try:
            async with self.acquire_connection() as conn:
                # Check if profile exists
                existing = await self.get_customer_profile(customer_id)
                
                if existing:
                    # Build update query dynamically
                    updates = ["last_interaction = CURRENT_TIMESTAMP", "updated_at = CURRENT_TIMESTAMP"]
                    params = []
                    param_count = 1
                    
                    if preferences is not None:
                        updates.append(f"preferences = ${param_count}")
                        params.append(json.dumps(preferences))
                        param_count += 1
                    
                    if purchase_history is not None:
                        updates.append(f"purchase_history = ${param_count}")
                        params.append(json.dumps(purchase_history))
                        param_count += 1
                    
                    if increment_interaction:
                        updates.append("interaction_count = interaction_count + 1")
                    
                    params.append(customer_id)
                    
                    await conn.execute(f"""
                        UPDATE profiles
                        SET {', '.join(updates)}
                        WHERE id::text = ${param_count}
                    """, *params)
                else:
                    # Create new profile - need user_id for profiles table
                    # For now, create with a generated user_id
                    await conn.execute("""
                        INSERT INTO profiles
                        (user_id, preferences, purchase_history, interaction_count, last_interaction)
                        VALUES (gen_random_uuid(), $1, $2, 1, CURRENT_TIMESTAMP)
                    """,
                        json.dumps(preferences or {}),
                        json.dumps(purchase_history or []))
                
                logger.debug(f"Updated profile for customer {customer_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update profile for customer {customer_id}: {e}")
            return False
    
    async def get_recent_interactions(self, 
                                     session_id: Optional[str] = None,
                                     customer_id: Optional[str] = None,
                                     limit: int = 20) -> List[Dict]:
        """
        Get recent chat interactions
        
        Args:
            session_id: Optional session filter
            customer_id: Optional customer filter
            limit: Maximum number of interactions to return
            
        Returns:
            List of interaction dictionaries
        """
        try:
            async with self.acquire_connection() as conn:
                # Build query based on filters
                conditions = []
                params = []
                param_count = 1
                
                if session_id:
                    conditions.append(f"session_id = ${param_count}")
                    params.append(session_id)
                    param_count += 1
                
                if customer_id:
                    conditions.append(f"customer_id = ${param_count}")
                    params.append(customer_id)
                    param_count += 1
                
                params.append(limit)
                
                where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
                
                rows = await conn.fetch(f"""
                    SELECT message_id, session_id, customer_id, user_message, 
                           ai_response, intent, response_time, created_at, metadata
                    FROM chat_interactions
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT ${param_count}
                """, *params)
                
                return [
                    {
                        'message_id': row['message_id'],
                        'session_id': row['session_id'],
                        'customer_id': row['customer_id'],
                        'user_message': row['user_message'],
                        'ai_response': row['ai_response'],
                        'intent': row['intent'],
                        'response_time': row['response_time'],
                        'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                        'metadata': row['metadata'] or {}
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"Failed to get recent interactions: {e}")
            return []
    
    async def cleanup_old_sessions(self, days: int = 7) -> int:
        """
        Clean up old conversation sessions
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of sessions deleted
        """
        try:
            async with self.acquire_connection() as conn:
                result = await conn.execute("""
                    DELETE FROM ai_conversations
                    WHERE updated_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
                    RETURNING conversation_id
                """, days)
                
                deleted_count = int(result.split()[-1]) if result else 0
                
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old conversation sessions")
                
                return deleted_count
                
        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {e}")
            return 0
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """
        Get database storage statistics
        
        Returns:
            Statistics dictionary
        """
        try:
            async with self.acquire_connection() as conn:
                # Get counts
                conv_count = await conn.fetchval("SELECT COUNT(*) FROM ai_conversations")
                interaction_count = await conn.fetchval("SELECT COUNT(*) FROM chat_interactions")
                profile_count = await conn.fetchval("SELECT COUNT(*) FROM profiles")
                
                # Get recent activity
                recent_activity = await conn.fetchval("""
                    SELECT COUNT(*) FROM ai_conversations
                    WHERE updated_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
                """)
                
                return {
                    'total_conversations': conv_count,
                    'total_interactions': interaction_count,
                    'total_profiles': profile_count,
                    'active_conversations_24h': recent_activity,
                    'storage_type': 'PostgreSQL',
                    'pool_size': self.pool.get_size() if self.pool else 0
                }
                
        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            return {'error': str(e)}