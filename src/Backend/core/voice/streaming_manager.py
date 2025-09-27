"""
Real-time Streaming Manager for Voice
Handles WebSocket streaming, WebRTC fallback, and connection quality monitoring
Follows SOLID principles with clear separation of concerns
"""
import asyncio
import logging
import time
import numpy as np
from typing import Dict, Any, Optional, Callable, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import json

logger = logging.getLogger(__name__)

class ConnectionType(Enum):
    """Connection types for streaming"""
    WEBSOCKET = "websocket"
    WEBRTC = "webrtc"
    FALLBACK = "http_chunked"

class ConnectionQuality(Enum):
    """Connection quality levels"""
    EXCELLENT = "excellent"  # < 50ms latency, 0% loss
    GOOD = "good"            # < 100ms latency, < 1% loss
    FAIR = "fair"            # < 200ms latency, < 3% loss
    POOR = "poor"            # < 500ms latency, < 5% loss
    CRITICAL = "critical"    # > 500ms latency or > 5% loss

@dataclass
class StreamingConfig:
    """Configuration for streaming"""
    chunk_duration_ms: int = 250  # Audio chunk duration
    sample_rate: int = 16000
    channels: int = 1
    partial_result_interval_ms: int = 100  # How often to send partials
    silence_threshold_ms: int = 1500  # Silence to trigger endpoint
    max_utterance_duration_ms: int = 60000  # Max recording length
    enable_webrtc: bool = True
    enable_predictive_text: bool = True
    buffer_size: int = 10  # Number of chunks to buffer
    
    # Quality thresholds
    latency_threshold_good: int = 100
    latency_threshold_fair: int = 200
    latency_threshold_poor: int = 500
    packet_loss_threshold: float = 0.03

@dataclass
class ConnectionMetrics:
    """Metrics for connection quality monitoring"""
    latency_ms: float = 0
    packet_loss_rate: float = 0
    jitter_ms: float = 0
    bandwidth_kbps: float = 0
    last_update: float = field(default_factory=time.time)
    quality: ConnectionQuality = ConnectionQuality.GOOD
    
    def update(self, latency: float = None, loss: float = None):
        """Update metrics and calculate quality"""
        if latency is not None:
            self.latency_ms = latency
        if loss is not None:
            self.packet_loss_rate = loss
        self.last_update = time.time()
        self.quality = self._calculate_quality()
    
    def _calculate_quality(self) -> ConnectionQuality:
        """Calculate connection quality based on metrics"""
        if self.latency_ms < 50 and self.packet_loss_rate < 0.001:
            return ConnectionQuality.EXCELLENT
        elif self.latency_ms < 100 and self.packet_loss_rate < 0.01:
            return ConnectionQuality.GOOD
        elif self.latency_ms < 200 and self.packet_loss_rate < 0.03:
            return ConnectionQuality.FAIR
        elif self.latency_ms < 500 and self.packet_loss_rate < 0.05:
            return ConnectionQuality.POOR
        else:
            return ConnectionQuality.CRITICAL

@dataclass
class StreamingSession:
    """Represents a streaming session"""
    session_id: str
    connection_type: ConnectionType
    metrics: ConnectionMetrics = field(default_factory=ConnectionMetrics)
    start_time: float = field(default_factory=time.time)
    audio_buffer: List[bytes] = field(default_factory=list)
    transcript_buffer: List[str] = field(default_factory=list)
    is_speaking: bool = False
    last_speech_time: float = 0
    partial_transcript: str = ""
    final_transcript: str = ""
    
class IStreamingTransport(ABC):
    """Abstract interface for streaming transport (SRP)"""
    
    @abstractmethod
    async def connect(self, endpoint: str, session: StreamingSession) -> bool:
        """Establish connection"""
        pass
    
    @abstractmethod
    async def send_audio(self, audio_chunk: bytes) -> bool:
        """Send audio chunk"""
        pass
    
    @abstractmethod
    async def receive_transcript(self) -> Optional[Dict[str, Any]]:
        """Receive transcript data"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection"""
        pass
    
    @abstractmethod
    def get_metrics(self) -> ConnectionMetrics:
        """Get connection metrics"""
        pass

class IEndpointDetector(ABC):
    """Abstract interface for endpoint detection (SRP)"""
    
    @abstractmethod
    async def detect_endpoint(self, audio: np.ndarray, transcript: str) -> bool:
        """Detect if utterance is complete"""
        pass

class IAudioProcessor(ABC):
    """Abstract interface for audio processing (SRP)"""
    
    @abstractmethod
    async def process_chunk(self, audio: bytes) -> np.ndarray:
        """Process audio chunk"""
        pass
    
    @abstractmethod
    async def apply_noise_reduction(self, audio: np.ndarray) -> np.ndarray:
        """Apply noise reduction"""
        pass

