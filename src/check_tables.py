#!/usr/bin/env python3
import asyncio
import asyncpg

async def check_tables():
    conn = await asyncpg.connect(
        host='localhost',
        port=5434,
        database='ai_engine',
        user='weedgo',
        password='your_password_here'
    )
    
    # Get all tables
    tables = await conn.fetch("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
    """)
    
    print("Tables in database:")
    for table in tables:
        print(f"  - {table['table_name']}")
    
    # Check suppliers table structure
    print("\nSuppliers table columns:")
    columns = await conn.fetch("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'suppliers' 
        ORDER BY ordinal_position
    """)
    
    for col in columns:
        print(f"  - {col['column_name']}: {col['data_type']}")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check_tables())