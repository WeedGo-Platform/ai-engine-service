"""
Search and Extraction Interfaces
Following Single Responsibility Principle for different AI roles
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class SearchStrategy(Enum):
    """Different search strategies for different roles"""
    BUDTENDER = "budtender"  # Cannabis product search
    MEDICAL = "medical"      # Medical/health focused search
    RECREATIONAL = "recreational"  # Fun/party focused search
    WHOLESALE = "wholesale"  # B2B bulk search
    EDUCATIONAL = "educational"  # Information/learning search

@dataclass
class SearchCriteria:
    """Standardized search criteria"""
    product_name: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    size: Optional[str] = None
    strain_type: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    effects: Optional[List[str]] = None
    terpenes: Optional[List[str]] = None
    thc_range: Optional[tuple] = None
    cbd_range: Optional[tuple] = None
    brand: Optional[str] = None
    
class ISearchExtractor(ABC):
    """Interface for extracting search criteria from natural language"""
    
    @abstractmethod
    def extract_criteria(self, query: str, context: Optional[Dict] = None) -> SearchCriteria:
        """Extract structured search criteria from user query"""
        pass
    
    @abstractmethod
    def get_extraction_prompt(self, role: SearchStrategy) -> str:
        """Get role-specific extraction prompt"""
        pass

class IProductSearcher(ABC):
    """Interface for searching products"""
    
    @abstractmethod
    async def search_products(self, criteria: SearchCriteria, limit: int = 50) -> List[Dict]:
        """Search for products based on criteria"""
        pass
    
    @abstractmethod
    async def search_by_similarity(self, product_ids: List[int], limit: int = 10) -> List[Dict]:
        """Find similar products based on product IDs"""
        pass

class ISearchEngine(ABC):
    """
    Main search engine interface for budtender and other roles
    Combines extraction, search, and response generation
    """
    
    @abstractmethod
    async def process_query(
        self, 
        message: str, 
        context: Optional[Dict] = None,
        session_id: Optional[str] = None,
        personality: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a search query and return products with response
        
        Returns:
            Dict containing:
            - message: str (AI response)
            - products: List[Dict] (found products)
            - search_performed: bool
            - search_intent: Dict (extracted intent)
            - quick_actions: List[Dict] (suggested actions)
        """
        pass
    
    @abstractmethod
    async def initialize(self, db_pool: Any, llm: Any, prompt_manager: Any) -> None:
        """Initialize the search engine with required dependencies"""
        pass
    

class IResponseFormatter(ABC):
    """Interface for formatting search results into responses"""
    
    @abstractmethod
    def format_products(self, products: List[Dict], role: SearchStrategy) -> str:
        """Format product list for specific role"""
        pass
    
    @abstractmethod
    def format_no_results(self, criteria: SearchCriteria, role: SearchStrategy) -> str:
        """Format message when no products found"""
        pass
    
    @abstractmethod
    def format_recommendations(self, products: List[Dict], reason: str, role: SearchStrategy) -> str:
        """Format product recommendations with reasoning"""
        pass

# Concrete implementations for different roles

class BudtenderSearchExtractor(ISearchExtractor):
    """Cannabis budtender specific extraction"""
    
    def __init__(self, llm_function):
        self.llm = llm_function
    
    def extract_criteria(self, query: str, context: Optional[Dict] = None) -> SearchCriteria:
        """Extract with cannabis-specific understanding"""
        prompt = self.get_extraction_prompt(SearchStrategy.BUDTENDER)
        # Implementation uses existing llm_search_extractor logic
        # but with role-specific prompts
        return SearchCriteria()  # Placeholder
    
    def get_extraction_prompt(self, role: SearchStrategy) -> str:
        """Get budtender-specific extraction prompt"""
        return """You are a cannabis expert extracting search parameters.
        Focus on strain types, THC/CBD levels, terpenes, and effects.
        Understand slang terms like 'fire', 'gas', 'loud' for quality.
        Convert quantities: '2 by 1g' = '2x1g', 'half ounce' = '14g'
        """

