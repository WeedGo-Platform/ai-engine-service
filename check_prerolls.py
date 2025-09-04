import asyncpg
import asyncio
import json

async def check_products():
    conn = await asyncpg.connect(
        host='localhost',
        port=5434,
        database='ai_engine',
        user='weedgo',
        password='your_password_here'
    )
    
    # Check for pre-rolls
    query = '''
        SELECT DISTINCT 
            sub_category,
            size,
            plant_type,
            COUNT(*) as count
        FROM products
        WHERE LOWER(sub_category) LIKE '%pre%roll%'
           OR LOWER(sub_category) LIKE '%joint%'
           OR size = '1g'
        GROUP BY sub_category, size, plant_type
        ORDER BY count DESC
        LIMIT 20
    '''
    
    results = await conn.fetch(query)
    
    print('Pre-roll/Joint/1g products in database:')
    print('========================================')
    for row in results:
        print(f'Sub-category: {row["sub_category"]}, Size: {row["size"]}, Plant Type: {row["plant_type"]}, Count: {row["count"]}')
    
    # Check what plant types we have for 1g products
    plant_type_query = '''
        SELECT plant_type, COUNT(*) as count
        FROM products
        WHERE size = '1g' 
        GROUP BY plant_type
        ORDER BY count DESC
    '''
    
    plant_types = await conn.fetch(plant_type_query)
    print('\nPlant types for 1g products:')
    print('============================')
    for row in plant_types:
        print(f'{row["plant_type"]}: {row["count"]} products')
    
    # Get sample 1g products
    sample_query = '''
        SELECT name, sub_category, size, plant_type, price, brand
        FROM products
        WHERE size = '1g' 
        LIMIT 10
    '''
    
    samples = await conn.fetch(sample_query)
    print('\nSample 1g products (these are what "joint" should return):')
    print('==========================================================')
    for row in samples:
        print(f'- {row["name"]} | Brand: {row["brand"]} | {row["sub_category"]} | {row["size"]} | {row["plant_type"]} | ${row["price"]}')
    
    await conn.close()

asyncio.run(check_products())
