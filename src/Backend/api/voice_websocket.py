"""
WebSocket endpoints for real-time voice processing
Enables continuous wake word detection and streaming transcription
Following SOLID principles and industry best practices
"""
import asyncio
import logging
import json
import base64
import time
import numpy as np
from typing import Dict, Any, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from fastapi import APIRouter
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid

from core.voice import VoicePipeline, PipelineMode
from core.voice.wake_word_handler import WakeWordDetection
from core.voice.wake_word_state_manager import (
    WakeWordStateManager,
    WakeWordSessionState
)

logger = logging.getLogger(__name__)

# Create router for WebSocket endpoints
router = APIRouter(prefix="/api/voice/ws", tags=["voice-websocket"])


class WSMessageType(Enum):
    """WebSocket message types"""
    # Client to server
    AUDIO_DATA = "audio_data"
    START_LISTENING = "start_listening"
    STOP_LISTENING = "stop_listening"
    CONFIGURE = "configure"
    HEARTBEAT = "heartbeat"

    # Server to client
    WAKE_WORD_DETECTED = "wake_word_detected"
    TRANSCRIPTION = "transcription"
    VAD_STATE = "vad_state"
    STATUS = "status"
    ERROR = "error"
    HEARTBEAT_ACK = "heartbeat_ack"


class ListeningState(Enum):
    """Voice listening states"""
    IDLE = "idle"
    LISTENING_WAKE_WORD = "listening_wake_word"
    LISTENING_COMMAND = "listening_command"
    PROCESSING = "processing"
    ERROR = "error"


@dataclass
class WSSession:
    """WebSocket session information"""
    session_id: str
    websocket: WebSocket
    pipeline: Optional[VoicePipeline]
    state: ListeningState
    config: Dict[str, Any]
    start_time: float
    last_activity: float
    audio_buffer: list
    wake_word_active: bool
    command_timeout_task: Optional[asyncio.Task]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "session_id": self.session_id,
            "state": self.state.value,
            "wake_word_active": self.wake_word_active,
            "duration_s": time.time() - self.start_time,
            "last_activity_s": time.time() - self.last_activity
        }


