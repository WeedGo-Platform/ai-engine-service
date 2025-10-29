#!/usr/bin/env python3
"""
Clear OTP rate limits for development/testing
"""
import os
import asyncio
import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def clear_rate_limits(identifier=None):
    """Clear rate limits, optionally for a specific identifier"""
    try:
        conn = await asyncpg.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5434)),
            database=os.getenv('DB_NAME', 'ai_engine'),
            user=os.getenv('DB_USER', 'weedgo'),
            password=os.getenv('DB_PASSWORD', 'your_password_here')
        )
        
        if identifier:
            # Clear rate limit for specific identifier
            await conn.execute("""
                DELETE FROM otp_rate_limits 
                WHERE identifier = $1
            """, identifier)
            print(f"✅ Cleared rate limits for: {identifier}")
        else:
            # Clear all rate limits
            count = await conn.fetchval("SELECT COUNT(*) FROM otp_rate_limits")
            
            await conn.execute("DELETE FROM otp_rate_limits")
            print(f"✅ Cleared {count} rate limit records")
        
        # Show current rate limits
        remaining = await conn.fetch("""
            SELECT 
                identifier,
                identifier_type,
                request_count,
                blocked_until,
                EXTRACT(EPOCH FROM (blocked_until - NOW())) / 60 as minutes_remaining
            FROM otp_rate_limits
            ORDER BY last_request_at DESC
        """)
        
        if remaining:
            print(f"\n📊 Remaining rate limits: {len(remaining)}")
            for row in remaining:
                if row['blocked_until']:
                    print(f"  - {row['identifier']} ({row['identifier_type']}): "
                          f"{row['request_count']} requests, blocked for {int(row['minutes_remaining'])} min")
                else:
                    print(f"  - {row['identifier']} ({row['identifier_type']}): "
                          f"{row['request_count']} requests, not blocked")
        else:
            print("\n✨ No rate limits remaining - all clear!")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise

async def main():
    import sys
    
    if len(sys.argv) > 1:
        # Clear specific identifier
        identifier = sys.argv[1]
        await clear_rate_limits(identifier)
    else:
        # Clear all
        print("🧹 Clearing ALL rate limits...")
        await clear_rate_limits()

if __name__ == "__main__":
    asyncio.run(main())
