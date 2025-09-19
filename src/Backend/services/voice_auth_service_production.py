"""
Production Voice Authentication Service
Uses real biometric models for speaker verification and age detection
"""

from typing import Dict, Optional, Tuple, Any, List
import numpy as np
import logging
import json
import base64
import yaml
from datetime import datetime, timedelta
import asyncpg
from pathlib import Path
import asyncio
from collections import defaultdict

# Import production components
from core.voice_biometric.feature_extractor import VoiceFeatureExtractor, AudioFeatures
from core.security.encryption import encrypt_embedding, decrypt_embedding

logger = logging.getLogger(__name__)


class ProductionVoiceAuthService:
    """Production-ready voice authentication service with real biometric models"""

    def __init__(self, db_connection, config_path: str = "config/voice_auth_config.yaml"):
        """Initialize production voice auth service"""
        self.db = db_connection
        self.config = self._load_config(config_path)

        # Initialize feature extractor
        self.feature_extractor = VoiceFeatureExtractor(self.config)

        # Authentication parameters from config
        self.verification_threshold = self.config['authentication']['thresholds']['verification']
        self.age_minimum = self.config['authentication']['thresholds']['age_minimum']
        self.liveness_threshold = self.config['authentication']['thresholds']['liveness']
        self.quality_threshold = self.config['authentication']['thresholds']['quality']

        # Security settings
        self.max_attempts = self.config['authentication']['security']['max_attempts']
        self.lockout_duration = self.config['authentication']['security']['lockout_duration']
        self.require_liveness = self.config['authentication']['security']['require_liveness']
        self.require_age_verification = self.config['authentication']['security']['require_age_verification']

        # Cache for recent authentications (user_id -> timestamp)
        self.auth_cache = defaultdict(list)
        self.failed_attempts = defaultdict(int)
        self.lockout_until = {}

        # Performance metrics
        self.metrics = {
            'total_authentications': 0,
            'successful_authentications': 0,
            'failed_authentications': 0,
            'avg_processing_time': 0,
            'false_accepts': 0,
            'false_rejects': 0
        }

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        config_file = Path(config_path)
        if not config_file.exists():
            # Use default configuration
            return {
                'models': {
                    'speaker_verification': {
                        'primary': {'name': 'ecapa-tdnn', 'path': 'models/voice/biometric/speaker_verification/ecapa_tdnn.pt'},
                        'secondary': {'name': 'resnet34-se', 'path': 'models/voice/biometric/speaker_verification/resnet34.pt'},
                        'fusion': {'strategy': 'weighted_concat', 'primary_weight': 0.6, 'secondary_weight': 0.4}
                    },
                    'age_detection': {'name': 'wav2vec2-age', 'path': 'models/voice/biometric/age_detection/wav2vec2.pt'},
                    'antispoofing': {'name': 'aasist', 'path': 'models/voice/biometric/antispoofing/aasist.pt'}
                },
                'authentication': {
                    'thresholds': {'verification': 0.85, 'age_minimum': 21, 'liveness': 0.75, 'quality': 0.7},
                    'security': {'max_attempts': 3, 'lockout_duration': 300, 'require_liveness': True, 'require_age_verification': True}
                },
                'audio': {
                    'sample_rate': 16000,
                    'duration': {'min_seconds': 2, 'max_seconds': 10, 'optimal_seconds': 5}
                }
            }

        with open(config_file, 'r') as f:
            return yaml.safe_load(f)

    async def extract_voice_features(self, audio_data: bytes) -> AudioFeatures:
        """Extract voice features using production models"""
        try:
            # Use production feature extractor - it accepts bytes directly
            features = await asyncio.to_thread(
                self.feature_extractor.extract_embeddings,
                audio_data
            )

            # Check audio quality
            if features.quality_score < self.quality_threshold:
                raise ValueError(f"Audio quality too low: {features.quality_score:.2f}")

            # Check liveness if required
            if self.require_liveness and features.liveness_score < self.liveness_threshold:
                raise ValueError(f"Liveness check failed: {features.liveness_score:.2f}")

            return features

        except Exception as e:
            logger.error(f"Error extracting voice features: {str(e)}")
            raise

    async def estimate_age_from_voice(self, features: AudioFeatures) -> Dict[str, Any]:
        """Estimate age using real acoustic analysis and deep learning"""
        try:
            # Get age estimation from features
            estimated_age = features.age_estimation
            confidence = features.age_confidence

            # Determine age category and verification status
            if estimated_age < self.age_minimum:
                category = "minor"
                is_adult = False
                is_verified = False
            elif estimated_age < 25:
                category = "young_adult"
                is_adult = True
                is_verified = True
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

            # Create confidence-adjusted age range
            age_uncertainty = max(2, int((1 - confidence) * 10))

            return {
                "estimated_age": int(estimated_age),
                "age_range": f"{max(0, int(estimated_age - age_uncertainty))}-{int(estimated_age + age_uncertainty)}",
                "confidence": round(confidence, 3),
                "category": category,
                "is_adult": is_adult,
                "is_verified": is_verified,
                "acoustic_features": {
                    "pitch_mean": round(features.acoustic_features.get('f0_mean', 0), 2),
                    "pitch_std": round(features.acoustic_features.get('f0_std', 0), 2),
                    "speech_rate": round(features.acoustic_features.get('speech_rate', 0), 2),
                    "energy": round(features.acoustic_features.get('energy', 0), 3)
                },
                "analysis_timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error estimating age from voice: {str(e)}")
            raise

    async def register_voice_profile(self, user_id: str, audio_data: bytes,
                                    metadata: Optional[Dict] = None) -> bool:
        """Register a new voice profile using production models"""
        try:
            # Check if user is locked out
            if user_id in self.lockout_until:
                if datetime.now() < self.lockout_until[user_id]:
                    raise ValueError(f"User locked out until {self.lockout_until[user_id]}")
                else:
                    del self.lockout_until[user_id]
                    self.failed_attempts[user_id] = 0

            # Extract voice features
            features = await self.extract_voice_features(audio_data)

            # Estimate age for verification
            age_info = await self.estimate_age_from_voice(features)

            # Check age requirement
            if self.require_age_verification and not age_info['is_verified']:
                raise ValueError(f"Age verification failed. Minimum age: {self.age_minimum}")

            # Encrypt embedding for storage
            encrypted_embedding = encrypt_embedding(features.embedding)

            # Prepare metadata
            profile_metadata = {
                "model_version": self.feature_extractor.model_version,
                "embedding_size": len(features.embedding),
                "quality_score": round(features.quality_score, 3),
                "liveness_score": round(features.liveness_score, 3),
                "antispoofing_score": round(features.antispoofing_score, 3),
                "age_info": age_info,
                "acoustic_features": features.acoustic_features,
                **(metadata or {})
            }

            # Store voice profile
            query = """
                INSERT INTO voice_profiles
                (user_id, voice_embedding, age_verification, metadata,
                 quality_score, liveness_score, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE
                SET voice_embedding = $2,
                    age_verification = $3,
                    metadata = $4,
                    quality_score = $5,
                    liveness_score = $6,
                    updated_at = CURRENT_TIMESTAMP
            """

            await self.db.execute(
                query,
                user_id,
                encrypted_embedding,
                json.dumps(age_info),
                json.dumps(profile_metadata),
                features.quality_score,
                features.liveness_score
            )

            # Update user age verification status
            if age_info['is_verified']:
                update_query = """
                    UPDATE users
                    SET age_verified = true,
                        voice_enrolled = true,
                        voice_enrollment_date = CURRENT_TIMESTAMP
                    WHERE id = $1
                """
                await self.db.execute(update_query, user_id)

            # Log successful enrollment
            await self._log_enrollment(user_id, success=True, features=features, age_info=age_info)

            logger.info(f"Voice profile registered for user {user_id} with quality {features.quality_score:.3f}")
            return True

        except Exception as e:
            logger.error(f"Error registering voice profile: {str(e)}")
            await self._log_enrollment(user_id, success=False, error=str(e))
            return False

    async def authenticate_voice(self, audio_data: bytes,
                                threshold: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Authenticate user by voice using production models"""
        try:
            start_time = datetime.now()
            threshold = threshold or self.verification_threshold

            # Extract features from input audio
            input_features = await self.extract_voice_features(audio_data)

            # Get age estimation
            age_info = await self.estimate_age_from_voice(input_features)

            # Check age requirement
            if self.require_age_verification and not age_info['is_verified']:
                return {
                    "authenticated": False,
                    "message": f"Age verification failed. Minimum age: {self.age_minimum}",
                    "age_info": age_info
                }

            # Get all voice profiles with FAISS optimization (future)
            query = """
                SELECT
                    vp.user_id,
                    vp.voice_embedding,
                    vp.age_verification,
                    vp.quality_score,
                    vp.liveness_score,
                    u.email,
                    u.first_name,
                    u.last_name,
                    u.age_verified,
                    u.voice_enrolled
                FROM voice_profiles vp
                JOIN users u ON vp.user_id = u.id
                WHERE u.active = true
                    AND u.voice_enrolled = true
                    AND vp.quality_score >= $1
            """

            profiles = await self.db.fetch(query, self.quality_threshold)

            if not profiles:
                logger.warning("No valid voice profiles found in database")
                return {
                    "authenticated": False,
                    "message": "No enrolled voice profiles",
                    "age_info": age_info
                }

            best_match = None
            best_score = 0.0
            scores = []

            # Compare with all profiles
            for profile in profiles:
                # Check if user is locked out
                user_id = profile['user_id']
                if user_id in self.lockout_until:
                    if datetime.now() < self.lockout_until[user_id]:
                        continue
                    else:
                        del self.lockout_until[user_id]
                        self.failed_attempts[user_id] = 0

                # Decrypt stored embedding
                stored_embedding = decrypt_embedding(profile['voice_embedding'])

                # Calculate similarity using production model
                similarity = self._calculate_similarity(
                    input_features.embedding,
                    stored_embedding
                )

                scores.append({
                    'user_id': user_id,
                    'score': similarity,
                    'profile': profile
                })

                if similarity > best_score:
                    best_score = similarity
                    best_match = profile

            # Apply adaptive threshold based on score distribution
            adaptive_threshold = self._calculate_adaptive_threshold(scores, threshold)

            # Check if match exceeds threshold
            if best_score >= adaptive_threshold:
                user_id = best_match['user_id']

                # Reset failed attempts
                self.failed_attempts[user_id] = 0

                # Update metrics
                processing_time = (datetime.now() - start_time).total_seconds()
                self._update_metrics(success=True, processing_time=processing_time)

                # Log successful authentication
                await self._log_auth_attempt(
                    user_id,
                    success=True,
                    score=best_score,
                    threshold=adaptive_threshold,
                    age_info=age_info,
                    features=input_features
                )

                logger.info(f"Voice authenticated for user {user_id} with score {best_score:.3f}")

                return {
                    "authenticated": True,
                    "user_id": user_id,
                    "email": best_match['email'],
                    "name": f"{best_match['first_name']} {best_match['last_name']}",
                    "confidence": round(best_score, 3),
                    "age_verified": best_match['age_verified'],
                    "age_info": age_info,
                    "quality_metrics": {
                        "audio_quality": round(input_features.quality_score, 3),
                        "liveness": round(input_features.liveness_score, 3),
                        "antispoofing": round(input_features.antispoofing_score, 3)
                    },
                    "processing_time_ms": int(processing_time * 1000)
                }
            else:
                # Handle failed authentication
                if best_match:
                    user_id = best_match['user_id']
                    self.failed_attempts[user_id] += 1

                    # Check for lockout
                    if self.failed_attempts[user_id] >= self.max_attempts:
                        self.lockout_until[user_id] = datetime.now() + timedelta(seconds=self.lockout_duration)
                        logger.warning(f"User {user_id} locked out after {self.max_attempts} failed attempts")

                # Update metrics
                processing_time = (datetime.now() - start_time).total_seconds()
                self._update_metrics(success=False, processing_time=processing_time)

                # Log failed authentication
                await self._log_auth_attempt(
                    best_match['user_id'] if best_match else None,
                    success=False,
                    score=best_score,
                    threshold=adaptive_threshold,
                    age_info=age_info,
                    features=input_features
                )

                logger.warning(f"Voice authentication failed. Best score: {best_score:.3f}, Threshold: {adaptive_threshold:.3f}")

                return {
                    "authenticated": False,
                    "message": "Voice not recognized",
                    "age_info": age_info,
                    "attempts_remaining": max(0, self.max_attempts - self.failed_attempts.get(best_match['user_id'], 0)) if best_match else self.max_attempts
                }

        except Exception as e:
            logger.error(f"Error authenticating voice: {str(e)}")
            import traceback
            logger.error(f"Voice auth traceback: {traceback.format_exc()}")
            return None

    def _calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between embeddings"""
        # Normalize embeddings
        embedding1 = embedding1 / np.linalg.norm(embedding1)
        embedding2 = embedding2 / np.linalg.norm(embedding2)

        # Calculate cosine similarity
        similarity = np.dot(embedding1, embedding2)

        # Clamp to [0, 1] range
        return float(np.clip(similarity, 0, 1))

    def _calculate_adaptive_threshold(self, scores: List[Dict], base_threshold: float) -> float:
        """Calculate adaptive threshold based on score distribution"""
        if len(scores) < 2:
            return base_threshold

        # Get score values
        score_values = [s['score'] for s in scores]

        # Calculate statistics
        mean_score = np.mean(score_values)
        std_score = np.std(score_values)
        max_score = max(score_values)

        # Adaptive threshold: base threshold adjusted by score distribution
        if max_score > base_threshold and std_score > 0.1:
            # Clear separation between best match and others
            second_best = sorted(score_values, reverse=True)[1] if len(score_values) > 1 else 0
            gap = max_score - second_best

            if gap > 0.15:  # Large gap indicates clear match
                return base_threshold * 0.95  # Slightly lower threshold
            elif gap < 0.05:  # Small gap indicates ambiguous match
                return base_threshold * 1.05  # Slightly higher threshold

        return base_threshold

    def _update_metrics(self, success: bool, processing_time: float):
        """Update performance metrics"""
        self.metrics['total_authentications'] += 1

        if success:
            self.metrics['successful_authentications'] += 1
        else:
            self.metrics['failed_authentications'] += 1

        # Update rolling average processing time
        n = self.metrics['total_authentications']
        current_avg = self.metrics['avg_processing_time']
        self.metrics['avg_processing_time'] = ((n - 1) * current_avg + processing_time) / n

    async def _log_auth_attempt(self, user_id: Optional[str], success: bool,
                               score: float, threshold: float, age_info: Dict,
                               features: AudioFeatures):
        """Log authentication attempt with detailed metrics"""
        try:
            query = """
                INSERT INTO voice_auth_logs
                (user_id, success, confidence_score, threshold_used, age_info,
                 quality_score, liveness_score, antispoofing_score, metadata, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, CURRENT_TIMESTAMP)
            """

            metadata = {
                "model_version": self.feature_extractor.model_version,
                "acoustic_features": features.acoustic_features,
                "processing_metadata": features.metadata
            }

            await self.db.execute(
                query,
                user_id,
                success,
                float(score),
                float(threshold),
                json.dumps(age_info),
                float(features.quality_score),
                float(features.liveness_score),
                float(features.antispoofing_score),
                json.dumps(metadata)
            )
        except Exception as e:
            logger.error(f"Error logging auth attempt: {str(e)}")

    async def _log_enrollment(self, user_id: str, success: bool,
                            features: Optional[AudioFeatures] = None,
                            age_info: Optional[Dict] = None,
                            error: Optional[str] = None):
        """Log enrollment attempt"""
        try:
            query = """
                INSERT INTO voice_enrollment_logs
                (user_id, success, age_info, quality_score, error_message, timestamp)
                VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
            """

            await self.db.execute(
                query,
                user_id,
                success,
                json.dumps(age_info) if age_info else None,
                float(features.quality_score) if features else None,
                error
            )
        except Exception as e:
            logger.error(f"Error logging enrollment: {str(e)}")

    async def verify_age_only(self, audio_data: bytes) -> Dict[str, Any]:
        """Verify age without authentication using production models"""
        try:
            # Extract features
            features = await self.extract_voice_features(audio_data)

            # Get age estimation
            age_info = await self.estimate_age_from_voice(features)

            # Log age verification
            await self._log_age_verification(age_info, features)

            return {
                "verified": age_info['is_verified'],
                "age_info": age_info,
                "confidence": age_info['confidence'],
                "quality_metrics": {
                    "audio_quality": round(features.quality_score, 3),
                    "liveness": round(features.liveness_score, 3)
                },
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error verifying age: {str(e)}")
            raise

    async def _log_age_verification(self, age_info: Dict, features: AudioFeatures):
        """Log age verification attempt"""
        try:
            query = """
                INSERT INTO age_verification_logs
                (age_info, verified, confidence, quality_score, timestamp)
                VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
            """

            await self.db.execute(
                query,
                json.dumps(age_info),
                age_info['is_verified'],
                float(age_info['confidence']),
                float(features.quality_score)
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
                    quality_score,
                    liveness_score,
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

                # Add enrollment status
                profile['enrollment_status'] = {
                    'enrolled': True,
                    'quality': profile.get('quality_score', 0),
                    'last_updated': profile.get('updated_at'),
                    'age_verified': profile.get('age_verification', {}).get('is_verified', False)
                }

                return profile
            return None

        except Exception as e:
            logger.error(f"Error getting voice profile: {str(e)}")
            raise

    async def delete_voice_profile(self, user_id: str) -> bool:
        """Delete voice profile (GDPR compliance)"""
        try:
            query = """
                DELETE FROM voice_profiles
                WHERE user_id = $1
            """

            result = await self.db.execute(query, user_id)

            # Update user record
            update_query = """
                UPDATE users
                SET voice_enrolled = false,
                    voice_enrollment_date = NULL
                WHERE id = $1
            """
            await self.db.execute(update_query, user_id)

            logger.info(f"Voice profile deleted for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting voice profile: {str(e)}")
            return False

    async def get_metrics(self) -> Dict[str, Any]:
        """Get authentication metrics"""
        return {
            **self.metrics,
            'active_lockouts': len(self.lockout_until),
            'cache_size': len(self.auth_cache),
            'model_version': self.feature_extractor.model_version
        }

    async def update_thresholds(self, verification: Optional[float] = None,
                               age_minimum: Optional[int] = None,
                               liveness: Optional[float] = None,
                               quality: Optional[float] = None) -> Dict[str, Any]:
        """Update authentication thresholds dynamically"""
        if verification is not None:
            self.verification_threshold = max(0.5, min(1.0, verification))
        if age_minimum is not None:
            self.age_minimum = max(18, min(100, age_minimum))
        if liveness is not None:
            self.liveness_threshold = max(0.5, min(1.0, liveness))
        if quality is not None:
            self.quality_threshold = max(0.5, min(1.0, quality))

        return {
            'verification_threshold': self.verification_threshold,
            'age_minimum': self.age_minimum,
            'liveness_threshold': self.liveness_threshold,
            'quality_threshold': self.quality_threshold
        }