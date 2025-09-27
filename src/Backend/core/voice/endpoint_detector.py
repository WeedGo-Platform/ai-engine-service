"""
Smart Endpoint Detection
Combines silence detection, punctuation, and semantic completion
"""
import numpy as np
import time
import logging
import re
from typing import Optional, Tuple, List
from dataclasses import dataclass
import asyncio

from .streaming_manager import IEndpointDetector

logger = logging.getLogger(__name__)

@dataclass
class EndpointConfig:
    """Configuration for endpoint detection"""
    silence_threshold_ms: int = 1500  # Silence duration to trigger endpoint
    min_utterance_duration_ms: int = 500  # Minimum speech duration
    energy_threshold: float = 0.01  # Energy level for silence detection
    semantic_completion_enabled: bool = True  # Use ML for semantic completion
    punctuation_triggers: List[str] = None  # Punctuation that triggers endpoint
    
    def __post_init__(self):
        if self.punctuation_triggers is None:
            self.punctuation_triggers = ['.', '?', '!', '。', '？', '！']  # Include CJK punctuation

class SmartEndpointDetector(IEndpointDetector):
    """Smart endpoint detection using multiple signals"""
    
    def __init__(self, config: Optional[EndpointConfig] = None):
        self.config = config or EndpointConfig()
        self.last_speech_time = 0
        self.utterance_start_time = 0
        self.is_speaking = False
        self.silence_buffer = []
        self.transcript_history = []
        
        # Semantic completion patterns
        self.completion_patterns = [
            r'\b(thank you|thanks|goodbye|bye|stop|that\'s all|that is all)\b',
            r'\b(please|could you|can you|would you|will you)\s+\w+',  # Complete questions
            r'\b(yes|no|yeah|nope|okay|ok|alright|sure)$',  # Short confirmations
        ]
        
        # Load ML model for semantic completion if available
        self.semantic_model = None
        if self.config.semantic_completion_enabled:
            asyncio.create_task(self._load_semantic_model())
    
    async def detect_endpoint(
        self,
        audio: np.ndarray,
        transcript: str
    ) -> bool:
        """Detect if utterance is complete"""
        
        # Check multiple signals
        silence_endpoint = await self._check_silence_endpoint(audio)
        punctuation_endpoint = self._check_punctuation_endpoint(transcript)
        semantic_endpoint = await self._check_semantic_endpoint(transcript)
        pattern_endpoint = self._check_pattern_endpoint(transcript)
        
        # Decision logic (can be weighted or use ML)
        if silence_endpoint and len(transcript.strip()) > 0:
            logger.debug(f"Silence endpoint detected: {transcript}")
            return True
        
        if punctuation_endpoint:
            logger.debug(f"Punctuation endpoint detected: {transcript}")
            return True
        
        if semantic_endpoint and silence_endpoint:
            logger.debug(f"Semantic + silence endpoint detected: {transcript}")
            return True
        
        if pattern_endpoint:
            logger.debug(f"Pattern endpoint detected: {transcript}")
            return True
        
        return False
    
    async def _check_silence_endpoint(self, audio: np.ndarray) -> bool:
        """Check if silence duration exceeds threshold"""
        
        # Calculate audio energy
        energy = np.sqrt(np.mean(audio ** 2))
        current_time = time.time() * 1000  # Convert to milliseconds
        
        if energy < self.config.energy_threshold:
            # Silence detected
            if self.is_speaking:
                # Track silence duration
                silence_duration = current_time - self.last_speech_time
                if silence_duration >= self.config.silence_threshold_ms:
                    # Check minimum utterance duration
                    utterance_duration = self.last_speech_time - self.utterance_start_time
                    if utterance_duration >= self.config.min_utterance_duration_ms:
                        self.is_speaking = False
                        return True
        else:
            # Speech detected
            if not self.is_speaking:
                self.is_speaking = True
                self.utterance_start_time = current_time
            self.last_speech_time = current_time
        
        return False
    
    def _check_punctuation_endpoint(self, transcript: str) -> bool:
        """Check if transcript ends with endpoint punctuation"""
        
        if not transcript:
            return False
        
        # Get last character (handling unicode)
        transcript = transcript.strip()
        if not transcript:
            return False
        
        # Check if ends with trigger punctuation
        for punct in self.config.punctuation_triggers:
            if transcript.endswith(punct):
                return True
        
        return False
    
    async def _check_semantic_endpoint(self, transcript: str) -> bool:
        """Check if transcript is semantically complete using ML"""
        
        if not self.config.semantic_completion_enabled or not self.semantic_model:
            return False
        
        if not transcript or len(transcript.strip()) < 3:
            return False
        
        try:
            # Use model to predict if sentence is complete
            # This is a placeholder - would use actual model
            # For now, use heuristics
            
            # Check if it looks like a complete thought
            words = transcript.strip().split()
            if len(words) < 2:
                return False
            
            # Check for subject-verb patterns
            has_verb = any(word in transcript.lower() for word in 
                         ['is', 'are', 'was', 'were', 'have', 'has', 'had',
                          'do', 'does', 'did', 'will', 'would', 'could',
                          'should', 'can', 'want', 'need', 'like'])
            
            # Simple heuristic: if has verb and > 3 words, might be complete
            if has_verb and len(words) >= 3:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Semantic endpoint detection error: {e}")
            return False
    
    def _check_pattern_endpoint(self, transcript: str) -> bool:
        """Check if transcript matches completion patterns"""
        
        if not transcript:
            return False
        
        transcript_lower = transcript.lower().strip()
        
        for pattern in self.completion_patterns:
            if re.search(pattern, transcript_lower, re.IGNORECASE):
                # Extra check for questions - ensure they have enough context
                if 'you' in pattern and len(transcript_lower.split()) < 3:
                    continue
                return True
        
        return False
    
    async def _load_semantic_model(self) -> None:
        """Load ML model for semantic completion detection"""
        
        try:
            # Check if a lightweight model exists
            model_path = "models/voice/endpoint/semantic_completion.onnx"
            import os
            
            if os.path.exists(model_path):
                import onnxruntime as ort
                self.semantic_model = ort.InferenceSession(
                    model_path,
                    providers=['CPUExecutionProvider']
                )
                logger.info("Loaded semantic completion model")
            else:
                logger.info("Semantic model not found, using heuristics")
                
        except Exception as e:
            logger.warning(f"Could not load semantic model: {e}")
            self.semantic_model = None
    
    def reset(self) -> None:
        """Reset detector state"""
        self.last_speech_time = 0
        self.utterance_start_time = 0
        self.is_speaking = False
        self.silence_buffer.clear()
        self.transcript_history.clear()

