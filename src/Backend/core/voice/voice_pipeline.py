"""
Voice Pipeline Orchestrator for V5
Combines STT, TTS, and VAD into a complete voice system
"""
import asyncio
import logging
import time
import platform
from typing import Dict, Any, Optional, Callable, AsyncGenerator, Union
from dataclasses import dataclass
import numpy as np
from enum import Enum

from .base_handler import VoiceState, AudioConfig
from .whisper_stt import WhisperSTTHandler
from .piper_tts import PiperTTSHandler
from .vad_handler import SileroVADHandler
from .whisper_wake_word import WhisperWakeWordHandler
from .wake_word_handler import WakeWordConfig, WakeWordModel

logger = logging.getLogger(__name__)

class PipelineMode(Enum):
    """Voice pipeline operating modes"""
    MANUAL = "manual"  # Process on demand
    AUTO_VAD = "auto_vad"  # Automatic with VAD
    CONTINUOUS = "continuous"  # Continuous streaming
    WAKE_WORD = "wake_word"  # Wake word activated

@dataclass
class VoiceSession:
    """Voice interaction session"""
    session_id: str
    mode: PipelineMode
    start_time: float
    language: Optional[str] = None
    domain: str = "general"
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}

class VoicePipeline:
    """Main voice processing pipeline"""
    
    def __init__(
        self,
        stt_model: str = "base",
        config: Optional[AudioConfig] = None,
        wake_word_enabled: bool = True
    ):
        """Initialize voice pipeline

        Args:
            stt_model: Whisper model size
            config: Audio configuration
            wake_word_enabled: Enable wake word detection
        """
        self.config = config or AudioConfig()

        # Initialize handlers
        self.stt = WhisperSTTHandler(stt_model, self.config)

        # Use only Piper neural TTS for production compatibility
        self.tts = PiperTTSHandler(self.config)
        logger.info("Using high-quality Piper neural TTS handler")

        self.vad = SileroVADHandler(self.config)

        # Initialize wake word handler if enabled
        self.wake_word_enabled = wake_word_enabled
        self.wake_word = None
        if wake_word_enabled:
            wake_config = WakeWordConfig(
                models=[WakeWordModel.HEY_WEEDGO, WakeWordModel.WEEDGO],
                threshold=0.7,
                sensitivity=0.6
            )
            self.wake_word = WhisperWakeWordHandler(
                self.config,
                wake_config,
                whisper_model="tiny"  # Use tiny model for wake word detection
            )
            logger.info("Wake word detection enabled")

        # Pipeline state
        self.is_initialized = False
        self.current_session: Optional[VoiceSession] = None
        self.mode = PipelineMode.MANUAL
        self.wake_word_active = False

        # Audio buffer for streaming
        self.audio_buffer = []
        self.silence_counter = 0
        self.silence_threshold = 3  # Number of silent chunks before processing

        # Callbacks
        self.on_transcription: Optional[Callable] = None
        self.on_synthesis: Optional[Callable] = None
        self.on_vad_change: Optional[Callable] = None
        self.on_wake_word: Optional[Callable] = None
    
    async def initialize(self) -> bool:
        """Initialize all voice components"""
        try:
            logger.info("Initializing voice pipeline...")

            # Build initialization tasks
            init_tasks = [
                self.stt.initialize(),
                self.tts.initialize(),
                self.vad.initialize()
            ]
            names = ["STT", "TTS", "VAD"]

            # Add wake word initialization if enabled
            if self.wake_word:
                init_tasks.append(self.wake_word.initialize())
                names.append("Wake Word")

            # Initialize all handlers in parallel
            results = await asyncio.gather(*init_tasks, return_exceptions=True)

            # Check results
            for i, (result, name) in enumerate(zip(results, names)):
                if isinstance(result, Exception):
                    logger.error(f"Failed to initialize {name}: {result}")
                    return False
                elif not result:
                    logger.error(f"Failed to initialize {name}")
                    return False

            # Load custom wake word models if available
            if self.wake_word:
                from pathlib import Path
                custom_models_dir = Path("models/voice/wake_words")
                if custom_models_dir.exists():
                    model_paths = {}
                    for model_file in custom_models_dir.glob("*.txt"):
                        model_name = model_file.stem
                        model_paths[model_name] = model_file
                    if model_paths:
                        await self.wake_word.load_models(model_paths)
                        logger.info(f"Loaded {len(model_paths)} custom wake word models")

            self.is_initialized = True
            logger.info("✅ Voice pipeline initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Pipeline initialization failed: {e}")
            return False
    
    async def process_audio(
        self,
        audio: Union[np.ndarray, bytes],
        mode: PipelineMode = PipelineMode.AUTO_VAD,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process audio through the pipeline
        
        Args:
            audio: Audio data
            mode: Processing mode
            language: Language for transcription
            
        Returns:
            Processing results
        """
        if not self.is_initialized:
            raise RuntimeError("Pipeline not initialized")
        
        # Create session if needed
        if not self.current_session:
            self.current_session = VoiceSession(
                session_id=f"session_{int(time.time())}",
                mode=mode,
                start_time=time.time(),
                language=language
            )
        
        results = {
            "session_id": self.current_session.session_id,
            "has_speech": False,
            "transcription": None,
            "vad_result": None,
            "processing_time_ms": 0
        }
        
        start_time = time.time()
        
        try:
            if mode == PipelineMode.AUTO_VAD:
                # Use VAD to detect speech
                vad_result = await self.vad.detect(audio)
                results["vad_result"] = {
                    "has_speech": vad_result.has_speech,
                    "confidence": vad_result.confidence,
                    "segments": vad_result.speech_segments
                }
                
                if vad_result.has_speech:
                    results["has_speech"] = True
                    
                    # Transcribe detected speech
                    transcription = await self.stt.transcribe(audio, language)
                    results["transcription"] = {
                        "text": transcription.text,
                        "confidence": transcription.confidence,
                        "language": transcription.language
                    }
                    
                    # Call transcription callback
                    if self.on_transcription:
                        await self.on_transcription(transcription)
                    
            elif mode == PipelineMode.MANUAL:
                # Direct transcription without VAD
                transcription = await self.stt.transcribe(audio, language)
                results["transcription"] = {
                    "text": transcription.text,
                    "confidence": transcription.confidence,
                    "language": transcription.language
                }
                results["has_speech"] = bool(transcription.text)
                
                if self.on_transcription:
                    await self.on_transcription(transcription)
            
            elif mode == PipelineMode.WAKE_WORD:
                # Wake word detection mode
                if not self.wake_word:
                    logger.warning("Wake word handler not initialized")
                    results["error"] = "Wake word detection not available"
                    return results

                # First detect wake word
                wake_detection = await self.wake_word.detect(audio)
                results["wake_word_detection"] = {
                    "detected": wake_detection.detected,
                    "wake_word": wake_detection.wake_word,
                    "confidence": wake_detection.confidence
                }

                if wake_detection.detected:
                    logger.info(f"Wake word detected: {wake_detection.wake_word}")
                    self.wake_word_active = True
                    results["has_speech"] = True

                    # Trigger wake word callback
                    if self.on_wake_word:
                        await self.on_wake_word(wake_detection)

                    # After wake word, process following audio for commands
                    # This would typically transition to listening mode
                    # For now, just transcribe the audio after wake word
                    if wake_detection.audio_context is not None:
                        transcription = await self.stt.transcribe(
                            wake_detection.audio_context,
                            language
                        )
                        results["transcription"] = {
                            "text": transcription.text,
                            "confidence": transcription.confidence,
                            "language": transcription.language
                        }

                        if self.on_transcription:
                            await self.on_transcription(transcription)

            elif mode == PipelineMode.CONTINUOUS:
                # Add to buffer for continuous processing
                self.audio_buffer.append(audio)
                
                # Process when buffer is large enough
                if len(self.audio_buffer) >= 5:  # ~0.5 seconds at typical chunk size
                    full_audio = np.concatenate(self.audio_buffer)
                    
                    # Check for speech
                    vad_result = await self.vad.detect(full_audio)
                    
                    if vad_result.has_speech:
                        # Transcribe
                        transcription = await self.stt.transcribe(full_audio, language)
                        results["transcription"] = {
                            "text": transcription.text,
                            "confidence": transcription.confidence,
                            "language": transcription.language
                        }
                        results["has_speech"] = True
                        
                        # Clear buffer after processing
                        self.audio_buffer = []
                        self.silence_counter = 0
                    else:
                        # Count silence
                        self.silence_counter += 1
                        
                        # Clear buffer if too much silence
                        if self.silence_counter >= self.silence_threshold:
                            self.audio_buffer = []
                            self.silence_counter = 0
            
        except Exception as e:
            logger.error(f"Pipeline processing error: {e}")
            results["error"] = str(e)
        
        results["processing_time_ms"] = (time.time() - start_time) * 1000
        return results
    
    async def synthesize_response(
        self,
        text: str,
        voice: Optional[str] = None,
        language: Optional[str] = None,
        speed: float = 1.0
    ) -> bytes:
        """Synthesize speech from text
        
        Args:
            text: Text to synthesize
            voice: Voice ID
            language: Language code
            speed: Speech rate
            
        Returns:
            Audio data as bytes
        """
        if not self.is_initialized:
            raise RuntimeError("Pipeline not initialized")
        
        try:
            # Apply domain-specific adjustments
            if self.current_session and self.current_session.domain:
                text = self._apply_domain_style(text, self.current_session.domain)
            
            # Synthesize speech
            result = await self.tts.synthesize(text, voice, language, speed)
            
            # Call synthesis callback
            if self.on_synthesis:
                await self.on_synthesis(result)
            
            return result.audio
            
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            raise
    
    async def process_stream(
        self,
        audio_stream: AsyncGenerator[bytes, None],
        mode: PipelineMode = PipelineMode.AUTO_VAD,
        language: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process streaming audio
        
        Args:
            audio_stream: Async generator of audio chunks
            mode: Processing mode
            language: Language for transcription
            
        Yields:
            Processing results for each chunk
        """
        if not self.is_initialized:
            raise RuntimeError("Pipeline not initialized")
        
        # Create session
        self.current_session = VoiceSession(
            session_id=f"stream_{int(time.time())}",
            mode=mode,
            start_time=time.time(),
            language=language
        )
        
        buffer = []
        async for chunk in audio_stream:
            buffer.append(chunk)
            
            # Process periodically
            if len(buffer) >= 10:  # Process every ~1 second
                full_audio = b''.join(buffer) if isinstance(buffer[0], bytes) else np.concatenate(buffer)
                
                # Process audio
                result = await self.process_audio(full_audio, mode, language)
                
                # Clear buffer if speech was found
                if result.get("has_speech"):
                    buffer = []
                    yield result
                elif len(buffer) > 50:  # Clear if buffer gets too large
                    buffer = buffer[-10:]  # Keep last second
    
    def _apply_domain_style(self, text: str, domain: str) -> str:
        """Apply domain-specific style to text
        
        Args:
            text: Original text
            domain: Domain context
            
        Returns:
            Styled text
        """
        # Domain-specific modifications
        if domain == "healthcare":
            # More formal, clear enunciation
            text = text.replace("gonna", "going to")
            text = text.replace("wanna", "want to")
            
        elif domain == "budtender":
            # More casual, friendly
            text = text.replace("Hello", "Hey there")
            text = text.replace("Goodbye", "Take it easy")
            
        elif domain == "legal":
            # Very formal
            text = text.replace("can't", "cannot")
            text = text.replace("won't", "will not")
        
        return text
    
    async def set_callbacks(
        self,
        on_transcription: Optional[Callable] = None,
        on_synthesis: Optional[Callable] = None,
        on_vad_change: Optional[Callable] = None,
        on_wake_word: Optional[Callable] = None
    ):
        """Set pipeline callbacks

        Args:
            on_transcription: Called when transcription completes
            on_synthesis: Called when synthesis completes
            on_vad_change: Called when VAD state changes
            on_wake_word: Called when wake word is detected
        """
        self.on_transcription = on_transcription
        self.on_synthesis = on_synthesis
        self.on_vad_change = on_vad_change
        self.on_wake_word = on_wake_word

        # Register wake word callback with handler
        if self.wake_word and on_wake_word:
            self.wake_word.register_callback(on_wake_word)
    
    async def cleanup(self):
        """Clean up all resources"""
        try:
            cleanup_tasks = [
                self.stt.cleanup(),
                self.tts.cleanup(),
                self.vad.cleanup()
            ]

            # Add wake word cleanup if initialized
            if self.wake_word:
                cleanup_tasks.append(self.wake_word.cleanup())

            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            
            self.is_initialized = False
            self.current_session = None
            self.audio_buffer = []
            
            logger.info("Voice pipeline cleaned up")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics from all handlers"""
        return {
            "stt": self.stt.get_metrics(),
            "tts": self.tts.get_metrics(),
            "vad": self.vad.get_metrics(),
            "session": {
                "id": self.current_session.session_id if self.current_session else None,
                "duration_s": (time.time() - self.current_session.start_time) if self.current_session else 0
            }
        }