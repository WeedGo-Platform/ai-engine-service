#!/usr/bin/env python3
"""
Test the LLM Search Extractor deployment
"""
import asyncio
import json
import logging
import sys
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test queries covering various scenarios
TEST_QUERIES = [
    # Specific product searches
    {
        "query": "pink kush flower",
        "expected": {
            "product_name": "Pink Kush",
            "category": "Flower"
        },
        "description": "Specific product with category"
    },
    {
        "query": "I want pink kush dried flower in 14g",
        "expected": {
            "product_name": "Pink Kush",
            "category": "Flower",
            "sub_category": "Dried Flower",
            "size": "14g"
        },
        "description": "Specific product with size"
    },
    {
        "query": "half ounce of blue dream",
        "expected": {
            "product_name": "Blue Dream",
            "size": "14g"
        },
        "description": "Size conversion (half ounce → 14g)"
    },
    {
        "query": "show me pink kush pre-rolls",
        "expected": {
            "product_name": "Pink Kush",
            "category": "Flower",
            "sub_category": "Pre-Rolls"
        },
        "description": "Pre-rolls subcategory"
    },
    # Category searches
    {
        "query": "cheapest sativa edibles",
        "expected": {
            "category": "Edibles",
            "strain_type": "Sativa"
        },
        "description": "Category with strain type"
    },
    {
        "query": "show me all flower products",
        "expected": {
            "category": "Flower"
        },
        "description": "Category browse"
    },
    # Size specific
    {
        "query": "do you have any 14g options",
        "expected": {
            "size": "14g"
        },
        "description": "Size-specific search"
    },
    {
        "query": "I need an eighth",
        "expected": {
            "size": "3.5g"
        },
        "description": "Size conversion (eighth → 3.5g)"
    },
    # Strain type searches
    {
        "query": "give me a sativa",
        "expected": {
            "strain_type": "Sativa"
        },
        "description": "Strain type only"
    },
    {
        "query": "indica flower for sleep",
        "expected": {
            "strain_type": "Indica",
            "category": "Flower"
        },
        "description": "Strain with category"
    },
    # Price searches
    {
        "query": "flower under $20",
        "expected": {
            "category": "Flower",
            "max_price": 20
        },
        "description": "Price constraint"
    }
]

async def test_search_api(query: str, session_num: int):
    """Test search through the API"""
    import aiohttp
    
    url = "http://localhost:8080/api/v1/chat"
    payload = {
        "message": query,
        "session_id": f"test-session-{session_num}",
        "customer_id": "test-customer"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"API error: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Request failed: {e}")
        return None

async def test_direct_extraction():
    """Test extraction directly using the extractor"""
    try:
        # Import and initialize
        from services.smart_ai_engine_v3 import SmartAIEngineV3
        
        logger.info("Initializing Smart AI Engine V3...")
        engine = SmartAIEngineV3()
        await engine.initialize()
        
        if not engine.search_extractor:
            logger.error("Search extractor not initialized!")
            return
        
        logger.info("\n" + "="*60)
        logger.info("DIRECT EXTRACTION TESTS")
        logger.info("="*60 + "\n")
        
        for test in TEST_QUERIES:
            query = test["query"]
            expected = test["expected"]
            description = test["description"]
            
            logger.info(f"Test: {description}")
            logger.info(f"Query: '{query}'")
            
            # Extract criteria
            criteria = engine.search_extractor.extract_search_criteria(query)
            
            logger.info(f"Extracted: {json.dumps(criteria, indent=2)}")
            logger.info(f"Expected: {json.dumps(expected, indent=2)}")
            
            # Check matches
            matches = []
            mismatches = []
            for key, value in expected.items():
                if key in criteria and criteria[key] == value:
                    matches.append(key)
                else:
                    mismatches.append(f"{key}: got '{criteria.get(key)}', expected '{value}'")
            
            if mismatches:
                logger.warning(f"❌ Mismatches: {', '.join(mismatches)}")
            else:
                logger.info(f"✅ All expected fields match!")
            
            logger.info("-" * 40 + "\n")
            
    except Exception as e:
        logger.error(f"Direct extraction test failed: {e}")
        import traceback
        traceback.print_exc()

async def test_api_searches():
    """Test searches through the API"""
    logger.info("\n" + "="*60)
    logger.info("API SEARCH TESTS")
    logger.info("="*60 + "\n")
    
    for i, test in enumerate(TEST_QUERIES[:5]):  # Test first 5 through API
        query = test["query"]
        description = test["description"]
        
        logger.info(f"Test {i+1}: {description}")
        logger.info(f"Query: '{query}'")
        
        result = await test_search_api(query, i+1)
        
        if result:
            # Check products returned
            products = result.get("products", [])
            logger.info(f"Products found: {len(products)}")
            
            if products:
                # Show first 2 products
                for j, product in enumerate(products[:2]):
                    logger.info(f"  {j+1}. {product.get('product_name', 'Unknown')} - "
                              f"{product.get('size', '')} - "
                              f"${product.get('price', 0)}")
            
            # Show AI response
            message = result.get("message", "")
            if message:
                logger.info(f"AI Response: {message[:100]}...")
        else:
            logger.error("No response from API")
        
        logger.info("-" * 40 + "\n")
        
        # Small delay between requests
        await asyncio.sleep(1)

async def main():
    """Run all tests"""
    logger.info("Starting LLM Search Extractor Tests")
    logger.info(f"Time: {datetime.now()}")
    
    # Test 1: Direct extraction
    await test_direct_extraction()
    
    # Test 2: API searches
    await test_api_searches()
    
    logger.info("\nTests completed!")

if __name__ == "__main__":
    asyncio.run(main())