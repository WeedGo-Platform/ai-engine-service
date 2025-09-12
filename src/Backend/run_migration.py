#!/usr/bin/env python3
"""Run database migration"""

import asyncio
import asyncpg
import sys
from pathlib import Path

async def run_migration():
    # Read migration file
    migration_file = Path("migrations/011_inventory_movements.sql")
    if not migration_file.exists():
        print(f"Migration file not found: {migration_file}")
        return False
    
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    # Connect to database
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5434,
            database='ai_engine',
            user='weedgo',
            password='weedgo123'
        )
        
        print(f"Running migration: {migration_file}")
        
        # Execute migration
        await conn.execute(migration_sql)
        
        print("Migration completed successfully!")
        
        # Verify tables were created
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('inventory_movements', 'inventory_snapshots')
        """)
        
        print(f"Created tables: {[t['table_name'] for t in tables]}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"Error running migration: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_migration())
    sys.exit(0 if success else 1)
