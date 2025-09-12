#!/usr/bin/env python3
"""
Debug Voice Matching Logic
"""

import asyncio
import asyncpg
import base64
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from services.voice_auth_service import VoiceAuthService

async def debug_matching():
    """Debug the voice matching logic"""
    try:
        # Connect to database
        conn = await asyncpg.connect(
            host='localhost',
            port=5434,
            database='ai_engine',
            user='weedgo',
            password='your_password_here'
        )
        
        service = VoiceAuthService(conn)
        
        # Read the exact same audio file used for registration
        with open('test_voice_auth.py', 'rb') as f:
            audio_data = f.read()
        
        print(f"🔍 Testing with {len(audio_data)} bytes of audio")
        
        # Extract features for this audio
        features = await service.extract_voice_features(audio_data)
        print(f"✅ Extracted features: shape {features.shape}")
        print(f"   Feature sample: {features[:5]}")
        
        # Get stored profile features
        query = "SELECT user_id, voice_embedding FROM voice_profiles"
        profiles = await conn.fetch(query)
        
        if profiles:
            profile = profiles[0]
            stored_features = np.frombuffer(
                base64.b64decode(profile['voice_embedding']),
                dtype=np.float32
            )
            print(f"✅ Stored features: shape {stored_features.shape}")
            print(f"   Stored sample: {stored_features[:5]}")
            
            # Calculate similarity manually
            similarity = np.dot(features, stored_features)
            print(f"🎯 Similarity score: {similarity:.6f}")
            print(f"   Threshold: 0.85")
            print(f"   Match: {'YES' if similarity >= 0.85 else 'NO'}")
            
            # Test different thresholds
            for threshold in [0.1, 0.5, 0.7, 0.8, 0.9, 0.95, 0.99]:
                match = similarity >= threshold
                print(f"   Threshold {threshold}: {'MATCH' if match else 'no match'}")
        else:
            print("❌ No voice profiles found")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import numpy as np
    asyncio.run(debug_matching())