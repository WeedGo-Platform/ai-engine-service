"""
Whisper Speech-to-Text handler for V5
Fully offline speech recognition using OpenAI Whisper
"""
import whisper
import numpy as np
import asyncio
import logging
import time
from typing import Dict, Any, Optional, Union
import torch
from pathlib import Path
import wave
import io

from .base_handler import STTHandler, TranscriptionResult, AudioConfig, VoiceState

logger = logging.getLogger(__name__)

class WhisperSTTHandler(STTHandler):
    """Offline speech recognition using Whisper models"""
    
    def __init__(self, model_name: str = "base", config: Optional[AudioConfig] = None):
        """Initialize with Whisper model

        Args:
            model_name: Model size (tiny, base, small, medium, large)
            config: Audio configuration
        """
        super().__init__(config)
        self.model_name = model_name
        self.model = None
        self.model_path = Path(f"models/voice/whisper/{model_name}.bin")
        
    async def initialize(self) -> bool:
        """Initialize and load Whisper model"""
        try:
            self.set_state(VoiceState.PROCESSING)

            logger.info(f"Initializing Whisper {self.model_name} model")

            # Run model loading in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None,
                self._load_model_sync
            )
            
            if self.model:
                logger.info(f"✅ Whisper {self.model_name} model loaded successfully")
                self.set_state(VoiceState.IDLE)
                return True
            else:
                self.set_state(VoiceState.ERROR)
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize Whisper: {e}")
            self.set_state(VoiceState.ERROR)
            return False
    
    def _load_model_sync(self):
        """Synchronously load the model (for thread pool execution)"""
        try:
            # Try loading by model name first (this will use Whisper's built-in loading)
            logger.info(f"Loading Whisper model: {self.model_name}")
            model = whisper.load_model(self.model_name)
            logger.info(f"Successfully loaded Whisper model: {self.model_name}")
            return model
        except Exception as e:
            logger.error(f"Error loading model by name: {e}")
            # Try loading from file path
            try:
                logger.info(f"Trying to load from file path: {self.model_path}")
                model = whisper.load_model(str(self.model_path))
                return model
            except Exception as e2:
                logger.error(f"File path loading also failed: {e2}")
                return None
    
    async def transcribe(
        self, 
        audio: Union[np.ndarray, bytes],
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """Transcribe audio to text
        
        Args:
            audio: Audio data as numpy array or bytes
            language: Optional language code (None for auto-detect)
            
        Returns:
            TranscriptionResult with transcribed text
        """
        start_time = time.time()
        
        try:
            self.set_state(VoiceState.PROCESSING)
            
            # Convert bytes to numpy array if needed
            if isinstance(audio, bytes):
                audio = self._bytes_to_numpy(audio)
            
            # Ensure audio is float32 and normalized
            audio = self._preprocess_audio(audio)
            
            # Run transcription in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._transcribe_sync,
                audio,
                language
            )
            
            # Calculate metrics
            duration_ms = (time.time() - start_time) * 1000
            self.update_metrics(duration_ms, success=True)
            
            self.set_state(VoiceState.IDLE)
            
            return TranscriptionResult(
                text=result["text"].strip(),
                confidence=self._estimate_confidence(result),
                language=result.get("language", language or "en"),
                timestamps=result.get("segments"),
                duration_ms=duration_ms
            )
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            duration_ms = (time.time() - start_time) * 1000
            self.update_metrics(duration_ms, success=False)
            self.set_state(VoiceState.ERROR)
            
            return TranscriptionResult(
                text="",
                confidence=0.0,
                language=language or "en",
                duration_ms=duration_ms
            )
    
    async def transcribe_stream(self, audio_stream: Any) -> TranscriptionResult:
        """Transcribe streaming audio
        
        This collects audio chunks and transcribes when silence is detected
        """
        # Buffer for collecting audio chunks
        audio_buffer = []
        
        async for chunk in audio_stream:
            audio_buffer.append(chunk)
            
            # Check if we have enough audio (e.g., 3 seconds)
            total_samples = sum(len(c) for c in audio_buffer)
            if total_samples >= self.config.sample_rate * 3:
                # Concatenate and transcribe
                full_audio = np.concatenate(audio_buffer)
                result = await self.transcribe(full_audio)
                
                # Clear buffer for next segment
                audio_buffer = []
                
                # Yield intermediate result
                if result.text:
                    return result
        
        # Transcribe any remaining audio
        if audio_buffer:
            full_audio = np.concatenate(audio_buffer)
            return await self.transcribe(full_audio)
        
        return TranscriptionResult(text="", confidence=0.0, language="en")
    
    def _transcribe_sync(self, audio: np.ndarray, language: Optional[str]) -> Dict:
        """Synchronous transcription for thread pool"""
        if self.model is None:
            raise RuntimeError("Model not initialized")
        
        # Whisper expects 16kHz audio
        result = self.model.transcribe(
            audio,
            language=language,  # None for auto-detect
            task="transcribe",
            fp16=False,  # Use FP32 for CPU
            verbose=False
        )
        return result
    
    def _preprocess_audio(self, audio: np.ndarray) -> np.ndarray:
        """Preprocess audio for Whisper"""
        # Ensure float32
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
        
        # Normalize to [-1, 1] if needed
        if np.abs(audio).max() > 1.0:
            audio = audio / 32768.0
        
        # Ensure 1D array
        if len(audio.shape) > 1:
            audio = audio.flatten()
        
        return audio
    
    def _bytes_to_numpy(self, audio_bytes: bytes) -> np.ndarray:
        """Convert audio bytes to numpy array"""
        # Assume 16-bit PCM audio
        audio = np.frombuffer(audio_bytes, dtype=np.int16)
        return audio.astype(np.float32) / 32768.0
    
    def _estimate_confidence(self, result: Dict) -> float:
        """Estimate confidence from Whisper result
        
        Whisper doesn't provide direct confidence scores,
        so we estimate based on various factors
        """
        # Base confidence
        confidence = 0.9
        
        # Reduce confidence if no speech probability is high
        if "no_speech_prob" in result:
            confidence *= (1.0 - result["no_speech_prob"])
        
        # Reduce confidence for very short text
        text_length = len(result.get("text", "").strip())
        if text_length < 3:
            confidence *= 0.5
        
        return min(max(confidence, 0.0), 1.0)
    
    async def cleanup(self) -> None:
        """Clean up resources"""
        self.model = None
        self.set_state(VoiceState.IDLE)
        logger.info("Whisper STT handler cleaned up")