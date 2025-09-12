#!/usr/bin/env python3
import asyncio
import asyncpg
import os

async def check_images():
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5434)),
        'database': os.getenv('DB_NAME', 'ai_engine'),
        'user': os.getenv('DB_USER', 'weedgo'),
        'password': os.getenv('DB_PASSWORD', 'your_password_here')
    }
    
    try:
        conn = await asyncpg.connect(**db_config)
        
        # Check total products and products with images
        result = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN image_url IS NOT NULL AND image_url != '' THEN 1 END) as with_image
            FROM product_catalog
        """)
        
        print(f"Total products: {result['total']}")
        print(f"Products with images: {result['with_image']}")
        
        # Get a few sample products with images
        samples = await conn.fetch("""
            SELECT ocs_variant_number, product_name, image_url
            FROM product_catalog
            WHERE image_url IS NOT NULL AND image_url != ''
            LIMIT 5
        """)
        
        if samples:
            print("\nSample products with images:")
            for row in samples:
                print(f"  SKU: {row['ocs_variant_number']}")
                print(f"  Name: {row['product_name']}")
                print(f"  Image: {row['image_url']}")
                print()
        
        # Test the case-insensitive match
        test_sku = "106745_10X0.35G___"  # Example SKU from your screenshot
        test_result = await conn.fetchrow("""
            SELECT 
                pc.product_name,
                pc.image_url,
                pc.category,
                pc.brand,
                pc.unit_price as retail_price
            FROM product_catalog pc
            WHERE LOWER(TRIM(pc.ocs_variant_number)) = LOWER(TRIM($1))
            LIMIT 1
        """, test_sku)
        
        if test_result:
            print(f"\nTest SKU '{test_sku}' found:")
            print(f"  Name: {test_result['product_name']}")
            print(f"  Image: {test_result['image_url']}")
            print(f"  Category: {test_result['category']}")
            print(f"  Brand: {test_result['brand']}")
            print(f"  Retail Price: {test_result['retail_price']}")
        else:
            print(f"\nTest SKU '{test_sku}' not found")
        
        await conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_images())