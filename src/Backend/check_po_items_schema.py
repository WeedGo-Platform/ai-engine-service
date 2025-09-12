#!/usr/bin/env python3
"""Check purchase_order_items table schema"""

import asyncio
import asyncpg
import os

async def check_schema():
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5434)),
        'database': os.getenv('DB_NAME', 'ai_engine'),
        'user': os.getenv('DB_USER', 'weedgo'),
        'password': os.getenv('DB_PASSWORD', 'weedgo123')
    }
    
    try:
        conn = await asyncpg.connect(**db_config)
        
        # Check purchase_order_items columns
        result = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'purchase_order_items'
            ORDER BY ordinal_position;
        """)
        
        print("Purchase Order Items table columns:")
        for row in result:
            print(f"  - {row['column_name']}: {row['data_type']} (nullable: {row['is_nullable']})")
        
        await conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_schema())
