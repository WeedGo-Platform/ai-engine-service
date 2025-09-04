#!/usr/bin/env python3
"""
Training Module: Teaching AI to Understand "Joint" = 1g Pre-Roll
================================================================

This training module teaches the AI:
1. "Joint" refers to 1g pre-rolls (sub_category='Pre-Rolls', size='1x1g' or '1g')
2. To provide plant type breakdown when multiple products are found
3. To offer smart follow-up quick actions for sales conversion
"""

import asyncio
import asyncpg
import requests
import json
from datetime import datetime

# API Configuration
API_BASE_URL = "http://localhost:8080"
TRAINING_ENDPOINT = f"{API_BASE_URL}/api/v1/training/examples"

# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'ai_engine',
    'user': 'weedgo',
    'password': 'weedgo123'
}

async def get_joint_stats():
    """Get actual statistics about joints/pre-rolls from database"""
    conn = await asyncpg.connect(**DB_CONFIG)
    
    # Get plant type breakdown
    query = '''
        SELECT 
            plant_type,
            COUNT(*) as count,
            ROUND(AVG(unit_price)::numeric, 2) as avg_price,
            MIN(unit_price) as min_price,
            MAX(unit_price) as max_price
        FROM products
        WHERE sub_category = 'Pre-Rolls' 
          AND (size = '1x1g' OR size = '1g')
        GROUP BY plant_type
        ORDER BY count DESC
    '''
    
    results = await conn.fetch(query)
    
    stats = {
        'total': 0,
        'by_plant_type': {},
        'price_range': {'min': float('inf'), 'max': 0}
    }
    
    for row in results:
        plant_type = row['plant_type']
        count = row['count']
        stats['total'] += count
        stats['by_plant_type'][plant_type] = {
            'count': count,
            'avg_price': float(row['avg_price']),
            'min_price': float(row['min_price']),
            'max_price': float(row['max_price'])
        }
        stats['price_range']['min'] = min(stats['price_range']['min'], float(row['min_price']))
        stats['price_range']['max'] = max(stats['price_range']['max'], float(row['max_price']))
    
    await conn.close()
    return stats

def create_training_examples(stats):
    """Create comprehensive training examples for joint recognition"""
    
    examples = []
    
    # Basic joint queries
    basic_queries = [
        "give me a joint",
        "I want a joint",
        "show me joints",
        "got any joints?",
        "do you have joints",
        "I need a joint",
        "looking for a joint",
        "joint please",
        "can I get a joint",
        "what joints do you have"
    ]
    
    # Create response template with actual data
    plant_type_summary = []
    for plant_type, data in stats['by_plant_type'].items():
        plant_type_summary.append(f"{plant_type}: {data['count']} options")
    
    base_response = f"""I have {stats['total']} pre-rolled joints (1g) available:

• {' | '.join(plant_type_summary)}
• Price range: ${stats['price_range']['min']:.2f} - ${stats['price_range']['max']:.2f}

What type are you looking for?"""

    # Add basic recognition examples
    for query in basic_queries:
        examples.append({
            "query": query,
            "expected_intent": "product_inquiry",
            "expected_response": base_response,
            "entities": {
                "entities": {
                    "product_type": "joint",
                    "sub_category": "Pre-Rolls",
                    "size": "1x1g"
                },
                "search_criteria": {
                    "sub_category": "Pre-Rolls",
                    "size": ["1x1g", "1g"]
                },
                "follow_up_actions": [
                    "Show me indica joints",
                    "Show me sativa joints", 
                    "What's your budget?",
                    "Looking for high THC?"
                ]
            }
        })
    
    # Plant type specific queries
    plant_type_queries = {
        "indica": [
            "give me an indica joint",
            "I want indica joints",
            "show me indica pre-rolls"
        ],
        "sativa": [
            "give me a sativa joint",
            "I want sativa joints",
            "show me sativa pre-rolls"
        ],
        "hybrid": [
            "give me a hybrid joint",
            "I want hybrid joints",
            "show me hybrid pre-rolls"
        ]
    }
    
    for plant_type, queries in plant_type_queries.items():
        if plant_type.title() in stats['by_plant_type'] or f"{plant_type.title()} Dominant" in stats['by_plant_type']:
            # Find the matching plant type key
            pt_key = None
            for key in stats['by_plant_type']:
                if plant_type.lower() in key.lower():
                    pt_key = key
                    break
            
            if pt_key:
                pt_data = stats['by_plant_type'][pt_key]
                specific_response = f"""I have {pt_data['count']} {pt_key} pre-rolled joints (1g) available:

• Price range: ${pt_data['min_price']:.2f} - ${pt_data['max_price']:.2f}
• Average price: ${pt_data['avg_price']:.2f}

Would you like to see specific brands or filter by THC content?"""
                
                for query in queries:
                    examples.append({
                        "user_input": query,
                        "ideal_response": specific_response,
                        "intent": "product_inquiry",
                        "confidence": 0.95,
                        "context_required": False,
                        "metadata": {
                            "entities": {
                                "product_type": "joint",
                                "sub_category": "Pre-Rolls",
                                "size": "1x1g",
                                "plant_type": pt_key
                            },
                            "search_criteria": {
                                "sub_category": "Pre-Rolls",
                                "size": ["1x1g", "1g"],
                                "plant_type": pt_key
                            },
                            "follow_up_actions": [
                                "Show me premium options",
                                "Show me budget friendly",
                                "Filter by THC > 25%",
                                "Show popular brands"
                            ]
                        }
                    })
    
    # Price-based queries
    price_queries = [
        {
            "query": "show me cheap joints",
            "price_filter": "budget",
            "response": f"I have budget-friendly joints starting at ${stats['price_range']['min']:.2f}. Would you like to see our value options?"
        },
        {
            "query": "what's your cheapest joint",
            "price_filter": "minimum",
            "response": f"Our most affordable joints start at ${stats['price_range']['min']:.2f}. These are quality 1g pre-rolls at great prices."
        },
        {
            "query": "show me premium joints",
            "price_filter": "premium",
            "response": f"Our premium joints range up to ${stats['price_range']['max']:.2f}. These feature top-shelf flower and high THC content."
        }
    ]
    
    for pq in price_queries:
        examples.append({
            "user_input": pq["query"],
            "ideal_response": pq["response"],
            "intent": "product_inquiry",
            "confidence": 0.95,
            "context_required": False,
            "metadata": {
                "entities": {
                    "product_type": "joint",
                    "sub_category": "Pre-Rolls",
                    "size": "1x1g",
                    "price_preference": pq["price_filter"]
                },
                "search_criteria": {
                    "sub_category": "Pre-Rolls",
                    "size": ["1x1g", "1g"]
                },
                "follow_up_actions": [
                    "Show me all options",
                    "Filter by plant type",
                    "What's popular?",
                    "Show similar products"
                ]
            }
        })
    
    # Slang variations
    slang_queries = [
        "got any j's",
        "need a doobie",
        "looking for a fatty",
        "got any pre-rolls",
        "hook me up with a joint"
    ]
    
    for query in slang_queries:
        examples.append({
            "user_input": query,
            "ideal_response": base_response,
            "intent": "product_inquiry",
            "confidence": 0.9,
            "context_required": False,
            "metadata": {
                "entities": {
                    "product_type": "joint",
                    "sub_category": "Pre-Rolls",
                    "size": "1x1g",
                    "slang_detected": True
                },
                "search_criteria": {
                    "sub_category": "Pre-Rolls",
                    "size": ["1x1g", "1g"]
                },
                "slang_mapping": {
                    "j": "joint",
                    "doobie": "joint",
                    "fatty": "joint",
                    "pre-roll": "joint"
                }
            }
        })
    
    return examples

