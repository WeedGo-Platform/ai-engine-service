#!/usr/bin/env python3
import asyncio
import asyncpg
import os

async def run_migration():
    # Database connection
    conn = await asyncpg.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5434)),
        database=os.getenv('DB_NAME', 'ai_engine'),
        user=os.getenv('DB_USER', 'weedgo'),
        password=os.getenv('DB_PASSWORD', 'weedgo123')
    )
    
    try:
        # Read migration file
        with open('migrations/create_pricing_promotions_schema.sql', 'r') as f:
            migration_sql = f.read()
        
        # Execute migration
        await conn.execute(migration_sql)
        print("✅ Pricing and promotions schema created successfully!")
        
        # Verify tables were created
        tables = await conn.fetch("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename IN (
                'price_tiers', 'promotions', 'bundle_deals', 
                'customer_pricing_rules', 'product_recommendations',
                'discount_codes', 'promotion_usage', 'dynamic_pricing_rules',
                'price_history', 'recommendation_metrics'
            )
            ORDER BY tablename
        """)
        
        print("\n📊 Created tables:")
        for table in tables:
            print(f"  ✓ {table['tablename']}")
        
        # Check sample data
        tiers = await conn.fetch("SELECT name, discount_percentage FROM price_tiers ORDER BY priority")
        print("\n💰 Price tiers:")
        for tier in tiers:
            print(f"  • {tier['name']}: {tier['discount_percentage']}% discount")
        
        promos = await conn.fetch("SELECT code, name, discount_value FROM promotions WHERE active = true")
        print("\n🎁 Active promotions:")
        for promo in promos:
            print(f"  • {promo['code']}: {promo['name']} ({promo['discount_value']}% off)")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migration())