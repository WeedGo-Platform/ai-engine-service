from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
import pandas as pd
import io
import re
from typing import Dict, Any, Optional
import asyncpg
from datetime import datetime
from pydantic import BaseModel
from database.connection import get_db_connection
from core.authentication import get_current_user

# Simple User model for authentication
class User(BaseModel):
    id: str
    email: str
    role: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

router = APIRouter()

def generate_slug(brand, product_name, sub_category, size):
    """Generate a URL-friendly slug from brand, product name, sub-category, and size."""
    parts = []

    # Add brand if available
    if brand and pd.notna(brand):
        brand_slug = str(brand).lower()
        brand_slug = re.sub(r'[^\w\s-]', '', brand_slug)
        brand_slug = re.sub(r'[-\s]+', '-', brand_slug).strip('-')
        if brand_slug:
            parts.append(brand_slug)

    # Add product name if available
    if product_name and pd.notna(product_name):
        name_slug = str(product_name).lower()
        name_slug = re.sub(r'[^\w\s-]', '', name_slug)
        name_slug = re.sub(r'[-\s]+', '-', name_slug).strip('-')
        if name_slug:
            parts.append(name_slug)

    # Add sub-category if available
    if sub_category and pd.notna(sub_category):
        sub_cat_slug = str(sub_category).lower()
        sub_cat_slug = re.sub(r'[^\w\s-]', '', sub_cat_slug)
        sub_cat_slug = re.sub(r'[-\s]+', '-', sub_cat_slug).strip('-')
        if sub_cat_slug:
            parts.append(sub_cat_slug)

    # Add size if available
    if size and pd.notna(size):
        size_slug = str(size).lower()
        size_slug = re.sub(r'[^\w\s-]', '', size_slug)
        size_slug = re.sub(r'[-\s]+', '-', size_slug).strip('-')
        if size_slug:
            parts.append(size_slug)

    # Join all parts with hyphen
    slug = '-'.join(parts) if parts else 'product'
    return slug

def normalize_column_name(name: str) -> str:
    """Convert OCS column names to database column names."""
    # Exact mappings from OCS Excel columns to database columns
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
        # Also add strain_type which appears in the database
        'Strain Type': 'strain_type'
    }

    return mappings.get(name, name.strip().replace(' ', '_').lower())

