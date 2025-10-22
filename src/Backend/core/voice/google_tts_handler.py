"""
Google Cloud Text-to-Speech Handler
High-quality cloud TTS with 100+ languages and voices
"""
import asyncio
import logging
import time
import os
import wave
import io
import numpy as np
from typing import Dict, Any, Optional, List
from pathlib import Path

from .base_handler import TTSHandler, SynthesisResult, AudioConfig, VoiceState

logger = logging.getLogger(__name__)


class GoogleTTSHandler(TTSHandler):
    """Google Cloud TTS handler (cloud-based, requires API key)"""

    def __init__(self, config: Optional[AudioConfig] = None, api_key: Optional[str] = None):
        """Initialize Google TTS handler

        Args:
            config: Audio configuration
            api_key: Google Cloud API key (or set GOOGLE_APPLICATION_CREDENTIALS env var)
        """
        if config is None:
            config = AudioConfig()

        # Google TTS outputs at 24kHz by default
        config.sample_rate = 24000
        config.channels = 1  # Mono output
        config.quality = "high"

        super().__init__(config)

        self.api_key = api_key
        self.client = None

        # Supported languages (100+ languages)
        self.supported_languages = [
            'en-US', 'en-GB', 'en-AU', 'en-IN',  # English variants
            'es-ES', 'es-US', 'es-MX',  # Spanish
            'fr-FR', 'fr-CA',  # French
            'de-DE',  # German
            'it-IT',  # Italian
            'pt-BR', 'pt-PT',  # Portuguese
            'pl-PL',  # Polish
            'tr-TR',  # Turkish
            'ru-RU',  # Russian
            'nl-NL',  # Dutch
            'cs-CZ',  # Czech
            'ar-XA',  # Arabic
            'zh-CN', 'zh-TW',  # Chinese
            'ja-JP',  # Japanese
            'ko-KR',  # Korean
            'hi-IN',  # Hindi
            'th-TH',  # Thai
            'vi-VN',  # Vietnamese
            'id-ID',  # Indonesian
            'fil-PH',  # Filipino
            'ms-MY',  # Malay
            'sw-KE',  # Swahili
            'hu-HU',  # Hungarian
            # ... and 70+ more languages
        ]

        # Popular voice mappings (language -> default voice)
        self.default_voices = {
            'en-US': 'en-US-Neural2-C',  # Female
            'en-GB': 'en-GB-Neural2-A',  # Female
            'es-ES': 'es-ES-Neural2-A',  # Female
            'fr-FR': 'fr-FR-Neural2-A',  # Female
            'de-DE': 'de-DE-Neural2-A',  # Female
            'it-IT': 'it-IT-Neural2-A',  # Female
            'pt-BR': 'pt-BR-Neural2-A',  # Female
            'ja-JP': 'ja-JP-Neural2-B',  # Female
            'ko-KR': 'ko-KR-Neural2-A',  # Female
            'zh-CN': 'cmn-CN-Standard-A',  # Female
        }

    async def initialize(self) -> bool:
        """Initialize Google Cloud TTS client"""
        try:
            self.set_state(VoiceState.PROCESSING)

            logger.info("Initializing Google Cloud Text-to-Speech...")

            # Check for API credentials
            credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
            if not credentials_path and not self.api_key:
                logger.warning(
                    "No Google Cloud credentials found. "
                    "Set GOOGLE_APPLICATION_CREDENTIALS environment variable or provide api_key"
                )
                self.set_state(VoiceState.ERROR)
                return False

            # Import Google Cloud TTS
            try:
                from google.cloud import texttospeech
            except ImportError:
                logger.error("google-cloud-texttospeech not installed. Run: pip install google-cloud-texttospeech")
                self.set_state(VoiceState.ERROR)
                return False

            # Initialize client in thread pool
            loop = asyncio.get_event_loop()
            self.client = await loop.run_in_executor(
                None,
                lambda: texttospeech.TextToSpeechClient()
            )

            logger.info(f"✅ Google Cloud TTS initialized")
            logger.info(f"   Supports 100+ languages and 500+ voices")
            logger.info(f"   Neural2 and WaveNet voices available")

            self.set_state(VoiceState.IDLE)
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Google TTS: {e}")
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
        """Synthesize speech using Google Cloud TTS

        Args:
            text: Text to synthesize
            voice: Voice name (e.g., 'en-US-Neural2-C') or None for default
            language: Language code (e.g., 'en-US', 'es-ES')
            speed: Speech rate (0.25-4.0, default 1.0)
            pitch: Pitch adjustment in semitones (-20.0 to 20.0)
            speaker_wav: Not supported (Google TTS doesn't do voice cloning)

        Returns:
            High-quality cloud-generated audio
        """
        start_time = time.time()

        try:
            self.set_state(VoiceState.PROCESSING)

            if not self.client:
                raise RuntimeError("Google TTS client not initialized")

            # Determine language
            lang = language or 'en-US'

            # Map simple language codes to full codes
            lang_map = {
                'en': 'en-US',
                'es': 'es-ES',
                'fr': 'fr-FR',
                'de': 'de-DE',
                'it': 'it-IT',
                'pt': 'pt-BR',
                'ja': 'ja-JP',
                'ko': 'ko-KR',
                'zh': 'zh-CN',
                'zh-cn': 'zh-CN',
                'ar': 'ar-XA'
            }

            if lang in lang_map:
                lang = lang_map[lang]

            # Determine voice
            voice_name = voice or self.default_voices.get(lang, 'en-US-Neural2-C')

            # Clamp speed and pitch to valid ranges
            speed = max(0.25, min(4.0, speed))
            pitch = max(-20.0, min(20.0, pitch))

            logger.info(f"Generating speech with Google TTS:")
            logger.info(f"  Voice: {voice_name}, Language: {lang}")
            logger.info(f"  Speed: {speed}x, Pitch: {pitch:+.1f} semitones")

            # Generate audio
            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(
                None,
                self._synthesize_with_google,
                text,
                voice_name,
                lang,
                speed,
                pitch
            )

            # Calculate metrics
            duration_ms = (time.time() - start_time) * 1000
            self.update_metrics(duration_ms, success=True)

            self.set_state(VoiceState.IDLE)

            # Estimate audio duration
            audio_duration_ms = len(text) * 60 / speed

            return SynthesisResult(
                audio=audio_data,
                sample_rate=24000,
                duration_ms=audio_duration_ms,
                format="wav",
                provider="google_cloud"
            )

        except Exception as e:
            logger.error(f"Google TTS synthesis failed: {e}")
            duration_ms = (time.time() - start_time) * 1000
            self.update_metrics(duration_ms, success=False)
            self.set_state(VoiceState.ERROR)

            # Return silence on error
            return SynthesisResult(
                audio=self._generate_silence(),
                sample_rate=24000,
                duration_ms=0,
                format="wav",
                provider="google_cloud"
            )

    def _synthesize_with_google(
        self,
        text: str,
        voice_name: str,
        language_code: str,
        speed: float,
        pitch: float
    ) -> bytes:
        """Synthesize using Google Cloud TTS

        Args:
            text: Text to synthesize
            voice_name: Google voice name
            language_code: BCP-47 language code
            speed: Speaking rate
            pitch: Pitch adjustment

        Returns:
            WAV audio bytes
        """
        from google.cloud import texttospeech

        # Set the text input
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Build the voice request
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_name
        )

        # Select audio config
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            sample_rate_hertz=24000,
            speaking_rate=speed,
            pitch=pitch
        )

        # Perform the text-to-speech request
        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        # The response's audio_content is binary
        audio_content = response.audio_content

        # Convert raw PCM to WAV
        audio_data = self._raw_pcm_to_wav(audio_content, sample_rate=24000)

        # Convert to stereo
        audio_data = self._mono_to_stereo(audio_data)

        return audio_data

    def _raw_pcm_to_wav(self, pcm_data: bytes, sample_rate: int = 24000) -> bytes:
        """Convert raw PCM data to WAV format

        Args:
            pcm_data: Raw PCM audio bytes
            sample_rate: Sample rate in Hz

        Returns:
            WAV audio bytes
        """
        # Convert bytes to numpy array
        audio_array = np.frombuffer(pcm_data, dtype=np.int16)

        # Create WAV file in memory
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_array.tobytes())

        buffer.seek(0)
        return buffer.read()

    def _mono_to_stereo(self, audio_data: bytes) -> bytes:
        """Convert mono audio to stereo

        Args:
            audio_data: Mono WAV data

        Returns:
            Stereo WAV data
        """
        try:
            with io.BytesIO(audio_data) as input_buffer:
                with wave.open(input_buffer, 'rb') as wav_in:
                    params = wav_in.getparams()

                    # Already stereo
                    if params.nchannels == 2:
                        return audio_data

                    frames = wav_in.readframes(params.nframes)
                    audio = np.frombuffer(frames, dtype=np.int16)

                    # Duplicate channel
                    audio = np.column_stack((audio, audio))

                    # Create output WAV
                    output_buffer = io.BytesIO()
                    with wave.open(output_buffer, 'wb') as wav_out:
                        wav_out.setnchannels(2)  # Stereo
                        wav_out.setsampwidth(2)  # 16-bit
                        wav_out.setframerate(params.framerate)
                        wav_out.writeframes(audio.tobytes())

                    output_buffer.seek(0)
                    return output_buffer.read()

        except Exception as e:
            logger.warning(f"Mono to stereo conversion failed: {e}")
            return audio_data

    async def get_available_voices(self) -> List[Dict[str, str]]:
        """Get list of available Google TTS voices

        Returns:
            List of voice metadata (limited to popular voices)
        """
        voices = []

        # Return default voices for supported languages
        for lang, voice_name in self.default_voices.items():
            voices.append({
                "id": voice_name,
                "name": f"Google {voice_name}",
                "language": lang,
                "type": "neural",
                "quality": "high",
                "provider": "google_cloud"
            })

        logger.info(f"Google TTS: {len(voices)} default voices available (500+ total)")

        return voices

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
            # Close client
            if self.client:
                self.client = None

            self.set_state(VoiceState.IDLE)
            logger.info("Google TTS handler cleaned up")

        except Exception as e:
            logger.error(f"Cleanup error: {e}")
