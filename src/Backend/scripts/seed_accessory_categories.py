#!/usr/bin/env python3
"""
Seed accessory categories with common smoking accessory categories
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
    'password': 'your_password_here'
}

# Common accessory categories with Lucide-style icon names and descriptions
CATEGORIES = [
    {
        'name': 'Rolling Papers',
        'slug': 'rolling-papers',
        'icon': 'scroll-text',
        'description': 'Rolling papers of all sizes - King Size, 1¼, regular, flavored, etc.',
        'sort_order': 1
    },
    {
        'name': 'Tips & Filters',
        'slug': 'tips-filters',
        'icon': 'filter',
        'description': 'Filter tips, crutches, and mouthpieces for joints and blunts',
        'sort_order': 2
    },
    {
        'name': 'Blunt Wraps',
        'slug': 'blunt-wraps',
        'icon': 'scroll',
        'description': 'Blunt wraps, cigars for rolling, flavored wraps',
        'sort_order': 3
    },
    {
        'name': 'Grinders',
        'slug': 'grinders',
        'icon': 'circle-dashed',
        'description': 'Herb grinders - 2-piece, 3-piece, 4-piece, electric',
        'sort_order': 4
    },
    {
        'name': 'Lighters',
        'slug': 'lighters',
        'icon': 'flame',
        'description': 'Lighters, torch lighters, hemp wick, matches',
        'sort_order': 5
    },
    {
        'name': 'Rolling Trays',
        'slug': 'rolling-trays',
        'icon': 'rectangle-horizontal',
        'description': 'Rolling trays for organizing and preparing',
        'sort_order': 6
    },
    {
        'name': 'Storage & Containers',
        'slug': 'storage-containers',
        'icon': 'archive',
        'description': 'Airtight jars, smell-proof bags, stash boxes',
        'sort_order': 7
    },
    {
        'name': 'Pipes & Bowls',
        'slug': 'pipes-bowls',
        'icon': 'cigarette',
        'description': 'Glass pipes, metal pipes, bowls, one-hitters',
        'sort_order': 8
    },
    {
        'name': 'Bongs & Water Pipes',
        'slug': 'bongs',
        'icon': 'flask-conical',
        'description': 'Water bongs, bubblers, percolators, downstems',
        'sort_order': 9
    },
    {
        'name': 'Vaporizers',
        'slug': 'vaporizers',
        'icon': 'wind',
        'description': 'Dry herb vaporizers, vape pens, accessories',
        'sort_order': 10
    },
    {
        'name': 'Ashtrays',
        'slug': 'ashtrays',
        'icon': 'circle',
        'description': 'Ashtrays, ash catchers, cleaning accessories',
        'sort_order': 11
    },
    {
        'name': 'Rolling Machines',
        'slug': 'rolling-machines',
        'icon': 'cpu',
        'description': 'Automatic and manual rolling machines',
        'sort_order': 12
    },
    {
        'name': 'Cleaning Supplies',
        'slug': 'cleaning-supplies',
        'icon': 'spray-can',
        'description': 'Pipe cleaners, cleaning solutions, brushes, wipes',
        'sort_order': 13
    },
    {
        'name': 'Smell Proof Bags',
        'slug': 'smell-proof-bags',
        'icon': 'shield',
        'description': 'Odor-proof bags, cases, and pouches',
        'sort_order': 14
    },
    {
        'name': 'Other Accessories',
        'slug': 'other-accessories',
        'icon': 'boxes',
        'description': 'Miscellaneous smoking accessories',
        'sort_order': 99
    }
]


def seed_categories():
    """Seed accessory categories table"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        logger.info("🌱 Starting category seeding...")
        
        # Check if categories already exist
        cursor.execute("SELECT COUNT(*) FROM accessory_categories")
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            logger.info(f"⚠️  Found {existing_count} existing categories - will update existing records")
        
        # Insert categories
        inserted = 0
        for cat in CATEGORIES:
            try:
                # Check if category already exists
                cursor.execute("""
                    SELECT id FROM accessory_categories WHERE slug = %s
                """, (cat['slug'],))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing
                    cursor.execute("""
                        UPDATE accessory_categories
                        SET name = %s, icon = %s, description = %s, sort_order = %s, is_active = true
                        WHERE slug = %s
                    """, (
                        cat['name'],
                        cat['icon'],
                        cat['description'],
                        cat['sort_order'],
                        cat['slug']
                    ))
                    logger.info(f"  🔄 {cat['icon']} {cat['name']} (updated)")
                else:
                    # Insert new
                    cursor.execute("""
                        INSERT INTO accessory_categories 
                        (name, slug, icon, description, sort_order, is_active)
                        VALUES (%s, %s, %s, %s, %s, true)
                    """, (
                        cat['name'],
                        cat['slug'],
                        cat['icon'],
                        cat['description'],
                        cat['sort_order']
                    ))
                    logger.info(f"  ✅ {cat['icon']} {cat['name']}")
                
                inserted += 1
            except Exception as e:
                logger.error(f"  ❌ Failed to process {cat['name']}: {str(e)}")
        
        conn.commit()
        
        # Verify
        cursor.execute("""
            SELECT name, icon, sort_order 
            FROM accessory_categories 
            ORDER BY sort_order
        """)
        categories = cursor.fetchall()
        
        logger.info(f"\n✅ Successfully seeded {inserted} categories!")
        logger.info(f"📊 Total categories in database: {len(categories)}")
        logger.info("\nCategories list:")
        for name, icon, sort_order in categories:
            logger.info(f"  {sort_order:2d}. {icon} {name}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Error seeding categories: {str(e)}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    seed_categories()
