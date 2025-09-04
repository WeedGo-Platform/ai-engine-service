#!/usr/bin/env python3
"""
Test script for Database-Connected Dispensary Search Tool
"""

import asyncio
import sys
import json
sys.path.append('.')

from services.tools.dispensary_tools_db import DispensarySearchToolDB, DispensaryStatsToolDB

async def test_product_search():
    """Test searching products in database"""
    print("\n=== Testing Database Product Search ===\n")
    
    # Database configuration
    db_config = {
        'connection_string': 'postgresql://weedgo:your_password_here@localhost:5434/ai_engine'
    }
    
    # Create search tool
    search_tool = DispensarySearchToolDB(db_config)
    
    # Test 1: Search by product name
    print("Test 1: Search for 'blue' products")
    result = await search_tool.execute(query="blue", limit=5)
    if result.success:
        print(f"Found {len(result.data)} products:")
        for product in result.data[:3]:
            print(f"  - {product['name']} ({product['brand']}) - ${product['price']}")
    else:
        print(f"Error: {result.error}")
    
    print("\n" + "-"*50 + "\n")
    
    # Test 2: Search by brand
    print("Test 2: Search for DIVVY brand products")
    result = await search_tool.execute(query="*", brand="DIVVY", limit=5)
    if result.success:
        print(f"Found {len(result.data)} DIVVY products:")
        for product in result.data[:3]:
            print(f"  - {product['name']} - {product['category']} - ${product['price']}")
    else:
        print(f"Error: {result.error}")
    
    print("\n" + "-"*50 + "\n")
    
    # Test 3: Search by category and strain type
    print("Test 3: Search for Sativa flower products")
    result = await search_tool.execute(
        query="*", 
        category="flower",
        strain_type="Sativa",
        limit=5
    )
    if result.success:
        print(f"Found {len(result.data)} Sativa flower products:")
        for product in result.data[:3]:
            print(f"  - {product['name']} - THC: {product['thc_level']}% - ${product['price']}")
    else:
        print(f"Error: {result.error}")
    
    print("\n" + "-"*50 + "\n")
    
    # Test 4: Search with price range
    print("Test 4: Search for products between $20-$50")
    result = await search_tool.execute(
        query="*",
        min_price=20,
        max_price=50,
        limit=5
    )
    if result.success:
        print(f"Found {len(result.data)} products in price range:")
        for product in result.data[:3]:
            print(f"  - {product['name']} - ${product['price']}")
    else:
        print(f"Error: {result.error}")
    
    print("\n" + "-"*50 + "\n")
    
    # Test 5: Complex search
    print("Test 5: Complex search - edibles under $30")
    result = await search_tool.execute(
        query="*",
        category="edibles",
        max_price=30,
        limit=10
    )
    if result.success:
        print(f"Found {len(result.data)} edibles under $30:")
        for product in result.data[:5]:
            print(f"  - {product['name']} ({product['brand']}) - ${product['price']}")
            if product['description']:
                print(f"    Description: {product['description'][:100]}")
    else:
        print(f"Error: {result.error}")
    
    # Close connection
    await search_tool.close()

async def test_product_stats():
    """Test getting product statistics"""
    print("\n=== Testing Product Statistics ===\n")
    
    # Database configuration
    db_config = {
        'connection_string': 'postgresql://weedgo:your_password_here@localhost:5434/ai_engine'
    }
    
    # Create stats tool
    stats_tool = DispensaryStatsToolDB(db_config)
    
    # Test 1: Category counts
    print("Test 1: Product counts by category")
    result = await stats_tool.execute(stat_type="category_counts")
    if result.success:
        print("Categories:")
        for stat in result.data[:5]:
            print(f"  - {stat['category']}: {stat['count']} products")
    else:
        print(f"Error: {result.error}")
    
    print("\n" + "-"*50 + "\n")
    
    # Test 2: Brand distribution
    print("Test 2: Top brands by product count")
    result = await stats_tool.execute(stat_type="brand_counts")
    if result.success:
        print("Top Brands:")
        for stat in result.data[:10]:
            print(f"  - {stat['brand']}: {stat['count']} products")
    else:
        print(f"Error: {result.error}")
    
    print("\n" + "-"*50 + "\n")
    
    # Test 3: Strain distribution
    print("Test 3: Products by strain type")
    result = await stats_tool.execute(stat_type="strain_distribution")
    if result.success:
        print("Strain Types:")
        for stat in result.data:
            print(f"  - {stat['strain_type']}: {stat['count']} products")
    else:
        print(f"Error: {result.error}")
    
    print("\n" + "-"*50 + "\n")
    
    # Test 4: Price ranges
    print("Test 4: Products by price range")
    result = await stats_tool.execute(stat_type="price_ranges")
    if result.success:
        print("Price Ranges:")
        for stat in result.data:
            print(f"  - {stat['price_range']}: {stat['count']} products")
    else:
        print(f"Error: {result.error}")
    
    # Close connection
    await stats_tool.close()

async def main():
    """Run all tests"""
    print("=" * 60)
    print("Database-Connected Dispensary Tool Test Suite")
    print("=" * 60)
    
    try:
        await test_product_search()
        await test_product_stats()
        
        print("\n" + "=" * 60)
        print("Test suite completed successfully!")
        print("=" * 60)
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())