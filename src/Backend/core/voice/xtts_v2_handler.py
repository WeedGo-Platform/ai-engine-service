"""
XTTS v2 Voice Cloning Handler
Zero-shot voice cloning with multilingual support
"""
import asyncio
import logging
import time
import os
import tempfile
import wave
import io
import numpy as np
from typing import Dict, Any, Optional, List
from pathlib import Path

from .base_handler import TTSHandler, SynthesisResult, AudioConfig, VoiceState

logger = logging.getLogger(__name__)

class XTTSv2Handler(TTSHandler):
    """XTTS v2 zero-shot voice cloning TTS handler"""

    def __init__(self, config: Optional[AudioConfig] = None, device: str = "cpu"):
        """Initialize XTTS v2 handler

        Args:
            config: Audio configuration
            device: Device to run on ('cpu' or 'cuda')
        """
        if config is None:
            config = AudioConfig()

        # XTTS v2 outputs at 24kHz
        config.sample_rate = 24000
        config.channels = 1  # Mono output
        config.quality = "high"

        super().__init__(config)

        self.device = device
        self.tts = None
        self.model_name = "tts_models/multilingual/multi-dataset/xtts_v2"

        # Centralized model cache directory
        self.models_dir = Path(__file__).parent.parent.parent / "models" / "voice" / "xtts_v2"
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Supported languages (17 languages)
        self.supported_languages = [
            'en', 'es', 'fr', 'de', 'it', 'pt', 'pl', 'tr',
            'ru', 'nl', 'cs', 'ar', 'zh-cn', 'hu', 'ko', 'ja', 'hi'
        ]

        # Voice sample cache (personality_id -> voice_sample_path)
        self.voice_cache: Dict[str, str] = {}

    async def initialize(self) -> bool:
        """Initialize XTTS v2 model"""
        try:
            self.set_state(VoiceState.PROCESSING)

            logger.info("Initializing XTTS v2 voice cloning model...")
            logger.info(f"Device: {self.device}")
            logger.info(f"Model cache: {self.models_dir}")

            # Set license acceptance environment variable
            os.environ['COQUI_TOS_AGREED'] = '1'

            # Set custom TTS cache directory
            os.environ['COQUI_TTS_CACHE_PATH'] = str(self.models_dir)

            # Fix PyTorch 2.6+ weights_only=True compatibility
            try:
                import torch
                torch.serialization.add_safe_globals([getattr])
                logger.info("Added safe globals for PyTorch 2.6+ compatibility")
            except Exception as e:
                logger.warning(f"Could not add safe globals (PyTorch < 2.6?): {e}")

            # Import TTS library
            from TTS.api import TTS

            # Load model in thread pool to avoid blocking
            # Note: Don't pass model_path since COQUI_TTS_CACHE_PATH is set
            loop = asyncio.get_event_loop()
            self.tts = await loop.run_in_executor(
                None,
                lambda: TTS(self.model_name).to(self.device)
            )

            logger.info(f"✅ XTTS v2 loaded successfully on {self.device}")
            logger.info(f"   Supports {len(self.supported_languages)} languages")
            logger.info(f"   Zero-shot voice cloning enabled")

            self.set_state(VoiceState.IDLE)
            return True

        except Exception as e:
            logger.error(f"Failed to initialize XTTS v2: {e}")
            self.set_state(VoiceState.ERROR)
            return False

    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        language: Optional[str] = None,
        speed: float = 1.0,
        pitch: float = 0.0,
        speaker_wav: Optional[str] = None
    ) -> SynthesisResult:
        """Synthesize speech with voice cloning

        Args:
            text: Text to synthesize
            voice: Voice ID (personality ID to load from cache)
            language: Language code (e.g., 'en', 'es', 'fr')
            speed: Speech rate (0.5-2.0) - Note: XTTS v2 doesn't support speed natively
            pitch: Pitch adjustment (not supported)
            speaker_wav: Path to reference audio for voice cloning

        Returns:
            Audio data with cloned voice
        """
        start_time = time.time()

        try:
            self.set_state(VoiceState.PROCESSING)

            # Determine reference audio
            reference_audio = speaker_wav

            # If voice ID provided, check cache for pre-loaded voice sample
            if voice and not speaker_wav:
                if voice in self.voice_cache:
                    reference_audio = self.voice_cache[voice]
                    logger.info(f"Using cached voice sample for personality: {voice}")
                else:
                    logger.warning(f"Voice ID '{voice}' not found in cache")

            # XTTS v2 requires a speaker reference
            if not reference_audio:
                raise ValueError(
                    "XTTS v2 requires either 'voice' (cached personality) or 'speaker_wav' "
                    "for voice cloning. Neither was provided."
                )

            # Validate language
            lang = language or 'en'
            if lang not in self.supported_languages:
                logger.warning(f"Language '{lang}' not supported, using 'en'")
                lang = 'en'

            # Generate audio with XTTS v2
            logger.info(f"Generating speech: lang={lang}, ref_audio={Path(reference_audio).name}")

            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(
                None,
                self._synthesize_with_xtts,
                text,
                reference_audio,
                lang,
                speed
            )

            # Calculate metrics
            duration_ms = (time.time() - start_time) * 1000
            self.update_metrics(duration_ms, success=True)

            self.set_state(VoiceState.IDLE)

            # Estimate audio duration (characters * 60ms is rough estimate)
            audio_duration_ms = len(text) * 60 / speed

            return SynthesisResult(
                audio=audio_data,
                sample_rate=24000,  # XTTS v2 native sample rate
                duration_ms=audio_duration_ms,
                format="wav",
                provider="xtts_v2"
            )

        except Exception as e:
            logger.error(f"XTTS v2 synthesis failed: {e}")
            duration_ms = (time.time() - start_time) * 1000
            self.update_metrics(duration_ms, success=False)
            self.set_state(VoiceState.ERROR)

            # Return silence on error
            return SynthesisResult(
                audio=self._generate_silence(),
                sample_rate=24000,
                duration_ms=0,
                format="wav",
                provider="xtts_v2"
            )

    def _synthesize_with_xtts(
        self,
        text: str,
        speaker_wav: str,
        language: str,
        speed: float
    ) -> bytes:
        """Synthesize using XTTS v2 voice cloning

        Args:
            text: Text to synthesize
            speaker_wav: Path to reference audio
            language: Language code
            speed: Speed multiplier (applied via post-processing)

        Returns:
            WAV audio bytes
        """
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            output_path = tmp_file.name

        try:
            # Verify reference audio exists
            if not os.path.exists(speaker_wav):
                raise FileNotFoundError(f"Speaker reference audio not found: {speaker_wav}")

            # Generate with XTTS v2
            self.tts.tts_to_file(
                text=text,
                speaker_wav=speaker_wav,
                language=language,
                file_path=output_path
            )

            # Read the generated audio
            with open(output_path, 'rb') as f:
                audio_data = f.read()

            # Apply speed adjustment if needed (via resampling)
            if speed != 1.0:
                audio_data = self._apply_speed_change(audio_data, speed)

            # Convert to stereo for consistency with Piper
            audio_data = self._mono_to_stereo(audio_data)

            return audio_data

        finally:
            Path(output_path).unlink(missing_ok=True)

    def _apply_speed_change(self, audio_data: bytes, speed: float) -> bytes:
        """Apply speed change by resampling

        Args:
            audio_data: Original audio WAV data
            speed: Speed multiplier (>1.0 = faster, <1.0 = slower)

        Returns:
            Speed-adjusted WAV data
        """
        try:
            with io.BytesIO(audio_data) as input_buffer:
                with wave.open(input_buffer, 'rb') as wav_in:
                    params = wav_in.getparams()
                    frames = wav_in.readframes(params.nframes)

                    # Convert to numpy array
                    if params.sampwidth == 2:
                        audio = np.frombuffer(frames, dtype=np.int16)
                    else:
                        audio = np.frombuffer(frames, dtype=np.int8)

                    # Resample to achieve speed change
                    new_length = int(len(audio) / speed)
                    old_indices = np.arange(len(audio))
                    new_indices = np.linspace(0, len(audio) - 1, new_length)
                    audio = np.interp(new_indices, old_indices, audio).astype(np.int16)

                    # Create output WAV
                    output_buffer = io.BytesIO()
                    with wave.open(output_buffer, 'wb') as wav_out:
                        wav_out.setnchannels(params.nchannels)
                        wav_out.setsampwidth(params.sampwidth)
                        wav_out.setframerate(params.framerate)
                        wav_out.writeframes(audio.tobytes())

                    output_buffer.seek(0)
                    return output_buffer.read()

        except Exception as e:
            logger.warning(f"Speed adjustment failed: {e}, using original audio")
            return audio_data

    def _mono_to_stereo(self, audio_data: bytes) -> bytes:
        """Convert mono audio to stereo for consistency

        Args:
            audio_data: Mono WAV data

        Returns:
            Stereo WAV data
        """
        try:
            with io.BytesIO(audio_data) as input_buffer:
                with wave.open(input_buffer, 'rb') as wav_in:
                    params = wav_in.getparams()

                    # Already stereo, return as-is
                    if params.nchannels == 2:
                        return audio_data

                    frames = wav_in.readframes(params.nframes)

                    # Convert to numpy array
                    if params.sampwidth == 2:
                        audio = np.frombuffer(frames, dtype=np.int16)
                    else:
                        audio = np.frombuffer(frames, dtype=np.int8)

                    # Duplicate mono channel to create stereo
                    audio = np.column_stack((audio, audio))

                    # Create output WAV
                    output_buffer = io.BytesIO()
                    with wave.open(output_buffer, 'wb') as wav_out:
                        wav_out.setnchannels(2)  # Stereo
                        wav_out.setsampwidth(params.sampwidth)
                        wav_out.setframerate(params.framerate)
                        wav_out.writeframes(audio.tobytes())

                    output_buffer.seek(0)
                    return output_buffer.read()

        except Exception as e:
            logger.warning(f"Mono to stereo conversion failed: {e}")
            return audio_data

    async def get_available_voices(self) -> List[Dict[str, str]]:
        """Get list of available cached voice personalities

        Returns:
            List of voice metadata dictionaries
        """
        voices = []

        # Return cached personalities
        for personality_id, voice_path in self.voice_cache.items():
            voices.append({
                "id": personality_id,
                "name": f"Custom Voice: {personality_id}",
                "type": "cloned",
                "languages": ", ".join(self.supported_languages),
                "sample_path": voice_path
            })

        # Add note about voice cloning capability
        if not voices:
            logger.info("No cached voices. XTTS v2 supports zero-shot voice cloning from any audio sample.")

        return voices

    async def load_voice_sample(self, personality_id: str, audio_path: str) -> bool:
        """Load and cache a voice sample for a personality

        Args:
            personality_id: Unique ID for the personality
            audio_path: Path to voice sample audio file

        Returns:
            True if loaded successfully
        """
        try:
            if not os.path.exists(audio_path):
                logger.error(f"Voice sample not found: {audio_path}")
                return False

            # Validate audio file (basic check)
            # TODO: Add quality validation (duration, sample rate, noise level)

            self.voice_cache[personality_id] = audio_path
            logger.info(f"✅ Loaded voice sample for personality '{personality_id}'")
            logger.info(f"   Sample: {Path(audio_path).name}")

            return True

        except Exception as e:
            logger.error(f"Failed to load voice sample for '{personality_id}': {e}")
            return False

    async def remove_voice_sample(self, personality_id: str) -> bool:
        """Remove a cached voice sample

        Args:
            personality_id: Personality ID to remove

        Returns:
            True if removed successfully
        """
        if personality_id in self.voice_cache:
            del self.voice_cache[personality_id]
            logger.info(f"Removed voice sample for personality '{personality_id}'")
            return True
        return False

    def _generate_silence(self, duration_ms: int = 1000) -> bytes:
        """Generate silence WAV

        Args:
            duration_ms: Duration in milliseconds

        Returns:
            WAV audio bytes
        """
        sample_rate = 24000
        num_samples = int(sample_rate * duration_ms / 1000)

        # Stereo silence
        silence = np.zeros((num_samples, 2), dtype=np.int16)

        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(2)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(silence.tobytes())

        buffer.seek(0)
        return buffer.read()

    async def cleanup(self) -> None:
        """Clean up resources"""
        try:
            # Clear voice cache
            self.voice_cache.clear()

            # Unload model
            if self.tts:
                del self.tts
                self.tts = None

            self.set_state(VoiceState.IDLE)
            logger.info("XTTS v2 handler cleaned up")

        except Exception as e:
            logger.error(f"Cleanup error: {e}")
