"""Context persistence interface and implementations"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import logging
from dataclasses import dataclass, asdict
import asyncpg
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class ContextEntry:
    """Single context entry"""
    session_id: str
    user_id: Optional[str]
    agent_id: Optional[str]
    role: str  # 'user', 'assistant', 'system'
    content: str
    metadata: Optional[Dict] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat() if self.timestamp else None
        return data

class IContextStore(ABC):
    """Interface for context storage"""
    
    @abstractmethod
    async def save_context(self, entry: ContextEntry) -> bool:
        """Save a context entry"""
        pass
    
    @abstractmethod
    async def get_context(self, session_id: str, limit: int = 10) -> List[ContextEntry]:
        """Get context for a session"""
        pass
    
    @abstractmethod
    async def clear_context(self, session_id: str) -> bool:
        """Clear context for a session"""
        pass
    
    @abstractmethod
    async def search_context(self, query: str, session_id: Optional[str] = None) -> List[ContextEntry]:
        """Search context entries"""
        pass

class MemoryContextStore(IContextStore):
    """In-memory context storage (for testing)"""
    
    def __init__(self, max_entries_per_session: int = 100):
        self.contexts: Dict[str, List[ContextEntry]] = {}
        self.max_entries = max_entries_per_session
    
    async def save_context(self, entry: ContextEntry) -> bool:
        """Save context entry to memory"""
        if entry.session_id not in self.contexts:
            self.contexts[entry.session_id] = []
        
        self.contexts[entry.session_id].append(entry)
        
        # Trim if exceeds max entries
        if len(self.contexts[entry.session_id]) > self.max_entries:
            self.contexts[entry.session_id] = self.contexts[entry.session_id][-self.max_entries:]
        
        return True
    
    async def get_context(self, session_id: str, limit: int = 10) -> List[ContextEntry]:
        """Get recent context for a session"""
        if session_id not in self.contexts:
            return []
        return self.contexts[session_id][-limit:]
    
    async def clear_context(self, session_id: str) -> bool:
        """Clear context for a session"""
        if session_id in self.contexts:
            del self.contexts[session_id]
        return True
    
    async def search_context(self, query: str, session_id: Optional[str] = None) -> List[ContextEntry]:
        """Search context entries"""
        results = []
        sessions = [session_id] if session_id else self.contexts.keys()
        
        for sid in sessions:
            if sid in self.contexts:
                for entry in self.contexts[sid]:
                    if query.lower() in entry.content.lower():
                        results.append(entry)
        
        return results

class DatabaseContextStore(IContextStore):
    """PostgreSQL context storage"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.pool = None
    
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(self.connection_string)
            await self._create_table_if_not_exists()
        except Exception as e:
            logger.error(f"Failed to initialize database context store: {e}")
            raise
    
    async def _create_table_if_not_exists(self):
        """Create context table if it doesn't exist"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS context_history (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL,
                    user_id VARCHAR(255),
                    agent_id VARCHAR(255),
                    role VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    metadata JSONB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_session_id (session_id),
                    INDEX idx_timestamp (timestamp)
                )
            ''')
    
    async def save_context(self, entry: ContextEntry) -> bool:
        """Save context entry to database"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO context_history 
                    (session_id, user_id, agent_id, role, content, metadata, timestamp)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                ''', entry.session_id, entry.user_id, entry.agent_id, entry.role,
                    entry.content, json.dumps(entry.metadata) if entry.metadata else None,
                    entry.timestamp)
                return True
        except Exception as e:
            logger.error(f"Failed to save context: {e}")
            return False
    
    async def get_context(self, session_id: str, limit: int = 10) -> List[ContextEntry]:
        """Get recent context for a session"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT * FROM context_history
                    WHERE session_id = $1
                    ORDER BY timestamp DESC
                    LIMIT $2
                ''', session_id, limit)
                
                entries = []
                for row in reversed(rows):  # Reverse to get chronological order
                    entries.append(ContextEntry(
                        session_id=row['session_id'],
                        user_id=row['user_id'],
                        agent_id=row['agent_id'],
                        role=row['role'],
                        content=row['content'],
                        metadata=json.loads(row['metadata']) if row['metadata'] else None,
                        timestamp=row['timestamp']
                    ))
                return entries
        except Exception as e:
            logger.error(f"Failed to get context: {e}")
            return []
    
    async def clear_context(self, session_id: str) -> bool:
        """Clear context for a session"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    'DELETE FROM context_history WHERE session_id = $1',
                    session_id
                )
                return True
        except Exception as e:
            logger.error(f"Failed to clear context: {e}")
            return False
    
    async def search_context(self, query: str, session_id: Optional[str] = None) -> List[ContextEntry]:
        """Search context entries using full-text search"""
        try:
            async with self.pool.acquire() as conn:
                sql = '''
                    SELECT * FROM context_history
                    WHERE content ILIKE $1
                '''
                params = [f'%{query}%']
                
                if session_id:
                    sql += ' AND session_id = $2'
                    params.append(session_id)
                
                sql += ' ORDER BY timestamp DESC LIMIT 50'
                
                rows = await conn.fetch(sql, *params)
                
                entries = []
                for row in rows:
                    entries.append(ContextEntry(
                        session_id=row['session_id'],
                        user_id=row['user_id'],
                        agent_id=row['agent_id'],
                        role=row['role'],
                        content=row['content'],
                        metadata=json.loads(row['metadata']) if row['metadata'] else None,
                        timestamp=row['timestamp']
                    ))
                return entries
        except Exception as e:
            logger.error(f"Failed to search context: {e}")
            return []
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()

class ContextManager:
    """Manages context for AI conversations"""
    
    def __init__(self, store: IContextStore, config: Dict = None):
        self.store = store
        self.config = config or {}
        self.max_context_length = self.config.get('max_context_length', 4000)
        self.context_window_size = self.config.get('context_window_size', 10)
    
    async def add_message(self, session_id: str, role: str, content: str, 
                          user_id: Optional[str] = None, agent_id: Optional[str] = None,
                          metadata: Optional[Dict] = None):
        """Add a message to context"""
        entry = ContextEntry(
            session_id=session_id,
            user_id=user_id,
            agent_id=agent_id,
            role=role,
            content=content,
            metadata=metadata
        )
        return await self.store.save_context(entry)
    
    async def get_conversation_context(self, session_id: str) -> str:
        """Get formatted conversation context for LLM"""
        entries = await self.store.get_context(session_id, self.context_window_size)
        
        context_parts = []
        total_length = 0
        
        for entry in reversed(entries):  # Start from most recent
            formatted = f"{entry.role}: {entry.content}"
            entry_length = len(formatted)
            
            if total_length + entry_length > self.max_context_length:
                break
            
            context_parts.insert(0, formatted)
            total_length += entry_length
        
        return "\n".join(context_parts)
    
    async def summarize_context(self, session_id: str) -> Optional[str]:
        """Get a summary of the conversation context"""
        entries = await self.store.get_context(session_id, 50)
        
        if not entries:
            return None
        
        # Build summary of conversation topics
        topics = set()
        for entry in entries:
            if entry.role == 'user':
                # Extract key topics from user messages
                words = entry.content.lower().split()
                for word in words:
                    if len(word) > 4:  # Skip short words
                        topics.add(word)
        
        return f"Previous conversation topics: {', '.join(list(topics)[:10])}"