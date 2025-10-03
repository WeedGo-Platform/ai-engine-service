"""
Product API Endpoints
Provides product catalog functionality with variant support and frontend field mapping
Fixed: Using correct column names from inventory_products_view
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Path, Header
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
import logging
import asyncpg
import os
from decimal import Decimal
import json
from datetime import datetime
import random

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
            password=os.getenv('DB_PASSWORD', 'weedgo123'),
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
        'unit_price', 'price', 'retail_price',
        'thc_content', 'thc_min', 'cbd_content', 'cbd_min',
        'minimum_thc_content_percent', 'maximum_thc_content_percent',
        'minimum_cbd_content_percent', 'maximum_cbd_content_percent',
        'thc_content_per_unit', 'cbd_content_per_unit',
        'reorder_point', 'reorder_quantity'
    ]

    for field in decimal_fields:
        if product.get(field) is not None and isinstance(product.get(field), Decimal):
            product[field] = float(product[field])

    return product


def parse_terpenes(terpenes_value):
    """Safely parse terpenes JSON field"""
    if not terpenes_value:
        return None

    # If already a dict/list, return as is
    if isinstance(terpenes_value, (dict, list)):
        return terpenes_value

    # If it's a string, try to parse as JSON
    if isinstance(terpenes_value, str):
        # Skip empty strings or strings that are just whitespace
        terpenes_value = terpenes_value.strip()
        if not terpenes_value or terpenes_value == '':
            return None

        try:
            return json.loads(terpenes_value)
        except (json.JSONDecodeError, ValueError) as e:
            # If it fails to parse, log and return None
            logger.debug(f"Failed to parse terpenes JSON: {e}, value: {terpenes_value[:100]}")
            return None

    return None


def transform_product_for_frontend(product: Dict[str, Any], include_variants: bool = False) -> Dict[str, Any]:
    """Transform backend product data to match frontend expectations"""

    # Handle decimal conversions
    def convert_decimal(value):
        if value is None:
            return None
        if isinstance(value, Decimal):
            return float(value)
        return value

    # Build images array - return as simple array of URL strings
    # Frontend expects array of strings, not objects
    images = []
    if product.get('image_url'):
        images = [product['image_url']]  # Simple array of URL strings

    # Calculate price fields
    base_price = convert_decimal(product.get('unit_price', 0))
    retail_price = convert_decimal(product.get('retail_price', base_price))

    # Determine if on sale (if retail price is less than base price)
    on_sale = retail_price < base_price if base_price and retail_price else False

    # Build sizes array from variants if available
    sizes = []
    if include_variants and 'variants' in product:
        for variant in product['variants']:
            sizes.append({
                'id': variant.get('ocs_variant_number'),
                'name': variant.get('size', ''),
                'price': convert_decimal(variant.get('unit_price', 0)),
                'inStock': variant.get('in_stock', False)
            })
    elif product.get('size'):
        sizes.append({
            'id': product.get('ocs_variant_number'),
            'name': product.get('size'),
            'price': retail_price,
            'inStock': product.get('in_stock', False)
        })

    # Transform to frontend expected format
    transformed = {
        # IDs
        'id': product.get('ocs_variant_number', product.get('product_id')),
        'sku': product.get('ocs_variant_number'),
        'slug': product.get('slug', '').lower().replace(' ', '-') if product.get('slug') else
                (product.get('product_name', '').lower().replace(' ', '-').replace('/', '-')),

        # Basic info
        'name': product.get('product_name'),
        'brand': product.get('brand'),
        'description': product.get('product_short_description', ''),
        'longDescription': product.get('product_long_description', ''),

        # Categories
        'category': product.get('category'),
        'subCategory': product.get('sub_category'),
        'subSubCategory': product.get('sub_sub_category'),

        # Cannabis specific - map plant_type to strainType for frontend
        'strainType': product.get('plant_type'),  # Frontend expects strainType
        'plantType': product.get('plant_type'),   # Also include plantType
        'strain': product.get('strain_type'),

        # Images
        'images': images,
        'image': product.get('image_url'),  # Single image for backwards compatibility

        # Sizes/Variants
        'sizes': sizes,
        'size': product.get('size'),

        # Pricing
        'price': retail_price,
        'basePrice': base_price,
        'compareAtPrice': base_price if on_sale else None,
        'onSale': on_sale,

        # THC/CBD Content
        'thcContent': {
            'min': convert_decimal(product.get('minimum_thc_content_percent', 0)),
            'max': convert_decimal(product.get('maximum_thc_content_percent', 0)),
            'display': f"{convert_decimal(product.get('minimum_thc_content_percent', 0))}-{convert_decimal(product.get('maximum_thc_content_percent', 0))}%"
        },
        'cbdContent': {
            'min': convert_decimal(product.get('minimum_cbd_content_percent', 0)),
            'max': convert_decimal(product.get('maximum_cbd_content_percent', 0)),
            'display': f"{convert_decimal(product.get('minimum_cbd_content_percent', 0))}-{convert_decimal(product.get('maximum_cbd_content_percent', 0))}%"
        },

        # Inventory
        'inStock': product.get('in_stock', False),
        'stockStatus': product.get('stock_status', 'out_of_stock'),
        'quantity': product.get('quantity_available', 0),

        # Ratings from product_ratings table (real data only - no dummy values)
        'rating': float(product.get('average_rating')) if product.get('average_rating') else 0,
        'reviewCount': int(product.get('total_reviews')) if product.get('total_reviews') else 0,

        # Flags
        'featured': product.get('featured', False),
        'bestseller': product.get('bestseller', False),
        'newArrival': product.get('new_arrival', False),

        # Tags (extract from categories and attributes)
        'tags': [],

        # Additional fields
        'terpenes': parse_terpenes(product.get('terpenes')),
        'ocsItemNumber': product.get('ocs_item_number'),
        'ocsVariantNumber': product.get('ocs_variant_number'),
        'gtin': str(product.get('gtin')) if product.get('gtin') else None,
    }

    # Build tags from various attributes
    tags = []
    if product.get('category'):
        tags.append(product['category'])
    if product.get('plant_type'):
        tags.append(product['plant_type'])
    if product.get('strain_type'):
        tags.append(product['strain_type'])
    if on_sale:
        tags.append('sale')
    if product.get('in_stock'):
        tags.append('in-stock')
    transformed['tags'] = tags

    return transformed


# Add alternative search endpoint for SearchBar component
@router.get("/categories")
async def get_categories(
    store_id: Optional[str] = Query(None),
    x_store_id: Optional[str] = Header(None, alias="X-Store-ID"),
    conn = Depends(get_db_connection)
):
    """
    Get all distinct product categories from the database
    Used by entity extractor for dynamic category mapping
    """
    effective_store_id = x_store_id or store_id

    try:
        query = """
            SELECT DISTINCT p.category
            FROM inventory_products_view p
            LEFT JOIN ocs_inventory i ON UPPER(p.ocs_variant_number) = UPPER(i.sku)
            WHERE p.category IS NOT NULL
            AND p.category != ''
        """

        params = []
        if effective_store_id:
            query += " AND (i.store_id = $1 OR i.store_id IS NULL)"
            params.append(effective_store_id)

        query += " ORDER BY p.category"

        rows = await conn.fetch(query, *params)
        categories = [row['category'] for row in rows]

        return {
            'categories': categories,
            'count': len(categories)
        }

    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sub-categories")
async def get_sub_categories(
    category: Optional[str] = Query(None, description="Filter by parent category"),
    store_id: Optional[str] = Query(None),
    x_store_id: Optional[str] = Header(None, alias="X-Store-ID"),
    conn = Depends(get_db_connection)
):
    """
    Get all distinct product subcategories from the database
    Optionally filter by parent category
    Used by entity extractor for dynamic subcategory mapping
    """
    effective_store_id = x_store_id or store_id

    try:
        query = """
            SELECT DISTINCT p.sub_category, p.category
            FROM inventory_products_view p
            LEFT JOIN ocs_inventory i ON UPPER(p.ocs_variant_number) = UPPER(i.sku)
            WHERE p.sub_category IS NOT NULL
            AND p.sub_category != ''
        """

        params = []
        param_count = 0

        if category:
            param_count += 1
            query += f" AND LOWER(p.category) = LOWER(${param_count})"
            params.append(category)

        if effective_store_id:
            param_count += 1
            query += f" AND (i.store_id = ${param_count} OR i.store_id IS NULL)"
            params.append(effective_store_id)

        query += " ORDER BY p.category, p.sub_category"

        rows = await conn.fetch(query, *params)

        # Return as array of objects with category context
        subcategories = [
            {
                'name': row['sub_category'],
                'category': row['category']
            }
            for row in rows
        ]

        return {
            'subcategories': subcategories,
            'count': len(subcategories)
        }

    except Exception as e:
        logger.error(f"Error fetching subcategories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_products_alt(
    q: str = Query("", description="Search query (optional)"),
    limit: int = Query(10, ge=1, le=50),
    store_id: Optional[str] = Query(None),
    x_store_id: Optional[str] = Header(None, alias="X-Store-ID"),
    conn = Depends(get_db_connection)
):
    """Alternative search endpoint for SearchBar component"""
    # Use header if provided, otherwise fall back to query param
    effective_store_id = x_store_id or store_id
    try:
        # Base query
        if q and q.strip():
            # Search with query
            query = """
                SELECT DISTINCT ON (p.ocs_item_number)
                    p.*,
                    i.quantity_available,
                    i.retail_price,
                    CASE WHEN i.quantity_available > 0 THEN true ELSE false END as in_stock
                FROM inventory_products_view p
                LEFT JOIN ocs_inventory i ON UPPER(p.ocs_variant_number) = UPPER(i.sku)
                WHERE (
                    p.product_name ILIKE $1 OR
                    p.brand ILIKE $1 OR
                    p.category ILIKE $1 OR
                    p.ocs_variant_number ILIKE $1
                )
            """
            params = [f"%{q}%"]
            param_count = 1
        else:
            # Return all products if no query
            query = """
                SELECT DISTINCT ON (p.ocs_item_number)
                    p.*,
                    i.quantity_available,
                    i.retail_price,
                    CASE WHEN i.quantity_available > 0 THEN true ELSE false END as in_stock
                FROM inventory_products_view p
                LEFT JOIN ocs_inventory i ON UPPER(p.ocs_variant_number) = UPPER(i.sku)
                WHERE 1=1
            """
            params = []
            param_count = 0

        if store_id:
            param_count += 1
            query += f" AND i.store_id = ${param_count}"
            params.append(store_id)

        query += f" ORDER BY p.ocs_item_number, p.product_name LIMIT {limit}"

        rows = await conn.fetch(query, *params)

        products = []
        for row in rows:
            product = convert_decimal_fields(dict(row))
            products.append(transform_product_for_frontend(product))

        return {
            'results': products
        }

    except Exception as e:
        logger.error(f"Error searching products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# IMPORTANT: Specific routes must come before parameterized routes
@router.get("/featured")
async def get_featured_products(
    limit: int = Query(8, ge=1, le=50),
    store_id: Optional[str] = Query(None),
    x_store_id: Optional[str] = Header(None, alias="X-Store-ID"),
    conn = Depends(get_db_connection)
):
    """Get featured products"""
    # Use header if provided, otherwise fall back to query param
    effective_store_id = x_store_id or store_id

    try:
        # For now, return random products as featured
        # In production, would have a featured flag in database
        query = """
            SELECT DISTINCT ON (p.ocs_item_number)
                p.*,
                i.quantity_available,
                i.retail_price,
                CASE WHEN i.quantity_available > 0 THEN true ELSE false END as in_stock,
                CASE
                    WHEN i.quantity_available > 10 THEN 'in_stock'
                    WHEN i.quantity_available > 0 THEN 'low_stock'
                    ELSE 'out_of_stock'
                END as stock_status
            FROM inventory_products_view p
            LEFT JOIN ocs_inventory i ON UPPER(p.ocs_variant_number) = UPPER(i.sku)
            WHERE i.quantity_available > 0
        """

        params = []
        if effective_store_id:
            query += " AND i.store_id = $1"
            params.append(effective_store_id)

        query += f" ORDER BY p.ocs_item_number, RANDOM() LIMIT {limit}"

        rows = await conn.fetch(query, *params)

        products = []
        for row in rows:
            product = convert_decimal_fields(dict(row))
            product['featured'] = True
            products.append(transform_product_for_frontend(product))

        return products

    except Exception as e:
        logger.error(f"Error fetching featured products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bestsellers")
async def get_bestsellers(
    limit: int = Query(8, ge=1, le=50),
    store_id: Optional[str] = Query(None),
    x_store_id: Optional[str] = Header(None, alias="X-Store-ID"),
    conn = Depends(get_db_connection)
):
    """Get bestselling products"""
    # Use header if provided, otherwise fall back to query param
    effective_store_id = x_store_id or store_id

    try:
        # For now, return products with low stock as "bestsellers"
        # In production, would track actual sales
        query = """
            SELECT DISTINCT ON (p.ocs_item_number)
                p.*,
                i.quantity_available,
                i.retail_price,
                CASE WHEN i.quantity_available > 0 THEN true ELSE false END as in_stock,
                CASE
                    WHEN i.quantity_available > 10 THEN 'in_stock'
                    WHEN i.quantity_available > 0 THEN 'low_stock'
                    ELSE 'out_of_stock'
                END as stock_status
            FROM inventory_products_view p
            LEFT JOIN ocs_inventory i ON UPPER(p.ocs_variant_number) = UPPER(i.sku)
            WHERE i.quantity_available BETWEEN 1 AND 20
        """

        params = []
        if effective_store_id:
            query += " AND i.store_id = $1"
            params.append(effective_store_id)

        query += f" ORDER BY p.ocs_item_number, i.quantity_available ASC LIMIT {limit}"

        rows = await conn.fetch(query, *params)

        products = []
        for row in rows:
            product = convert_decimal_fields(dict(row))
            product['bestseller'] = True
            products.append(transform_product_for_frontend(product))

        return products

    except Exception as e:
        logger.error(f"Error fetching bestsellers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/new-arrivals")
async def get_new_arrivals(
    limit: int = Query(8, ge=1, le=50),
    store_id: Optional[str] = Query(None),
    x_store_id: Optional[str] = Header(None, alias="X-Store-ID"),
    conn = Depends(get_db_connection)
):
    """Get new arrival products"""
    # Use header if provided, otherwise fall back to query param
    effective_store_id = x_store_id or store_id

    try:
        query = """
            SELECT DISTINCT ON (p.ocs_item_number)
                p.*,
                i.quantity_available,
                i.retail_price,
                CASE WHEN i.quantity_available > 0 THEN true ELSE false END as in_stock,
                CASE
                    WHEN i.quantity_available > 10 THEN 'in_stock'
                    WHEN i.quantity_available > 0 THEN 'low_stock'
                    ELSE 'out_of_stock'
                END as stock_status
            FROM inventory_products_view p
            LEFT JOIN ocs_inventory i ON UPPER(p.ocs_variant_number) = UPPER(i.sku)
            WHERE i.quantity_available > 0
        """

        params = []
        if effective_store_id:
            query += " AND i.store_id = $1"
            params.append(effective_store_id)

        # Order by creation date (newest first)
        query += f" ORDER BY p.ocs_item_number, p.product_created_at DESC NULLS LAST LIMIT {limit}"

        rows = await conn.fetch(query, *params)

        products = []
        for row in rows:
            product = convert_decimal_fields(dict(row))
            product['new_arrival'] = True
            products.append(transform_product_for_frontend(product))

        return products

    except Exception as e:
        logger.error(f"Error fetching new arrivals: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommended")
async def get_recommended_products(
    based_on: Optional[str] = Query(None, description="Product ID to base recommendations on"),
    limit: int = Query(8, ge=1, le=50),
    store_id: Optional[str] = Query(None),
    x_store_id: Optional[str] = Header(None, alias="X-Store-ID"),
    conn = Depends(get_db_connection)
):
    """Get recommended products"""
    # Use header if provided, otherwise fall back to query param
    effective_store_id = x_store_id or store_id

    try:
        if based_on:
            # Get the product's category to find similar items
            base_product = await conn.fetchrow(
                "SELECT category, sub_category, plant_type FROM inventory_products_view WHERE ocs_variant_number = $1",
                based_on
            )

            if base_product:
                query = """
                    SELECT DISTINCT ON (p.ocs_item_number)
                        p.*,
                        i.quantity_available,
                        i.retail_price,
                        CASE WHEN i.quantity_available > 0 THEN true ELSE false END as in_stock
                    FROM inventory_products_view p
                    LEFT JOIN ocs_inventory i ON UPPER(p.ocs_variant_number) = UPPER(i.sku)
                    WHERE p.ocs_variant_number != $1
                    AND i.quantity_available > 0
                    AND (p.category = $2 OR p.sub_category = $3 OR p.plant_type = $4)
                """

                params = [
                    based_on,
                    base_product['category'],
                    base_product['sub_category'],
                    base_product['plant_type']
                ]

                if effective_store_id:
                    query += " AND i.store_id = $5"
                    params.append(effective_store_id)

                query += f" ORDER BY p.ocs_item_number, RANDOM() LIMIT {limit}"
            else:
                # Fallback to random recommendations
                query = """
                    SELECT DISTINCT ON (p.ocs_item_number)
                        p.*,
                        i.quantity_available,
                        i.retail_price,
                        CASE WHEN i.quantity_available > 0 THEN true ELSE false END as in_stock
                    FROM inventory_products_view p
                    LEFT JOIN ocs_inventory i ON UPPER(p.ocs_variant_number) = UPPER(i.sku)
                    WHERE i.quantity_available > 0
                """

                params = []
                if effective_store_id:
                    query += " AND i.store_id = $1"
                    params.append(effective_store_id)

                query += f" ORDER BY p.ocs_item_number, RANDOM() LIMIT {limit}"
        else:
            # General recommendations
            query = """
                SELECT DISTINCT ON (p.ocs_item_number)
                    p.*,
                    i.quantity_available,
                    i.retail_price,
                    CASE WHEN i.quantity_available > 0 THEN true ELSE false END as in_stock
                FROM inventory_products_view p
                LEFT JOIN ocs_inventory i ON UPPER(p.ocs_variant_number) = UPPER(i.sku)
                WHERE i.quantity_available > 0
            """

            params = []
            if effective_store_id:
                query += " AND i.store_id = $1"
                params.append(effective_store_id)

            query += f" ORDER BY p.ocs_item_number, RANDOM() LIMIT {limit}"

        rows = await conn.fetch(query, *params)

        products = []
        for row in rows:
            product = convert_decimal_fields(dict(row))
            products.append(transform_product_for_frontend(product))

        return products

    except Exception as e:
        logger.error(f"Error fetching recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending")
async def get_trending_products(
    limit: int = Query(12, ge=1, le=50),
    store_id: Optional[str] = Query(None),
    x_store_id: Optional[str] = Header(None, alias="X-Store-ID"),
    conn = Depends(get_db_connection)
):
    """Get trending products"""
    # Use header if provided, otherwise fall back to query param
    effective_store_id = x_store_id or store_id

    try:
        # For demo, return products with medium stock levels
        # In production, would track view/purchase velocity
        query = """
            SELECT DISTINCT ON (p.ocs_item_number)
                p.*,
                i.quantity_available,
                i.retail_price,
                CASE WHEN i.quantity_available > 0 THEN true ELSE false END as in_stock
            FROM inventory_products_view p
            LEFT JOIN ocs_inventory i ON UPPER(p.ocs_variant_number) = UPPER(i.sku)
            WHERE i.quantity_available BETWEEN 5 AND 50
        """

        params = []
        if effective_store_id:
            query += " AND i.store_id = $1"
            params.append(effective_store_id)

        query += f" ORDER BY p.ocs_item_number, i.quantity_available DESC LIMIT {limit}"

        rows = await conn.fetch(query, *params)

        products = []
        for row in rows:
            product = convert_decimal_fields(dict(row))
            products.append(transform_product_for_frontend(product))

        return products

    except Exception as e:
        logger.error(f"Error fetching trending products: {str(e)}")
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
                p.ocs_variant_number,
                p.ocs_variant_number as sku,
                p.product_name as name,
                p.brand,
                p.category,
                p.plant_type,
                p.strain_type,
                p.maximum_thc_content_percent as thc_content,
                p.maximum_cbd_content_percent as cbd_content,
                COALESCE(i.retail_price, p.unit_price) as price,
                p.product_short_description as short_description,
                p.image_url,
                i.quantity_available,
                CASE
                    WHEN i.quantity_available > 0 THEN true
                    ELSE false
                END as in_stock,
                COALESCE(pr.average_rating, 0) as average_rating,
                COALESCE(pr.total_reviews, 0) as total_reviews
            FROM inventory_products_view p
            LEFT JOIN ocs_inventory i ON UPPER(p.ocs_variant_number) = UPPER(i.sku)
            LEFT JOIN product_ratings pr ON UPPER(p.ocs_variant_number) = UPPER(pr.sku)
            WHERE p.ocs_variant_number = ANY($1::text[])
        """
        
        rows = await conn.fetch(query, ids)
        products = []
        for row in rows:
            product = convert_decimal_fields(dict(row))
            products.append(transform_product_for_frontend(product))

        return products
        
    except Exception as e:
        logger.error(f"Error fetching products by IDs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def get_products(
    # Filters
    category: Optional[str] = Query(None),
    subCategory: Optional[str] = Query(None),
    strainType: Optional[str] = Query(None),  # Maps to plant_type in DB
    plantType: Optional[str] = Query(None),   # Also accept plantType
    search: Optional[str] = Query(None),
    priceMin: Optional[float] = Query(None, ge=0),
    priceMax: Optional[float] = Query(None, ge=0),
    onSale: Optional[bool] = Query(None),
    inStock: Optional[bool] = Query(True),
    featured: Optional[bool] = Query(None),
    bestseller: Optional[bool] = Query(None),
    newArrival: Optional[bool] = Query(None),
    # Sorting
    sortBy: Optional[str] = Query('name'),
    sortOrder: Optional[str] = Query('asc'),
    # Pagination
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    # Store context
    store_id: Optional[str] = Query(None),
    x_store_id: Optional[str] = Header(None, alias="X-Store-ID"),
    conn = Depends(get_db_connection)
):
    """Get paginated products with filters"""
    # Use header if provided, otherwise fall back to query param
    effective_store_id = x_store_id or store_id

    try:
        offset = (page - 1) * pageSize

        # Build query
        query = """
            SELECT DISTINCT ON (p.ocs_item_number)
                p.*,
                i.quantity_available,
                i.quantity_on_hand,
                i.retail_price,
                CASE WHEN i.quantity_available > 0 THEN true ELSE false END as in_stock,
                CASE
                    WHEN i.quantity_available > 10 THEN 'in_stock'
                    WHEN i.quantity_available > 0 THEN 'low_stock'
                    ELSE 'out_of_stock'
                END as stock_status,
                COALESCE(pr.average_rating, 0) as average_rating,
                COALESCE(pr.total_reviews, 0) as total_reviews
            FROM inventory_products_view p
            LEFT JOIN ocs_inventory i ON UPPER(p.ocs_variant_number) = UPPER(i.sku)
            LEFT JOIN product_ratings pr ON UPPER(p.ocs_variant_number) = UPPER(pr.sku)
            WHERE 1=1
        """

        params = []
        param_count = 0

        # Apply filters
        if effective_store_id:
            param_count += 1
            query += f" AND (i.store_id = ${param_count} OR i.store_id IS NULL)"
            params.append(effective_store_id)

        if category:
            param_count += 1
            query += f" AND LOWER(p.category) = LOWER(${param_count})"
            params.append(category)

        if subCategory:
            param_count += 1
            query += f" AND LOWER(p.sub_category) = LOWER(${param_count})"
            params.append(subCategory)

        # Handle strainType/plantType (frontend sends strainType, DB has plant_type)
        plant_type_filter = strainType or plantType
        if plant_type_filter:
            param_count += 1
            query += f" AND p.plant_type ILIKE ${param_count}"
            params.append(f"%{plant_type_filter}%")

        if search:
            param_count += 1
            query += f""" AND (
                p.product_name ILIKE ${param_count} OR
                p.brand ILIKE ${param_count} OR
                p.category ILIKE ${param_count} OR
                p.ocs_variant_number ILIKE ${param_count}
            )"""
            params.append(f"%{search}%")

        if priceMin is not None:
            param_count += 1
            query += f" AND COALESCE(i.retail_price, p.unit_price) >= ${param_count}"
            params.append(priceMin)

        if priceMax is not None:
            param_count += 1
            query += f" AND COALESCE(i.retail_price, p.unit_price) <= ${param_count}"
            params.append(priceMax)

        if inStock:
            query += " AND i.quantity_available > 0"

        # Filter out products with invalid THC/CBD content (0.0 or null means incomplete data)
        # Cannabis products should have valid THC or CBD content
        query += """ AND (
            (p.thc_content_per_unit > 0 OR p.cbd_content_per_unit > 0) OR
            (p.minimum_thc_content_percent > 0 OR p.minimum_cbd_content_percent > 0)
        )"""

        # Mock featured/bestseller/newArrival flags for now
        # In production, these would be actual database fields

        # Sorting
        sort_map = {
            'name': 'p.product_name',
            'price': 'COALESCE(i.retail_price, p.unit_price)',
            'price-asc': 'COALESCE(i.retail_price, p.unit_price)',
            'price-desc': 'COALESCE(i.retail_price, p.unit_price)',
            'newest': 'p.product_created_at',
            'popular': 'p.product_name',  # Would be sales/view count in production
            'rating': 'p.product_name',   # Would be actual rating in production
            'thc-high': 'p.maximum_thc_content_percent',
            'thc-low': 'p.minimum_thc_content_percent'
        }

        # Handle sortBy with embedded direction
        if sortBy in ['price-asc', 'price-desc']:
            sort_field = sort_map.get(sortBy, 'p.product_name')
            sort_direction = 'ASC' if sortBy == 'price-asc' else 'DESC'
        else:
            sort_field = sort_map.get(sortBy, 'p.product_name')
            sort_direction = 'DESC' if sortOrder == 'desc' else 'ASC'

        # Order by OCS item number first for DISTINCT ON, then our sort
        query += f" ORDER BY p.ocs_item_number, {sort_field} {sort_direction}"

        # Get total count before pagination
        count_query = f"""
            SELECT COUNT(DISTINCT p.ocs_item_number)
            FROM inventory_products_view p
            LEFT JOIN ocs_inventory i ON UPPER(p.ocs_variant_number) = UPPER(i.sku)
            WHERE 1=1
        """

        # Apply same filters to count
        count_params = []
        if effective_store_id:
            count_query += f" AND (i.store_id = $1 OR i.store_id IS NULL)"
            count_params.append(effective_store_id)
        if category:
            count_query += f" AND LOWER(p.category) = LOWER(${len(count_params)+1})"
            count_params.append(category)
        if subCategory:
            count_query += f" AND LOWER(p.sub_category) = LOWER(${len(count_params)+1})"
            count_params.append(subCategory)
        if plant_type_filter:
            count_query += f" AND p.plant_type ILIKE ${len(count_params)+1}"
            count_params.append(f"%{plant_type_filter}%")
        if search:
            count_query += f""" AND (
                p.product_name ILIKE ${len(count_params)+1} OR
                p.brand ILIKE ${len(count_params)+1} OR
                p.category ILIKE ${len(count_params)+1}
            )"""
            count_params.append(f"%{search}%")
        if priceMin is not None:
            count_query += f" AND COALESCE(i.retail_price, p.unit_price) >= ${len(count_params)+1}"
            count_params.append(priceMin)
        if priceMax is not None:
            count_query += f" AND COALESCE(i.retail_price, p.unit_price) <= ${len(count_params)+1}"
            count_params.append(priceMax)
        if inStock:
            count_query += " AND i.quantity_available > 0"

        total = await conn.fetchval(count_query, *count_params)

        # Add pagination
        param_count += 1
        query += f" LIMIT ${param_count}"
        params.append(pageSize)

        param_count += 1
        query += f" OFFSET ${param_count}"
        params.append(offset)

        # Execute query
        rows = await conn.fetch(query, *params)

        # Transform products
        products = []
        for row in rows:
            product = convert_decimal_fields(dict(row))
            # Add mock flags for demo
            product['featured'] = featured if featured is not None else random.random() > 0.7
            product['bestseller'] = bestseller if bestseller is not None else random.random() > 0.8
            product['new_arrival'] = newArrival if newArrival is not None else random.random() > 0.85

            products.append(transform_product_for_frontend(product))

        return {
            'data': products,
            'total': total,
            'page': page,
            'pageSize': pageSize,
            'totalPages': (total + pageSize - 1) // pageSize if total > 0 else 0
        }

    except Exception as e:
        logger.error(f"Error fetching products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{product_id}/related")
