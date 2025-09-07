"""
Hybrid Context Manager with Multi-Tier Storage
Combines memory caching with database persistence for optimal performance
Implements entity extraction and medical compliance features
"""

import re
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
from collections import deque
import hashlib

from .base import MemoryContextStore, ContextManager
from .database_store import DatabaseContextStore

logger = logging.getLogger(__name__)


class EntityExtractor:
    """
    Extracts entities from conversations
    Single Responsibility: Entity extraction and classification
    """
    
    # Important fields to preserve during compression
    IMPORTANT_FIELDS = {
        'product_name', 'price', 'strain_type', 'category', 
        'user_preference', 'quantity', 'order_id'
    }
    
    # Regular expressions for entity extraction
    PATTERNS = {
        'thc_percentage': r'\b(\d+(?:\.\d+)?)\s*(?:%|percent|pct)?\s*THC\b',
        'cbd_percentage': r'\b(\d+(?:\.\d+)?)\s*(?:%|percent|pct)?\s*CBD\b',
        'price': r'\$(\d+(?:\.\d{2})?)|(\d+(?:\.\d{2})?)\s*(?:dollar|bucks?)',
        'product_name': r'(?:looking for|want|need|interested in)\s+([A-Za-z0-9\s\-]+?)(?:\.|,|\?|$)',
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
        'strain_type': r'\b(indica|sativa|hybrid)\b',
        'category': r'\b(flower|edible|vape|tincture|topical|accessory)\b'
    }
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract entities from text
        
        Args:
            text: Input text to process
            
        Returns:
            Dictionary of extracted entities
        """
        entities = {}
        text_lower = text.lower()
        
        # Extract using patterns
        for entity_type, pattern in self.PATTERNS.items():
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                # Clean up matches
                if isinstance(matches[0], tuple):
                    matches = [m for group in matches for m in group if m]
                entities[entity_type] = matches[0] if len(matches) == 1 else matches
        
        # Extract product preferences
        if 'prefer' in text_lower or 'like' in text_lower or 'favorite' in text_lower:
            entities['preference_mentioned'] = True
        
        return entities
    
    def classify_intent(self, text: str, entities: Dict) -> str:
        """
        Classify the intent based on text and entities
        
        Args:
            text: Input text
            entities: Extracted entities
            
        Returns:
            Intent classification
        """
        text_lower = text.lower()
        
        # Intent patterns
        if any(word in text_lower for word in ['recommend', 'suggest', 'what should']):
            return 'recommendation'
        elif any(word in text_lower for word in ['how much', 'price', 'cost']):
            return 'pricing'
        elif any(word in text_lower for word in ['order', 'buy', 'purchase']):
            return 'purchase_intent'
        elif any(word in text_lower for word in ['hello', 'hi', 'hey']):
            return 'greeting'
        elif any(word in text_lower for word in ['search', 'find', 'looking for']):
            return 'product_search'
        else:
            return 'general_inquiry'


class ContextCompressor:
    """
    Compresses and summarizes conversation context
    Single Responsibility: Context compression while preserving critical information
    """
    
    def __init__(self, max_summary_length: int = 500):
        """
        Initialize context compressor
        
        Args:
            max_summary_length: Maximum length for summaries
        """
        self.max_summary_length = max_summary_length
        self.extractor = EntityExtractor()
    
    def compress_messages(self, messages: List[Dict], keep_last: int = 5) -> Tuple[str, Dict]:
        """
        Compress messages into a summary while preserving important information
        
        Args:
            messages: List of message dictionaries
            keep_last: Number of recent messages to keep uncompressed
            
        Returns:
            Tuple of (summary, important_data)
        """
        if len(messages) <= keep_last:
            return "", {}
        
        # Separate messages to compress and keep
        to_compress = messages[:-keep_last]
        important_data = {}
        
        # Extract all important information first
        for msg in to_compress:
            content = msg.get('content', '')
            entities = self.extractor.extract_entities(content)
            
            # Preserve important entities
            for field in EntityExtractor.IMPORTANT_FIELDS:
                if field in entities:
                    if field not in important_data:
                        important_data[field] = []
                    important_data[field].append({
                        'value': entities[field],
                        'timestamp': msg.get('timestamp'),
                        'role': msg.get('role')
                    })
        
        # Create summary
        summary_parts = []
        
        # Group messages by intent/topic
        for msg in to_compress:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            # Truncate long messages
            if len(content) > 100:
                content = content[:97] + "..."
            
            # Only include key messages
            if role == 'user' or 'recommend' in content.lower():
                summary_parts.append(f"{role}: {content}")
        
        summary = " | ".join(summary_parts[-10:])  # Keep last 10 key exchanges
        
        if len(summary) > self.max_summary_length:
            summary = "..." + summary[-self.max_summary_length:]
        
        return summary, critical_data
    
    def merge_critical_data(self, *data_dicts: Dict) -> Dict:
        """
        Merge multiple critical data dictionaries
        
        Args:
            *data_dicts: Variable number of dictionaries to merge
            
        Returns:
            Merged dictionary with de-duplicated values
        """
        merged = {}
        
        for data in data_dicts:
            for key, values in data.items():
                if key not in merged:
                    merged[key] = []
                
                # Add new values, avoiding duplicates
                for value in values if isinstance(values, list) else [values]:
                    # Create a hash for de-duplication
                    value_hash = hashlib.md5(
                        json.dumps(value, sort_keys=True).encode()
                    ).hexdigest()
                    
                    # Check if this value already exists
                    existing_hashes = [
                        hashlib.md5(json.dumps(v, sort_keys=True).encode()).hexdigest()
                        for v in merged[key]
                    ]
                    
                    if value_hash not in existing_hashes:
                        merged[key].append(value)
        
        return merged


class HybridContextManager:
    """
    Hybrid context manager with multi-tier storage
    Combines memory, database, and compression for optimal performance
    """
    
    def __init__(self, 
                 db_config: Optional[Dict] = None,
                 memory_ttl: int = 3600,
                 max_memory_sessions: int = 100,
                 enable_compression: bool = True):
        """
        Initialize hybrid context manager
        
        Args:
            db_config: Database configuration
            memory_ttl: TTL for memory cache in seconds
            max_memory_sessions: Maximum sessions to keep in memory
            enable_compression: Whether to enable context compression
        """
        # Initialize storage layers
        self.memory_store = MemoryContextStore(max_history_per_session=50)
        self.db_store = DatabaseContextStore(**(db_config or {}))
        
        # Initialize helpers
        self.extractor = EntityExtractor()
        self.compressor = ContextCompressor() if enable_compression else None
        
        # Configuration
        self.memory_ttl = memory_ttl
        self.max_memory_sessions = max_memory_sessions
        self.enable_compression = enable_compression
        
        # Cache management
        self._session_cache = {}
        self._cache_timestamps = {}
        self._lock = asyncio.Lock()
        
        logger.info("HybridContextManager initialized with memory and database storage")
    
    async def initialize(self):
        """Initialize database connections"""
        await self.db_store.initialize()
        logger.info("HybridContextManager fully initialized")
    
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
            Context dictionary
        """
        async with self._lock:
            # L1: Check memory cache
            if session_id in self._session_cache:
                cache_age = (datetime.now() - self._cache_timestamps[session_id]).seconds
                if cache_age < self.memory_ttl:
                    logger.debug(f"Context cache hit for session {session_id}")
                    return self._session_cache[session_id]
            
            # L2: Check memory store
            memory_context = self.memory_store.get_session(session_id)
            if memory_context.get('context'):
                logger.debug(f"Memory store hit for session {session_id}")
                self._update_cache(session_id, memory_context['context'])
                return memory_context['context']
            
            # L3: Load from database
            db_conversation = await self.db_store.get_conversation(session_id)
            if db_conversation:
                logger.debug(f"Database hit for session {session_id}")
                
                # Restore to memory store
                self.memory_store.sessions[session_id] = {
                    'context': db_conversation['context'],
                    'history': deque(db_conversation['messages'], maxlen=50),
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
                'entities': {},
                'preferences': {},
                'critical_data': {}
            }
            
            # Initialize in all layers
            self.memory_store.sessions[session_id] = {
                'context': new_context,
                'history': deque(maxlen=50),
                'created_at': new_context['created_at'],
                'last_activity': datetime.now().isoformat()
            }
            
            self._update_cache(session_id, new_context)
            
            # Save to database
            await self.db_store.save_conversation(
                session_id, [], new_context, customer_id
            )
            
            return new_context
    
    async def add_interaction(self, 
                            session_id: str,
                            user_message: str,
                            ai_response: str,
                            customer_id: Optional[str] = None) -> None:
        """
        Add an interaction and update context
        
        Args:
            session_id: Session identifier
            user_message: User's message
            ai_response: AI's response
            customer_id: Optional customer identifier
        """
        timestamp = datetime.now().isoformat()
        
        # Extract entities from user message
        user_entities = self.extractor.extract_entities(user_message)
        intent = self.extractor.classify_intent(user_message, user_entities)
        
        # Extract entities from AI response
        ai_entities = self.extractor.extract_entities(ai_response)
        
        # Create message objects
        user_msg = {
            'role': 'user',
            'content': user_message,
            'timestamp': timestamp,
            'entities': user_entities,
            'intent': intent
        }
        
        ai_msg = {
            'role': 'assistant',
            'content': ai_response,
            'timestamp': timestamp,
            'entities': ai_entities
        }
        
        # Update memory store
        session = self.memory_store.get_session(session_id)
        session['history'].append(user_msg)
        session['history'].append(ai_msg)
        
        # Update context with entities
        context = await self.get_context(session_id, customer_id)
        
        # Merge entities into context
        if 'entities' not in context:
            context['entities'] = {}
        
        for entity_dict in [user_entities, ai_entities]:
            for key, value in entity_dict.items():
                if key in EntityExtractor.CRITICAL_FIELDS:
                    # Store critical fields separately
                    if 'critical_data' not in context:
                        context['critical_data'] = {}
                    context['critical_data'][key] = value
                else:
                    context['entities'][key] = value
        
        # Update intent history
        if 'intent_history' not in context:
            context['intent_history'] = []
        context['intent_history'].append(intent)
        
        # Apply compression if needed
        history = list(session['history'])
        if self.enable_compression and len(history) > 20:
            summary, critical = self.compressor.compress_messages(history, keep_last=10)
            if summary:
                context['conversation_summary'] = summary
                context['critical_data'] = self.compressor.merge_critical_data(
                    context.get('critical_data', {}), critical
                )
        
        # Update all storage layers
        self._update_cache(session_id, context)
        self.memory_store.sessions[session_id]['context'] = context
        
        # Save to database asynchronously
        asyncio.create_task(self._persist_to_database(
            session_id, history, context, customer_id, 
            user_message, ai_response, intent
        ))
    
    async def _persist_to_database(self,
                                  session_id: str,
                                  history: List[Dict],
                                  context: Dict,
                                  customer_id: Optional[str],
                                  user_message: str,
                                  ai_response: str,
                                  intent: str):
        """
        Persist data to database (runs asynchronously)
        """
        try:
            # Save conversation
            await self.db_store.save_conversation(
                session_id, history, context, customer_id
            )
            
            # Save interaction
            await self.db_store.add_interaction(
                session_id, user_message, ai_response,
                intent=intent, customer_id=customer_id
            )
            
            # Update customer profile if customer_id provided
            if customer_id:
                await self.db_store.update_customer_profile(
                    customer_id,
                    preferences=context.get('entities', {}),
                    increment_interaction=True
                )
            
            logger.debug(f"Persisted session {session_id} to database")
            
        except Exception as e:
            logger.error(f"Failed to persist to database: {e}")
    
    def _update_cache(self, session_id: str, context: Dict):
        """Update memory cache"""
        self._session_cache[session_id] = context
        self._cache_timestamps[session_id] = datetime.now()
        
        # Evict old sessions if cache is full
        if len(self._session_cache) > self.max_memory_sessions:
            # Find oldest session
            oldest_session = min(
                self._cache_timestamps.items(),
                key=lambda x: x[1]
            )[0]
            
            del self._session_cache[oldest_session]
            del self._cache_timestamps[oldest_session]
            logger.debug(f"Evicted session {oldest_session} from cache")
    
    async def get_customer_context(self, customer_id: str) -> Dict:
        """
        Get aggregated context for a customer across all sessions
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            Aggregated customer context
        """
        # Get customer profile
        profile = await self.db_store.get_customer_profile(customer_id)
        
        # Get recent interactions
        interactions = await self.db_store.get_recent_interactions(
            customer_id=customer_id, limit=50
        )
        
        # Aggregate context
        aggregated = {
            'customer_id': customer_id,
            'profile': profile or {},
            'total_interactions': len(interactions),
            'recent_intents': [],
            'mentioned_products': set(),
            'medical_info': {}
        }
        
        # Process interactions
        for interaction in interactions:
            # Extract entities from messages
            user_entities = self.extractor.extract_entities(
                interaction.get('user_message', '')
            )
            
            # Collect intents
            if interaction.get('intent'):
                aggregated['recent_intents'].append(interaction['intent'])
            
            # Collect product mentions
            if 'product_name' in user_entities:
                aggregated['mentioned_products'].add(user_entities['product_name'])
            
            # Collect medical information
            for field in EntityExtractor.CRITICAL_FIELDS:
                if field in user_entities:
                    aggregated['medical_info'][field] = user_entities[field]
        
        # Convert set to list for JSON serialization
        aggregated['mentioned_products'] = list(aggregated['mentioned_products'])
        
        return aggregated
    
    async def create_audit_trail(self, 
                                session_id: str,
                                action: str,
                                details: Dict) -> None:
        """
        Create audit trail for compliance
        
        Args:
            session_id: Session identifier
            action: Action performed
            details: Action details
        """
        audit_entry = {
            'session_id': session_id,
            'action': action,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in context
        context = await self.get_context(session_id)
        if 'audit_trail' not in context:
            context['audit_trail'] = []
        context['audit_trail'].append(audit_entry)
        
        # Log for compliance
        logger.info(f"AUDIT: {action} for session {session_id}: {details}")
    
    async def get_stats(self) -> Dict:
        """
        Get comprehensive statistics
        
        Returns:
            Statistics dictionary
        """
        db_stats = await self.db_store.get_session_stats()
        
        return {
            'memory_sessions': len(self.memory_store.sessions),
            'cached_sessions': len(self._session_cache),
            'database_stats': db_stats,
            'compression_enabled': self.enable_compression,
            'memory_ttl_seconds': self.memory_ttl
        }