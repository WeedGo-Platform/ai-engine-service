#!/usr/bin/env python3
"""Check if Britane product is in database"""

import psycopg2

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'ai_engine',
    'user': 'weedgo',
    'password': 'weedgo123'
}

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

# Check for the barcode
barcode = "6528273015278"
cursor.execute("""
    SELECT id, barcode, name, brand, category_id, msrp
    FROM accessories_catalog
    WHERE barcode = %s
""", (barcode,))

result = cursor.fetchone()
if result:
    print(f"✅ Found in database:")
    print(f"   ID: {result[0]}")
    print(f"   Barcode: {result[1]}")
    print(f"   Name: {result[2]}")
    print(f"   Brand: {result[3]}")
    print(f"   Category ID: {result[4]}")
    print(f"   Price: ${result[5]}")
else:
    print(f"❌ Barcode {barcode} not found in database")
    
    # Check all barcodes
    cursor.execute("SELECT barcode, name FROM accessories_catalog")
    all_products = cursor.fetchall()
    print(f"\nTotal products in database: {len(all_products)}")
    for bc, name in all_products[:10]:
        print(f"  {bc}: {name}")

cursor.close()
conn.close()