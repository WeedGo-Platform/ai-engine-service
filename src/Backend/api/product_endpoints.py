"""
Product API Endpoints
Provides product catalog functionality for e-commerce frontend
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Path
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
import logging
import asyncpg
import os
from decimal import Decimal

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/products", tags=["products"])

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


def convert_decimal_fields(product: Dict) -> Dict:
    """Convert Decimal fields to float for JSON serialization"""
    decimal_fields = [
        'unit_price', 'price',
        'thc_content', 'thc_min', 'cbd_content', 'cbd_min',
        'thc_content_per_unit', 'cbd_content_per_unit',
        'reorder_point', 'reorder_quantity'
    ]
    
    for field in decimal_fields:
        if product.get(field) is not None and isinstance(product.get(field), Decimal):
            product[field] = float(product[field])
    
    return product


# IMPORTANT: Specific routes must come before parameterized routes
@router.get("/featured")
async def get_featured_products(
    limit: int = Query(8, ge=1, le=50),
    conn = Depends(get_db_connection)
):
    """
    Get featured products
    """
    try:
        # Query for featured products (could be based on a featured flag, high ratings, or curated list)
        query = """
            SELECT 
                id,
                sku,
                name,
                brand,
                category,
                strain_type,
                thc_percentage as thc_content,
                cbd_percentage as cbd_content,
                price,
                short_description,
                image_url,
                quantity_available,
                CASE 
                    WHEN quantity_available > 0 THEN true
                    ELSE false
                END as in_stock
            FROM inventory_products_view
            WHERE quantity_available > 0
            ORDER BY RANDOM()  -- For now, random selection. In production, use featured flag
            LIMIT $1
        """
        
        rows = await conn.fetch(query, limit)
        products = [convert_decimal_fields(dict(row)) for row in rows]
        
        return products
        
    except Exception as e:
        logger.error(f"Error fetching featured products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bestsellers")
async def get_bestsellers(
    limit: int = Query(8, ge=1, le=50),
    conn = Depends(get_db_connection)
):
    """
    Get bestselling products
    """
    try:
        # Query for bestsellers (in production, join with sales data)
        query = """
            SELECT 
                id,
                sku,
                name,
                brand,
                category,
                strain_type,
                thc_percentage as thc_content,
                cbd_percentage as cbd_content,
                price,
                short_description,
                image_url,
                quantity_available,
                CASE 
                    WHEN quantity_available > 0 THEN true
                    ELSE false
                END as in_stock
            FROM inventory_products_view
            WHERE quantity_available > 0
            AND category IN ('Flower', 'Pre-Rolls')  -- Popular categories
            ORDER BY RANDOM()  -- In production, order by sales volume
            LIMIT $1
        """
        
        rows = await conn.fetch(query, limit)
        products = [convert_decimal_fields(dict(row)) for row in rows]
        
        return products
        
    except Exception as e:
        logger.error(f"Error fetching bestsellers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/new-arrivals")
async def get_new_arrivals(
    limit: int = Query(8, ge=1, le=50),
    conn = Depends(get_db_connection)
):
    """
    Get new arrival products
    """
    try:
        # Query for newest products
        query = """
            SELECT 
                id,
                sku,
                name,
                brand,
                category,
                strain_type,
                thc_percentage as thc_content,
                cbd_percentage as cbd_content,
                price,
                short_description,
                image_url,
                quantity_available,
                CASE 
                    WHEN quantity_available > 0 THEN true
                    ELSE false
                END as in_stock,
                created_at
            FROM inventory_products_view
            WHERE quantity_available > 0
            ORDER BY created_at DESC
            LIMIT $1
        """
        
        rows = await conn.fetch(query, limit)
        products = [convert_decimal_fields(dict(row)) for row in rows]
        
        return products
        
    except Exception as e:
        logger.error(f"Error fetching new arrivals: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def get_products_by_ids(
    ids: List[str],
    conn = Depends(get_db_connection)
):
    """
    Get multiple products by their IDs
    """
    try:
        if not ids:
            return []
        
        # Query for specific products
        query = """
            SELECT 
                id,
                sku,
                name,
                brand,
                category,
                strain_type,
                thc_percentage as thc_content,
                cbd_percentage as cbd_content,
                price,
                short_description,
                image_url,
                quantity_available,
                CASE 
                    WHEN quantity_available > 0 THEN true
                    ELSE false
                END as in_stock
            FROM inventory_products_view
            WHERE id::text = ANY($1::text[])
        """
        
        rows = await conn.fetch(query, ids)
        products = [convert_decimal_fields(dict(row)) for row in rows]
        
        return products
        
    except Exception as e:
        logger.error(f"Error fetching products by IDs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def get_products(
    category: Optional[str] = Query(None),
    subCategory: Optional[str] = Query(None),
    strainType: Optional[str] = Query(None),
    plantType: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    priceMin: Optional[float] = Query(None, ge=0),
    priceMax: Optional[float] = Query(None, ge=0),
    onSale: Optional[bool] = Query(None),
    inStock: Optional[bool] = Query(True),
    sortBy: str = Query("name"),
    sortOrder: str = Query("asc"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(24, ge=1, le=100),
    conn = Depends(get_db_connection)
):
    """
    Get paginated products with filters
    """
    try:
        # Build the query
        query = """
            SELECT 
                id,
                sku,
                name,
                brand,
                category,
                sub_category,
                strain_type,
                plant_type,
                thc_percentage as thc_content,
                cbd_percentage as cbd_content,
                price,
                short_description,
                image_url,
                quantity_available,
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
        if category:
            param_count += 1
            query += f" AND category ILIKE ${param_count}"
            params.append(f"%{category}%")
        
        if subCategory:
            param_count += 1
            query += f" AND sub_category ILIKE ${param_count}"
            params.append(f"%{subCategory}%")
        
        if strainType:
            param_count += 1
            query += f" AND strain_type ILIKE ${param_count}"
            params.append(f"%{strainType}%")
        
        if plantType:
            param_count += 1
            query += f" AND plant_type ILIKE ${param_count}"
            params.append(f"%{plantType}%")
        
        if search:
            param_count += 1
            query += f""" AND (
                name ILIKE ${param_count} OR 
                brand ILIKE ${param_count} OR
                description ILIKE ${param_count}
            )"""
            params.append(f"%{search}%")
        
        if priceMin is not None:
            param_count += 1
            query += f" AND price >= ${param_count}"
            params.append(priceMin)
        
        if priceMax is not None:
            param_count += 1
            query += f" AND price <= ${param_count}"
            params.append(priceMax)
        
        if inStock:
            query += " AND quantity_available > 0"
        
        # Count total items
        count_query = f"SELECT COUNT(*) FROM ({query}) as filtered"
        total = await conn.fetchval(count_query, *params)
        
        # Add sorting
        sort_field_map = {
            "name": "name",
            "price": "price",
            "category": "category",
            "newest": "created_at",
            "popular": "RANDOM()"  # In production, use sales data
        }
        
        sort_field = sort_field_map.get(sortBy, "name")
        sort_direction = "DESC" if sortOrder.lower() == "desc" else "ASC"
        query += f" ORDER BY {sort_field} {sort_direction}"
        
        # Add pagination
        offset = (page - 1) * pageSize
        param_count += 1
        query += f" LIMIT ${param_count}"
        params.append(pageSize)
        
        param_count += 1
        query += f" OFFSET ${param_count}"
        params.append(offset)
        
        # Execute query
        rows = await conn.fetch(query, *params)
        products = [convert_decimal_fields(dict(row)) for row in rows]
        
        # Calculate total pages
        total_pages = (total + pageSize - 1) // pageSize if total > 0 else 0
        
        return {
            "items": products,
            "total": total,
            "page": page,
            "pageSize": pageSize,
            "totalPages": total_pages
        }
        
    except Exception as e:
        logger.error(f"Error fetching products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# This route MUST be last because it matches any path
@router.get("/{id_or_slug}")
async def get_product_detail(
    id_or_slug: str = Path(..., description="Product ID or slug"),
    conn = Depends(get_db_connection)
):
    """
    Get single product details by ID or slug
    """
    try:
        # Try to find by ID first (if it's a valid UUID format)
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
                END as in_stock,
                created_at,
                updated_at
            FROM inventory_products_view
            WHERE id::text = $1 OR LOWER(REPLACE(name, ' ', '-')) = LOWER($1)
            LIMIT 1
        """
        
        row = await conn.fetchrow(query, id_or_slug)
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Product not found: {id_or_slug}")
        
        product = dict(row)
        product = convert_decimal_fields(product)
        
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product detail: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))