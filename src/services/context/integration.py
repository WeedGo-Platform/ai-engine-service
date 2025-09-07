"""
Integration module for connecting HybridContextManager with SmartAIEngineV5
Provides seamless context persistence and retrieval for the AI engine
"""

import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from .hybrid_manager import HybridContextManager

logger = logging.getLogger(__name__)


class SmartAIEngineV5ContextIntegration:
    """
    Integration layer between SmartAIEngineV5 and HybridContextManager
    Single Responsibility: Bridging AI engine with context persistence
    """
    
    def __init__(self, engine_instance=None):
        """
        Initialize integration
        
        Args:
            engine_instance: SmartAIEngineV5 instance to integrate with
        """
        self.engine = engine_instance
        
        # Database configuration from environment or defaults
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5434)),
            'database': os.getenv('DB_NAME', 'ai_engine'),
            'user': os.getenv('DB_USER', 'weedgo'),
            'password': os.getenv('DB_PASSWORD', 'your_password_here'),
            'min_connections': 2,
            'max_connections': 10
        }
        
        # Initialize hybrid context manager
        self.context_manager = HybridContextManager(
            db_config=db_config,
            memory_ttl=3600,
            max_memory_sessions=100,
            enable_compression=True
        )
        
        self._initialized = False
        logger.info("SmartAIEngineV5 context integration initialized")
    
    async def initialize(self):
        """Initialize async components"""
        if not self._initialized:
            await self.context_manager.initialize()
            self._initialized = True
            logger.info("Context integration fully initialized")
    
    async def close(self):
        """Clean up resources"""
        await self.context_manager.close()
        self._initialized = False
    
    def attach_to_engine(self, engine):
        """
        Attach context manager to SmartAIEngineV5 instance
        
        Args:
            engine: SmartAIEngineV5 instance
        """
        self.engine = engine
        
        # Monkey-patch the engine's generate method to include context
        original_generate = engine.generate
        
        async def generate_with_context(prompt: str, 
                                       session_id: Optional[str] = None,
                                       customer_id: Optional[str] = None,
                                       **kwargs) -> str:
            """Enhanced generate method with context persistence"""
            
            # Get context if session provided
            context = {}
            if session_id:
                context = await self.get_enhanced_context(session_id, customer_id)
                
                # Build enhanced prompt with context
                prompt = self.build_contextual_prompt(prompt, context)
            
            # Generate response
            response = original_generate(prompt, **kwargs)
            
            # Save interaction if session provided
            if session_id:
                await self.save_interaction(
                    session_id, prompt, response, customer_id
                )
            
            return response
        
        # Replace the method
        engine.generate_with_context = generate_with_context
        logger.info("Context manager attached to SmartAIEngineV5")
    
    async def get_enhanced_context(self, 
                                  session_id: str,
                                  customer_id: Optional[str] = None) -> Dict:
        """
        Get enhanced context for generation
        
        Args:
            session_id: Session identifier
            customer_id: Optional customer identifier
            
        Returns:
            Enhanced context dictionary
        """
        # Get base context
        context = await self.context_manager.get_context(session_id, customer_id)
        
        # Get customer context if available
        if customer_id:
            customer_context = await self.context_manager.get_customer_context(customer_id)
            context['customer'] = customer_context
        
        # Get conversation history
        session = self.context_manager.memory_store.get_session(session_id)
        history = list(session.get('history', []))[-10:]  # Last 10 messages
        
        # Format for generation
        context['formatted_history'] = self._format_history(history)
        context['has_medical_context'] = bool(context.get('critical_data'))
        
        return context
    
    def build_contextual_prompt(self, prompt: str, context: Dict) -> str:
        """
        Build prompt with context information
        
        Args:
            prompt: Original prompt
            context: Context dictionary
            
        Returns:
            Enhanced prompt with context
        """
        parts = []
        
        # Add conversation summary if available
        if context.get('conversation_summary'):
            parts.append(f"Previous conversation summary: {context['conversation_summary']}")
        
        # Add critical medical information
        if context.get('critical_data'):
            medical_info = []
            for field, value in context['critical_data'].items():
                if field in ['thc_percentage', 'cbd_percentage', 'dosage_amount']:
                    medical_info.append(f"{field}: {value}")
            
            if medical_info:
                parts.append(f"Important medical context: {', '.join(medical_info)}")
        
        # Add customer preferences if available
        if context.get('customer', {}).get('profile', {}).get('preferences'):
            prefs = context['customer']['profile']['preferences']
            if prefs:
                parts.append(f"Customer preferences: {prefs}")
        
        # Add recent conversation if available
        if context.get('formatted_history'):
            parts.append(f"Recent conversation:\n{context['formatted_history']}")
        
        # Add the current prompt
        parts.append(f"Current message: {prompt}")
        
        return "\n\n".join(parts)
    
    async def save_interaction(self,
                              session_id: str,
                              user_message: str,
                              ai_response: str,
                              customer_id: Optional[str] = None):
        """
        Save interaction to context
        
        Args:
            session_id: Session identifier
            user_message: User's message
            ai_response: AI's response
            customer_id: Optional customer identifier
        """
        await self.context_manager.add_interaction(
            session_id, user_message, ai_response, customer_id
        )
        
        # Check for medical compliance triggers
        if any(term in user_message.lower() for term in ['dosage', 'medical', 'prescription']):
            await self.context_manager.create_audit_trail(
                session_id,
                'medical_inquiry',
                {
                    'user_message': user_message[:200],  # Truncate for audit
                    'response_provided': True
                }
            )
    
    def _format_history(self, history: List[Dict]) -> str:
        """
        Format conversation history for prompt
        
        Args:
            history: List of message dictionaries
            
        Returns:
            Formatted history string
        """
        if not history:
            return ""
        
        formatted = []
        for msg in history:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            # Truncate long messages
            if len(content) > 200:
                content = content[:197] + "..."
            
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)
    
    async def get_session_recommendations(self, 
                                         session_id: str,
                                         limit: int = 5) -> List[Dict]:
        """
        Get product recommendations based on session context
        
        Args:
            session_id: Session identifier
            limit: Maximum recommendations
            
        Returns:
            List of product recommendations
        """
        context = await self.context_manager.get_context(session_id)
        
        recommendations = []
        
        # Extract preferences from entities
        entities = context.get('entities', {})
        
        # Build recommendation criteria
        criteria = {
            'strain_type': entities.get('strain_type'),
            'thc_range': entities.get('thc_percentage'),
            'cbd_range': entities.get('cbd_percentage'),
            'price_range': entities.get('price'),
            'consumption_method': entities.get('consumption_method')
        }
        
        # Filter out None values
        criteria = {k: v for k, v in criteria.items() if v is not None}
        
        # TODO: Query product database based on criteria
        # This would integrate with your product recommendation system
        
        return recommendations
    
    async def export_session_data(self, session_id: str) -> Dict:
        """
        Export complete session data for analysis or backup
        
        Args:
            session_id: Session identifier
            
        Returns:
            Complete session data
        """
        # Get all data
        context = await self.context_manager.get_context(session_id)
        session = self.context_manager.memory_store.get_session(session_id)
        
        # Get database records
        db_conversation = await self.context_manager.db_store.get_conversation(session_id)
        interactions = await self.context_manager.db_store.get_recent_interactions(
            session_id=session_id
        )
        
        return {
            'session_id': session_id,
            'context': context,
            'memory_state': {
                'history': list(session.get('history', [])),
                'created_at': session.get('created_at'),
                'last_activity': session.get('last_activity')
            },
            'database_state': {
                'conversation': db_conversation,
                'interactions': interactions
            },
            'export_timestamp': datetime.now().isoformat()
        }
    
    async def import_session_data(self, data: Dict) -> bool:
        """
        Import session data from export
        
        Args:
            data: Exported session data
            
        Returns:
            True if successful
        """
        try:
            session_id = data['session_id']
            
            # Restore to memory
            self.context_manager.memory_store.sessions[session_id] = {
                'context': data['context'],
                'history': deque(data['memory_state']['history'], maxlen=50),
                'created_at': data['memory_state']['created_at'],
                'last_activity': datetime.now().isoformat()
            }
            
            # Restore to database
            await self.context_manager.db_store.save_conversation(
                session_id,
                data['memory_state']['history'],
                data['context']
            )
            
            logger.info(f"Imported session data for {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import session data: {e}")
            return False
    
    async def get_analytics(self) -> Dict:
        """
        Get analytics data for monitoring
        
        Returns:
            Analytics dictionary
        """
        stats = await self.context_manager.get_stats()
        
        # Add engine-specific stats if available
        if self.engine:
            stats['engine'] = {
                'model_loaded': bool(self.engine.current_model),
                'current_agent': getattr(self.engine, 'current_agent', None),
                'current_personality': getattr(self.engine, 'current_personality_type', None)
            }
        
        return stats


# Convenience function for easy integration
async def create_context_enhanced_engine(engine_instance):
    """
    Create a context-enhanced SmartAIEngineV5 instance
    
    Args:
        engine_instance: SmartAIEngineV5 instance
        
    Returns:
        Integration instance with enhanced engine
    """
    integration = SmartAIEngineV5ContextIntegration(engine_instance)
    await integration.initialize()
    integration.attach_to_engine(engine_instance)
    
    return integration