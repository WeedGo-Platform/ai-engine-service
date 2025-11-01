#!/usr/bin/env python3
"""
Debug Feature Extraction in Detail
"""

import asyncio
import asyncpg
import os
import sys
import hashlib
from pathlib import Path
import numpy as np

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from services.voice_auth_service import VoiceAuthService

async def debug_feature_extraction():
    """Debug the feature extraction step by step"""
    try:
        # Connect to database
        conn = await asyncpg.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME', 'ai_engine'),
            user=os.getenv('DB_USER', 'weedgo'),
            password=os.getenv('DB_PASSWORD', 'weedgo123')
        )
        
        service = VoiceAuthService(conn)
        
        # Read test audio
        with open('test_voice_auth.py', 'rb') as f:
            audio_data = f.read()
        
        print(f"🔍 Audio data length: {len(audio_data)} bytes")
        print(f"   First 50 bytes: {audio_data[:50]}")
        
        # Step 1: Generate hash
        audio_hash = hashlib.sha256(audio_data).digest()
        print(f"✅ SHA256 hash length: {len(audio_hash)} bytes")
        print(f"   Hash: {audio_hash.hex()[:50]}...")
        
        # Step 2: Repeat hash to get enough data
        repeated_hash = audio_hash * 8  # 32 * 8 = 256 bytes
        print(f"✅ Repeated hash length: {len(repeated_hash)} bytes")
        
        # Step 3: Convert to float32 array
        features_raw = np.frombuffer(repeated_hash, dtype=np.float32)
        print(f"✅ Raw features shape: {features_raw.shape}")
        print(f"   Raw features sample: {features_raw[:10]}")
        print(f"   Raw features stats: min={features_raw.min():.6f}, max={features_raw.max():.6f}")
        
        # Step 4: Take first 256 elements (service.feature_dim)
        features_trimmed = features_raw[:service.feature_dim]
        print(f"✅ Trimmed features shape: {features_trimmed.shape}")
        print(f"   Trimmed features sample: {features_trimmed[:10]}")
        
        # Step 5: Calculate norm
        norm = np.linalg.norm(features_trimmed)
        print(f"✅ L2 norm: {norm:.6f}")
        
        # Step 6: Normalize
        if norm > 0:
            features_normalized = features_trimmed / norm
            print(f"✅ Normalized features sample: {features_normalized[:10]}")
            print(f"   Normalized norm: {np.linalg.norm(features_normalized):.6f}")
        else:
            print("⚠️  Norm is zero, using random initialization")
            features_normalized = np.random.normal(0, 0.1, service.feature_dim).astype(np.float32)
            features_normalized = features_normalized / np.linalg.norm(features_normalized)
            print(f"   Random features sample: {features_normalized[:10]}")
        
        # Test with different audio
        print("\n🔍 Testing with different audio content...")
        different_audio = b"different audio content for testing comparison"
        
        hash2 = hashlib.sha256(different_audio).digest()
        repeated_hash2 = hash2 * 8
        features_raw2 = np.frombuffer(repeated_hash2, dtype=np.float32)
        features_trimmed2 = features_raw2[:service.feature_dim]
        norm2 = np.linalg.norm(features_trimmed2)
        
        if norm2 > 0:
            features_normalized2 = features_trimmed2 / norm2
        else:
            features_normalized2 = np.random.normal(0, 0.1, service.feature_dim).astype(np.float32)
            features_normalized2 = features_normalized2 / np.linalg.norm(features_normalized2)
        
        print(f"✅ Different audio features sample: {features_normalized2[:10]}")
        
        # Test similarity
        if 'features_normalized' in locals():
            similarity = np.dot(features_normalized, features_normalized2)
            print(f"🎯 Cross-similarity: {similarity:.6f}")
            
            self_similarity = np.dot(features_normalized, features_normalized)
            print(f"🎯 Self-similarity: {self_similarity:.6f}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_feature_extraction())