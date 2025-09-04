#!/usr/bin/env python3
"""
Create conversation_messages table for storing chat history
"""

import asyncio
import asyncpg
import os
from datetime import datetime

async def create_conversation_messages_table():
    """Create the conversation_messages table"""
    
    # Database connection settings
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 5434))
    DB_NAME = os.environ.get('DB_NAME', 'ai_engine')
    DB_USER = os.environ.get('DB_USER', 'weedgo')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'your_password_here')
    
    try:
        # Connect to database
        conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        print(f"Connected to database: {DB_NAME}")
        
        # Create conversation_messages table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_messages (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL,
                customer_id VARCHAR(255),
                user_message TEXT,
                ai_response TEXT,
                intent VARCHAR(50),
                products_shown INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB
            );
        """)
        
        print("✅ Created conversation_messages table")
        
        # Create indexes separately for better performance
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversation_messages_session_id 
            ON conversation_messages(session_id);
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversation_messages_customer_id 
            ON conversation_messages(customer_id);
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversation_messages_created_at 
            ON conversation_messages(created_at);
        """)
        
        print("✅ Created indexes on conversation_messages table")
        
        # Also ensure conversation_context has last_selected_product column
        await conn.execute("""
            ALTER TABLE conversation_context 
            ADD COLUMN IF NOT EXISTS last_selected_product JSONB;
        """)
        
        await conn.execute("""
            ALTER TABLE conversation_context 
            ADD COLUMN IF NOT EXISTS last_action_product JSONB;
        """)
        
        print("✅ Updated conversation_context table with product tracking columns")
        
        # Create indexes for better performance
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversation_messages_session 
            ON conversation_messages(session_id, created_at DESC);
        """)
        
        print("✅ Created indexes for optimal performance")
        
        # Verify the table was created
        result = await conn.fetchval("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'conversation_messages'
        """)
        
        if result > 0:
            print(f"✅ Successfully verified conversation_messages table exists")
            
            # Get column info
            columns = await conn.fetch("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'conversation_messages'
                ORDER BY ordinal_position;
            """)
            
            print("\nTable structure:")
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']}")
        else:
            print("❌ Table creation may have failed")
        
        await conn.close()
        print("\n✅ Database setup complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(create_conversation_messages_table())