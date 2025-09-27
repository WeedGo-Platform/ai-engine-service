"""
Check existing api_keys table structure
"""
import asyncio
import asyncpg
from agi.config.agi_config import get_config

async def check_table():
    config = get_config().database

    conn = await asyncpg.connect(
        host=config.host,
        port=config.port,
        user=config.user,
        password=config.password,
        database=config.database
    )

    try:
        # Check if table exists
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'agi'
                AND table_name = 'api_keys'
            )
        """)

        print(f"Table agi.api_keys exists: {exists}")

        if exists:
            # Get column information
            columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'agi'
                AND table_name = 'api_keys'
                ORDER BY ordinal_position
            """)

            print("\nExisting columns:")
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")

            # Check for data
            count = await conn.fetchval("SELECT COUNT(*) FROM agi.api_keys")
            print(f"\nRows in table: {count}")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_table())