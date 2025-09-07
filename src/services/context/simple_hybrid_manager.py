"""
Simplified Hybrid Context Manager
Pure context persistence without entity extraction or medical features
Focuses on efficient storage and retrieval of conversation history
"""

import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import deque

from .base import MemoryContextStore
from .database_store import DatabaseContextStore

logger = logging.getLogger(__name__)


class SimpleHybridContextManager:
    """
    Simplified hybrid context manager for conversation persistence
    Combines memory caching with database storage for optimal performance
    """
    
    def __init__(self, 
                 db_config: Optional[Dict] = None,
                 memory_ttl: int = 3600,
                 max_memory_sessions: int = 100,
                 max_history_length: int = 50):
        """
        Initialize hybrid context manager
        
        Args:
            db_config: Database configuration
            memory_ttl: TTL for memory cache in seconds
            max_memory_sessions: Maximum sessions to keep in memory
            max_history_length: Maximum messages to keep in history
        """
        # Initialize storage layers
        self.memory_store = MemoryContextStore(ttl_seconds=memory_ttl)
        self.db_store = DatabaseContextStore(**(db_config or {}))
        
        # We'll manage sessions separately with history tracking
        self.sessions = {}
        
        # Configuration
        self.memory_ttl = memory_ttl
        self.max_memory_sessions = max_memory_sessions
        self.max_history_length = max_history_length
        
        # Cache management
        self._session_cache = {}
        self._cache_timestamps = {}
        self._lock = asyncio.Lock()
        
        logger.info("SimpleHybridContextManager initialized")
    
    async def initialize(self):
        """Initialize database connections"""
        await self.db_store.initialize()
        logger.info("SimpleHybridContextManager database initialized")
    
    async def close(self):
        """Close database connections"""
        await self.db_store.close()
    
    async def get_context(self, session_id: str, customer_id: Optional[str] = None) -> Dict:
        """
        Get context for a session with multi-tier lookup
        
        Args:
            session_id: Session identifier
            customer_id: Optional customer identifier
            
        Returns:
            Context dictionary with session information
        """
        async with self._lock:
            # L1: Check memory cache
            if session_id in self._session_cache:
                cache_age = (datetime.now() - self._cache_timestamps[session_id]).seconds
                if cache_age < self.memory_ttl:
                    logger.debug(f"Cache hit for session {session_id}")
                    return self._session_cache[session_id]
            
            # L2: Check sessions
            if session_id in self.sessions:
                logger.debug(f"Memory store hit for session {session_id}")
                context = self.sessions[session_id].get('context', {})
                self._update_cache(session_id, context)
                return context
            
            # L3: Load from database
            db_conversation = await self.db_store.get_conversation(session_id)
            if db_conversation:
                logger.debug(f"Database hit for session {session_id}")
                
                # Restore to memory store
                self.sessions[session_id] = {
                    'context': db_conversation['context'],
                    'history': deque(db_conversation['messages'], maxlen=self.max_history_length),
                    'created_at': db_conversation['created_at'],
                    'last_activity': datetime.now().isoformat()
                }
                
                self._update_cache(session_id, db_conversation['context'])
                return db_conversation['context']
            
            # Create new context
            new_context = {
                'session_id': session_id,
                'customer_id': customer_id,
                'created_at': datetime.now().isoformat(),
                'message_count': 0,
                'last_activity': datetime.now().isoformat()
            }
            
            # Initialize in all layers
            self.sessions[session_id] = {
                'context': new_context,
                'history': deque(maxlen=self.max_history_length),
                'created_at': new_context['created_at'],
                'last_activity': new_context['last_activity']
            }
            
            self._update_cache(session_id, new_context)
            
            # Save to database
            await self.db_store.save_conversation(
                session_id, [], new_context, customer_id
            )
            
            return new_context
    
    async def add_message(self, 
                         session_id: str,
                         role: str,
                         content: str,
                         customer_id: Optional[str] = None,
                         metadata: Optional[Dict] = None) -> None:
        """
        Add a message to the conversation history
        
        Args:
            session_id: Session identifier
            role: Message role (user/assistant)
            content: Message content
            customer_id: Optional customer identifier
            metadata: Optional metadata for the message
        """
        timestamp = datetime.now().isoformat()
        
        # Create message object
        message = {
            'role': role,
            'content': content,
            'timestamp': timestamp
        }
        
        if metadata:
            message['metadata'] = metadata
        
        # Get current context
        context = await self.get_context(session_id, customer_id)
        
        # Update memory store
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'context': context,
                'history': deque(maxlen=self.max_history_length),
                'created_at': timestamp,
                'last_activity': timestamp
            }
        
        session = self.sessions[session_id]
        session['history'].append(message)
        session['last_activity'] = timestamp
        
        # Update context
        context['message_count'] = len(session['history'])
        context['last_activity'] = timestamp
        
        # Update all storage layers
        self._update_cache(session_id, context)
        self.sessions[session_id]['context'] = context
        
        # Save to database asynchronously
        asyncio.create_task(self._persist_to_database(
            session_id, list(session['history']), context, customer_id
        ))
    
    async def add_interaction(self, 
                            session_id: str,
                            user_message: str,
                            ai_response: str,
                            customer_id: Optional[str] = None,
                            metadata: Optional[Dict] = None) -> None:
        """
        Add a complete interaction (user message + AI response)
        
        Args:
            session_id: Session identifier
            user_message: User's message
            ai_response: AI's response
            customer_id: Optional customer identifier
            metadata: Optional metadata for the interaction
        """
        # Add user message
        await self.add_message(session_id, 'user', user_message, customer_id, metadata)
        
        # Add AI response
        await self.add_message(session_id, 'assistant', ai_response, customer_id, metadata)
        
        # Also save as interaction record for analytics
        if hasattr(self.db_store, 'add_interaction'):
            await self.db_store.add_interaction(
                session_id, user_message, ai_response,
                response_time=metadata.get('response_time') if metadata else None,
                metadata=metadata,
                customer_id=customer_id
            )
    
    async def get_history(self, 
                         session_id: str, 
                         limit: Optional[int] = None) -> List[Dict]:
        """
        Get conversation history for a session
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return
            
        Returns:
            List of message dictionaries
        """
        # Try memory first
        session = self.sessions.get(session_id, {})
        history = list(session.get('history', []))
        
        if not history:
            # Load from database
            db_conversation = await self.db_store.get_conversation(session_id)
            if db_conversation:
                history = db_conversation.get('messages', [])
                
                # Restore to memory
                session['history'] = deque(history, maxlen=self.max_history_length)
        
        # Apply limit if specified
        if limit and len(history) > limit:
            return history[-limit:]
        
        return history
    
    async def get_formatted_history(self, 
                                   session_id: str,
                                   limit: int = 10,
                                   format_style: str = 'simple') -> str:
        """
        Get formatted conversation history for prompt inclusion
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages
            format_style: Formatting style ('simple', 'detailed')
            
        Returns:
            Formatted history string
        """
        history = await self.get_history(session_id, limit)
        
        if not history:
            return ""
        
        if format_style == 'simple':
            # Simple format: role: content
            lines = []
            for msg in history:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                # Truncate very long messages
                if len(content) > 500:
                    content = content[:497] + "..."
                lines.append(f"{role}: {content}")
            return "\n".join(lines)
        
        elif format_style == 'detailed':
            # Detailed format with timestamps
            lines = []
            for msg in history:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                timestamp = msg.get('timestamp', '')
                if len(content) > 500:
                    content = content[:497] + "..."
                lines.append(f"[{timestamp}] {role}: {content}")
            return "\n".join(lines)
        
        return str(history)
    
    async def clear_session(self, session_id: str) -> None:
        """
        Clear a session from all storage layers
        
        Args:
            session_id: Session identifier
        """
        async with self._lock:
            # Clear from cache
            if session_id in self._session_cache:
                del self._session_cache[session_id]
            if session_id in self._cache_timestamps:
                del self._cache_timestamps[session_id]
            
            # Clear from memory store
            if session_id in self.sessions:
                del self.sessions[session_id]
            
            # Note: We don't delete from database to maintain history
            logger.info(f"Cleared session {session_id} from memory")
    
    async def _persist_to_database(self,
                                  session_id: str,
                                  history: List[Dict],
                                  context: Dict,
                                  customer_id: Optional[str]):
        """
        Persist data to database (runs asynchronously)
        """
        try:
            # Save conversation
            await self.db_store.save_conversation(
                session_id, history, context, customer_id
            )
            
            # Update customer profile if customer_id provided
            if customer_id:
                await self.db_store.update_customer_profile(
                    customer_id,
                    increment_interaction=True
                )
            
            logger.debug(f"Persisted session {session_id} to database")
            
        except Exception as e:
            logger.error(f"Failed to persist to database: {e}")
    
    def _update_cache(self, session_id: str, context: Dict):
        """Update memory cache"""
        self._session_cache[session_id] = context
        self._cache_timestamps[session_id] = datetime.now()
        
        # Evict oldest session if cache is full
        if len(self._session_cache) > self.max_memory_sessions:
            # Find oldest session
            oldest_session = min(
                self._cache_timestamps.items(),
                key=lambda x: x[1]
            )[0]
            
            del self._session_cache[oldest_session]
            del self._cache_timestamps[oldest_session]
            logger.debug(f"Evicted session {oldest_session} from cache")
    
    async def get_stats(self) -> Dict:
        """
        Get context manager statistics
        
        Returns:
            Statistics dictionary
        """
        db_stats = await self.db_store.get_session_stats()
        
        return {
            'memory_sessions': len(self.sessions),
            'cached_sessions': len(self._session_cache),
            'database_stats': db_stats,
            'memory_ttl_seconds': self.memory_ttl,
            'max_history_length': self.max_history_length
        }
    
    async def cleanup_old_sessions(self, days: int = 7) -> int:
        """
        Clean up old sessions from database
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of sessions cleaned up
        """
        return await self.db_store.cleanup_old_sessions(days)