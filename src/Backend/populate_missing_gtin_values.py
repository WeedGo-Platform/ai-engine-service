#!/usr/bin/env python3
"""
Script to populate missing GTIN values in batch_tracking table
by retrieving them from purchase_order_items table
"""

import asyncio
import asyncpg
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def populate_gtin_values():
    """Update batch_tracking records with GTIN values from purchase_order_items"""
    conn = None
    try:
        # Connect to database
        logger.info("Connecting to database...")
        conn = await asyncpg.connect(
            host='localhost',
            port=5434,
            database='ai_engine',
            user='weedgo',
            password='your_password_here'
        )
        
        # First, check how many batch_tracking records have missing GTIN values
        count_missing = await conn.fetchval("""
            SELECT COUNT(*) 
            FROM batch_tracking 
            WHERE (case_gtin IS NULL OR case_gtin = '') 
               AND (gtin_barcode IS NULL OR gtin_barcode = '')
               AND (each_gtin IS NULL OR each_gtin = '')
        """)
        
        logger.info(f"Found {count_missing} batch_tracking records with missing GTIN values")
        
        if count_missing == 0:
            logger.info("No records need updating")
            return
        
        # Update batch_tracking with GTIN values from purchase_order_items
        # Join on purchase_order_id and sku
        update_query = """
            UPDATE batch_tracking bt
            SET 
                case_gtin = COALESCE(bt.case_gtin, poi.case_gtin),
                gtin_barcode = COALESCE(bt.gtin_barcode, poi.gtin_barcode),
                each_gtin = COALESCE(bt.each_gtin, poi.each_gtin)
            FROM purchase_order_items poi
            WHERE bt.purchase_order_id = poi.purchase_order_id
              AND bt.sku = poi.sku
              AND bt.batch_lot = poi.batch_lot
              AND (
                  (bt.case_gtin IS NULL OR bt.case_gtin = '') OR
                  (bt.gtin_barcode IS NULL OR bt.gtin_barcode = '') OR
                  (bt.each_gtin IS NULL OR bt.each_gtin = '')
              )
              AND (
                  poi.case_gtin IS NOT NULL OR
                  poi.gtin_barcode IS NOT NULL OR
                  poi.each_gtin IS NOT NULL
              )
            RETURNING bt.id, bt.sku, bt.batch_lot
        """
        
        updated_records = await conn.fetch(update_query)
        
        if updated_records:
            logger.info(f"Successfully updated {len(updated_records)} batch_tracking records with GTIN values")
            for record in updated_records[:5]:  # Show first 5 as examples
                logger.info(f"  - Updated SKU: {record['sku']}, Batch: {record['batch_lot']}")
            if len(updated_records) > 5:
                logger.info(f"  ... and {len(updated_records) - 5} more records")
        else:
            logger.info("No matching purchase_order_items found with GTIN values to update")
        
        # For records without matching purchase_order_items, try to get GTIN from products table
        # (if products table has GTIN columns)
        check_products_gtin = await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'products' 
                AND column_name IN ('case_gtin', 'gtin_barcode', 'each_gtin')
            )
        """)
        
        if check_products_gtin:
            logger.info("Checking products table for GTIN values...")
            
            update_from_products = """
                UPDATE batch_tracking bt
                SET 
                    case_gtin = COALESCE(bt.case_gtin, p.case_gtin),
                    gtin_barcode = COALESCE(bt.gtin_barcode, p.gtin_barcode),
                    each_gtin = COALESCE(bt.each_gtin, p.each_gtin)
                FROM products p
                WHERE bt.sku = p.sku
                  AND (
                      (bt.case_gtin IS NULL OR bt.case_gtin = '') OR
                      (bt.gtin_barcode IS NULL OR bt.gtin_barcode = '') OR
                      (bt.each_gtin IS NULL OR bt.each_gtin = '')
                  )
                  AND (
                      p.case_gtin IS NOT NULL OR
                      p.gtin_barcode IS NOT NULL OR
                      p.each_gtin IS NOT NULL
                  )
                RETURNING bt.id, bt.sku, bt.batch_lot
            """
            
            products_updated = await conn.fetch(update_from_products)
            
            if products_updated:
                logger.info(f"Updated {len(products_updated)} additional records from products table")
        
        # Final check
        remaining_missing = await conn.fetchval("""
            SELECT COUNT(*) 
            FROM batch_tracking 
            WHERE (case_gtin IS NULL OR case_gtin = '') 
               AND (gtin_barcode IS NULL OR gtin_barcode = '')
               AND (each_gtin IS NULL OR each_gtin = '')
        """)
        
        logger.info(f"\nFinal status: {remaining_missing} batch_tracking records still have no GTIN values")
        
        if remaining_missing > 0:
            # Show some examples of records still missing GTIN
            examples = await conn.fetch("""
                SELECT sku, batch_lot, purchase_order_id
                FROM batch_tracking 
                WHERE (case_gtin IS NULL OR case_gtin = '') 
                   AND (gtin_barcode IS NULL OR gtin_barcode = '')
                   AND (each_gtin IS NULL OR each_gtin = '')
                LIMIT 5
            """)
            
            logger.info("Examples of records still missing GTIN values:")
            for ex in examples:
                logger.info(f"  - SKU: {ex['sku']}, Batch: {ex['batch_lot']}, PO: {ex['purchase_order_id']}")
            
            logger.info("\nThese records may need GTIN values to be manually added or imported from external sources")
        
    except Exception as e:
        logger.error(f"Error updating GTIN values: {e}")
        return False
    finally:
        if conn:
            await conn.close()
    
    return True

if __name__ == "__main__":
    success = asyncio.run(populate_gtin_values())
    exit(0 if success else 1)