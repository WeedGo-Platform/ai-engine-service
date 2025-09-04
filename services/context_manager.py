"""
Conversation Context and Memory Management Service
Handles multi-turn conversations, context windows, and conversation summarization
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import hashlib

from langchain.memory import (
    ConversationBufferMemory,
    ConversationSummaryMemory,
    ConversationBufferWindowMemory,
    ConversationSummaryBufferMemory,
    ConversationKGMemory,
    VectorStoreRetrieverMemory
)
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.memory.chat_memory import BaseChatMemory

from repositories.chat_repository import ChatRepository
from services.llm_service import get_llm_service
from utils.cache import CacheManager
from config import settings

logger = logging.getLogger(__name__)

class MemoryStrategy(Enum):
    """Memory management strategies"""
    BUFFER = "buffer"  # Keep all messages
    WINDOW = "window"  # Keep last N messages
    SUMMARY = "summary"  # Summarize older messages
    SUMMARY_BUFFER = "summary_buffer"  # Hybrid approach
    KNOWLEDGE_GRAPH = "knowledge_graph"  # Extract entities and relationships
    VECTOR_STORE = "vector_store"  # Store in vector database

@dataclass
class ConversationContext:
    """Complete conversation context"""
    session_id: str
    customer_id: str
    messages: List[BaseMessage]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    summary: Optional[str] = None
    entities: Dict[str, List[str]] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "session_id": self.session_id,
            "customer_id": self.customer_id,
            "messages": [
                {
                    "type": msg.__class__.__name__,
                    "content": msg.content,
                    "additional_kwargs": msg.additional_kwargs
                }
                for msg in self.messages
            ],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "summary": self.summary,
            "entities": self.entities,
            "preferences": self.preferences
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationContext':
        """Create from dictionary"""
        messages = []
        for msg_data in data.get("messages", []):
            if msg_data["type"] == "HumanMessage":
                messages.append(HumanMessage(content=msg_data["content"]))
            elif msg_data["type"] == "AIMessage":
                messages.append(AIMessage(content=msg_data["content"]))
            elif msg_data["type"] == "SystemMessage":
                messages.append(SystemMessage(content=msg_data["content"]))
        
        return cls(
            session_id=data["session_id"],
            customer_id=data["customer_id"],
            messages=messages,
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            summary=data.get("summary"),
            entities=data.get("entities", {}),
            preferences=data.get("preferences", {})
        )

@dataclass
class ContextWindow:
    """Manages context window for LLM"""
    max_tokens: int = 4096
    max_messages: int = 20
    preserve_system: bool = True
    summarize_overflow: bool = True

class ConversationMemory:
    """Wrapper for different memory strategies"""
    
    def __init__(
        self,
        strategy: MemoryStrategy,
        llm_service=None,
        **kwargs
    ):
        self.strategy = strategy
        self.llm_service = llm_service or get_llm_service()
        self.memory = self._create_memory(kwargs)
        
    def _create_memory(self, kwargs) -> BaseChatMemory:
        """Create appropriate memory implementation"""
        
        if self.strategy == MemoryStrategy.BUFFER:
            return ConversationBufferMemory(
                return_messages=True,
                **kwargs
            )
        
        elif self.strategy == MemoryStrategy.WINDOW:
            return ConversationBufferWindowMemory(
                k=kwargs.get('window_size', 10),
                return_messages=True,
                **kwargs
            )
        
        elif self.strategy == MemoryStrategy.SUMMARY:
            # Need LangChain LLM wrapper
            if hasattr(self.llm_service, 'langchain_llm'):
                return ConversationSummaryMemory(
                    llm=self.llm_service.langchain_llm,
                    return_messages=True,
                    **kwargs
                )
            else:
                # Fallback to buffer if no LLM available
                return ConversationBufferMemory(
                    return_messages=True,
                    **kwargs
                )
        
        elif self.strategy == MemoryStrategy.SUMMARY_BUFFER:
            if hasattr(self.llm_service, 'langchain_llm'):
                return ConversationSummaryBufferMemory(
                    llm=self.llm_service.langchain_llm,
                    max_token_limit=kwargs.get('max_tokens', 2000),
                    return_messages=True,
                    **kwargs
                )
            else:
                return ConversationBufferWindowMemory(
                    k=10,
                    return_messages=True,
                    **kwargs
                )
        
        else:
            # Default to buffer
            return ConversationBufferMemory(
                return_messages=True,
                **kwargs
            )
    
    async def add_message(self, message: BaseMessage):
        """Add a message to memory"""
        if isinstance(message, HumanMessage):
            self.memory.chat_memory.add_user_message(message.content)
        elif isinstance(message, AIMessage):
            self.memory.chat_memory.add_ai_message(message.content)
        elif isinstance(message, SystemMessage):
            # System messages might not be directly supported by all memory types
            self.memory.chat_memory.messages.append(message)
    
    async def get_messages(self) -> List[BaseMessage]:
        """Get all messages from memory"""
        return self.memory.chat_memory.messages
    
    async def get_context(self) -> str:
        """Get formatted context string"""
        if hasattr(self.memory, 'buffer'):
            return self.memory.buffer
        else:
            messages = await self.get_messages()
            return "\n".join([f"{msg.__class__.__name__}: {msg.content}" for msg in messages])
    
    async def clear(self):
        """Clear memory"""
        self.memory.clear()

class ContextManager:
    """
    Manages conversation context and memory across sessions
    """
    
    def __init__(
        self,
        default_strategy: MemoryStrategy = MemoryStrategy.SUMMARY_BUFFER,
        chat_repo: Optional[ChatRepository] = None,
        cache: Optional[CacheManager] = None
    ):
        self.default_strategy = default_strategy
        self.chat_repo = chat_repo or ChatRepository()
        self.cache = cache or CacheManager()
        self.active_contexts: Dict[str, ConversationContext] = {}
        self.memories: Dict[str, ConversationMemory] = {}
        self.context_window = ContextWindow()
        
    async def get_or_create_context(
        self,
        session_id: str,
        customer_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationContext:
        """
        Get existing context or create new one
        
        Args:
            session_id: Unique session identifier
            customer_id: Customer identifier
            metadata: Optional metadata for context
        
        Returns:
            ConversationContext instance
        """
        
        # Check active contexts
        if session_id in self.active_contexts:
            context = self.active_contexts[session_id]
            context.updated_at = datetime.utcnow()
            return context
        
        # Check cache
        cache_key = f"context:{session_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            context = ConversationContext.from_dict(cached)
            self.active_contexts[session_id] = context
            return context
        
        # Load from database
        history = await self.chat_repo.get_session_history(session_id)
        
        if history:
            # Reconstruct context from history
            messages = []
            for entry in history:
                if entry['role'] == 'user':
                    messages.append(HumanMessage(content=entry['message']))
                elif entry['role'] == 'assistant':
                    messages.append(AIMessage(content=entry['response']))
            
            context = ConversationContext(
                session_id=session_id,
                customer_id=customer_id,
                messages=messages,
                metadata=metadata or {},
                created_at=history[0]['created_at'] if history else datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        else:
            # Create new context
            context = ConversationContext(
                session_id=session_id,
                customer_id=customer_id,
                messages=[],
                metadata=metadata or {},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        
        self.active_contexts[session_id] = context
        
        # Initialize memory for this session
        if session_id not in self.memories:
            self.memories[session_id] = ConversationMemory(self.default_strategy)
            # Add existing messages to memory
            for msg in context.messages:
                await self.memories[session_id].add_message(msg)
        
        return context
    
    async def add_interaction(
        self,
        session_id: str,
        user_message: str,
        ai_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add a new interaction to the context
        
        Args:
            session_id: Session identifier
            user_message: User's message
            ai_response: AI's response
            metadata: Optional metadata for this interaction
        """
        
        if session_id not in self.active_contexts:
            logger.warning(f"Session {session_id} not found in active contexts")
            return
        
        context = self.active_contexts[session_id]
        
        # Create message objects
        human_msg = HumanMessage(content=user_message)
        ai_msg = AIMessage(content=ai_response)
        
        # Add to context
        context.messages.extend([human_msg, ai_msg])
        context.updated_at = datetime.utcnow()
        
        # Update metadata if provided
        if metadata:
            context.metadata.update(metadata)
        
        # Add to memory
        if session_id in self.memories:
            await self.memories[session_id].add_message(human_msg)
            await self.memories[session_id].add_message(ai_msg)
        
        # Extract entities and preferences
        await self._extract_entities(session_id, user_message, ai_response)
        await self._extract_preferences(session_id, user_message)
        
        # Save to cache
        await self.cache.set(
            f"context:{session_id}",
            context.to_dict(),
            ttl=3600
        )
        
        # Save to database
        await self.chat_repo.save_interaction(
            customer_id=context.customer_id,
            message=user_message,
            response=ai_response,
            language=context.metadata.get('language', 'en'),
            model_used=context.metadata.get('model', 'unknown'),
            session_id=session_id
        )
    
    async def get_context_for_prompt(
        self,
        session_id: str,
        include_summary: bool = True,
        max_messages: Optional[int] = None
    ) -> str:
        """
        Get formatted context for LLM prompt
        
        Args:
            session_id: Session identifier
            include_summary: Whether to include conversation summary
            max_messages: Maximum number of recent messages to include
        
        Returns:
            Formatted context string
        """
        
        if session_id not in self.active_contexts:
            return ""
        
        context = self.active_contexts[session_id]
        max_messages = max_messages or self.context_window.max_messages
        
        # Build context string
        context_parts = []
        
        # Add summary if available and requested
        if include_summary and context.summary:
            context_parts.append(f"Conversation Summary:\n{context.summary}\n")
        
        # Add customer preferences
        if context.preferences:
            pref_str = ", ".join([f"{k}: {v}" for k, v in context.preferences.items()])
            context_parts.append(f"Customer Preferences: {pref_str}\n")
        
        # Add extracted entities
        if context.entities:
            entities_str = ", ".join([
                f"{entity_type}: {', '.join(entities)}"
                for entity_type, entities in context.entities.items()
            ])
            context_parts.append(f"Mentioned: {entities_str}\n")
        
        # Add recent messages
        recent_messages = context.messages[-max_messages:] if max_messages else context.messages
        
        if recent_messages:
            context_parts.append("Recent Conversation:")
            for msg in recent_messages:
                if isinstance(msg, HumanMessage):
                    context_parts.append(f"Customer: {msg.content}")
                elif isinstance(msg, AIMessage):
                    context_parts.append(f"Assistant: {msg.content}")
        
        return "\n".join(context_parts)
    
    async def summarize_context(
        self,
        session_id: str,
        force: bool = False
    ) -> Optional[str]:
        """
        Generate summary of conversation context
        
        Args:
            session_id: Session identifier
            force: Force regeneration even if summary exists
        
        Returns:
            Summary string or None
        """
        
        if session_id not in self.active_contexts:
            return None
        
        context = self.active_contexts[session_id]
        
        # Check if summary needed
        if context.summary and not force:
            return context.summary
        
        # Need at least a few messages to summarize
        if len(context.messages) < 4:
            return None
        
        # Build conversation text
        conversation = "\n".join([
            f"{'Customer' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}"
            for msg in context.messages
        ])
        
        # Generate summary using LLM
        llm_service = get_llm_service()
        
        summary_prompt = f"""Summarize this cannabis consultation conversation, highlighting:
1. Customer's main needs and preferences
2. Products or strains discussed
3. Medical conditions or symptoms mentioned
4. Key recommendations made

Conversation:
{conversation}

Summary:"""
        
        try:
            result = await llm_service.generate(
                prompt=summary_prompt,
                max_tokens=200,
                temperature=0.3
            )
            
            context.summary = result.text
            context.updated_at = datetime.utcnow()
            
            # Update cache
            await self.cache.set(
                f"context:{session_id}",
                context.to_dict(),
                ttl=3600
            )
            
            return context.summary
            
        except Exception as e:
            logger.error(f"Failed to generate summary: {str(e)}")
            return None
    
    async def _extract_entities(
        self,
        session_id: str,
        user_message: str,
        ai_response: str
    ):
        """Extract entities from conversation"""
        
        if session_id not in self.active_contexts:
            return
        
        context = self.active_contexts[session_id]
        
        # Simple entity extraction (can be enhanced with NER)
        entities = {
            "strains": [],
            "symptoms": [],
            "products": [],
            "terpenes": [],
            "effects": []
        }
        
        # Cannabis strain patterns
        strain_keywords = [
            "Blue Dream", "OG Kush", "Sour Diesel", "Girl Scout Cookies",
            "Gorilla Glue", "White Widow", "Northern Lights", "Jack Herer"
        ]
        
        # Symptom patterns
        symptom_keywords = [
            "pain", "anxiety", "insomnia", "depression", "nausea",
            "inflammation", "stress", "appetite", "migraine", "arthritis"
        ]
        
        # Product type patterns
        product_keywords = [
            "flower", "edible", "tincture", "vape", "concentrate",
            "topical", "oil", "capsule", "pre-roll", "gummy"
        ]
        
        # Terpene patterns
        terpene_keywords = [
            "myrcene", "limonene", "pinene", "linalool", "caryophyllene",
            "humulene", "terpinolene", "ocimene"
        ]
        
        # Effect patterns
        effect_keywords = [
            "relaxing", "energizing", "euphoric", "creative", "focused",
            "uplifting", "calming", "sedating", "giggly", "hungry"
        ]
        
        combined_text = f"{user_message} {ai_response}".lower()
        
        # Extract entities
        for strain in strain_keywords:
            if strain.lower() in combined_text:
                entities["strains"].append(strain)
        
        for symptom in symptom_keywords:
            if symptom in combined_text:
                entities["symptoms"].append(symptom)
        
        for product in product_keywords:
            if product in combined_text:
                entities["products"].append(product)
        
        for terpene in terpene_keywords:
            if terpene in combined_text:
                entities["terpenes"].append(terpene)
        
        for effect in effect_keywords:
            if effect in combined_text:
                entities["effects"].append(effect)
        
        # Update context entities
        for entity_type, entity_list in entities.items():
            if entity_list:
                if entity_type not in context.entities:
                    context.entities[entity_type] = []
                context.entities[entity_type].extend(entity_list)
                # Remove duplicates
                context.entities[entity_type] = list(set(context.entities[entity_type]))
    
    async def _extract_preferences(
        self,
        session_id: str,
        user_message: str
    ):
        """Extract user preferences from message"""
        
        if session_id not in self.active_contexts:
            return
        
        context = self.active_contexts[session_id]
        message_lower = user_message.lower()
        
        # THC/CBD preference
        if "high thc" in message_lower:
            context.preferences["thc_preference"] = "high"
        elif "low thc" in message_lower or "no thc" in message_lower:
            context.preferences["thc_preference"] = "low"
        elif "high cbd" in message_lower:
            context.preferences["cbd_preference"] = "high"
        
        # Time of use preference
        if "daytime" in message_lower or "morning" in message_lower:
            context.preferences["time_of_use"] = "daytime"
        elif "nighttime" in message_lower or "evening" in message_lower or "sleep" in message_lower:
            context.preferences["time_of_use"] = "nighttime"
        
        # Experience level
        if "beginner" in message_lower or "first time" in message_lower or "new to" in message_lower:
            context.preferences["experience_level"] = "beginner"
        elif "experienced" in message_lower or "regular user" in message_lower:
            context.preferences["experience_level"] = "experienced"
        
        # Consumption method
        if "smoke" in message_lower or "flower" in message_lower:
            context.preferences["consumption_method"] = "smoking"
        elif "edible" in message_lower or "eat" in message_lower:
            context.preferences["consumption_method"] = "edibles"
        elif "vape" in message_lower or "vaping" in message_lower:
            context.preferences["consumption_method"] = "vaping"
        elif "tincture" in message_lower or "oil" in message_lower:
            context.preferences["consumption_method"] = "tinctures"
        
        # Effects preference
        if "relax" in message_lower or "calm" in message_lower:
            context.preferences["desired_effects"] = "relaxation"
        elif "energy" in message_lower or "focus" in message_lower or "creative" in message_lower:
            context.preferences["desired_effects"] = "energy/focus"
        elif "pain" in message_lower:
            context.preferences["desired_effects"] = "pain_relief"
    
    async def get_customer_insights(
        self,
        customer_id: str,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Get insights about a customer from their conversation history
        
        Args:
            customer_id: Customer identifier
            days_back: Number of days to look back
        
        Returns:
            Dictionary of customer insights
        """
        
        # Get historical data
        history = await self.chat_repo.get_customer_history(
            customer_id=customer_id,
            days_back=days_back
        )
        
        if not history:
            return {}
        
        insights = {
            "total_interactions": len(history),
            "first_interaction": history[0]['created_at'] if history else None,
            "last_interaction": history[-1]['created_at'] if history else None,
            "preferred_language": self._get_most_common([h.get('language', 'en') for h in history]),
            "common_topics": {},
            "product_interests": [],
            "session_count": len(set([h.get('session_id') for h in history if h.get('session_id')]))
        }
        
        # Analyze conversation content
        all_messages = " ".join([h['message'] for h in history])
        
        # Extract common themes
        theme_counts = {
            "medical": all_messages.lower().count("medical") + all_messages.lower().count("pain"),
            "recreational": all_messages.lower().count("recreational") + all_messages.lower().count("fun"),
            "sleep": all_messages.lower().count("sleep") + all_messages.lower().count("insomnia"),
            "anxiety": all_messages.lower().count("anxiety") + all_messages.lower().count("stress"),
            "focus": all_messages.lower().count("focus") + all_messages.lower().count("productivity")
        }
        
        insights["common_topics"] = {k: v for k, v in theme_counts.items() if v > 0}
        
        return insights
    
    def _get_most_common(self, items: List[str]) -> str:
        """Get most common item from list"""
        if not items:
            return ""
        return max(set(items), key=items.count)
    
    async def cleanup_old_contexts(self, hours: int = 24):
        """
        Clean up old inactive contexts
        
        Args:
            hours: Remove contexts older than this many hours
        """
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        sessions_to_remove = []
        
        for session_id, context in self.active_contexts.items():
            if context.updated_at < cutoff_time:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            # Save final state to cache before removing
            context = self.active_contexts[session_id]
            await self.cache.set(
                f"context:archive:{session_id}",
                context.to_dict(),
                ttl=86400 * 7  # Keep for a week
            )
            
            # Remove from active contexts
            del self.active_contexts[session_id]
            
            # Clean up memory
            if session_id in self.memories:
                await self.memories[session_id].clear()
                del self.memories[session_id]
        
        logger.info(f"Cleaned up {len(sessions_to_remove)} old contexts")
    
    async def export_context(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Export context for analysis or backup
        
        Args:
            session_id: Session identifier
        
        Returns:
            Exported context dictionary
        """
        
        if session_id not in self.active_contexts:
            # Try to load from cache
            cached = await self.cache.get(f"context:{session_id}")
            if cached:
                return cached
            
            archived = await self.cache.get(f"context:archive:{session_id}")
            if archived:
                return archived
            
            return None
        
        context = self.active_contexts[session_id]
        return context.to_dict()

# Singleton instance
_context_manager: Optional[ContextManager] = None

def get_context_manager() -> ContextManager:
    """Get singleton context manager instance"""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager