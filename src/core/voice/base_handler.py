"""
Base voice handler interface for V5
Defines the contract for all voice processing components
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional, List, Union
import numpy as np
from dataclasses import dataclass
from datetime import datetime

class VoiceState(Enum):
    """Voice processing states"""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"

@dataclass
class AudioConfig:
    """Audio configuration settings"""
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024
    format: str = "int16"
    
@dataclass
class TranscriptionResult:
    """Speech-to-text result"""
    text: str
    confidence: float
    language: str
    timestamps: Optional[List[Dict]] = None
    duration_ms: float = 0
    
@dataclass
class SynthesisResult:
    """Text-to-speech result"""
    audio: bytes
    sample_rate: int
    duration_ms: float
    format: str = "wav"

@dataclass
class VADResult:
    """Voice activity detection result"""
    has_speech: bool
    confidence: float
    speech_segments: List[tuple]  # List of (start_ms, end_ms) tuples
    energy_level: float

class BaseVoiceHandler(ABC):
    """Abstract base class for voice handlers"""
    
    def __init__(self, config: Optional[AudioConfig] = None):
        """Initialize with audio configuration"""
        self.config = config or AudioConfig()
        self.state = VoiceState.IDLE
        self.metrics = {
            "total_processed": 0,
            "total_errors": 0,
            "avg_latency_ms": 0,
            "last_processed": None
        }
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the handler and load models"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources"""
        pass
    
    def set_state(self, state: VoiceState) -> None:
        """Update handler state"""
        self.state = state
        
    def get_state(self) -> VoiceState:
        """Get current handler state"""
        return self.state
    
    def update_metrics(self, latency_ms: float, success: bool = True) -> None:
        """Update performance metrics"""
        self.metrics["total_processed"] += 1
        if not success:
            self.metrics["total_errors"] += 1
        
        # Update average latency
        current_avg = self.metrics["avg_latency_ms"]
        total = self.metrics["total_processed"]
        self.metrics["avg_latency_ms"] = (current_avg * (total - 1) + latency_ms) / total
        self.metrics["last_processed"] = datetime.now().isoformat()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.metrics.copy()

class STTHandler(BaseVoiceHandler):
    """Speech-to-Text handler interface"""
    
    @abstractmethod
    async def transcribe(
        self, 
        audio: Union[np.ndarray, bytes],
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """Transcribe audio to text"""
        pass
    
    @abstractmethod
    async def transcribe_stream(
        self,
        audio_stream: Any
    ) -> TranscriptionResult:
        """Transcribe streaming audio"""
        pass

class TTSHandler(BaseVoiceHandler):
    """Text-to-Speech handler interface"""
    
    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        language: Optional[str] = None,
        speed: float = 1.0,
        pitch: float = 0.0
    ) -> SynthesisResult:
        """Synthesize speech from text"""
        pass
    
    @abstractmethod
    async def get_available_voices(self) -> List[Dict[str, str]]:
        """Get list of available voices"""
        pass

class VADHandler(BaseVoiceHandler):
    """Voice Activity Detection handler interface"""
    
    @abstractmethod
    async def detect(
        self,
        audio: Union[np.ndarray, bytes],
        threshold: float = 0.5
    ) -> VADResult:
        """Detect voice activity in audio"""
        pass
    
    @abstractmethod
    async def detect_stream(
        self,
        audio_stream: Any,
        callback: Any = None
    ) -> VADResult:
        """Detect voice activity in streaming audio"""
        pass