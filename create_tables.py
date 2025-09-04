#!/usr/bin/env python3
"""Create necessary database tables for AI Engine"""

import asyncio
import asyncpg
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_tables():
    """Create the chat_interactions table"""
    
    # Database connection
    conn = await asyncpg.connect(
        host='localhost',
        port=5434,
        user='weedgo',
        password='weedgo123',
        database='ai_engine'
    )
    
    try:
        # Create chat_interactions table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_interactions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL,
                message_id VARCHAR(255) UNIQUE NOT NULL,
                customer_id VARCHAR(255),
                user_message TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                service_used VARCHAR(50),
                response_time VARCHAR(20),
                intent VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB
            )
        """)
        logger.info("✅ Created chat_interactions table")
        
        # Create indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_customer ON chat_interactions(customer_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_interactions(session_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_created ON chat_interactions(created_at DESC)")
        logger.info("✅ Created indexes")
        
        # Create analytics_events table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS analytics_events (
                id SERIAL PRIMARY KEY,
                event_type VARCHAR(100) NOT NULL,
                customer_id VARCHAR(255),
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("✅ Created analytics_events table")
        
        # Create customers table if not exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id VARCHAR(255) PRIMARY KEY,
                preferences JSONB,
                medical_conditions TEXT[],
                purchase_history TEXT[],
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("✅ Created customers table")
        
        # Insert sample data for testing
        await conn.execute("""
            INSERT INTO customers (customer_id, preferences, medical_conditions, purchase_history)
            VALUES ('0001', '{"thc_tolerance": "medium", "methods": ["flower", "edibles"]}', 
                    ARRAY['anxiety', 'insomnia'], ARRAY['Blue Dream', 'OG Kush'])
            ON CONFLICT (customer_id) DO NOTHING
        """)
        logger.info("✅ Added sample customer")
        
    finally:
        await conn.close()
        logger.info("Database setup complete!")

if __name__ == "__main__":
    asyncio.run(create_tables())