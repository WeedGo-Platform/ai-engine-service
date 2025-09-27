"""
WebSocket Transport Implementation
Handles real-time bidirectional audio streaming
"""
import asyncio
import websockets
import json
import time
import logging
from typing import Dict, Any, Optional
import base64
from collections import deque

from .streaming_manager import (
    IStreamingTransport,
    ConnectionMetrics,
    StreamingSession,
    ConnectionQuality
)

logger = logging.getLogger(__name__)

class WebSocketTransport(IStreamingTransport):
    """WebSocket transport for real-time audio streaming"""
    
    def __init__(self):
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.metrics = ConnectionMetrics()
        self.session: Optional[StreamingSession] = None
        self._send_queue: asyncio.Queue = asyncio.Queue()
        self._receive_queue: asyncio.Queue = asyncio.Queue()
        self._ping_task: Optional[asyncio.Task] = None
        self._send_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._packet_count = 0
        self._packet_loss_count = 0
        self._latency_samples = deque(maxlen=10)  # Keep last 10 latency samples
    
    async def connect(self, endpoint: str, session: StreamingSession) -> bool:
        """Establish WebSocket connection"""
        try:
            self.session = session
            self.websocket = await websockets.connect(
                endpoint,
                ping_interval=10,
                ping_timeout=5,
                max_size=10 * 1024 * 1024,  # 10MB max message size
                compression=None  # Disable compression for lower latency
            )
            
            # Send initial handshake
            await self.websocket.send(json.dumps({
                'type': 'init',
                'session_id': session.session_id,
                'config': {
                    'sample_rate': 16000,
                    'channels': 1,
                    'encoding': 'linear16',
                    'streaming': True
                }
            }))
            
            # Wait for acknowledgment
            response = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=5.0
            )
            data = json.loads(response)
            
            if data.get('type') == 'init_ack':
                # Start background tasks
                self._ping_task = asyncio.create_task(self._ping_loop())
                self._send_task = asyncio.create_task(self._send_loop())
                self._receive_task = asyncio.create_task(self._receive_loop())
                
                logger.info(f"WebSocket connected to {endpoint}")
                return True
            else:
                logger.error(f"Invalid handshake response: {data}")
                return False
                
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            return False
    
    async def send_audio(self, audio_chunk: bytes) -> bool:
        """Send audio chunk via WebSocket"""
        if not self.websocket or self.websocket.closed:
            return False
        
        try:
            # Create message with timestamp for latency measurement
            message = {
                'type': 'audio',
                'data': base64.b64encode(audio_chunk).decode('utf-8'),
                'timestamp': time.time(),
                'seq': self._packet_count
            }
            
            # Add to send queue
            await self._send_queue.put(json.dumps(message))
            self._packet_count += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send audio: {e}")
            return False
    
    async def receive_transcript(self) -> Optional[Dict[str, Any]]:
        """Receive transcript data from WebSocket"""
        try:
            if not self._receive_queue.empty():
                return await self._receive_queue.get()
            return None
        except Exception as e:
            logger.error(f"Failed to receive transcript: {e}")
            return None
    
    async def disconnect(self) -> None:
        """Close WebSocket connection"""
        # Cancel background tasks
        for task in [self._ping_task, self._send_task, self._receive_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Close WebSocket
        if self.websocket and not self.websocket.closed:
            await self.websocket.close()
            logger.info("WebSocket disconnected")
    
    def get_metrics(self) -> ConnectionMetrics:
        """Get current connection metrics"""
        # Calculate average latency
        if self._latency_samples:
            avg_latency = sum(self._latency_samples) / len(self._latency_samples)
            self.metrics.latency_ms = avg_latency * 1000
        
        # Calculate packet loss rate
        if self._packet_count > 0:
            self.metrics.packet_loss_rate = self._packet_loss_count / self._packet_count
        
        # Update quality assessment
        self.metrics.update()
        
        return self.metrics
    
    async def _send_loop(self) -> None:
        """Background task to send queued messages"""
        while self.websocket and not self.websocket.closed:
            try:
                message = await self._send_queue.get()
                await self.websocket.send(message)
            except websockets.ConnectionClosed:
                logger.warning("WebSocket connection closed during send")
                break
            except Exception as e:
                logger.error(f"Send loop error: {e}")
    
    async def _receive_loop(self) -> None:
        """Background task to receive messages"""
        while self.websocket and not self.websocket.closed:
            try:
                message = await self.websocket.recv()
                data = json.loads(message)
                
                # Handle different message types
                if data.get('type') == 'transcript':
                    # Calculate latency if timestamp available
                    if 'request_timestamp' in data:
                        latency = time.time() - data['request_timestamp']
                        self._latency_samples.append(latency)
                    
                    # Add to receive queue
                    await self._receive_queue.put({
                        'partial': data.get('partial', ''),
                        'is_final': data.get('is_final', False),
                        'confidence': data.get('confidence', 0.0),
                        'timestamp': data.get('timestamp', time.time())
                    })
                    
                elif data.get('type') == 'error':
                    logger.error(f"Server error: {data.get('message')}")
                    
                elif data.get('type') == 'metrics':
                    # Server-side metrics for monitoring
                    self._update_metrics_from_server(data)
                    
            except websockets.ConnectionClosed:
                logger.warning("WebSocket connection closed during receive")
                break
            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
            except Exception as e:
                logger.error(f"Receive loop error: {e}")
    
    async def _ping_loop(self) -> None:
        """Background task to measure latency via ping/pong"""
        while self.websocket and not self.websocket.closed:
            try:
                # Send ping with timestamp
                start_time = time.time()
                pong_waiter = await self.websocket.ping()
                await asyncio.wait_for(pong_waiter, timeout=5.0)
                
                # Calculate latency
                latency = time.time() - start_time
                self._latency_samples.append(latency)
                
                await asyncio.sleep(2)  # Ping every 2 seconds
                
            except asyncio.TimeoutError:
                self._packet_loss_count += 1
                logger.warning("Ping timeout - possible packet loss")
            except Exception as e:
                logger.error(f"Ping loop error: {e}")
                break
    
    def _update_metrics_from_server(self, data: Dict[str, Any]) -> None:
        """Update metrics from server-provided data"""
        if 'bandwidth_kbps' in data:
            self.metrics.bandwidth_kbps = data['bandwidth_kbps']
        if 'jitter_ms' in data:
            self.metrics.jitter_ms = data['jitter_ms']
        if 'server_load' in data:
            # Adjust quality based on server load if needed
            pass