async def get_related_products(
    product_id: str = Path(...),
    limit: int = Query(8, ge=1, le=50),
    store_id: Optional[str] = Query(None),
    x_store_id: Optional[str] = Header(None, alias="X-Store-ID"),
    conn = Depends(get_db_connection)
):
    """Get related/similar products"""
    # Use header if provided, otherwise fall back to query param
    effective_store_id = x_store_id or store_id

    try:
        # Get the base product's attributes
        base_product = await conn.fetchrow(
            """
            SELECT category, sub_category, plant_type, strain_type
            FROM inventory_products_view
            WHERE ocs_variant_number = $1
            """,
            product_id
        )

        if not base_product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Find related products
        query = """
            SELECT DISTINCT ON (p.ocs_item_number)
                p.*,
                i.quantity_available,
                i.retail_price,
                CASE WHEN i.quantity_available > 0 THEN true ELSE false END as in_stock
            FROM inventory_products_view p
            LEFT JOIN ocs_inventory i ON UPPER(p.ocs_variant_number) = UPPER(i.sku)
            WHERE p.ocs_variant_number != $1
            AND i.quantity_available > 0
            AND (
                p.category = $2 OR
                p.sub_category = $3 OR
                p.plant_type = $4 OR
                p.strain_type = $5
            )
        """

        params = [
            product_id,
            base_product['category'],
            base_product['sub_category'],
            base_product['plant_type'],
            base_product['strain_type']
        ]

        if effective_store_id:
            query += " AND i.store_id = $6"
            params.append(effective_store_id)

        query += f" ORDER BY p.ocs_item_number, p.product_name LIMIT {limit}"

        rows = await conn.fetch(query, *params)

        products = []
        for row in rows:
            product = convert_decimal_fields(dict(row))
            products.append(transform_product_for_frontend(product))

        return products

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching related products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{product_id}/frequently-bought")
async def get_frequently_bought(
    product_id: str = Path(...),
    limit: int = Query(4, ge=1, le=20),
    store_id: Optional[str] = Query(None),
    x_store_id: Optional[str] = Header(None, alias="X-Store-ID"),
    conn = Depends(get_db_connection)
):
    """Get frequently bought together products"""
    # Use header if provided, otherwise fall back to query param
    effective_store_id = x_store_id or store_id

    try:
        # For now, return complementary category products
        # In production, would track actual purchase patterns

        base_product = await conn.fetchrow(
            "SELECT category FROM inventory_products_view WHERE ocs_variant_number = $1",
            product_id
        )

        if not base_product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Define complementary categories
        complementary = {
            'Flower': ['Pre-Roll', 'Accessories'],
            'Pre-Roll': ['Flower', 'Accessories'],
            'Edibles': ['Beverages', 'Flower'],
            'Beverages': ['Edibles', 'Pre-Roll'],
            'Vapes': ['Cartridges', 'Accessories'],
            'Cartridges': ['Vapes', 'Accessories'],
            'Accessories': ['Flower', 'Pre-Roll', 'Vapes']
        }

        target_categories = complementary.get(base_product['category'], ['Accessories'])

        # Build query for complementary products
        placeholders = ','.join([f"'{cat}'" for cat in target_categories])
        query = f"""
            SELECT DISTINCT ON (p.ocs_item_number)
                p.*,
                i.quantity_available,
                i.retail_price,
                CASE WHEN i.quantity_available > 0 THEN true ELSE false END as in_stock
            FROM inventory_products_view p
            LEFT JOIN ocs_inventory i ON UPPER(p.ocs_variant_number) = UPPER(i.sku)
            WHERE p.category IN ({placeholders})
            AND i.quantity_available > 0
        """

        params = []
        if effective_store_id:
            query += " AND i.store_id = $1"
            params.append(effective_store_id)

        query += f" ORDER BY p.ocs_item_number, RANDOM() LIMIT {limit}"

        rows = await conn.fetch(query, *params)

        products = []
        for row in rows:
            product = convert_decimal_fields(dict(row))
            products.append(transform_product_for_frontend(product))

        return products

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching frequently bought products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{product_id}/reviews")
async def get_product_reviews(
    product_id: str = Path(...),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    conn = Depends(get_db_connection)
):
    """Get product reviews (mock data for now)"""
    try:
        # Verify product exists
        product = await conn.fetchrow(
            "SELECT product_name FROM inventory_products_view WHERE ocs_variant_number = $1",
            product_id
        )

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Generate mock reviews for demo
        # In production, would fetch from reviews table
        reviews = []
        review_count = random.randint(10, 50)

        for i in range(min(limit, review_count)):
            reviews.append({
                'id': f"review-{product_id}-{i}",
                'productId': product_id,
                'userId': f"user-{random.randint(1000, 9999)}",
                'userName': f"Customer {random.randint(1, 100)}",
                'rating': random.choice([3, 4, 4, 5, 5]),  # Weighted towards positive
                'title': random.choice([
                    'Great product!',
                    'Exactly what I wanted',
                    'Good quality',
                    'Highly recommend',
                    'Worth the price'
                ]),
                'comment': random.choice([
                    'Really enjoyed this product. Will definitely buy again.',
                    'High quality and fast delivery. Very satisfied.',
                    'Exactly as described. Great experience.',
                    'Good value for money. Recommended.',
                    'Perfect for my needs. Thank you!'
                ]),
                'verified': random.random() > 0.3,
                'helpful': random.randint(0, 20),
                'createdAt': datetime.now().isoformat(),
                'updatedAt': datetime.now().isoformat()
            })

        return {
            'reviews': reviews,
            'total': review_count,
            'page': page,
            'pageSize': limit,
            'averageRating': 4.5,
            'ratingDistribution': {
                '5': 45,
                '4': 30,
                '3': 15,
                '2': 7,
                '1': 3
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching reviews: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# This route MUST be last because it matches any path
@router.get("/{id_or_slug}")
async def get_product_detail(
    id_or_slug: str = Path(...),
    store_id: Optional[str] = Query(None),
    x_store_id: Optional[str] = Header(None, alias="X-Store-ID"),
    conn = Depends(get_db_connection)
):
    """Get single product details with all variants"""
    # Use header if provided, otherwise fall back to query param
    effective_store_id = x_store_id or store_id

    try:
        # First try to find by OCS variant number (ID)
        query = """
            SELECT * FROM inventory_products_view
            WHERE ocs_variant_number = $1
            LIMIT 1
        """

        main_product = await conn.fetchrow(query, id_or_slug)

        # If not found by ID, try by slug (product name)
        if not main_product:
            query = """
                SELECT * FROM inventory_products_view
                WHERE LOWER(REPLACE(product_name, ' ', '-')) = LOWER($1)
                LIMIT 1
            """
            main_product = await conn.fetchrow(query, id_or_slug)

        if not main_product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Get all variants with the same OCS item number
        variants_query = """
            SELECT
                p.*,
                i.quantity_available,
                i.retail_price,
                CASE WHEN i.quantity_available > 0 THEN true ELSE false END as in_stock
            FROM inventory_products_view p
            LEFT JOIN ocs_inventory i ON UPPER(p.ocs_variant_number) = UPPER(i.sku)
            WHERE p.ocs_item_number = $1
        """

        params = [main_product['ocs_item_number']]
        if effective_store_id:
            variants_query += " AND (i.store_id = $2 OR i.store_id IS NULL)"
            params.append(effective_store_id)

        variants_query += " ORDER BY p.size"

        variant_rows = await conn.fetch(variants_query, *params)

        # Serialize main product
        product_data = convert_decimal_fields(dict(main_product))

        # Add inventory data from the first variant
        if variant_rows:
            first_variant = dict(variant_rows[0])
            product_data['quantity_available'] = first_variant.get('quantity_available', 0)
            product_data['retail_price'] = first_variant.get('retail_price', product_data.get('unit_price'))
            product_data['in_stock'] = first_variant.get('in_stock', False)

            # Build variants list
            product_data['variants'] = []
            for variant_row in variant_rows:
                variant = convert_decimal_fields(dict(variant_row))
                product_data['variants'].append(variant)

        # Transform for frontend
        return transform_product_for_frontend(product_data, include_variants=True)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product detail: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))