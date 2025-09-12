"""
OCS Product Catalog API Endpoints
Provides access to Ontario Cannabis Store product catalog data
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import asyncpg
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/province/catalog", tags=["Provincial Product Catalog"])


# Pydantic models for response
class OCSSizePricing(BaseModel):
    """Size and pricing information for OCS products"""
    size_3_5g: Optional[float] = Field(None, alias="3.5g")
    size_7g: Optional[float] = Field(None, alias="7g")
    size_14g: Optional[float] = Field(None, alias="14g")
    size_28g: Optional[float] = Field(None, alias="28g")

    class Config:
        populate_by_name = True


class OCSProduct(BaseModel):
    """OCS Product model with all 70 columns matching exact OCS specification"""
    # Core identification
    id: str
    
    # OCS Standard columns
    category: Optional[str]
    sub_category: Optional[str]
    sub_sub_category: Optional[str]
    product_name: str
    brand: Optional[str]
    supplier_name: Optional[str]
    product_short_description: Optional[str]
    product_long_description: Optional[str]
    size: Optional[str]
    colour: Optional[str]
    image_url: Optional[str]
    unit_of_measure: Optional[str]
    stock_status: Optional[str]
    unit_price: Optional[float]
    pack_size: Optional[int]
    
    # THC/CBD Content
    minimum_thc_content_percent: Optional[float]
    maximum_thc_content_percent: Optional[float]
    thc_content_per_unit: Optional[float]
    thc_content_per_volume: Optional[float]
    minimum_cbd_content_percent: Optional[float]
    maximum_cbd_content_percent: Optional[float]
    cbd_content_per_unit: Optional[float]
    cbd_content_per_volume: Optional[float]
    dried_flower_cannabis_equivalency: Optional[float]
    
    # Plant characteristics
    plant_type: Optional[str]
    terpenes: Optional[str]
    growing_method: Optional[str]
    number_of_items_in_retail_pack: Optional[int]
    
    # Product identifiers
    gtin: Optional[int]
    ocs_item_number: Optional[int]
    ocs_variant_number: Optional[str]
    
    # Physical dimensions
    physical_dimension_width: Optional[float]
    physical_dimension_height: Optional[float]
    physical_dimension_depth: Optional[float]
    physical_dimension_volume: Optional[float]
    physical_dimension_weight: Optional[float]
    
    # Packaging
    eaches_per_inner_pack: Optional[int]
    eaches_per_master_case: Optional[int]
    
    # Storage and allergens
    inventory_status: Optional[str]
    storage_criteria: Optional[str]
    food_allergens: Optional[str]
    ingredients: Optional[str]
    street_name: Optional[str]
    
    # Growing and production
    grow_medium: Optional[str]
    grow_method: Optional[str]
    grow_region: Optional[str]
    drying_method: Optional[str]
    trimming_method: Optional[str]
    extraction_process: Optional[str]
    carrier_oil: Optional[str]
    
    # Device specifications
    heating_element_type: Optional[str]
    battery_type: Optional[str]
    rechargeable_battery: Optional[bool]
    removable_battery: Optional[bool]
    replacement_parts_available: Optional[bool]
    temperature_control: Optional[bool]
    temperature_display: Optional[bool]
    compatibility: Optional[str]
    
    # Additional details
    strain_type: Optional[str]
    net_weight: Optional[float]
    ontario_grown: Optional[str]
    craft: Optional[str]
    fulfilment_method: Optional[str]
    delivery_tier: Optional[str]
    
    # Custom additions
    rating: Optional[float]
    rating_count: int = 0
    
    # Timestamps
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        populate_by_name = True


class OCSProductList(BaseModel):
    """Response model for product list"""
    products: List[OCSProduct]
    total: int
    page: int
    page_size: int
    total_pages: int


# Database connection
async def get_db_connection():
    """Get database connection"""
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5434,
            database='ai_engine',
            user='weedgo',
            password='your_password_here'
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=503, detail="Database connection failed")


# Helper function to parse pricing data
def parse_pricing(row: asyncpg.Record) -> Optional[OCSSizePricing]:
    """Parse pricing information from database row"""
    pricing_data = {}
    
    # Map database columns to pricing fields
    size_columns = {
        'size_3_5g': '3.5g',
        'size_7g': '7g', 
        'size_14g': '14g',
        'size_28g': '28g'
    }
    
    has_pricing = False
    for db_col, field_name in size_columns.items():
        if db_col in row and row[db_col] is not None:
            pricing_data[field_name] = float(row[db_col])
            has_pricing = True
    
    return OCSSizePricing(**pricing_data) if has_pricing else None


# API Endpoints
@router.get("/{province}", response_model=OCSProductList)
async def get_provincial_catalog(
    province: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    subcategory: Optional[str] = Query(None, description="Filter by subcategory"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    search: Optional[str] = Query(None, description="Search in product name or description"),
    strain_type: Optional[str] = Query(None, description="Filter by strain type (indica/sativa/hybrid)"),
    thc_min: Optional[float] = Query(None, description="Minimum THC percentage"),
    thc_max: Optional[float] = Query(None, description="Maximum THC percentage"),
    in_stock: Optional[bool] = Query(None, description="Filter by stock availability")
):
    """
    Get provincial product catalog with pagination and filtering
    
    - **province**: Province code (e.g., 'ocs' for Ontario)
    
    - **page**: Page number (starts from 1)
    - **page_size**: Number of items per page (max 100)
    - **category**: Filter by product category
    - **subcategory**: Filter by product subcategory
    - **brand**: Filter by brand name
    - **search**: Search in product name or description
    - **strain_type**: Filter by strain type
    - **thc_min/thc_max**: Filter by THC range
    - **in_stock**: Filter by availability
    """
    conn = None
    try:
        conn = await get_db_connection()
        
        # Build WHERE clause
        where_conditions = []
        params = []
        param_count = 0
        
        if category:
            param_count += 1
            where_conditions.append(f"category = ${param_count}")
            params.append(category)
        
        if subcategory:
            param_count += 1
            where_conditions.append(f"(subcategory = ${param_count} OR sub_category = ${param_count})")
            params.append(subcategory)
        
        if brand:
            param_count += 1
            where_conditions.append(f"brand = ${param_count}")
            params.append(brand)
        
        if search:
            param_count += 1
            where_conditions.append(f"(product_name ILIKE ${param_count} OR product_short_description ILIKE ${param_count} OR product_long_description ILIKE ${param_count})")
            params.append(f"%{search}%")
        
        if strain_type:
            param_count += 1
            where_conditions.append(f"strain_type = ${param_count}")
            params.append(strain_type)
        
        if thc_min is not None:
            param_count += 1
            where_conditions.append(f"maximum_thc_content_percent >= ${param_count}")
            params.append(thc_min)
        
        if thc_max is not None:
            param_count += 1
            where_conditions.append(f"minimum_thc_content_percent <= ${param_count}")
            params.append(thc_max)
        
        if in_stock is not None:
            param_count += 1
            where_conditions.append(f"stock_status = ${param_count}")
            params.append('In Stock' if in_stock else 'Out of Stock')
        
        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM product_catalog_ocs{where_clause}"
        total = await conn.fetchval(count_query, *params)
        
        # Calculate pagination
        offset = (page - 1) * page_size
        total_pages = (total + page_size - 1) // page_size
        
        # Get products
        param_count += 1
        limit_param = param_count
        param_count += 1
        offset_param = param_count
        
        query = f"""
            SELECT 
                id,
                category, sub_category, sub_sub_category,
                product_name, brand, supplier_name,
                product_short_description, product_long_description,
                size, colour, image_url, unit_of_measure,
                stock_status, unit_price, pack_size,
                minimum_thc_content_percent, maximum_thc_content_percent, 
                thc_content_per_unit, thc_content_per_volume,
                minimum_cbd_content_percent, maximum_cbd_content_percent, 
                cbd_content_per_unit, cbd_content_per_volume,
                dried_flower_cannabis_equivalency,
                plant_type, terpenes, growing_method,
                number_of_items_in_retail_pack,
                gtin, ocs_item_number, ocs_variant_number,
                physical_dimension_width, physical_dimension_height,
                physical_dimension_depth, physical_dimension_volume,
                physical_dimension_weight,
                eaches_per_inner_pack, eaches_per_master_case,
                inventory_status, storage_criteria,
                food_allergens, ingredients, street_name,
                grow_medium, grow_method, grow_region,
                drying_method, trimming_method,
                extraction_process, carrier_oil,
                heating_element_type, battery_type,
                rechargeable_battery, removable_battery,
                replacement_parts_available,
                temperature_control, temperature_display,
                compatibility,
                strain_type, net_weight,
                ontario_grown, craft,
                fulfilment_method, delivery_tier,
                rating, rating_count,
                created_at, updated_at
            FROM product_catalog_ocs
            {where_clause}
            ORDER BY rating DESC NULLS LAST, rating_count DESC, product_name, brand
            LIMIT ${limit_param} OFFSET ${offset_param}
        """
        
        rows = await conn.fetch(query, *params, page_size, offset)
        
        # Convert rows to products
        products = []
        for row in rows:
            product_data = {}
            
            # Map all columns from the row to the product model
            for key in row.keys():
                value = row[key]
                # Convert numeric types where needed
                if key in ['unit_price', 'minimum_thc_content_percent', 'maximum_thc_content_percent', 
                          'minimum_cbd_content_percent', 'maximum_cbd_content_percent',
                          'thc_content_per_unit', 'thc_content_per_volume',
                          'cbd_content_per_unit', 'cbd_content_per_volume',
                          'dried_flower_cannabis_equivalency', 'rating',
                          'physical_dimension_width', 'physical_dimension_height',
                          'physical_dimension_depth', 'physical_dimension_volume',
                          'physical_dimension_weight', 'net_weight']:
                    product_data[key] = float(value) if value is not None else None
                elif key == 'id':
                    product_data[key] = str(value)
                elif key in ['rechargeable_battery', 'removable_battery',
                            'replacement_parts_available', 'temperature_control',
                            'temperature_display']:
                    product_data[key] = bool(value) if value is not None else None
                else:
                    product_data[key] = value
            
            # Ensure rating_count defaults to 0
            if 'rating_count' not in product_data or product_data['rating_count'] is None:
                product_data['rating_count'] = 0
            
            product = OCSProduct(**product_data)
            products.append(product)
        
        return OCSProductList(
            products=products,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch OCS products: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            await conn.close()


@router.get("/{province}/categories", response_model=List[Dict[str, Any]])
async def get_provincial_categories(province: str):
    """
    Get all unique categories and subcategories from OCS catalog
    """
    conn = None
    try:
        conn = await get_db_connection()
        
        query = """
            SELECT DISTINCT 
                category,
                sub_category,
                COUNT(*) as product_count
            FROM product_catalog_ocs
            WHERE category IS NOT NULL
            GROUP BY category, COALESCE(subcategory, sub_category)
            ORDER BY category, subcategory
        """
        
        rows = await conn.fetch(query)
        
        # Organize into hierarchical structure
        categories = {}
        for row in rows:
            cat = row['category']
            subcat = row['subcategory']
            count = row['product_count']
            
            if cat not in categories:
                categories[cat] = {
                    'name': cat,
                    'product_count': 0,
                    'subcategories': []
                }
            
            categories[cat]['product_count'] += count
            
            if subcat:
                categories[cat]['subcategories'].append({
                    'name': subcat,
                    'product_count': count
                })
        
        return list(categories.values())
        
    except Exception as e:
        logger.error(f"Failed to fetch OCS categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            await conn.close()


@router.get("/{province}/brands", response_model=List[Dict[str, Any]])
async def get_provincial_brands(province: str):
    """
    Get all unique brands from OCS catalog with product counts
    """
    conn = None
    try:
        conn = await get_db_connection()
        
        query = """
            SELECT 
                brand,
                COUNT(*) as product_count
            FROM product_catalog_ocs
            WHERE brand IS NOT NULL
            GROUP BY brand
            ORDER BY brand
        """
        
        rows = await conn.fetch(query)
        
        return [
            {
                'name': row['brand'],
                'product_count': row['product_count']
            }
            for row in rows
        ]
        
    except Exception as e:
        logger.error(f"Failed to fetch OCS brands: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            await conn.close()


@router.get("/{province}/stats")
async def get_provincial_catalog_stats(province: str):
    """
    Get statistics about the provincial product catalog
    """
    conn = None
    try:
        conn = await get_db_connection()
        
        # Get total products
        total_query = "SELECT COUNT(*) as total FROM product_catalog_ocs"
        total_result = await conn.fetchrow(total_query)
        total_products = total_result['total'] if total_result else 0
        
        # Get categories count
        categories_query = "SELECT COUNT(DISTINCT category) as count FROM product_catalog_ocs WHERE category IS NOT NULL"
        categories_result = await conn.fetchrow(categories_query)
        total_categories = categories_result['count'] if categories_result else 0
        
        # Get brands count
        brands_query = "SELECT COUNT(DISTINCT brand) as count FROM product_catalog_ocs WHERE brand IS NOT NULL"
        brands_result = await conn.fetchrow(brands_query)
        total_brands = brands_result['count'] if brands_result else 0
        
        # Get last update time
        update_query = "SELECT MAX(updated_at) as last_update FROM product_catalog_ocs"
        update_result = await conn.fetchrow(update_query)
        last_update = update_result['last_update'] if update_result and update_result['last_update'] else None
        
        # Get product type breakdown
        type_query = """
            SELECT category, COUNT(*) as count 
            FROM product_catalog_ocs 
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
            LIMIT 10
        """
        type_results = await conn.fetch(type_query)
        category_breakdown = [
            {'category': row['category'], 'count': row['count']} 
            for row in type_results
        ]
        
        return {
            'total_products': total_products,
            'total_categories': total_categories,
            'total_brands': total_brands,
            'last_update': last_update.isoformat() if last_update else None,
            'category_breakdown': category_breakdown,
            'province': province.upper()
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch catalog stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            await conn.close()


@router.get("/{province}/all", response_model=List[Dict])
async def get_all_provincial_products(
    province: str,
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in product name or description")
):
    """
    Get ALL provincial products without pagination for virtual scrolling
    Returns simplified product data for performance
    """
    conn = None
    try:
        conn = await get_db_connection()
        
        # Build WHERE clause
        where_conditions = []
        params = []
        param_count = 0
        
        if category:
            param_count += 1
            where_conditions.append(f"category = ${param_count}")
            params.append(category)
        
        if search:
            param_count += 1
            where_conditions.append(f"(product_name ILIKE ${param_count} OR product_short_description ILIKE ${param_count} OR brand ILIKE ${param_count})")
            params.append(f"%{search}%")
        
        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Get all products with all columns including slug
        query = f"""
            SELECT 
                id, slug,
                category, sub_category, sub_sub_category,
                product_name, brand, supplier_name,
                product_short_description, product_long_description,
                size, colour, image_url, unit_of_measure,
                stock_status, unit_price, pack_size,
                minimum_thc_content_percent, maximum_thc_content_percent, 
                thc_content_per_unit, thc_content_per_volume,
                minimum_cbd_content_percent, maximum_cbd_content_percent, 
                cbd_content_per_unit, cbd_content_per_volume,
                dried_flower_cannabis_equivalency,
                plant_type, terpenes, growing_method,
                number_of_items_in_retail_pack,
                gtin, ocs_item_number, ocs_variant_number,
                physical_dimension_width, physical_dimension_height,
                physical_dimension_depth, physical_dimension_volume,
                physical_dimension_weight,
                eaches_per_inner_pack, eaches_per_master_case,
                inventory_status, storage_criteria,
                food_allergens, ingredients, street_name,
                grow_medium, grow_method, grow_region,
                drying_method, trimming_method,
                extraction_process, carrier_oil,
                heating_element_type, battery_type,
                rechargeable_battery, removable_battery,
                replacement_parts_available,
                temperature_control, temperature_display,
                compatibility,
                strain_type, net_weight,
                ontario_grown, craft,
                fulfilment_method, delivery_tier,
                rating, rating_count,
                created_at, updated_at
            FROM product_catalog_ocs
            {where_clause}
            ORDER BY product_name, brand
        """
        
        rows = await conn.fetch(query, *params)
        
        # Convert rows to simple dictionaries for performance
        products = []
        for row in rows:
            product = dict(row)
            # Convert id to string
            if 'id' in product:
                product['id'] = str(product['id'])
            # Convert timestamps to ISO format
            if 'created_at' in product and product['created_at']:
                product['created_at'] = product['created_at'].isoformat()
            if 'updated_at' in product and product['updated_at']:
                product['updated_at'] = product['updated_at'].isoformat()
            products.append(product)
        
        return products
        
    except Exception as e:
        logger.error(f"Failed to fetch all OCS products: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            await conn.close()


@router.get("/{province}/product/{ocs_variant_number}", response_model=OCSProduct)
async def get_provincial_product_by_variant(province: str, ocs_variant_number: str):
    """
    Get a single OCS product by its OCS variant number
    NOTE: This route must be last as it's a catch-all pattern
    
    - **ocs_variant_number**: OCS variant number identifier
    """
    conn = None
    try:
        conn = await get_db_connection()
        
        query = """
            SELECT 
                id,
                category, sub_category, sub_sub_category,
                product_name, brand, supplier_name,
                product_short_description, product_long_description,
                size, colour, image_url, unit_of_measure,
                stock_status, unit_price, pack_size,
                minimum_thc_content_percent, maximum_thc_content_percent, 
                thc_content_per_unit, thc_content_per_volume,
                minimum_cbd_content_percent, maximum_cbd_content_percent, 
                cbd_content_per_unit, cbd_content_per_volume,
                dried_flower_cannabis_equivalency,
                plant_type, terpenes, growing_method,
                number_of_items_in_retail_pack,
                gtin, ocs_item_number, ocs_variant_number,
                physical_dimension_width, physical_dimension_height,
                physical_dimension_depth, physical_dimension_volume,
                physical_dimension_weight,
                eaches_per_inner_pack, eaches_per_master_case,
                inventory_status, storage_criteria,
                food_allergens, ingredients, street_name,
                grow_medium, grow_method, grow_region,
                drying_method, trimming_method,
                extraction_process, carrier_oil,
                heating_element_type, battery_type,
                rechargeable_battery, removable_battery,
                replacement_parts_available,
                temperature_control, temperature_display,
                compatibility,
                strain_type, net_weight,
                ontario_grown, craft,
                fulfilment_method, delivery_tier,
                rating, rating_count,
                created_at, updated_at
            FROM product_catalog_ocs
            WHERE ocs_variant_number = $1
        """
        
        row = await conn.fetchrow(query, ocs_variant_number)
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Product with OCS variant number '{ocs_variant_number}' not found")
        
        # Convert row to product
        product_data = {}
        
        # Map all columns from the row to the product model
        for key in row.keys():
            value = row[key]
            # Convert numeric types where needed
            if key in ['unit_price', 'minimum_thc_content_percent', 'maximum_thc_content_percent', 
                      'minimum_cbd_content_percent', 'maximum_cbd_content_percent',
                      'thc_content_per_unit', 'thc_content_per_volume',
                      'cbd_content_per_unit', 'cbd_content_per_volume',
                      'dried_flower_cannabis_equivalency', 'rating',
                      'physical_dimension_width', 'physical_dimension_height',
                      'physical_dimension_depth', 'physical_dimension_volume',
                      'physical_dimension_weight', 'net_weight']:
                product_data[key] = float(value) if value is not None else None
            elif key == 'id':
                product_data[key] = str(value)
            elif key in ['rechargeable_battery', 'removable_battery',
                        'replacement_parts_available', 'temperature_control',
                        'temperature_display']:
                product_data[key] = bool(value) if value is not None else None
            else:
                product_data[key] = value
        
        # Ensure rating_count defaults to 0
        if 'rating_count' not in product_data or product_data['rating_count'] is None:
            product_data['rating_count'] = 0
        
        return OCSProduct(**product_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch OCS product by variant: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            await conn.close()