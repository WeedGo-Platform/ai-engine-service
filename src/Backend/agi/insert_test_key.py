"""
Insert a test API key into the existing table
"""
import asyncio
import asyncpg
import hashlib
from datetime import datetime, timedelta
from agi.config.agi_config import get_config

async def insert_test_key():
    config = get_config().database

    conn = await asyncpg.connect(
        host=config.host,
        port=config.port,
        user=config.user,
        password=config.password,
        database=config.database
    )

    try:
        # Create test key hash
        test_key = "agi_test_key_123"
        key_hash = hashlib.sha256(test_key.encode()).hexdigest()

        # Check if key already exists
        existing = await conn.fetchval("""
            SELECT id FROM agi.api_keys
            WHERE key_hash = $1
        """, key_hash)

        if existing:
            print(f"Test key already exists with ID: {existing}")
            return

        # Insert test key
        key_id = await conn.fetchval("""
            INSERT INTO agi.api_keys (
                key_hash,
                name,
                user_id,
                tenant_id,
                permissions,
                rate_limit,
                is_active,
                expires_at,
                created_at,
                metadata
            ) VALUES (
                $1,
                'test_key',
                'system',
                'default',
                $2::jsonb,
                1000,
                true,
                $3,
                CURRENT_TIMESTAMP,
                $4::jsonb
            ) RETURNING id
        """,
            key_hash,
            '["read", "write", "admin"]',
            datetime.now() + timedelta(days=365),
            '{"description": "Default test API key for development"}'
        )

        print(f"✅ Test API key created with ID: {key_id}")
        print(f"✅ Key value: {test_key}")
        print(f"✅ Key hash: {key_hash}")

    except Exception as e:
        print(f"❌ Failed to insert test key: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(insert_test_key())