class PredictiveEndpointDetector(SmartEndpointDetector):
    """Advanced detector with predictive capabilities"""
    
    def __init__(self, config: Optional[EndpointConfig] = None):
        super().__init__(config)
        self.prediction_threshold = 0.8
        self.context_window = 5  # Look at last 5 utterances
    
    async def detect_endpoint(
        self,
        audio: np.ndarray,
        transcript: str
    ) -> Tuple[bool, float]:
        """Detect endpoint with confidence score"""
        
        # Get base detection
        is_endpoint = await super().detect_endpoint(audio, transcript)
        
        # Calculate confidence based on multiple factors
        confidence = 0.0
        
        if is_endpoint:
            # Start with base confidence
            confidence = 0.6
            
            # Boost for punctuation
            if self._check_punctuation_endpoint(transcript):
                confidence += 0.2
            
            # Boost for patterns
            if self._check_pattern_endpoint(transcript):
                confidence += 0.1
            
            # Boost for longer silence
            current_time = time.time() * 1000
            if self.last_speech_time > 0:
                silence_duration = current_time - self.last_speech_time
                if silence_duration > 2000:  # 2 seconds
                    confidence += 0.1
            
            confidence = min(confidence, 1.0)
        
        return is_endpoint, confidence
    
    def predict_next_endpoint(self, transcript: str) -> float:
        """Predict how likely the next pause will be an endpoint"""
        
        if not transcript:
            return 0.0
        
        # Analyze transcript structure
        words = transcript.split()
        word_count = len(words)
        
        # Short utterances likely to end soon
        if word_count <= 3:
            return 0.8
        
        # Check if building to a question
        question_words = ['what', 'when', 'where', 'who', 'why', 'how', 'is', 'are', 'can', 'could']
        if any(word in transcript.lower() for word in question_words):
            if '?' not in transcript:
                return 0.3  # Still building question
            else:
                return 0.9  # Question complete
        
        # Check for conjunction at end (indicates more coming)
        conjunctions = ['and', 'but', 'or', 'so', 'because', 'if', 'when']
        last_word = words[-1].lower().rstrip(',.!?')
        if last_word in conjunctions:
            return 0.1  # More likely to continue
        
        # Default based on length
        if word_count > 10:
            return 0.7  # Longer utterances likely near end
        
        return 0.5  # Neutral