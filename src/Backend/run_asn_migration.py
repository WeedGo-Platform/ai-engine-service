#!/usr/bin/env python3
"""
Run the ASN (Advanced Shipping Notice) migration
"""

import asyncio
import asyncpg
import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_asn_migration():
    """Execute the ASN purchase order migration"""
    conn = None
    try:
        # Connect to database
        logger.info("Connecting to database...")
        conn = await asyncpg.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5434)),
            database=os.getenv('DB_NAME', 'ai_engine'),
            user=os.getenv('DB_USER', 'weedgo'),
            password=os.getenv('DB_PASSWORD', 'weedgo123')
        )
        
        # Read the migration file
        migration_file = Path(__file__).parent / 'migrations' / '006_asn_purchase_order_fields.sql'
        logger.info(f"Reading migration file: {migration_file.name}")
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        logger.info("Executing ASN purchase order migration...")
        
        # Execute the migration
        await conn.execute(migration_sql)
        
        logger.info("✓ Migration executed successfully!")
        
        # Verify the new columns
        logger.info("\nVerifying new columns in purchase_orders table...")
        
        po_columns = await conn.fetch("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'purchase_orders'
            AND column_name IN ('shipment_id', 'container_id', 'vendor')
            ORDER BY column_name
        """)
        
        if po_columns:
            logger.info(f"✓ Added {len(po_columns)} new columns to purchase_orders")
            for col in po_columns:
                logger.info(f"  - {col['column_name']}: {col['data_type']}")
        
        poi_columns = await conn.fetch("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'purchase_order_items'
            AND column_name IN ('item_name', 'case_gtin', 'gtin_barcode', 'each_gtin', 
                              'shipped_qty', 'uom', 'uom_conversion', 'exists_in_inventory')
            ORDER BY column_name
        """)
        
        if poi_columns:
            logger.info(f"✓ Added {len(poi_columns)} new columns to purchase_order_items")
        
        # Check if staging table was created
        staging_exists = await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'asn_import_staging'
            )
        """)
        
        if staging_exists:
            logger.info("✓ ASN import staging table created")
        
        # Check if functions were created
        functions = await conn.fetch("""
            SELECT proname FROM pg_proc
            WHERE proname IN ('check_inventory_exists', 'process_asn_to_purchase_order', 'receive_purchase_order')
        """)
        
        if functions:
            logger.info(f"✓ Created {len(functions)} support functions")
            for func in functions:
                logger.info(f"  - {func['proname']}()")
        
        logger.info("\n✅ ASN purchase order migration completed successfully!")
        logger.info("The system now supports importing ASN Excel files with all required columns.")
        
    except FileNotFoundError as e:
        logger.error(f"Migration file not found: {e}")
        return False
    except asyncpg.PostgresError as e:
        logger.error(f"Database error: {e}")
        logger.error("The migration may have already been applied or there's a conflict.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False
    finally:
        if conn:
            await conn.close()
    
    return True

if __name__ == "__main__":
    success = asyncio.run(run_asn_migration())
    exit(0 if success else 1)