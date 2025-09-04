"""
Product Repository Interface
Following SOLID principles - Interface Segregation and Dependency Inversion
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class IProductRepository(ABC):
    """Interface for product data access"""
    
    @abstractmethod
    async def search_products(self, params: Dict, limit: int = 10) -> List[Dict]:
        """Search for products based on parameters"""
        pass
    
    @abstractmethod
    async def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """Get a single product by ID"""
        pass
    
    @abstractmethod
    async def check_inventory(self, product_id: int) -> Dict:
        """Check product inventory status"""
        pass
    
    @abstractmethod
    async def get_recommendations(self, user_preferences: Dict, limit: int = 5) -> List[Dict]:
        """Get product recommendations based on preferences"""
        pass

class IConversationRepository(ABC):
    """Interface for conversation/history data access"""
    
    @abstractmethod
    async def log_interaction(self, user_id: str, message: str, response: str, domain: str):
        """Log a conversation interaction"""
        pass
    
    @abstractmethod
    async def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get conversation history for a user"""
        pass

class IKnowledgeRepository(ABC):
    """Interface for knowledge base access"""
    
    @abstractmethod
    async def search_knowledge(self, query: str, domain: str, limit: int = 10) -> List[Dict]:
        """Search domain-specific knowledge base"""
        pass
    
    @abstractmethod
    async def get_strain_info(self, strain_name: str) -> Optional[Dict]:
        """Get information about a specific strain"""
        pass