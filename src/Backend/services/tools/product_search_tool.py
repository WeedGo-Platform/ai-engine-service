"""
Product Search Tool - Bridges FunctionRegistry with actual database search
Provides comprehensive product search capabilities for the cannabis dispensary
"""

import json
import logging
from typing import Dict, Any, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import os

logger = logging.getLogger(__name__)

class ProductSearchTool:
    """Tool for searching cannabis products in the database"""
    
    def __init__(self):
        """Initialize the product search tool"""
        self.connection = None
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5434)),
            'database': os.getenv('DB_NAME', 'ai_engine'),
            'user': os.getenv('DB_USER', 'weedgo'),
            'password': os.getenv('DB_PASSWORD', 'weedgo')
        }
        self._connect()
        
    def _connect(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(
                **self.db_config,
                cursor_factory=RealDictCursor
            )
            logger.info("ProductSearchTool connected to database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            self.connection = None
    
    def _ensure_connection(self):
        """Ensure database connection is alive"""
        if not self.connection or self.connection.closed:
            self._connect()
            
    def search_products(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        strain_type: Optional[str] = None,
        min_thc: Optional[float] = None,
        max_thc: Optional[float] = None,
        min_cbd: Optional[float] = None,
        max_cbd: Optional[float] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        effects: Optional[List[str]] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Search for products with various filters
        
        Args:
            query: Text search query
            category: Product category (flower, edibles, concentrates, etc.)
            strain_type: Strain type (indica, sativa, hybrid)
            min_thc: Minimum THC percentage
            max_thc: Maximum THC percentage
            min_cbd: Minimum CBD percentage
            max_cbd: Maximum CBD percentage
            min_price: Minimum price
            max_price: Maximum price
            effects: List of desired effects
            limit: Maximum number of results
            
        Returns:
            Dictionary with search results
        """
        self._ensure_connection()
        
        if not self.connection:
            return {
                "success": False,
                "error": "Database connection not available",
                "products": []
            }
        
        try:
            # Build dynamic query
            where_clauses = []
            params = []
            
            # Text search
            if query:
                where_clauses.append("(name ILIKE %s OR description ILIKE %s OR brand ILIKE %s)")
                search_term = f"%{query}%"
                params.extend([search_term, search_term, search_term])
            
            # Category filter
            if category:
                where_clauses.append("category ILIKE %s")
                params.append(f"%{category}%")
            
            # Strain type filter
            if strain_type:
                where_clauses.append("strain_type ILIKE %s")
                params.append(f"%{strain_type}%")
            
            # THC range
            if min_thc is not None:
                where_clauses.append("thc_percentage >= %s")
                params.append(min_thc)
            if max_thc is not None:
                where_clauses.append("thc_percentage <= %s")
                params.append(max_thc)
            
            # CBD range
            if min_cbd is not None:
                where_clauses.append("cbd_percentage >= %s")
                params.append(min_cbd)
            if max_cbd is not None:
                where_clauses.append("cbd_percentage <= %s")
                params.append(max_cbd)
            
            # Price range
            if min_price is not None:
                where_clauses.append("price >= %s")
                params.append(min_price)
            if max_price is not None:
                where_clauses.append("price <= %s")
                params.append(max_price)
            
            # Effects filter (JSON search)
            if effects:
                effects_conditions = []
                for effect in effects:
                    effects_conditions.append("effects::text ILIKE %s")
                    params.append(f"%{effect}%")
                if effects_conditions:
                    where_clauses.append(f"({' OR '.join(effects_conditions)})")
            
            # Build final query using inventory_products_view
            base_query = """
                SELECT 
                    id,
                    name,
                    category,
                    strain_type,
                    thc_percentage as thc_content,
                    cbd_percentage as cbd_content,
                    price,
                    brand,
                    description,
                    effects,
                    flavors,
                    terpenes,
                    quantity_available as inventory_count,
                    stock_status,
                    location,
                    sku
                FROM inventory_products_view
                WHERE quantity_available > 0
            """
            
            if where_clauses:
                base_query += " AND " + " AND ".join(where_clauses)
            
            base_query += " ORDER BY quantity_available DESC, price ASC"
            base_query += f" LIMIT {limit}"
            
            # Execute query
            cursor = self.connection.cursor()
            cursor.execute(base_query, params)
            products = cursor.fetchall()
            cursor.close()
            
            # Format results
            formatted_products = []
            for product in products:
                formatted_product = dict(product)
                # Parse JSON fields
                if formatted_product.get('effects') and isinstance(formatted_product['effects'], str):
                    try:
                        formatted_product['effects'] = json.loads(formatted_product['effects'])
                    except:
                        pass
                if formatted_product.get('terpenes') and isinstance(formatted_product['terpenes'], str):
                    try:
                        formatted_product['terpenes'] = json.loads(formatted_product['terpenes'])
                    except:
                        pass
                formatted_products.append(formatted_product)
            
            return {
                "success": True,
                "count": len(formatted_products),
                "products": formatted_products,
                "filters_applied": {
                    "query": query,
                    "category": category,
                    "strain_type": strain_type,
                    "thc_range": [min_thc, max_thc] if min_thc or max_thc else None,
                    "cbd_range": [min_cbd, max_cbd] if min_cbd or max_cbd else None,
                    "price_range": [min_price, max_price] if min_price or max_price else None,
                    "effects": effects
                }
            }
            
        except Exception as e:
            logger.error(f"Product search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "products": []
            }
    
    def get_product_count(self) -> int:
        """Get total number of products in database"""
        self._ensure_connection()
        
        if not self.connection:
            return 0
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM inventory_products_view")
            result = cursor.fetchone()
            cursor.close()
            return result['count'] if result else 0
        except Exception as e:
            logger.error(f"Failed to get product count: {e}")
            return 0
    
    def get_trending_products(self, limit: int = 10) -> Dict[str, Any]:
        """Get trending products based on views and sales"""
        self._ensure_connection()
        
        if not self.connection:
            return {"success": False, "error": "Database connection not available", "products": []}
        
        try:
            cursor = self.connection.cursor()
            # Get top-rated and most reviewed products
            query = """
                SELECT 
                    id, name, category, strain_type, 
                    thc_content, cbd_content, price, brand,
                    rating, review_count, inventory_count
                FROM inventory_products_view
                WHERE in_stock = true
                ORDER BY 
                    rating DESC NULLS LAST,
                    review_count DESC NULLS LAST
                LIMIT %s
            """
            cursor.execute(query, (limit,))
            products = cursor.fetchall()
            cursor.close()
            
            return {
                "success": True,
                "count": len(products),
                "products": [dict(p) for p in products]
            }
        except Exception as e:
            logger.error(f"Failed to get trending products: {e}")
            return {"success": False, "error": str(e), "products": []}
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("ProductSearchTool database connection closed")