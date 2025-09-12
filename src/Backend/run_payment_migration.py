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
        with open('migrations/create_payment_schema.sql', 'r') as f:
            migration_sql = f.read()
        
        # Execute migration
        await conn.execute(migration_sql)
        print("✅ Payment schema created successfully!")
        
        # Verify tables were created
        tables = await conn.fetch("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename IN (
                'payment_providers', 'payment_methods', 'payment_transactions',
                'payment_refunds', 'payment_settlements', 'payment_subscriptions',
                'payment_webhooks', 'payment_disputes', 'payment_metrics'
            )
            ORDER BY tablename
        """)
        
        print("\n📊 Created tables:")
        for table in tables:
            print(f"  ✓ {table['tablename']}")
        
        # Check payment providers
        providers = await conn.fetch("SELECT name, provider_type, is_active FROM payment_providers ORDER BY is_default DESC, name")
        print("\n💳 Payment providers configured:")
        for provider in providers:
            status = "✓" if provider['is_active'] else "✗"
            print(f"  {status} {provider['name']} ({provider['provider_type']})")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migration())