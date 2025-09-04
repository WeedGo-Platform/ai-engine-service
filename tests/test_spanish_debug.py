#!/usr/bin/env python3
"""
Debug Spanish processing
"""

import asyncio
import sys
sys.path.append('/Users/charrcy/projects/WeedGo/microservices/ai-engine-service')

from services.smart_multilingual_engine import SmartMultilingualEngine
import asyncpg

async def test_spanish():
    # Connect to database
    db_pool = await asyncpg.create_pool(
        host='localhost',
        port=5434,
        database='ai_engine',
        user='ai_user',
        password='ai_password'
    )
    
    # Create engine
    engine = SmartMultilingualEngine(db_pool)
    await engine.initialize()
    
    # Test Spanish greeting
    print("Testing Spanish greeting...")
    result = await engine._process_tier_1_message(
        message="hola",
        language="es",
        session_id="test_debug",
        customer_id="test_user"
    )
    
    print(f"Result: {result}")
    print(f"Message: {result.get('message')}")
    print(f"Language: {result.get('response_language')}")
    
    await db_pool.close()

if __name__ == "__main__":
    asyncio.run(test_spanish())