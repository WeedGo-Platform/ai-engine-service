"""
Offline Text-to-Speech handler for V5
Uses system TTS engines - completely offline
"""
import pyttsx3
import asyncio
import logging
import time
import io
import wave
import numpy as np
from typing import Dict, Any, Optional, List
from pathlib import Path

from .base_handler import TTSHandler, SynthesisResult, AudioConfig, VoiceState

logger = logging.getLogger(__name__)

class OfflineTTSHandler(TTSHandler):
    """Fully offline text-to-speech using system voices"""
    
    def __init__(self, config: Optional[AudioConfig] = None):
        """Initialize offline TTS handler"""
        super().__init__(config)
        self.engine = None
        self.available_voices = []
        self.current_voice_id = None
        
    async def initialize(self) -> bool:
        """Initialize TTS engine"""
        try:
            self.set_state(VoiceState.PROCESSING)
            
            # Initialize pyttsx3 engine in thread pool
            loop = asyncio.get_event_loop()
            self.engine = await loop.run_in_executor(
                None,
                self._init_engine_sync
            )
            
            if self.engine:
                # Get available voices
                self.available_voices = await self.get_available_voices()
                logger.info(f"✅ Offline TTS initialized with {len(self.available_voices)} voices")
                self.set_state(VoiceState.IDLE)
                return True
            else:
                self.set_state(VoiceState.ERROR)
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize TTS: {e}")
            self.set_state(VoiceState.ERROR)
            return False
    
    def _init_engine_sync(self):
        """Initialize engine synchronously"""
        try:
            engine = pyttsx3.init()
            
            # Configure default settings
            engine.setProperty('rate', 150)  # Speed
            engine.setProperty('volume', 0.9)  # Volume
            
            return engine
        except Exception as e:
            logger.error(f"Error initializing TTS engine: {e}")
            return None
    
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        language: Optional[str] = None,
        speed: float = 1.0,
        pitch: float = 0.0
    ) -> SynthesisResult:
        """Synthesize speech from text
        
        Args:
            text: Text to synthesize
            voice: Voice ID or name
            language: Language code (ignored - uses system default)
            speed: Speech rate multiplier (0.5-2.0)
            pitch: Pitch adjustment (not supported by all engines)
            
        Returns:
            SynthesisResult with audio data
        """
        start_time = time.time()
        
        try:
            self.set_state(VoiceState.PROCESSING)
            
            # Configure voice if specified
            if voice and voice != self.current_voice_id:
                await self._set_voice(voice)
            
            # Configure speed (rate)
            base_rate = 150
            adjusted_rate = int(base_rate * speed)
            self.engine.setProperty('rate', adjusted_rate)
            
            # Generate audio in thread pool
            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(
                None,
                self._synthesize_sync,
                text
            )
            
            # Calculate metrics
            duration_ms = (time.time() - start_time) * 1000
            self.update_metrics(duration_ms, success=True)
            
            self.set_state(VoiceState.IDLE)
            
            # Estimate audio duration (rough estimate)
            audio_duration_ms = len(text) * 50 * (1.0 / speed)  # ~50ms per character at normal speed
            
            return SynthesisResult(
                audio=audio_data,
                sample_rate=self.config.sample_rate,
                duration_ms=audio_duration_ms,
                format="wav"
            )
            
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            duration_ms = (time.time() - start_time) * 1000
            self.update_metrics(duration_ms, success=False)
            self.set_state(VoiceState.ERROR)
            
            # Return silence
            return SynthesisResult(
                audio=self._generate_silence(),
                sample_rate=self.config.sample_rate,
                duration_ms=0,
                format="wav"
            )
    
    def _synthesize_sync(self, text: str) -> bytes:
        """Synchronously synthesize speech"""
        # Save to temporary file then read back
        # (pyttsx3 doesn't have direct memory output)
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            # Save speech to file
            self.engine.save_to_file(text, output_path)
            self.engine.runAndWait()
            
            # Read the audio file
            with open(output_path, 'rb') as f:
                audio_data = f.read()
            
            return audio_data
            
        finally:
            # Clean up temp file
            Path(output_path).unlink(missing_ok=True)
    
    async def get_available_voices(self) -> List[Dict[str, str]]:
        """Get list of available system voices"""
        try:
            if not self.engine:
                return []
            
            # Get voices in thread pool
            loop = asyncio.get_event_loop()
            voices = await loop.run_in_executor(
                None,
                self._get_voices_sync
            )
            
            return voices
            
        except Exception as e:
            logger.error(f"Error getting voices: {e}")
            return []
    
    def _get_voices_sync(self) -> List[Dict[str, str]]:
        """Get voices synchronously"""
        voices = []
        
        for voice in self.engine.getProperty('voices'):
            voice_info = {
                "id": voice.id,
                "name": voice.name,
                "languages": getattr(voice, 'languages', ['en']),
                "gender": getattr(voice, 'gender', 'neutral'),
                "age": getattr(voice, 'age', 'adult')
            }
            voices.append(voice_info)
        
        return voices
    
    async def _set_voice(self, voice_id: str) -> None:
        """Set the active voice"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.engine.setProperty('voice', voice_id)
            )
            self.current_voice_id = voice_id
        except Exception as e:
            logger.error(f"Error setting voice: {e}")
    
    def _generate_silence(self, duration_ms: int = 1000) -> bytes:
        """Generate silent audio as WAV"""
        # Generate silence
        sample_rate = self.config.sample_rate
        num_samples = int(sample_rate * duration_ms / 1000)
        silence = np.zeros(num_samples, dtype=np.int16)
        
        # Create WAV file in memory
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(silence.tobytes())
        
        buffer.seek(0)
        return buffer.read()
    
    async def cleanup(self) -> None:
        """Clean up resources"""
        if self.engine:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda: self.engine.stop()
                )
            except:
                pass
            self.engine = None
        
        self.set_state(VoiceState.IDLE)
        logger.info("Offline TTS handler cleaned up")