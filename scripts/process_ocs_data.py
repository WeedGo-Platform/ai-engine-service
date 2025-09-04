#!/usr/bin/env python3
"""
OCS Cannabis Data Processing Pipeline
Processes the OCS Excel catalogue and loads it into PostgreSQL
"""

import pandas as pd
import numpy as np
import psycopg2
from psycopg2.extras import execute_values
import sys
import os
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OCSDataProcessor:
    """Processes OCS cannabis catalogue data"""
    
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.conn = None
        
    def connect_db(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.conn.autocommit = False
            logger.info("Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def disconnect_db(self):
        """Disconnect from database"""
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from database")
    
    def clean_numeric_value(self, value: Any) -> Optional[float]:
        """Clean and convert numeric values"""
        if pd.isna(value) or value is None:
            return None
        
        if isinstance(value, (int, float)):
            return float(value) if not np.isnan(value) else None
        
        # Handle string values
        str_value = str(value).strip()
        if not str_value or str_value in ['-', 'N/A', 'n/a', '']:
            return None
        
        # Remove units and extra text
        str_value = re.sub(r'[^\d\.-]', '', str_value)
        
        try:
            return float(str_value) if str_value else None
        except ValueError:
            return None
    
    def clean_string_value(self, value: Any) -> Optional[str]:
        """Clean string values"""
        if pd.isna(value) or value is None:
            return None
        
        str_value = str(value).strip()
        if str_value in ['-', 'N/A', 'n/a', '', 'NaN']:
            return None
        
        return str_value
    
    def parse_terpenes(self, terpenes_str: str) -> List[str]:
        """Parse terpenes from comma-separated string"""
        if not terpenes_str or pd.isna(terpenes_str):
            return []
        
        # Split by comma and clean each terpene
        terpenes = [t.strip() for t in str(terpenes_str).split(',')]
        terpenes = [t for t in terpenes if t and t != '-']
        
        # Remove duplicates while preserving order
        seen = set()
        result = []
        for t in terpenes:
            if t not in seen:
                seen.add(t)
                result.append(t)
        
        return result
    
    def parse_thc_cbd_mg_values(self, value: Any) -> Optional[float]:
        """Parse THC/CBD values in mg/g format"""
        if pd.isna(value) or value is None:
            return None
        
        str_value = str(value).strip()
        if 'mg/g' in str_value:
            # Extract numeric part before mg/g
            match = re.search(r'([\d\.]+)\s*mg/g', str_value)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    return None
        
        # If it's just a number, assume it's already in mg/g
        try:
            return float(str_value)
        except ValueError:
            return None
    
    def process_product_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Process raw product data into structured format"""
        processed_products = []
        
        for _, row in df.iterrows():
            try:
                # Parse terpenes
                terpenes = self.parse_terpenes(row.get('Terpenes'))
                
                # Parse boolean values
                ontario_grown = self.clean_string_value(row.get('Ontario Grown', '')).lower() in ['yes', 'true', '1'] if self.clean_string_value(row.get('Ontario Grown')) else False
                craft = self.clean_string_value(row.get('Craft', '')).lower() in ['yes', 'true', '1'] if self.clean_string_value(row.get('Craft')) else False
                
                # Handle food allergens and ingredients as arrays
                food_allergens = []
                ingredients = []
                
                allergens_str = self.clean_string_value(row.get('Food Allergens'))
                if allergens_str:
                    food_allergens = [a.strip() for a in allergens_str.split(',') if a.strip()]
                
                ingredients_str = self.clean_string_value(row.get('Ingredients'))
                if ingredients_str:
                    ingredients = [i.strip() for i in ingredients_str.split(',') if i.strip()]
                
                product = {
                    'ocs_item_number': self.clean_string_value(row.get('OCS Item Number')),
                    'ocs_variant_number': self.clean_string_value(row.get('OCS Variant Number')),
                    'gtin': self.clean_numeric_value(row.get('GTIN')),
                    
                    # Basic information
                    'name': self.clean_string_value(row.get('Product Name')),
                    'brand': self.clean_string_value(row.get('Brand')),
                    'supplier_name': self.clean_string_value(row.get('Supplier Name')),
                    'street_name': self.clean_string_value(row.get('Street Name')),
                    
                    # Categories
                    'category': self.clean_string_value(row.get('Category')),
                    'sub_category': self.clean_string_value(row.get('Sub-Category')),
                    'sub_sub_category': self.clean_string_value(row.get('Sub-Sub-Category')),
                    
                    # Descriptions
                    'short_description': self.clean_string_value(row.get('Product Short Description')),
                    'long_description': self.clean_string_value(row.get('Product Long Description')),
                    
                    # Product specifications
                    'size': self.clean_string_value(row.get('Size')),
                    'unit_of_measure': self.clean_string_value(row.get('Unit of Measure')),
                    'pack_size': self.clean_numeric_value(row.get('Pack Size')),
                    'net_weight': self.clean_numeric_value(row.get('Net Weight')),
                    'color': self.clean_string_value(row.get('Colour')),
                    
                    # THC content
                    'thc_min_percent': self.clean_numeric_value(row.get('Minimum THC Content (%)')),
                    'thc_max_percent': self.clean_numeric_value(row.get('Maximum THC Content (%)')),
                    'thc_content_per_unit': self.clean_numeric_value(row.get('THC Content Per Unit')),
                    'thc_content_per_volume': self.clean_numeric_value(row.get('THC Content Per Volume')),
                    'thc_min_mg_g': self.parse_thc_cbd_mg_values(row.get('THC Min')),
                    'thc_max_mg_g': self.parse_thc_cbd_mg_values(row.get('THC Max')),
                    
                    # CBD content
                    'cbd_min_percent': self.clean_numeric_value(row.get('Minimum CBD Content (%)')),
                    'cbd_max_percent': self.clean_numeric_value(row.get('Maximum CBD Content (%)')),
                    'cbd_content_per_unit': self.clean_numeric_value(row.get('CBD Content Per Unit')),
                    'cbd_content_per_volume': self.clean_numeric_value(row.get('CBD Content Per Volume')),
                    'cbd_min_mg_g': self.parse_thc_cbd_mg_values(row.get('CBD Min')),
                    'cbd_max_mg_g': self.parse_thc_cbd_mg_values(row.get('CBD Max')),
                    
                    # Cannabis characteristics
                    'plant_type': self.clean_string_value(row.get('Plant Type')),
                    'dried_flower_equivalency': self.clean_numeric_value(row.get('Dried Flower Cannabis Equivalency')),
                    'terpenes': terpenes,
                    
                    # Growing information
                    'growing_method': self.clean_string_value(row.get('GrowingMethod')),
                    'grow_medium': self.clean_string_value(row.get('Grow Medium')),
                    'grow_method': self.clean_string_value(row.get('Grow Method')),
                    'grow_region': self.clean_string_value(row.get('Grow Region')),
                    'drying_method': self.clean_string_value(row.get('Drying Method')),
                    'trimming_method': self.clean_string_value(row.get('Trimming Method')),
                    'ontario_grown': ontario_grown,
                    'craft': craft,
                    
                    # Processing information
                    'extraction_process': self.clean_string_value(row.get('Extraction Process')),
                    'carrier_oil': self.clean_string_value(row.get('Carrier Oil')),
                    
                    # Hardware specifications
                    'heating_element_type': self.clean_string_value(row.get('Heating Element Type')),
                    'battery_type': self.clean_string_value(row.get('Battery Type')),
                    'rechargeable_battery': self.clean_string_value(row.get('Rechargeable Battery', '')).lower() in ['yes', 'true', '1'] if self.clean_string_value(row.get('Rechargeable Battery')) else None,
                    'removable_battery': self.clean_string_value(row.get('Removable Battery', '')).lower() in ['yes', 'true', '1'] if self.clean_string_value(row.get('Removable Battery')) else None,
                    'replacement_parts_available': self.clean_string_value(row.get('Replacement Parts Available', '')).lower() in ['yes', 'true', '1'] if self.clean_string_value(row.get('Replacement Parts Available')) else None,
                    'temperature_control': self.clean_string_value(row.get('Temperature Control', '')).lower() in ['yes', 'true', '1'] if self.clean_string_value(row.get('Temperature Control')) else None,
                    'temperature_display': self.clean_string_value(row.get('Temperature Display', '')).lower() in ['yes', 'true', '1'] if self.clean_string_value(row.get('Temperature Display')) else None,
                    'compatibility': self.clean_string_value(row.get('Compatibility')),
                    
                    # Inventory and logistics
                    'stock_status': self.clean_string_value(row.get('Stock Status')),
                    'inventory_status': self.clean_string_value(row.get('Inventory Status')),
                    'items_per_retail_pack': self.clean_numeric_value(row.get('Number of Items in a Retail Pack')),
                    'eaches_per_inner_pack': self.clean_numeric_value(row.get('Eaches Per Inner Pack')),
                    'eaches_per_master_case': self.clean_numeric_value(row.get('Eaches Per Master Case')),
                    'fulfilment_method': self.clean_string_value(row.get('Fulfilment Method')),
                    'delivery_tier': self.clean_string_value(row.get('Delivery Tier')),
                    
                    # Physical dimensions
                    'dimension_width_cm': self.clean_numeric_value(row.get('Physical Dimension Width')),
                    'dimension_height_cm': self.clean_numeric_value(row.get('Physical Dimension Height')),
                    'dimension_depth_cm': self.clean_numeric_value(row.get('Physical Dimension Depth')),
                    'dimension_volume_ml': self.clean_numeric_value(row.get('Physical Dimension Volume')),
                    'dimension_weight_kg': self.clean_numeric_value(row.get('Physical Dimension Weight')),
                    
                    # Storage and safety
                    'storage_criteria': self.clean_string_value(row.get('Storage Criteria')),
                    'food_allergens': food_allergens,
                    'ingredients': ingredients,
                    
                    # Media
                    'image_url': self.clean_string_value(row.get('Image URL')),
                    
                    # Metadata
                    'is_active': True,  # These are from MasterCatalogue
                    'last_scraped_at': datetime.now()
                }
                
                # Only add products with required fields
                if product['ocs_item_number'] and product['name'] and product['brand']:
                    processed_products.append(product)
                else:
                    logger.warning(f"Skipping product with missing required fields: {product.get('name', 'Unknown')}")
                    
            except Exception as e:
                logger.error(f"Error processing product row: {e}")
                continue
        
        logger.info(f"Processed {len(processed_products)} valid products")
        return processed_products
    
    def insert_products(self, products: List[Dict[str, Any]]):
        """Insert products into database"""
        if not products:
            logger.warning("No products to insert")
            return
        
        # Define the column order and SQL template
        columns = [
            'ocs_item_number', 'ocs_variant_number', 'gtin', 'name', 'brand', 'supplier_name',
            'street_name', 'category', 'sub_category', 'sub_sub_category', 'short_description',
            'long_description', 'size', 'unit_of_measure', 'pack_size', 'net_weight', 'color',
            'thc_min_percent', 'thc_max_percent', 'thc_content_per_unit', 'thc_content_per_volume',
            'thc_min_mg_g', 'thc_max_mg_g', 'cbd_min_percent', 'cbd_max_percent', 'cbd_content_per_unit',
            'cbd_content_per_volume', 'cbd_min_mg_g', 'cbd_max_mg_g', 'plant_type',
            'dried_flower_equivalency', 'terpenes', 'growing_method', 'grow_medium', 'grow_method',
            'grow_region', 'drying_method', 'trimming_method', 'ontario_grown', 'craft',
            'extraction_process', 'carrier_oil', 'heating_element_type', 'battery_type',
            'rechargeable_battery', 'removable_battery', 'replacement_parts_available',
            'temperature_control', 'temperature_display', 'compatibility', 'stock_status',
            'inventory_status', 'items_per_retail_pack', 'eaches_per_inner_pack',
            'eaches_per_master_case', 'fulfilment_method', 'delivery_tier', 'dimension_width_cm',
            'dimension_height_cm', 'dimension_depth_cm', 'dimension_volume_ml', 'dimension_weight_kg',
            'storage_criteria', 'food_allergens', 'ingredients', 'image_url', 'is_active',
            'last_scraped_at'
        ]
        
        # Prepare data for insertion
        values = []
        for product in products:
            row = []
            for col in columns:
                value = product.get(col)
                
                # Handle arrays for PostgreSQL
                if col in ['terpenes', 'food_allergens', 'ingredients']:
                    if isinstance(value, list):
                        row.append(value)
                    else:
                        row.append([])
                else:
                    row.append(value)
            
            values.append(tuple(row))
        
        # SQL for insertion with conflict resolution - use %s for execute_values
        sql = f"""
        INSERT INTO cannabis_data.products ({', '.join(columns)})
        VALUES %s
        ON CONFLICT (ocs_variant_number) 
        DO UPDATE SET
            name = EXCLUDED.name,
            brand = EXCLUDED.brand,
            supplier_name = EXCLUDED.supplier_name,
            short_description = EXCLUDED.short_description,
            long_description = EXCLUDED.long_description,
            thc_min_percent = EXCLUDED.thc_min_percent,
            thc_max_percent = EXCLUDED.thc_max_percent,
            cbd_min_percent = EXCLUDED.cbd_min_percent,
            cbd_max_percent = EXCLUDED.cbd_max_percent,
            terpenes = EXCLUDED.terpenes,
            image_url = EXCLUDED.image_url,
            stock_status = EXCLUDED.stock_status,
            last_scraped_at = EXCLUDED.last_scraped_at,
            updated_at = NOW()
        """
        
        try:
            cursor = self.conn.cursor()
            execute_values(cursor, sql, values, page_size=100)
            self.conn.commit()
            logger.info(f"Successfully inserted/updated {len(products)} products")
            cursor.close()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to insert products: {e}")
            raise
    
    def load_ocs_data(self, excel_path: str):
        """Load OCS data from Excel file"""
        logger.info(f"Loading OCS data from {excel_path}")
        
        try:
            # Read both sheets
            master_df = pd.read_excel(excel_path, sheet_name='MasterCatalogue')
            logger.info(f"Loaded {len(master_df)} products from MasterCatalogue")
            
            # Process the data
            processed_products = self.process_product_data(master_df)
            
            # Insert into database
            if processed_products:
                self.insert_products(processed_products)
                
                # Update statistics
                cursor = self.conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM cannabis_data.products WHERE is_active = true")
                active_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT category) FROM cannabis_data.products WHERE is_active = true")
                category_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT brand) FROM cannabis_data.products WHERE is_active = true")
                brand_count = cursor.fetchone()[0]
                
                cursor.close()
                
                logger.info(f"Data loading complete:")
                logger.info(f"  - Total active products: {active_count}")
                logger.info(f"  - Categories: {category_count}")
                logger.info(f"  - Brands: {brand_count}")
            
        except Exception as e:
            logger.error(f"Failed to load OCS data: {e}")
            raise
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate a summary report of loaded data"""
        try:
            cursor = self.conn.cursor()
            
            # Basic statistics
            cursor.execute("SELECT COUNT(*) FROM cannabis_data.products WHERE is_active = true")
            total_products = cursor.fetchone()[0]
            
            # Category breakdown
            cursor.execute("""
                SELECT category, sub_category, COUNT(*) as count
                FROM cannabis_data.products 
                WHERE is_active = true
                GROUP BY category, sub_category
                ORDER BY category, count DESC
            """)
            categories = cursor.fetchall()
            
            # Brand breakdown (top 10)
            cursor.execute("""
                SELECT brand, COUNT(*) as count
                FROM cannabis_data.products 
                WHERE is_active = true
                GROUP BY brand
                ORDER BY count DESC
                LIMIT 10
            """)
            top_brands = cursor.fetchall()
            
            # THC/CBD statistics
            cursor.execute("""
                SELECT 
                    AVG(thc_min_percent) as avg_thc_min,
                    AVG(thc_max_percent) as avg_thc_max,
                    AVG(cbd_min_percent) as avg_cbd_min,
                    AVG(cbd_max_percent) as avg_cbd_max
                FROM cannabis_data.products 
                WHERE is_active = true
            """)
            thc_cbd_stats = cursor.fetchone()
            
            cursor.close()
            
            report = {
                'total_products': total_products,
                'categories': [{'category': c[0], 'sub_category': c[1], 'count': c[2]} for c in categories],
                'top_brands': [{'brand': b[0], 'count': b[1]} for b in top_brands],
                'thc_cbd_averages': {
                    'avg_thc_min': float(thc_cbd_stats[0]) if thc_cbd_stats[0] else 0,
                    'avg_thc_max': float(thc_cbd_stats[1]) if thc_cbd_stats[1] else 0,
                    'avg_cbd_min': float(thc_cbd_stats[2]) if thc_cbd_stats[2] else 0,
                    'avg_cbd_max': float(thc_cbd_stats[3]) if thc_cbd_stats[3] else 0,
                },
                'generated_at': datetime.now().isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate summary report: {e}")
            return {}

def main():
    """Main function"""
    # Database configuration
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'ai_engine'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres'),
    }
    
    # File paths
    project_root = Path(__file__).parent.parent
    excel_path = project_root / "data" / "datasets" / "OCS_Catalogue_31_Jul_2025_226PM.xlsx"
    output_dir = project_root / "data" / "pipeline"
    
    if not excel_path.exists():
        logger.error(f"Excel file not found: {excel_path}")
        sys.exit(1)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process the data
    processor = OCSDataProcessor(db_config)
    
    try:
        processor.connect_db()
        processor.load_ocs_data(str(excel_path))
        
        # Generate summary report
        report = processor.generate_summary_report()
        if report:
            with open(output_dir / "data_load_summary.json", "w") as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info("Summary report saved to data_load_summary.json")
            
            # Print summary
            print("\n=== OCS Data Loading Summary ===")
            print(f"Total products loaded: {report['total_products']}")
            print(f"\nTop categories:")
            for cat in report['categories'][:10]:
                print(f"  {cat['category']} > {cat['sub_category']}: {cat['count']} products")
            
            print(f"\nTop brands:")
            for brand in report['top_brands']:
                print(f"  {brand['brand']}: {brand['count']} products")
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        sys.exit(1)
    finally:
        processor.disconnect_db()
    
    logger.info("OCS data processing completed successfully!")

if __name__ == "__main__":
    main()