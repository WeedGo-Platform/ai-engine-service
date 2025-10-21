"""
StyleTTS2 Voice Cloning Handler
High-quality zero-shot voice cloning (human-level quality)
"""
import asyncio
import logging
import time
import os
import tempfile
import wave
import io
import warnings
import numpy as np
from typing import Dict, Any, Optional, List
from pathlib import Path

from .base_handler import TTSHandler, SynthesisResult, AudioConfig, VoiceState

logger = logging.getLogger(__name__)

# Suppress StyleTTS2 dependency warnings
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

class StyleTTS2Handler(TTSHandler):
    """StyleTTS2 zero-shot voice cloning TTS handler (human-level quality)"""

    def __init__(self, config: Optional[AudioConfig] = None):
        """Initialize StyleTTS2 handler

        Args:
            config: Audio configuration
        """
        if config is None:
            config = AudioConfig()

        # StyleTTS2 outputs at 24kHz
        config.sample_rate = 24000
        config.channels = 1  # Mono output
        config.quality = "high"

        super().__init__(config)

        self.tts = None

        # Centralized model cache directory
        self.models_dir = Path(__file__).parent.parent.parent / "models" / "voice" / "styletts2"
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Supported parameters (can be customized per personality)
        self.default_alpha = 0.3  # Timbre control (0-1, higher = more text-aligned)
        self.default_beta = 0.7  # Prosody control (0-1, higher = more text-aligned)
        self.default_diffusion_steps = 5  # Quality vs speed (1-10, higher = better quality)
        self.default_embedding_scale = 1.0  # Emotional intensity

        # Voice sample cache (personality_id -> voice_sample_path)
        self.voice_cache: Dict[str, str] = {}

    async def initialize(self) -> bool:
        """Initialize StyleTTS2 model"""
        try:
            self.set_state(VoiceState.PROCESSING)

            logger.info("Initializing StyleTTS2 voice cloning model...")
            logger.info("This will download models if not cached (~1.5GB)")
            logger.info(f"Model cache: {self.models_dir}")

            # Set custom cache directory for HuggingFace models (StyleTTS2 uses HF)
            os.environ['HF_HOME'] = str(self.models_dir)
            os.environ['TRANSFORMERS_CACHE'] = str(self.models_dir / "transformers")
            os.environ['HF_DATASETS_CACHE'] = str(self.models_dir / "datasets")

            # Fix PyTorch 2.6+ weights_only=True compatibility
            try:
                import torch
                # Add safe globals for PyTorch model loading
                torch.serialization.add_safe_globals([
                    getattr,
                    type,
                    dict,
                    list,
                    tuple,
                    set,
                    frozenset,
                ])
                logger.info("Added safe globals for PyTorch 2.6+ compatibility")
            except Exception as e:
                logger.warning(f"Could not add safe globals (PyTorch < 2.6?): {e}")

            # Import StyleTTS2 library
            from styletts2 import tts

            # Load model in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.tts = await loop.run_in_executor(
                None,
                lambda: tts.StyleTTS2()
            )

            logger.info(f"✅ StyleTTS2 loaded successfully")
            logger.info(f"   Quality: Human-level (state-of-the-art)")
            logger.info(f"   Zero-shot voice cloning enabled")
            logger.info(f"   Optimal sample length: 5-8 seconds")

            self.set_state(VoiceState.IDLE)
            return True

        except Exception as e:
            logger.error(f"Failed to initialize StyleTTS2: {e}")
            self.set_state(VoiceState.ERROR)
            return False

    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        language: Optional[str] = None,
        speed: float = 1.0,
        pitch: float = 0.0,
        speaker_wav: Optional[str] = None,
        alpha: Optional[float] = None,
        beta: Optional[float] = None,
        diffusion_steps: Optional[int] = None,
        embedding_scale: Optional[float] = None
    ) -> SynthesisResult:
        """Synthesize speech with high-quality voice cloning

        Args:
            text: Text to synthesize
            voice: Voice ID (personality ID to load from cache)
            language: Language code (currently English only, parameter for future)
            speed: Speech rate (0.5-2.0) - applied via post-processing
            pitch: Pitch adjustment (not supported)
            speaker_wav: Path to reference audio for voice cloning
            alpha: Timbre control (0-1, higher = more text-aligned)
            beta: Prosody control (0-1, higher = more text-aligned)
            diffusion_steps: Quality vs speed (1-10, higher = better)
            embedding_scale: Emotional intensity

        Returns:
            High-quality audio data with cloned voice
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

            # StyleTTS2 requires a speaker reference
            if not reference_audio:
                raise ValueError(
                    "StyleTTS2 requires either 'voice' (cached personality) or 'speaker_wav' "
                    "for voice cloning. Neither was provided."
                )

            # Use provided parameters or defaults
            alpha = alpha if alpha is not None else self.default_alpha
            beta = beta if beta is not None else self.default_beta
            diffusion_steps = diffusion_steps if diffusion_steps is not None else self.default_diffusion_steps
            embedding_scale = embedding_scale if embedding_scale is not None else self.default_embedding_scale

            # Generate audio with StyleTTS2
            logger.info(f"Generating speech with StyleTTS2:")
            logger.info(f"  Reference: {Path(reference_audio).name}")
            logger.info(f"  Alpha: {alpha}, Beta: {beta}")
            logger.info(f"  Diffusion steps: {diffusion_steps}, Embedding scale: {embedding_scale}")

            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(
                None,
                self._synthesize_with_styletts2,
                text,
                reference_audio,
                alpha,
                beta,
                diffusion_steps,
                embedding_scale,
                speed
            )

            # Calculate metrics
            duration_ms = (time.time() - start_time) * 1000
            self.update_metrics(duration_ms, success=True)

            self.set_state(VoiceState.IDLE)

            # Estimate audio duration
            audio_duration_ms = len(text) * 60 / speed

            return SynthesisResult(
                audio=audio_data,
                sample_rate=24000,  # StyleTTS2 native sample rate
                duration_ms=audio_duration_ms,
                format="wav"
            )

        except Exception as e:
            logger.error(f"StyleTTS2 synthesis failed: {e}")
            duration_ms = (time.time() - start_time) * 1000
            self.update_metrics(duration_ms, success=False)
            self.set_state(VoiceState.ERROR)

            # Return silence on error
            return SynthesisResult(
                audio=self._generate_silence(),
                sample_rate=24000,
                duration_ms=0,
                format="wav"
            )

    def _synthesize_with_styletts2(
        self,
        text: str,
        speaker_wav: str,
        alpha: float,
        beta: float,
        diffusion_steps: int,
        embedding_scale: float,
        speed: float
    ) -> bytes:
        """Synthesize using StyleTTS2 voice cloning

        Args:
            text: Text to synthesize
            speaker_wav: Path to reference audio
            alpha: Timbre control
            beta: Prosody control
            diffusion_steps: Quality vs speed
            embedding_scale: Emotional intensity
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

            # Generate with StyleTTS2
            # Returns numpy array
            audio_array = self.tts.inference(
                text=text,
                target_voice_path=speaker_wav,
                output_wav_file=output_path,
                output_sample_rate=24000,
                alpha=alpha,
                beta=beta,
                diffusion_steps=diffusion_steps,
                embedding_scale=embedding_scale
            )

            # Read the generated WAV file
            with open(output_path, 'rb') as f:
                audio_data = f.read()

            # Apply speed adjustment if needed
            if speed != 1.0:
                audio_data = self._apply_speed_change(audio_data, speed)

            # Convert to stereo for consistency
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
                "name": f"StyleTTS2: {personality_id}",
                "type": "cloned_high_quality",
                "quality": "human-level",
                "sample_path": voice_path
            })

        # Add note about voice cloning capability
        if not voices:
            logger.info("No cached voices. StyleTTS2 supports zero-shot voice cloning from 5-8s audio samples.")

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

            # Validate audio file
            # TODO: Add quality validation (duration 5-8s, sample rate, noise level)

            self.voice_cache[personality_id] = audio_path
            logger.info(f"✅ Loaded StyleTTS2 voice sample for personality '{personality_id}'")
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
            logger.info(f"Removed StyleTTS2 voice sample for personality '{personality_id}'")
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
            logger.info("StyleTTS2 handler cleaned up")

        except Exception as e:
            logger.error(f"Cleanup error: {e}")
