"""Context management for conversation persistence"""

from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

class IContextStore(ABC):
    """Interface for context storage"""
    
    @abstractmethod
    async def get(self, session_id: str) -> Optional[Dict]:
        pass
    
    @abstractmethod
    async def set(self, session_id: str, context: Dict):
        pass
    
    @abstractmethod
    async def delete(self, session_id: str):
        pass

class MemoryContextStore(IContextStore):
    """In-memory context storage"""
    
    def __init__(self, ttl_seconds: int = 3600):
        self.storage: Dict[str, Dict] = {}
        self.ttl_seconds = ttl_seconds
        logger.info("MemoryContextStore initialized")
    
    async def get(self, session_id: str) -> Optional[Dict]:
        """Get context for session"""
        if session_id in self.storage:
            context = self.storage[session_id]
            # Check if expired
            if 'timestamp' in context:
                age = (datetime.now() - context['timestamp']).seconds
                if age > self.ttl_seconds:
                    del self.storage[session_id]
                    return None
            return context
        return None
    
    async def set(self, session_id: str, context: Dict):
        """Store context for session"""
        context['timestamp'] = datetime.now()
        self.storage[session_id] = context
    
    async def delete(self, session_id: str):
        """Delete context for session"""
        if session_id in self.storage:
            del self.storage[session_id]

class DatabaseContextStore(IContextStore):
    """Database-backed context storage"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        logger.info("DatabaseContextStore initialized")
    
    async def get(self, session_id: str) -> Optional[Dict]:
        # Placeholder for database implementation
        return None
    
    async def set(self, session_id: str, context: Dict):
        # Placeholder for database implementation
        pass
    
    async def delete(self, session_id: str):
        # Placeholder for database implementation
        pass

class ContextManager:
    """Manages conversation context"""
    
    def __init__(self, store: Optional[IContextStore] = None):
        self.store = store or MemoryContextStore()
        logger.info("ContextManager initialized")
    
    async def get_context(self, session_id: str) -> Dict:
        """Get or create context for session"""
        context = await self.store.get(session_id)
        if not context:
            context = {
                'session_id': session_id,
                'messages': [],
                'user_preferences': {},
                'created_at': datetime.now().isoformat()
            }
            await self.store.set(session_id, context)
        return context
    
    async def add_message(self, session_id: str, role: str, content: str):
        """Add message to conversation history"""
        context = await self.get_context(session_id)
        context['messages'].append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 20 messages
        if len(context['messages']) > 20:
            context['messages'] = context['messages'][-20:]
        
        await self.store.set(session_id, context)
    
    async def clear_context(self, session_id: str):
        """Clear context for session"""
        await self.store.delete(session_id)