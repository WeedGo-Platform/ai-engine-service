"""
Smart Engine Repository Implementation
Concrete implementation that delegates to existing Smart AI Engine
Following Single Responsibility Principle - only handles data access
"""
import logging
from typing import Dict, List, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.interfaces.product_repository import (
    IProductRepository, IConversationRepository, IKnowledgeRepository
)

logger = logging.getLogger(__name__)

class SmartEngineProductRepository(IProductRepository):
    """Product repository using Smart AI Engine's existing database"""
    
    def __init__(self, smart_engine=None):
        """Initialize with reference to Smart AI Engine"""
        self.smart_engine = smart_engine
    
    async def search_products(self, params: Dict, limit: int = 10) -> List[Dict]:
        """Search products using existing Smart AI Engine functionality"""
        if not self.smart_engine:
            logger.warning("Smart engine not initialized, returning empty results")
            return []
        
        try:
            # Delegate to existing Smart AI Engine method
            products = await self.smart_engine._search_products(params)
            return products[:limit] if products else []
        except Exception as e:
            logger.error(f"Product search failed: {e}")
            return []
    
    async def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """Get product by ID using existing database"""
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
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get product: {e}")
            return None
    
    async def check_inventory(self, product_id: int) -> Dict:
        """Check inventory using existing database"""
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
    
    async def get_recommendations(self, user_preferences: Dict, limit: int = 5) -> List[Dict]:
        """Get recommendations using existing search logic"""
        # Build search parameters from preferences
        params = {
            'effects': user_preferences.get('desired_effects', []),
            'medical_conditions': user_preferences.get('medical_conditions', []),
            'avoid_effects': user_preferences.get('avoid_effects', []),
            'product_type': user_preferences.get('product_type'),
            'price_range': user_preferences.get('price_range')
        }
        
        return await self.search_products(params, limit)


class SmartEngineConversationRepository(IConversationRepository):
    """Conversation repository using Smart AI Engine's database"""
    
    def __init__(self, smart_engine=None):
        """Initialize with reference to Smart AI Engine"""
        self.smart_engine = smart_engine
    
    async def log_interaction(self, user_id: str, message: str, response: str, domain: str):
        """Log interaction to existing database"""
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
    
    async def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get conversation history from existing database"""
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


class SmartEngineKnowledgeRepository(IKnowledgeRepository):
    """Knowledge repository using domain plugins and Smart AI Engine"""
    
    def __init__(self, domain_manager=None):
        """Initialize with domain manager"""
        self.domain_manager = domain_manager
    
    async def search_knowledge(self, query: str, domain: str, limit: int = 10) -> List[Dict]:
        """Search knowledge using domain plugin"""
        if not self.domain_manager:
            return []
        
        domain_plugin = self.domain_manager.get_domain(domain)
        if domain_plugin:
            return domain_plugin.search_knowledge(query, limit)
        
        return []
    
    async def get_strain_info(self, strain_name: str) -> Optional[Dict]:
        """Get strain information from knowledge base"""
        results = await self.search_knowledge(strain_name, 'budtender', 1)
        return results[0] if results else None