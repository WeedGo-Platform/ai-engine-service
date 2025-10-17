"""
Provincial Catalog V2 API Endpoints

DDD-powered provincial cannabis catalog upload and management.
Supports Ontario (OCS) catalog imports with automatic slug generation and data normalization.

Features:
- Bulk catalog upload from Excel/CSV files
- Automatic column name normalization
- UPSERT logic (insert new, update existing based on ocs_variant_number)
- Slug generation for URL-friendly product identifiers
- Statistics and error reporting
"""

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import pandas as pd
import io
import re
import logging

from ..dependencies import get_current_user, get_provincial_catalog_repository
from ddd_refactored.domain.product_catalog.repositories import IProvincialCatalogRepository

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v2/provincial-catalog",
    tags=["🍁 Provincial Catalog V2 (DDD)"],
    responses={404: {"description": "Not found"}},
)


# ============================================================================
# Helper Functions (Domain Logic)
# ============================================================================

def generate_slug(brand: Any, product_name: Any, sub_category: Any, size: Any) -> str:
    """
    Generate a URL-friendly slug from product attributes

    KISS Principle: Simple string concatenation with regex cleaning
    """
    parts = []

    for value in [brand, product_name, sub_category, size]:
        if value and pd.notna(value):
            # Convert to lowercase, remove special chars, replace spaces with hyphens
            slug_part = str(value).lower()
            slug_part = re.sub(r'[^\w\s-]', '', slug_part)
            slug_part = re.sub(r'[-\s]+', '-', slug_part).strip('-')
            if slug_part:
                parts.append(slug_part)

    return '-'.join(parts) if parts else 'product'


def normalize_column_name(name: str) -> str:
    """
    Convert OCS Excel column names to database column names

    DRY Principle: Centralized column mapping
    """
    mappings = {
        'Category': 'category',
        'Sub-Category': 'sub_category',
        'Sub-Sub-Category': 'sub_sub_category',
        'Product Name': 'product_name',
        'Brand': 'brand',
        'Supplier Name': 'supplier_name',
        'Product Short Description': 'product_short_description',
        'Product Long Description': 'product_long_description',
        'Size': 'size',
        'Colour': 'colour',
        'Image URL': 'image_url',
        'Unit of Measure': 'unit_of_measure',
        'Stock Status': 'stock_status',
        'Unit Price': 'unit_price',
        'Pack Size': 'pack_size',
        'Minimum THC Content (%)': 'minimum_thc_content_percent',
        'Maximum THC Content (%)': 'maximum_thc_content_percent',
        'THC Content Per Unit': 'thc_content_per_unit',
        'THC Content Per Volume': 'thc_content_per_volume',
        'Minimum CBD Content (%)': 'minimum_cbd_content_percent',
        'Maximum CBD Content (%)': 'maximum_cbd_content_percent',
        'CBD Content Per Unit': 'cbd_content_per_unit',
        'CBD Content Per Volume': 'cbd_content_per_volume',
        'Dried Flower Cannabis Equivalency': 'dried_flower_cannabis_equivalency',
        'Plant Type': 'plant_type',
        'Terpenes': 'terpenes',
        'GrowingMethod': 'growing_method',
        'Number of Items in a Retail Pack': 'number_of_items_in_retail_pack',
        'GTIN': 'gtin',
        'OCS Item Number': 'ocs_item_number',
        'OCS Variant Number': 'ocs_variant_number',
        'Physical Dimension Width': 'physical_dimension_width',
        'Physical Dimension Height': 'physical_dimension_height',
        'Physical Dimension Depth': 'physical_dimension_depth',
        'Physical Dimension Volume': 'physical_dimension_volume',
        'Physical Dimension Weight': 'physical_dimension_weight',
        'Eaches Per Inner Pack': 'eaches_per_inner_pack',
        'Eaches Per Master Case': 'eaches_per_master_case',
        'Inventory Status': 'inventory_status',
        'Storage Criteria': 'storage_criteria',
        'Food Allergens': 'food_allergens',
        'Ingredients': 'ingredients',
        'Street Name': 'street_name',
        'Grow Medium': 'grow_medium',
        'Grow Method': 'grow_method',
        'Grow Region': 'grow_region',
        'Drying Method': 'drying_method',
        'Trimming Method': 'trimming_method',
        'Extraction Process': 'extraction_process',
        'Carrier Oil': 'carrier_oil',
        'Heating Element Type': 'heating_element_type',
        'Battery Type': 'battery_type',
        'Rechargeable Battery': 'rechargeable_battery',
        'Removable Battery': 'removable_battery',
        'Replacement Parts Available': 'replacement_parts_available',
        'Temperature Control': 'temperature_control',
        'Temperature Display': 'temperature_display',
        'Compatibility': 'compatibility',
        'THC Min': 'thc_min',
        'THC Max': 'thc_max',
        'CBD Min': 'cbd_min',
        'CBD Max': 'cbd_max',
        'Net Weight': 'net_weight',
        'Ontario Grown': 'ontario_grown',
        'Craft': 'craft',
        'Fulfilment Method': 'fulfilment_method',
        'Delivery Tier': 'delivery_tier',
        'Strain Type': 'strain_type'
    }

    return mappings.get(name, name.strip().replace(' ', '_').lower())


