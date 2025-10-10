"""
Product Repository
Implements repository pattern for product data access
Following SOLID principles
"""

import logging
from typing import Dict, Any, List, Optional
from psycopg2.extras import RealDictCursor
from decimal import Decimal

logger = logging.getLogger(__name__)


class ProductRepository:
    """
    Repository for accessing product data
    Single Responsibility: Product data access abstraction
    """

    def __init__(self, connection_manager):
        """
        Initialize product repository with dependency injection

        Args:
            connection_manager: Database connection manager instance
        """
        self.connection_manager = connection_manager
        logger.info("ProductRepository initialized")

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
    ) -> List[Dict[str, Any]]:
        """
        Search for products with various filters

        Args:
            query: Text search query
            category: Product category
            strain_type: Cannabis strain type
            min_thc: Minimum THC percentage
            max_thc: Maximum THC percentage
            min_cbd: Minimum CBD percentage
            max_cbd: Maximum CBD percentage
            min_price: Minimum price
            max_price: Maximum price
            effects: List of desired effects
            limit: Maximum number of results

        Returns:
            List of product dictionaries
        """
        connection = None
        cursor = None

        try:
            # Get connection from pool
            connection = self.connection_manager.get_connection()
            cursor = connection.cursor(cursor_factory=RealDictCursor)

            # Build dynamic query
            where_clauses = []
            params = []

            # Text search
            if query:
                where_clauses.append("""(
                    COALESCE(cat.product_name, inv.product_name) ILIKE %s
                    OR cat.street_name ILIKE %s
                    OR cat.brand ILIKE %s
                    OR cat.category ILIKE %s
                    OR cat.sub_category ILIKE %s
                )""")
                search_term = f"%{query}%"
                params.extend([search_term] * 5)

            # Category filter
            if category:
                where_clauses.append("(cat.category ILIKE %s OR cat.sub_category ILIKE %s)")
                params.append(f"%{category}%")
                params.append(f"%{category}%")

            # Strain type filter (using plant_type column)
            if strain_type:
                where_clauses.append("cat.plant_type ILIKE %s")
                params.append(f"%{strain_type}%")

            # THC range
            if min_thc is not None:
                where_clauses.append("cat.thc_content_per_unit >= %s")
                params.append(min_thc)
            if max_thc is not None:
                where_clauses.append("cat.thc_content_per_unit <= %s")
                params.append(max_thc)

            # CBD range
            if min_cbd is not None:
                where_clauses.append("cat.cbd_content_per_unit >= %s")
                params.append(min_cbd)
            if max_cbd is not None:
                where_clauses.append("cat.cbd_content_per_unit <= %s")
                params.append(max_cbd)

            # Price range
            if min_price is not None:
                where_clauses.append("COALESCE(inv.retail_price, cat.unit_price) >= %s")
                params.append(min_price)
            if max_price is not None:
                where_clauses.append("COALESCE(inv.retail_price, cat.unit_price) <= %s")
                params.append(max_price)

            # Effects filter (terpenes search)
            if effects:
                effects_conditions = []
                for effect in effects:
                    effects_conditions.append("cat.terpenes ILIKE %s")
                    params.append(f"%{effect}%")
                if effects_conditions:
                    where_clauses.append(f"({' OR '.join(effects_conditions)})")

            # Build final query
            base_query = """
                SELECT DISTINCT
                    inv.id,
                    COALESCE(cat.product_name, inv.product_name) as name,
                    cat.brand,
                    cat.supplier_name,
                    cat.category,
                    cat.sub_category,
                    cat.sub_sub_category,
                    cat.plant_type,
                    cat.plant_type as strain_type,
                    cat.size,
                    cat.unit_of_measure,
                    COALESCE(inv.retail_price, cat.unit_price) as price,
                    cat.image_url,
                    cat.street_name as short_description,
                    cat.terpenes,
                    cat.thc_content_per_unit as thc_content,
                    cat.cbd_content_per_unit as cbd_content,
                    cat.ingredients,
                    cat.grow_method,
                    cat.grow_region,
                    cat.drying_method,
                    cat.trimming_method,
                    cat.extraction_process,
                    inv.quantity_available as inventory_count,
                    inv.is_available,
                    CASE
                        WHEN inv.quantity_available > 20 THEN 'In Stock'
                        WHEN inv.quantity_available > 0 THEN 'Low Stock'
                        ELSE 'Out of Stock'
                    END as stock_status,
                    inv.sku,
                    cat.ocs_variant_number,
                    cat.gtin
                FROM ocs_inventory inv
                LEFT JOIN ocs_product_catalog cat
                    ON LOWER(TRIM(inv.sku)) = LOWER(TRIM(cat.ocs_variant_number))
                WHERE inv.quantity_available > 0
                AND inv.is_available = true
            """

            if where_clauses:
                base_query += " AND " + " AND ".join(where_clauses)

            base_query += " ORDER BY quantity_available DESC, price ASC"
            base_query += f" LIMIT {limit}"

            # Execute query
            cursor.execute(base_query, params)
            products = cursor.fetchall()

            # Convert to list of dicts and handle Decimal types
            formatted_products = []
            for product in products:
                formatted_product = dict(product)
                # Convert Decimal to float for numeric fields
                numeric_fields = ['price', 'thc_content', 'cbd_content', 'inventory_count']
                for field in numeric_fields:
                    if formatted_product.get(field) is not None:
                        formatted_product[field] = float(formatted_product[field])
                formatted_products.append(formatted_product)

            return formatted_products

        except Exception as e:
            logger.error(f"Product search failed: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                self.connection_manager.release_connection(connection)

    def get_product_count(self) -> int:
        """
        Get total number of products in database

        Returns:
            Product count
        """
        connection = None
        cursor = None

        try:
            connection = self.connection_manager.get_connection()
            cursor = connection.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT COUNT(DISTINCT inv.id) as count
                FROM ocs_inventory inv
                WHERE inv.quantity_available > 0
                AND inv.is_available = true
            """)
            result = cursor.fetchone()
            return result['count'] if result else 0

        except Exception as e:
            logger.error(f"Failed to get product count: {e}")
            return 0
        finally:
            if cursor:
                cursor.close()
            if connection:
                self.connection_manager.release_connection(connection)

    def get_trending_products(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get trending products based on availability and popularity

        Args:
            limit: Maximum number of results

        Returns:
            List of trending products
        """
        connection = None
        cursor = None

        try:
            connection = self.connection_manager.get_connection()
            cursor = connection.cursor(cursor_factory=RealDictCursor)

            query = """
                SELECT DISTINCT
                    inv.id,
                    COALESCE(cat.product_name, inv.product_name) as name,
                    cat.brand,
                    cat.category,
                    cat.sub_category,
                    cat.plant_type as strain_type,
                    cat.thc_content_per_unit as thc_content,
                    cat.cbd_content_per_unit as cbd_content,
                    COALESCE(inv.retail_price, cat.unit_price) as price,
                    cat.image_url,
                    cat.size,
                    inv.quantity_available as inventory_count,
                    CASE
                        WHEN inv.quantity_available > 20 THEN 'In Stock'
                        WHEN inv.quantity_available > 0 THEN 'Low Stock'
                        ELSE 'Out of Stock'
                    END as stock_status
                FROM ocs_inventory inv
                LEFT JOIN ocs_product_catalog cat
                    ON LOWER(TRIM(inv.sku)) = LOWER(TRIM(cat.ocs_variant_number))
                WHERE inv.quantity_available > 10
                AND inv.is_available = true
                AND cat.product_name IS NOT NULL
                ORDER BY
                    inv.quantity_available DESC,
                    COALESCE(inv.retail_price, cat.unit_price) ASC
                LIMIT %s
            """

            cursor.execute(query, (limit,))
            products = cursor.fetchall()

            formatted_products = []
            for product in products:
                p_dict = dict(product)
                # Ensure numeric types are converted
                if p_dict.get('price'):
                    p_dict['price'] = float(p_dict['price'])
                if p_dict.get('thc_content'):
                    p_dict['thc_content'] = float(p_dict['thc_content'])
                if p_dict.get('cbd_content'):
                    p_dict['cbd_content'] = float(p_dict['cbd_content'])
                formatted_products.append(p_dict)

            return formatted_products

        except Exception as e:
            logger.error(f"Failed to get trending products: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                self.connection_manager.release_connection(connection)