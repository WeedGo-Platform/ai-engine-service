"""
High-quality Text-to-Speech handler using Piper neural voices
Provides natural, human-like speech synthesis
"""
import asyncio
import logging
import time
import json
import subprocess
import tempfile
import wave
import numpy as np
from typing import Dict, Any, Optional, List
from pathlib import Path
import io

from .base_handler import TTSHandler, SynthesisResult, AudioConfig, VoiceState

logger = logging.getLogger(__name__)

class PiperTTSHandler(TTSHandler):
    """High-quality neural TTS using Piper models"""
    
    def __init__(self, config: Optional[AudioConfig] = None):
        """Initialize Piper TTS handler"""
        if config is None:
            config = AudioConfig()
        
        # Force high-quality settings for Piper
        config.sample_rate = 22050  # Piper's native sample rate
        config.channels = 1  # Piper outputs mono, we'll convert to stereo
        config.quality = "high"
        
        super().__init__(config)
        
        # Piper model paths
        self.models_dir = Path("/Users/charrcy/projects/WeedGo/microservices/ai-engine-service/src/models/voice/piper")
        self.available_voices = {
            # American English voices
            "amy": {
                "id": "amy",
                "name": "Amy (US Female)",
                "model": self.models_dir / "en_US-amy-medium.onnx",
                "config": self.models_dir / "en_US-amy-medium.onnx.json",
                "gender": "female",
                "language": "en-US",
                "quality": "neural"
            },
            "ryan": {
                "id": "ryan", 
                "name": "Ryan (US Male)",
                "model": self.models_dir / "en_US-ryan-medium.onnx",
                "config": self.models_dir / "en_US-ryan-medium.onnx.json",
                "gender": "male",
                "language": "en-US",
                "quality": "neural"
            },
            "kristin": {
                "id": "kristin",
                "name": "Kristin (US Female)",
                "model": self.models_dir / "en_US-kristin-medium.onnx",
                "config": self.models_dir / "en_US-kristin-medium.onnx.json",
                "gender": "female",
                "language": "en-US",
                "quality": "neural"
            },
            "joe": {
                "id": "joe",
                "name": "Joe (US Male)",
                "model": self.models_dir / "en_US-joe-medium.onnx",
                "config": self.models_dir / "en_US-joe-medium.onnx.json",
                "gender": "male",
                "language": "en-US",
                "quality": "neural"
            },
            # British English voices
            "alba": {
                "id": "alba",
                "name": "Alba (UK Female)",
                "model": self.models_dir / "en_GB-alba-medium.onnx",
                "config": self.models_dir / "en_GB-alba-medium.onnx.json",
                "gender": "female",
                "language": "en-GB",
                "quality": "neural"
            },
            "alan": {
                "id": "alan",
                "name": "Alan (UK Male)",
                "model": self.models_dir / "en_GB-alan-medium.onnx",
                "config": self.models_dir / "en_GB-alan-medium.onnx.json",
                "gender": "male",
                "language": "en-GB",
                "quality": "neural"
            },
            # French voices
            "siwis": {
                "id": "siwis",
                "name": "Siwis (French Female)",
                "model": self.models_dir / "fr_FR-siwis-medium.onnx",
                "config": self.models_dir / "fr_FR-siwis-medium.onnx.json",
                "gender": "female",
                "language": "fr-FR",
                "quality": "neural"
            },
            "gilles": {
                "id": "gilles",
                "name": "Gilles (French Male)",
                "model": self.models_dir / "fr_FR-gilles-low.onnx",
                "config": self.models_dir / "fr_FR-gilles-low.onnx.json",
                "gender": "male",
                "language": "fr-FR",
                "quality": "neural"
            },
            # Spanish voices
            "ald": {
                "id": "ald",
                "name": "Ald (Mexican Spanish Female)",
                "model": self.models_dir / "es_MX-ald-medium.onnx",
                "config": self.models_dir / "es_MX-ald-medium.onnx.json",
                "gender": "female",
                "language": "es-MX",
                "quality": "neural"
            },
            "davefx": {
                "id": "davefx",
                "name": "DaveFX (Spanish Male)",
                "model": self.models_dir / "es_ES-davefx-medium.onnx",
                "config": self.models_dir / "es_ES-davefx-medium.onnx.json",
                "gender": "male",
                "language": "es-ES",
                "quality": "neural"
            },
            # Portuguese voices
            "faber": {
                "id": "faber",
                "name": "Faber (Brazilian Portuguese Female)",
                "model": self.models_dir / "pt_BR-faber-medium.onnx",
                "config": self.models_dir / "pt_BR-faber-medium.onnx.json",
                "gender": "female",
                "language": "pt-BR",
                "quality": "neural"
            },
            "cadu": {
                "id": "cadu",
                "name": "Cadu (Brazilian Portuguese Male)",
                "model": self.models_dir / "pt_BR-cadu-medium.onnx",
                "config": self.models_dir / "pt_BR-cadu-medium.onnx.json",
                "gender": "male",
                "language": "pt-BR",
                "quality": "neural"
            },
            # Chinese voices
            "huayan": {
                "id": "huayan",
                "name": "Huayan (Chinese Female)",
                "model": self.models_dir / "zh_CN-huayan-medium.onnx",
                "config": self.models_dir / "zh_CN-huayan-medium.onnx.json",
                "gender": "female",
                "language": "zh-CN",
                "quality": "neural"
            },
            "huayan_male": {
                "id": "huayan_male",
                "name": "Huayan (Chinese Variant)",
                "model": self.models_dir / "zh_CN-huayan-x_low.onnx",
                "config": self.models_dir / "zh_CN-huayan-x_low.onnx.json",
                "gender": "male",
                "language": "zh-CN",
                "quality": "neural"
            }
        }
        
        self.current_voice_id = "amy"  # Default to Amy
        self.piper_binary = None
        
    async def initialize(self) -> bool:
        """Initialize Piper TTS handler"""
        try:
            self.set_state(VoiceState.PROCESSING)
            
            # Check if Piper is installed
            self.piper_binary = await self._find_piper_binary()
            if not self.piper_binary:
                # Try to install Piper
                logger.info("Piper not found, attempting to install...")
                if not await self._install_piper():
                    logger.error("Failed to install Piper TTS")
                    self.set_state(VoiceState.ERROR)
                    return False
            
            # Verify models exist
            for voice_id, voice_info in self.available_voices.items():
                if not voice_info["model"].exists():
                    logger.error(f"Model not found: {voice_info['model']}")
                    self.set_state(VoiceState.ERROR)
                    return False
                if not voice_info["config"].exists():
                    logger.error(f"Config not found: {voice_info['config']}")
                    self.set_state(VoiceState.ERROR)
                    return False
            
            logger.info(f"✅ Piper TTS initialized with {len(self.available_voices)} high-quality neural voices")
            self.set_state(VoiceState.IDLE)
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Piper TTS: {e}")
            self.set_state(VoiceState.ERROR)
            return False
    
    async def _find_piper_binary(self) -> Optional[str]:
        """Find Piper binary"""
        # Check common locations
        possible_paths = [
            "/Users/charrcy/projects/WeedGo/.venv/bin/piper",  # Virtual env
            "piper",  # In PATH
            "/usr/local/bin/piper",
            "/opt/homebrew/bin/piper",
            "./piper/piper",  # Local installation
            "../piper/piper"
        ]
        
        for path in possible_paths:
            try:
                # Test with a dummy command to see if it works
                result = subprocess.run([path, "--help"], capture_output=True, timeout=2)
                if result.returncode == 0 and (b"piper" in result.stdout or b"MODEL" in result.stdout):
                    logger.info(f"Found Piper at: {path}")
                    return path
            except:
                continue
        
        return None
    
    async def _install_piper(self) -> bool:
        """Install Piper TTS"""
        try:
            # Try pip installation
            logger.info("Installing Piper TTS via pip...")
            result = subprocess.run(
                ["pip", "install", "piper-tts"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                # Find the installed binary
                self.piper_binary = await self._find_piper_binary()
                return self.piper_binary is not None
            
            # Alternative: Download pre-built binary
            logger.info("Pip installation failed, trying direct download...")
            # This would download a pre-built binary for the platform
            # For now, we'll use a fallback method
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to install Piper: {e}")
            return False
    
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        language: Optional[str] = None,
        speed: float = 1.0,
        pitch: float = 0.0
    ) -> SynthesisResult:
        """Synthesize high-quality neural speech
        
        Args:
            text: Text to synthesize
            voice: Voice ID (amy or ryan)
            language: Language (ignored, uses voice's language)
            speed: Speech rate (0.5-2.0)
            pitch: Pitch adjustment (not supported by Piper directly)
            
        Returns:
            High-quality audio data
        """
        start_time = time.time()
        
        try:
            self.set_state(VoiceState.PROCESSING)
            
            # Select voice
            voice_id = voice or self.current_voice_id
            if voice_id not in self.available_voices:
                voice_id = "amy"  # Default
            
            voice_info = self.available_voices[voice_id]
            
            # If Piper binary not available, return error
            if not self.piper_binary:
                logger.error("Piper binary not available - cannot synthesize speech")
                raise RuntimeError("Piper TTS not installed. Please install with: pip install piper-tts")
            
            # Generate audio with Piper
            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(
                None,
                self._synthesize_with_piper,
                text,
                voice_info,
                speed
            )
            
            # Calculate metrics
            duration_ms = (time.time() - start_time) * 1000
            self.update_metrics(duration_ms, success=True)
            
            self.set_state(VoiceState.IDLE)
            
            # Estimate duration
            audio_duration_ms = len(text) * 60 / speed
            
            return SynthesisResult(
                audio=audio_data,
                sample_rate=48000,  # We upsample to 48kHz
                duration_ms=audio_duration_ms,
                format="wav"
            )
            
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            duration_ms = (time.time() - start_time) * 1000
            self.update_metrics(duration_ms, success=False)
            self.set_state(VoiceState.ERROR)
            
            return SynthesisResult(
                audio=self._generate_silence(),
                sample_rate=48000,
                duration_ms=0,
                format="wav"
            )
    
    def _synthesize_with_piper(self, text: str, voice_info: Dict, speed: float) -> bytes:
        """Synthesize using Piper with conversational parameters"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            # Preprocess text for more natural speech
            # Add subtle pauses and emphasis markers
            text = self._preprocess_for_natural_speech(text)
            
            # Piper command with enhanced parameters
            cmd = [
                self.piper_binary,
                "--model", str(voice_info["model"]),
                "--config", str(voice_info["config"]),
                "--output_file", output_path,
                # Add variability for more natural speech
                "--noise_scale", "0.667",  # Add slight variability (default is 0.667)
                "--noise_w", "0.8",  # Control prosody variation
                "--sentence_silence", "0.2"  # Natural pause between sentences
            ]
            
            # Adjust speed for more natural pacing
            if speed != 1.0:
                # Piper uses length_scale for speed (inverse relationship)
                # Slightly slower for more natural speech
                length_scale = (1.0 / speed) * 1.1  # Add 10% more time for naturalness
                cmd.extend(["--length_scale", str(length_scale)])
            else:
                # Default to slightly slower for conversational tone
                cmd.extend(["--length_scale", "1.1"])
            
            # Run Piper
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=text, timeout=30)
            
            if process.returncode != 0:
                logger.error(f"Piper failed: {stderr}")
                raise RuntimeError(f"Piper synthesis failed: {stderr}")
            
            # Read the generated audio
            with open(output_path, 'rb') as f:
                audio_data = f.read()
            
            # Upsample to 48kHz stereo for better quality
            audio_data = self._upsample_to_48khz_stereo(audio_data)
            
            # Apply audio enhancements for more natural sound
            audio_data = self._enhance_audio_quality(audio_data)
            
            return audio_data
            
        finally:
            Path(output_path).unlink(missing_ok=True)
    
    def _preprocess_for_natural_speech(self, text: str) -> str:
        """Preprocess text to make speech more natural and conversational"""
        import re
        
        # Remove emojis and emoticons - don't read them out loud
        # Remove unicode emojis
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002500-\U00002BEF"  # chinese char
            u"\U00002702-\U000027B0"
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            u"\U0001f926-\U0001f937"
            u"\U00010000-\U0010ffff"
            u"\u2640-\u2642"
            u"\u2600-\u2B55"
            u"\u200d"
            u"\u23cf"
            u"\u23e9"
            u"\u231a"
            u"\ufe0f"  # dingbats
            u"\u3030"
            "]+", flags=re.UNICODE)
        text = emoji_pattern.sub('', text)
        
        # Remove text emoticons like :), :D, :(, :P, etc.
        text = re.sub(r':\)|:\(|:D|:P|:\||:/|:\\|:o|:O|;\)|;D|=\)|=D|=\(|\^_\^|\*_\*|o_O|O_o|-_-|>_<|<3', '', text)
        
        # Remove other emoji-like patterns (e.g., :smile:, :heart:)
        text = re.sub(r':[a-zA-Z_]+:', '', text)
        
        # Clean up any multiple spaces left after emoji removal
        text = re.sub(r'\s+', ' ', text)
        
        # Add subtle pauses after punctuation for natural rhythm
        text = re.sub(r'([.!?])\s+', r'\1 ... ', text)
        text = re.sub(r'([,;:])\s+', r'\1 .. ', text)
        
        # Add emphasis to question words for natural intonation
        question_words = ['what', 'when', 'where', 'why', 'how', 'who', 'which']
        for word in question_words:
            # Case insensitive replacement at word boundaries
            pattern = r'\b' + word + r'\b'
            text = re.sub(pattern, word.upper(), text, flags=re.IGNORECASE)
        
        # Add slight pauses around "um", "uh", "well" for conversational feel
        filler_words = ['um', 'uh', 'well', 'you know', 'I mean']
        for filler in filler_words:
            pattern = r'\b' + filler + r'\b'
            text = re.sub(pattern, f'.. {filler} ..', text, flags=re.IGNORECASE)
        
        # Handle contractions for more natural speech
        contractions = {
            "don't": "don't",
            "won't": "won't", 
            "can't": "can't",
            "I'm": "I'm",
            "you're": "you're",
            "we're": "we're",
            "they're": "they're",
            "it's": "it's",
            "that's": "that's",
            "what's": "what's",
            "let's": "let's"
        }
        
        for long_form, short_form in contractions.items():
            text = re.sub(r'\b' + long_form.replace("'", r"\'") + r'\b', 
                         short_form, text, flags=re.IGNORECASE)
        
        # Add emphasis to exclamations
        text = re.sub(r'!', '!!', text)
        
        # Handle parenthetical statements with pauses
        text = re.sub(r'\(', ' .. (', text)
        text = re.sub(r'\)', ') .. ', text)
        
        # Ensure proper spacing
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    # Removed espeak fallback - only use Piper for production
    
    def _enhance_audio_quality(self, audio_data: bytes) -> bytes:
        """Apply audio enhancements for more natural, conversational sound"""
        try:
            # Read the WAV data
            with io.BytesIO(audio_data) as input_buffer:
                with wave.open(input_buffer, 'rb') as wav_in:
                    params = wav_in.getparams()
                    frames = wav_in.readframes(params.nframes)
                    
                    # Convert to numpy array
                    if params.sampwidth == 2:
                        audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32)
                    else:
                        audio = np.frombuffer(frames, dtype=np.int8).astype(np.float32)
                    
                    # Reshape for stereo if needed
                    if params.nchannels == 2:
                        audio = audio.reshape(-1, 2)
                    
                    # Normalize to -1 to 1 range for processing
                    max_val = np.abs(audio).max()
                    if max_val > 0:
                        audio = audio / max_val
                    
                    # 1. Apply subtle compression for more consistent volume
                    threshold = 0.6
                    ratio = 3.0
                    above_threshold = np.abs(audio) > threshold
                    if audio.ndim == 2:
                        for ch in range(2):
                            channel = audio[:, ch]
                            compressed = np.where(
                                above_threshold[:, ch],
                                np.sign(channel) * (threshold + (np.abs(channel) - threshold) / ratio),
                                channel
                            )
                            audio[:, ch] = compressed
                    else:
                        audio = np.where(
                            above_threshold,
                            np.sign(audio) * (threshold + (np.abs(audio) - threshold) / ratio),
                            audio
                        )
                    
                    # 2. Add subtle warmth with harmonic enhancement
                    # Create a gentle saturation effect
                    warmth_amount = 0.15
                    warmed = np.tanh(audio * (1 + warmth_amount)) / (1 + warmth_amount * 0.5)
                    audio = audio * 0.7 + warmed * 0.3
                    
                    # 3. Apply gentle EQ for presence
                    # Simple high-shelf boost for clarity (crude approximation)
                    if len(audio) > 100:
                        # Very simple high-frequency emphasis
                        diff = np.diff(audio, axis=0 if audio.ndim == 2 else None)
                        diff_padded = np.pad(diff, ((0, 1), (0, 0)) if audio.ndim == 2 else (0, 1), 'constant')
                        audio = audio + diff_padded * 0.05  # Subtle high-frequency boost
                    
                    # 4. Add micro-dynamics for liveliness
                    # Random subtle volume variations
                    if len(audio) > 1000:
                        # Create smooth random variations
                        variation_length = len(audio) // 100
                        variations = np.random.normal(1.0, 0.02, variation_length)
                        # Smooth the variations
                        from scipy.ndimage import gaussian_filter1d
                        variations = gaussian_filter1d(variations, sigma=5)
                        # Interpolate to match audio length
                        variation_indices = np.linspace(0, len(variations) - 1, len(audio))
                        smooth_variations = np.interp(variation_indices, np.arange(len(variations)), variations)
                        
                        if audio.ndim == 2:
                            audio = audio * smooth_variations.reshape(-1, 1)
                        else:
                            audio = audio * smooth_variations
                    
                    # 5. Soft limiting to prevent clipping while maintaining dynamics
                    audio = np.tanh(audio * 0.9) * 0.95
                    
                    # Convert back to int16
                    audio = (audio * 32767).clip(-32768, 32767).astype(np.int16)
                    
                    # Create output WAV
                    output_buffer = io.BytesIO()
                    with wave.open(output_buffer, 'wb') as wav_out:
                        wav_out.setnchannels(params.nchannels)
                        wav_out.setsampwidth(2)  # 16-bit
                        wav_out.setframerate(params.framerate)
                        wav_out.writeframes(audio.tobytes())
                    
                    output_buffer.seek(0)
                    return output_buffer.read()
                    
        except Exception as e:
            logger.warning(f"Audio enhancement failed: {e}, using original audio")
            return audio_data  # Return original if enhancement fails
    
    def _upsample_to_48khz_stereo(self, audio_data: bytes) -> bytes:
        """Upsample audio to 48kHz stereo for better quality"""
        try:
            # Read the WAV data
            with io.BytesIO(audio_data) as input_buffer:
                with wave.open(input_buffer, 'rb') as wav_in:
                    params = wav_in.getparams()
                    frames = wav_in.readframes(params.nframes)
                    
                    # Convert to numpy array
                    if params.sampwidth == 2:
                        audio = np.frombuffer(frames, dtype=np.int16)
                    else:
                        audio = np.frombuffer(frames, dtype=np.int8)
                    
                    # Resample to 48kHz if needed
                    if params.framerate != 48000:
                        # Simple linear interpolation resampling
                        old_rate = params.framerate
                        new_rate = 48000
                        duration = len(audio) / old_rate
                        new_length = int(duration * new_rate)
                        
                        old_indices = np.arange(len(audio))
                        new_indices = np.linspace(0, len(audio) - 1, new_length)
                        audio = np.interp(new_indices, old_indices, audio).astype(np.int16)
                    
                    # Convert mono to stereo
                    if params.nchannels == 1:
                        audio = np.column_stack((audio, audio))
                    
                    # Create output WAV
                    output_buffer = io.BytesIO()
                    with wave.open(output_buffer, 'wb') as wav_out:
                        wav_out.setnchannels(2)  # Stereo
                        wav_out.setsampwidth(2)  # 16-bit
                        wav_out.setframerate(48000)  # 48kHz
                        wav_out.writeframes(audio.tobytes())
                    
                    output_buffer.seek(0)
                    return output_buffer.read()
                    
        except Exception as e:
            logger.error(f"Upsampling failed: {e}")
            return audio_data  # Return original if conversion fails
    
    async def get_available_voices(self) -> List[Dict[str, str]]:
        """Get list of available high-quality voices"""
        voices = []
        for voice_id, voice_info in self.available_voices.items():
            voices.append({
                "id": voice_id,
                "name": voice_info["name"],
                "gender": voice_info["gender"],
                "language": voice_info["language"],
                "quality": voice_info["quality"],
                "type": "neural"
            })
        return voices
    
    async def set_voice(self, voice_id: str) -> bool:
        """Set the active voice"""
        if voice_id in self.available_voices:
            self.current_voice_id = voice_id
            logger.info(f"Voice set to: {self.available_voices[voice_id]['name']}")
            return True
        return False
    
    def _generate_silence(self, duration_ms: int = 1000) -> bytes:
        """Generate high-quality silence"""
        sample_rate = 48000
        num_samples = int(sample_rate * duration_ms / 1000)
        
        # Stereo silence
        silence = np.zeros((num_samples, 2), dtype=np.int16)
        
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
        logger.info("Piper TTS handler cleaned up")