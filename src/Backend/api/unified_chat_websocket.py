"""
Unified WebSocket Handler for Real-Time Chat.

This module provides a clean WebSocket implementation following SOLID principles,
consolidating all real-time chat functionality into a single, maintainable handler.
"""

import logging
import json
import asyncio
from typing import Optional, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect, status
from datetime import datetime

from services.chat import (
    get_chat_service,
    ChatRequest,
    WebSocketMessageType
)

logger = logging.getLogger(__name__)


class WebSocketConnectionManager:
    """
    Manages WebSocket connections and message routing.

    This class handles connection lifecycle, message parsing, and error handling
    for WebSocket clients.
    """

    def __init__(self):
        """Initialize connection manager"""
        self.active_connections: Dict[str, WebSocket] = {}
        logger.info("WebSocketConnectionManager initialized")

    async def connect(
        self,
        websocket: WebSocket,
        session_id: Optional[str] = None
    ) -> str:
        """
        Accept a new WebSocket connection and create/resume session.

        Args:
            websocket: The WebSocket connection
            session_id: Optional existing session ID to resume

        Returns:
            str: Session ID for this connection
        """
        await websocket.accept()

        chat_service = get_chat_service()

        # Create or resume session
        if session_id:
            try:
                # Verify session exists
                await chat_service.get_session(session_id)
                logger.info(f"Resumed existing session {session_id}")
            except ValueError:
                # Session doesn't exist, create new one
                logger.warning(f"Session {session_id} not found, creating new session")
                session_id = await chat_service.create_session()
        else:
            # Create new session
            session_id = await chat_service.create_session()
            logger.info(f"Created new session {session_id}")

        # Store connection
        self.active_connections[session_id] = websocket

        # Send connection confirmation
        await self.send_message(
            session_id,
            {
                "type": WebSocketMessageType.CONNECTION.value,
                "session_id": session_id,
                "message": "Connected successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        return session_id

    async def disconnect(self, session_id: str):
        """
        Handle WebSocket disconnection.

        Args:
            session_id: Session identifier
        """
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"Disconnected session {session_id}")

    async def send_message(self, session_id: str, message: Dict[str, Any]):
        """
        Send a message to a specific session.

        Args:
            session_id: Session identifier
            message: Message data to send
        """
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {session_id}: {str(e)}")
                await self.disconnect(session_id)

    async def send_typing_indicator(self, session_id: str, is_typing: bool = True):
        """
        Send typing indicator to client.

        Args:
            session_id: Session identifier
            is_typing: Whether the bot is typing
        """
        await self.send_message(
            session_id,
            {
                "type": WebSocketMessageType.TYPING.value,
                "typing": is_typing,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    async def send_error(self, session_id: str, error_message: str, error_code: str = "UNKNOWN"):
        """
        Send error message to client.

        Args:
            session_id: Session identifier
            error_message: Error description
            error_code: Error code identifier
        """
        await self.send_message(
            session_id,
            {
                "type": WebSocketMessageType.ERROR.value,
                "error": error_message,
                "error_code": error_code,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    async def send_token_update(self, session_id: str, message_id: str, current_tokens: int):
        """
        Send token count update to client during response streaming.

        Args:
            session_id: Session identifier
            message_id: Message being generated
            current_tokens: Current token count
        """
        await self.send_message(
            session_id,
            {
                "type": WebSocketMessageType.TOKEN_UPDATE.value,
                "message_id": message_id,
                "current_tokens": current_tokens,
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# Global connection manager instance
_connection_manager: Optional[WebSocketConnectionManager] = None


def get_connection_manager() -> WebSocketConnectionManager:
    """Get or create the global connection manager"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = WebSocketConnectionManager()
    return _connection_manager


async def handle_websocket_connection(
    websocket: WebSocket,
    session_id: Optional[str] = None
):
    """
    Main WebSocket connection handler.

    This function manages the entire lifecycle of a WebSocket connection,
    including message processing, session management, and error handling.

    Args:
        websocket: The WebSocket connection
        session_id: Optional existing session ID to resume

    Message Types:
        - "message": User message (requires: message)
        - "session_update": Update agent/personality (requires: agent and/or personality)
        - "heartbeat": Keep-alive ping (no payload required)

    Example Messages:
        # Send a message
        {"type": "message", "message": "I want sativa pre-rolls"}

        # Update agent/personality
        {"type": "session_update", "agent": "dispensary", "personality": "marcel"}

        # Heartbeat
        {"type": "heartbeat"}
    """
    manager = get_connection_manager()
    chat_service = get_chat_service()

    # Establish connection
    active_session_id = await manager.connect(websocket, session_id)

    try:
        while True:
            # Receive message from client
            try:
                data = await websocket.receive_json()
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {str(e)}")
                await manager.send_error(
                    active_session_id,
                    "Invalid JSON format",
                    "INVALID_JSON"
                )
                continue

            message_type = data.get("type")

            # ============================================================
            # Handle Message Type: "message"
            # ============================================================
            if message_type == "message":
                user_message = data.get("message")

                if not user_message:
                    await manager.send_error(
                        active_session_id,
                        "Message text is required",
                        "MISSING_MESSAGE"
                    )
                    continue

                try:
                    # Send typing indicator
                    await manager.send_typing_indicator(active_session_id, True)

                    # Process message through ChatService
                    response_data = await chat_service.process_message(
                        message=user_message,
                        session_id=active_session_id,
                        user_id=data.get("user_id"),
                        store_id=data.get("store_id"),
                        language=data.get("language", "en"),
                        use_tools=data.get("use_tools", True),
                        use_context=data.get("use_context", True),
                        max_tokens=data.get("max_tokens", 500)
                    )

                    # Stop typing indicator
                    await manager.send_typing_indicator(active_session_id, False)

                    # Extract metadata for top-level fields
                    metadata = response_data.get("metadata", {})
                    final_token_count = metadata.get("tokens_used", 0)

                    # Generate message ID for this response
                    message_id = response_data.get("id", datetime.utcnow().isoformat())

                    # Simulate token streaming for UX (send incremental updates)
                    if final_token_count > 0:
                        num_updates = min(5, final_token_count // 10)  # Send 5-10 updates

                        for i in range(1, num_updates + 1):
                            current_tokens = int((final_token_count * i) / (num_updates + 1))
                            await manager.send_token_update(
                                active_session_id,
                                message_id,
                                current_tokens
                            )
                            await asyncio.sleep(0.05)  # 50ms between updates

                    # Send response with extracted metadata fields
                    await manager.send_message(
                        active_session_id,
                        {
                            "type": WebSocketMessageType.MESSAGE.value,
                            "id": message_id,
                            "content": response_data.get("text", ""),
                            "products": response_data.get("products", []),
                            "quick_actions": response_data.get("quick_actions", []),
                            "metadata": metadata,
                            "response_time": metadata.get("response_time"),
                            "token_count": metadata.get("tokens_used"),
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )

                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}", exc_info=True)
                    await manager.send_typing_indicator(active_session_id, False)
                    await manager.send_error(
                        active_session_id,
                        "Failed to process message",
                        "PROCESSING_ERROR"
                    )

            # ============================================================
            # Handle Message Type: "session_update"
            # ============================================================
            elif message_type == "session_update":
                agent_id = data.get("agent")
                personality_id = data.get("personality")

                if not agent_id and not personality_id:
                    await manager.send_error(
                        active_session_id,
                        "Agent or personality must be provided",
                        "MISSING_PARAMETERS"
                    )
                    continue

                try:
                    success = await chat_service.update_session(
                        session_id=active_session_id,
                        agent_id=agent_id,
                        personality_id=personality_id,
                        store_id=data.get("store_id"),
                        language=data.get("language")
                    )

                    if success:
                        session_data = await chat_service.get_session(active_session_id)
                        await manager.send_message(
                            active_session_id,
                            {
                                "type": WebSocketMessageType.SESSION_UPDATED.value,
                                "message": f"Session updated successfully",
                                "agent": session_data["agent_id"],
                                "personality": session_data["personality_id"],
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        )
                    else:
                        await manager.send_error(
                            active_session_id,
                            "Failed to update session",
                            "UPDATE_FAILED"
                        )

                except Exception as e:
                    logger.error(f"Error updating session: {str(e)}", exc_info=True)
                    await manager.send_error(
                        active_session_id,
                        "Failed to update session",
                        "UPDATE_ERROR"
                    )

            # ============================================================
            # Handle Message Type: "heartbeat" or "ping"
            # ============================================================
            elif message_type in ("heartbeat", "ping"):
                # Respond with same message type as received (ping->pong, heartbeat->heartbeat)
                response_type = "pong" if message_type == "ping" else "heartbeat"
                await manager.send_message(
                    active_session_id,
                    {
                        "type": response_type,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )

            # ============================================================
            # Handle Unknown Message Type
            # ============================================================
            else:
                logger.warning(f"Unknown message type: {message_type}")
                await manager.send_error(
                    active_session_id,
                    f"Unknown message type: {message_type}",
                    "UNKNOWN_MESSAGE_TYPE"
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {active_session_id}")
        await manager.disconnect(active_session_id)

    except Exception as e:
        logger.error(f"Unexpected error in WebSocket handler: {str(e)}", exc_info=True)
        try:
            await manager.send_error(
                active_session_id,
                "Internal server error",
                "INTERNAL_ERROR"
            )
        except:
            pass  # Connection may already be closed
        await manager.disconnect(active_session_id)


async def broadcast_to_all(message: Dict[str, Any]):
    """
    Broadcast a message to all active connections.

    Useful for system-wide notifications or announcements.

    Args:
        message: Message data to broadcast
    """
    manager = get_connection_manager()

    for session_id in list(manager.active_connections.keys()):
        try:
            await manager.send_message(session_id, message)
        except Exception as e:
            logger.error(f"Error broadcasting to {session_id}: {str(e)}")


async def get_active_connections() -> int:
    """
    Get the number of active WebSocket connections.

    Returns:
        int: Number of active connections
    """
    manager = get_connection_manager()
    return len(manager.active_connections)
