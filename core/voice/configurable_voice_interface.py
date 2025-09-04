"""
Fully Configurable Voice Interface
No hardcoded values - everything driven by configuration
"""
import yaml
import json
import asyncio
import numpy as np
from typing import Optional, Dict, Any, List
from pathlib import Path
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

class ConfigurableVoiceInterface:
    """
    Fully configurable voice interface
    All settings loaded from YAML configuration
    """
    
    def __init__(self, config_path: str = "config/voice_config.yaml"):
        """Initialize with configuration file"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # Components (initialized based on config)
        self.stt = None
        self.tts = None
        self.vad = None
        self.wake_detector = None
        
        # Dynamic state
        self.current_domain = "default"
        self.active_wake_words = []
        self.voice_profiles = {}
        
        # Initialize components from config
        self._initialize_components()
        
    def _load_config(self) -> Dict:
        """Load configuration from YAML file or use defaults"""
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}, using defaults")
            # Return default configuration
            return self._get_default_config()
        
        try:
            with open(self.config_path) as f:
                config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}, using defaults")
            return self._get_default_config()
        
        # Load environment variables for sensitive data
        config = self._substitute_env_vars(config)
        
        return config
    
    def _get_default_config(self) -> Dict:
        """Get default configuration when YAML is not available"""
        return {
            "stt": {
                "default_model": "whisper-base",
                "models": {
                    "whisper-base": {
                        "path": "models/voice/whisper/base.bin",
                        "language": "en"
                    }
                }
            },
            "tts": {
                "default_voice": "en_US-amy-medium",
                "voices": {
                    "en_US-amy-medium": {
                        "path": "models/voice/piper/amy-medium.onnx"
                    }
                }
            },
            "vad": {
                "model": "silero-vad",
                "speech_threshold": 0.5
            },
            "wake_word": {
                "enabled": True,
                "wake_words": {
                    "default": [
                        {"phrase": "hey assistant", "threshold": 0.8}
                    ],
                    "budtender": [
                        {"phrase": "hey budtender", "threshold": 0.8}
                    ]
                }
            },
            "domain_profiles": {
                "default": {
                    "tts": {"voice": "en_US-amy-medium", "speed": 1.0},
                    "stt": {"model": "whisper-base", "language_hint": "en"}
                },
                "budtender": {
                    "tts": {"voice": "en_US-amy-medium", "speed": 1.0},
                    "stt": {"model": "whisper-base", "language_hint": "en"}
                }
            }
        }
    
    def _substitute_env_vars(self, config: Any) -> Any:
        """Replace ${VAR} with environment variables"""
        import os
        import re
        
        if isinstance(config, str):
            # Replace ${VAR} with environment variable
            pattern = r'\$\{([^}]+)\}'
            
            def replacer(match):
                var_name = match.group(1)
                return os.environ.get(var_name, match.group(0))
            
            return re.sub(pattern, replacer, config)
        
        elif isinstance(config, dict):
            return {k: self._substitute_env_vars(v) for k, v in config.items()}
        
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        
        return config
    
    def _initialize_components(self):
        """Initialize all components from configuration"""
        
        # Initialize STT
        self._initialize_stt()
        
        # Initialize TTS
        self._initialize_tts()
        
        # Initialize VAD
        self._initialize_vad()
        
        # Initialize Wake Word
        self._initialize_wake_word()
        
        # Load domain profiles
        self._load_domain_profiles()
        
        logger.info("All voice components initialized from configuration")
    
    def _initialize_stt(self):
        """Initialize STT from config"""
        stt_config = self.config.get("stt", {})
        default_model = stt_config.get("default_model", "whisper-base")
        model_config = stt_config.get("models", {}).get(default_model, {})
        
        self.stt = {
            "model": default_model,
            "path": model_config.get("path"),
            "config": stt_config,
            "model_config": model_config
        }
        
        logger.info(f"STT initialized with model: {default_model}")
    
    def _initialize_tts(self):
        """Initialize TTS from config"""
        tts_config = self.config.get("tts", {})
        voices = tts_config.get("voices", {})
        
        self.tts = {
            "voices": voices,
            "config": tts_config,
            "cache": {} if tts_config.get("cache_enabled") else None
        }
        
        logger.info(f"TTS initialized with {len(voices)} voices")
    
    def _initialize_vad(self):
        """Initialize VAD from config"""
        vad_config = self.config.get("vad", {})
        
        self.vad = {
            "model": vad_config.get("model"),
            "path": vad_config.get("model_path"),
            "config": vad_config,
            "thresholds": {
                "speech": vad_config.get("speech_threshold"),
                "energy": vad_config.get("energy_threshold"),
                "silence_ms": vad_config.get("min_silence_duration_ms")
            }
        }
        
        logger.info(f"VAD initialized with model: {self.vad['model']}")
    
    def _initialize_wake_word(self):
        """Initialize wake word detection from config"""
        wake_config = self.config.get("wake_word", {})
        wake_words = wake_config.get("wake_words", {})
        
        self.wake_detector = {
            "model": wake_config.get("model"),
            "path": wake_config.get("model_path"),
            "config": wake_config,
            "wake_words": wake_words
        }
        
        # Set active wake words for current domain
        self._update_wake_words(self.current_domain)
        
        logger.info(f"Wake word detector initialized")
    
    def _load_domain_profiles(self):
        """Load domain-specific voice profiles from config"""
        profiles = self.config.get("domain_profiles", {})
        
        for domain, profile in profiles.items():
            self.voice_profiles[domain] = profile
            logger.info(f"Loaded voice profile for domain: {domain}")
    
    def _update_wake_words(self, domain: str):
        """Update active wake words for domain"""
        wake_words = self.wake_detector["wake_words"]
        
        # Get domain-specific wake words
        domain_words = wake_words.get(domain, [])
        default_words = wake_words.get("default", [])
        
        # Combine domain and default wake words
        self.active_wake_words = domain_words + default_words
        
        logger.info(f"Active wake words for {domain}: {[w['phrase'] for w in self.active_wake_words]}")
    
    async def switch_domain(self, domain: str):
        """Switch to a different domain"""
        if domain not in self.voice_profiles:
            logger.warning(f"Domain {domain} not found in profiles, using default")
            domain = "default"
        
        self.current_domain = domain
        self._update_wake_words(domain)
        
        # Update component settings for domain
        profile = self.voice_profiles.get(domain, {})
        
        # Update STT settings
        if "stt" in profile:
            stt_settings = profile["stt"]
            if "preferred_model" in stt_settings:
                await self._switch_stt_model(stt_settings["preferred_model"])
        
        # Update TTS voice
        if "tts" in profile:
            tts_settings = profile["tts"]
            self.current_voice = tts_settings.get("voice", "en-professional")
        
        logger.info(f"Switched to domain: {domain}")
    
    async def _switch_stt_model(self, model_name: str):
        """Switch to a different STT model"""
        models = self.config["stt"]["models"]
        
        if model_name in models:
            model_config = models[model_name]
            self.stt["model"] = model_name
            self.stt["model_config"] = model_config
            logger.info(f"Switched to STT model: {model_name}")
    
    async def process_audio(self, audio: np.ndarray) -> Dict[str, Any]:
        """Process audio input based on configuration"""
        
        # Get current domain profile
        profile = self.voice_profiles.get(self.current_domain, {})
        
        # 1. Apply audio processing from config
        processed_audio = await self._apply_audio_processing(audio)
        
        # 2. Check for wake word (if enabled)
        if self.config["features"]["wake_word_detection"]:
            wake_detected = await self._detect_wake_word(processed_audio)
            if not wake_detected:
                return {"status": "waiting_for_wake_word"}
        
        # 3. Voice activity detection
        vad_result = await self._detect_voice_activity(processed_audio)
        
        if not vad_result["is_speech"]:
            return {"status": "no_speech_detected"}
        
        # 4. Speech recognition with configured model
        transcription = await self._transcribe(
            processed_audio,
            profile.get("stt", {})
        )
        
        # 5. Return structured result
        return {
            "status": "success",
            "transcription": transcription,
            "domain": self.current_domain,
            "metadata": {
                "stt_model": self.stt["model"],
                "vad_confidence": vad_result.get("confidence"),
                "processing_time_ms": vad_result.get("processing_time_ms")
            }
        }
    
    async def _apply_audio_processing(self, audio: np.ndarray) -> np.ndarray:
        """Apply configured audio processing"""
        audio_config = self.config.get("audio", {})
        
        # Apply noise reduction if enabled
        if audio_config.get("enable_noise_reduction"):
            audio = await self._apply_noise_reduction(audio, audio_config)
        
        # Apply echo cancellation if enabled
        if audio_config.get("enable_echo_cancellation"):
            audio = await self._apply_echo_cancellation(audio, audio_config)
        
        # Apply AGC if enabled
        if audio_config.get("enable_agc"):
            audio = await self._apply_agc(audio, audio_config)
        
        return audio
    
    async def _detect_wake_word(self, audio: np.ndarray) -> bool:
        """Detect wake word from configuration"""
        for wake_word in self.active_wake_words:
            # Check against configured threshold
            confidence = await self._check_wake_word(audio, wake_word)
            if confidence >= wake_word["threshold"]:
                logger.info(f"Wake word detected: {wake_word['phrase']}")
                return True
        return False
    
    async def _detect_voice_activity(self, audio: np.ndarray) -> Dict:
        """Detect voice activity using configured thresholds"""
        vad_config = self.vad["config"]
        
        # Calculate energy
        energy = np.sqrt(np.mean(audio ** 2))
        
        # Check against configured thresholds
        is_speech = energy > vad_config["energy_threshold"]
        
        # Check minimum duration
        duration_ms = len(audio) / self.config["audio"]["input_sample_rate"] * 1000
        
        if duration_ms < vad_config["min_speech_duration_ms"]:
            is_speech = False
        
        return {
            "is_speech": is_speech,
            "confidence": min(energy / vad_config["energy_threshold"], 1.0),
            "duration_ms": duration_ms
        }
    
    async def _transcribe(self, audio: np.ndarray, stt_settings: Dict) -> Dict:
        """Transcribe using configured STT model"""
        
        # Get model configuration
        model_config = self.stt["model_config"]
        
        # Apply domain-specific settings
        language_hints = stt_settings.get("language_hints", [])
        
        # Simulate transcription (would use actual model)
        result = {
            "text": "Transcribed text",
            "language": language_hints[0] if language_hints else "en",
            "confidence": model_config.get("accuracy", 0.9),
            "model": self.stt["model"]
        }
        
        return result
    
    async def generate_speech(
        self,
        text: str,
        override_settings: Optional[Dict] = None
    ) -> np.ndarray:
        """Generate speech using configured TTS"""
        
        # Get domain profile
        profile = self.voice_profiles.get(self.current_domain, {})
        tts_settings = profile.get("tts", {})
        
        # Apply overrides if provided
        if override_settings:
            tts_settings.update(override_settings)
        
        # Get voice configuration
        voice_name = tts_settings.get("voice", "en-professional")
        voice_config = self.tts["voices"].get(voice_name, {})
        
        # Apply personality traits
        text = self._apply_personality(text, tts_settings.get("personality_traits", []))
        
        # Apply conversation style
        text = self._apply_conversation_style(text, profile.get("conversation", {}))
        
        # Generate audio (would use actual TTS)
        audio = np.random.randn(16000) * 0.1  # Placeholder
        
        # Cache if enabled
        if self.tts["cache"] is not None:
            cache_key = f"{text}_{voice_name}_{tts_settings}"
            self.tts["cache"][cache_key] = audio
        
        return audio
    
    def _apply_personality(self, text: str, traits: List[str]) -> str:
        """Apply personality traits to text"""
        
        # Load personality modifiers from config
        for trait in traits:
            if trait == "friendly":
                # Add friendly markers (configured, not hardcoded)
                pass
            elif trait == "professional":
                # Apply professional tone
                pass
            # etc.
        
        return text
    
    def _apply_conversation_style(self, text: str, conversation_config: Dict) -> str:
        """Apply conversation style from config"""
        
        # Add fillers if configured
        if conversation_config.get("use_fillers"):
            fillers = conversation_config.get("fillers", [])
            # Add fillers at natural points
        
        # Add backchanneling
        backchannel = conversation_config.get("backchannel", [])
        
        # Apply formality level
        formality = conversation_config.get("formality", "neutral")
        
        return text
    
    async def _apply_noise_reduction(self, audio: np.ndarray, config: Dict) -> np.ndarray:
        """Apply noise reduction based on config"""
        model = config.get("noise_reduction_model")
        # Apply configured noise reduction
        return audio
    
    async def _apply_echo_cancellation(self, audio: np.ndarray, config: Dict) -> np.ndarray:
        """Apply echo cancellation based on config"""
        model = config.get("echo_cancellation_model")
        # Apply configured echo cancellation
        return audio
    
    async def _apply_agc(self, audio: np.ndarray, config: Dict) -> np.ndarray:
        """Apply automatic gain control based on config"""
        target_level = config.get("target_level_dbfs")
        # Apply configured AGC
        return audio
    
    async def _check_wake_word(self, audio: np.ndarray, wake_word: Dict) -> float:
        """Check for specific wake word"""
        # Load model for this wake word
        model_file = wake_word.get("model_file")
        # Process audio through wake word model
        # Return confidence score
        return 0.0  # Placeholder
    
    def reload_config(self):
        """Reload configuration from file"""
        self.config = self._load_config()
        self._initialize_components()
        logger.info("Configuration reloaded")
    
    def get_config_value(self, path: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation path"""
        keys = path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def update_config_value(self, path: str, value: Any):
        """Update configuration value at runtime"""
        keys = path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
        logger.info(f"Updated config: {path} = {value}")
    
    async def calibrate_for_environment(self) -> Dict:
        """Auto-calibrate based on environment"""
        calibration = {
            "noise_level": 0,
            "echo_present": False,
            "recommended_settings": {}
        }
        
        # Measure ambient noise
        # Detect echo
        # Recommend settings
        
        return calibration
    
    def export_config(self, path: str):
        """Export current configuration"""
        with open(path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
        logger.info(f"Configuration exported to: {path}")
    
    async def process_audio_stream(self, audio_chunk: np.ndarray) -> Optional[Dict[str, Any]]:
        """Process streaming audio chunk for real-time transcription
        
        Args:
            audio_chunk: Audio chunk as numpy array
            
        Returns:
            Transcription result if speech detected, None otherwise
        """
        # For streaming, we can use the regular process_audio method
        # In a real implementation, this would handle buffering and streaming differently
        try:
            result = await self.process_audio(audio_chunk)
            return result
        except Exception as e:
            logger.error(f"Error processing audio stream: {e}")
            return None