"""Database-connected dispensary tool implementations"""

import asyncio
import asyncpg
import json
import logging
from typing import Dict, List, Optional, Any
from services.tools.base import ITool, ToolResult, SearchTool

logger = logging.getLogger(__name__)

class DispensarySearchToolDB(SearchTool):
    """Database-connected search tool for dispensary products"""
    
    def __init__(self, db_config: Dict[str, Any] = None):
        """Initialize with database configuration"""
        self.db_config = db_config or {}
        self.connection_string = self.db_config.get(
            'connection_string', 
            'postgresql://weedgo:your_password_here@localhost:5434/ai_engine'
        )
        self.pool = None
    
    async def _ensure_connection(self):
        """Ensure database connection pool is established"""
        if not self.pool:
            try:
                self.pool = await asyncpg.create_pool(
                    self.connection_string,
                    min_size=1,
                    max_size=5,
                    command_timeout=10
                )
                logger.info("Database connection pool established for DispensarySearchToolDB")
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                raise
    
    @property
    def name(self) -> str:
        return "search_products_db"
    
    @property
    def description(self) -> str:
        return "Search cannabis products in database by name, brand, category"
    
    @property
    def parameters(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for products (searches name, brand, categories)"
                },
                "brand": {
                    "type": "string",
                    "description": "Filter by specific brand name"
                },
                "category": {
                    "type": "string",
                    "description": "Filter by category"
                },
                "sub_category": {
                    "type": "string",
                    "description": "Filter by sub-category"
                },
                "strain_type": {
                    "type": "string",
                    "enum": ["Sativa", "Indica", "Hybrid", "CBD", "any"],
                    "description": "Filter by strain type"
                },
                "min_price": {
                    "type": "number",
                    "description": "Minimum price filter"
                },
                "max_price": {
                    "type": "number",
                    "description": "Maximum price filter"
                },
                "limit": {
                    "type": "integer",
                    "default": 10,
                    "description": "Maximum number of results"
                }
            },
            "required": ["query"]
        }
    
    async def execute(self, 
                     query: str,
                     brand: Optional[str] = None,
                     category: Optional[str] = None,
                     sub_category: Optional[str] = None,
                     strain_type: str = "any",
                     min_price: Optional[float] = None,
                     max_price: Optional[float] = None,
                     limit: int = 10,
                     **kwargs) -> ToolResult:
        """Execute database product search"""
        try:
            await self._ensure_connection()
            
            # Build dynamic SQL query
            sql_conditions = []
            params = []
            param_count = 0
            
            # Search across multiple fields if query is provided
            if query and query != "*":
                param_count += 1
                search_pattern = f"%{query}%"
                sql_conditions.append(f"""
                    (LOWER(name) LIKE LOWER(${param_count}) OR
                     LOWER(brand) LIKE LOWER(${param_count}) OR
                     LOWER(category) LIKE LOWER(${param_count}) OR
                     LOWER(sub_category) LIKE LOWER(${param_count}) OR
                     LOWER(sub_sub_category) LIKE LOWER(${param_count}))
                """)
                params.append(search_pattern)
            
            # Add brand filter
            if brand:
                param_count += 1
                sql_conditions.append(f"LOWER(brand) = LOWER(${param_count})")
                params.append(brand)
            
            # Add category filters
            if category:
                param_count += 1
                sql_conditions.append(f"LOWER(category) = LOWER(${param_count})")
                params.append(category)
            
            if sub_category:
                param_count += 1
                sql_conditions.append(f"LOWER(sub_category) = LOWER(${param_count})")
                params.append(sub_category)
            
            # Add strain type filter
            if strain_type and strain_type != "any":
                param_count += 1
                sql_conditions.append(f"strain_type = ${param_count}")
                params.append(strain_type)
            
            # Add price filters
            if min_price is not None:
                param_count += 1
                sql_conditions.append(f"unit_price >= ${param_count}")
                params.append(min_price)
            
            if max_price is not None:
                param_count += 1
                sql_conditions.append(f"unit_price <= ${param_count}")
                params.append(max_price)
            
            # Construct final query
            where_clause = " AND ".join(sql_conditions) if sql_conditions else "1=1"
            
            sql = f"""
                SELECT 
                    id,
                    name as product_name,
                    brand,
                    category,
                    sub_category,
                    sub_sub_category,
                    plant_type,
                    COALESCE(unit_price, 0) as unit_price,
                    plant_type as strain_type,
                    thc_min as thc_level,
                    cbd_min as cbd_level,
                    short_description as product_description,
                    COALESCE(inventory_quantity, 0) as inventory_quantity
                FROM cannabis_data.products
                WHERE {where_clause}
                ORDER BY name
                LIMIT {limit}
            """
            
            # Execute query
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(sql, *params)
            
            # Format results
            products = []
            for row in rows:
                product = {
                    "product_id": row['id'],
                    "name": row['product_name'],
                    "brand": row['brand'],
                    "category": row['category'],
                    "sub_category": row['sub_category'],
                    "sub_sub_category": row['sub_sub_category'],
                    "strain_type": row['strain_type'],
                    "plant_type": row['plant_type'],
                    "price": float(row['unit_price']) if row['unit_price'] else 0,
                    "thc_level": row['thc_level'],
                    "cbd_level": row['cbd_level'],
                    "description": row['product_description'],
                    "in_stock": row['inventory_quantity'] > 0 if row['inventory_quantity'] else False
                }
                products.append(product)
            
            return ToolResult(
                success=True,
                data=products,
                metadata={
                    "query": query,
                    "count": len(products),
                    "filters_applied": {
                        "brand": brand,
                        "category": category,
                        "sub_category": sub_category,
                        "strain_type": strain_type,
                        "price_range": f"${min_price or 0}-${max_price or 'unlimited'}"
                    }
                }
            )
            
        except asyncpg.exceptions.PostgresError as e:
            logger.error(f"Database query error: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=f"Database error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Search execution error: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=f"Search failed: {str(e)}"
            )
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Database connection pool closed")


