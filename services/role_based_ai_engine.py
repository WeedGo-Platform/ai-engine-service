"""
Role-Based AI Engine
Implements different search/extraction strategies based on AI role
Following Single Responsibility Principle
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import asdict

from services.search_interfaces import (
    SearchStrategy, 
    SearchCriteria,
    ISearchExtractor,
    IProductSearcher,
    IResponseFormatter,
    SearchOrchestrator
)
from services.llm_search_extractor import LLMSearchExtractor

logger = logging.getLogger(__name__)

class RoleBasedSearchExtractor(ISearchExtractor):
    """Concrete implementation that adapts based on role"""
    
    def __init__(self, llm_function, role: SearchStrategy):
        self.llm = llm_function
        self.role = role
        self.base_extractor = LLMSearchExtractor(llm_function)
        
        # Load role configuration
        config_path = Path("config/ai_roles.yaml")
        if config_path.exists():
            with open(config_path) as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {"roles": {}}
    
    def extract_criteria(self, query: str, context: Optional[Dict] = None) -> SearchCriteria:
        """Extract criteria using role-specific prompt"""
        
        # Get role-specific prompt
        prompt = self.get_extraction_prompt(self.role)
        
        # Add the query
        full_prompt = f"{prompt}\n\nUser Query: {query}"
        
        # If context provided, add it
        if context:
            if context.get("language") and context["language"] != "en":
                full_prompt += f"\nLanguage: {context['language']}"
            if context.get("previous_purchases"):
                full_prompt += f"\nCustomer usually buys: {context['previous_purchases']}"
        
        # Get extraction from LLM
        response = self.llm(full_prompt, max_tokens=200)
        response_text = response.get('choices', [{}])[0].get('text', '{}')
        
        # Parse response into SearchCriteria
        import json
        try:
            data = json.loads(response_text)
            return SearchCriteria(
                product_name=data.get("product_name"),
                category=data.get("category"),
                sub_category=data.get("sub_category"),
                size=data.get("size"),
                strain_type=data.get("strain_type"),
                min_price=data.get("min_price"),
                max_price=data.get("max_price"),
                effects=data.get("effects"),
                brand=data.get("brand")
            )
        except:
            # Fallback to base extractor
            extracted = self.base_extractor.extract_search_criteria(query)
            return SearchCriteria(**extracted)
    
    def get_extraction_prompt(self, role: SearchStrategy) -> str:
        """Get role-specific extraction prompt"""
        
        role_prompts = {
            SearchStrategy.BUDTENDER: """You are a cannabis budtender extracting search parameters.
Extract: product_name, category, sub_category, size, strain_type, price range.
Convert quantities: '2 by 1g' = '2x1g', 'half ounce' = '14g'.
Understand slang: 'fire', 'gas', 'loud' = high quality.
Output JSON only.""",

            SearchStrategy.MEDICAL: """You are a medical cannabis consultant extracting search parameters.
Focus on: CBD content, THC/CBD ratios, terpenes for conditions.
Understand conditions: anxiety, pain, inflammation, insomnia, PTSD.
Prioritize non-psychoactive when appropriate.
Output JSON only.""",

            SearchStrategy.RECREATIONAL: """You are extracting for recreational cannabis users.
Focus on: High THC, popular strains, social effects.
Understand: 'get lit', 'party', 'chill', 'vibes'.
Suggest formats: pre-rolls, edibles for sharing.
Output JSON only.""",

            SearchStrategy.WHOLESALE: """You are extracting for B2B wholesale orders.
Focus on: Bulk quantities, price per unit, consistency.
Convert to wholesale: 'pounds', 'kilos', 'cases'.
Include: minimum order quantities.
Output JSON only.""",

            SearchStrategy.EDUCATIONAL: """You are extracting for educational purposes.
