"""
Product Details API Endpoint
Provides comprehensive product information using the inventory_products_view
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, Dict, Any
import logging
import asyncpg
import os
from decimal import Decimal
import json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/products", tags=["product-details"])

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


def serialize_product(row) -> Dict[str, Any]:
    """Convert database row to JSON-serializable dictionary"""
    product = dict(row)

    # Convert Decimal types to float
    decimal_fields = [
        'unit_price', 'unit_cost', 'retail_price', 'effective_price',
        'thc_content_per_unit', 'cbd_content_per_unit',
        'thc_content_per_volume', 'cbd_content_per_volume',
        'minimum_thc_content_percent', 'maximum_thc_content_percent',
        'minimum_cbd_content_percent', 'maximum_cbd_content_percent',
        'thc_range_min', 'thc_range_max', 'cbd_range_min', 'cbd_range_max',
        'physical_dimension_width', 'physical_dimension_height',
        'physical_dimension_depth', 'physical_dimension_volume',
        'physical_dimension_weight', 'net_weight',
        'reorder_point', 'reorder_quantity',
        'min_stock_level', 'max_stock_level'
    ]

    for field in decimal_fields:
        if field in product and product[field] is not None:
            product[field] = float(product[field])

    # Convert datetime objects to strings
    datetime_fields = [
        'product_created_at', 'product_updated_at',
        'inventory_created_at', 'inventory_updated_at',
        'last_restock_date', 'product_created_date', 'product_modified_date'
    ]

    for field in datetime_fields:
        if field in product and product[field] is not None:
            product[field] = product[field].isoformat()

    # Parse JSON fields
    if 'terpenes' in product and product['terpenes'] is not None:
        try:
            if isinstance(product['terpenes'], str):
                product['terpenes'] = json.loads(product['terpenes'])
        except:
            pass

    return product


@router.get("/details/{product_id}")
async def get_product_details(
    product_id: str,
    store_id: Optional[str] = Query(None, description="Store ID for inventory data"),
    conn = Depends(get_db_connection)
):
    """
    Get comprehensive product details including all fields from both
    ocs_product_catalog and ocs_inventory tables
    """
    try:
        # Build query with optional store filter
        query = """
            SELECT * FROM inventory_products_view
            WHERE LOWER(ocs_variant_number) = LOWER($1)
        """
        params = [product_id]

        if store_id:
            query += " AND store_id = $2"
            params.append(store_id)

        query += " LIMIT 1"

        # Execute query
        row = await conn.fetchrow(query, *params)

        if not row:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

        # Convert to dictionary and serialize
        product = serialize_product(row)

        # Organize data into logical groups for frontend display
        organized_data = {
            "basic_info": {
                "product_id": product.get("product_id"),
                "sku": product.get("sku"),
                "ocs_variant_number": product.get("ocs_variant_number"),
                "ocs_item_number": product.get("ocs_item_number"),
                "gtin": product.get("gtin"),
                "product_name": product.get("product_name"),
                "brand": product.get("brand"),
                "supplier_name": product.get("supplier_name"),
                "slug": product.get("slug")
            },
            "categorization": {
                "category": product.get("category"),
                "sub_category": product.get("sub_category"),
                "sub_sub_category": product.get("sub_sub_category"),
                "plant_type": product.get("plant_type"),
                "strain_type": product.get("strain_type"),
                "street_name": product.get("street_name")
            },
            "cannabinoids": {
                "thc_content_per_unit": product.get("thc_content_per_unit"),
                "cbd_content_per_unit": product.get("cbd_content_per_unit"),
                "thc_content_per_volume": product.get("thc_content_per_volume"),
                "cbd_content_per_volume": product.get("cbd_content_per_volume"),
                "minimum_thc_content_percent": product.get("minimum_thc_content_percent"),
                "maximum_thc_content_percent": product.get("maximum_thc_content_percent"),
                "minimum_cbd_content_percent": product.get("minimum_cbd_content_percent"),
                "maximum_cbd_content_percent": product.get("maximum_cbd_content_percent"),
                "terpenes": product.get("terpenes")
            },
            "inventory": {
                "inventory_id": product.get("inventory_id"),
                "store_id": product.get("store_id"),
                "quantity_on_hand": product.get("quantity_on_hand"),
                "quantity_available": product.get("quantity_available"),
                "quantity_reserved": product.get("quantity_reserved"),
                "in_stock": product.get("in_stock"),
                "stock_status": product.get("stock_status"),
                "is_available": product.get("is_available"),
                "reorder_point": product.get("reorder_point"),
                "reorder_quantity": product.get("reorder_quantity"),
                "min_stock_level": product.get("min_stock_level"),
                "max_stock_level": product.get("max_stock_level"),
                "last_restock_date": product.get("last_restock_date")
            },
            "pricing": {
                "unit_price": product.get("unit_price"),
                "unit_cost": product.get("unit_cost"),
                "retail_price": product.get("retail_price"),
                "effective_price": product.get("effective_price"),
                "override_price": product.get("override_price")
            },
            "physical_specs": {
                "size": product.get("size"),
                "pack_size": product.get("pack_size"),
                "unit_of_measure": product.get("unit_of_measure"),
                "net_weight": product.get("net_weight"),
                "physical_dimension_width": product.get("physical_dimension_width"),
                "physical_dimension_height": product.get("physical_dimension_height"),
                "physical_dimension_depth": product.get("physical_dimension_depth"),
                "physical_dimension_volume": product.get("physical_dimension_volume"),
                "physical_dimension_weight": product.get("physical_dimension_weight"),
                "number_of_items_in_retail_pack": product.get("number_of_items_in_retail_pack"),
                "eaches_per_inner_pack": product.get("eaches_per_inner_pack"),
                "eaches_per_master_case": product.get("eaches_per_master_case"),
                "dried_flower_cannabis_equivalency": product.get("dried_flower_cannabis_equivalency")
            },
            "production": {
                "grow_method": product.get("grow_method"),
                "growing_method": product.get("growing_method"),
                "grow_region": product.get("grow_region"),
                "grow_medium": product.get("grow_medium"),
                "drying_method": product.get("drying_method"),
                "trimming_method": product.get("trimming_method"),
                "extraction_process": product.get("extraction_process"),
                "ontario_grown": product.get("ontario_grown"),
                "craft": product.get("craft")
            },
            "description": {
                "product_short_description": product.get("product_short_description"),
                "product_long_description": product.get("product_long_description"),
                "colour": product.get("colour"),
                "ingredients": product.get("ingredients"),
                "carrier_oil": product.get("carrier_oil"),
                "food_allergens": product.get("food_allergens"),
                "storage_criteria": product.get("storage_criteria")
            },
            "hardware": {
                "heating_element_type": product.get("heating_element_type"),
                "battery_type": product.get("battery_type"),
                "rechargeable_battery": product.get("rechargeable_battery"),
                "removable_battery": product.get("removable_battery"),
                "replacement_parts_available": product.get("replacement_parts_available"),
                "temperature_control": product.get("temperature_control"),
                "temperature_display": product.get("temperature_display"),
                "compatibility": product.get("compatibility")
            },
            "ratings": {
                "rating": product.get("rating"),
                "rating_count": product.get("rating_count")
            },
            "logistics": {
                "fulfilment_method": product.get("fulfilment_method"),
                "delivery_tier": product.get("delivery_tier"),
                "catalog_stock_status": product.get("catalog_stock_status"),
                "inventory_status": product.get("inventory_status")
            },
            "metadata": {
                "product_created_at": product.get("product_created_at"),
                "product_updated_at": product.get("product_updated_at"),
                "inventory_created_at": product.get("inventory_created_at"),
                "inventory_updated_at": product.get("inventory_updated_at"),
                "image_url": product.get("image_url")
            },
            "raw_data": product  # Include all raw fields for completeness
        }

        return organized_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/details")
async def search_product_details(
    q: Optional[str] = Query(None, description="Search query"),
    store_id: Optional[str] = Query(None, description="Store ID filter"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    conn = Depends(get_db_connection)
):
    """
    Search products with comprehensive details
    """
    try:
        # Build query
        query = "SELECT * FROM inventory_products_view WHERE 1=1"
        params = []
        param_count = 0

        if store_id:
            param_count += 1
            query += f" AND store_id = ${param_count}"
            params.append(store_id)

        if q:
            param_count += 1
            query += f""" AND (
                product_name ILIKE ${param_count} OR
                brand ILIKE ${param_count} OR
                ocs_variant_number ILIKE ${param_count} OR
                CAST(gtin AS TEXT) ILIKE ${param_count}
            )"""
            params.append(f"%{q}%")

        # Add pagination
        param_count += 1
        query += f" LIMIT ${param_count}"
        params.append(limit)

        param_count += 1
        query += f" OFFSET ${param_count}"
        params.append(offset)

        # Execute query
        rows = await conn.fetch(query, *params)

        # Convert to list of dictionaries
        products = [serialize_product(row) for row in rows]

        # Get total count
        count_query = "SELECT COUNT(*) FROM inventory_products_view WHERE 1=1"
        if store_id:
            count_query += f" AND store_id = $1"
            if q:
                count_query += f""" AND (
                    product_name ILIKE $2 OR
                    brand ILIKE $2 OR
                    ocs_variant_number ILIKE $2 OR
                    CAST(gtin AS TEXT) ILIKE $2
                )"""
                total = await conn.fetchval(count_query, store_id, f"%{q}%")
            else:
                total = await conn.fetchval(count_query, store_id)
        elif q:
            count_query += f""" AND (
                product_name ILIKE $1 OR
                brand ILIKE $1 OR
                ocs_variant_number ILIKE $1 OR
                CAST(gtin AS TEXT) ILIKE $1
            )"""
            total = await conn.fetchval(count_query, f"%{q}%")
        else:
            total = await conn.fetchval(count_query)

        return {
            "products": products,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Error searching products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))