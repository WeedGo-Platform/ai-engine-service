"""
Offline Voice Interface
Real-time speech recognition and synthesis for domain-agnostic AI
"""
import asyncio
import numpy as np
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path
import time
import json

logger = logging.getLogger(__name__)

class VoiceState(Enum):
    """Voice pipeline states"""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"

@dataclass
class VoiceConfig:
    """Voice system configuration"""
    # STT Settings
    stt_model: str = "whisper-base"
    stt_language: str = "auto"  # Auto-detect
    stt_device: str = "cpu"  # cpu, cuda, mps
    
    # TTS Settings
    tts_model: str = "piper-amy"
    tts_speed: float = 1.0
    tts_pitch: float = 0.0
    
    # VAD Settings
    vad_threshold: float = 0.5
    vad_min_speech_ms: int = 250
    vad_max_silence_ms: int = 1000
    
    # Wake Word
    wake_words: List[str] = None
    wake_threshold: float = 0.8
    
    # Audio Settings
    sample_rate: int = 16000
    chunk_size: int = 480  # 30ms at 16kHz
    
    # Performance
    enable_gpu: bool = False
    max_threads: int = 4
    cache_size: int = 100  # MB

@dataclass
class AudioSegment:
    """Audio segment with metadata"""
    data: np.ndarray
    timestamp: float
    duration: float
    is_speech: bool
    energy: float
    speaker_id: Optional[str] = None

class WhisperOffline:
    """Offline Whisper implementation using whisper.cpp"""
    
    def __init__(self, model_path: str, config: VoiceConfig):
        self.model_path = model_path
        self.config = config
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load Whisper model"""
        try:
            # This would use whisper.cpp bindings
            # import whisper_cpp
            # self.model = whisper_cpp.load_model(self.model_path)
            logger.info(f"Loaded Whisper model: {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load Whisper: {e}")
    
    async def transcribe(self, audio: np.ndarray, language: Optional[str] = None) -> Dict:
        """Transcribe audio to text"""
        start_time = time.time()
        
        # Simulate transcription for demo
        result = {
            "text": "Transcribed text from audio",
            "language": language or "en",
            "confidence": 0.95,
            "segments": [],
            "duration": time.time() - start_time
        }
        
        # In production:
        # result = self.model.transcribe(audio, language=language)
        
        return result
    
    async def transcribe_streaming(self, audio_stream) -> str:
        """Real-time streaming transcription"""
        # This would process audio chunks as they arrive
        partial_text = ""
        async for chunk in audio_stream:
            # Process chunk
            partial_text += await self.transcribe(chunk)
        return partial_text

class PiperTTS:
    """Offline TTS using Piper"""
    
    def __init__(self, voice_path: str, config: VoiceConfig):
        self.voice_path = voice_path
        self.config = config
        self.voice_model = None
        self._load_voice()
    
    def _load_voice(self):
        """Load Piper voice model"""
        try:
            # This would use Piper Python bindings
            # import piper
            # self.voice_model = piper.load_voice(self.voice_path)
            logger.info(f"Loaded Piper voice: {self.voice_path}")
        except Exception as e:
            logger.error(f"Failed to load Piper: {e}")
    
    async def synthesize(self, text: str, voice_params: Optional[Dict] = None) -> np.ndarray:
        """Convert text to speech"""
        start_time = time.time()
        
        # Apply voice parameters
        params = voice_params or {}
        speed = params.get("speed", self.config.tts_speed)
        pitch = params.get("pitch", self.config.tts_pitch)
        
        # Simulate synthesis for demo
        duration = len(text) * 0.05  # Rough estimate
        samples = int(duration * self.config.sample_rate)
        audio = np.random.randn(samples) * 0.1  # Placeholder
        
        # In production:
        # audio = self.voice_model.synthesize(text, speed=speed, pitch=pitch)
        
        logger.debug(f"TTS synthesis took {time.time() - start_time:.3f}s")
        return audio

class SileroVAD:
    """Voice Activity Detection using Silero"""
    
    def __init__(self, config: VoiceConfig):
        self.config = config
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load Silero VAD model"""
        try:
            # This would load the actual Silero model
            # import silero_vad
            # self.model = silero_vad.load_model()
            logger.info("Loaded Silero VAD model")
        except Exception as e:
            logger.error(f"Failed to load VAD: {e}")
    
    def is_speech(self, audio: np.ndarray) -> bool:
        """Detect if audio contains speech"""
        # Calculate energy
        energy = np.sqrt(np.mean(audio ** 2))
        
        # Simple energy-based VAD for demo
        is_speech = energy > 0.01
        
        # In production:
        # probability = self.model.predict(audio)
        # is_speech = probability > self.config.vad_threshold
        
        return is_speech
    
    def get_speech_segments(self, audio: np.ndarray) -> List[tuple]:
        """Get timestamps of speech segments"""
        segments = []
        chunk_duration = len(audio) / self.config.sample_rate / self.config.chunk_size
        
        in_speech = False
        start_time = 0
        
        for i in range(0, len(audio), self.config.chunk_size):
            chunk = audio[i:i + self.config.chunk_size]
            if self.is_speech(chunk):
                if not in_speech:
                    start_time = i / self.config.sample_rate
                    in_speech = True
            else:
                if in_speech:
                    end_time = i / self.config.sample_rate
                    segments.append((start_time, end_time))
                    in_speech = False
        
        return segments

