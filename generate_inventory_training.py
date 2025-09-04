#!/usr/bin/env python3
"""
Generate training examples from actual inventory
Teaches the model what products ACTUALLY exist
"""

import asyncio
import asyncpg
import json
import os
from typing import List, Dict

async def generate_training_from_inventory():
    """Generate training examples from real database products"""
    
    # Connect to database
    db_pool = await asyncpg.create_pool(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5434)),
        database=os.getenv('DB_NAME', 'ai_engine'),
        user=os.getenv('DB_USER', 'weedgo'),
        password=os.getenv('DB_PASSWORD', 'weedgo123')
    )
    
    training_examples = []
    
    async with db_pool.acquire() as conn:
        # Get unique product names that might be questioned
        interesting_products = await conn.fetch("""
            SELECT DISTINCT product_name, category, sub_category, unit_price, size
            FROM products
            WHERE product_name ILIKE '%tiger%' 
               OR product_name ILIKE '%blood%'
               OR product_name ILIKE '%pink%'
               OR product_name ILIKE '%kush%'
               OR product_name ILIKE '%dream%'
               OR sub_category = 'Pre-Rolls'
               OR category = 'Extracts'
            ORDER BY product_name
            LIMIT 100
        """)
        
        # Generate training examples for each product
        for product in interesting_products:
            name = product['product_name']
            category = product['category']
            sub_category = product['sub_category']
            price = product['unit_price']
            size = product['size']
            
            # Example 1: "Do you have X?"
            training_examples.append({
                "query": f"do you have {name.lower()}?",
                "correct_response": f"Yes! We have {name} ({category}/{sub_category}) for ${price:.2f}",
                "search_required": True,
                "product_exists": True,
                "actual_product": name
            })
            
            # Example 2: "Give me X"
            training_examples.append({
                "query": f"give me {name.lower()}",
                "correct_response": f"Sure! {name} is available for ${price:.2f}. Would you like to add it to your cart?",
                "search_required": True,
                "product_exists": True,
                "actual_product": name
            })
            
            # Example 3: "Is X real?"
            if 'tiger' in name.lower() or 'blood' in name.lower():
                training_examples.append({
                    "query": f"is {name.lower()} a real product?",
                    "correct_response": f"Yes, {name} is a real product we carry. It's in our {category} section for ${price:.2f}",
                    "search_required": True,
                    "product_exists": True,
                    "actual_product": name
                })
        
        # Special focus on Tiger Blood products
        tiger_blood_products = await conn.fetch("""
            SELECT * FROM products 
            WHERE product_name ILIKE '%tiger%blood%'
            ORDER BY unit_price
        """)
        
        if tiger_blood_products:
            # Add specific Tiger Blood training
            training_examples.append({
                "query": "do you have tiger blood pre-rolls?",
                "correct_response": f"Yes! We have Tiger Blood Distillate Infused Pre-Roll for ${tiger_blood_products[0]['unit_price']:.2f}",
                "search_required": True,
                "product_exists": True,
                "products_found": len(tiger_blood_products),
                "note": "Tiger Blood is a REAL product line, not a myth"
            })
            
            training_examples.append({
                "query": "is tiger blood real?",
                "correct_response": f"Yes, Tiger Blood is a real product line. We carry {len(tiger_blood_products)} Tiger Blood products including gummies, pre-rolls, and flower.",
                "search_required": True,
                "product_exists": True,
                "products_found": len(tiger_blood_products),
                "note": "Never claim products don't exist without searching"
            })
    
    # Save training examples
    with open('inventory_training_data.json', 'w') as f:
        json.dump(training_examples, f, indent=2)
    
    print(f"Generated {len(training_examples)} training examples from actual inventory")
    
    # Print some examples
    print("\n=== Sample Training Examples ===")
    for example in training_examples[:5]:
        print(f"\nQuery: {example['query']}")
        print(f"Correct: {example['correct_response']}")
    
    # Generate prompt instructions
    prompt_instructions = """
CRITICAL INVENTORY AWARENESS RULES:

1. THESE PRODUCTS ARE REAL AND IN STOCK:
   - Tiger Blood Distillate Infused Pre-Roll (Extracts) - $11.77
   - Tiger Blood Milled Flower (Flower) - $13.99
   - Tiger Blood Hash Rosin Gummy (Edibles) - $2.88
   - Tiger Blood THC Gummy (Edibles) - $4.00

2. NEVER CLAIM THESE DON'T EXIST:
   - Tiger Blood is a REAL product line, not a myth or pop culture reference
   - We have multiple Tiger Blood products in different categories
   - Always search the database before claiming something doesn't exist

3. WHEN SOMEONE ASKS "DO YOU HAVE X?":
   - ALWAYS search the database first
   - Report what you actually found
   - Never say "we don't carry" without searching
   - If found: "Yes, we have [exact name] for $[price]"
   - If not found after search: "I searched but couldn't find that specific item"

4. CATEGORY NOTES:
   - Infused pre-rolls may be under "Extracts" not "Flower/Pre-Rolls"
   - Always search multiple categories
   - Don't assume category structure
    """
    
    with open('inventory_awareness_prompt.txt', 'w') as f:
        f.write(prompt_instructions)
    
    print("\n=== Generated Inventory Awareness Prompt ===")
    print(prompt_instructions)
    
    await db_pool.close()

if __name__ == "__main__":
    asyncio.run(generate_training_from_inventory())