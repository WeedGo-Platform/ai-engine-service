"""
Context Management Service
Implements IContextManager interface following SOLID principles
Handles conversation context and session management
"""

import json
import logging
import time
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
from datetime import datetime

# Import interface
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from core.interfaces import IContextManager

logger = logging.getLogger(__name__)


class MemoryContextStore:
    """In-memory context storage implementation"""
    
    def __init__(self, max_history_per_session: int = 100):
        """
        Initialize memory context store
        
        Args:
            max_history_per_session: Maximum history entries per session
        """
        self.sessions = defaultdict(lambda: {
            'context': {},
            'history': deque(maxlen=max_history_per_session),
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat()
        })
        self.max_history = max_history_per_session
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session data"""
        session = self.sessions[session_id]
        session['last_activity'] = datetime.now().isoformat()
        return session
    
    def update_session(self, session_id: str, data: Dict[str, Any]):
        """Update session data"""
        session = self.sessions[session_id]
        session.update(data)
        session['last_activity'] = datetime.now().isoformat()
    
    def clear_session(self, session_id: str):
        """Clear a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def get_all_sessions(self) -> List[str]:
        """Get all active session IDs"""
        return list(self.sessions.keys())


class ContextManager(IContextManager):
    """
    Context Manager implementation that handles session and conversation context
    Single Responsibility: Session and context state management
    """
    
    def __init__(self, store: Optional[MemoryContextStore] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Context Manager
        
        Args:
            store: Context storage backend (defaults to MemoryContextStore)
            config: Configuration dictionary
        """
        self.store = store or MemoryContextStore()
        self.config = config or {}
        
        # Configuration settings
        self.max_context_length = self.config.get('max_context_length', 4000)
        self.max_history_entries = self.config.get('max_history_entries', 100)
        self.context_window_size = self.config.get('context_window_size', 10)
        
        logger.info(f"ContextManager initialized with {type(self.store).__name__} storage")
    
    def get_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get context for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Context dictionary for the session
        """
        try:
            session = self.store.get_session(session_id)
            context = session.get('context', {})
            
            # Add session metadata to context
            context['session_id'] = session_id
            context['created_at'] = session.get('created_at')
            context['last_activity'] = session.get('last_activity')
            context['message_count'] = len(session.get('history', []))
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to get context for session {session_id}: {e}")
            return {'session_id': session_id, 'error': str(e)}
    
    def update_context(self, session_id: str, context: Dict[str, Any]) -> None:
        """
        Update context for a session
        
        Args:
            session_id: Session identifier
            context: Context dictionary to update
        """
        try:
            session = self.store.get_session(session_id)
            
            # Merge with existing context
            existing_context = session.get('context', {})
            existing_context.update(context)
            
            # Store updated context
            session['context'] = existing_context
            self.store.update_session(session_id, session)
            
            logger.debug(f"Updated context for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to update context for session {session_id}: {e}")
    
    def add_to_history(self, session_id: str, user_message: Dict, assistant_message: Dict) -> None:
        """
        Add messages to conversation history
        
        Args:
            session_id: Session identifier
            user_message: User message dictionary
            assistant_message: Assistant response dictionary
        """
        try:
            session = self.store.get_session(session_id)
            history = session.get('history', deque(maxlen=self.max_history_entries))
            
            # Add timestamp if not present
            timestamp = datetime.now().isoformat()
            if 'timestamp' not in user_message:
                user_message['timestamp'] = timestamp
            if 'timestamp' not in assistant_message:
                assistant_message['timestamp'] = timestamp
            
            # Add role identifiers if not present
            if 'role' not in user_message:
                user_message['role'] = 'user'
            if 'role' not in assistant_message:
                assistant_message['role'] = 'assistant'
            
            # Add to history
            history.append(user_message)
            history.append(assistant_message)
            
            # Update session
            session['history'] = history
            self.store.update_session(session_id, session)
            
            # Update message count in context
            self.update_context(session_id, {'total_messages': len(history)})
            
            logger.debug(f"Added messages to history for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to add to history for session {session_id}: {e}")
    
    def get_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        """
        Get conversation history
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return
            
        Returns:
            List of message dictionaries
        """
        try:
            session = self.store.get_session(session_id)
            history = session.get('history', deque())
            
            # Convert deque to list and apply limit
            history_list = list(history)
            
            if limit > 0 and len(history_list) > limit:
                # Return the most recent messages
                return history_list[-limit:]
            
            return history_list
            
        except Exception as e:
            logger.error(f"Failed to get history for session {session_id}: {e}")
            return []
    
    def clear_context(self, session_id: str) -> None:
        """
        Clear context for a session
        
        Args:
            session_id: Session identifier
        """
        try:
            self.store.clear_session(session_id)
            logger.info(f"Cleared context for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to clear context for session {session_id}: {e}")
    
    def get_conversation_summary(self, session_id: str) -> str:
        """
        Get a summary of the conversation for context
        
        Args:
            session_id: Session identifier
            
        Returns:
            Conversation summary string
        """
        try:
            history = self.get_history(session_id, limit=self.context_window_size)
            
            if not history:
                return ""
            
            # Build conversation summary
            summary_parts = []
            for msg in history:
                role = msg.get('role', 'unknown')
                content = msg.get('content', msg.get('message', ''))
                
                # Truncate long messages
                if len(content) > 200:
                    content = content[:197] + "..."
                
                summary_parts.append(f"{role}: {content}")
            
            summary = "\n".join(summary_parts)
            
            # Ensure summary doesn't exceed max context length
            if len(summary) > self.max_context_length:
                summary = summary[-self.max_context_length:]
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get conversation summary: {e}")
            return ""
    
    def get_context_for_generation(self, session_id: str, include_history: bool = True) -> Dict[str, Any]:
        """
        Get formatted context for text generation
        
        Args:
            session_id: Session identifier
            include_history: Whether to include conversation history
            
        Returns:
            Context dictionary formatted for generation
        """
        context = self.get_context(session_id)
        
        result = {
            'session_id': session_id,
            'context': context
        }
        
        if include_history:
            # Get recent conversation history
            history = self.get_history(session_id, limit=self.context_window_size)
            
            # Format history for generation
            formatted_history = []
            for msg in history:
                formatted_msg = {
                    'role': msg.get('role', 'user'),
                    'content': msg.get('content', msg.get('message', ''))
                }
                formatted_history.append(formatted_msg)
            
            result['history'] = formatted_history
            
            # Add conversation summary if history is long
            if len(history) > 5:
                result['summary'] = self.get_conversation_summary(session_id)
        
        return result
    
    def merge_contexts(self, session_id: str, external_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge external context with session context
        
        Args:
            session_id: Session identifier
            external_context: External context to merge
            
        Returns:
            Merged context dictionary
        """
        session_context = self.get_context(session_id)
        
        # Merge contexts with session context taking priority
        merged = external_context.copy()
        merged.update(session_context)
        
        return merged
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """
        Clean up old inactive sessions
        
        Args:
            max_age_hours: Maximum age in hours for inactive sessions
        """
        try:
            current_time = datetime.now()
            sessions_to_clear = []
            
            for session_id in self.store.get_all_sessions():
                session = self.store.get_session(session_id)
                last_activity = session.get('last_activity')
                
                if last_activity:
                    try:
                        last_time = datetime.fromisoformat(last_activity)
                        age_hours = (current_time - last_time).total_seconds() / 3600
                        
                        if age_hours > max_age_hours:
                            sessions_to_clear.append(session_id)
                    except:
                        pass
            
            # Clear old sessions
            for session_id in sessions_to_clear:
                self.clear_context(session_id)
            
            if sessions_to_clear:
                logger.info(f"Cleaned up {len(sessions_to_clear)} old sessions")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get context manager statistics
        
        Returns:
            Statistics dictionary
        """
        try:
            all_sessions = self.store.get_all_sessions()
            total_messages = 0
            
            for session_id in all_sessions:
                history = self.get_history(session_id, limit=0)
                total_messages += len(history)
            
            return {
                'active_sessions': len(all_sessions),
                'total_messages': total_messages,
                'storage_type': type(self.store).__name__,
                'max_history_entries': self.max_history_entries,
                'context_window_size': self.context_window_size
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {'error': str(e)}