class VoiceInterface:
    """
    Main voice interface combining STT, TTS, and VAD
    """
    
    def __init__(self, config: VoiceConfig, domain_engine=None):
        self.config = config
        self.domain_engine = domain_engine
        
        # Initialize components
        self.stt = WhisperOffline("models/whisper-base.bin", config)
        self.tts = PiperTTS("models/piper-voice.onnx", config)
        self.vad = SileroVAD(config)
        
        # State management
        self.state = VoiceState.IDLE
        self.audio_buffer = []
        self.transcription_buffer = ""
        
        # Voice profiles per domain
        self.voice_profiles = self._load_voice_profiles()
        
        # Callbacks
        self.on_wake_word: Optional[Callable] = None
        self.on_speech_start: Optional[Callable] = None
        self.on_speech_end: Optional[Callable] = None
        self.on_transcription: Optional[Callable] = None
        
        logger.info("Voice interface initialized")
    
    def _load_voice_profiles(self) -> Dict:
        """Load domain-specific voice profiles"""
        return {
            "budtender": {
                "voice": "piper-ryan",
                "speed": 0.95,
                "pitch": -1,
                "style": "casual",
                "fillers": ["you know", "like", "basically"],
                "personality": "friendly and knowledgeable"
            },
            "healthcare": {
                "voice": "piper-amy",
                "speed": 0.9,
                "pitch": 0,
                "style": "professional",
                "fillers": ["let me explain", "importantly"],
                "personality": "caring and clear"
            },
            "legal": {
                "voice": "piper-john",
                "speed": 0.85,
                "pitch": -2,
                "style": "formal",
                "fillers": ["specifically", "according to"],
                "personality": "authoritative and precise"
            }
        }
    
    async def process_audio_stream(self, audio_chunk: np.ndarray) -> Optional[np.ndarray]:
        """
        Process incoming audio chunk
        Returns synthesized speech response if ready
        """
        
        # 1. Check for speech
        if self.vad.is_speech(audio_chunk):
            if self.state == VoiceState.IDLE:
                self.state = VoiceState.LISTENING
                if self.on_speech_start:
                    await self.on_speech_start()
            
            # Add to buffer
            self.audio_buffer.append(audio_chunk)
            
            # Check for pause (end of utterance)
            if len(self.audio_buffer) > 10:  # Minimum chunks
                recent_chunks = self.audio_buffer[-5:]
                if not any(self.vad.is_speech(chunk) for chunk in recent_chunks):
                    # User stopped speaking
                    return await self._process_complete_utterance()
        
        return None
    
    async def _process_complete_utterance(self) -> Optional[np.ndarray]:
        """Process complete user utterance"""
        
        self.state = VoiceState.PROCESSING
        
        try:
            # 1. Combine audio buffer
            full_audio = np.concatenate(self.audio_buffer)
            self.audio_buffer.clear()
            
            # 2. Transcribe
            transcription = await self.stt.transcribe(full_audio)
            text = transcription["text"]
            language = transcription["language"]
            
            logger.info(f"Transcribed ({language}): {text}")
            
            if self.on_transcription:
                await self.on_transcription(text, language)
            
            # 3. Process through domain engine
            if self.domain_engine:
                response = await self.domain_engine.process(
                    message=text,
                    metadata={"language": language, "input_mode": "voice"}
                )
                
                # 4. Generate speech response
                response_audio = await self.generate_response(
                    response["message"],
                    domain=response.get("domain", "default"),
                    emotion=response.get("emotion", "neutral")
                )
                
                self.state = VoiceState.SPEAKING
                return response_audio
            
        except Exception as e:
            logger.error(f"Error processing utterance: {e}")
            self.state = VoiceState.ERROR
        
        finally:
            # Reset to idle after processing
            await asyncio.sleep(0.5)
            self.state = VoiceState.IDLE
        
        return None
    
    async def generate_response(
        self,
        text: str,
        domain: str = "default",
        emotion: str = "neutral"
    ) -> np.ndarray:
        """Generate speech response with domain-specific voice"""
        
        # Get voice profile for domain
        profile = self.voice_profiles.get(domain, self.voice_profiles.get("default", {}))
        
        # Adjust for emotion
        voice_params = self._adjust_for_emotion(profile, emotion)
        
        # Add natural elements
        text = self._add_natural_elements(text, profile)
        
        # Generate speech
        audio = await self.tts.synthesize(text, voice_params)
        
        return audio
    
    def _adjust_for_emotion(self, profile: Dict, emotion: str) -> Dict:
        """Adjust voice parameters based on emotion"""
        params = profile.copy()
        
        emotion_adjustments = {
            "happy": {"speed": 1.1, "pitch": 2},
            "sad": {"speed": 0.9, "pitch": -2},
            "excited": {"speed": 1.2, "pitch": 3},
            "calm": {"speed": 0.85, "pitch": -1},
            "urgent": {"speed": 1.15, "pitch": 1},
            "empathetic": {"speed": 0.9, "pitch": 0}
        }
        
        if emotion in emotion_adjustments:
            adj = emotion_adjustments[emotion]
            params["speed"] = params.get("speed", 1.0) * adj["speed"]
            params["pitch"] = params.get("pitch", 0) + adj["pitch"]
        
        return params
    
    def _add_natural_elements(self, text: str, profile: Dict) -> str:
        """Add natural speech elements"""
        
        # Add occasional fillers for naturalness
        if "fillers" in profile:
            import random
            if random.random() < 0.2:  # 20% chance
                filler = random.choice(profile["fillers"])
                # Insert filler at natural break
                sentences = text.split(". ")
                if len(sentences) > 1:
                    insert_pos = random.randint(1, len(sentences) - 1)
                    sentences.insert(insert_pos, filler)
                    text = ". ".join(sentences)
        
        # Add pauses (SSML-style markers)
        text = text.replace(". ", ". <break time='200ms'/> ")
        text = text.replace(", ", ", <break time='100ms'/> ")
        
        return text
    
    async def calibrate_user(self, duration: float = 5.0) -> Dict:
        """Calibrate for specific user's voice"""
        
        logger.info(f"Starting voice calibration for {duration} seconds...")
        
        calibration_data = {
            "average_energy": 0,
            "pitch_range": (0, 0),
            "speaking_rate": 0,
            "accent_markers": [],
            "noise_profile": None
        }
        
        # Collect audio samples
        # Analyze voice characteristics
        # Create user profile
        
        return calibration_data
    
    def set_domain_voice(self, domain: str, voice_config: Dict):
        """Set custom voice for a domain"""
        self.voice_profiles[domain] = voice_config
        logger.info(f"Updated voice profile for domain: {domain}")
    
    async def interrupt(self):
        """Handle interruption during speech"""
        if self.state == VoiceState.SPEAKING:
            logger.info("Speech interrupted by user")
            self.state = VoiceState.LISTENING
            # Stop TTS playback
            # Clear audio output buffer
    
    def get_state(self) -> Dict:
        """Get current voice interface state"""
        return {
            "state": self.state.value,
            "buffer_size": len(self.audio_buffer),
            "active_domain": getattr(self.domain_engine, "active_domain", None),
            "is_listening": self.state == VoiceState.LISTENING,
            "is_speaking": self.state == VoiceState.SPEAKING
        }

