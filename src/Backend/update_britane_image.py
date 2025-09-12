#!/usr/bin/env python3
"""Update Britane butane with image URL"""

import psycopg2
import redis

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'ai_engine',
    'user': 'weedgo',
    'password': 'weedgo123'
}

def update_britane_image():
    """Add image URL to Britane product"""
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Update with a generic butane image URL
    cursor.execute("""
        UPDATE accessories_catalog
        SET image_url = %s
        WHERE barcode = %s
        RETURNING id, name, image_url
    """, (
        'https://m.media-amazon.com/images/I/71YtLh8aYPL._AC_SL1500_.jpg',  # Generic butane image
        '6528273015278'
    ))
    
    result = cursor.fetchone()
    if result:
        print(f"✅ Updated product: {result[1]}")
        print(f"   Image URL: {result[2][:60]}...")
        
        # Clear cache
        try:
            r = redis.Redis(host='localhost', port=6379, db=0)
            cache_key = f"barcode:6528273015278"
            if r.exists(cache_key):
                r.delete(cache_key)
                print(f"   Cleared cache")
        except:
            pass
    
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    update_britane_image()