Focus on: Variety, representative samples, learning objectives.
Include: Different categories, effects, cannabinoid profiles.
Explain terminology in extraction.
Output JSON only."""
        }
        
        return role_prompts.get(role, role_prompts[SearchStrategy.BUDTENDER])

class RoleBasedProductSearcher(IProductSearcher):
    """Concrete implementation of product searcher"""
    
    def __init__(self, db_pool, role: SearchStrategy):
        self.db_pool = db_pool
        self.role = role
    
    async def search_products(self, criteria: SearchCriteria, limit: int = 50) -> List[Dict]:
        """Search for products based on criteria (Interface method)"""
        return await self.search(criteria)
    
    async def search_by_similarity(self, product_ids: List[int], limit: int = 10) -> List[Dict]:
        """Find similar products based on product IDs (Interface method)"""
        if not product_ids or not self.db_pool:
            return []
        
        async with self.db_pool.acquire() as conn:
            # Find products in same categories as the given products
            query = """
                SELECT DISTINCT p2.*
                FROM products p1
                JOIN products p2 ON p1.category = p2.category
                WHERE p1.id = ANY($1::int[])
                AND p2.id != ALL($1::int[])
                LIMIT $2
            """
            results = await conn.fetch(query, product_ids, limit)
            return [dict(r) for r in results]
    
    async def search(self, criteria: SearchCriteria) -> List[Dict[str, Any]]:
        """Search products based on criteria and role"""
        
        # Build query based on role priorities
        query_parts = []
        params = []
        
        # Convert criteria to dict for easier handling
        criteria_dict = {k: v for k, v in asdict(criteria).items() if v is not None}
        
        # Role-specific query building
        if self.role == SearchStrategy.MEDICAL:
            # Prioritize CBD products
            if not criteria.strain_type:
                query_parts.append("cbd_max_percent > 5")
        elif self.role == SearchStrategy.RECREATIONAL:
            # Prioritize high THC
            if not criteria.strain_type:
                query_parts.append("thc_max_percent > 20")
        
        # Standard criteria
        if criteria.product_name:
            query_parts.append("LOWER(product_name) LIKE %s")
            params.append(f"%{criteria.product_name.lower()}%")
        
        if criteria.category:
            query_parts.append("category = %s")
            params.append(criteria.category)
        
        if criteria.size:
            query_parts.append("size = %s")
            params.append(criteria.size)
        
        if criteria.strain_type:
            query_parts.append("plant_type ILIKE %s")
            params.append(f"%{criteria.strain_type}%")
        
        where_clause = " AND ".join(query_parts) if query_parts else "1=1"
        
        # Role-specific ordering
        order_by = self._get_role_specific_ordering()
        
        query = f"""
            SELECT * FROM products
            WHERE {where_clause}
            ORDER BY {order_by}
            LIMIT 20
        """
        
        async with self.db_pool.acquire() as conn:
            results = await conn.fetch(query, *params)
            return [dict(row) for row in results]
    
    def _get_role_specific_ordering(self) -> str:
        """Get role-specific result ordering"""
        
        orderings = {
            SearchStrategy.BUDTENDER: "unit_price ASC, thc_max_percent DESC",
            SearchStrategy.MEDICAL: "cbd_max_percent DESC, thc_max_percent ASC",
            SearchStrategy.RECREATIONAL: "thc_max_percent DESC, unit_price ASC",
            SearchStrategy.WHOLESALE: "unit_price ASC, id ASC",
            SearchStrategy.EDUCATIONAL: "category ASC, strain_type ASC"
        }
        
        return orderings.get(self.role, "unit_price ASC")
    
    async def search_by_effects(self, effects: List[str]) -> List[Dict[str, Any]]:
        """Search by desired effects"""
        # Implementation here
        return []
    
    async def search_by_medical_condition(self, condition: str) -> List[Dict[str, Any]]:
        """Search for medical conditions"""
        # Implementation here
        return []
    
    async def get_recommendations(self, customer_profile: Dict) -> List[Dict[str, Any]]:
        """Get personalized recommendations"""
        # Implementation here
        return []

class RoleBasedResponseFormatter(IResponseFormatter):
    """Concrete implementation of response formatter"""
    
    def __init__(self, role: SearchStrategy):
        self.role = role
    
    def format_products(self, products: List[Dict], role: SearchStrategy) -> str:
        """Format products based on role"""
        
        if not products:
            return self.format_no_results(SearchCriteria(), role)
        
        formatters = {
            SearchStrategy.BUDTENDER: self._format_budtender,
            SearchStrategy.MEDICAL: self._format_medical,
            SearchStrategy.RECREATIONAL: self._format_recreational,
            SearchStrategy.WHOLESALE: self._format_wholesale,
            SearchStrategy.EDUCATIONAL: self._format_educational
        }
        
        formatter = formatters.get(role, self._format_budtender)
        return formatter(products)
    
    def _format_budtender(self, products: List[Dict]) -> str:
        """Budtender friendly format"""
        response = "Here are some great options I found for you:\n\n"
        for i, p in enumerate(products[:5], 1):
            response += f"{i}. **{p['product_name']}** - ${p['unit_price']:.2f}\n"
            response += f"   {p['size']} | {p['plant_type']} | THC: {p['thc_max_percent']}%\n"
        return response
    
    def _format_medical(self, products: List[Dict]) -> str:
        """Medical focused format"""
        response = "Based on your medical needs, I recommend:\n\n"
        for i, p in enumerate(products[:3], 1):
            response += f"{i}. **{p['product_name']}**\n"
            response += f"   CBD: {p['cbd_max_percent']}% | THC: {p['thc_max_percent']}%\n"
            response += f"   Ratio: {self._calculate_ratio(p)}\n"
            response += f"   Recommended for: {self._get_medical_uses(p)}\n\n"
        return response
    
    def _format_recreational(self, products: List[Dict]) -> str:
        """Fun, social format"""
        response = "🔥 Check out these fire options! 🔥\n\n"
        for i, p in enumerate(products[:6], 1):
            response += f"{i}. **{p['product_name']}** 🌿\n"
            response += f"   THC: {p['thc_max_percent']}% - "
            if p['thc_max_percent'] > 25:
                response += "SUPER POTENT! 🚀\n"
            elif p['thc_max_percent'] > 20:
                response += "Nice and strong! 💪\n"
            else:
                response += "Smooth vibes! 😎\n"
            response += f"   Only ${p['unit_price']:.2f}\n\n"
        return response
    
    def _format_wholesale(self, products: List[Dict]) -> str:
        """Business format with bulk info"""
        response = "Wholesale Product Listing:\n\n"
        response += "| Product | Size | Units/Case | Price/Unit | Stock |\n"
        response += "|---------|------|------------|------------|-------|\n"
        for p in products[:10]:
            response += f"| {p['product_name'][:20]} | {p['size']} | 24 | ${p['unit_price']:.2f} | Available |\n"
        return response
    
    def _format_educational(self, products: List[Dict]) -> str:
        """Educational format with details"""
        response = "Let me explain these cannabis products:\n\n"
        for i, p in enumerate(products[:4], 1):
            response += f"{i}. **{p['product_name']}**\n"
            response += f"   Category: {p['category']}\n"
            response += f"   Type: {p['plant_type']}\n"
            response += f"   Cannabinoids: THC {p['thc_max_percent']}%, CBD {p['cbd_max_percent']}%\n"
            response += f"   What this means: {self._explain_effects(p)}\n\n"
        return response
    
    def _calculate_ratio(self, product: Dict) -> str:
        """Calculate CBD:THC ratio"""
        cbd = product.get('cbd_max_percent', 0)
        thc = product.get('thc_max_percent', 1)
        if thc == 0:
            return "CBD only"
        ratio = cbd / thc
        if ratio > 2:
            return f"{ratio:.1f}:1 CBD dominant"
        elif ratio > 0.5:
            return "Balanced"
        else:
            return "THC dominant"
    
    def _get_medical_uses(self, product: Dict) -> str:
        """Get medical uses based on profile"""
        cbd = product.get('cbd_max_percent', 0)
        if cbd > 10:
            return "Anti-inflammatory, anxiety relief, pain management"
        elif cbd > 5:
            return "Mild pain relief, relaxation, stress reduction"
        else:
            return "Consult with medical professional"
    
    def _explain_effects(self, product: Dict) -> str:
        """Explain effects educationally"""
        strain = product.get('plant_type', '').lower()
        if 'sativa' in strain:
            return "Typically energizing and uplifting, good for daytime use"
        elif 'indica' in strain:
            return "Typically relaxing and sedating, good for evening use"
        else:
            return "Balanced effects, suitable for various times"
    
    def format_no_results(self, criteria: SearchCriteria, role: SearchStrategy) -> str:
        """Format no results message"""
        messages = {
            SearchStrategy.BUDTENDER: "I couldn't find exactly what you're looking for. Can you tell me more about what effects you want?",
            SearchStrategy.MEDICAL: "No products match your medical criteria. Would you like to consult with our medical specialist?",
            SearchStrategy.RECREATIONAL: "Bummer! Nothing matches that. Want to try something different?",
            SearchStrategy.WHOLESALE: "No products available for bulk order with those specifications.",
            SearchStrategy.EDUCATIONAL: "I don't have products matching that query. Let me explain what's available instead."
        }
        return messages.get(role, "No products found matching your criteria.")
    
    def format_recommendations(self, products: List[Dict], reason: str, role: SearchStrategy) -> str:
        """Format recommendations with reasoning"""
        response = f"Based on {reason}, I recommend:\n\n"
        response += self.format_products(products, role)
        return response

# Main engine that uses role-based components

class RoleBasedAIEngine:
    """AI Engine that adapts behavior based on role"""
    
    def __init__(self, llm_function, db_pool):
        self.llm = llm_function
        self.db_pool = db_pool
        self.current_role = SearchStrategy.BUDTENDER
        self.orchestrator = None
        self._initialize_orchestrator()
    
    def _initialize_orchestrator(self):
        """Initialize the search orchestrator"""
        self.orchestrator = SearchOrchestrator(
            self.current_role,
            self.llm,
            self.db_pool
        )
    
    def switch_role(self, role: SearchStrategy):
        """Switch to a different AI role"""
        logger.info(f"Switching from {self.current_role.value} to {role.value}")
        self.current_role = role
        self.orchestrator.switch_role(role)
    
    def detect_role_from_context(self, message: str, context: Dict) -> SearchStrategy:
        """Auto-detect appropriate role from message and context"""
        
        message_lower = message.lower()
        
        # Check for medical indicators
        medical_keywords = ["pain", "anxiety", "insomnia", "medical", "cbd", "condition"]
        if any(keyword in message_lower for keyword in medical_keywords):
            return SearchStrategy.MEDICAL
        
        # Check for recreational indicators
        recreational_keywords = ["party", "fun", "weekend", "friends", "high", "lit"]
        if any(keyword in message_lower for keyword in recreational_keywords):
            return SearchStrategy.RECREATIONAL
        
        # Check for wholesale indicators
        wholesale_keywords = ["bulk", "wholesale", "pounds", "kilos", "business"]
        if any(keyword in message_lower for keyword in wholesale_keywords):
            return SearchStrategy.WHOLESALE
        
        # Check for educational indicators
        educational_keywords = ["what is", "how does", "explain", "tell me about", "learn"]
        if any(keyword in message_lower for keyword in educational_keywords):
            return SearchStrategy.EDUCATIONAL
        
        # Default to budtender
        return SearchStrategy.BUDTENDER
    
    async def process_message(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Process message with role-appropriate handling"""
        
        # Auto-detect role if needed
        if context and context.get("auto_detect_role", True):
            detected_role = self.detect_role_from_context(message, context or {})
            if detected_role != self.current_role:
                self.switch_role(detected_role)
        
        # Process with current role
        result = await self.orchestrator.process_search(message, context)
        
        # Add role info to result
        result["role_used"] = self.current_role.value
        
        return result