#!/usr/bin/env python3
"""Add Britane butane product to database"""

import psycopg2
import redis
import json

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'ai_engine',
    'user': 'weedgo',
    'password': 'your_password_here'
}

# Redis connection
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0
}

def add_britane_product():
    """Add Britane butane product to the database"""
    
    # Connect to database
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Get lighters category ID
        cursor.execute("SELECT id FROM accessory_categories WHERE slug = 'lighters'")
        result = cursor.fetchone()
        if result:
            category_id = result[0]
        else:
            # Create lighters category if it doesn't exist
            cursor.execute("""
                INSERT INTO accessory_categories (name, slug, icon, sort_order)
                VALUES ('Lighters & Fuel', 'lighters', '🔥', 6)
                RETURNING id
            """)
            category_id = cursor.fetchone()[0]
        
        # Insert Britane butane product
        cursor.execute("""
            INSERT INTO accessories_catalog 
            (barcode, sku, name, brand, category_id, description, 
             msrp, default_cost, suggested_retail, data_source, confidence_score, verified)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (barcode) DO UPDATE SET
                name = EXCLUDED.name,
                brand = EXCLUDED.brand,
                description = EXCLUDED.description,
                category_id = EXCLUDED.category_id,
                verified = true
            RETURNING id, name, barcode
        """, (
            '6528273015278',  # Barcode
            'BRITANE-BUTANE-400ML',
            'Britane Ultra Refined Butane - 400ml',
            'Britane',
            category_id,
            'Ultra refined butane gas for torch lighters and culinary torches. 400ml can with universal nozzle adapter set. Premium quality fuel for optimal performance.',
            12.99,  # MSRP
            6.50,   # Cost
            12.99,  # Retail
            'manual',
            1.0,
            True
        ))
        
        result = cursor.fetchone()
        if result:
            product_id, name, barcode = result
            print(f"✅ Added product: {name}")
            print(f"   ID: {product_id}")
            print(f"   Barcode: {barcode}")
            
            # Clear Redis cache for this barcode
            try:
                r = redis.Redis(**REDIS_CONFIG)
                cache_key = f"barcode:{barcode}"
                if r.exists(cache_key):
                    r.delete(cache_key)
                    print(f"   Cleared cache for {cache_key}")
            except Exception as e:
                print(f"   Warning: Could not clear Redis cache: {e}")
        
        conn.commit()
        print("\n✅ Product successfully added to database!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    add_britane_product()