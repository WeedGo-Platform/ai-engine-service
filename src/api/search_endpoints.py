"""
Product Search API Endpoints
Provides search functionality for products with filters
"""

from fastapi import APIRouter, HTTPException, Query, Depends
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
    try:
        # Build the query using inventory_products_view
        query = """
            SELECT 
                id,
                sku,
                name,
                brand,
                supplier_name,
                category,
                sub_category,
                sub_sub_category,
                plant_type,
                strain_type,
                size,
                unit_of_measure,
                thc_percentage as thc_content,
                thc_min_percent as thc_min,
                cbd_percentage as cbd_content,
                cbd_min_percent as cbd_min,
                unit_price,
                price,
                short_description,
                description,
                long_description,
                image_url,
                street_name,
                terpenes,
                ocs_item_number,
                ocs_variant_number,
                gtin,
                colour,
                pack_size,
                thc_content_per_unit,
                cbd_content_per_unit,
                stock_status,
                pc_stock_status,
                pc_inventory_status,
                ingredients,
                grow_method,
                grow_region,
                drying_method,
                trimming_method,
                extraction_process,
                ontario_grown,
                craft,
                quantity_on_hand as stock_quantity,
                quantity_available as available_quantity,
                quantity_reserved,
                location,
                reorder_point,
                reorder_quantity,
                CASE 
                    WHEN quantity_available > 0 THEN true
                    ELSE false
                END as in_stock
            FROM inventory_products_view
            WHERE 1=1
        """
        
        params = []
        param_count = 0
        
        # Add filters
        if id:
            param_count += 1
            query += f" AND id = ${param_count}"
            params.append(id)
        
        if q:
            param_count += 1
            query += f""" AND (
                name ILIKE $%d OR 
                short_description ILIKE $%d OR 
                long_description ILIKE $%d OR
                brand ILIKE $%d OR
                terpenes::text ILIKE $%d
            )""" % (param_count, param_count, param_count, param_count, param_count)
            search_term = f"%{q}%"
            params.append(search_term)
        
        if category:
            param_count += 1
            query += f" AND category ILIKE ${param_count}"
            params.append(f"%{category}%")
        
        if min_price is not None:
            param_count += 1
            query += f" AND price >= ${param_count}"
            params.append(min_price)
        
        if max_price is not None:
            param_count += 1
            query += f" AND price <= ${param_count}"
            params.append(max_price)
        
        if in_stock:
            query += " AND quantity_available > 0"
        
        # Add sorting
        sort_field_map = {
            "name": "name",
            "price": "price",
            "category": "category",
            "stock": "quantity_available",
            "thc": "thc_percentage"
        }
        
        sort_field = sort_field_map.get(sort_by, "name")
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
        rows = await conn.fetch(query, *params)
        
        # Convert to list of dicts
        products = []
        for row in rows:
            product = dict(row)
            # Convert Decimal to float for JSON serialization
            decimal_fields = [
                'unit_price', 'price',
                'thc_content', 'thc_min', 'cbd_content', 'cbd_min',
                'thc_content_per_unit', 'cbd_content_per_unit',
                'reorder_point', 'reorder_quantity'
            ]
            
            for field in decimal_fields:
                if product.get(field) is not None:
                    product[field] = float(product[field])
            
            products.append(product)
        
        # Get total count for pagination
        count_query = """
            SELECT COUNT(*) as total
            FROM inventory_products_view
            WHERE 1=1
        """
        
        # Apply same filters for count
        count_params = []
        count_param_count = 0
        
        if id:
            count_param_count += 1
            count_query += f" AND id = ${count_param_count}"
            count_params.append(id)
        
        if q:
            count_param_count += 1
            count_query += f""" AND (
                name ILIKE $%d OR 
                short_description ILIKE $%d OR 
                long_description ILIKE $%d OR
                brand ILIKE $%d OR
                terpenes::text ILIKE $%d
            )""" % (count_param_count, count_param_count, count_param_count, count_param_count, count_param_count)
            count_params.append(search_term)
        
        if category:
            count_param_count += 1
            count_query += f" AND category ILIKE ${count_param_count}"
            count_params.append(f"%{category}%")
        
        if min_price is not None:
            count_param_count += 1
            count_query += f" AND price >= ${count_param_count}"
            count_params.append(min_price)
        
        if max_price is not None:
            count_param_count += 1
            count_query += f" AND price <= ${count_param_count}"
            count_params.append(max_price)
        
        if in_stock:
            count_query += " AND quantity_available > 0"
        
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