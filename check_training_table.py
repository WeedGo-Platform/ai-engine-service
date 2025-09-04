import asyncpg
import asyncio

async def check():
    conn = await asyncpg.connect(
        host='localhost',
        port=5434,
        database='ai_engine',
        user='weedgo',
        password='weedgo123'
    )
    
    # Check if training_examples table exists
    query = '''
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'training_examples'
        ORDER BY ordinal_position
    '''
    
    columns = await conn.fetch(query)
    
    if columns:
        print('Columns in training_examples table:')
        print('=====================================')
        for col in columns:
            print(f'- {col["column_name"]}')
    else:
        print('training_examples table not found!')
        
        # Create the table
        print('\nCreating training_examples table...')
        create_query = '''
            CREATE TABLE IF NOT EXISTS training_examples (
                id SERIAL PRIMARY KEY,
                user_input TEXT NOT NULL,
                ideal_response TEXT NOT NULL,
                intent VARCHAR(255),
                context_required BOOLEAN DEFAULT false,
                confidence FLOAT DEFAULT 0.95,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''
        await conn.execute(create_query)
        print('✅ Table created successfully!')
    
    await conn.close()

asyncio.run(check())
