#!/usr/bin/env python3
"""
Create essential tables for dashboard
"""

import asyncio
import asyncpg
import os
import asyncpg
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_tables():
    conn = await asyncpg.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5434)),
        database=os.getenv('DB_NAME', 'ai_engine'),
        user=os.getenv('DB_USER', 'weedgo'),
        password=os.getenv('DB_PASSWORD', 'weedgo123')
    )
    
    try:
        # 1. Create products table
        logger.info("Creating products table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                sku VARCHAR(100) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                category VARCHAR(100),
                subcategory VARCHAR(100),
                brand VARCHAR(100),
                supplier VARCHAR(100),
                unit_price DECIMAL(10, 2),
                thc_content DECIMAL(5, 2),
                cbd_content DECIMAL(5, 2),
                strain_type VARCHAR(50),
                terpenes JSONB,
                effects JSONB,
                medical_benefits JSONB,
                image_url TEXT,
                tags JSONB,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("✓ Products table created")
        
        # 2. Copy data from product_catalog if exists
        logger.info("Copying data from product_catalog...")
        result = await conn.execute("""
            INSERT INTO products (
                sku, name, description, category, subcategory, brand, supplier,
                unit_price, thc_content, cbd_content, strain_type, terpenes,
                effects, medical_benefits, image_url, tags, is_active
            )
            SELECT 
                sku, name, description, category, subcategory, brand, supplier,
                unit_price, thc_content, cbd_content, strain_type, terpenes,
                effects, medical_benefits, image_url, tags, is_active
            FROM product_catalog
            ON CONFLICT (sku) DO NOTHING
        """)
        logger.info(f"✓ Copied {result.split()[-1]} products from product_catalog")
        
        # 3. Update suppliers table
        logger.info("Updating suppliers table...")
        await conn.execute("""
            ALTER TABLE suppliers 
            ADD COLUMN IF NOT EXISTS city VARCHAR(100),
            ADD COLUMN IF NOT EXISTS state VARCHAR(50),
            ADD COLUMN IF NOT EXISTS postal_code VARCHAR(20),
            ADD COLUMN IF NOT EXISTS country VARCHAR(100),
            ADD COLUMN IF NOT EXISTS notes TEXT
        """)
        logger.info("✓ Suppliers table updated")
        
        # 4. Create profiles table
        logger.info("Creating profiles table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                phone VARCHAR(20),
                date_of_birth DATE,
                address TEXT,
                city VARCHAR(100),
                state VARCHAR(50),
                postal_code VARCHAR(20),
                country VARCHAR(100),
                loyalty_points INTEGER DEFAULT 0,
                customer_type VARCHAR(50) DEFAULT 'regular',
                preferred_payment_method VARCHAR(50),
                marketing_consent BOOLEAN DEFAULT false,
                notes TEXT,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("✓ Customers table created")
        
        # 5. Update orders table
        logger.info("Updating orders table...")
        await conn.execute("""
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS order_number VARCHAR(50),
            ADD COLUMN IF NOT EXISTS customer_name VARCHAR(255),
            ADD COLUMN IF NOT EXISTS customer_email VARCHAR(255),
            ADD COLUMN IF NOT EXISTS delivery_address TEXT,
            ADD COLUMN IF NOT EXISTS payment_method VARCHAR(50),
            ADD COLUMN IF NOT EXISTS payment_status VARCHAR(50) DEFAULT 'pending',
            ADD COLUMN IF NOT EXISTS delivery_date TIMESTAMP,
            ADD COLUMN IF NOT EXISTS tracking_number VARCHAR(100),
            ADD COLUMN IF NOT EXISTS discount_amount DECIMAL(10, 2) DEFAULT 0,
            ADD COLUMN IF NOT EXISTS tax_amount DECIMAL(10, 2) DEFAULT 0,
            ADD COLUMN IF NOT EXISTS shipping_cost DECIMAL(10, 2) DEFAULT 0,
            ADD COLUMN IF NOT EXISTS notes TEXT,
            ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'pending',
            ADD COLUMN IF NOT EXISTS customer_id UUID
        """)
        logger.info("✓ Orders table updated")
        
        # 6. Generate order numbers for existing orders
        logger.info("Generating order numbers...")
        await conn.execute("""
            UPDATE orders 
            SET order_number = 'ORD-' || EXTRACT(YEAR FROM created_at)::text || '-' || LPAD(id::text, 6, '0')
            WHERE order_number IS NULL
        """)
        logger.info("✓ Order numbers generated")
        
        # 7. Insert sample products if empty
        count = await conn.fetchval("SELECT COUNT(*) FROM products")
        if count == 0:
            logger.info("Inserting sample products...")
            await conn.execute("""
                INSERT INTO products (sku, name, description, category, unit_price, thc_content, cbd_content, strain_type, is_active)
                VALUES 
                    ('SKU-001', 'Purple Haze', 'Classic sativa strain with uplifting effects', 'Flower', 45.00, 18.5, 0.5, 'Sativa', true),
                    ('SKU-002', 'OG Kush', 'Popular indica strain for relaxation', 'Flower', 50.00, 22.0, 0.3, 'Indica', true),
                    ('SKU-003', 'Blue Dream', 'Balanced hybrid with calming effects', 'Flower', 48.00, 20.0, 2.0, 'Hybrid', true),
                    ('SKU-004', 'THC Gummies', 'Fruit-flavored edibles 10mg each', 'Edibles', 25.00, 10.0, 0.0, null, true),
                    ('SKU-005', 'CBD Tincture', 'High-CBD oil for wellness', 'Tinctures', 60.00, 0.5, 20.0, null, true),
                    ('SKU-006', 'Vape Cartridge', 'Premium distillate cartridge', 'Vapes', 40.00, 85.0, 0.0, null, true),
                    ('SKU-007', 'Pre-Roll Pack', '5 pack of premium pre-rolls', 'Pre-Rolls', 35.00, 18.0, 0.5, 'Hybrid', true),
                    ('SKU-008', 'Hash Rosin', 'Solventless concentrate', 'Concentrates', 80.00, 75.0, 0.0, null, true),
                    ('SKU-009', 'CBD Balm', 'Topical relief balm', 'Topicals', 30.00, 0.0, 5.0, null, true),
                    ('SKU-010', 'Indica Capsules', 'Precise dosing capsules', 'Edibles', 45.00, 10.0, 0.0, 'Indica', true)
            """)
            logger.info("✓ Sample products inserted")
        
        # 8. Insert sample inventory for products
        logger.info("Creating inventory records...")
        await conn.execute("""
            INSERT INTO inventory (sku, quantity_on_hand, quantity_available, reorder_point, reorder_quantity)
            SELECT 
                sku, 
                50 + (random() * 100)::int,
                40 + (random() * 80)::int,
                20,
                50
            FROM products
            ON CONFLICT (sku) DO NOTHING
        """)
        logger.info("✓ Inventory records created")
        
        # 9. Insert sample suppliers if empty
        count = await conn.fetchval("SELECT COUNT(*) FROM suppliers WHERE city IS NOT NULL")
        if count == 0:
            logger.info("Inserting sample suppliers...")
            await conn.execute("""
                INSERT INTO suppliers (name, contact_person, email, phone, city, state, postal_code, country, payment_terms, is_active)
                VALUES 
                    ('Green Valley Farms', 'John Smith', 'john@greenvalley.com', '555-0001', 'Los Angeles', 'CA', '90001', 'USA', 'Net 30', true),
                    ('Pacific Coast Growers', 'Sarah Johnson', 'sarah@pcgrowers.com', '555-0002', 'San Francisco', 'CA', '94102', 'USA', 'Net 45', true),
                    ('Mountain High Organics', 'Mike Davis', 'mike@mountainhigh.com', '555-0003', 'Denver', 'CO', '80201', 'USA', 'Net 30', true),
                    ('Desert Sun Cultivators', 'Lisa Brown', 'lisa@desertsun.com', '555-0004', 'Phoenix', 'AZ', '85001', 'USA', 'Net 60', true),
                    ('Northern Lights LLC', 'Tom Wilson', 'tom@northernlights.com', '555-0005', 'Seattle', 'WA', '98101', 'USA', 'Net 30', true)
            """)
            logger.info("✓ Sample suppliers inserted")
        
        # 10. Insert sample profiles if empty
        count = await conn.fetchval("SELECT COUNT(*) FROM profiles")
        if count == 0:
            logger.info("Inserting sample profiles...")
            await conn.execute("""
                INSERT INTO profiles (email, first_name, last_name, phone, city, state, loyalty_points, is_active)
                VALUES 
                    ('alice@example.com', 'Alice', 'Anderson', '555-1001', 'Los Angeles', 'CA', 100, true),
                    ('bob@example.com', 'Bob', 'Brown', '555-1002', 'San Diego', 'CA', 250, true),
                    ('carol@example.com', 'Carol', 'Clark', '555-1003', 'San Francisco', 'CA', 50, true),
                    ('david@example.com', 'David', 'Davis', '555-1004', 'Sacramento', 'CA', 175, true),
                    ('emma@example.com', 'Emma', 'Evans', '555-1005', 'Oakland', 'CA', 300, true)
            """)
            logger.info("✓ Sample profiles inserted")
        
        logger.info("\n✅ All essential tables created and populated successfully!")
        
        # Verify
        products_count = await conn.fetchval("SELECT COUNT(*) FROM products")
        profiles_count = await conn.fetchval("SELECT COUNT(*) FROM profiles")
        suppliers_count = await conn.fetchval("SELECT COUNT(*) FROM suppliers WHERE city IS NOT NULL")
        inventory_count = await conn.fetchval("SELECT COUNT(*) FROM inventory")
        
        logger.info(f"\nDatabase Status:")
        logger.info(f"  - Products: {products_count} records")
        logger.info(f"  - Profiles: {profiles_count} records")
        logger.info(f"  - Suppliers: {suppliers_count} records")
        logger.info(f"  - Inventory: {inventory_count} records")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_tables())