def normalize_product_data(df: pd.DataFrame) -> list[Dict[str, Any]]:
    """
    Transform DataFrame into list of normalized product dictionaries

    DRY Principle: Single function for all data transformation
    KISS Principle: Simple row-by-row processing
    """
    products = []
    used_slugs = {}
    slug_counter = {}

    for index, row in df.iterrows():
        try:
            # Skip row if OCS Variant Number is missing
            ocs_variant_raw = row.get('OCS Variant Number')
            if pd.isna(ocs_variant_raw):
                logger.warning(f"Row {index+2}: Skipped due to missing OCS Variant Number")
                continue

            ocs_variant = str(ocs_variant_raw).strip()

            # Generate slug
            brand = row.get('Brand')
            product_name = row.get('Product Name')
            sub_category = row.get('Sub-Category')
            size = row.get('Size')

            base_slug = generate_slug(brand, product_name, sub_category, size)

            # Ensure slug uniqueness per variant
            slug = base_slug
            if base_slug in used_slugs and used_slugs[base_slug] != ocs_variant:
                if base_slug not in slug_counter:
                    slug_counter[base_slug] = 1
                slug_counter[base_slug] += 1
                slug = f"{base_slug}-{slug_counter[base_slug]}"
            else:
                used_slugs[base_slug] = ocs_variant

            # Build normalized product dictionary
            product_data = {'slug': slug}

            for excel_col, value in row.items():
                # Normalize column name
                db_col = normalize_column_name(excel_col)

                # Skip NaN values
                if pd.isna(value):
                    continue

                # Handle data type conversions
                if db_col in ['rechargeable_battery', 'removable_battery', 'replacement_parts_available']:
                    str_value = str(value).strip().lower()
                    if str_value in ['yes', 'true', '1']:
                        value = True
                    elif str_value in ['no', 'false', '0']:
                        value = False
                    else:
                        continue

                elif db_col in ['ocs_variant_number', 'gtin']:
                    value = str(value).strip()

                elif db_col in ['ocs_item_number', 'pack_size', 'number_of_items_in_retail_pack',
                               'eaches_per_inner_pack', 'eaches_per_master_case']:
                    try:
                        value = int(float(value))
                    except (ValueError, TypeError):
                        logger.warning(f"Row {index+2}: Invalid integer for '{excel_col}': {value}")
                        continue

                elif db_col in ['unit_price', 'physical_dimension_width', 'physical_dimension_height',
                               'physical_dimension_depth', 'physical_dimension_volume', 'physical_dimension_weight',
                               'thc_content_per_unit', 'cbd_content_per_unit', 'thc_content_per_volume',
                               'cbd_content_per_volume', 'dried_flower_cannabis_equivalency',
                               'minimum_thc_content_percent', 'maximum_thc_content_percent',
                               'minimum_cbd_content_percent', 'maximum_cbd_content_percent',
                               'thc_min', 'thc_max', 'cbd_min', 'cbd_max', 'net_weight']:
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        logger.warning(f"Row {index+2}: Invalid numeric value for '{excel_col}': {value}")
                        continue

                else:
                    value = str(value).strip()

                product_data[db_col] = value

            products.append(product_data)

        except Exception as e:
            logger.error(f"Row {index+2}: Error processing row - {str(e)}")
            continue

    return products


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/upload", status_code=status.HTTP_200_OK)
async def upload_provincial_catalog(
    file: UploadFile = File(...),
    province: str = Form(...),
    current_user: dict = Depends(get_current_user),
    repository: IProvincialCatalogRepository = Depends(get_provincial_catalog_repository)
):
    """
    Upload and process provincial cannabis catalog files

    Currently supports:
    - Ontario (OCS) catalog

    Process:
    1. Validate file type (CSV or Excel)
    2. Parse and normalize data
    3. Bulk upsert into database (insert new, update existing)
    4. Return statistics

    **Authorization**: Requires authentication (super_admin role recommended)

    **Request**:
    - file: Excel (.xlsx, .xls) or CSV file
    - province: Province code (currently only "ON" supported)

    **Response**:
    ```json
    {
        "success": true,
        "message": "Successfully processed ON catalog",
        "stats": {
            "totalRecords": 5388,
            "inserted": 5000,
            "updated": 388,
            "errors": 0,
            "error_details": []
        }
    }
    ```
    """

    # Validate province
    if province not in ['ON']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Province '{province}' is not currently supported. Supported: ON (Ontario)"
        )

    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )

    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in ['csv', 'xlsx', 'xls']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Supported: CSV, XLSX, XLS"
        )

    try:
        # Read file content
        content = await file.read()

        # Parse file
        if file_ext == 'csv':
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))

        logger.info(f"Parsed {len(df)} rows from {file.filename}")

        # Validate required columns
        if 'OCS Variant Number' not in df.columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Required column 'OCS Variant Number' not found in file"
            )

        # Normalize data
        products = normalize_product_data(df)
        logger.info(f"Normalized {len(products)} valid products")

        if not products:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid products found in file"
            )

        # Bulk upsert via repository
        stats = await repository.bulk_upsert(products)

        return JSONResponse(content={
            'success': True,
            'message': f'Successfully processed {province} catalog',
            'stats': stats
        })

    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty"
        )
    except Exception as e:
        logger.error(f"Error processing catalog upload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )


@router.get("/statistics", status_code=status.HTTP_200_OK)
async def get_catalog_statistics(
    current_user: dict = Depends(get_current_user),
    repository: IProvincialCatalogRepository = Depends(get_provincial_catalog_repository)
):
    """
    Get provincial catalog statistics

    Returns counts and metrics about the imported catalog data.
    """
    try:
        stats = await repository.get_statistics()
        return JSONResponse(content={
            'success': True,
            'statistics': stats
        })
    except Exception as e:
        logger.error(f"Error getting catalog statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving statistics: {str(e)}"
        )


@router.delete("/clear", status_code=status.HTTP_200_OK)
async def clear_catalog(
    current_user: dict = Depends(get_current_user),
    repository: IProvincialCatalogRepository = Depends(get_provincial_catalog_repository)
):
    """
    Clear entire provincial catalog

    **Warning**: This deletes ALL products from the catalog.
    Use with caution - typically for fresh imports only.

    **Authorization**: Requires super_admin role
    """
    try:
        # TODO: Add role check for super_admin
        # if current_user.get('role') != 'super_admin':
        #     raise HTTPException(status_code=403, detail="Requires super_admin role")

        count = await repository.delete_all()
        return JSONResponse(content={
            'success': True,
            'message': f'Deleted {count} products from catalog',
            'deleted_count': count
        })
    except Exception as e:
        logger.error(f"Error clearing catalog: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing catalog: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Provincial Catalog V2",
        "supported_provinces": ["ON"]
    }
