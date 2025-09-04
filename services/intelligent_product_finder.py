#!/usr/bin/env python3
"""
Intelligent Product Finder
Handles complex queries and always returns relevant products
"""

import logging
from typing import Dict, List, Optional, Tuple
import httpx
import asyncio

logger = logging.getLogger(__name__)

class IntelligentProductFinder:
    """
    Smart product finder that always returns relevant products
    """
    
    def __init__(self, api_base: str = "http://localhost:8080"):
        self.api_base = api_base
        
    async def get_category_showcase(self) -> Dict:
        """
        Get sample products from each category for showcase
        """
        categories = ["Flower", "Edibles", "Vapes", "Extracts", "Topicals", "Accessories"]
        showcase = {}
        
        async with httpx.AsyncClient() as client:
            tasks = []
            for category in categories:
                # Get 2 products from each category
                task = client.post(
                    f"{self.api_base}/api/v1/products/search",
                    json={"category": category, "limit": 2},
                    timeout=5.0
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            for category, response in zip(categories, responses):
                if not isinstance(response, Exception) and response.status_code == 200:
                    products = response.json()
                    if products:
                        showcase[category] = products[:2]
                    else:
                        showcase[category] = []
                else:
                    showcase[category] = []
        
        return showcase
    
    async def find_by_preferences(self, preferences: Dict) -> List[Dict]:
        """
        Find products based on complex preferences
        
        Examples:
        - {"no_smoking": True, "no_edibles": True} -> Vapes, Topicals, Capsules
        - {"odorless": True, "sativa": True} -> Capsules, Tablets, Tinctures
        """
        
        # Map preferences to search parameters
        search_params = self._parse_preferences(preferences)
        all_products = []
        
        async with httpx.AsyncClient() as client:
            tasks = []
            
            for params in search_params:
                task = client.post(
                    f"{self.api_base}/api/v1/products/search",
                    json=params,
                    timeout=5.0
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            for response in responses:
                if not isinstance(response, Exception) and response.status_code == 200:
                    products = response.json()
                    all_products.extend(products[:3])  # Take top 3 from each search
        
        # Remove duplicates by product ID
        seen = set()
        unique_products = []
        for product in all_products:
            if product.get('id') not in seen:
                seen.add(product.get('id'))
                unique_products.append(product)
        
        return unique_products[:10]  # Return top 10 unique products
    
    def _parse_preferences(self, preferences: Dict) -> List[Dict]:
        """
        Parse complex preferences into search parameters
        """
        search_params = []
        
        # Handle "no smoking" preference
        if preferences.get("no_smoking"):
            # Exclude Flower category, focus on alternatives
            alternative_categories = []
            
            if not preferences.get("no_edibles"):
                alternative_categories.append("Edibles")
            
            if not preferences.get("no_vapes"):
                alternative_categories.append("Vapes")
            
            # Always include these for non-smokers
            alternative_categories.extend(["Extracts", "Topicals"])
            
            for category in alternative_categories:
                params = {"category": category, "limit": 5}
                
                # Add strain preference if specified
                if preferences.get("strain_type"):
                    params["query"] = preferences["strain_type"]
                
                search_params.append(params)
        
        # Handle "odorless" preference
        if preferences.get("odorless"):
            # Search for specific odorless products
            odorless_searches = [
                {"query": "capsule", "limit": 3},
                {"query": "tablet", "limit": 3},
                {"query": "softgel", "limit": 3},
                {"query": "tincture", "limit": 3},
                {"category": "Topicals", "limit": 3}
            ]
            
            for search in odorless_searches:
                if preferences.get("strain_type"):
                    search["query"] = search.get("query", "") + " " + preferences["strain_type"]
                search_params.append(search)
        
        # Handle specific effect preferences
        if preferences.get("effect"):
            search_params.append({
                "intent": preferences["effect"],
                "limit": 5
            })
        
        # Default fallback if no specific preferences
        if not search_params:
            search_params.append({"limit": 10})
        
        return search_params
    
    def parse_customer_message(self, message: str) -> Dict:
        """
        Parse customer message into preferences
        """
        message_lower = message.lower()
        preferences = {}
        
        # Check for consumption method preferences
        if any(phrase in message_lower for phrase in ["don't smoke", "dont smoke", "no smoking", "don't like to smoke"]):
            preferences["no_smoking"] = True
        
        if any(phrase in message_lower for phrase in ["don't like edibles", "dont like edibles", "no edibles"]):
            preferences["no_edibles"] = True
        
        if any(phrase in message_lower for phrase in ["no vape", "don't vape", "dont vape"]):
            preferences["no_vapes"] = True
        
        # Check for odor preferences
        if any(word in message_lower for word in ["odorless", "odourless", "no smell", "discrete", "discreet"]):
            preferences["odorless"] = True
        
        # Check for strain preferences
        if "sativa" in message_lower:
            preferences["strain_type"] = "sativa"
        elif "indica" in message_lower:
            preferences["strain_type"] = "indica"
        elif "hybrid" in message_lower:
            preferences["strain_type"] = "hybrid"
        
        # Check for effect preferences
        effect_keywords = {
            "sleep": ["sleep", "insomnia", "rest"],
            "pain": ["pain", "ache", "hurt"],
            "relax": ["relax", "calm", "anxiety", "stress"],
            "energy": ["energy", "energetic", "focus", "productive"],
            "appetite": ["appetite", "hungry", "munchies"]
        }
        
        for effect, keywords in effect_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                preferences["effect"] = effect
                break
        
        # Check for potency preferences
        if any(word in message_lower for word in ["mild", "low thc", "beginner", "light"]):
            preferences["potency"] = "low"
        elif any(word in message_lower for word in ["strong", "high thc", "potent"]):
            preferences["potency"] = "high"
        
        return preferences
    
    async def smart_product_search(self, message: str) -> Tuple[List[Dict], str]:
        """
        Smart search that always returns relevant products
        Returns: (products, explanation)
        """
        
        message_lower = message.lower()
        
        # Check for specific product types first
        if "dab" in message_lower or "concentrate" in message_lower:
            # Search for dab/concentrate products
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/api/v1/products/search",
                    json={"category": "Extracts", "limit": 10},
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    products = response.json()
                    if products:
                        return products[:10], "Here are our dab concentrates and extracts:"
        
        # Check if asking about categories
        if any(phrase in message_lower for phrase in ["what categories", "all categories", "types of products", "what do you carry"]):
            showcase = await self.get_category_showcase()
            
            # Flatten showcase into product list
            all_products = []
            explanation_parts = []
            
            for category, products in showcase.items():
                if products:
                    all_products.extend(products)
                    explanation_parts.append(f"**{category}** ({len(products)} shown)")
            
            explanation = f"We carry these categories: {', '.join(explanation_parts)}"
            return all_products, explanation
        
        # Check for complex preferences
        preferences = self.parse_customer_message(message)
        
        if preferences:
            products = await self.find_by_preferences(preferences)
            
            # Build explanation based on preferences
            explanation_parts = []
            
            if preferences.get("no_smoking"):
                explanation_parts.append("non-smoking options")
            if preferences.get("no_edibles"):
                explanation_parts.append("excluding edibles")
            if preferences.get("odorless"):
                explanation_parts.append("odorless products")
            if preferences.get("strain_type"):
                explanation_parts.append(f"{preferences['strain_type']} strains")
            
            if explanation_parts:
                explanation = f"Here are {', '.join(explanation_parts)} for you:"
            else:
                explanation = "Here are some options based on your preferences:"
            
            return products, explanation
        
        # Default: search for what they asked
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/api/v1/products/search",
                json={"query": message, "limit": 10},
                timeout=5.0
            )
            
            if response.status_code == 200:
                products = response.json()
                if products:
                    return products, f"Found {len(products)} products matching your request:"
                else:
                    # If no direct match, get some recommendations
                    response = await client.post(
                        f"{self.api_base}/api/v1/products/search",
                        json={"limit": 10},
                        timeout=5.0
                    )
                    products = response.json() if response.status_code == 200 else []
                    return products, "Here are some popular products you might like:"
            
        return [], "Let me help you find what you're looking for."