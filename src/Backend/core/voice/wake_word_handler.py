"""
Wake Word Detection Handler for V5
Implements wake word detection using OpenWakeWord or similar frameworks
Following SOLID principles and industry best practices
"""
import asyncio
import logging
import time
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum

from .base_handler import BaseVoiceHandler, AudioConfig, VoiceState

logger = logging.getLogger(__name__)


class WakeWordModel(Enum):
    """Available wake word models"""
    HEY_WEEDGO = "hey_weedgo"
    WEEDGO = "weedgo"
    HEY_BUD = "hey_bud"
    CUSTOM = "custom"


@dataclass
class WakeWordConfig:
    """Wake word detection configuration"""
    models: List[WakeWordModel] = field(default_factory=lambda: [WakeWordModel.HEY_WEEDGO])
    threshold: float = 0.5  # Detection threshold (0.0-1.0)
    sensitivity: float = 0.5  # Overall sensitivity adjustment
    pre_silence_ms: int = 300  # Ms of silence before wake word
    post_silence_ms: int = 500  # Ms of silence after wake word
    cooldown_ms: int = 2000  # Ms to wait before next detection
    max_duration_ms: int = 3000  # Max duration for wake word
    min_duration_ms: int = 500  # Min duration for wake word
    enable_vad: bool = True  # Use VAD for efficiency
    continuous_mode: bool = True  # Keep listening after detection
    audio_context_ms: int = 1000  # Audio context to keep for verification


@dataclass
class WakeWordDetection:
    """Wake word detection result"""
    detected: bool
    wake_word: Optional[str]
    confidence: float
    timestamp_ms: float
    audio_context: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WakeWordMetrics:
    """Wake word detection metrics"""
    total_detections: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    avg_confidence: float = 0.0
    avg_latency_ms: float = 0.0
    last_detection: Optional[datetime] = None
    session_start: datetime = field(default_factory=datetime.now)

    def update_detection(self, confidence: float, latency_ms: float):
        """Update metrics with new detection"""
        self.total_detections += 1
        self.avg_confidence = (
            (self.avg_confidence * (self.total_detections - 1) + confidence)
            / self.total_detections
        )
        self.avg_latency_ms = (
            (self.avg_latency_ms * (self.total_detections - 1) + latency_ms)
            / self.total_detections
        )
        self.last_detection = datetime.now()

    def get_precision(self) -> float:
        """Calculate precision metric"""
        if self.total_detections == 0:
            return 0.0
        return 1.0 - (self.false_positives / self.total_detections)

    def get_session_duration(self) -> float:
        """Get session duration in seconds"""
        return (datetime.now() - self.session_start).total_seconds()


