#!/usr/bin/env python3
"""
Apply database migrations for the AI engine
"""

import asyncio
import asyncpg
import os
from pathlib import Path

async def apply_migrations():
    """Apply all SQL migrations"""
    
    # Database connection
    conn = await asyncpg.connect(
        host='localhost',
        port=5434,
        database='ai_engine',
        user='weedgo',
        password='weedgo123'
    )
    
    migrations_dir = Path("data/migrations")
    
    # List of migrations to apply
    migrations = [
        "009_create_model_versioning_tables.sql"
    ]
    
    for migration in migrations:
        migration_file = migrations_dir / migration
        
        if migration_file.exists():
            print(f"Applying migration: {migration}")
            
            with open(migration_file, 'r') as f:
                sql = f.read()
            
            try:
                await conn.execute(sql)
                print(f"✅ Successfully applied: {migration}")
            except asyncpg.exceptions.DuplicateTableError:
                print(f"⚠️  Tables already exist in: {migration}")
            except Exception as e:
                print(f"❌ Failed to apply {migration}: {e}")
        else:
            print(f"❌ Migration file not found: {migration_file}")
    
    await conn.close()
    print("\n✅ Migration process complete")

if __name__ == "__main__":
    asyncio.run(apply_migrations())