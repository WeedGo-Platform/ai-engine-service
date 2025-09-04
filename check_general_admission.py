#!/usr/bin/env python3
import asyncio
import asyncpg
import os

async def check_general_admission():
    db_pool = await asyncpg.create_pool(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5434)),
        database=os.getenv('DB_NAME', 'ai_engine'),
        user=os.getenv('DB_USER', 'weedgo'),
        password=os.getenv('DB_PASSWORD', 'weedgo123')
    )
    
    async with db_pool.acquire() as conn:
        # Check for General Admission brand
        print("=== General Admission Products ===")
        results = await conn.fetch("""
            SELECT product_name, brand, category, sub_category, sub_sub_category, size, unit_price
            FROM products 
            WHERE LOWER(brand) LIKE '%general%admission%'
            ORDER BY category, product_name
            LIMIT 20
        """)
        
        if results:
            for r in results:
                print(f"- {r['product_name']} | Brand: {r['brand']} | {r['category']}/{r['sub_category']} | Size: {r['size']} | ${r['unit_price']}")
        else:
            print("No General Admission products found")
        
        print("\n=== Infused Pre-Rolls (any brand) ===")
        results = await conn.fetch("""
            SELECT product_name, brand, category, sub_category, sub_sub_category, size, unit_price
            FROM products 
            WHERE LOWER(product_name) LIKE '%infused%' 
            AND (LOWER(sub_category) LIKE '%pre-roll%' OR LOWER(product_name) LIKE '%pre%roll%')
            ORDER BY brand, unit_price
            LIMIT 10
        """)
        
        if results:
            for r in results:
                print(f"- {r['product_name']} | Brand: {r['brand']} | {r['category']}/{r['sub_category']} | Size: {r['size']} | ${r['unit_price']}")
        else:
            print("No infused pre-rolls found")
            
        print("\n=== Search for 'General Admission' as brand or in product name ===")
        results = await conn.fetch("""
            SELECT DISTINCT brand, COUNT(*) as count
            FROM products
            WHERE LOWER(brand) LIKE '%general%' OR LOWER(brand) LIKE '%admission%'
               OR LOWER(product_name) LIKE '%general%admission%'
            GROUP BY brand
            ORDER BY count DESC
        """)
        
        if results:
            for r in results:
                print(f"Brand: {r['brand']} - {r['count']} products")
    
    await db_pool.close()

if __name__ == "__main__":
    asyncio.run(check_general_admission())