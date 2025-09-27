"""
Whisper-based Wake Word Detection Handler for V5
Lightweight keyword spotting using existing Whisper STT model
No additional dependencies required - uses existing infrastructure
"""
import asyncio
import logging
import time
import numpy as np
import re
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from collections import deque
import Levenshtein  # For fuzzy matching

from .wake_word_handler import (
    WakeWordHandler,
    WakeWordConfig,
    WakeWordDetection,
    WakeWordModel
)
from .whisper_stt import WhisperSTTHandler
from .base_handler import AudioConfig, VoiceState

logger = logging.getLogger(__name__)


class WhisperWakeWordHandler(WakeWordHandler):
    """
    Wake word detection using Whisper STT model
    Implements keyword spotting with fuzzy matching
    """

    # Default wake words and their variations
    DEFAULT_WAKE_WORDS = {
        WakeWordModel.HEY_WEEDGO: [
            "hey weedgo", "hey weed go", "hey weed-go", "hey widgo",
            "hey we go", "hey weego", "hey wheat go"
        ],
        WakeWordModel.WEEDGO: [
            "weedgo", "weed go", "weed-go", "widgo", "we go",
            "weego", "wheat go"
        ],
        WakeWordModel.HEY_BUD: [
            "hey bud", "hey buddy", "hey budd", "hey but", "hey bird"
        ]
    }

    def __init__(
        self,
        config: Optional[AudioConfig] = None,
        wake_config: Optional[WakeWordConfig] = None,
        whisper_model: str = "tiny"  # Use tiny model for speed
    ):
        """Initialize Whisper-based wake word handler

        Args:
            config: Audio configuration
            wake_config: Wake word configuration
            whisper_model: Whisper model size (tiny for low latency)
        """
        super().__init__(config, wake_config)

        # Use tiny Whisper model for minimal latency
        self.whisper_model = whisper_model
        self.stt_handler = WhisperSTTHandler(whisper_model, config)

        # Wake word patterns
        self.wake_words: Dict[str, List[str]] = {}
        self.custom_wake_words: Dict[str, List[str]] = {}

        # Circular buffer for recent transcriptions
        self.transcript_buffer = deque(maxlen=5)
        self.buffer_lock = asyncio.Lock()

        # Optimization: Process only short audio chunks
        self.chunk_duration_ms = 1500  # Process 1.5 second chunks
        self.overlap_ms = 500  # Overlap between chunks

        # Fuzzy matching threshold
        self.fuzzy_threshold = 0.75  # 75% similarity required

    async def initialize(self) -> bool:
        """Initialize the handler and load models"""
        try:
            self.set_state(VoiceState.PROCESSING)
            logger.info(f"Initializing Whisper wake word handler with {self.whisper_model} model")

            # Initialize Whisper STT handler
            if not await self.stt_handler.initialize():
                logger.error("Failed to initialize Whisper STT handler")
                self.set_state(VoiceState.ERROR)
                return False

            # Load default wake words
            self._load_default_wake_words()

            self.set_state(VoiceState.IDLE)
            logger.info("✅ Whisper wake word handler initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize wake word handler: {e}")
            self.set_state(VoiceState.ERROR)
            return False

    def _load_default_wake_words(self):
        """Load default wake words for enabled models"""
        self.wake_words.clear()

        for model in self.wake_config.models:
            if model in self.DEFAULT_WAKE_WORDS:
                model_words = self.DEFAULT_WAKE_WORDS[model]
                self.wake_words[model.value] = model_words
                logger.info(f"Loaded wake word model: {model.value} with {len(model_words)} variations")

    async def load_models(self, model_paths: Dict[str, Path]) -> bool:
        """Load custom wake word models from files

        Args:
            model_paths: Dictionary mapping model names to file paths

        Returns:
            Success status
        """
        try:
            for model_name, path in model_paths.items():
                if path.exists():
                    # Load custom wake words from file (one per line)
                    with open(path, 'r') as f:
                        words = [line.strip().lower() for line in f if line.strip()]

                    self.custom_wake_words[model_name] = words
                    logger.info(f"Loaded custom wake word model: {model_name} "
                              f"with {len(words)} variations from {path}")
                else:
                    logger.warning(f"Wake word model file not found: {path}")

            return True

        except Exception as e:
            logger.error(f"Failed to load wake word models: {e}")
            return False

    async def detect(
        self,
        audio: Union[np.ndarray, bytes],
        return_confidence: bool = False
    ) -> WakeWordDetection:
        """Detect wake word in audio using Whisper transcription

        Args:
            audio: Audio data to process
            return_confidence: Whether to return confidence scores

        Returns:
            Wake word detection result
        """
        start_time = time.time()

        try:
            # Convert bytes to numpy if needed
            if isinstance(audio, bytes):
                audio = np.frombuffer(audio, dtype=np.float32)

            # Ensure proper audio format
            audio = self._preprocess_audio(audio)

            # Quick energy check - skip if too quiet
            energy = np.sqrt(np.mean(audio ** 2))
            if energy < 0.01:  # Very quiet audio
                return WakeWordDetection(
                    detected=False,
                    wake_word=None,
                    confidence=0.0,
                    timestamp_ms=time.time() * 1000
                )

            # Transcribe audio
            transcription = await self.stt_handler.transcribe(audio, language="en")

            if not transcription.text:
                return WakeWordDetection(
                    detected=False,
                    wake_word=None,
                    confidence=0.0,
                    timestamp_ms=time.time() * 1000
                )

            # Check for wake words
            text_lower = transcription.text.lower().strip()

            # Update transcript buffer
            async with self.buffer_lock:
                self.transcript_buffer.append(text_lower)

                # Check recent transcripts for wake words
                recent_text = " ".join(self.transcript_buffer)
                detection = self._check_wake_words(recent_text)

                if not detection.detected:
                    # Also check just the current transcript
                    detection = self._check_wake_words(text_lower)

            # Add timing information
            detection.timestamp_ms = time.time() * 1000

            # Update metrics
            latency_ms = (time.time() - start_time) * 1000
            self.update_metrics(latency_ms, success=True)

            # Log detection
            if detection.detected:
                logger.debug(f"Wake word detected: '{detection.wake_word}' "
                           f"in text: '{text_lower}' (confidence: {detection.confidence:.2f})")

            return detection

        except Exception as e:
            logger.error(f"Wake word detection error: {e}")
            latency_ms = (time.time() - start_time) * 1000
            self.update_metrics(latency_ms, success=False)

            return WakeWordDetection(
                detected=False,
                wake_word=None,
                confidence=0.0,
                timestamp_ms=time.time() * 1000
            )

    def _check_wake_words(self, text: str) -> WakeWordDetection:
        """Check text for wake words with fuzzy matching

        Args:
            text: Text to check

        Returns:
            Detection result
        """
        best_match = None
        best_confidence = 0.0
        best_wake_word = None

        # Check default wake words
        for model_name, variations in self.wake_words.items():
            for variation in variations:
                # Exact match
                if variation in text:
                    return WakeWordDetection(
                        detected=True,
                        wake_word=model_name,
                        confidence=1.0,
                        timestamp_ms=time.time() * 1000,
                        metadata={"matched_text": variation}
                    )

                # Fuzzy matching for close matches
                confidence = self._fuzzy_match(text, variation)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_wake_word = model_name
                    best_match = variation

        # Check custom wake words
        for model_name, variations in self.custom_wake_words.items():
            for variation in variations:
                if variation in text:
                    return WakeWordDetection(
                        detected=True,
                        wake_word=model_name,
                        confidence=1.0,
                        timestamp_ms=time.time() * 1000,
                        metadata={"matched_text": variation, "custom": True}
                    )

                confidence = self._fuzzy_match(text, variation)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_wake_word = model_name
                    best_match = variation

        # Check if best match exceeds threshold
        if best_confidence >= self.wake_config.threshold:
            return WakeWordDetection(
                detected=True,
                wake_word=best_wake_word,
                confidence=best_confidence,
                timestamp_ms=time.time() * 1000,
                metadata={"matched_text": best_match, "fuzzy_match": True}
            )

        return WakeWordDetection(
            detected=False,
            wake_word=None,
            confidence=0.0,
            timestamp_ms=time.time() * 1000
        )

    def _fuzzy_match(self, text: str, wake_word: str) -> float:
        """Calculate fuzzy match confidence

        Args:
            text: Text to search in
            wake_word: Wake word to match

        Returns:
            Confidence score (0.0-1.0)
        """
        # Check if wake word is at the beginning
        if text.startswith(wake_word):
            return 0.95

        # Check word boundaries
        pattern = r'\b' + re.escape(wake_word) + r'\b'
        if re.search(pattern, text):
            return 0.9

        # Use Levenshtein distance for fuzzy matching
        # Find the best matching substring
        wake_len = len(wake_word)
        best_ratio = 0.0

        for i in range(len(text) - wake_len + 1):
            substring = text[i:i + wake_len]
            ratio = Levenshtein.ratio(substring, wake_word)
            if ratio > best_ratio:
                best_ratio = ratio

        # Apply sensitivity adjustment
        adjusted_ratio = best_ratio * (0.5 + self.wake_config.sensitivity)

        return min(adjusted_ratio, 1.0)

    def _preprocess_audio(self, audio: np.ndarray) -> np.ndarray:
        """Preprocess audio for Whisper

        Args:
            audio: Raw audio data

        Returns:
            Preprocessed audio
        """
        # Ensure float32
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        # Normalize to [-1, 1]
        if np.abs(audio).max() > 1.0:
            audio = audio / 32768.0

        # Ensure 1D array
        if len(audio.shape) > 1:
            audio = audio.flatten()

        return audio

    async def get_supported_models(self) -> List[str]:
        """Get list of supported wake word models

        Returns:
            List of model names
        """
        models = list(self.DEFAULT_WAKE_WORDS.keys())
        models.extend(self.custom_wake_words.keys())
        return [m.value if hasattr(m, 'value') else m for m in models]

    def add_custom_wake_word(self, name: str, variations: List[str]) -> None:
        """Add custom wake word at runtime

        Args:
            name: Wake word model name
            variations: List of text variations
        """
        self.custom_wake_words[name] = [v.lower().strip() for v in variations]
        logger.info(f"Added custom wake word: {name} with {len(variations)} variations")

    def remove_custom_wake_word(self, name: str) -> bool:
        """Remove custom wake word

        Args:
            name: Wake word model name

        Returns:
            Success status
        """
        if name in self.custom_wake_words:
            del self.custom_wake_words[name]
            logger.info(f"Removed custom wake word: {name}")
            return True
        return False

    def clear_transcript_buffer(self) -> None:
        """Clear the transcript buffer"""
        self.transcript_buffer.clear()
        logger.debug("Cleared transcript buffer")

    async def cleanup(self) -> None:
        """Clean up resources"""
        await super().cleanup()
        if self.stt_handler:
            await self.stt_handler.cleanup()
        self.transcript_buffer.clear()
        logger.info("Whisper wake word handler cleaned up")