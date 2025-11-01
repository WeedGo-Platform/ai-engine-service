"""
Seed script to populate database with sample cannabis products
"""

import asyncio
import asyncpg
import uuid
from datetime import datetime
from decimal import Decimal
import random

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'ai_engine',
    'user': 'weedgo',
    'password': 'weedgo123'
}

# Sample product data
SAMPLE_PRODUCTS = [
    # Flower products
    {
        'name': 'Pink Kush',
        'brand': 'Top Leaf',
        'category': 'Flower',
        'strain_type': 'Indica',
        'thc_percentage': 22.5,
        'cbd_percentage': 0.1,
        'price': 35.99,
        'size': '3.5g',
        'description': 'A potent indica strain with a sweet, floral aroma',
        'terpenes': ['Myrcene', 'Limonene', 'Caryophyllene']
    },
    {
        'name': 'Blue Dream',
        'brand': 'Aurora',
        'category': 'Flower',
        'strain_type': 'Hybrid',
        'thc_percentage': 18.0,
        'cbd_percentage': 2.0,
        'price': 32.99,
        'size': '3.5g',
        'description': 'Balanced hybrid with berry and herbal notes',
        'terpenes': ['Pinene', 'Myrcene', 'Caryophyllene']
    },
    {
        'name': 'Sour Diesel',
        'brand': 'Broken Coast',
        'category': 'Flower',
        'strain_type': 'Sativa',
        'thc_percentage': 20.0,
        'cbd_percentage': 0.5,
        'price': 42.99,
        'size': '3.5g',
        'description': 'Energizing sativa with diesel aroma',
        'terpenes': ['Limonene', 'Caryophyllene', 'Humulene']
    },
    {
        'name': 'Wedding Cake',
        'brand': 'Spinach',
        'category': 'Flower',
        'strain_type': 'Indica',
        'thc_percentage': 25.0,
        'cbd_percentage': 0.1,
        'price': 38.99,
        'size': '3.5g',
        'description': 'Sweet and tangy with relaxing effects',
        'terpenes': ['Limonene', 'Caryophyllene', 'Linalool']
    },
    
    # Pre-rolls
    {
        'name': 'Redees Pre-Rolls',
        'brand': 'Redecan',
        'category': 'Pre-Rolls',
        'strain_type': 'Hybrid',
        'thc_percentage': 19.0,
        'cbd_percentage': 0.5,
        'price': 24.99,
        'size': '10x0.35g',
        'description': 'Pack of 10 mini pre-rolls',
        'terpenes': ['Myrcene', 'Pinene']
    },
    {
        'name': 'Sage N Sour Pre-Roll',
        'brand': 'MTL Cannabis',
        'category': 'Pre-Rolls',
        'strain_type': 'Sativa',
        'thc_percentage': 21.0,
        'cbd_percentage': 0.1,
        'price': 12.99,
        'size': '3x0.5g',
        'description': 'Premium sativa pre-rolls',
        'terpenes': ['Terpinolene', 'Ocimene']
    },
    
    # Edibles
    {
        'name': 'Chocolate Bar',
        'brand': 'Bhang',
        'category': 'Edibles',
        'strain_type': None,
        'thc_percentage': 0.0,
        'cbd_percentage': 0.0,
        'thc_content_per_unit': 10.0,
        'price': 8.99,
        'size': '10mg',
        'description': 'Milk chocolate infused with THC',
        'ingredients': 'Cocoa, Sugar, Cannabis Extract'
    },
    {
        'name': 'Sour Gummies',
        'brand': 'Wana',
        'category': 'Edibles',
        'strain_type': None,
        'thc_percentage': 0.0,
        'cbd_percentage': 0.0,
        'thc_content_per_unit': 10.0,
        'price': 12.99,
        'size': '10mg x 5',
        'description': 'Sour fruit-flavored gummies',
        'ingredients': 'Gelatin, Sugar, Cannabis Extract, Natural Flavors'
    },
    {
        'name': 'Sparkling Water',
        'brand': 'Deep Space',
        'category': 'Beverages',
        'strain_type': None,
        'thc_percentage': 0.0,
        'cbd_percentage': 0.0,
        'thc_content_per_unit': 10.0,
        'price': 5.99,
        'size': '355ml',
        'description': 'Cannabis-infused sparkling water',
        'ingredients': 'Carbonated Water, Cannabis Extract, Natural Flavors'
    },
    
    # Concentrates
    {
        'name': 'Live Resin',
        'brand': 'Greybeard',
        'category': 'Concentrates',
        'strain_type': 'Indica',
        'thc_percentage': 75.0,
        'cbd_percentage': 2.0,
        'price': 45.99,
        'size': '1g',
        'description': 'Premium live resin concentrate',
        'extraction_process': 'CO2 Extraction'
    },
    {
        'name': 'Shatter',
        'brand': 'San Rafael',
        'category': 'Concentrates',
        'strain_type': 'Sativa',
        'thc_percentage': 80.0,
        'cbd_percentage': 1.0,
        'price': 39.99,
        'size': '1g',
        'description': 'Glass-like concentrate',
        'extraction_process': 'BHO Extraction'
    },
    
    # Vapes
    {
        'name': 'Mango Haze Cart',
        'brand': 'Good Supply',
        'category': 'Vapes',
        'strain_type': 'Sativa',
        'thc_percentage': 85.0,
        'cbd_percentage': 5.0,
        'price': 29.99,
        'size': '0.5g',
        'description': 'Tropical mango flavored vape cartridge',
        'terpenes': ['Myrcene', 'Pinene']
    },
    {
        'name': 'Disposable Vape Pen',
        'brand': 'Kolab',
        'category': 'Vapes',
        'strain_type': 'Hybrid',
        'thc_percentage': 82.0,
        'cbd_percentage': 2.0,
        'price': 34.99,
        'size': '0.3g',
        'description': 'All-in-one disposable vape pen',
        'terpenes': ['Limonene', 'Linalool']
    },
    
    # CBD Products
    {
        'name': 'CBD Oil',
        'brand': 'Solei',
        'category': 'Oils',
        'strain_type': None,
        'thc_percentage': 0.0,
        'cbd_percentage': 20.0,
        'price': 45.99,
        'size': '30ml',
        'description': 'Pure CBD oil tincture',
        'ingredients': 'MCT Oil, CBD Extract'
    },
    {
        'name': 'Balanced Oil',
        'brand': 'Tweed',
        'category': 'Oils',
        'strain_type': None,
        'thc_percentage': 10.0,
        'cbd_percentage': 10.0,
        'price': 39.99,
        'size': '30ml',
        'description': '1:1 THC:CBD ratio oil',
        'ingredients': 'MCT Oil, Cannabis Extract'
    }
]


