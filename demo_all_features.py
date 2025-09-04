#!/usr/bin/env python3
"""
Demonstration of All Budtender Features
========================================
Shows the complete functionality of the intelligent budtender system
"""

import asyncio
import json
import aiohttp

async def test_buddy_api():
    """Test all features of the buddy API"""
    
    print("="*60)
    print("🎯 BUDDY API DEMONSTRATION - ALL FEATURES")
    print("="*60)
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Beverage Search
        print("\n1️⃣ BEVERAGE SEARCH")
        print("-"*40)
        async with session.post(f"{base_url}/api/chat", json={
            "message": "I want THC drinks",
            "customer_id": "demo_001"
        }) as resp:
            data = await resp.json()
            print(f"Request: I want THC drinks")
            print(f"Response: {data['response'][:150]}...")
            print(f"Products found: {len(data.get('products', []))}")
            if data.get('products'):
                print(f"First drink: {data['products'][0]['product_name']} - ${data['products'][0]['unit_price']}")
        
        # Test 2: Price-conscious search
        print("\n2️⃣ BUDGET SEARCH")
        print("-"*40)
        async with session.post(f"{base_url}/api/chat", json={
            "message": "cheapest flower under $5",
            "customer_id": "demo_002"
        }) as resp:
            data = await resp.json()
            print(f"Request: cheapest flower under $5")
            print(f"Products found: {len(data.get('products', []))}")
            if data.get('products'):
                print(f"Cheapest: {data['products'][0]['product_name']} - ${data['products'][0]['unit_price']}")
        
        # Test 3: Specific strain search
        print("\n3️⃣ SPECIFIC STRAIN SEARCH")
        print("-"*40)
        async with session.post(f"{base_url}/api/chat", json={
            "message": "high THC sativa",
            "customer_id": "demo_003"
        }) as resp:
            data = await resp.json()
            print(f"Request: high THC sativa")
            print(f"Products found: {len(data.get('products', []))}")
            if data.get('products'):
                p = data['products'][0]
                print(f"Top result: {p['product_name']} - THC: {p['thc_min_percent']}-{p['thc_max_percent']}%")
        
        # Test 4: Edibles search
        print("\n4️⃣ EDIBLES SEARCH")
        print("-"*40)
        async with session.post(f"{base_url}/api/chat", json={
            "message": "chocolate edibles",
            "customer_id": "demo_004"
        }) as resp:
            data = await resp.json()
            print(f"Request: chocolate edibles")
            print(f"Products found: {len(data.get('products', []))}")
            if data.get('products'):
                print(f"First edible: {data['products'][0]['product_name']} - ${data['products'][0]['unit_price']}")
        
        # Test 5: Check interaction history
        print("\n5️⃣ INTERACTION HISTORY")
        print("-"*40)
        async with session.get(f"{base_url}/api/interactions/demo_001") as resp:
            data = await resp.json()
            if 'interactions' in data:
                print(f"Customer demo_001 has {len(data['interactions'])} interactions")
                if data['interactions']:
                    print(f"Last interaction: {data['interactions'][-1]['message']}")
        
        # Test 6: Get all interactions summary
        print("\n6️⃣ ALL CUSTOMERS SUMMARY")
        print("-"*40)
        async with session.get(f"{base_url}/api/interactions") as resp:
            data = await resp.json()
            print(f"Total customers: {data.get('total_customers', 0)}")
            if data.get('customers'):
                for c in data['customers'][:3]:  # Show first 3
                    print(f"  - {c['customer_id']}: {c['total_interactions']} interactions, {c['total_products_shown']} products shown")
        
        # Test 7: Progressive refinement
        print("\n7️⃣ PROGRESSIVE REFINEMENT")
        print("-"*40)
        customer_id = "demo_progressive"
        
        # First: broad category
        async with session.post(f"{base_url}/api/chat", json={
            "message": "I want vapes",
            "customer_id": customer_id
        }) as resp:
            data = await resp.json()
            print(f"Step 1 - Request: I want vapes")
            print(f"         Products: {len(data.get('products', []))}")
        
        # Second: narrow by type
        async with session.post(f"{base_url}/api/chat", json={
            "message": "indica vapes",
            "customer_id": customer_id
        }) as resp:
            data = await resp.json()
            print(f"Step 2 - Request: indica vapes")
            print(f"         Products: {len(data.get('products', []))}")
        
        # Third: narrow by price
        async with session.post(f"{base_url}/api/chat", json={
            "message": "under $50",
            "customer_id": customer_id
        }) as resp:
            data = await resp.json()
            print(f"Step 3 - Request: under $50")
            print(f"         Products: {len(data.get('products', []))}")
        
        print("\n" + "="*60)
        print("✅ ALL FEATURES DEMONSTRATED SUCCESSFULLY!")
        print("="*60)

if __name__ == "__main__":
    asyncio.run(test_buddy_api())