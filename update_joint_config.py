#!/usr/bin/env python3
"""
Update AI Configuration to Handle Joints Properly
==================================================

This script updates the AI configuration to ensure "joint" queries
return 1g pre-rolls with proper plant type breakdown.
"""

import asyncpg
import asyncio
import json

DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'ai_engine',
    'user': 'weedgo',
    'password': 'weedgo123'
}

async def update_config():
    """Update AI configuration for joint recognition"""
    conn = await asyncpg.connect(**DB_CONFIG)
    
    # Check if config exists
    existing = await conn.fetchval("""
        SELECT config_value FROM ai_config 
        WHERE config_key = 'product_mappings'
    """)
    
    if existing:
        config = json.loads(existing)
    else:
        config = {}
    
    # Add joint-specific mappings
    config['slang_mappings'] = config.get('slang_mappings', {})
    config['slang_mappings'].update({
        "joint": {"category": "Pre-Rolls", "size": ["1x1g", "1g"]},
        "j": {"category": "Pre-Rolls", "size": ["1x1g", "1g"]},
        "doobie": {"category": "Pre-Rolls", "size": ["1x1g", "1g"]},
        "fatty": {"category": "Pre-Rolls", "size": ["1x1g", "1g"]}
    })
    
    # Add product category hints
    config['category_hints'] = config.get('category_hints', {})
    config['category_hints']['Pre-Rolls'] = {
        "keywords": ["joint", "pre-roll", "preroll", "j", "doobie", "fatty", "blunt"],
        "default_size": "1x1g",
        "response_template": "I have {count} pre-rolled joints (1g) available. {plant_types}. Price range: ${min_price} - ${max_price}. What type are you looking for?"
    }
    
    # Update or insert config
    await conn.execute("""
        INSERT INTO ai_config (config_key, config_value, created_at, updated_at)
        VALUES ('product_mappings', $1, NOW(), NOW())
        ON CONFLICT (config_key) 
        DO UPDATE SET config_value = $1, updated_at = NOW()
    """, json.dumps(config))
    
    print("✅ Configuration updated successfully")
    
    # Also update the smart response templates
    template_config = {
        "product_inquiry": {
            "joint": {
                "search_params": {
                    "sub_category": "Pre-Rolls",
                    "size": ["1x1g", "1g"]
                },
                "response_format": "grouped_by_plant_type",
                "include_stats": True,
                "quick_actions": [
                    "Show indica joints",
                    "Show sativa joints",
                    "Filter by price",
                    "High THC options"
                ]
            }
        }
    }
    
    await conn.execute("""
        INSERT INTO ai_config (config_key, config_value, created_at, updated_at)
        VALUES ('response_templates', $1, NOW(), NOW())
        ON CONFLICT (config_key) 
        DO UPDATE SET config_value = $1, updated_at = NOW()
    """, json.dumps(template_config))
    
    print("✅ Response templates updated")
    
    await conn.close()

async def main():
    print("🔧 Updating AI Configuration for Joint Recognition")
    print("=" * 50)
    
    # First check if ai_config table exists
    conn = await asyncpg.connect(**DB_CONFIG)
    
    # Create table if it doesn't exist
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS ai_config (
            id SERIAL PRIMARY KEY,
            config_key VARCHAR(255) UNIQUE NOT NULL,
            config_value JSONB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    await conn.close()
    
    # Update configuration
    await update_config()
    
    print("\n📝 Configuration applied!")
    print("The AI should now:")
    print("1. Recognize 'joint' as 1g pre-rolls")
    print("2. Filter by size (1x1g or 1g)")
    print("3. Group results by plant type")
    print("4. Provide relevant quick actions")

if __name__ == "__main__":
    asyncio.run(main())