async def seed_products():
    """Seed the database with sample products"""
    conn = None
    try:
        # Connect to database
        conn = await asyncpg.connect(**DB_CONFIG)
        print("Connected to database")
        
        # Clear existing data
        await conn.execute("DELETE FROM inventory")
        await conn.execute("DELETE FROM product_catalog")
        print("Cleared existing data")
        
        # Insert products
        for idx, product in enumerate(SAMPLE_PRODUCTS):
            product_id = str(uuid.uuid4())
            sku = f"SKU-{idx+1:04d}"
            
            # Insert into product_catalog
            await conn.execute("""
                INSERT INTO product_catalog (
                    id, sku, name, brand, category, sub_category,
                    strain_type, plant_type, size, unit_of_measure,
                    thc_percentage, cbd_percentage, 
                    thc_content_per_unit, cbd_content_per_unit,
                    unit_price, price,
                    short_description, description,
                    image_url, terpenes, ingredients,
                    extraction_process, ontario_grown, craft,
                    created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6,
                    $7, $8, $9, $10,
                    $11, $12, $13, $14,
                    $15, $16,
                    $17, $18,
                    $19, $20, $21,
                    $22, $23, $24,
                    $25, $26
                )
            """,
                product_id, sku, product['name'], product['brand'],
                product['category'], product.get('sub_category'),
                product.get('strain_type'), product.get('plant_type'),
                product.get('size'), product.get('unit_of_measure', 'g'),
                product.get('thc_percentage', 0.0), product.get('cbd_percentage', 0.0),
                product.get('thc_content_per_unit', 0.0), product.get('cbd_content_per_unit', 0.0),
                product['price'], product['price'],
                product['description'][:100] if len(product['description']) > 100 else product['description'],
                product['description'],
                f"/images/{product['category'].lower()}/{sku}.jpg",
                product.get('terpenes', []), product.get('ingredients'),
                product.get('extraction_process'), 
                random.choice([True, False]), random.choice([True, False]),
                datetime.now(), datetime.now()
            )
            
            # Insert into inventory
            await conn.execute("""
                INSERT INTO inventory (
                    id, product_id, sku, name,
                    quantity_on_hand, quantity_available, quantity_reserved,
                    reorder_point, reorder_quantity,
                    location, batch_lot,
                    created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4,
                    $5, $6, $7,
                    $8, $9,
                    $10, $11,
                    $12, $13
                )
            """,
                str(uuid.uuid4()), product_id, sku, product['name'],
                random.randint(50, 200),  # quantity_on_hand
                random.randint(30, 150),  # quantity_available
                random.randint(0, 20),    # quantity_reserved
                20.0,  # reorder_point
                50.0,  # reorder_quantity
                f"Shelf-{random.randint(1, 10)}-{random.choice(['A', 'B', 'C'])}",
                f"BATCH-{datetime.now().strftime('%Y%m')}-{random.randint(100, 999)}",
                datetime.now(), datetime.now()
            )
            
            print(f"Inserted product: {product['name']}")
        
        # Verify insertion
        count = await conn.fetchval("SELECT COUNT(*) FROM product_catalog")
        inv_count = await conn.fetchval("SELECT COUNT(*) FROM inventory")
        print(f"\nSuccessfully seeded {count} products in catalog and {inv_count} in inventory")
        
        # Test the view
        view_count = await conn.fetchval("SELECT COUNT(*) FROM inventory_products_view")
        print(f"Inventory products view shows {view_count} products")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        raise
    finally:
        if conn:
            await conn.close()


if __name__ == "__main__":
    asyncio.run(seed_products())