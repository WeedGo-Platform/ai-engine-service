"""
Domain Integration Bridge
Connects domain plugins with existing AI engine functionality
Preserves all existing budtender features while enabling domain switching
"""
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.smart_ai_engine_v3 import SmartAIEngineV3
from core.interfaces.domain_plugin import DomainContext, TaskType

logger = logging.getLogger(__name__)

class DomainIntegrationBridge:
    """
    Bridge between domain plugins and existing AI engine functionality
    Ensures backward compatibility with existing budtender features
    """
    
    def __init__(self):
        """Initialize the integration bridge"""
        self.smart_engine = None
        self.active_domain = None
        
    async def initialize(self, smart_engine: SmartAIEngineV3 = None):
        """Initialize with existing Smart AI Engine"""
        if smart_engine:
            self.smart_engine = smart_engine
        else:
            # Create new instance if not provided
            self.smart_engine = SmartAIEngineV3()
            await self.smart_engine.initialize()
        
        logger.info("Domain Integration Bridge initialized")
    
    async def process_budtender_query(
        self,
        message: str,
        context: DomainContext,
        task_type: TaskType
    ) -> Dict[str, Any]:
        """
        Process budtender queries using existing Smart AI Engine
        Preserves all existing functionality including:
        - Product search with database
        - Context memory
        - Personalized recommendations
        - Multi-language support
        """
        
        if not self.smart_engine:
            await self.initialize()
        
        # Map task type to existing Smart AI Engine query type
        query_type = self._map_task_to_query_type(task_type)
        
        # Call existing Smart AI Engine with all its features
        result = await self.smart_engine.process_query(
            query=message,
            query_type=query_type,
            language=context.language if context else 'en',
            user_id=context.session_id if context else None,
            context={
                'location': context.location if context else None,
                'preferences': context.preferences if context else {},
                'history': context.history if context else []
            }
        )
        
        return result
    
    async def search_products(
        self,
        search_params: Dict,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search products using existing database connection
        Uses the Smart AI Engine's _search_products method
        """
        
        if not self.smart_engine:
            await self.initialize()
        
        # Use existing product search functionality
        products = await self.smart_engine._search_products(search_params)
        
        return products[:limit] if products else []
    
    async def get_recommendations(
        self,
        user_preferences: Dict,
        medical_conditions: List[str] = None
    ) -> List[Dict]:
        """
        Get recommendations using existing recommendation engine
        """
        
        if not self.smart_engine:
            await self.initialize()
        
        # Build search parameters for recommendation
        params = {
            'effects': user_preferences.get('desired_effects', []),
            'medical_conditions': medical_conditions or [],
            'avoid_effects': user_preferences.get('avoid_effects', []),
            'product_type': user_preferences.get('product_type'),
            'price_range': user_preferences.get('price_range')
        }
        
        # Use existing search with recommendation logic
        recommendations = await self.search_products(params, limit=5)
        
        return recommendations
    
    def _map_task_to_query_type(self, task_type: TaskType) -> str:
        """Map domain task types to existing query types"""
        
        mapping = {
            TaskType.SEARCH: 'product_search',
            TaskType.RECOMMENDATION: 'recommendation',
            TaskType.INFORMATION: 'question',
            TaskType.CONSULTATION: 'consultation',
            TaskType.GREETING: 'greeting',
            TaskType.SUPPORT: 'support',
            TaskType.EDUCATION: 'education'
        }
        
        return mapping.get(task_type, 'general')
    
    async def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """Get product details using existing database"""
        
        if not self.smart_engine or not self.smart_engine.db_pool:
            return None
        
        try:
            async with self.smart_engine.db_pool.acquire() as conn:
                query = """
                    SELECT p.*, s.name as strain_name, s.type as strain_type
                    FROM products p
                    LEFT JOIN strains s ON p.strain_id = s.id
                    WHERE p.id = $1
                """
                row = await conn.fetchrow(query, product_id)
                
                if row:
                    return dict(row)
        except Exception as e:
            logger.error(f"Failed to get product: {e}")
        
        return None
    
    async def check_inventory(self, product_id: int) -> Dict:
        """Check product inventory using existing database"""
        
        if not self.smart_engine or not self.smart_engine.db_pool:
            return {'available': False, 'quantity': 0}
        
        try:
            async with self.smart_engine.db_pool.acquire() as conn:
                query = """
                    SELECT quantity, in_stock
                    FROM inventory
                    WHERE product_id = $1
                """
                row = await conn.fetchrow(query, product_id)
                
                if row:
                    return {
                        'available': row['in_stock'],
                        'quantity': row['quantity']
                    }
        except Exception as e:
            logger.error(f"Failed to check inventory: {e}")
        
        return {'available': False, 'quantity': 0}
    
    async def log_interaction(
        self,
        user_id: str,
        message: str,
        response: str,
        domain: str = 'budtender'
    ):
        """Log interaction to database for learning"""
        
        if not self.smart_engine or not self.smart_engine.db_pool:
            return
        
        try:
            async with self.smart_engine.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO conversation_history 
                    (user_id, user_message, ai_response, domain, created_at)
                    VALUES ($1, $2, $3, $4, NOW())
                """, user_id, message, response, domain)
        except Exception as e:
            logger.error(f"Failed to log interaction: {e}")
    
    async def get_conversation_history(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """Get conversation history for context"""
        
        if not self.smart_engine or not self.smart_engine.db_pool:
            return []
        
        try:
            async with self.smart_engine.db_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT user_message, ai_response, created_at
                    FROM conversation_history
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                """, user_id, limit)
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get history: {e}")
        
        return []

# Global instance for easy access
_integration_bridge = None

def get_integration_bridge():
    """Get or create integration bridge instance"""
    global _integration_bridge
    if _integration_bridge is None:
        _integration_bridge = DomainIntegrationBridge()
    return _integration_bridge