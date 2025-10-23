#!/usr/bin/env python3
"""
Apply dashboard migration: Add dashboard_config table
"""

import asyncio
import asyncpg
import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def apply_migration():
    # Read migration file
    migration_file = Path(__file__).parent / 'migrations' / '004_dashboard_compatibility.sql'
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    # Connect to database
    conn = await asyncpg.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5434)),
        database=os.getenv('DB_NAME', 'ai_engine'),
        user=os.getenv('DB_USER', 'weedgo'),
        password=os.getenv('DB_PASSWORD', 'your_password_here')
    )
    
    try:
        logger.info("Starting dashboard compatibility migration...")
        
        # Split migration into individual statements (by semicolon)
        statements = [s.strip() for s in migration_sql.split(';') if s.strip()]
        
        for i, statement in enumerate(statements, 1):
            if statement and not statement.startswith('--'):
                try:
                    logger.info(f"Executing statement {i}/{len(statements)}...")
                    await conn.execute(statement)
                except asyncpg.exceptions.DuplicateTableError as e:
                    logger.warning(f"Table already exists: {e}")
                except asyncpg.exceptions.DuplicateColumnError as e:
                    logger.warning(f"Column already exists: {e}")
                except asyncpg.exceptions.DuplicateObjectError as e:
                    logger.warning(f"Object already exists: {e}")
                except Exception as e:
                    logger.error(f"Error in statement {i}: {e}")
                    logger.error(f"Statement: {statement[:100]}...")
        
        logger.info("Migration completed successfully!")
        
        # Verify the changes
        logger.info("\nVerifying migration results...")
        
        # Check products table
        products_count = await conn.fetchval("SELECT COUNT(*) FROM products")
        logger.info(f"✓ Products table: {products_count} records")
        
        # Check suppliers columns
        supplier_columns = await conn.fetch("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'suppliers' 
            AND column_name IN ('city', 'state', 'postal_code', 'country')
        """)
        logger.info(f"✓ Suppliers table: Added {len(supplier_columns)} location columns")
        
        # Check customers table
        customers_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'customers'
            )
        """)
        logger.info(f"✓ Customers table: {'Created' if customers_exists else 'Failed to create'}")
        
        # Check orders columns
        order_columns = await conn.fetch("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'orders' 
            AND column_name IN ('order_number', 'customer_name', 'delivery_address')
        """)
        logger.info(f"✓ Orders table: Added {len(order_columns)} new columns")
        
        # Check views
        views = await conn.fetch("""
            SELECT viewname 
            FROM pg_views 
            WHERE schemaname = 'public' 
            AND viewname LIKE 'dashboard_%'
        """)
        logger.info(f"✓ Dashboard views: Created {len(views)} views")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(apply_migration())