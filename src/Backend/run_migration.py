#!/usr/bin/env python3
"""Run database migration"""

import asyncio
import asyncpg
import os
import sys
from pathlib import Path

async def run_migration():
    # Read migration file
    migration_file = Path("migrations/001_ocs_integration_schema.sql")
    if not migration_file.exists():
        print(f"Migration file not found: {migration_file}")
        return False
    
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    # Connect to database
    try:
        conn = await asyncpg.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5434)),
            database=os.getenv('DB_NAME', 'ai_engine'),
            user=os.getenv('DB_USER', 'weedgo'),
            password=os.getenv('DB_PASSWORD', 'your_password_here')
        )
        
        print(f"Running migration: {migration_file}")
        
        # Execute migration
        await conn.execute(migration_sql)
        
        print("✅ Migration completed successfully!")
        
        # Verify tables were created
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'ocs_%'
            ORDER BY table_name
        """)
        
        print(f"\n✅ Created OCS tables ({len(tables)}):")
        for t in tables:
            print(f"   - {t['table_name']}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"Error running migration: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_migration())
    sys.exit(0 if success else 1)