class VoiceWebSocketManager:
    """Manages WebSocket connections for voice processing"""

    def __init__(self):
        """Initialize WebSocket manager"""
        self.active_sessions: Dict[str, WSSession] = {}
        self.pipeline_pool: Dict[str, VoicePipeline] = {}
        self.state_manager = WakeWordStateManager()
        self.max_sessions = 100
        self.command_timeout_s = 10  # Timeout after wake word detection
        self.idle_timeout_s = 300  # 5 minutes idle timeout
        self.audio_chunk_size = 1024 * 4  # 4KB chunks
        self.cleanup_task_started = False

    async def get_pipeline(self, session_id: str) -> VoicePipeline:
        """Get or create pipeline for session"""
        if session_id not in self.pipeline_pool:
            pipeline = VoicePipeline(wake_word_enabled=True)
            if not await pipeline.initialize():
                raise RuntimeError("Failed to initialize voice pipeline")
            self.pipeline_pool[session_id] = pipeline
        return self.pipeline_pool[session_id]

    async def cleanup_session(self, session_id: str):
        """Clean up session resources"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]

            # Cancel command timeout if exists
            if session.command_timeout_task:
                session.command_timeout_task.cancel()

            # Remove from active sessions
            del self.active_sessions[session_id]

        # Clean up pipeline
        if session_id in self.pipeline_pool:
            await self.pipeline_pool[session_id].cleanup()
            del self.pipeline_pool[session_id]

        logger.info(f"Cleaned up session: {session_id}")

    async def handle_audio_data(
        self,
        session: WSSession,
        audio_data: bytes
    ) -> None:
        """Process incoming audio data"""
        try:
            # Update activity timestamp
            session.last_activity = time.time()

            # Convert audio data
            audio_array = np.frombuffer(audio_data, dtype=np.float32)

            # Add to buffer
            session.audio_buffer.append(audio_array)

            # Process based on state
            if session.state == ListeningState.LISTENING_WAKE_WORD:
                await self._process_wake_word(session, audio_array)

            elif session.state == ListeningState.LISTENING_COMMAND:
                await self._process_command(session, audio_array)

        except Exception as e:
            logger.error(f"Error processing audio data: {e}")
            await self._send_error(session, f"Audio processing error: {str(e)}")

    async def _process_wake_word(
        self,
        session: WSSession,
        audio: np.ndarray
    ) -> None:
        """Process audio for wake word detection"""
        if not session.pipeline or not session.pipeline.wake_word:
            return

        # Detect wake word
        detection = await session.pipeline.wake_word.detect(audio)

        if detection.detected:
            logger.info(f"Wake word detected: {detection.wake_word} "
                       f"(confidence: {detection.confidence:.2f})")

            # Update session state
            session.state = ListeningState.LISTENING_COMMAND
            session.wake_word_active = True

            # Send wake word detection notification
            await session.websocket.send_json({
                "type": WSMessageType.WAKE_WORD_DETECTED.value,
                "data": {
                    "wake_word": detection.wake_word,
                    "confidence": detection.confidence,
                    "timestamp": detection.timestamp_ms
                }
            })

            # Start command timeout
            session.command_timeout_task = asyncio.create_task(
                self._command_timeout(session)
            )

            # Clear audio buffer for command processing
            session.audio_buffer.clear()

    async def _process_command(
        self,
        session: WSSession,
        audio: np.ndarray
    ) -> None:
        """Process audio for command transcription"""
        if not session.pipeline:
            return

        # Check if we have enough audio (at least 0.5 seconds)
        if len(session.audio_buffer) >= 8:  # ~0.5s at 16kHz
            # Concatenate buffer
            full_audio = np.concatenate(session.audio_buffer)

            # Process with VAD
            result = await session.pipeline.process_audio(
                full_audio,
                mode=PipelineMode.AUTO_VAD
            )

            # Check for speech
            if result.get("has_speech") and result.get("transcription"):
                transcription = result["transcription"]

                # Send transcription
                await session.websocket.send_json({
                    "type": WSMessageType.TRANSCRIPTION.value,
                    "data": {
                        "text": transcription["text"],
                        "confidence": transcription["confidence"],
                        "language": transcription.get("language"),
                        "is_command": True,
                        "session_id": session.session_id
                    }
                })

                # Reset to wake word listening
                await self._reset_to_wake_word_listening(session)

            # Send VAD state if changed
            if result.get("vad_result"):
                vad_result = result["vad_result"]
                await session.websocket.send_json({
                    "type": WSMessageType.VAD_STATE.value,
                    "data": {
                        "has_speech": vad_result["has_speech"],
                        "confidence": vad_result["confidence"]
                    }
                })

    async def _command_timeout(self, session: WSSession):
        """Handle command timeout after wake word detection"""
        try:
            await asyncio.sleep(self.command_timeout_s)

            # Timeout reached - reset to wake word listening
            logger.info(f"Command timeout for session {session.session_id}")
            await self._reset_to_wake_word_listening(session)

        except asyncio.CancelledError:
            # Task was cancelled (command received or session ended)
            pass

    async def _reset_to_wake_word_listening(self, session: WSSession):
        """Reset session to wake word listening state"""
        session.state = ListeningState.LISTENING_WAKE_WORD
        session.wake_word_active = False
        session.audio_buffer.clear()

        # Cancel command timeout if exists
        if session.command_timeout_task:
            session.command_timeout_task.cancel()
            session.command_timeout_task = None

        # Notify client of state change
        await session.websocket.send_json({
            "type": WSMessageType.STATUS.value,
            "data": {
                "state": session.state.value,
                "message": "Listening for wake word"
            }
        })

    async def _send_error(self, session: WSSession, error_msg: str):
        """Send error message to client"""
        try:
            await session.websocket.send_json({
                "type": WSMessageType.ERROR.value,
                "data": {
                    "error": error_msg,
                    "timestamp": time.time() * 1000
                }
            })
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")

    async def start_listening(self, session: WSSession):
        """Start continuous listening"""
        try:
            # Start cleanup task on first use
            if not self.cleanup_task_started:
                asyncio.create_task(self.state_manager.start_cleanup_task())
                self.cleanup_task_started = True

            # Initialize pipeline if needed
            if not session.pipeline:
                session.pipeline = await self.get_pipeline(session.session_id)

            # Set initial state
            session.state = ListeningState.LISTENING_WAKE_WORD

            # Configure wake word callback
            async def on_wake_word(detection: WakeWordDetection):
                logger.debug(f"Wake word callback: {detection.wake_word}")

            await session.pipeline.set_callbacks(
                on_wake_word=on_wake_word
            )

            # Send status update
            await session.websocket.send_json({
                "type": WSMessageType.STATUS.value,
                "data": {
                    "state": session.state.value,
                    "message": "Started listening for wake word",
                    "config": session.config
                }
            })

            logger.info(f"Started listening for session {session.session_id}")

        except Exception as e:
            logger.error(f"Failed to start listening: {e}")
            await self._send_error(session, f"Failed to start listening: {str(e)}")

    async def stop_listening(self, session: WSSession):
        """Stop continuous listening"""
        session.state = ListeningState.IDLE
        session.audio_buffer.clear()

        if session.command_timeout_task:
            session.command_timeout_task.cancel()
            session.command_timeout_task = None

        await session.websocket.send_json({
            "type": WSMessageType.STATUS.value,
            "data": {
                "state": session.state.value,
                "message": "Stopped listening"
            }
        })

        logger.info(f"Stopped listening for session {session.session_id}")


# Global manager instance
ws_manager = VoiceWebSocketManager()


@router.websocket("/listen")
async def websocket_listen(websocket: WebSocket):
    """WebSocket endpoint for continuous voice listening

    Protocol:
    1. Client connects and sends START_LISTENING message
    2. Client streams audio data in chunks
    3. Server detects wake words and transcribes commands
    4. Server sends notifications for wake words, transcriptions, and VAD states
    5. Client sends STOP_LISTENING to end session

    Message Format:
    {
        "type": "message_type",
        "data": { ... }
    }
    """
    await websocket.accept()

    # Create session
    session_id = str(uuid.uuid4())
    session = WSSession(
        session_id=session_id,
        websocket=websocket,
        pipeline=None,
        state=ListeningState.IDLE,
        config={},
        start_time=time.time(),
        last_activity=time.time(),
        audio_buffer=[],
        wake_word_active=False,
        command_timeout_task=None
    )

    # Add to active sessions
    ws_manager.active_sessions[session_id] = session

    try:
        logger.info(f"WebSocket connection established: {session_id}")

        # Send initial status
        await websocket.send_json({
            "type": WSMessageType.STATUS.value,
            "data": {
                "session_id": session_id,
                "state": session.state.value,
                "message": "Connected successfully"
            }
        })

        # Message handling loop
        while True:
            # Receive message with timeout
            message = await asyncio.wait_for(
                websocket.receive_json(),
                timeout=ws_manager.idle_timeout_s
            )

            msg_type = message.get("type")
            msg_data = message.get("data", {})

            if msg_type == WSMessageType.START_LISTENING.value:
                # Start continuous listening
                session.config = msg_data.get("config", {})
                await ws_manager.start_listening(session)

            elif msg_type == WSMessageType.STOP_LISTENING.value:
                # Stop listening
                await ws_manager.stop_listening(session)

            elif msg_type == WSMessageType.AUDIO_DATA.value:
                # Process audio data
                audio_base64 = msg_data.get("audio")
                if audio_base64:
                    audio_bytes = base64.b64decode(audio_base64)
                    await ws_manager.handle_audio_data(session, audio_bytes)

            elif msg_type == WSMessageType.CONFIGURE.value:
                # Update configuration
                session.config.update(msg_data)

                # Apply to pipeline if exists
                if session.pipeline and session.pipeline.wake_word:
                    if "threshold" in msg_data:
                        session.pipeline.wake_word.wake_config.threshold = msg_data["threshold"]
                    if "sensitivity" in msg_data:
                        session.pipeline.wake_word.wake_config.sensitivity = msg_data["sensitivity"]

                await websocket.send_json({
                    "type": WSMessageType.STATUS.value,
                    "data": {
                        "message": "Configuration updated",
                        "config": session.config
                    }
                })

            elif msg_type == WSMessageType.HEARTBEAT.value:
                # Respond to heartbeat
                await websocket.send_json({
                    "type": WSMessageType.HEARTBEAT_ACK.value,
                    "data": {"timestamp": time.time() * 1000}
                })
                session.last_activity = time.time()

            else:
                logger.warning(f"Unknown message type: {msg_type}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except asyncio.TimeoutError:
        logger.info(f"WebSocket timeout: {session_id}")
        await websocket.close(code=1000, reason="Idle timeout")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason=str(e))
    finally:
        # Clean up session
        await ws_manager.cleanup_session(session_id)


@router.websocket("/stream")
async def websocket_stream(websocket: WebSocket):
    """Simplified WebSocket endpoint for streaming transcription

    This endpoint provides real-time transcription without wake word detection.
    Useful for applications that handle wake word detection client-side.
    """
    await websocket.accept()
    session_id = str(uuid.uuid4())

    try:
        # Get pipeline
        pipeline = await ws_manager.get_pipeline(session_id)

        # Send initial status
        await websocket.send_json({
            "type": "status",
            "session_id": session_id,
            "message": "Ready for streaming"
        })

        # Audio buffer for accumulation
        audio_buffer = []
        buffer_duration_ms = 0
        min_buffer_duration_ms = 250  # Process every 250ms for real-time feedback

        # Transcript accumulation
        accumulated_transcript = ""
        last_partial = ""
        silence_start = None
        pause_threshold_ms = 3000  # 3 second pause for auto-send

        while True:
            # Receive audio chunk
            message = await websocket.receive_json()

            if message.get("type") == "audio":
                # Decode audio
                audio_base64 = message.get("data")
                if audio_base64:
                    audio_bytes = base64.b64decode(audio_base64)
                    audio_array = np.frombuffer(audio_bytes, dtype=np.float32)

                    # Add to buffer
                    audio_buffer.append(audio_array)
                    chunk_duration = (len(audio_array) / 16000) * 1000
                    buffer_duration_ms += chunk_duration

                    # Process when buffer is sufficient (every 250ms)
                    if buffer_duration_ms >= min_buffer_duration_ms:
                        full_audio = np.concatenate(audio_buffer)

                        # Process audio with VAD
                        result = await pipeline.process_audio(
                            full_audio,
                            mode=PipelineMode.AUTO_VAD
                        )

                        # Check for speech
                        if result.get("has_speech"):
                            # Reset silence timer
                            silence_start = None

                            # Get transcription
                            if result.get("transcription"):
                                new_text = result["transcription"]["text"]

                                # Send partial transcript immediately
                                if new_text and new_text != last_partial:
                                    await websocket.send_json({
                                        "type": "partial",
                                        "text": new_text,
                                        "confidence": result["transcription"].get("confidence", 0.5),
                                        "is_partial": True
                                    })
                                    last_partial = new_text
                                    accumulated_transcript = new_text

                            # Keep a sliding window of audio
                            audio_buffer = audio_buffer[-2:]  # Keep last 2 chunks for context
                            buffer_duration_ms = chunk_duration * 2
                        else:
                            # No speech detected - track silence
                            if accumulated_transcript and silence_start is None:
                                silence_start = time.time()

                            # Check for pause threshold
                            if silence_start and (time.time() - silence_start) * 1000 >= pause_threshold_ms:
                                if accumulated_transcript:
                                    # Send final transcript after pause
                                    await websocket.send_json({
                                        "type": "final",
                                        "text": accumulated_transcript,
                                        "confidence": 1.0,
                                        "is_final": True,
                                        "reason": "pause_detected"
                                    })

                                    # Reset
                                    accumulated_transcript = ""
                                    last_partial = ""
                                    silence_start = None

                            # Clear old audio to prevent memory growth
                            if len(audio_buffer) > 10:
                                audio_buffer = audio_buffer[-3:]
                                buffer_duration_ms = chunk_duration * 3

            elif message.get("type") == "end":
                # Send any remaining transcript as final
                if accumulated_transcript:
                    await websocket.send_json({
                        "type": "final",
                        "text": accumulated_transcript,
                        "confidence": 1.0,
                        "is_final": True,
                        "reason": "session_end"
                    })
                break

    except WebSocketDisconnect:
        logger.info(f"Stream WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"Stream WebSocket error: {e}")
    finally:
        # Clean up
        if session_id in ws_manager.pipeline_pool:
            await ws_manager.pipeline_pool[session_id].cleanup()
            del ws_manager.pipeline_pool[session_id]


@router.get("/sessions")
async def get_active_sessions() -> Dict[str, Any]:
    """Get information about active WebSocket sessions"""
    sessions = []
    for session_id, session in ws_manager.active_sessions.items():
        sessions.append(session.to_dict())

    return {
        "status": "success",
        "total_sessions": len(sessions),
        "sessions": sessions,
        "max_sessions": ws_manager.max_sessions
    }