#!/usr/bin/env python3
"""
Debug Voice Authentication Issues
"""

import asyncio
import asyncpg
import base64
import os
import sys
import traceback
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from services.voice_auth_service import VoiceAuthService

async def debug_voice_auth():
    """Debug voice authentication step by step"""
    try:
        print("🔍 Step 1: Testing database connection...")
        
        # Test direct database connection
        conn = await asyncpg.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME', 'ai_engine'),
            user=os.getenv('DB_USER', 'weedgo'),
            password=os.getenv('DB_PASSWORD', 'your_password_here')
        )
        
        print("✅ Direct database connection successful")
        
        # Test creating service
        print("🔍 Step 2: Creating VoiceAuthService...")
        service = VoiceAuthService(conn)
        print("✅ VoiceAuthService created")
        
        # Test audio data
        print("🔍 Step 3: Preparing test audio...")
        audio_base64 = "dGVzdCBhdWRpbyBkYXRh"  # "test audio data"
        audio_data = base64.b64decode(audio_base64)
        print(f"✅ Audio data prepared: {len(audio_data)} bytes")
        
        # Test authenticate_voice method with detailed error handling
        print("🔍 Step 4: Testing authenticate_voice...")
        try:
            result = await service.authenticate_voice(audio_data)
            print(f"✅ authenticate_voice returned: {result}")
            print(f"Result type: {type(result)}")
            if result:
                print(f"Result keys: {result.keys()}")
            else:
                print("❌ Result is falsy (None, False, empty dict, etc.)")
                
        except Exception as e:
            print(f"❌ authenticate_voice raised exception: {e}")
            traceback.print_exc()
        
        # Test with pool connection (like the endpoint)
        print("\n🔍 Step 5: Testing with connection pool...")
        pool = await asyncpg.create_pool(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME', 'ai_engine'),
            user=os.getenv('DB_USER', 'weedgo'),
            password=os.getenv('DB_PASSWORD', 'your_password_here'),
            min_size=1,
            max_size=10
        )
        
        pool_conn = await pool.acquire()
        pool_service = VoiceAuthService(pool_conn)
        
        try:
            pool_result = await pool_service.authenticate_voice(audio_data)
            print(f"✅ Pool authenticate_voice returned: {pool_result}")
        except Exception as e:
            print(f"❌ Pool authenticate_voice raised exception: {e}")
            traceback.print_exc()
        finally:
            await pool.release(pool_conn)
            await pool.close()
        
        await conn.close()
        print("\n✅ All debugging steps completed")
        
    except Exception as e:
        print(f"❌ Debug error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_voice_auth())