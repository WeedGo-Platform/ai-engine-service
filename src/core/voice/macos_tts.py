"""
High-quality Text-to-Speech handler for macOS
Uses native macOS 'say' command for superior audio quality
"""
import asyncio
import logging
import time
import io
import wave
import numpy as np
import subprocess
import tempfile
from typing import Dict, Any, Optional, List
from pathlib import Path
import platform

from .base_handler import TTSHandler, SynthesisResult, AudioConfig, VoiceState

logger = logging.getLogger(__name__)

class MacOSTTSHandler(TTSHandler):
    """High-quality TTS using macOS native voices"""
    
    def __init__(self, config: Optional[AudioConfig] = None):
        """Initialize macOS TTS handler"""
        # Override config with high-quality settings
        if config is None:
            config = AudioConfig()
        
        # Force high-quality audio settings
        config.sample_rate = 48000  # Professional audio quality
        config.quality = "high"
        config.bit_depth = 16  # 16-bit is standard for TTS
        config.channels = 2  # Stereo output
        
        super().__init__(config)
        self.available_voices = []
        self.current_voice_id = "Samantha"  # Default to high-quality voice
        self.default_rate = 200  # Normal speaking rate (words per minute)
        self.is_macos = platform.system() == 'Darwin'
        
    async def initialize(self) -> bool:
        """Initialize TTS handler"""
        try:
            self.set_state(VoiceState.PROCESSING)
            
            if not self.is_macos:
                logger.error("MacOS TTS handler requires macOS")
                self.set_state(VoiceState.ERROR)
                return False
            
            # Get available voices
            self.available_voices = await self.get_available_voices()
            
            if self.available_voices:
                # Select best quality voice by default
                premium_voices = ["Samantha", "Alex", "Karen", "Daniel", "Tessa", "Moira"]
                for voice_name in premium_voices:
                    if any(voice_name in v["name"] for v in self.available_voices):
                        self.current_voice_id = voice_name
                        break
                
                logger.info(f"✅ macOS TTS initialized with {len(self.available_voices)} voices")
                logger.info(f"Default voice: {self.current_voice_id}")
                self.set_state(VoiceState.IDLE)
                return True
            else:
                logger.error("No voices available")
                self.set_state(VoiceState.ERROR)
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize macOS TTS: {e}")
            self.set_state(VoiceState.ERROR)
            return False
    
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        language: Optional[str] = None,
        speed: float = 1.0,
        pitch: float = 0.0
    ) -> SynthesisResult:
        """Synthesize high-quality speech from text
        
        Args:
            text: Text to synthesize
            voice: Voice name or ID
            language: Language code (ignored - uses voice's language)
            speed: Speech rate multiplier (0.5-2.0)
            pitch: Pitch adjustment (not supported by macOS say)
            
        Returns:
            SynthesisResult with high-quality audio data
        """
        start_time = time.time()
        
        try:
            self.set_state(VoiceState.PROCESSING)
            
            # Use specified voice or current
            voice_name = voice or self.current_voice_id
            
            # Adjust rate (words per minute)
            # Normal rate is about 200 wpm for natural speech
            base_rate = 200
            adjusted_rate = int(base_rate * speed)
            adjusted_rate = max(150, min(300, adjusted_rate))  # Keep in natural range
            
            # Generate audio in thread pool
            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(
                None,
                self._synthesize_high_quality,
                text,
                voice_name,
                adjusted_rate
            )
            
            # Calculate metrics
            duration_ms = (time.time() - start_time) * 1000
            self.update_metrics(duration_ms, success=True)
            
            self.set_state(VoiceState.IDLE)
            
            # Estimate audio duration
            audio_duration_ms = len(text) * 60 * (1.0 / speed)
            
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
    
    def _synthesize_high_quality(self, text: str, voice: str, rate: int) -> bytes:
        """Synthesize speech with maximum quality"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            # Use macOS 'say' command with optimized settings for natural speech
            cmd = [
                'say',
                '-v', voice,
                '-r', str(rate),
                '--data-format=LEI16@48000',  # 16-bit PCM at 48kHz (standard high quality)
                '--file-format=WAVE',  # Direct WAV output
                '-o', output_path,
                text
            ]
            
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"Say command failed: {result.stderr}")
                raise RuntimeError(f"Say command failed: {result.stderr}")
            
            # For stereo output, we need to process the audio
            wav_path = output_path.replace('.aiff', '.wav')
            
            # Convert to stereo if needed using afconvert
            try:
                subprocess.run([
                    'afconvert',
                    '-f', 'WAVE',
                    '-d', 'LEI16@48000',  # 16-bit PCM at 48kHz
                    '-c', '2',  # Convert to stereo
                    output_path,
                    wav_path
                ], check=True, capture_output=True, timeout=10)
                
                # Read the stereo audio
                with open(wav_path, 'rb') as f:
                    audio_data = f.read()
                Path(wav_path).unlink(missing_ok=True)
            except:
                # Fallback to original if conversion fails
                with open(output_path, 'rb') as f:
                    audio_data = f.read()
            
            # Clean up
            Path(output_path).unlink(missing_ok=True)
            
            return audio_data
            
        except subprocess.TimeoutExpired:
            logger.error("TTS synthesis timed out")
            raise
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            raise
        finally:
            # Ensure cleanup
            Path(output_path).unlink(missing_ok=True)
    
    async def get_available_voices(self) -> List[Dict[str, str]]:
        """Get list of available macOS voices"""
        try:
            # Get voices using 'say -v ?'
            result = subprocess.run(
                ['say', '-v', '?'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            voices = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    # Parse voice info
                    parts = line.split('#')
                    if parts:
                        voice_info = parts[0].strip().split()
                        if voice_info:
                            voice_name = voice_info[0]
                            language = voice_info[1] if len(voice_info) > 1 else 'en_US'
                            
                            # Check if it's an enhanced voice
                            is_enhanced = '(Enhanced)' in line or '(Premium)' in line
                            
                            voices.append({
                                "id": voice_name,
                                "name": voice_name,
                                "language": language,
                                "quality": "premium" if is_enhanced else "standard",
                                "sample_text": parts[1].strip() if len(parts) > 1 else ""
                            })
            
            # Sort with premium voices first
            voices.sort(key=lambda x: (x["quality"] != "premium", x["name"]))
            
            return voices
            
        except Exception as e:
            logger.error(f"Error getting voices: {e}")
            return []
    
    async def set_voice(self, voice_id: str) -> bool:
        """Set the active voice"""
        try:
            # Check if voice exists
            if any(v["id"] == voice_id or v["name"] == voice_id for v in self.available_voices):
                self.current_voice_id = voice_id
                logger.info(f"Voice set to: {voice_id}")
                return True
            else:
                logger.error(f"Voice not found: {voice_id}")
                return False
        except Exception as e:
            logger.error(f"Error setting voice: {e}")
            return False
    
    def _generate_silence(self, duration_ms: int = 1000) -> bytes:
        """Generate high-quality stereo silent audio"""
        # Generate silence at 48kHz, 16-bit, stereo
        sample_rate = 48000
        num_samples = int(sample_rate * duration_ms / 1000)
        
        # Create stereo silence (2 channels)
        silence = np.zeros((num_samples, 2), dtype=np.int16)
        
        # Create WAV file in memory
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(2)  # Stereo
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(silence.tobytes())
        
        buffer.seek(0)
        return buffer.read()
    
    async def cleanup(self) -> None:
        """Clean up resources"""
        self.set_state(VoiceState.IDLE)
        logger.info("macOS TTS handler cleaned up")