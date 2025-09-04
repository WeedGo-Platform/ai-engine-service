#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import RealDictCursor

# Try both passwords to find the correct one
passwords = ['your_password_here', 'weedgo']

for password in passwords:
    try:
        print(f"\nTrying password: {password}")
        conn = psycopg2.connect(
            host='localhost',
            port=5434,
            database='ai_engine',
            user='weedgo',
            password=password
        )
        print(f"✓ Connected with password: {password}")
        
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check for products table in all schemas
        cur.execute("""
            SELECT schemaname, tablename 
            FROM pg_tables 
            WHERE tablename = 'products'
        """)
        tables = cur.fetchall()
        print(f"\nProducts tables found: {tables}")
        
        # Try default schema first
        try:
            cur.execute("SELECT COUNT(*) as count FROM products")
            result = cur.fetchone()
            print(f"Default schema products count: {result['count']}")
            
            # Get sample data
            cur.execute("SELECT product_name, brand, category FROM products LIMIT 5")
            samples = cur.fetchall()
            print("\nSample products from default schema:")
            for p in samples:
                print(f"  - {p['product_name']} | {p['brand']} | {p['category']}")
                
            # Check column count
            cur.execute("""
                SELECT COUNT(*) as col_count 
                FROM information_schema.columns 
                WHERE table_name = 'products' 
                AND table_schema = 'public'
            """)
            col_info = cur.fetchone()
            print(f"\nColumns in products table: {col_info['col_count']}")
            
        except psycopg2.Error as e:
            print(f"No products table in default schema: {e}")
        
        # Try cannabis_data schema
        try:
            cur.execute("SELECT COUNT(*) as count FROM cannabis_data.products")
            result = cur.fetchone()
            print(f"\nCannabis_data schema products count: {result['count']}")
            
            # Check column count
            cur.execute("""
                SELECT COUNT(*) as col_count 
                FROM information_schema.columns 
                WHERE table_name = 'products' 
                AND table_schema = 'cannabis_data'
            """)
            col_info = cur.fetchone()
            print(f"Columns in cannabis_data.products table: {col_info['col_count']}")
            
        except psycopg2.Error as e:
            print(f"No products table in cannabis_data schema: {e}")
        
        conn.close()
        break
        
    except psycopg2.Error as e:
        print(f"Failed with password {password}: {e}")
        continue