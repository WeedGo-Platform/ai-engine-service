import asyncpg
import asyncio

async def check_columns():
    conn = await asyncpg.connect(
        host='localhost',
        port=5434,
        database='ai_engine',
        user='weedgo',
        password='weedgo123'
    )
    
    # Get column names
    query = '''
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'products'
        ORDER BY ordinal_position
    '''
    
    columns = await conn.fetch(query)
    
    print('Columns in products table:')
    print('=========================')
    for row in columns:
        print(f'- {row["column_name"]}')
    
    # Get sample products with 1g size
    sample_query = '''
        SELECT *
        FROM products
        WHERE size = '1g' AND sub_category = 'Pre-Rolls'
        LIMIT 3
    '''
    
    samples = await conn.fetch(sample_query)
    print(f'\nFound {len(samples)} Pre-Roll products with size 1g')
    
    if samples:
        print('\nSample pre-roll product:')
        print('========================')
        for key, value in dict(samples[0]).items():
            print(f'{key}: {value}')
    
    await conn.close()

asyncio.run(check_columns())
