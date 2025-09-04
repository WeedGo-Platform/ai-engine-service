"""
Create conversation context table for session persistence
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def create_tables():
    # Database connection parameters
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 5434))
    DB_NAME = os.getenv('DB_NAME', 'ai_engine')
    DB_USER = os.getenv('DB_USER', 'weedgo')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'your_password_here')
    
    print(f"Connecting to database {DB_NAME} at {DB_HOST}:{DB_PORT}...")
    
    # Connect to database
    conn = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    
    try:
        # Create conversation_context table
        print("Creating conversation_context table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_context (
                session_id VARCHAR(255) PRIMARY KEY,
                customer_id VARCHAR(255),
                last_products_shown JSONB,
                last_intent VARCHAR(50),
                user_preferences JSONB,
                last_search_criteria JSONB,
                current_cart JSONB,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ Table conversation_context created")
        
        # Create index for customer lookups
        print("Creating indexes...")
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversation_context_customer 
            ON conversation_context(customer_id)
        """)
        print("✓ Index on customer_id created")
        
        # Add columns to conversation_messages if table exists
        try:
            await conn.execute("""
                ALTER TABLE conversation_messages 
                ADD COLUMN IF NOT EXISTS products_shown JSONB,
                ADD COLUMN IF NOT EXISTS intent_type VARCHAR(50),
                ADD COLUMN IF NOT EXISTS referenced_products JSONB
            """)
            print("✓ Updated conversation_messages table")
        except Exception as e:
            print(f"Note: Could not update conversation_messages table: {e}")
        
        # Create index for session lookups
        try:
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversation_messages_session 
                ON conversation_messages(session_id, created_at DESC)
            """)
            print("✓ Index on conversation_messages created")
        except Exception as e:
            print(f"Note: Could not create index on conversation_messages: {e}")
        
        # Check if table was created successfully
        result = await conn.fetchval("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'conversation_context'
        """)
        
        if result > 0:
            print("\n✅ Migration completed successfully!")
            
            # Show table structure
            columns = await conn.fetch("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'conversation_context'
                ORDER BY ordinal_position
            """)
            
            print("\nTable structure:")
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']}")
                
            # Check if any data exists
            count = await conn.fetchval("SELECT COUNT(*) FROM conversation_context")
            print(f"\nCurrent records in table: {count}")
        else:
            print("\n❌ Migration failed - table not created")
            
    except Exception as e:
        print(f"Error during migration: {e}")
        raise
            
    finally:
        await conn.close()
        print("\nDatabase connection closed")

if __name__ == "__main__":
    asyncio.run(create_tables())