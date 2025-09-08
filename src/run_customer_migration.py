#!/usr/bin/env python3
"""
Run specific migration to resolve customer table conflict
"""

import asyncio
import asyncpg
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_customer_migration():
    """Execute the customer conflict resolution migration"""
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
        
        # Read the specific migration file
        migration_file = Path(__file__).parent / 'migrations' / '005_resolve_customer_conflict.sql'
        logger.info(f"Reading migration file: {migration_file.name}")
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        logger.info("Executing customer conflict resolution migration...")
        
        # Execute the migration in a transaction
        async with conn.transaction():
            await conn.execute(migration_sql)
        
        logger.info("✓ Migration executed successfully!")
        
        # Verify the new table structure
        logger.info("\nVerifying new customers table structure...")
        
        # Check if customers table exists with correct structure
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'customers'
            ORDER BY ordinal_position
        """)
        
        logger.info(f"Customers table has {len(columns)} columns")
        
        # Check for user_id foreign key
        fk_check = await conn.fetchval("""
            SELECT COUNT(*)
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = 'customers'
                AND tc.constraint_type = 'FOREIGN KEY'
                AND kcu.column_name = 'user_id'
        """)
        
        if fk_check > 0:
            logger.info("✓ Foreign key relationship to users table established")
        else:
            logger.warning("⚠ No foreign key found for user_id")
        
        # Check for customer_details view
        view_exists = await conn.fetchval("""
            SELECT COUNT(*)
            FROM information_schema.views
            WHERE table_name = 'customer_details'
        """)
        
        if view_exists:
            logger.info("✓ customer_details view created")
        
        # Check trigger
        trigger_exists = await conn.fetchval("""
            SELECT COUNT(*)
            FROM pg_trigger
            WHERE tgname = 'create_customer_on_user_insert'
        """)
        
        if trigger_exists:
            logger.info("✓ Auto-create customer trigger installed")
        
        # Show record counts
        user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
        customer_count = await conn.fetchval("SELECT COUNT(*) FROM customers")
        
        logger.info(f"\nRecord counts:")
        logger.info(f"  Users: {user_count}")
        logger.info(f"  Customers: {customer_count}")
        
        logger.info("\n✅ Customer table conflict resolved successfully!")
        logger.info("The customers table now properly links to the users table.")
        
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
    success = asyncio.run(run_customer_migration())
    exit(0 if success else 1)