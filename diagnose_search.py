#!/usr/bin/env python3
"""
Diagnose the product search issue
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# Database configuration (from config.py)
db_config = {
    'host': 'localhost',
    'port': 5434,
    'database': 'ai_engine',
    'user': 'weedgo',
    'password': 'your_password_here'
}

def diagnose_search():
    """Diagnose why search is returning wrong results"""
    
    conn = psycopg2.connect(**db_config, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    
    print("=== DIAGNOSING PRODUCT SEARCH ISSUE ===\n")
    
    # 1. Check categories in database
    print("1. Available categories in database:")
    cur.execute("SELECT DISTINCT category FROM products ORDER BY category")
    categories = [row['category'] for row in cur.fetchall()]
    for cat in categories[:10]:
        print(f"   - {cat}")
    print()
    
    # 2. Check sativa flower products
    print("2. Sativa FLOWER products between $10-20:")
    cur.execute("""
        SELECT product_name, category, unit_price, thc_max_percent
        FROM products 
        WHERE (product_name ILIKE '%sativa%' OR brand ILIKE '%sativa%')
        AND category = 'Flower'
        AND unit_price >= 10 
        AND unit_price <= 20
        ORDER BY unit_price
        LIMIT 5
    """)
    results = cur.fetchall()
    if results:
        for r in results:
            print(f"   - {r['product_name']} | {r['category']} | ${r['unit_price']:.2f} | THC: {r['thc_max_percent']}%")
    else:
        print("   NO RESULTS FOUND!")
    print()
    
    # 3. Test the actual query being generated
    print("3. Testing the ACTUAL query from search endpoint:")
    print("   Query: 'sativa', Category: 'Flower', Price: $10-20")
    
    # This mimics the exact logic from api_server.py
    query = """
        SELECT * FROM products
        WHERE product_name ILIKE %s OR brand ILIKE %s
    """
    params = ['%sativa%', '%sativa%']
    
    # Add filters (as done in api_server.py)
    query += " AND category = %s"
    params.append('Flower')
    
    query += " AND unit_price >= %s"
    params.append(10)
    
    query += " AND unit_price <= %s"
    params.append(20)
    
    query += " ORDER BY unit_price ASC LIMIT 5"
    
    print(f"   SQL: {query}")
    print(f"   Params: {params}")
    print()
    
    cur.execute(query, params)
    results = cur.fetchall()
    
    print(f"   Results found: {len(results)}")
    if results:
        for r in results:
            print(f"   - {r['product_name']} | {r['category']} | ${r['unit_price']:.2f}")
    else:
        print("   NO RESULTS! This explains the bug.")
    print()
    
    # 4. Check what's actually being returned
    print("4. What search IS returning (without filters):")
    cur.execute("""
        SELECT product_name, category, unit_price
        FROM products
        WHERE product_name ILIKE %s OR brand ILIKE %s
        ORDER BY unit_price ASC
        LIMIT 5
    """, ('%sativa%', '%sativa%'))
    
    results = cur.fetchall()
    for r in results:
        print(f"   - {r['product_name']} | {r['category']} | ${r['unit_price']:.2f}")
    print()
    
    # 5. Check case sensitivity
    print("5. Testing case sensitivity:")
    for cat in ['Flower', 'flower', 'FLOWER']:
        cur.execute("SELECT COUNT(*) as count FROM products WHERE category = %s", (cat,))
        count = cur.fetchone()['count']
        print(f"   category = '{cat}': {count} products")
    
    conn.close()

if __name__ == "__main__":
    diagnose_search()