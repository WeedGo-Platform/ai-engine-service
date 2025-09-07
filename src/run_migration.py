#!/usr/bin/env python3
"""
Run database migration for authentication tables
"""

import asyncio
import asyncpg
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_migration():
    """Execute the auth tables migration"""
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
        
        # Read migration files
        logger.info("Reading migration files...")
        migrations = [
            'migrations/002_create_auth_tables.sql',
            'migrations/003_create_otp_tables.sql'
        ]
        
        for migration_file in migrations:
            try:
                with open(migration_file, 'r') as f:
                    migration_sql = f.read()
                logger.info(f"Executing {migration_file}...")
                await conn.execute(migration_sql)
                logger.info(f"Successfully executed {migration_file}")
            except FileNotFoundError:
                logger.warning(f"Migration file not found: {migration_file}")
                continue
            except Exception as e:
                logger.warning(f"Migration {migration_file} may have already been applied: {e}")
                continue
        
        # Execute migration
        logger.info("Executing migration...")
        await conn.execute(migration_sql)
        
        # Verify tables were created
        logger.info("Verifying tables...")
        tables = await conn.fetch("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename IN ('users', 'user_profiles', 'cart_sessions', 'orders', 'conversion_metrics')
            ORDER BY tablename
        """)
        
        logger.info(f"Created tables: {[t['tablename'] for t in tables]}")
        
        # Check if users table has records
        count = await conn.fetchval("SELECT COUNT(*) FROM users")
        logger.info(f"Users table has {count} records")
        
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        if conn:
            await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migration())