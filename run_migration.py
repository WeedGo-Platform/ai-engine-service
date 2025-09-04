#!/usr/bin/env python3
"""Run multilingual tables migration"""

import asyncio
import asyncpg
import os

async def run_migration():
    # Connect to the database
    conn = await asyncpg.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5434)),
        database=os.getenv('DB_NAME', 'ai_engine'),
        user=os.getenv('DB_USER', 'weedgo'),
        password=os.getenv('DB_PASSWORD', 'your_password_here')
    )
    
    try:
        # Read the migration file
        with open('migrations/create_multilingual_tables.sql', 'r') as f:
            sql = f.read()
        
        # Split SQL into individual statements
        statements = [s.strip() for s in sql.split(';') if s.strip()]
        
        for stmt in statements:
            if stmt:
                try:
                    await conn.execute(stmt + ';')
                except Exception as e:
                    print(f"Warning: {str(e)[:100]}")
        
        print("✅ Migration completed!")
        
        # Verify tables were created
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN (
                'customer_language_preferences',
                'translation_cache',
                'cannabis_terminology',
                'multilingual_products',
                'multilingual_conversations',
                'language_quality_metrics'
            )
            ORDER BY table_name
        """)
        
        print("\nCreated tables:")
        for table in tables:
            print(f"  - {table['table_name']}")
        
        # Check cannabis terminology entries
        terms = await conn.fetch("SELECT COUNT(*) as count FROM cannabis_terminology")
        print(f"\nInserted {terms[0]['count']} cannabis terminology entries")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
