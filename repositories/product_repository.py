"""
Product Repository - Data access for cannabis products
Implements full-text search and similarity matching
"""

import logging
from typing import List, Dict, Any, Optional

from repositories.base_repository import BaseRepository
from services.interfaces import IProductRepository

logger = logging.getLogger(__name__)

class ProductRepository(BaseRepository, IProductRepository):
    """
    Repository for product data access
    Handles OCS product catalog queries
    """
    
    def __init__(self):
        """Initialize product repository"""
        super().__init__("products")
    
    async def search(
        self,
        keywords: List[str],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search products using full-text search
        
        Args:
            keywords: Search keywords
            limit: Maximum results
        
        Returns:
            List of matching products
        """
        if not keywords:
            return []
        
        # Build search query
        search_term = " | ".join(keywords)  # OR operator for tsvector
        
        query = """
            SELECT 
                id,
                ocs_item_number,
                product_name,
                brand,
                category,
                subcategory,
                thc_content,
                cbd_content,
                unit_price,
                effects,
                terpenes,
                description,
                ts_rank(search_vector, to_tsquery('english', $1)) as rank
            FROM products
            WHERE search_vector @@ to_tsquery('english', $1)
            ORDER BY rank DESC
            LIMIT $2
        """
        
        try:
            results = await self.fetch_many(query, search_term, limit)
            
            # Process results
            for result in results:
                # Parse JSON fields
                if result.get("effects") and isinstance(result["effects"], str):
                    result["effects"] = result["effects"].split(",")
                if result.get("terpenes") and isinstance(result["terpenes"], str):
                    result["terpenes"] = result["terpenes"].split(",")
            
            return results
            
        except Exception as e:
            logger.error(f"Product search error: {str(e)}")
            
            # Fallback to LIKE search
            return await self._fallback_search(keywords, limit)
    
    async def _fallback_search(
        self,
        keywords: List[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fallback search using LIKE patterns"""
        
        # Build LIKE conditions
        conditions = []
        values = []
        param_count = 1
        
        for keyword in keywords:
            conditions.append(f"""
                (product_name ILIKE ${param_count} OR 
                 brand ILIKE ${param_count} OR 
                 category ILIKE ${param_count})
            """)
            values.append(f"%{keyword}%")
            param_count += 1
        
        where_clause = " OR ".join(conditions)
        
        query = f"""
            SELECT 
                id,
                ocs_item_number,
                product_name,
                brand,
                category,
                subcategory,
                thc_content,
                cbd_content,
                unit_price,
                effects,
                terpenes,
                description
            FROM products
            WHERE {where_clause}
            LIMIT ${param_count}
        """
        
        values.append(limit)
        
        return await self.fetch_many(query, *values)
    
    async def get_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product by ID or OCS item number"""
        
        query = """
            SELECT *
            FROM products
            WHERE id = $1 OR ocs_item_number = $1
        """
        
        return await self.fetch_one(query, product_id)
    
    async def get_by_category(
        self,
        category: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get products by category"""
        
        query = """
            SELECT 
                id,
                ocs_item_number,
                product_name,
                brand,
                category,
                subcategory,
                thc_content,
                cbd_content,
                unit_price,
                effects,
                terpenes
            FROM products
            WHERE category ILIKE $1
            ORDER BY unit_price ASC
            LIMIT $2
        """
        
        return await self.fetch_many(query, f"%{category}%", limit)
    
    async def get_inventory(self, product_id: str) -> int:
        """Get current inventory level for product"""
        
        query = """
            SELECT quantity_available
            FROM inventory
            WHERE product_id = $1
        """
        
        result = await self.fetch_one(query, product_id)
        return result["quantity_available"] if result else 0
    
    async def get_similar_products(
        self,
        product_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get similar products based on characteristics"""
        
        # First get the reference product
        product = await self.get_by_id(product_id)
        
        if not product:
            return []
        
        # Find similar products based on category and THC/CBD levels
        query = """
            SELECT 
                id,
                ocs_item_number,
                product_name,
                brand,
                category,
                thc_content,
                cbd_content,
                unit_price,
                ABS(thc_content - $2) + ABS(cbd_content - $3) as similarity
            FROM products
            WHERE 
                category = $4
                AND id != $1
            ORDER BY similarity ASC
            LIMIT $5
        """
        
        return await self.fetch_many(
            query,
            product_id,
            product.get("thc_content", 0),
            product.get("cbd_content", 0),
            product["category"],
            limit
        )
    
    async def get_recommendations(
        self,
        customer_preferences: Dict[str, Any],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get product recommendations based on preferences"""
        
        conditions = []
        values = []
        param_count = 1
        
        # Build conditions based on preferences
        if "effects" in customer_preferences:
            effects = customer_preferences["effects"]
            if isinstance(effects, list):
                effects = ",".join(effects)
            conditions.append(f"effects @> ${param_count}")
            values.append(effects)
            param_count += 1
        
        if "max_thc" in customer_preferences:
            conditions.append(f"thc_content <= ${param_count}")
            values.append(customer_preferences["max_thc"])
            param_count += 1
        
        if "min_cbd" in customer_preferences:
            conditions.append(f"cbd_content >= ${param_count}")
            values.append(customer_preferences["min_cbd"])
            param_count += 1
        
        if "category" in customer_preferences:
            conditions.append(f"category = ${param_count}")
            values.append(customer_preferences["category"])
            param_count += 1
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT 
                id,
                ocs_item_number,
                product_name,
                brand,
                category,
                thc_content,
                cbd_content,
                unit_price,
                effects,
                terpenes
            FROM products
            WHERE {where_clause}
            ORDER BY unit_price ASC
            LIMIT ${param_count}
        """
        
        values.append(limit)
        
        return await self.fetch_many(query, *values)