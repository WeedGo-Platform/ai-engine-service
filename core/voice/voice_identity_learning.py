"""
Voice Identity and Self-Learning System
Identifies customers by voice and builds personalized context
"""
import numpy as np
import json
import logging
from typing import Dict, Optional, List, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import pickle
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class VoiceProfile:
    """Individual voice profile"""
    user_id: str
    voice_embedding: np.ndarray  # Voice fingerprint
    created_at: datetime
    updated_at: datetime
    interaction_count: int = 0
    
    # Voice characteristics
    avg_pitch: float = 0.0
    pitch_variance: float = 0.0
    speaking_rate: float = 0.0  # Words per minute
    energy_level: float = 0.0
    formant_frequencies: List[float] = field(default_factory=list)
    
    # Behavioral patterns
    typical_greeting: Optional[str] = None
    common_phrases: List[str] = field(default_factory=list)
    vocabulary_complexity: float = 0.0
    
    # Preferences learned over time
    preferred_products: List[str] = field(default_factory=list)
    preferred_effects: List[str] = field(default_factory=list)
    price_sensitivity: float = 0.5  # 0-1 scale
    quality_preference: float = 0.5  # 0-1 scale
    
    # Context history
    last_purchase: Optional[Dict] = None
    purchase_history: List[Dict] = field(default_factory=list)
    conversation_topics: List[str] = field(default_factory=list)
    satisfaction_scores: List[float] = field(default_factory=list)

@dataclass
class LearningContext:
    """Context learned from interactions"""
    user_id: str
    session_id: str
    timestamp: datetime
    
    # Current interaction
    voice_features: Dict[str, float]
    transcription: str
    intent: str
    entities: Dict[str, Any]
    
    # Response and outcome
    ai_response: str
    user_satisfaction: Optional[float] = None  # Inferred from voice
    purchase_made: bool = False
    products_discussed: List[str] = field(default_factory=list)
    
    # Emotional state
    detected_emotion: str = "neutral"
    stress_level: float = 0.0
    engagement_level: float = 0.5

