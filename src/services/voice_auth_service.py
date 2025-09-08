"""
Voice Authentication Service
Handles voice-based user authentication and age verification
"""

from typing import Dict, Optional, Tuple, Any
import numpy as np
import logging
import json
import hashlib
import base64
from datetime import datetime
import asyncpg

logger = logging.getLogger(__name__)


class VoiceAuthService:
    """Service for voice authentication and age detection"""
    
    def __init__(self, db_connection):
        """Initialize voice auth service"""
        self.db = db_connection
        # Voice feature extraction parameters
        self.sample_rate = 16000
        self.feature_dim = 256  # Voice embedding dimension
        
    async def extract_voice_features(self, audio_data: bytes) -> np.ndarray:
        """
        Extract voice features from audio data
        This would use a pre-trained model like wav2vec2 or speaker embedding model
        """
        try:
            # In production, you would use:
            # 1. librosa for audio processing
            # 2. A pre-trained model (wav2vec2, x-vector, d-vector)
            # 3. Feature extraction pipeline
            
            # Placeholder: Generate consistent features based on audio hash
            audio_hash = hashlib.sha256(audio_data).digest()
            features = np.frombuffer(audio_hash * 8, dtype=np.float32)[:self.feature_dim]
            features = features / np.linalg.norm(features)  # Normalize
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting voice features: {str(e)}")
            raise
    
    async def estimate_age_from_voice(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Estimate age from voice characteristics
        Uses acoustic features like pitch, formants, speech rate
        """
        try:
            # In production, you would analyze:
            # 1. Fundamental frequency (F0) - tends to be lower in adults
            # 2. Formant frequencies - change with vocal tract length
            # 3. Speech rate and articulation
            # 4. Voice quality measures (jitter, shimmer)
            
            # Placeholder implementation
            audio_hash = hashlib.sha256(audio_data).hexdigest()
            hash_value = int(audio_hash[:8], 16)
            
            # Simulate age estimation with confidence
            estimated_age = 18 + (hash_value % 50)  # Range: 18-67
            confidence = 0.65 + (hash_value % 35) / 100  # Range: 0.65-0.99
            
            # Age category classification
            if estimated_age < 21:
                category = "young_adult"
                is_adult = True
                is_verified = estimated_age >= 19  # Legal age for cannabis
            elif estimated_age < 35:
                category = "adult"
                is_adult = True
                is_verified = True
            elif estimated_age < 50:
                category = "middle_aged"
                is_adult = True
                is_verified = True
            else:
                category = "senior"
                is_adult = True
                is_verified = True
            
            return {
                "estimated_age": estimated_age,
                "age_range": f"{max(18, estimated_age-3)}-{estimated_age+3}",
                "confidence": round(confidence, 2),
                "category": category,
                "is_adult": is_adult,
                "is_verified": is_verified,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error estimating age from voice: {str(e)}")
            raise
    
    async def register_voice_profile(self, user_id: str, audio_data: bytes, 
                                    metadata: Optional[Dict] = None) -> bool:
        """Register a new voice profile for a user"""
        try:
            # Extract voice features
            features = await self.extract_voice_features(audio_data)
            
            # Estimate age for verification
            age_info = await self.estimate_age_from_voice(audio_data)
            
            # Convert features to base64 for storage
            features_b64 = base64.b64encode(features.tobytes()).decode('utf-8')
            
            # Store voice profile
            query = """
                INSERT INTO voice_profiles 
                (user_id, voice_embedding, age_verification, metadata, created_at, updated_at)
                VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE
                SET voice_embedding = $2,
                    age_verification = $3,
                    metadata = $4,
                    updated_at = CURRENT_TIMESTAMP
            """
            
            profile_metadata = {
                "feature_dim": self.feature_dim,
                "sample_rate": self.sample_rate,
                "age_info": age_info,
                **(metadata or {})
            }
            
            await self.db.execute(
                query,
                user_id,
                features_b64,
                json.dumps(age_info),
                json.dumps(profile_metadata)
            )
            
            # Update user age verification status if verified
            if age_info['is_verified']:
                update_query = """
                    UPDATE users 
                    SET age_verified = true 
                    WHERE id = $1
                """
                await self.db.execute(update_query, user_id)
            
            logger.info(f"Voice profile registered for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering voice profile: {str(e)}")
            return False
    
    async def authenticate_voice(self, audio_data: bytes, 
                                threshold: float = 0.85) -> Optional[Dict[str, Any]]:
        """
        Authenticate user by voice
        Returns user info if match found
        """
        try:
            # Extract features from input audio
            input_features = await self.extract_voice_features(audio_data)
            
            # Get age estimation
            age_info = await self.estimate_age_from_voice(audio_data)
            
            # Get all voice profiles
            query = """
                SELECT 
                    vp.user_id,
                    vp.voice_embedding,
                    vp.age_verification,
                    u.email,
                    u.first_name,
                    u.last_name,
                    u.age_verified
                FROM voice_profiles vp
                JOIN users u ON vp.user_id = u.id
                WHERE u.active = true
            """
            
            profiles = await self.db.fetch(query)
            
            best_match = None
            best_score = 0.0
            
            for profile in profiles:
                # Decode stored features
                stored_features = np.frombuffer(
                    base64.b64decode(profile['voice_embedding']),
                    dtype=np.float32
                )
                
                # Calculate cosine similarity
                similarity = np.dot(input_features, stored_features)
                
                if similarity > best_score:
                    best_score = similarity
                    best_match = profile
            
            # Check if match exceeds threshold
            if best_score >= threshold:
                logger.info(f"Voice authenticated for user {best_match['user_id']} with score {best_score:.3f}")
                
                # Log authentication attempt
                await self.log_auth_attempt(
                    best_match['user_id'],
                    success=True,
                    score=best_score,
                    age_info=age_info
                )
                
                return {
                    "authenticated": True,
                    "user_id": best_match['user_id'],
                    "email": best_match['email'],
                    "name": f"{best_match['first_name']} {best_match['last_name']}",
                    "confidence": round(best_score, 3),
                    "age_verified": best_match['age_verified'],
                    "age_info": age_info
                }
            else:
                logger.warning(f"Voice authentication failed. Best score: {best_score:.3f}")
                return {
                    "authenticated": False,
                    "message": "Voice not recognized",
                    "age_info": age_info
                }
            
        except Exception as e:
            logger.error(f"Error authenticating voice: {str(e)}")
            return None
    
    async def verify_age_only(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Verify age without authentication
        Useful for anonymous age verification
        """
        try:
            age_info = await self.estimate_age_from_voice(audio_data)
            
            # Log age verification attempt
            await self.log_age_verification(age_info)
            
            return {
                "verified": age_info['is_verified'],
                "age_info": age_info,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error verifying age: {str(e)}")
            raise
    
    async def log_auth_attempt(self, user_id: Optional[str], success: bool, 
                              score: float, age_info: Dict):
        """Log authentication attempt"""
        try:
            query = """
                INSERT INTO voice_auth_logs
                (user_id, success, confidence_score, age_info, timestamp)
                VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
            """
            
            await self.db.execute(
                query,
                user_id,
                success,
                score,
                json.dumps(age_info)
            )
        except Exception as e:
            logger.error(f"Error logging auth attempt: {str(e)}")
    
    async def log_age_verification(self, age_info: Dict):
        """Log age verification attempt"""
        try:
            query = """
                INSERT INTO age_verification_logs
                (age_info, verified, timestamp)
                VALUES ($1, $2, CURRENT_TIMESTAMP)
            """
            
            await self.db.execute(
                query,
                json.dumps(age_info),
                age_info['is_verified']
            )
        except Exception as e:
            logger.error(f"Error logging age verification: {str(e)}")
    
    async def get_voice_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get voice profile for a user"""
        try:
            query = """
                SELECT 
                    user_id,
                    age_verification,
                    metadata,
                    created_at,
                    updated_at
                FROM voice_profiles
                WHERE user_id = $1
            """
            
            result = await self.db.fetchrow(query, user_id)
            if result:
                profile = dict(result)
                if profile.get('age_verification'):
                    profile['age_verification'] = json.loads(profile['age_verification'])
                if profile.get('metadata'):
                    profile['metadata'] = json.loads(profile['metadata'])
                return profile
            return None
            
        except Exception as e:
            logger.error(f"Error getting voice profile: {str(e)}")
            raise