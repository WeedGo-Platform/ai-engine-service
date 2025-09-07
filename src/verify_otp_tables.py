#!/usr/bin/env python3
"""Verify OTP tables were created successfully"""

import asyncio
import asyncpg
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_tables():
    """Check if OTP tables exist in database"""
    conn = None
    try:
        # Connect to database
        conn = await asyncpg.connect(
            host='localhost',
            port=5434,
            database='ai_engine',
            user='weedgo',
            password='weedgo123'
        )
        
        # Check for OTP tables
        tables = await conn.fetch("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename IN ('otp_codes', 'otp_rate_limits', 'communication_logs')
            ORDER BY tablename
        """)
        
        if tables:
            logger.info("✅ OTP tables found:")
            for table in tables:
                logger.info(f"  - {table['tablename']}")
                
            # Get count of each table
            for table in tables:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table['tablename']}")
                logger.info(f"    {table['tablename']}: {count} records")
                
            # Check functions
            functions = await conn.fetch("""
                SELECT proname FROM pg_proc 
                WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
                AND proname IN ('check_otp_rate_limit', 'cleanup_expired_otp_codes')
            """)
            
            if functions:
                logger.info("\n✅ OTP functions found:")
                for func in functions:
                    logger.info(f"  - {func['proname']}()")
        else:
            logger.warning("❌ OTP tables not found!")
            
    except Exception as e:
        logger.error(f"Verification failed: {e}")
    finally:
        if conn:
            await conn.close()

if __name__ == "__main__":
    asyncio.run(verify_tables())