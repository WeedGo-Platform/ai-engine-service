"""
Enhanced Search Criteria Extractor
Improves extraction of search parameters from user queries
"""
import re
import json
import logging
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

class EnhancedSearchExtractor:
    """Extract structured search criteria from natural language queries"""
    
    def __init__(self):
        # Size mappings
        self.size_mappings = {
            'eighth': '3.5g',
            '1/8': '3.5g',
            '1/8oz': '3.5g',
            'quarter': '7g',
            '1/4': '7g',
            '1/4oz': '7g',
            'half': '14g',
            'half ounce': '14g',
            '1/2': '14g',
            '1/2oz': '14g',
            '1/2 ounce': '14g',
            'ounce': '28g',
            'oz': '28g',
            '1oz': '28g'
        }
        
        # Category mappings
        self.category_keywords = {
            'flower': 'Flower',
            'flowers': 'Flower',
            'bud': 'Flower',
            'buds': 'Flower',
            'dried': 'Flower',
            'edible': 'Edibles',
            'edibles': 'Edibles',
            'gummy': 'Edibles',
            'gummies': 'Edibles',
            'chocolate': 'Edibles',
            'beverage': 'Edibles',
            'drink': 'Edibles',
            'vape': 'Vapes',
            'vapes': 'Vapes',
            'cartridge': 'Vapes',
            'cart': 'Vapes',
            'extract': 'Extracts',
            'extracts': 'Extracts',
            'oil': 'Extracts',
            'resin': 'Extracts',
            'topical': 'Topicals',
            'topicals': 'Topicals',
            'cream': 'Topicals',
            'lotion': 'Topicals'
        }
        
        # Subcategory mappings
        self.subcategory_keywords = {
            'joint': 'Pre-Rolls',
            'joints': 'Pre-Rolls',
            'pre-roll': 'Pre-Rolls',
            'preroll': 'Pre-Rolls',
            'pre-rolled': 'Pre-Rolls',
            'rolled': 'Pre-Rolls',
            'dried flower': 'Dried Flower',
            'flower': 'Dried Flower',
            'bud': 'Dried Flower',
            'buds': 'Dried Flower'
        }
        
        # Strain type mappings
        self.strain_mappings = {
            'sativa': 'Sativa',
            'sativas': 'Sativa',
            'indica': 'Indica',
            'indicas': 'Indica',
            'hybrid': 'Hybrid',
            'hybrids': 'Hybrid',
            'balanced': 'Hybrid'
        }
        
        # Known product names (partial list - should be loaded from DB)
        self.known_products = [
            'Pink Kush', 'Blue Dream', 'OG Kush', 'Purple Kush',
            'Sour Diesel', 'Northern Lights', 'Granddaddy Purple',
            'Wedding Cake', 'Gelato', 'GG4', 'Gorilla Glue',
            'White Widow', 'AK-47', 'Jack Herer', 'Green Crack'
        ]
    
    def extract_search_criteria(self, user_query: str) -> Dict[str, Any]:
        """
        Extract structured search criteria from user query
        
        Args:
            user_query: Natural language query from user
            
        Returns:
            Dictionary with search parameters
        """
        query_lower = user_query.lower()
        criteria = {
            'product_name': None,
            'category': None,
            'sub_category': None,
            'size': None,
            'strain_type': None,
            'price_range': None,
            'sort_by': 'price_asc'
        }
        
        # Extract product name
        criteria['product_name'] = self._extract_product_name(user_query, query_lower)
        
        # Extract category
        criteria['category'] = self._extract_category(query_lower)
        
        # Extract subcategory
        criteria['sub_category'] = self._extract_subcategory(query_lower, criteria['category'])
        
        # Extract size
        criteria['size'] = self._extract_size(query_lower)
        
        # Extract strain type
        criteria['strain_type'] = self._extract_strain_type(query_lower)
        
        # Extract price constraints
        criteria['price_range'] = self._extract_price_range(query_lower)
        
        # Clean up None values
        criteria = {k: v for k, v in criteria.items() if v is not None}
        
        logger.info(f"Extracted search criteria: {criteria}")
        return criteria
    
    def _extract_product_name(self, original_query: str, query_lower: str) -> Optional[str]:
        """Extract specific product name from query"""
        
        # Check for exact product name matches (case-insensitive)
        for product in self.known_products:
            product_lower = product.lower()
            if product_lower in query_lower:
                # Return the properly capitalized version
                return product
        
        # Check for common patterns
        patterns = [
            r'(pink\s+kush)',
            r'(blue\s+dream)',
            r'(og\s+kush)',
            r'(purple\s+kush)',
            r'(sour\s+diesel)',
            r'(northern\s+lights)',
            r'(wedding\s+cake)',
            r'(gorilla\s+glue)',
            r'(gg4)',
            r'(white\s+widow)',
            r'(jack\s+herer)',
            r'(green\s+crack)',
            r'(\w+\s+kush)',  # Any word + kush
            r'(\w+\s+dream)',  # Any word + dream
            r'(\w+\s+haze)',  # Any word + haze
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                # Capitalize properly
                product_name = match.group(1)
                return ' '.join(word.capitalize() for word in product_name.split())
        
        return None
    
    def _extract_category(self, query_lower: str) -> Optional[str]:
        """Extract category from query"""
        
        for keyword, category in self.category_keywords.items():
            if keyword in query_lower:
                return category
        
        # Check if query mentions joints/pre-rolls -> Flower category
        if any(word in query_lower for word in ['joint', 'joints', 'pre-roll', 'preroll']):
            return 'Flower'
        
        return None
    
    def _extract_subcategory(self, query_lower: str, category: Optional[str]) -> Optional[str]:
        """Extract subcategory from query"""
        
        # Check for explicit subcategory keywords
        for keyword, subcategory in self.subcategory_keywords.items():
            if keyword in query_lower:
                # Special case: if "flower" is mentioned with a product name, 
                # it usually means Dried Flower, not Pre-Rolls
                if subcategory == 'Dried Flower' and category == 'Flower':
                    # Check if pre-roll keywords are also present
                    if not any(word in query_lower for word in ['joint', 'pre-roll', 'preroll', 'rolled']):
                        return 'Dried Flower'
                return subcategory
        
        # Infer subcategory from context
        if category == 'Flower':
            # If query mentions flower/bud without pre-roll keywords, assume dried flower
            if 'flower' in query_lower or 'bud' in query_lower:
                if not any(word in query_lower for word in ['joint', 'pre-roll', 'preroll']):
                    return 'Dried Flower'
            # If query mentions joints/pre-rolls, set subcategory
            elif any(word in query_lower for word in ['joint', 'joints', 'pre-roll', 'preroll']):
                return 'Pre-Rolls'
        
        return None
    
    def _extract_size(self, query_lower: str) -> Optional[str]:
        """Extract size specification from query"""
        
        # Check for mapped sizes (eighth, quarter, half, etc.)
        for size_term, standard_size in self.size_mappings.items():
            if size_term in query_lower:
                return standard_size
        
        # Check for explicit gram amounts
        gram_pattern = r'(\d+(?:\.\d+)?)\s*(?:g|gram|grams)'
        match = re.search(gram_pattern, query_lower)
        if match:
            return f"{match.group(1)}g"
        
        # Check for pre-roll specific sizes
        preroll_pattern = r'(\d+)\s*x\s*(\d+(?:\.\d+)?)\s*g'
        match = re.search(preroll_pattern, query_lower)
        if match:
            return f"{match.group(1)}x{match.group(2)}g"
        
        # Check for ounce specifications
        oz_pattern = r'(\d+(?:/\d+)?)\s*(?:oz|ounce)'
        match = re.search(oz_pattern, query_lower)
        if match:
            oz_str = match.group(1)
            if '1/8' in oz_str:
                return '3.5g'
            elif '1/4' in oz_str:
                return '7g'
            elif '1/2' in oz_str:
                return '14g'
            elif oz_str == '1':
                return '28g'
        
        return None
    
    def _extract_strain_type(self, query_lower: str) -> Optional[str]:
        """Extract strain type from query"""
        
        for strain_keyword, strain_type in self.strain_mappings.items():
            if strain_keyword in query_lower and not self._is_part_of_product_name(strain_keyword, query_lower):
                return strain_type
        
        return None
    
    def _extract_price_range(self, query_lower: str) -> Optional[Dict[str, Any]]:
        """Extract price constraints from query"""
        
        price_range = {}
        
        # Check for "under X" pattern
        under_pattern = r'under\s+\$?(\d+(?:\.\d+)?)'
        match = re.search(under_pattern, query_lower)
        if match:
            price_range['max'] = float(match.group(1))
        
        # Check for "less than X" pattern
        less_pattern = r'less\s+than\s+\$?(\d+(?:\.\d+)?)'
        match = re.search(less_pattern, query_lower)
        if match:
            price_range['max'] = float(match.group(1))
        
        # Check for "between X and Y" pattern
        between_pattern = r'between\s+\$?(\d+(?:\.\d+)?)\s+and\s+\$?(\d+(?:\.\d+)?)'
        match = re.search(between_pattern, query_lower)
        if match:
            price_range['min'] = float(match.group(1))
            price_range['max'] = float(match.group(2))
        
        # Check for cheapest/lowest price
        if any(word in query_lower for word in ['cheapest', 'lowest', 'cheap', 'budget']):
            price_range['sort'] = 'lowest'
        
        # Check for most expensive/highest price
        if any(word in query_lower for word in ['expensive', 'premium', 'top shelf', 'best']):
            price_range['sort'] = 'highest'
        
        return price_range if price_range else None
    
    def _is_part_of_product_name(self, word: str, query: str) -> bool:
        """Check if a word is part of a product name rather than a standalone descriptor"""
        
        # Check if word appears in known product names in the query
        for product in self.known_products:
            if product.lower() in query and word in product.lower():
                return True
        
        return False
    
    def build_search_filters(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert extracted criteria into search API filters
        
        Args:
            criteria: Extracted search criteria
            
        Returns:
            Filters dictionary for search API
        """
        filters = {}
        
        # Handle product name
        if criteria.get('product_name'):
            filters['query'] = criteria['product_name']
        
        # Handle category
        if criteria.get('category'):
            filters['category'] = criteria['category']
        
        # Handle subcategory
        if criteria.get('sub_category'):
            if 'filters' not in filters:
                filters['filters'] = {}
            filters['filters']['sub_category'] = criteria['sub_category']
        
        # Handle size
        if criteria.get('size'):
            if 'filters' not in filters:
                filters['filters'] = {}
            filters['filters']['size'] = criteria['size']
        
        # Handle strain type
        if criteria.get('strain_type'):
            if 'filters' not in filters:
                filters['filters'] = {}
            filters['filters']['strain_type'] = criteria['strain_type']
        
        # Handle price range
        if criteria.get('price_range'):
            if 'filters' not in filters:
                filters['filters'] = {}
            if 'max' in criteria['price_range']:
                filters['filters']['max_price'] = criteria['price_range']['max']
            if 'min' in criteria['price_range']:
                filters['filters']['min_price'] = criteria['price_range']['min']
            if 'sort' in criteria['price_range']:
                filters['sort'] = 'price_asc' if criteria['price_range']['sort'] == 'lowest' else 'price_desc'
        
        return filters