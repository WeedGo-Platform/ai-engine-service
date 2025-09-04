#!/usr/bin/env python3
"""Test why Tiger Blood search isn't working"""

import logging
import asyncio
import os

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Set database environment
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5434'
os.environ['DB_NAME'] = 'ai_engine'
os.environ['DB_USER'] = 'weedgo'
os.environ['DB_PASSWORD'] = 'weedgo123'

async def test_tiger_blood():
    from services.smart_ai_engine_v3 import SmartAIEngineV3
    
    print("\n" + "="*60)
    print("TESTING TIGER BLOOD SEARCH")
    print("="*60)
    
    # Initialize engine
    engine = SmartAIEngineV3()
    await engine.initialize()
    
    # Test queries
    test_queries = [
        "do you have tiger blood?",
        "give me tiger blood",
        "I want tiger blood 1.5g",
        "search for tiger blood"
    ]
    
    for query in test_queries:
        print(f"\n--- Testing: '{query}' ---")
        
        result = await engine.process_message(
            query,
            'test-customer',
            f'test-session-{query[:10]}'
        )
        
        print(f"Stage: {result.get('stage')}")
        print(f"Confidence: {result.get('confidence')}")
        print(f"Message preview: {result.get('message', '')[:150]}...")
        print(f"Products found: {len(result.get('products', []))}")
        
        if result.get('products'):
            print("Products returned:")
            for p in result.get('products', [])[:3]:
                print(f"  - {p.get('product_name')} ({p.get('category')}): ${p.get('price')}")
        else:
            print("No products returned!")

if __name__ == "__main__":
    asyncio.run(test_tiger_blood())