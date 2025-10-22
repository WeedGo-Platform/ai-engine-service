#!/usr/bin/env python3
"""
Migration 009: Run model usage tracking and tenant tokens migration
"""
import os
import sys
import asyncio
import asyncpg
from pathlib import Path

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5434')),
    'database': os.getenv('DB_NAME', 'ai_engine'),
    'user': os.getenv('DB_USER', 'weedgo'),
    'password': os.getenv('DB_PASSWORD', 'your_password_here')
}

# LLM Provider API Keys (from environment)
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
LLM7_API_KEY = os.getenv('LLM7_API_KEY', '')


async def run_migration():
    """Run the migration SQL and migrate tokens"""
    print("=" * 80)
    print("Running Migration 009: Model Usage Tracking & Tenant Tokens")
    print("=" * 80)
    
    # Read SQL migration file
    migration_file = Path(__file__).parent / '009_add_model_usage_and_tenant_tokens.sql'
    
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        sys.exit(1)
    
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    print(f"\n📄 Read migration SQL from: {migration_file}")
    
    # Connect to database
    print(f"\n🔌 Connecting to database: {DB_CONFIG['database']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}")
    
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        print("✅ Database connected successfully")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        sys.exit(1)
    
    try:
        # Run migration SQL
        print("\n🚀 Executing migration SQL...")
        await conn.execute(migration_sql)
        print("✅ Migration SQL executed successfully")
        
        # Get the first tenant (should only be one)
        print("\n🔍 Finding first tenant to migrate tokens...")
        tenant = await conn.fetchrow("SELECT id, name FROM tenants LIMIT 1")
        
        if not tenant:
            print("⚠️  No tenants found in database. Skipping token migration.")
        else:
            tenant_id = tenant['id']
            tenant_name = tenant['name']
            print(f"✅ Found tenant: {tenant_name} (ID: {tenant_id})")
            
            # Check if any API keys are available
            if not any([GROQ_API_KEY, OPENROUTER_API_KEY, LLM7_API_KEY]):
                print("\n⚠️  No API keys found in environment variables:")
                print("    - GROQ_API_KEY")
                print("    - OPENROUTER_API_KEY")
                print("    - LLM7_API_KEY")
                print("    Skipping token migration. Tokens will need to be set via UI.")
            else:
                # Migrate tokens to tenant
                print(f"\n🔑 Migrating API keys to tenant '{tenant_name}'...")
                
                keys_found = []
                if GROQ_API_KEY:
                    keys_found.append("Groq")
                if OPENROUTER_API_KEY:
                    keys_found.append("OpenRouter")
                if LLM7_API_KEY:
                    keys_found.append("LLM7")
                
                print(f"    Found keys for: {', '.join(keys_found)}")
                
                await conn.execute(
                    "SELECT migrate_system_tokens_to_tenant($1, $2, $3, $4)",
                    tenant_id,
                    GROQ_API_KEY or '',
                    OPENROUTER_API_KEY or '',
                    LLM7_API_KEY or ''
                )
                print("✅ API keys migrated to tenant successfully")
                
                # Verify migration
                result = await conn.fetchrow(
                    "SELECT llm_tokens FROM tenants WHERE id = $1",
                    tenant_id
                )
                
                if result and result['llm_tokens']:
                    token_keys = list(result['llm_tokens'].keys())
                    print(f"✅ Verified: Tenant now has tokens for: {', '.join(token_keys)}")
        
        # Show summary
        print("\n" + "=" * 80)
        print("✅ Migration 009 completed successfully!")
        print("=" * 80)
        print("\nChanges applied:")
        print("  ✓ Added 'llm_tokens' JSONB column to tenants table")
        print("  ✓ Added 'inference_config' JSONB column to tenants table")
        print("  ✓ Created 'model_usage_stats' table for real-time tracking")
        print("  ✓ Created 'model_usage_summary' materialized view")
        print("  ✓ Created 'model_usage_stats_24h' view for recent stats")
        print("  ✓ Created helper functions for usage tracking")
        print("  ✓ Created indexes for optimal query performance")
        if tenant:
            print(f"  ✓ Migrated API keys to tenant: {tenant_name}")
        
        print("\nNext steps:")
        print("  1. Implement backend endpoints for token/config management")
        print("  2. Update LLM router to use tenant-specific tokens")
        print("  3. Add usage tracking to all LLM requests")
        print("  4. Create frontend UI for token and provider management")
        print("  5. Set up cron job to refresh materialized view hourly:")
        print("     */60 * * * * psql -d ai_engine -c 'SELECT refresh_model_usage_summary();'")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await conn.close()
        print("\n🔌 Database connection closed")


if __name__ == '__main__':
    asyncio.run(run_migration())