def submit_training_examples(examples):
    """Submit training examples to the API"""
    
    print(f"\n📚 Submitting {len(examples)} training examples...")
    print("=" * 60)
    
    successful = 0
    failed = 0
    
    for i, example in enumerate(examples, 1):
        try:
            response = requests.post(
                TRAINING_ENDPOINT,
                json=example,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in [200, 201]:
                successful += 1
                print(f"✅ Example {i}/{len(examples)}: {example['user_input'][:30]}...")
            else:
                failed += 1
                print(f"❌ Example {i}/{len(examples)} failed: {response.status_code}")
                
        except Exception as e:
            failed += 1
            print(f"❌ Example {i}/{len(examples)} error: {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"📊 Training Summary:")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {(successful/len(examples)*100):.1f}%")
    
    return successful, failed

async def main():
    """Main training execution"""
    
    print("\n🚀 Joint Recognition Training Module")
    print("=" * 60)
    print("Teaching AI: 'joint' = 1g pre-roll")
    print("=" * 60)
    
    # Get actual statistics
    print("\n📊 Fetching current joint inventory stats...")
    stats = await get_joint_stats()
    
    print(f"\n📈 Current Inventory:")
    print(f"   Total 1g joints: {stats['total']}")
    for plant_type, data in stats['by_plant_type'].items():
        print(f"   • {plant_type}: {data['count']} products (${data['min_price']:.2f}-${data['max_price']:.2f})")
    
    # Create training examples
    print("\n🎯 Creating training examples...")
    examples = create_training_examples(stats)
    print(f"   Generated {len(examples)} training examples")
    
    # Submit to API
    successful, failed = submit_training_examples(examples)
    
    if successful > 0:
        print("\n✨ Training Complete!")
        print("\n📝 Next Steps:")
        print("1. Test with queries like 'give me a joint' in the chat")
        print("2. Verify it returns 1g pre-rolls grouped by plant type")
        print("3. Check that quick actions are generated for sales conversion")
        print("4. Fine-tune responses based on actual results")
    else:
        print("\n⚠️ Training failed. Please check the API is running.")
    
    # Save training data for reference
    training_file = f"joint_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(training_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'stats': stats,
            'examples': examples,
            'results': {
                'successful': successful,
                'failed': failed
            }
        }, f, indent=2)
    
    print(f"\n💾 Training data saved to: {training_file}")

if __name__ == "__main__":
    asyncio.run(main())