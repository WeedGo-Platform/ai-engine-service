#!/usr/bin/env python3
"""
Apply missing tables migration for AGI system
Ensures all required tables exist with proper schema
"""

import asyncio
import asyncpg
import logging
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agi.config.agi_config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_pgvector_extension(conn):
    """Check if pgvector extension is available"""
    try:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        logger.info("✅ pgvector extension enabled")
        return True
    except Exception as e:
        logger.warning(f"⚠️ pgvector extension not available: {e}")
        logger.warning("  Falling back to JSONB storage for embeddings")
        return False


async def apply_migration():
    """Apply the missing tables migration"""
    config = get_config()

    try:
        # Connect to database
        conn = await asyncpg.connect(
            host=config.database.host,
            port=config.database.port,
            user=config.database.user,
            password=config.database.password,
            database=config.database.database
        )

        logger.info(f"Connected to database {config.database.database}")

        # Check for pgvector extension
        has_pgvector = await check_pgvector_extension(conn)

        # Read migration file
        migration_file = Path(__file__).parent / "create_missing_tables.sql"
        with open(migration_file, 'r') as f:
            migration_sql = f.read()

        # If pgvector is not available, modify the SQL
        if not has_pgvector:
            logger.info("Modifying migration for non-pgvector database...")
            migration_sql = migration_sql.replace("VECTOR(384)", "JSONB")
            migration_sql = migration_sql.replace(
                "USING ivfflat (embedding vector_cosine_ops)",
                "USING gin (embedding_json)"
            )

        # Split into individual statements
        statements = []
        current_statement = []

        for line in migration_sql.split('\n'):
            # Skip comments
            if line.strip().startswith('--') or not line.strip():
                continue

            current_statement.append(line)

            # Check if statement is complete
            if line.strip().endswith(';'):
                stmt = '\n'.join(current_statement)
                if stmt.strip():
                    statements.append(stmt)
                current_statement = []

        # Execute each statement
        total = len(statements)
        logger.info(f"Executing {total} SQL statements...")

        for i, stmt in enumerate(statements, 1):
            try:
                # Extract table name for logging
                if 'CREATE TABLE' in stmt:
                    table_name = stmt.split('CREATE TABLE IF NOT EXISTS')[1].split('(')[0].strip()
                    logger.info(f"  [{i}/{total}] Creating table {table_name}")
                elif 'CREATE INDEX' in stmt:
                    index_name = stmt.split('CREATE INDEX IF NOT EXISTS')[1].split('\n')[0].strip()
                    logger.info(f"  [{i}/{total}] Creating index {index_name}")
                elif 'ALTER TABLE' in stmt:
                    table_name = stmt.split('ALTER TABLE')[1].split('\n')[0].strip()
                    logger.info(f"  [{i}/{total}] Altering table {table_name}")
                else:
                    logger.info(f"  [{i}/{total}] Executing statement")

                await conn.execute(stmt)

            except asyncpg.exceptions.DuplicateTableError:
                logger.info(f"    Table already exists, skipping")
            except asyncpg.exceptions.DuplicateObjectError:
                logger.info(f"    Object already exists, skipping")
            except Exception as e:
                logger.error(f"    Error: {e}")
                # Continue with other statements

        # Verify tables were created
        logger.info("\n✅ Verifying created tables...")

        tables_to_check = [
            'document_embeddings',
            'document_chunks',
            'learning_feedback',
            'agent_memories',
            'security_audit_log',
            'api_keys',
            'users'
        ]

        for table in tables_to_check:
            exists = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'agi' AND tablename = $1)",
                table
            )
            if exists:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM agi.{table}")
                logger.info(f"  ✅ agi.{table} exists ({count} rows)")
            else:
                logger.error(f"  ❌ agi.{table} not found")

        # Check if metrics.session_id column was added
        has_session_id = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_schema = 'agi'
                AND table_name = 'metrics'
                AND column_name = 'session_id'
            )
        """)

        if has_session_id:
            logger.info("  ✅ agi.metrics.session_id column added")
        else:
            logger.error("  ❌ agi.metrics.session_id column not found")

        await conn.close()
        logger.info("\n🎉 Migration completed successfully!")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


async def rollback_migration():
    """Rollback the migration if needed"""
    config = get_config()

    try:
        conn = await asyncpg.connect(
            host=config.database.host,
            port=config.database.port,
            user=config.database.user,
            password=config.database.password,
            database=config.database.database
        )

        logger.info("Rolling back migration...")

        tables_to_drop = [
            'agi.security_audit_log',
            'agi.agent_memories',
            'agi.learning_feedback',
            'agi.document_chunks',
            'agi.document_embeddings',
            'agi.api_keys',
            'agi.users'
        ]

        for table in tables_to_drop:
            await conn.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
            logger.info(f"  Dropped {table}")

        # Remove session_id column from metrics
        await conn.execute("""
            ALTER TABLE agi.metrics
            DROP COLUMN IF EXISTS session_id
        """)
        logger.info("  Removed session_id column from metrics")

        await conn.close()
        logger.info("Rollback completed")

    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Apply AGI database migration")
    parser.add_argument('--rollback', action='store_true', help="Rollback the migration")
    args = parser.parse_args()

    if args.rollback:
        asyncio.run(rollback_migration())
    else:
        asyncio.run(apply_migration())