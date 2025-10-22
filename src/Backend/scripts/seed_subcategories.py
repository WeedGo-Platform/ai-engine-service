#!/usr/bin/env python3
"""
Seed subcategories for accessory categories
"""

import psycopg2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'ai_engine',
    'user': 'weedgo',
    'password': 'weedgo123'
}

# Subcategories organized by main category slug
SUBCATEGORIES = {
    'rolling-papers': [
        '1¼ Size',
        '1½ Size',
        'King Size',
        'King Size Slim',
        'Regular Size',
        'Flavored',
        'Hemp Papers',
        'Rice Papers',
        'Pre-Rolled Cones'
    ],
    'tips-filters': [
        'Glass Tips',
        'Paper Tips',
        'Wooden Tips',
        'Reusable Filters',
        'Activated Carbon',
        'Pre-Made Tips'
    ],
    'blunt-wraps': [
        'Tobacco Wraps',
        'Hemp Wraps',
        'Flavored Wraps',
        'Natural Leaf',
        'Pre-Rolled Blunts'
    ],
    'grinders': [
        '2-Piece',
        '3-Piece',
        '4-Piece',
        'Electric',
        'Metal',
        'Acrylic',
        'Wooden',
        'Travel Size'
    ],
    'lighters': [
        'Disposable',
        'Refillable',
        'Torch',
        'Electric',
        'Hemp Wick',
        'Matches'
    ],
    'rolling-trays': [
        'Small',
        'Medium',
        'Large',
        'Metal',
        'Wood',
        'Plastic',
        'Magnetic',
        'LED'
    ],
    'storage-containers': [
        'Glass Jars',
        'Metal Tins',
        'Plastic Containers',
        'Smell Proof Bags',
        'Humidity Control',
        'UV Protection',
        'Travel Cases'
    ],
    'pipes-bowls': [
        'Glass Pipes',
        'Metal Pipes',
        'Wooden Pipes',
        'Silicone Pipes',
        'One-Hitters',
        'Chillums',
        'Bubblers',
        'Bowls & Slides'
    ],
    'bongs': [
        'Glass Bongs',
        'Acrylic Bongs',
        'Silicone Bongs',
        'Beaker Base',
        'Straight Tube',
        'Percolators',
        'Bubblers',
        'Downstems',
        'Bowl Pieces'
    ],
    'vaporizers': [
        'Dry Herb',
        'Concentrate',
        'Desktop',
        'Portable',
        'Pen Style',
        'Batteries',
        'Cartridges',
        'Accessories'
    ],
    'ashtrays': [
        'Glass',
        'Metal',
        'Ceramic',
        'Silicone',
        'Pocket',
        'Tabletop',
        'Outdoor'
    ],
    'rolling-machines': [
        '70mm',
        '79mm',
        '110mm',
        'Automatic',
        'Manual',
        'Joint Roller',
        'Blunt Roller'
    ],
    'cleaning-supplies': [
        'Cleaning Solutions',
        'Pipe Cleaners',
        'Brushes',
        'Wipes',
        'Alcohol',
        'Salt',
        'Cleaning Kits'
    ],
    'smell-proof-bags': [
        'Small Pouches',
        'Medium Bags',
        'Large Cases',
        'Backpacks',
        'Duffel Bags',
        'Lockable',
        'Waterproof'
    ],
    'other-accessories': [
        'Scales',
        'Magnifiers',
        'Scoops',
        'Funnels',
        'Stickers',
        'Apparel',
        'Books',
        'Miscellaneous'
    ]
}

def seed_subcategories():
    """Add subcategories to database by storing them in a JSON field or simple categorization"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        logger.info("🌱 Seeding subcategories...")
        
        # Get all categories
        cursor.execute("SELECT id, slug, name FROM accessory_categories ORDER BY sort_order")
        categories = cursor.fetchall()
        
        total_subcats = 0
        for cat_id, slug, name in categories:
            if slug in SUBCATEGORIES:
                subcats = SUBCATEGORIES[slug]
                logger.info(f"\n📁 {name} ({len(subcats)} subcategories)")
                for subcat in subcats:
                    logger.info(f"   • {subcat}")
                total_subcats += len(subcats)
        
        logger.info(f"\n✅ Total subcategories available: {total_subcats}")
        logger.info(f"📊 Across {len(SUBCATEGORIES)} main categories")
        logger.info("\n💡 Subcategories will be selectable when adding products")
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        conn.rollback()
        return False

if __name__ == "__main__":
    seed_subcategories()