class VoiceIdentitySystem:
    """
    Identifies users by voice and maintains their profiles
    """
    
    def __init__(self, profiles_dir: str = "data/voice_profiles"):
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory profile cache
        self.profiles: Dict[str, VoiceProfile] = {}
        self.embeddings_index = {}  # Fast similarity search
        
        # Load existing profiles
        self._load_profiles()
        
        # Similarity threshold for identification
        self.identification_threshold = 0.85
        
    def _load_profiles(self):
        """Load existing voice profiles from disk"""
        profile_files = self.profiles_dir.glob("*.profile")
        
        for profile_file in profile_files:
            try:
                with open(profile_file, 'rb') as f:
                    profile = pickle.load(f)
                    self.profiles[profile.user_id] = profile
                    self._index_embedding(profile.user_id, profile.voice_embedding)
                    
                logger.info(f"Loaded voice profile: {profile.user_id}")
                
            except Exception as e:
                logger.error(f"Failed to load profile {profile_file}: {e}")
        
        logger.info(f"Loaded {len(self.profiles)} voice profiles")
    
    def _index_embedding(self, user_id: str, embedding: np.ndarray):
        """Index embedding for fast similarity search"""
        # Simple indexing - in production, use FAISS or similar
        self.embeddings_index[user_id] = embedding
    
    def extract_voice_features(self, audio: np.ndarray, sample_rate: int = 16000) -> Dict[str, float]:
        """
        Extract voice features for identification and learning
        """
        features = {}
        
        # Basic features
        features['energy'] = float(np.sqrt(np.mean(audio ** 2)))
        features['zero_crossing_rate'] = float(np.sum(np.diff(np.sign(audio)) != 0) / len(audio))
        
        # Pitch estimation (simplified)
        # In production, use librosa or praat-parselmouth
        autocorr = np.correlate(audio, audio, mode='full')
        autocorr = autocorr[len(autocorr)//2:]
        
        # Find first peak after zero lag
        min_period = int(sample_rate / 300)  # 300 Hz max
        max_period = int(sample_rate / 50)   # 50 Hz min
        
        if max_period < len(autocorr):
            autocorr_slice = autocorr[min_period:max_period]
            if len(autocorr_slice) > 0:
                pitch_period = np.argmax(autocorr_slice) + min_period
                features['pitch'] = float(sample_rate / pitch_period)
            else:
                features['pitch'] = 0.0
        else:
            features['pitch'] = 0.0
        
        # Spectral features
        fft = np.fft.rfft(audio)
        magnitude = np.abs(fft)
        
        # Spectral centroid
        freqs = np.fft.rfftfreq(len(audio), 1/sample_rate)
        features['spectral_centroid'] = float(np.sum(freqs * magnitude) / np.sum(magnitude))
        
        # Formants (simplified - just peaks in spectrum)
        peaks = self._find_spectral_peaks(magnitude, freqs)
        features['formant_1'] = peaks[0] if len(peaks) > 0 else 0.0
        features['formant_2'] = peaks[1] if len(peaks) > 1 else 0.0
        features['formant_3'] = peaks[2] if len(peaks) > 2 else 0.0
        
        return features
    
    def _find_spectral_peaks(self, magnitude: np.ndarray, freqs: np.ndarray, n_peaks: int = 3) -> List[float]:
        """Find spectral peaks (formants)"""
        from scipy.signal import find_peaks
        
        # Find peaks in magnitude spectrum
        peaks, _ = find_peaks(magnitude, height=np.max(magnitude) * 0.1)
        
        if len(peaks) > 0:
            # Sort by magnitude and take top n
            peak_mags = magnitude[peaks]
            top_peaks = peaks[np.argsort(peak_mags)[-n_peaks:]]
            return [float(freqs[p]) for p in sorted(top_peaks)]
        
        return []
    
    def create_voice_embedding(self, audio_segments: List[np.ndarray]) -> np.ndarray:
        """
        Create voice embedding from multiple audio segments
        """
        all_features = []
        
        for segment in audio_segments:
            features = self.extract_voice_features(segment)
            feature_vector = np.array(list(features.values()))
            all_features.append(feature_vector)
        
        # Average features across segments
        if all_features:
            embedding = np.mean(all_features, axis=0)
            # Normalize
            embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
            return embedding
        
        return np.zeros(6)  # Default embedding size
    
    def identify_user(self, audio: np.ndarray, confidence_threshold: float = 0.85) -> Tuple[Optional[str], float]:
        """
        Identify user by voice
        
        Returns:
            Tuple of (user_id, confidence)
        """
        # Extract features from current audio
        features = self.extract_voice_features(audio)
        current_embedding = np.array(list(features.values()))
        current_embedding = current_embedding / (np.linalg.norm(current_embedding) + 1e-8)
        
        # Compare with known profiles
        best_match = None
        best_similarity = 0.0
        
        for user_id, stored_embedding in self.embeddings_index.items():
            # Cosine similarity
            similarity = np.dot(current_embedding, stored_embedding)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = user_id
        
        # Check if similarity meets threshold
        if best_similarity >= confidence_threshold:
            logger.info(f"Identified user: {best_match} (confidence: {best_similarity:.2f})")
            return best_match, best_similarity
        
        logger.info(f"No voice match found (best similarity: {best_similarity:.2f})")
        return None, best_similarity
    
    def create_or_update_profile(
        self,
        audio: np.ndarray,
        user_id: Optional[str] = None,
        context: Optional[LearningContext] = None
    ) -> VoiceProfile:
        """
        Create new profile or update existing one
        """
        features = self.extract_voice_features(audio)
        
        # Try to identify user if no ID provided
        if not user_id:
            identified_id, confidence = self.identify_user(audio)
            if identified_id and confidence > self.identification_threshold:
                user_id = identified_id
            else:
                # Generate new user ID
                user_id = self._generate_user_id(audio)
                logger.info(f"Creating new voice profile: {user_id}")
        
        # Get or create profile
        if user_id in self.profiles:
            profile = self.profiles[user_id]
            # Update profile
            self._update_profile(profile, features, context)
        else:
            # Create new profile
            embedding = self.create_voice_embedding([audio])
            profile = VoiceProfile(
                user_id=user_id,
                voice_embedding=embedding,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                avg_pitch=features.get('pitch', 0.0),
                energy_level=features.get('energy', 0.0)
            )
            self.profiles[user_id] = profile
            self._index_embedding(user_id, embedding)
        
        # Save profile
        self._save_profile(profile)
        
        return profile
    
    def _update_profile(self, profile: VoiceProfile, features: Dict, context: Optional[LearningContext]):
        """Update existing profile with new information"""
        profile.interaction_count += 1
        profile.updated_at = datetime.now()
        
        # Update voice characteristics (moving average)
        alpha = 0.1  # Learning rate
        profile.avg_pitch = (1 - alpha) * profile.avg_pitch + alpha * features.get('pitch', 0)
        profile.energy_level = (1 - alpha) * profile.energy_level + alpha * features.get('energy', 0)
        
        if context:
            # Update preferences based on context
            if context.products_discussed:
                profile.preferred_products.extend(context.products_discussed)
                # Keep only most recent/frequent
                profile.preferred_products = self._get_most_frequent(profile.preferred_products, 10)
            
            if context.user_satisfaction is not None:
                profile.satisfaction_scores.append(context.user_satisfaction)
                # Keep last 20 scores
                profile.satisfaction_scores = profile.satisfaction_scores[-20:]
            
            # Update conversation topics
            if context.intent:
                profile.conversation_topics.append(context.intent)
                profile.conversation_topics = profile.conversation_topics[-50:]
            
            # Learn from purchase behavior
            if context.purchase_made and context.products_discussed:
                purchase_info = {
                    "timestamp": context.timestamp.isoformat(),
                    "products": context.products_discussed,
                    "session_id": context.session_id
                }
                profile.purchase_history.append(purchase_info)
                profile.last_purchase = purchase_info
    
    def _get_most_frequent(self, items: List[str], n: int) -> List[str]:
        """Get n most frequent items from list"""
        from collections import Counter
        counter = Counter(items)
        return [item for item, _ in counter.most_common(n)]
    
    def _generate_user_id(self, audio: np.ndarray) -> str:
        """Generate unique user ID from voice"""
        # Create hash from audio features
        features = self.extract_voice_features(audio)
        feature_str = json.dumps(features, sort_keys=True)
        hash_obj = hashlib.sha256(feature_str.encode())
        return f"voice_{hash_obj.hexdigest()[:12]}"
    
    def _save_profile(self, profile: VoiceProfile):
        """Save profile to disk"""
        profile_file = self.profiles_dir / f"{profile.user_id}.profile"
        
        with open(profile_file, 'wb') as f:
            pickle.dump(profile, f)
    
    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive user context for AI engine
        """
        if user_id not in self.profiles:
            return {}
        
        profile = self.profiles[user_id]
        
        # Calculate user insights
        avg_satisfaction = np.mean(profile.satisfaction_scores) if profile.satisfaction_scores else 0.5
        
        # Determine user type
        user_type = self._classify_user_type(profile)
        
        context = {
            "user_id": user_id,
            "interaction_count": profile.interaction_count,
            "user_type": user_type,
            "preferences": {
                "products": profile.preferred_products[:5] if profile.preferred_products else [],
                "effects": profile.preferred_effects[:5] if profile.preferred_effects else [],
                "price_sensitivity": profile.price_sensitivity,
                "quality_preference": profile.quality_preference
            },
            "history": {
                "last_purchase": profile.last_purchase,
                "purchase_count": len(profile.purchase_history),
                "common_topics": self._get_most_frequent(profile.conversation_topics, 5)
            },
            "satisfaction": {
                "average": avg_satisfaction,
                "trend": self._calculate_trend(profile.satisfaction_scores)
            },
            "voice_characteristics": {
                "speaking_rate": profile.speaking_rate,
                "energy_level": profile.energy_level,
                "typical_greeting": profile.typical_greeting
            }
        }
        
        return context
    
    def _classify_user_type(self, profile: VoiceProfile) -> str:
        """Classify user based on behavior patterns"""
        if profile.interaction_count < 3:
            return "new_customer"
        
        if len(profile.purchase_history) > 10:
            return "regular_customer"
        elif len(profile.purchase_history) > 3:
            return "returning_customer"
        
        # Check preferences
        if profile.quality_preference > 0.7:
            return "quality_focused"
        elif profile.price_sensitivity > 0.7:
            return "price_conscious"
        
        return "casual_browser"
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend from values"""
        if len(values) < 3:
            return "stable"
        
        recent = np.mean(values[-3:])
        older = np.mean(values[-6:-3]) if len(values) >= 6 else np.mean(values[:-3])
        
        if recent > older + 0.1:
            return "improving"
        elif recent < older - 0.1:
            return "declining"
        
        return "stable"

class SelfLearningSystem:
    """
    Self-learning system that improves from every interaction
    """
    
    def __init__(self, voice_identity: VoiceIdentitySystem):
        self.voice_identity = voice_identity
        self.learning_history = []
        self.model_adaptations = {}
        
    async def learn_from_interaction(
        self,
        audio: np.ndarray,
        transcription: str,
        ai_response: str,
        outcome: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Learn from a complete interaction
        """
        # Identify or create user profile
        user_id, confidence = self.voice_identity.identify_user(audio)
        
        if not user_id:
            # New user
            profile = self.voice_identity.create_or_update_profile(audio)
            user_id = profile.user_id
        else:
            # Update existing profile
            profile = self.voice_identity.create_or_update_profile(audio, user_id)
        
        # Create learning context
        context = LearningContext(
            user_id=user_id,
            session_id=outcome.get("session_id", ""),
            timestamp=datetime.now(),
            voice_features=self.voice_identity.extract_voice_features(audio),
            transcription=transcription,
            intent=outcome.get("intent", ""),
            entities=outcome.get("entities", {}),
            ai_response=ai_response,
            user_satisfaction=self._infer_satisfaction(audio, transcription),
            purchase_made=outcome.get("purchase_made", False),
            products_discussed=outcome.get("products", []),
            detected_emotion=self._detect_emotion(audio),
            engagement_level=self._calculate_engagement(audio, transcription)
        )
        
        # Update profile with context
        self.voice_identity._update_profile(profile, context.voice_features, context)
        
        # Learn patterns
        learnings = self._extract_learnings(context, profile)
        
        # Store learning history
        self.learning_history.append({
            "timestamp": context.timestamp,
            "user_id": user_id,
            "learnings": learnings
        })
        
        # Adapt models if needed
        self._adapt_models(learnings)
        
        return {
            "user_identified": user_id is not None,
            "user_id": user_id,
            "confidence": confidence,
            "learnings": learnings,
            "profile_updated": True
        }
    
    def _infer_satisfaction(self, audio: np.ndarray, transcription: str) -> float:
        """Infer user satisfaction from voice and text"""
        # Analyze voice energy and pitch variation
        features = self.voice_identity.extract_voice_features(audio)
        
        # Higher energy and pitch variation often indicate engagement
        energy_score = min(features.get('energy', 0) * 2, 1.0)
        
        # Analyze text sentiment (simplified)
        positive_words = ['great', 'perfect', 'excellent', 'love', 'amazing', 'thanks']
        negative_words = ['bad', 'wrong', 'hate', 'terrible', 'awful', 'disappointed']
        
        text_lower = transcription.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        text_score = 0.5 + (positive_count - negative_count) * 0.1
        text_score = max(0, min(1, text_score))
        
        # Combine scores
        satisfaction = 0.6 * text_score + 0.4 * energy_score
        
        return satisfaction
    
    def _detect_emotion(self, audio: np.ndarray) -> str:
        """Detect emotion from voice"""
        features = self.voice_identity.extract_voice_features(audio)
        
        pitch = features.get('pitch', 150)
        energy = features.get('energy', 0.5)
        
        # Simple emotion detection based on pitch and energy
        if energy > 0.7 and pitch > 200:
            return "excited"
        elif energy < 0.3 and pitch < 100:
            return "sad"
        elif energy > 0.6 and pitch < 150:
            return "angry"
        elif energy < 0.4:
            return "calm"
        
        return "neutral"
    
    def _calculate_engagement(self, audio: np.ndarray, transcription: str) -> float:
        """Calculate user engagement level"""
        # Longer utterances suggest higher engagement
        word_count = len(transcription.split())
        length_score = min(word_count / 20, 1.0)
        
        # Voice energy indicates engagement
        features = self.voice_identity.extract_voice_features(audio)
        energy_score = min(features.get('energy', 0) * 2, 1.0)
        
        engagement = 0.5 * length_score + 0.5 * energy_score
        
        return engagement
    
    def _extract_learnings(self, context: LearningContext, profile: VoiceProfile) -> Dict:
        """Extract learnings from interaction"""
        learnings = {
            "user_patterns": [],
            "preferences_updates": [],
            "behavior_insights": []
        }
        
        # Learn speech patterns
        if context.transcription:
            words = context.transcription.lower().split()
            if len(words) > 0:
                # Update typical greeting if at start of conversation
                if profile.interaction_count == 1 or not profile.typical_greeting:
                    profile.typical_greeting = ' '.join(words[:5])
                
                # Learn common phrases
                for i in range(len(words) - 2):
                    phrase = ' '.join(words[i:i+3])
                    profile.common_phrases.append(phrase)
        
        # Learn preferences from products discussed
        if context.products_discussed:
            learnings["preferences_updates"].append({
                "type": "product_interest",
                "products": context.products_discussed
            })
        
        # Learn from emotional state
        if context.detected_emotion != "neutral":
            learnings["behavior_insights"].append({
                "emotion": context.detected_emotion,
                "context": context.intent,
                "engagement": context.engagement_level
            })
        
        # Learn from satisfaction
        if context.user_satisfaction > 0.7:
            learnings["user_patterns"].append({
                "pattern": "satisfied_interaction",
                "factors": {
                    "response": ai_response[:100],
                    "intent": context.intent
                }
            })
        elif context.user_satisfaction < 0.3:
            learnings["user_patterns"].append({
                "pattern": "unsatisfied_interaction",
                "factors": {
                    "response": ai_response[:100],
                    "intent": context.intent
                }
            })
        
        return learnings
    
    def _adapt_models(self, learnings: Dict):
        """Adapt models based on learnings"""
        # Track successful patterns
        for pattern in learnings.get("user_patterns", []):
            if pattern["pattern"] == "satisfied_interaction":
                # Store successful response patterns
                key = pattern["factors"]["intent"]
                if key not in self.model_adaptations:
                    self.model_adaptations[key] = {
                        "successful_responses": [],
                        "failed_responses": []
                    }
                self.model_adaptations[key]["successful_responses"].append(
                    pattern["factors"]["response"]
                )
        
        # Adapt to user preferences
        for update in learnings.get("preferences_updates", []):
            if update["type"] == "product_interest":
                # This information would be used to bias future recommendations
                pass
    
    def get_personalized_prompt_context(self, user_id: str) -> str:
        """
        Generate personalized prompt context for AI engine
        """
        context = self.voice_identity.get_user_context(user_id)
        
        if not context:
            return ""
        
        prompt = f"""
User Profile:
- Customer Type: {context.get('user_type', 'new')}
- Interactions: {context.get('interaction_count', 0)}
- Satisfaction Level: {context.get('satisfaction', {}).get('average', 0.5):.1%}
- Satisfaction Trend: {context.get('satisfaction', {}).get('trend', 'stable')}

Preferences:
- Preferred Products: {', '.join(context.get('preferences', {}).get('products', []))}
- Preferred Effects: {', '.join(context.get('preferences', {}).get('effects', []))}
- Price Sensitivity: {'High' if context.get('preferences', {}).get('price_sensitivity', 0.5) > 0.7 else 'Moderate'}
- Quality Focus: {'High' if context.get('preferences', {}).get('quality_preference', 0.5) > 0.7 else 'Moderate'}

Recent History:
- Last Purchase: {context.get('history', {}).get('last_purchase', {}).get('products', 'None')}
- Common Topics: {', '.join(context.get('history', {}).get('common_topics', []))}

Voice Characteristics:
- Energy Level: {context.get('voice_characteristics', {}).get('energy_level', 0.5):.1%}
- Typical Greeting: {context.get('voice_characteristics', {}).get('typical_greeting', 'Unknown')}

Adjust your response to match this user's preferences and communication style.
"""
        
        return prompt