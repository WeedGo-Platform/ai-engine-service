#!/usr/bin/env python3
"""Test why shatter/concentrate searches are failing"""

import psycopg2
from psycopg2.extras import RealDictCursor

db_config = {
    'host': 'localhost',
    'port': 5434,
    'database': 'ai_engine',
    'user': 'weedgo',
    'password': 'weedgo123'
}

conn = psycopg2.connect(**db_config, cursor_factory=RealDictCursor)
cur = conn.cursor()

print("=== SEARCHING FOR CONCENTRATES/EXTRACTS ===\n")

# 1. Search for shatter
print("1. Products with 'shatter' in name or description:")
cur.execute("""
    SELECT product_name, brand, category, unit_price
    FROM products
    WHERE product_name ILIKE %s 
       OR short_description ILIKE %s
       OR long_description ILIKE %s
       OR category = 'Extracts'
    ORDER BY 
        CASE 
            WHEN product_name ILIKE %s THEN 1
            WHEN category = 'Extracts' THEN 2
            ELSE 3
        END,
        unit_price
    LIMIT 10
""", ('%shatter%', '%shatter%', '%shatter%', '%shatter%'))

results = cur.fetchall()
if results:
    for r in results:
        print(f"   {r['product_name']} | {r['category']} | ${r['unit_price']:.2f}")
else:
    print("   NO SHATTER PRODUCTS FOUND!")

# 2. Show all Extract category products
print("\n2. All products in 'Extracts' category:")
cur.execute("""
    SELECT product_name, brand, unit_price
    FROM products
    WHERE category = 'Extracts'
    ORDER BY unit_price
    LIMIT 10
""")

results = cur.fetchall()
if results:
    for r in results:
        print(f"   {r['product_name']} | {r['brand']} | ${r['unit_price']:.2f}")
else:
    print("   NO EXTRACTS FOUND!")

# 3. Search for concentrates/dabs
print("\n3. Products related to dabs/concentrates:")
cur.execute("""
    SELECT DISTINCT product_name, category, unit_price
    FROM products
    WHERE category IN ('Extracts', 'Vapes')
       OR product_name ILIKE ANY(ARRAY['%dab%', '%concentrate%', '%wax%', '%resin%', '%rosin%'])
    ORDER BY unit_price
    LIMIT 10
""")

results = cur.fetchall()
if results:
    for r in results:
        print(f"   {r['product_name']} | {r['category']} | ${r['unit_price']:.2f}")
else:
    print("   NO DAB PRODUCTS FOUND!")

# 4. List all categories
print("\n4. All available categories:")
cur.execute("""
    SELECT DISTINCT category, COUNT(*) as product_count
    FROM products
    WHERE category IS NOT NULL
    GROUP BY category
    ORDER BY product_count DESC
""")

for r in cur.fetchall():
    print(f"   {r['category']}: {r['product_count']} products")

conn.close()