class ConversationManager:
    """Manages natural conversation flow"""
    
    def __init__(self, voice_interface: VoiceInterface):
        self.voice = voice_interface
        self.turn_history = []
        self.interruption_count = 0
        self.backchannel_enabled = True
        
    async def manage_turn_taking(self):
        """Handle conversation turn-taking"""
        
        # Detect interruption attempts
        if self.voice.state == VoiceState.SPEAKING:
            # Check if user is trying to speak
            # Yield turn if appropriate
            pass
        
        # Add backchanneling ("uh-huh", "I see")
        if self.backchannel_enabled:
            # Generate appropriate backchannel
            pass
    
    def should_yield_turn(self, user_energy: float) -> bool:
        """Determine if should yield speaking turn"""
        # If user energy suddenly increases during AI speech
        # It's likely an interruption attempt
        return user_energy > 0.7

class DialectAdapter:
    """Adapt to different dialects and accents"""
    
    def __init__(self):
        self.dialect_models = {}
        self.accent_profiles = {}
    
    def detect_dialect(self, audio_features: Dict) -> str:
        """Detect speaker's dialect"""
        # Analyze phonetic features
        # Match against known dialect patterns
        return "en-US"  # Default
    
    def adapt_model(self, dialect: str):
        """Load dialect-specific model"""
        if dialect in self.dialect_models:
            return self.dialect_models[dialect]
        return None