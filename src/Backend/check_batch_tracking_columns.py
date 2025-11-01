#!/usr/bin/env python3
import asyncio
import asyncpg
import os

async def check_columns():
    db_config = {
        'host': 'localhost',
        'port': 5434,
        'database': 'ai_engine',
        'user': 'weedgo',
        'password': 'weedgo123'
    }
    
    conn = await asyncpg.connect(**db_config)
    
    result = await conn.fetch("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'batch_tracking'
        ORDER BY ordinal_position;
    """)
    
    print("batch_tracking columns:")
    for row in result:
        print(f"  - {row['column_name']}: {row['data_type']}")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check_columns())