class WakeWordHandler(BaseVoiceHandler):
    """Abstract base class for wake word detection handlers"""

    def __init__(
        self,
        config: Optional[AudioConfig] = None,
        wake_config: Optional[WakeWordConfig] = None
    ):
        """Initialize wake word handler

        Args:
            config: Audio configuration
            wake_config: Wake word specific configuration
        """
        super().__init__(config)
        self.wake_config = wake_config or WakeWordConfig()
        self.wake_metrics = WakeWordMetrics()
        self.last_detection_time = 0
        self.is_listening = False
        self.detection_callbacks: List[Callable] = []
        self.audio_buffer: List[np.ndarray] = []
        self.buffer_duration_ms = 0

    @abstractmethod
    async def load_models(self, model_paths: Dict[str, Path]) -> bool:
        """Load wake word detection models

        Args:
            model_paths: Dictionary mapping model names to file paths

        Returns:
            Success status
        """
        pass

    @abstractmethod
    async def detect(
        self,
        audio: Union[np.ndarray, bytes],
        return_confidence: bool = False
    ) -> WakeWordDetection:
        """Detect wake word in audio

        Args:
            audio: Audio data to process
            return_confidence: Whether to return confidence scores

        Returns:
            Wake word detection result
        """
        pass

    @abstractmethod
    async def get_supported_models(self) -> List[str]:
        """Get list of supported wake word models

        Returns:
            List of model names
        """
        pass

    async def start_continuous_detection(
        self,
        audio_stream: asyncio.Queue,
        callback: Optional[Callable] = None
    ) -> None:
        """Start continuous wake word detection

        Args:
            audio_stream: Queue of audio chunks
            callback: Function to call on detection
        """
        if callback:
            self.detection_callbacks.append(callback)

        self.is_listening = True
        self.set_state(VoiceState.LISTENING)

        try:
            while self.is_listening:
                # Get audio chunk from stream
                if not audio_stream.empty():
                    audio_chunk = await audio_stream.get()

                    # Add to buffer for context
                    self._update_buffer(audio_chunk)

                    # Check for wake word
                    detection = await self.detect(audio_chunk)

                    if detection.detected:
                        # Check cooldown period
                        current_time = time.time() * 1000
                        if current_time - self.last_detection_time > self.wake_config.cooldown_ms:
                            self.last_detection_time = current_time

                            # Update metrics
                            latency = time.time() * 1000 - detection.timestamp_ms
                            self.wake_metrics.update_detection(
                                detection.confidence,
                                latency
                            )

                            # Add audio context
                            detection.audio_context = self._get_audio_context()

                            # Trigger callbacks
                            await self._trigger_callbacks(detection)

                            logger.info(f"Wake word detected: {detection.wake_word} "
                                      f"(confidence: {detection.confidence:.2f})")
                else:
                    await asyncio.sleep(0.01)  # Small delay to prevent busy waiting

        except Exception as e:
            logger.error(f"Error in continuous detection: {e}")
            self.set_state(VoiceState.ERROR)
        finally:
            self.is_listening = False
            self.set_state(VoiceState.IDLE)

    async def stop_continuous_detection(self) -> None:
        """Stop continuous wake word detection"""
        self.is_listening = False
        logger.info("Stopped continuous wake word detection")

    def _update_buffer(self, audio_chunk: np.ndarray) -> None:
        """Update audio buffer with new chunk

        Args:
            audio_chunk: New audio data
        """
        # Calculate chunk duration
        chunk_duration_ms = (len(audio_chunk) / self.config.sample_rate) * 1000

        # Add to buffer
        self.audio_buffer.append(audio_chunk)
        self.buffer_duration_ms += chunk_duration_ms

        # Trim buffer to max context duration
        while self.buffer_duration_ms > self.wake_config.audio_context_ms:
            if self.audio_buffer:
                removed = self.audio_buffer.pop(0)
                removed_duration = (len(removed) / self.config.sample_rate) * 1000
                self.buffer_duration_ms -= removed_duration

    def _get_audio_context(self) -> np.ndarray:
        """Get audio context from buffer

        Returns:
            Concatenated audio buffer
        """
        if not self.audio_buffer:
            return np.array([])
        return np.concatenate(self.audio_buffer)

    async def _trigger_callbacks(self, detection: WakeWordDetection) -> None:
        """Trigger registered callbacks

        Args:
            detection: Wake word detection result
        """
        for callback in self.detection_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(detection)
                else:
                    callback(detection)
            except Exception as e:
                logger.error(f"Error in detection callback: {e}")

    def register_callback(self, callback: Callable) -> None:
        """Register a detection callback

        Args:
            callback: Function to call on detection
        """
        if callback not in self.detection_callbacks:
            self.detection_callbacks.append(callback)

    def unregister_callback(self, callback: Callable) -> None:
        """Unregister a detection callback

        Args:
            callback: Function to remove
        """
        if callback in self.detection_callbacks:
            self.detection_callbacks.remove(callback)

    def update_config(self, wake_config: WakeWordConfig) -> None:
        """Update wake word configuration

        Args:
            wake_config: New configuration
        """
        self.wake_config = wake_config
        logger.info(f"Updated wake word config: threshold={wake_config.threshold}, "
                   f"sensitivity={wake_config.sensitivity}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics

        Returns:
            Metrics dictionary
        """
        base_metrics = super().get_metrics()
        wake_metrics = {
            "wake_word": {
                "total_detections": self.wake_metrics.total_detections,
                "false_positives": self.wake_metrics.false_positives,
                "false_negatives": self.wake_metrics.false_negatives,
                "avg_confidence": self.wake_metrics.avg_confidence,
                "avg_latency_ms": self.wake_metrics.avg_latency_ms,
                "precision": self.wake_metrics.get_precision(),
                "session_duration_s": self.wake_metrics.get_session_duration(),
                "last_detection": self.wake_metrics.last_detection.isoformat()
                    if self.wake_metrics.last_detection else None
            }
        }
        return {**base_metrics, **wake_metrics}

    def mark_false_positive(self) -> None:
        """Mark last detection as false positive"""
        self.wake_metrics.false_positives += 1
        logger.info(f"Marked false positive. Total: {self.wake_metrics.false_positives}")

    def mark_false_negative(self) -> None:
        """Mark a missed detection (false negative)"""
        self.wake_metrics.false_negatives += 1
        logger.info(f"Marked false negative. Total: {self.wake_metrics.false_negatives}")

    async def cleanup(self) -> None:
        """Clean up resources"""
        await self.stop_continuous_detection()
        self.audio_buffer.clear()
        self.detection_callbacks.clear()
        logger.info("Wake word handler cleaned up")