@router.post("/upload")
async def upload_provincial_catalog(
    file: UploadFile = File(...),
    province: str = Form(...)
    # current_user: User = Depends(get_current_user),  # Temporarily disabled for testing
    # conn: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Upload and process provincial cannabis catalog files.
    Currently supports Ontario (OCS) catalog.
    """
    
    # Get asyncpg connection directly
    import os
    conn = await asyncpg.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5434)),
        database=os.getenv('DB_NAME', 'ai_engine'),
        user=os.getenv('DB_USER', 'weedgo'),
        password=os.getenv('DB_PASSWORD', 'your_password_here')
    )
    
    # Check if user is super admin
    # Temporarily disabled for testing
    # if current_user.role != 'super_admin':
    #     raise HTTPException(status_code=403, detail="Only super administrators can upload catalogs")
    
    # Validate province
    if province not in ['ON']:  # Currently only Ontario is supported
        raise HTTPException(status_code=400, detail=f"Province {province} is not currently supported")
    
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in ['csv', 'xlsx', 'xls']:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload CSV or Excel file")
    
    try:
        # Read file content
        content = await file.read()
        
        # Parse file based on type
        if file_ext == 'csv':
            df = pd.read_csv(io.BytesIO(content))
        else:  # Excel
            df = pd.read_excel(io.BytesIO(content))
        
        # Check for required OCS variant number column
        if 'OCS Variant Number' not in df.columns:
            raise HTTPException(
                status_code=400, 
                detail="OCS Variant Number column is required for matching products"
            )
        
        # Initialize statistics
        stats = {
            'totalRecords': len(df),
            'inserted': 0,
            'updated': 0,
            'errors': 0,
            'error_details': []
        }

        # Track generated slugs to ensure uniqueness
        used_slugs = {}
        slug_counter = {}

        # Get existing columns from database
        existing_columns_query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ocs_product_catalog'
        """
        existing_columns = await conn.fetch(existing_columns_query)
        db_columns = {row['column_name'] for row in existing_columns}
        
        # Process each row
        for index, row in df.iterrows():
            try:
                # Generate slug for this product
                brand = row.get('Brand')
                product_name = row.get('Product Name')
                sub_category = row.get('Sub-Category')
                size = row.get('Size')

                base_slug = generate_slug(brand, product_name, sub_category, size)

                # Ensure slug uniqueness
                slug = base_slug
                ocs_variant = str(row.get('OCS Variant Number', '')).strip()

                # If we've seen this slug before for a different variant, add a counter
                if base_slug in used_slugs and used_slugs[base_slug] != ocs_variant:
                    if base_slug not in slug_counter:
                        slug_counter[base_slug] = 1
                    slug_counter[base_slug] += 1
                    slug = f"{base_slug}-{slug_counter[base_slug]}"
                else:
                    used_slugs[base_slug] = ocs_variant

                # Build column lists and values for upsert
                columns = ['slug']
                values = [slug]
                update_sets = ['slug = EXCLUDED.slug']

                for col, value in row.items():
                    # Normalize the column name
                    db_col = normalize_column_name(col)

                    if db_col in db_columns and db_col not in ['id', 'created_at', 'updated_at', 'rating', 'rating_count', 'slug']:
                        # Skip NaN values
                        if pd.isna(value):
                            continue
                        
                        # Handle data type conversions
                        if db_col == 'ocs_item_number':
                            # OCS item number should be integer
                            try:
                                value = int(value)
                            except (ValueError, TypeError):
                                continue
                        elif db_col == 'ocs_variant_number':
                            # OCS variant number should be string
                            value = str(value).strip()
                        elif db_col == 'gtin':
                            # GTIN should be bigint
                            try:
                                value = int(value)
                            except (ValueError, TypeError):
                                continue
                        elif db_col in ['rechargeable_battery', 'removable_battery', 'replacement_parts_available']:
                            # These are boolean fields in the database (excluding temperature fields which are now strings)
                            if pd.isna(value) or str(value).strip() == '-':
                                continue  # Skip null/dash values
                            # Convert Yes/No to boolean
                            str_value = str(value).strip().lower()
                            if str_value in ['yes', 'true', '1']:
                                value = True
                            elif str_value in ['no', 'false', '0']:
                                value = False
                            else:
                                continue  # Skip invalid boolean values
                        elif db_col in ['pack_size', 'number_of_items_in_retail_pack', 'eaches_per_inner_pack', 'eaches_per_master_case']:
                            # These should be integers
                            try:
                                value = int(value)
                            except (ValueError, TypeError):
                                continue
                        elif db_col in ['unit_price', 'physical_dimension_width', 'physical_dimension_height', 
                                       'physical_dimension_depth', 'physical_dimension_volume', 'physical_dimension_weight',
                                       'thc_content_per_unit', 'cbd_content_per_unit', 'thc_content_per_volume', 
                                       'cbd_content_per_volume', 'dried_flower_cannabis_equivalency',
                                       'minimum_thc_content_percent', 'maximum_thc_content_percent',
                                       'minimum_cbd_content_percent', 'maximum_cbd_content_percent',
                                       'thc_min', 'thc_max', 'cbd_min', 'cbd_max', 'net_weight']:
                            # These should be numeric/decimal
                            try:
                                value = float(value)
                            except (ValueError, TypeError):
                                continue
                        else:
                            # Everything else should be string
                            value = str(value).strip() if not pd.isna(value) else value
                        
                        columns.append(db_col)
                        values.append(value)
                        
                        update_sets.append(f"{db_col} = EXCLUDED.{db_col}")
                
                
                # Add updated_at
                columns.append('updated_at')
                values.append(datetime.utcnow())
                update_sets.append("updated_at = EXCLUDED.updated_at")
                
                # Build the UPSERT query
                placeholders = [f"${i+1}" for i in range(len(values))]
                insert_query = f"""
                    INSERT INTO ocs_product_catalog ({', '.join(columns)})
                    VALUES ({', '.join(placeholders)})
                    ON CONFLICT (ocs_variant_number) DO UPDATE SET
                    {', '.join(update_sets)}
                    RETURNING (xmax = 0) as inserted
                """
                
                # Execute the query
                result = await conn.fetchrow(insert_query, *values)
                
                if result and result['inserted']:
                    stats['inserted'] += 1
                else:
                    stats['updated'] += 1
                    
            except Exception as e:
                error_msg = f"Row {index}: {str(e)}"
                print(f"Error processing {error_msg}")
                stats['errors'] += 1
                if len(stats['error_details']) < 10:  # Keep first 10 errors for debugging
                    stats['error_details'].append(error_msg)
                continue
        
        await conn.close()  # Close the connection
        return JSONResponse(content={
            'success': True,
            'message': f'Successfully processed {province} catalog',
            'stats': stats
        })
        
    except pd.errors.EmptyDataError:
        if conn:
            await conn.close()  # Ensure connection is closed on error
        raise HTTPException(status_code=400, detail="The uploaded file is empty")
    except Exception as e:
        if conn:
            await conn.close()  # Ensure connection is closed on error
        print(f"Error processing catalog upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")