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

async def add_training_to_database(examples):
    """Add training examples directly to database"""
    conn = await asyncpg.connect(**DB_CONFIG)
    
    successful = 0
    failed = 0
    
    for example in examples:
        try:
            # Insert into training_examples table
            await conn.execute('''
                INSERT INTO training_examples 
                (query, expected_intent, expected_response, entities, 
                 expected_products, expected_response_qualities, context, 
                 dataset_name, is_active, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
            ''', 
                example['query'],
                example['expected_intent'],
                example['expected_response'],
                json.dumps(example.get('entities', {})),
                json.dumps(example.get('expected_products', [])),
                json.dumps(example.get('expected_response_qualities', [])),
                json.dumps(example.get('context', {})),
                'joint_recognition_training',
                True
            )
            successful += 1
            print(f"✅ Added: {example['query'][:40]}...")
        except Exception as e:
            failed += 1
            print(f"❌ Failed: {example['query'][:40]}... - {str(e)}")
    
    await conn.close()
    return successful, failed

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

What type are you looking for? I can help you filter by:
- Plant type (Indica, Sativa, Hybrid)
- Price range
- THC content
- Popular brands"""

    # Add basic recognition examples
    for query in basic_queries:
        examples.append({
            "query": query,
            "expected_intent": "product_inquiry",
            "expected_response": base_response,
            "entities": {
                "product_type": "joint",
                "sub_category": "Pre-Rolls",
                "size": "1g"
            },
            "expected_products": [],  # Will be filled by actual search
            "expected_response_qualities": [
                "provides_count",
                "shows_plant_types",
                "mentions_price_range",
                "offers_filtering_options",
                "encourages_engagement"
            ],
            "context": {
                "search_criteria": {
                    "sub_category": "Pre-Rolls",
                    "size": ["1x1g", "1g"]
                },
                "quick_actions": [
                    "Show indica joints",
                    "Show sativa joints",
                    "Filter by price",
                    "High THC options"
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

Would you like to:
- See specific brands
- Filter by THC content  
- View customer favorites
- Check current deals"""
            
            for query in queries:
                examples.append({
                    "query": query,
                    "expected_intent": "product_inquiry",
                    "expected_response": specific_response,
                    "entities": {
                        "product_type": "joint",
                        "sub_category": "Pre-Rolls",
                        "size": "1g",
                        "plant_type": pt_key
                    },
                    "expected_products": [],
                    "expected_response_qualities": [
                        "specific_count",
                        "price_information",
                        "follow_up_options",
                        "sales_oriented"
                    ],
                    "context": {
                        "search_criteria": {
                            "sub_category": "Pre-Rolls",
                            "size": ["1x1g", "1g"],
                            "plant_type": pt_key
                        }
                    }
                })
    
    # Price-based queries
    price_queries = [
        {
            "query": "show me cheap joints",
            "price_filter": "budget",
            "response": f"I have budget-friendly joints starting at ${stats['price_range']['min']:.2f}. Here are our value options in 1g pre-rolls. Would you like to see all budget options under $6?"
        },
        {
            "query": "what's your cheapest joint",
            "price_filter": "minimum",
            "response": f"Our most affordable joints start at ${stats['price_range']['min']:.2f}. These are quality 1g pre-rolls at great prices. Interested in seeing what's available?"
        },
        {
            "query": "show me premium joints",
            "price_filter": "premium",
            "response": f"Our premium 1g joints range from $8 to ${stats['price_range']['max']:.2f}. These feature top-shelf flower with high THC content. Would you like to see our craft options?"
        }
    ]
    
    for pq in price_queries:
        examples.append({
            "query": pq["query"],
            "expected_intent": "product_inquiry",
            "expected_response": pq["response"],
            "entities": {
                "product_type": "joint",
                "sub_category": "Pre-Rolls",
                "size": "1g",
                "price_preference": pq["price_filter"]
            },
            "expected_products": [],
            "expected_response_qualities": [
                "price_focused",
                "conversion_oriented",
                "specific_recommendations"
            ],
            "context": {
                "search_criteria": {
                    "sub_category": "Pre-Rolls",
                    "size": ["1x1g", "1g"],
                    "price_filter": pq["price_filter"]
                }
            }
        })
    
    # Slang variations
    slang_queries = [
        ("got any j's", "j"),
        ("need a doobie", "doobie"),
        ("looking for a fatty", "fatty"),
        ("got any pre-rolls", "pre-roll"),
        ("hook me up with a joint", "joint")
    ]
    
    for query, slang in slang_queries:
        examples.append({
            "query": query,
            "expected_intent": "product_inquiry",
            "expected_response": base_response,
            "entities": {
                "product_type": "joint",
                "sub_category": "Pre-Rolls",
                "size": "1g",
                "slang_detected": slang
            },
            "expected_products": [],
            "expected_response_qualities": [
                "understands_slang",
                "provides_options",
                "professional_response"
            ],
            "context": {
                "slang_mapping": {
                    slang: "joint/pre-roll"
                }
            }
        })
    
    return examples

async def main():
    """Main training execution"""
    
    print("\n🚀 Joint Recognition Training Module V2")
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
    
    # Add to database
    print("\n📚 Adding training examples to database...")
    print("=" * 60)
    successful, failed = await add_training_to_database(examples)
    
    print("\n" + "=" * 60)
    print(f"📊 Training Summary:")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {(successful/(successful+failed)*100):.1f}%" if (successful+failed) > 0 else "0%")
    
    if successful > 0:
        print("\n✨ Training Complete!")
        print("\n📝 Instructions for Testing:")
        print("1. Go to the chat interface: http://localhost:5174/")
        print("2. Try these test queries:")
        print("   - 'give me a joint'")
        print("   - 'show me indica joints'")
        print("   - 'what's your cheapest joint'")
        print("3. Verify the AI:")
        print("   - Returns 1g pre-rolls (not other sizes)")
        print("   - Shows plant type breakdown")
        print("   - Provides quick action buttons")
        print("   - Suggests relevant follow-ups")
        print("\n4. Apply the training:")
        print("   Run: curl -X POST http://localhost:8080/api/v1/training/apply")
    
    # Save training data for reference
    training_file = f"joint_training_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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