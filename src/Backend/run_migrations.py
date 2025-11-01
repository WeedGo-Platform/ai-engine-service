#!/usr/bin/env python3
"""
Run database migrations for WeedGo AI Engine
"""

import asyncio
import asyncpg
import os
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_migrations():
    """Run all SQL migrations in order"""
    
    # Database connection parameters
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5434)),
        'database': os.getenv('DB_NAME', 'ai_engine'),
        'user': os.getenv('DB_USER', 'weedgo'),
        'password': os.getenv('DB_PASSWORD', 'weedgo123')
    }
    
    try:
        # Connect to database
        logger.info(f"Connecting to database at {db_config['host']}:{db_config['port']}")
        conn = await asyncpg.connect(**db_config)
        
        # Get migration files
        migrations_dir = Path(__file__).parent / 'migrations'
        migration_files = sorted(migrations_dir.glob('*.sql'))
        
        logger.info(f"Found {len(migration_files)} migration files")
        
        # Run each migration
        for migration_file in migration_files:
            logger.info(f"Running migration: {migration_file.name}")
            
            with open(migration_file, 'r') as f:
                sql = f.read()
            
            try:
                # Execute migration
                await conn.execute(sql)
                logger.info(f"✅ Successfully ran {migration_file.name}")
            except asyncpg.exceptions.DuplicateTableError as e:
                logger.warning(f"Table already exists in {migration_file.name}: {e}")
            except asyncpg.exceptions.DuplicateObjectError as e:
                logger.warning(f"Object already exists in {migration_file.name}: {e}")
            except Exception as e:
                logger.error(f"❌ Error running {migration_file.name}: {e}")
                # Continue with other migrations
        
        # List all tables
        tables = await conn.fetch("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """)
        
        logger.info("\n📊 Database tables after migrations:")
        for table in tables:
            logger.info(f"  - {table['tablename']}")
        
        await conn.close()
        logger.info("\n✅ Migration process completed!")
        
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        logger.error("Make sure PostgreSQL is running and the database exists")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_migrations())