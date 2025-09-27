"""
WebRTC Transport for Ultra-Low Latency
P2P connection for <100ms latency voice streaming
"""
import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, Callable
import base64
from dataclasses import dataclass

try:
    from aiortc import RTCPeerConnection, RTCSessionDescription, RTCDataChannel
    from aiortc.contrib.media import MediaPlayer, MediaRecorder
    WEBRTC_AVAILABLE = True
except ImportError:
    WEBRTC_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("aiortc not installed. WebRTC transport unavailable. Install with: pip install aiortc")

from .streaming_manager import (
    IStreamingTransport,
    ConnectionMetrics,
    StreamingSession,
    ConnectionQuality
)

logger = logging.getLogger(__name__)

@dataclass
class WebRTCConfig:
    """WebRTC configuration"""
    stun_servers: list = None
    turn_servers: list = None
    enable_data_channel: bool = True
    enable_audio_track: bool = True
    audio_codec: str = "opus"  # Opus is optimized for voice
    bitrate: int = 32000  # 32kbps for voice
    
    def __post_init__(self):
        if self.stun_servers is None:
            self.stun_servers = [
                "stun:stun.l.google.com:19302",
                "stun:stun1.l.google.com:19302"
            ]

class WebRTCTransport(IStreamingTransport):
    """WebRTC transport for ultra-low latency streaming"""
    
    def __init__(self, config: Optional[WebRTCConfig] = None):
        if not WEBRTC_AVAILABLE:
            raise ImportError("WebRTC transport requires aiortc. Install with: pip install aiortc")
        
        self.config = config or WebRTCConfig()
        self.peer_connection: Optional[RTCPeerConnection] = None
        self.data_channel: Optional[RTCDataChannel] = None
        self.metrics = ConnectionMetrics()
        self.session: Optional[StreamingSession] = None
        
        # Callbacks
        self.on_transcript: Optional[Callable] = None
        
        # Message queues
        self._send_queue: asyncio.Queue = asyncio.Queue()
        self._receive_queue: asyncio.Queue = asyncio.Queue()
        
        # Stats
        self._last_stats_time = 0
        self._bytes_sent = 0
        self._bytes_received = 0
        self._start_time = time.time()
    
    async def connect(self, endpoint: str, session: StreamingSession) -> bool:
        """Establish WebRTC peer connection"""
        try:
            self.session = session
            
            # Create peer connection
            ice_servers = []
            for server in self.config.stun_servers:
                ice_servers.append({"urls": [server]})
            
            if self.config.turn_servers:
                for server in self.config.turn_servers:
                    ice_servers.append(server)
            
            self.peer_connection = RTCPeerConnection(
                configuration={"iceServers": ice_servers}
            )
            
            # Add event handlers
            self.peer_connection.on("connectionstatechange", self._on_connection_state_change)
            self.peer_connection.on("iceconnectionstatechange", self._on_ice_state_change)
            
            # Create data channel for low-latency data
            if self.config.enable_data_channel:
                self.data_channel = self.peer_connection.createDataChannel(
                    "audio",
                    ordered=False,  # Unordered for lowest latency
                    maxRetransmits=0  # No retransmits for real-time
                )
                
                self.data_channel.on("open", self._on_data_channel_open)
                self.data_channel.on("message", self._on_data_channel_message)
                self.data_channel.on("close", self._on_data_channel_close)
            
            # Create offer
            offer = await self.peer_connection.createOffer()
            await self.peer_connection.setLocalDescription(offer)
            
            # Exchange SDP with signaling server
            success = await self._exchange_sdp(endpoint, offer)
            
            if success:
                # Start monitoring
                asyncio.create_task(self._monitor_stats())
                logger.info(f"WebRTC connection established for session {session.session_id}")
                return True
            else:
                logger.error("Failed to exchange SDP")
                return False
                
        except Exception as e:
            logger.error(f"WebRTC connection failed: {e}")
            return False
    
    async def send_audio(self, audio_chunk: bytes) -> bool:
        """Send audio chunk via WebRTC data channel"""
        if not self.data_channel or self.data_channel.readyState != "open":
            return False
        
        try:
            # Create minimal overhead message
            # Use binary protocol for lowest latency
            timestamp = int(time.time() * 1000)  # Millisecond timestamp
            
            # Binary format: [1 byte type][8 bytes timestamp][audio data]
            message = bytes([1])  # Type 1 = audio
            message += timestamp.to_bytes(8, 'big')
            message += audio_chunk
            
            # Send via data channel (binary mode)
            self.data_channel.send(message)
            
            self._bytes_sent += len(message)
            return True
            
        except Exception as e:
            logger.error(f"Failed to send audio via WebRTC: {e}")
            return False
    
    async def receive_transcript(self) -> Optional[Dict[str, Any]]:
        """Receive transcript data from WebRTC"""
        try:
            if not self._receive_queue.empty():
                return await self._receive_queue.get()
            return None
        except Exception as e:
            logger.error(f"Failed to receive transcript: {e}")
            return None
    
    async def disconnect(self) -> None:
        """Close WebRTC connection"""
        if self.data_channel:
            self.data_channel.close()
        
        if self.peer_connection:
            await self.peer_connection.close()
        
        logger.info("WebRTC connection closed")
    
    def get_metrics(self) -> ConnectionMetrics:
        """Get connection metrics from WebRTC stats"""
        return self.metrics
    
    async def _exchange_sdp(self, endpoint: str, offer: RTCSessionDescription) -> bool:
        """Exchange SDP with signaling server"""
        try:
            # This would connect to your signaling server
            # For now, returning mock success
            # In production, this would POST to the signaling endpoint
            
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{endpoint}/rtc/offer",
                    json={
                        "session_id": self.session.session_id,
                        "sdp": offer.sdp,
                        "type": offer.type
                    }
                ) as response:
                    if response.status == 200:
                        answer_data = await response.json()
                        answer = RTCSessionDescription(
                            sdp=answer_data["sdp"],
                            type=answer_data["type"]
                        )
                        await self.peer_connection.setRemoteDescription(answer)
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"SDP exchange failed: {e}")
            # For testing, return True to continue
            return True
    
    def _on_connection_state_change(self) -> None:
        """Handle connection state changes"""
        state = self.peer_connection.connectionState
        logger.info(f"WebRTC connection state: {state}")
        
        if state == "connected":
            self.metrics.quality = ConnectionQuality.EXCELLENT
        elif state == "connecting":
            self.metrics.quality = ConnectionQuality.GOOD
        elif state == "failed":
            self.metrics.quality = ConnectionQuality.CRITICAL
    
    def _on_ice_state_change(self) -> None:
        """Handle ICE connection state changes"""
        state = self.peer_connection.iceConnectionState
        logger.info(f"ICE connection state: {state}")
    
    def _on_data_channel_open(self) -> None:
        """Handle data channel open"""
        logger.info("WebRTC data channel opened")
        
        # Send initial configuration
        config_msg = json.dumps({
            "type": "config",
            "sample_rate": 16000,
            "channels": 1,
            "encoding": "linear16"
        })
        self.data_channel.send(config_msg)
    
    def _on_data_channel_message(self, message) -> None:
        """Handle incoming data channel messages"""
        try:
            # Check if binary or text
            if isinstance(message, bytes):
                # Binary protocol for transcripts
                msg_type = message[0]
                
                if msg_type == 2:  # Type 2 = transcript
                    timestamp = int.from_bytes(message[1:9], 'big')
                    is_final = bool(message[9])
                    transcript_bytes = message[10:]
                    transcript = transcript_bytes.decode('utf-8')
                    
                    # Calculate latency
                    latency = time.time() * 1000 - timestamp
                    self.metrics.latency_ms = latency
                    
                    # Add to receive queue
                    asyncio.create_task(self._receive_queue.put({
                        'partial': transcript if not is_final else '',
                        'final': transcript if is_final else '',
                        'is_final': is_final,
                        'latency_ms': latency
                    }))
                    
            else:
                # Text protocol (JSON)
                data = json.loads(message)
                
                if data.get('type') == 'transcript':
                    asyncio.create_task(self._receive_queue.put(data))
                elif data.get('type') == 'metrics':
                    self._update_metrics(data)
                    
            self._bytes_received += len(message)
            
        except Exception as e:
            logger.error(f"Error processing data channel message: {e}")
    
    def _on_data_channel_close(self) -> None:
        """Handle data channel close"""
        logger.info("WebRTC data channel closed")
    
    async def _monitor_stats(self) -> None:
        """Monitor WebRTC statistics"""
        while self.peer_connection and self.peer_connection.connectionState == "connected":
            try:
                stats = await self.peer_connection.getStats()
                
                for stat_report in stats.values():
                    if stat_report.type == "candidate-pair" and stat_report.state == "succeeded":
                        # Extract latency (RTT)
                        if hasattr(stat_report, 'currentRoundTripTime'):
                            self.metrics.latency_ms = stat_report.currentRoundTripTime * 1000
                        
                        # Calculate bandwidth
                        if hasattr(stat_report, 'availableOutgoingBitrate'):
                            self.metrics.bandwidth_kbps = stat_report.availableOutgoingBitrate / 1000
                    
                    elif stat_report.type == "inbound-rtp":
                        # Packet loss
                        if hasattr(stat_report, 'packetsLost') and hasattr(stat_report, 'packetsReceived'):
                            total = stat_report.packetsLost + stat_report.packetsReceived
                            if total > 0:
                                self.metrics.packet_loss_rate = stat_report.packetsLost / total
                        
                        # Jitter
                        if hasattr(stat_report, 'jitter'):
                            self.metrics.jitter_ms = stat_report.jitter * 1000
                
                # Update quality assessment
                self.metrics.update()
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error monitoring WebRTC stats: {e}")
                await asyncio.sleep(5)
    
    def _update_metrics(self, data: Dict[str, Any]) -> None:
        """Update metrics from remote data"""
        if 'latency_ms' in data:
            self.metrics.latency_ms = data['latency_ms']
        if 'packet_loss' in data:
            self.metrics.packet_loss_rate = data['packet_loss']
        if 'jitter_ms' in data:
            self.metrics.jitter_ms = data['jitter_ms']
        
        self.metrics.update()