class DispensaryStatsToolDB(ITool):
    """Database tool for getting dispensary statistics"""
    
    def __init__(self, db_config: Dict[str, Any] = None):
        """Initialize with database configuration"""
        self.db_config = db_config or {}
        self.connection_string = self.db_config.get(
            'connection_string',
            'postgresql://weedgo:weedgo@localhost:5434/ai_engine'
        )
        self.pool = None
    
    async def _ensure_connection(self):
        """Ensure database connection pool is established"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=1,
                max_size=5
            )
    
    @property
    def name(self) -> str:
        return "get_product_stats"
    
    @property  
    def description(self) -> str:
        return "Get statistics about products (counts by category, brands, etc.)"
    
    @property
    def parameters(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "stat_type": {
                    "type": "string",
                    "enum": ["category_counts", "brand_counts", "strain_distribution", "price_ranges"],
                    "description": "Type of statistics to retrieve"
                }
            },
            "required": ["stat_type"]
        }
    
    async def execute(self, stat_type: str, **kwargs) -> ToolResult:
        """Get product statistics from database"""
        try:
            await self._ensure_connection()
            
            if stat_type == "category_counts":
                sql = """
                    SELECT category, COUNT(*) as count
                    FROM products
                    GROUP BY category
                    ORDER BY count DESC
                """
            elif stat_type == "brand_counts":
                sql = """
                    SELECT brand, COUNT(*) as count
                    FROM products
                    WHERE brand IS NOT NULL
                    GROUP BY brand
                    ORDER BY count DESC
                    LIMIT 20
                """
            elif stat_type == "strain_distribution":
                sql = """
                    SELECT strain_type, COUNT(*) as count
                    FROM products
                    WHERE strain_type IS NOT NULL
                    GROUP BY strain_type
                    ORDER BY count DESC
                """
            elif stat_type == "price_ranges":
                sql = """
                    SELECT 
                        CASE 
                            WHEN unit_price < 20 THEN 'Under $20'
                            WHEN unit_price BETWEEN 20 AND 50 THEN '$20-$50'
                            WHEN unit_price BETWEEN 50 AND 100 THEN '$50-$100'
                            ELSE 'Over $100'
                        END as price_range,
                        COUNT(*) as count
                    FROM products
                    WHERE unit_price IS NOT NULL
                    GROUP BY price_range
                    ORDER BY 
                        CASE price_range
                            WHEN 'Under $20' THEN 1
                            WHEN '$20-$50' THEN 2
                            WHEN '$50-$100' THEN 3
                            ELSE 4
                        END
                """
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Unknown stat_type: {stat_type}"
                )
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(sql)
            
            stats = [dict(row) for row in rows]
            
            return ToolResult(
                success=True,
                data=stats,
                metadata={"stat_type": stat_type, "count": len(stats)}
            )
            
        except Exception as e:
            logger.error(f"Stats query error: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to get statistics: {str(e)}"
            )
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()