class MedicalSearchExtractor(ISearchExtractor):
    """Medical cannabis specific extraction"""
    
    def __init__(self, llm_function):
        self.llm = llm_function
    
    def extract_criteria(self, query: str, context: Optional[Dict] = None) -> SearchCriteria:
        """Extract with medical focus"""
        # Focus on CBD, ratios, terpenes for conditions
        return SearchCriteria()  # Placeholder
    
    def get_extraction_prompt(self, role: SearchStrategy) -> str:
        """Get medical-specific extraction prompt"""
        return """You are a medical cannabis consultant extracting search parameters.
        Focus on CBD/THC ratios, specific terpenes for conditions, dosage.
        Understand medical terms: anxiety, pain, inflammation, insomnia.
        Prioritize non-psychoactive options when appropriate.
        """

class RecreationalSearchExtractor(ISearchExtractor):
    """Recreational/party focused extraction"""
    
    def __init__(self, llm_function):
        self.llm = llm_function
    
    def extract_criteria(self, query: str, context: Optional[Dict] = None) -> SearchCriteria:
        """Extract with recreational focus"""
        # Focus on THC levels, popular strains, social effects
        return SearchCriteria()  # Placeholder
    
    def get_extraction_prompt(self, role: SearchStrategy) -> str:
        """Get recreational-specific extraction prompt"""
        return """You are extracting search parameters for recreational users.
        Focus on THC potency, energizing/social effects, popular strains.
        Understand party terms: 'get lit', 'vibes', 'chill', 'turn up'.
        Suggest social-friendly formats like pre-rolls and edibles.
        """

# Factory for creating role-specific extractors

class SearchExtractorFactory:
    """Factory for creating appropriate search extractors"""
    
    @staticmethod
    def create_extractor(role: SearchStrategy, llm_function) -> ISearchExtractor:
        """Create extractor based on role"""
        # Import here to avoid circular dependency
        from services.role_based_ai_engine import RoleBasedSearchExtractor
        return RoleBasedSearchExtractor(llm_function, role)

# Similar pattern for searchers and formatters

class ProductSearcherFactory:
    """Factory for creating appropriate product searchers"""
    
    @staticmethod
    def create_searcher(role: SearchStrategy, db_pool) -> IProductSearcher:
        """Create searcher based on role"""
        # Import here to avoid circular dependency
        from services.role_based_ai_engine import RoleBasedProductSearcher
        return RoleBasedProductSearcher(db_pool, role)

class ResponseFormatterFactory:
    """Factory for creating appropriate response formatters"""
    
    @staticmethod
    def create_formatter(role: SearchStrategy) -> IResponseFormatter:
        """Create formatter based on role"""
        # Import here to avoid circular dependency
        from services.role_based_ai_engine import RoleBasedResponseFormatter
        return RoleBasedResponseFormatter(role)

# Orchestrator that uses the interfaces

class SearchOrchestrator:
    """Orchestrates search using appropriate strategies"""
    
    def __init__(self, role: SearchStrategy, llm_function, db_pool):
        self.role = role
        self.extractor = SearchExtractorFactory.create_extractor(role, llm_function)
        self.searcher = ProductSearcherFactory.create_searcher(role, db_pool)
        self.formatter = ResponseFormatterFactory.create_formatter(role)
    
    async def process_search(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Process search request using role-specific components"""
        
        # 1. Extract criteria using role-specific extractor
        criteria = self.extractor.extract_criteria(query, context)
        
        # 2. Search using role-specific searcher
        products = await self.searcher.search(criteria)
        
        # 3. Format using role-specific formatter
        if products:
            response = self.formatter.format_products(products, self.role)
        else:
            response = self.formatter.format_no_results(criteria, self.role)
        
        return {
            "response": response,
            "products": products,
            "criteria": criteria,
            "role": self.role.value
        }
    
    def switch_role(self, new_role: SearchStrategy):
        """Switch to different search strategy"""
        self.role = new_role
        # Recreate components for new role
        self.extractor = SearchExtractorFactory.create_extractor(new_role, self.extractor.llm)
        # ... etc