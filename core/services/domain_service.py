"""
Domain Service Layer
Following SOLID principles - handles business logic
Open/Closed Principle - can be extended without modification
"""
import logging
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

from core.interfaces.domain_plugin import DomainContext, TaskType
from core.interfaces.product_repository import (
    IProductRepository, IConversationRepository, IKnowledgeRepository
)

logger = logging.getLogger(__name__)

class IDomainService(ABC):
    """Abstract base for domain services - Liskov Substitution Principle"""
    
    @abstractmethod
    async def process_query(
        self,
        message: str,
        context: DomainContext,
        task_type: TaskType
    ) -> Dict[str, Any]:
        """Process a domain-specific query"""
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get domain capabilities"""
        pass


class BudtenderService(IDomainService):
    """
    Budtender domain service
    Single Responsibility: Handle budtender business logic
    Dependency Inversion: Depends on abstractions (interfaces)
    """
    
    def __init__(
        self,
        product_repo: IProductRepository,
        conversation_repo: IConversationRepository,
        knowledge_repo: IKnowledgeRepository,
        ai_processor=None
    ):
        """Initialize with injected dependencies"""
        self.product_repo = product_repo
        self.conversation_repo = conversation_repo
        self.knowledge_repo = knowledge_repo
        self.ai_processor = ai_processor  # The AI model processor
        
    async def process_query(
        self,
        message: str,
        context: DomainContext,
        task_type: TaskType
    ) -> Dict[str, Any]:
        """Process budtender query with all existing functionality preserved"""
        
        try:
            # Based on task type, use appropriate repository
            if task_type == TaskType.SEARCH:
                return await self._handle_product_search(message, context)
            elif task_type == TaskType.RECOMMENDATION:
                return await self._handle_recommendation(message, context)
            elif task_type == TaskType.INFORMATION:
                return await self._handle_information_query(message, context)
            elif task_type == TaskType.CONSULTATION:
                return await self._handle_consultation(message, context)
            else:
                return await self._handle_general_query(message, context, task_type)
                
        except Exception as e:
            logger.error(f"Error processing budtender query: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "I apologize, but I encountered an error. Please try again."
            }
    
    async def _handle_product_search(self, message: str, context: DomainContext) -> Dict:
        """Handle product search requests"""
        # Extract search parameters from message
        params = await self._extract_search_params(message)
        
        # Search products
        products = await self.product_repo.search_products(params)
        
        # Log interaction
        response = self._format_product_results(products)
        await self.conversation_repo.log_interaction(
            context.session_id,
            message,
            response,
            'budtender'
        )
        
        return {
            "success": True,
            "products": products,
            "message": response,
            "task": "search"
        }
    
    async def _handle_recommendation(self, message: str, context: DomainContext) -> Dict:
        """Handle recommendation requests"""
        # Extract preferences from message and context
        preferences = await self._extract_preferences(message, context)
        
        # Get recommendations
        recommendations = await self.product_repo.get_recommendations(preferences)
        
        # Log interaction
        response = self._format_recommendations(recommendations)
        await self.conversation_repo.log_interaction(
            context.session_id,
            message,
            response,
            'budtender'
        )
        
        return {
            "success": True,
            "recommendations": recommendations,
            "message": response,
            "task": "recommendation"
        }
    
    async def _handle_information_query(self, message: str, context: DomainContext) -> Dict:
        """Handle information requests"""
        # Search knowledge base
        knowledge = await self.knowledge_repo.search_knowledge(message, 'budtender')
        
        # Use AI to generate response
        if self.ai_processor:
            response = await self.ai_processor.generate_response(
                message,
                knowledge,
                context
            )
        else:
            response = self._format_knowledge_results(knowledge)
        
        # Log interaction
        await self.conversation_repo.log_interaction(
            context.session_id,
            message,
            response,
            'budtender'
        )
        
        return {
            "success": True,
            "knowledge": knowledge,
            "message": response,
            "task": "information"
        }
    
    async def _handle_consultation(self, message: str, context: DomainContext) -> Dict:
        """Handle consultation requests"""
        # Get conversation history for context
        history = await self.conversation_repo.get_conversation_history(
            context.session_id
        )
        
        # Search relevant knowledge
        knowledge = await self.knowledge_repo.search_knowledge(message, 'budtender')
        
        # Use AI for consultation response
        if self.ai_processor:
            response = await self.ai_processor.generate_consultation(
                message,
                history,
                knowledge,
                context
            )
        else:
            response = "I'd be happy to help with your consultation. " + \
                      "Based on your needs, " + self._format_knowledge_results(knowledge)
        
        # Log interaction
        await self.conversation_repo.log_interaction(
            context.session_id,
            message,
            response,
            'budtender'
        )
        
        return {
            "success": True,
            "message": response,
            "task": "consultation",
            "context_used": len(history) > 0
        }
    
    async def _handle_general_query(
        self,
        message: str,
        context: DomainContext,
        task_type: TaskType
    ) -> Dict:
        """Handle general queries"""
        # Use AI for general response
        if self.ai_processor:
            response = await self.ai_processor.generate_response(
                message,
                [],
                context
            )
        else:
            response = f"I understand you're asking about {task_type.value}. How can I help?"
        
        # Log interaction
        await self.conversation_repo.log_interaction(
            context.session_id,
            message,
            response,
            'budtender'
        )
        
        return {
            "success": True,
            "message": response,
            "task": task_type.value
        }
    
    async def _extract_search_params(self, message: str) -> Dict:
        """Extract search parameters from message"""
        # This would use AI to extract parameters
        # For now, basic implementation
        params = {}
        
        message_lower = message.lower()
        
        # Extract product type
        if 'flower' in message_lower:
            params['product_type'] = 'flower'
        elif 'edible' in message_lower:
            params['product_type'] = 'edible'
        elif 'concentrate' in message_lower:
            params['product_type'] = 'concentrate'
        
        # Extract effects
        effects = []
        if 'relax' in message_lower or 'sleep' in message_lower:
            effects.append('relaxed')
        if 'energy' in message_lower or 'focus' in message_lower:
            effects.append('energetic')
        if 'pain' in message_lower:
            effects.append('pain relief')
        
        if effects:
            params['effects'] = effects
        
        return params
    
    async def _extract_preferences(self, message: str, context: DomainContext) -> Dict:
        """Extract user preferences from message and context"""
        preferences = context.preferences.copy() if context and context.preferences else {}
        
        # Update with message-specific preferences
        message_params = await self._extract_search_params(message)
        preferences.update(message_params)
        
        return preferences
    
    def _format_product_results(self, products: List[Dict]) -> str:
        """Format product results for display"""
        if not products:
            return "I couldn't find any products matching your criteria."
        
        response = f"I found {len(products)} products for you:\n"
        for p in products[:3]:  # Show top 3
            response += f"- {p.get('name', 'Unknown')}: {p.get('description', '')}\n"
        
        return response
    
    def _format_recommendations(self, recommendations: List[Dict]) -> str:
        """Format recommendations for display"""
        if not recommendations:
            return "I don't have specific recommendations based on your criteria."
        
        response = "Based on your preferences, I recommend:\n"
        for r in recommendations[:3]:
            response += f"- {r.get('name', 'Unknown')}: {r.get('description', '')}\n"
        
        return response
    
    def _format_knowledge_results(self, knowledge: List[Dict]) -> str:
        """Format knowledge results for display"""
        if not knowledge:
            return "I don't have specific information about that."
        
        response = "Here's what I know:\n"
        for k in knowledge[:2]:
            response += f"- {k.get('data', {}).get('description', '')}\n"
        
        return response
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get budtender service capabilities"""
        return {
            "domain": "budtender",
            "features": [
                "product_search",
                "personalized_recommendations",
                "strain_information",
                "dosage_guidance",
                "effect_consultation",
                "medical_use_advice",
                "context_awareness",
                "multi_language_support"
            ],
            "data_sources": [
                "product_database",
                "strain_knowledge",
                "effects_database",
                "user_history"
            ]
        }


class HealthcareService(IDomainService):
    """Healthcare domain service - can be implemented similarly"""
    
    def __init__(self, knowledge_repo: IKnowledgeRepository, ai_processor=None):
        self.knowledge_repo = knowledge_repo
        self.ai_processor = ai_processor
    
    async def process_query(
        self,
        message: str,
        context: DomainContext,
        task_type: TaskType
    ) -> Dict[str, Any]:
        """Process healthcare query"""
        # Healthcare-specific implementation
        return {
            "success": True,
            "message": "Healthcare service processing",
            "task": task_type.value
        }
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get healthcare service capabilities"""
        return {
            "domain": "healthcare",
            "features": [
                "symptom_analysis",
                "medical_information",
                "treatment_guidance"
            ]
        }