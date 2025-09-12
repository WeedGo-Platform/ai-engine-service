#!/usr/bin/env python3
"""
Quick setup script for accessories system with RAW papers test data
"""

import psycopg2
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'ai_engine',
    'user': 'weedgo',
    'password': 'your_password_here'
}

def setup_accessories():
    """Set up accessories tables and test data"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Create simplified tables
        logger.info("Creating accessories tables...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accessory_categories (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                slug VARCHAR(100) UNIQUE NOT NULL,
                icon VARCHAR(50),
                sort_order INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accessories_catalog (
                id SERIAL PRIMARY KEY,
                barcode VARCHAR(50) UNIQUE,
                sku VARCHAR(100) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                brand VARCHAR(100),
                category_id INTEGER REFERENCES accessory_categories(id),
                description TEXT,
                image_url TEXT,
                msrp DECIMAL(10,2),
                default_cost DECIMAL(10,2),
                suggested_retail DECIMAL(10,2),
                data_source VARCHAR(50),
                confidence_score DECIMAL(3,2),
                verified BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accessories_inventory (
                id SERIAL PRIMARY KEY,
                store_id VARCHAR(50) NOT NULL,
                accessory_id INTEGER NOT NULL REFERENCES accessories_catalog(id),
                quantity INTEGER NOT NULL DEFAULT 0,
                cost_price DECIMAL(10,2) NOT NULL,
                retail_price DECIMAL(10,2) NOT NULL,
                min_stock_level INTEGER DEFAULT 5,
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(store_id, accessory_id)
            )
        """)
        
        # Insert categories
        logger.info("Adding categories...")
        categories = [
            ('Rolling Papers', 'rolling-papers', '📜', 1),
            ('Grinders', 'grinders', '⚙️', 2),
            ('Pipes & Bongs', 'pipes-bongs', '🚬', 3),
            ('Vaporizers', 'vaporizers', '💨', 4),
            ('Storage', 'storage', '📦', 5),
            ('Lighters', 'lighters', '🔥', 6),
            ('Other', 'other', '📌', 99)
        ]
        
        for cat in categories:
            cursor.execute("""
                INSERT INTO accessory_categories (name, slug, icon, sort_order)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (slug) DO NOTHING
            """, cat)
        
        # Add RAW papers test data
        logger.info("Adding RAW papers test data...")
        
        # Get rolling papers category ID
        cursor.execute("SELECT id FROM accessory_categories WHERE slug = 'rolling-papers'")
        category_id = cursor.fetchone()[0]
        
        # Insert RAW Classic 1¼ papers (barcode from your screenshot: 716165177395)
        cursor.execute("""
            INSERT INTO accessories_catalog 
            (barcode, sku, name, brand, category_id, description, image_url, 
             msrp, default_cost, suggested_retail, data_source, confidence_score, verified)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (barcode) DO UPDATE SET
                name = EXCLUDED.name,
                brand = EXCLUDED.brand,
                verified = true
            RETURNING id
        """, (
            '716165177395',  # Actual RAW papers barcode
            'RAW-CLASSIC-125',
            'RAW Classic 1¼ Size Rolling Papers',
            'RAW',
            category_id,
            'RAW Classic 1¼ size is the original size. Also known as "Spanish Size", 1¼ papers were the standard size of all rolling papers starting hundreds of years ago.',
            'https://rawthentic.com/wp-content/uploads/2018/08/raw-classic-1-14-papers.jpg',
            2.99,  # MSRP
            1.50,  # Cost
            2.99,  # Retail
            'manual',
            1.0,
            True
        ))
        
        # Add more RAW products for testing
        raw_products = [
            ('716165174486', 'RAW-CLASSIC-KS', 'RAW Classic King Size Slim Rolling Papers', 'RAW', 3.49),
            ('716165250432', 'RAW-CONES-3PK', 'RAW Classic Pre-Rolled Cones 3-Pack', 'RAW', 4.99),
            ('716165178385', 'RAW-TIPS', 'RAW Filter Tips', 'RAW', 1.99),
            ('716165179382', 'RAW-TRAY-SM', 'RAW Metal Rolling Tray Small', 'RAW', 9.99),
        ]
        
        for barcode, sku, name, brand, price in raw_products:
            cursor.execute("""
                INSERT INTO accessories_catalog 
                (barcode, sku, name, brand, category_id, msrp, default_cost, suggested_retail, 
                 data_source, confidence_score, verified)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (barcode) DO NOTHING
            """, (
                barcode, sku, name, brand, category_id,
                price, price * 0.5, price,
                'manual', 1.0, True
            ))
        
        conn.commit()
        logger.info("✅ Accessories system setup complete!")
        
        # Verify the data
        cursor.execute("""
            SELECT barcode, name, brand, suggested_retail 
            FROM accessories_catalog 
            WHERE barcode = '716165177395'
        """)
        result = cursor.fetchone()
        if result:
            logger.info(f"✅ Test barcode verified: {result[1]} - ${result[3]}")
        
        return True
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    if setup_accessories():
        print("\n✅ Accessories system is ready!")
        print("Test barcode 716165177395 (RAW Classic 1¼ papers) is now in the database.")
    else:
        print("\n❌ Setup failed. Check the logs above.")
        sys.exit(1)