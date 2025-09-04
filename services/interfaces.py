"""
Service Interfaces - Dependency Inversion Principle
Defines contracts for services to enable loose coupling
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass

class IModel(ABC):
    """Interface for AI models"""
    
    @abstractmethod
    async def load(self) -> bool:
        """Load model into memory"""
        pass
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> Any:
        """Generate response from prompt"""
        pass
    
    @abstractmethod
    async def unload(self) -> None:
        """Unload model from memory"""
        pass

class IModelManager(ABC):
    """Interface for model management"""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize model manager"""
        pass
    
    @abstractmethod
    async def generate(self, model: Any, prompt: str, **kwargs) -> Any:
        """Generate using specified model"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[Any]:
        """Get list of available models"""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, bool]:
        """Get model status"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources"""
        pass

class IBudtenderService(ABC):
    """Interface for budtender service"""
    
    @abstractmethod
    async def chat(
        self,
        message: str,
        customer_id: str,
        language: str = "en",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process chat message"""
        pass

class IRecognitionService(ABC):
    """Interface for face recognition service"""
    
    @abstractmethod
    async def recognize(
        self,
        image_base64: str,
        store_id: str
    ) -> Dict[str, Any]:
        """Recognize customer from image"""
        pass
    
    @abstractmethod
    async def enroll(
        self,
        customer_id: str,
        image_base64: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """Enroll new customer"""
        pass

class IPricingService(ABC):
    """Interface for pricing service"""
    
    @abstractmethod
    async def calculate(
        self,
        product_id: str,
        quantity: float,
        customer_type: str = "regular"
    ) -> Dict[str, Any]:
        """Calculate dynamic pricing"""
        pass
    
    @abstractmethod
    async def get_recommendations(
        self,
        customer_id: str,
        product_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Get pricing recommendations"""
        pass

class IVerificationService(ABC):
    """Interface for age verification service"""
    
    @abstractmethod
    async def verify(
        self,
        document_base64: str,
        document_type: str = "drivers_license"
    ) -> Dict[str, Any]:
        """Verify age from document"""
        pass

class IProductRepository(ABC):
    """Interface for product data access"""
    
    @abstractmethod
    async def search(
        self,
        keywords: List[str],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search products by keywords"""
        pass
    
    @abstractmethod
    async def get_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product by ID"""
        pass
    
    @abstractmethod
    async def get_by_category(
        self,
        category: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get products by category"""
        pass

class IChatRepository(ABC):
    """Interface for chat history data access"""
    
    @abstractmethod
    async def save_interaction(
        self,
        customer_id: str,
        message: str,
        response: str,
        language: str,
        model_used: str
    ) -> None:
        """Save chat interaction"""
        pass
    
    @abstractmethod
    async def get_history(
        self,
        customer_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get chat history for customer"""
        pass

class ICacheManager(ABC):
    """Interface for caching"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set value in cache"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete from cache"""
        pass