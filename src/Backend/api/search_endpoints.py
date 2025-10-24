"""
Product Search API Endpoints
Provides search functionality for products with filters
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Header
from typing import List, Dict, Optional, Any
import logging
import asyncpg
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/search", tags=["search"])

# Database connection pool
db_pool = None

async def get_db_pool():
    """Get or create database connection pool"""
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5434)),
            database=os.getenv('DB_NAME', 'ai_engine'),
            user=os.getenv('DB_USER', 'weedgo'),
            password=os.getenv('DB_PASSWORD', 'your_password_here'),
            min_size=1,
            max_size=10
        )
    return db_pool


async def get_db_connection():
    """Get database connection from pool"""
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        yield connection


@router.get("/products")
async def search_products(
    q: Optional[str] = Query(None, description="Search query"),
    id: Optional[str] = Query(None, description="Product ID"),
    store_id: Optional[str] = Query(None, description="Store ID for inventory filtering"),
    x_store_id: Optional[str] = Header(None, alias="X-Store-ID", description="Store ID from header"),
    category: Optional[str] = Query(None, description="Product category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    in_stock: bool = Query(True, description="Only show in-stock items"),
    sort_by: str = Query("name", description="Sort field"),
    sort_order: str = Query("asc", description="Sort order (asc/desc)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    conn = Depends(get_db_connection)
):
    """
    Search products with various filters
    """
    # Use header if provided, otherwise fall back to query param
    effective_store_id = x_store_id or store_id

    try:
        # Parse GS1-128 barcode if present
        # GS1-128 format: (01)GTIN(13)DATE(10)BATCH
        original_barcode = q
        if q and q.startswith('01') and len(q) > 16:
            # Extract GTIN from GS1-128 barcode
            # Position 2-15 contains the 14-digit GTIN
            gtin = q[2:16]
            # Use the extracted GTIN for search
            q = gtin
            logger.info(f"Parsed GS1-128 barcode: {original_barcode}, extracted GTIN: {gtin}")

        # Build the query using catalog with optional inventory
        # This allows POS to see all products, not just those with inventory
        query = (
            "SELECT "
            "p.ocs_variant_number as id, "
            "p.ocs_variant_number as sku, "
            "p.product_name as name, "
            "p.brand, "
            "p.category, "
            "p.sub_category, "
            "p.sub_sub_category, "
            "p.plant_type, "
            "p.strain_type, "
            "p.pack_size as size, "
            "p.unit_of_measure, "
            "p.maximum_thc_content_percent as thc_content, "
            "p.minimum_thc_content_percent as thc_min, "
            "p.maximum_cbd_content_percent as cbd_content, "
            "p.minimum_cbd_content_percent as cbd_min, "
            "p.unit_price, "
            "COALESCE(i.retail_price, p.unit_price) as price, "
            "p.terpenes, "
            "p.ocs_item_number, "
            "p.ocs_variant_number, "
            "p.gtin, "
            "CASE "
            "WHEN i.quantity_available > 10 THEN 'in_stock' "
            "WHEN i.quantity_available > 0 THEN 'low_stock' "
            "ELSE 'out_of_stock' "
            "END as stock_status, "
            "COALESCE(i.quantity_on_hand, 0) as stock_quantity, "
            "COALESCE(i.quantity_available, 0) as available_quantity, "
            "COALESCE(i.quantity_reserved, 0) as quantity_reserved, "
            "i.reorder_point, "
            "i.reorder_quantity, "
            "CASE WHEN i.quantity_available > 0 THEN true ELSE false END as in_stock "
            "FROM ocs_product_catalog p "
            "LEFT JOIN ocs_inventory i ON p.ocs_variant_number = i.sku "
            "WHERE 1=1"
        )
        
        params = []
        param_count = 0
        
        # Add filters
        if id:
            param_count += 1
            query += f" AND p.ocs_variant_number = ${param_count}"
            params.append(id)
        
        if q:
            param_count += 1
            query += f""" AND (
                p.product_name ILIKE ${param_count} OR
                p.brand ILIKE ${param_count} OR
                p.category ILIKE ${param_count} OR
                p.ocs_variant_number ILIKE ${param_count} OR
                p.gtin ILIKE ${param_count} OR
                p.ocs_item_number ILIKE ${param_count} OR
                p.terpenes::text ILIKE ${param_count}
            )"""
            search_term = f"%{q}%"
            params.append(search_term)
        
        if category:
            param_count += 1
            query += f" AND p.category ILIKE ${param_count}"
            params.append(f"%{category}%")
        
        if min_price is not None:
            param_count += 1
            query += f" AND COALESCE(i.retail_price, p.unit_price) >= ${param_count}"
            params.append(min_price)
        
        if max_price is not None:
            param_count += 1
            query += f" AND COALESCE(i.retail_price, p.unit_price) <= ${param_count}"
            params.append(max_price)
        
        if in_stock:
            query += " AND i.quantity_available > 0"
        
        # Add sorting
        sort_field_map = {
            "name": "p.product_name",
            "price": "COALESCE(i.retail_price, p.unit_price)",
            "category": "p.category",
            "stock": "i.quantity_available",
            "thc": "p.maximum_thc_content_percent"
        }
        
        sort_field = sort_field_map.get(sort_by, "p.product_name")
        sort_direction = "DESC" if sort_order.lower() == "desc" else "ASC"
        query += f" ORDER BY {sort_field} {sort_direction}"
        
        # Add pagination
        param_count += 1
        query += f" LIMIT ${param_count}"
        params.append(limit)
        
        param_count += 1
        query += f" OFFSET ${param_count}"
        params.append(offset)
        
        # Execute query

        # Build the actual query with dynamic filters and batch information
        actual_query = f"""
            WITH product_batches AS (
                SELECT
                    LOWER(TRIM(bt.sku)) as sku,
                    bt.store_id,
                    json_agg(
                        json_build_object(
                            'batch_lot', bt.batch_lot,
                            'quantity_remaining', bt.quantity_remaining,
                            'case_gtin', bt.case_gtin,
                            'each_gtin', bt.each_gtin,
                            'packaged_on_date', bt.packaged_on_date,
                            'location_code', sl.location_code
                        ) ORDER BY bt.batch_lot
                    ) FILTER (WHERE bt.quantity_remaining > 0) as batches,
                    COUNT(bt.id) FILTER (WHERE bt.quantity_remaining > 0) as batch_count
                FROM batch_tracking bt
                LEFT JOIN shelf_locations sl ON bt.location_id = sl.id
                WHERE bt.is_active = true
                GROUP BY LOWER(TRIM(bt.sku)), bt.store_id
            )
            SELECT
                p.ocs_variant_number as id,
                p.ocs_variant_number as sku,
                p.slug,
                p.product_name as name,
                p.brand,
                p.category,
                p.sub_category,
                p.plant_type,
                p.strain_type,
                p.pack_size as size,
                p.image_url,
                p.gtin,
                p.ocs_item_number,
                COALESCE(MAX(i.retail_price), p.unit_price, 0) as price,
                p.unit_price,
                COALESCE(SUM(i.quantity_available), 0) as available_quantity,
                CASE WHEN SUM(i.quantity_available) > 0 THEN true ELSE false END as in_stock,
                CASE
                    WHEN SUM(i.quantity_available) > 10 THEN 'in_stock'
                    WHEN SUM(i.quantity_available) > 0 THEN 'low_stock'
                    ELSE 'out_of_stock'
                END as stock_status,
                p.maximum_thc_content_percent as thc_content,
                p.maximum_cbd_content_percent as cbd_content,
                COALESCE(MAX(pb.batch_count), 0) as batch_count,
                MAX(pb.batches::text)::json as batches
            FROM ocs_product_catalog p
            INNER JOIN ocs_inventory i ON LOWER(TRIM(i.sku)) = LOWER(TRIM(p.ocs_variant_number))
            LEFT JOIN product_batches pb ON pb.sku = LOWER(TRIM(p.ocs_variant_number))
                AND (pb.store_id = i.store_id OR pb.store_id IS NULL)
        """

        # Add WHERE clause with filters
        where_conditions = ["1=1"]
        actual_params = []
        param_counter = 0

        # Add store filter if provided
        if effective_store_id:
            param_counter += 1
            where_conditions.append(f"i.store_id = ${param_counter}")
            actual_params.append(effective_store_id)

        if q:
            param_counter += 1
            where_conditions.append(f"""(
                p.product_name ILIKE ${param_counter} OR
                p.brand ILIKE ${param_counter} OR
                p.category ILIKE ${param_counter} OR
                p.ocs_variant_number ILIKE ${param_counter} OR
                p.slug = ${param_counter + 1} OR
                COALESCE(p.gtin::TEXT, '') ILIKE ${param_counter} OR
                COALESCE(p.ocs_item_number::TEXT, '') ILIKE ${param_counter} OR
                EXISTS (
                    SELECT 1 FROM batch_tracking bt
                    WHERE UPPER(TRIM(bt.sku)) = UPPER(TRIM(p.ocs_variant_number))
                    AND (
                        COALESCE(bt.case_gtin, '') ILIKE ${param_counter} OR
                        COALESCE(bt.each_gtin, '') ILIKE ${param_counter} OR
                        COALESCE(bt.gtin_barcode, '') ILIKE ${param_counter}
                    )
                    AND bt.is_active = true
                    AND bt.quantity_remaining > 0
                )
            )""")
            # Always use wildcards for search except for exact slug match
            actual_params.append(f"%{q}%")
            param_counter += 1
            actual_params.append(q)  # Exact match for slug

        if id:
            param_counter += 1
            where_conditions.append(f"p.ocs_variant_number = ${param_counter}")
            actual_params.append(id)

        if category:
            param_counter += 1
            where_conditions.append(f"p.category ILIKE ${param_counter}")
            actual_params.append(f"%{category}%")

        if min_price is not None:
            param_counter += 1
            where_conditions.append(f"COALESCE(i.retail_price, p.unit_price) >= ${param_counter}")
            actual_params.append(min_price)

        if max_price is not None:
            param_counter += 1
            where_conditions.append(f"COALESCE(i.retail_price, p.unit_price) <= ${param_counter}")
            actual_params.append(max_price)

        if in_stock:
            where_conditions.append("i.quantity_available > 0")

        actual_query += " WHERE " + " AND ".join(where_conditions)

        # Add GROUP BY
        actual_query += """
            GROUP BY p.ocs_variant_number, p.slug, p.product_name, p.brand, p.category,
                     p.sub_category, p.plant_type, p.strain_type, p.pack_size, p.unit_price, p.image_url,
                     p.gtin, p.ocs_item_number,
                     p.maximum_thc_content_percent, p.maximum_cbd_content_percent
        """

        # Add sorting
        sort_field_map = {
            "name": "p.product_name",
            "price": "COALESCE(MAX(i.retail_price), p.unit_price)",
            "category": "p.category",
            "stock": "SUM(i.quantity_available)",
            "thc": "p.maximum_thc_content_percent"
        }

        sort_field = sort_field_map.get(sort_by, "p.product_name")
        sort_direction = "DESC" if sort_order.lower() == "desc" else "ASC"
        actual_query += f" ORDER BY {sort_field} {sort_direction}"

        # Add pagination
        param_counter += 1
        actual_query += f" LIMIT ${param_counter}"
        actual_params.append(limit)

        param_counter += 1
        actual_query += f" OFFSET ${param_counter}"
        actual_params.append(offset)

        try:
            logger.info(f"Executing search with params: {actual_params[:3]}")  # Log first 3 params
            rows = await conn.fetch(actual_query, *actual_params)
            logger.info(f"Search returned {len(rows)} products")
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            logger.error(f"Query was: {actual_query[:500]}")
            raise

        # Convert to list of dicts
        products = []
        for row in rows:
            product = dict(row)
            # Convert Decimal to float for JSON serialization
            decimal_fields = [
                'unit_price', 'price',
                'thc_content', 'thc_min', 'cbd_content', 'cbd_min',
                'reorder_point', 'reorder_quantity'
            ]
            
            for field in decimal_fields:
                if product.get(field) is not None:
                    product[field] = float(product[field])
            
            products.append(product)
        
        # Get total count for pagination - simplified count for unique products
        count_query = """
            SELECT COUNT(DISTINCT p.ocs_variant_number) as total
            FROM ocs_product_catalog p
            INNER JOIN ocs_inventory i ON LOWER(TRIM(i.sku)) = LOWER(TRIM(p.ocs_variant_number))
            WHERE 1=1
        """

        # Apply same filters for count
        count_params = []
        count_param_count = 0

        # Add store filter to count as well
        if effective_store_id:
            count_param_count += 1
            count_query += f" AND i.store_id = ${count_param_count}"
            count_params.append(effective_store_id)

        if q:
            count_param_count += 1
            count_query += f""" AND (
                p.product_name ILIKE ${count_param_count} OR
                p.brand ILIKE ${count_param_count} OR
                p.category ILIKE ${count_param_count} OR
                p.ocs_variant_number ILIKE ${count_param_count} OR
                COALESCE(p.gtin::TEXT, '') ILIKE ${count_param_count} OR
                COALESCE(p.ocs_item_number::TEXT, '') ILIKE ${count_param_count}
            )"""
            count_params.append(f"%{q}%")

        if id:
            count_param_count += 1
            count_query += f" AND p.ocs_variant_number = ${count_param_count}"
            count_params.append(id)

        if category:
            count_param_count += 1
            count_query += f" AND p.category ILIKE ${count_param_count}"
            count_params.append(f"%{category}%")

        if min_price is not None:
            count_param_count += 1
            count_query += f" AND COALESCE(i.retail_price, p.unit_price) >= ${count_param_count}"
            count_params.append(min_price)

        if max_price is not None:
            count_param_count += 1
            count_query += f" AND COALESCE(i.retail_price, p.unit_price) <= ${count_param_count}"
            count_params.append(max_price)

        if in_stock:
            count_query += " AND i.quantity_available > 0"

        total_count = await conn.fetchval(count_query, *count_params)
        
        return {
            "products": products,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "page": (offset // limit) + 1,
            "total_pages": ((total_count - 1) // limit) + 1 if total_count > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Error searching products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))