class StreamingManager:
    """Main streaming manager coordinating all components"""
    
    def __init__(
        self,
        config: Optional[StreamingConfig] = None,
        transport: Optional[IStreamingTransport] = None,
        endpoint_detector: Optional[IEndpointDetector] = None,
        audio_processor: Optional[IAudioProcessor] = None
    ):
        self.config = config or StreamingConfig()
        self.transport = transport
        self.endpoint_detector = endpoint_detector
        self.audio_processor = audio_processor
        self.sessions: Dict[str, StreamingSession] = {}
        self.callbacks: Dict[str, List[Callable]] = {
            'on_partial': [],
            'on_final': [],
            'on_error': [],
            'on_quality_change': []
        }
        self._monitoring_task: Optional[asyncio.Task] = None
        
    async def start_session(
        self,
        session_id: str,
        connection_type: ConnectionType = ConnectionType.WEBSOCKET
    ) -> StreamingSession:
        """Start a new streaming session"""
        session = StreamingSession(
            session_id=session_id,
            connection_type=connection_type
        )
        self.sessions[session_id] = session
        
        # Start monitoring if not already running
        if not self._monitoring_task:
            self._monitoring_task = asyncio.create_task(self._monitor_connections())
        
        logger.info(f"Started streaming session {session_id} with {connection_type.value}")
        return session
    
    async def process_audio_chunk(
        self,
        session_id: str,
        audio_chunk: bytes
    ) -> Optional[Dict[str, Any]]:
        """Process incoming audio chunk"""
        session = self.sessions.get(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            return None
        
        # Add to buffer
        session.audio_buffer.append(audio_chunk)
        
        # Process audio if processor available
        if self.audio_processor:
            audio_np = await self.audio_processor.process_chunk(audio_chunk)
        else:
            audio_np = self._bytes_to_numpy(audio_chunk)
        
        # Send via transport
        if self.transport:
            success = await self.transport.send_audio(audio_chunk)
            if not success:
                await self._handle_transport_failure(session)
        
        # Check for endpoint
        if self.endpoint_detector and session.partial_transcript:
            is_endpoint = await self.endpoint_detector.detect_endpoint(
                audio_np,
                session.partial_transcript
            )
            
            if is_endpoint:
                await self._finalize_utterance(session)
        
        return {
            'session_id': session_id,
            'partial': session.partial_transcript,
            'is_final': False
        }
    
    async def _finalize_utterance(self, session: StreamingSession) -> None:
        """Finalize current utterance"""
        if session.partial_transcript:
            session.final_transcript = session.partial_transcript
            session.transcript_buffer.append(session.final_transcript)
            
            # Trigger callbacks
            for callback in self.callbacks['on_final']:
                await callback({
                    'session_id': session.session_id,
                    'transcript': session.final_transcript,
                    'timestamp': time.time()
                })
            
            # Reset for next utterance
            session.partial_transcript = ""
            session.audio_buffer.clear()
    
    async def _handle_transport_failure(self, session: StreamingSession) -> None:
        """Handle transport failure and attempt fallback"""
        logger.warning(f"Transport failure for session {session.session_id}")
        
        # Try fallback based on current type
        if session.connection_type == ConnectionType.WEBSOCKET:
            if self.config.enable_webrtc:
                logger.info("Falling back to WebRTC")
                session.connection_type = ConnectionType.WEBRTC
                # TODO: Initialize WebRTC transport
            else:
                logger.info("Falling back to HTTP chunked")
                session.connection_type = ConnectionType.FALLBACK
    
    async def _monitor_connections(self) -> None:
        """Monitor connection quality for all sessions"""
        while self.sessions:
            for session in list(self.sessions.values()):
                if self.transport:
                    metrics = self.transport.get_metrics()
                    old_quality = session.metrics.quality
                    session.metrics = metrics
                    
                    # Check if quality changed significantly
                    if old_quality != metrics.quality:
                        await self._handle_quality_change(session, old_quality, metrics.quality)
                
            await asyncio.sleep(1)  # Check every second
    
    async def _handle_quality_change(
        self,
        session: StreamingSession,
        old_quality: ConnectionQuality,
        new_quality: ConnectionQuality
    ) -> None:
        """Handle connection quality changes"""
        logger.info(f"Quality change for {session.session_id}: {old_quality.value} -> {new_quality.value}")
        
        # Trigger callbacks
        for callback in self.callbacks['on_quality_change']:
            await callback({
                'session_id': session.session_id,
                'old_quality': old_quality.value,
                'new_quality': new_quality.value,
                'metrics': session.metrics
            })
        
        # Auto-switch transport if needed
        if new_quality in [ConnectionQuality.POOR, ConnectionQuality.CRITICAL]:
            await self._handle_transport_failure(session)
    
    def register_callback(self, event: str, callback: Callable) -> None:
        """Register event callback"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)
    
    def _bytes_to_numpy(self, audio_bytes: bytes) -> np.ndarray:
        """Convert bytes to numpy array"""
        return np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    
    async def stop_session(self, session_id: str) -> None:
        """Stop a streaming session"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            
            # Finalize any pending transcript
            if session.partial_transcript:
                await self._finalize_utterance(session)
            
            # Clean up
            del self.sessions[session_id]
            
            # Stop monitoring if no more sessions
            if not self.sessions and self._monitoring_task:
                self._monitoring_task.cancel()
                self._monitoring_task = None
            
            logger.info(f"Stopped streaming session {session_id}")
    
    def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session statistics"""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        duration = time.time() - session.start_time
        return {
            'session_id': session_id,
            'duration_seconds': duration,
            'connection_type': session.connection_type.value,
            'quality': session.metrics.quality.value,
            'latency_ms': session.metrics.latency_ms,
            'packet_loss': session.metrics.packet_loss_rate,
            'transcripts_count': len(session.transcript_buffer),
            'audio_chunks_buffered': len(session.audio_buffer)
        }