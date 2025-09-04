import asyncpg
import asyncio

async def analyze_joints():
    conn = await asyncpg.connect(
        host='localhost',
        port=5434,
        database='ai_engine',
        user='weedgo',
        password='your_password_here'
    )
    
    # Count 1g pre-rolls grouped by plant type
    query = '''
        SELECT 
            plant_type,
            COUNT(*) as count
        FROM products
        WHERE sub_category = 'Pre-Rolls' 
          AND (size = '1x1g' OR size = '1g')
        GROUP BY plant_type
        ORDER BY count DESC
    '''
    
    results = await conn.fetch(query)
    
    print('1g Pre-Rolls (Joints) by Plant Type:')
    print('=====================================')
    total = 0
    for row in results:
        print(f'{row["plant_type"]}: {row["count"]} products')
        total += row["count"]
    print(f'\nTotal 1g pre-rolls: {total}')
    
    # Get some example products
    example_query = '''
        SELECT 
            product_name,
            brand,
            plant_type,
            size,
            thc_min_percent,
            thc_max_percent,
            unit_price
        FROM products
        WHERE sub_category = 'Pre-Rolls' 
          AND (size = '1x1g' OR size = '1g')
        ORDER BY RANDOM()
        LIMIT 5
    '''
    
    examples = await conn.fetch(example_query)
    
    print('\nExample 1g Pre-Rolls (what "joint" should return):')
    print('===================================================')
    for row in examples:
        print(f'• {row["product_name"]} by {row["brand"]}')
        print(f'  Type: {row["plant_type"]} | Size: {row["size"]} | THC: {row["thc_min_percent"]}-{row["thc_max_percent"]}% | Price: ${row["unit_price"]}')
    
    await conn.close()

asyncio.run(analyze_joints())
