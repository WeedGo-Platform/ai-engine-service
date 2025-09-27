"""
Run API keys table migration
"""
import asyncio
import asyncpg
import hashlib
from agi.config.agi_config import get_config

async def run_migration():
    config = get_config().database

    # Connect to database
    conn = await asyncpg.connect(
        host=config.host,
        port=config.port,
        user=config.user,
        password=config.password,
        database=config.database
    )

    try:
        # Read SQL file
        with open('agi/migrations/add_api_keys_table.sql', 'r') as f:
            sql = f.read()

        # Execute migration
        await conn.execute(sql)
        print("✅ API keys table migration completed successfully")

        # Verify table was created
        result = await conn.fetchval("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'agi'
            AND table_name = 'api_keys'
        """)

        if result > 0:
            print("✅ API keys table verified")

            # Check if test key was inserted
            test_key_hash = hashlib.sha256(b'agi_test_key_123').hexdigest()
            test_key = await conn.fetchrow("""
                SELECT * FROM agi.api_keys
                WHERE key_hash = $1
            """, test_key_hash)

            if test_key:
                print(f"✅ Test API key created: key_name={test_key['key_name']}")
        else:
            print("❌ API keys table not found")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migration())