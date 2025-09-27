"""
WebSocket Handler for Real-time Communication
Manages WebSocket connections, streaming responses, and live updates
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from enum import Enum

from agi.orchestrator import get_orchestrator
from agi.core.interfaces import ConversationContext, Message, MessageRole
from agi.analytics import get_metrics_collector
from agi.api.middleware.auth import verify_token

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket message types"""
    # Client -> Server
    AUTH = "auth"
    CHAT = "chat"
    STREAM_START = "stream_start"
    STREAM_STOP = "stream_stop"
    PING = "ping"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"

    # Server -> Client
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILED = "auth_failed"
    CHAT_RESPONSE = "chat_response"
    STREAM_CHUNK = "stream_chunk"
    STREAM_END = "stream_end"
    PONG = "pong"
    EVENT = "event"
    ERROR = "error"
    METRICS = "metrics"
    AGENT_STATUS = "agent_status"
    MODEL_STATUS = "model_status"


class WebSocketConnection:
    """Individual WebSocket connection handler"""

    def __init__(self, websocket: WebSocket, client_id: str):
        self.websocket = websocket
        self.client_id = client_id
        self.authenticated = False
        self.user_id: Optional[str] = None
        self.subscriptions: Set[str] = set()
        self.session_id: Optional[str] = None
        self.is_streaming = False

    async def send_message(self, message_type: MessageType, data: Any):
        """Send message to client"""
        try:
            await self.websocket.send_json({
                "type": message_type.value,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to send message to {self.client_id}: {e}")

    async def handle_auth(self, token: str) -> bool:
        """Authenticate WebSocket connection"""
        try:
            payload = verify_token(token)
            self.user_id = payload.get("sub")
            self.authenticated = True
            await self.send_message(MessageType.AUTH_SUCCESS, {
                "user_id": self.user_id,
                "username": payload.get("username")
            })
            return True
        except Exception as e:
            await self.send_message(MessageType.AUTH_FAILED, {"error": str(e)})
            return False


class WebSocketManager:
    """Manages all WebSocket connections"""

    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.topic_subscribers: Dict[str, Set[str]] = {}
        self._client_counter = 0

    def _generate_client_id(self) -> str:
        """Generate unique client ID"""
        self._client_counter += 1
        return f"client_{self._client_counter}_{datetime.utcnow().timestamp()}"

    async def connect(self, websocket: WebSocket) -> WebSocketConnection:
        """Accept and register new WebSocket connection"""
        await websocket.accept()
        client_id = self._generate_client_id()
        connection = WebSocketConnection(websocket, client_id)
        self.connections[client_id] = connection

        logger.info(f"WebSocket client {client_id} connected")

        # Send initial connection success
        await connection.send_message(MessageType.EVENT, {
            "event": "connected",
            "client_id": client_id
        })

        return connection

    def disconnect(self, client_id: str):
        """Remove WebSocket connection"""
        if client_id in self.connections:
            connection = self.connections[client_id]

            # Remove from all subscriptions
            for topic in connection.subscriptions:
                if topic in self.topic_subscribers:
                    self.topic_subscribers[topic].discard(client_id)

            del self.connections[client_id]
            logger.info(f"WebSocket client {client_id} disconnected")

    async def broadcast_to_topic(self, topic: str, message_type: MessageType, data: Any):
        """Broadcast message to all subscribers of a topic"""
        if topic not in self.topic_subscribers:
            return

        disconnected = []

        for client_id in self.topic_subscribers[topic]:
            if client_id in self.connections:
                try:
                    await self.connections[client_id].send_message(message_type, data)
                except Exception as e:
                    logger.error(f"Failed to send to {client_id}: {e}")
                    disconnected.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)

    async def subscribe_to_topic(self, client_id: str, topic: str):
        """Subscribe client to a topic"""
        if client_id not in self.connections:
            return

        if topic not in self.topic_subscribers:
            self.topic_subscribers[topic] = set()

        self.topic_subscribers[topic].add(client_id)
        self.connections[client_id].subscriptions.add(topic)

        logger.info(f"Client {client_id} subscribed to {topic}")

    async def unsubscribe_from_topic(self, client_id: str, topic: str):
        """Unsubscribe client from a topic"""
        if client_id not in self.connections:
            return

        if topic in self.topic_subscribers:
            self.topic_subscribers[topic].discard(client_id)

        if client_id in self.connections:
            self.connections[client_id].subscriptions.discard(topic)

        logger.info(f"Client {client_id} unsubscribed from {topic}")


# Global WebSocket manager
ws_manager = WebSocketManager()


async def handle_websocket(websocket: WebSocket):
    """Main WebSocket handler"""
    connection = await ws_manager.connect(websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            msg_type = message.get("type")
            msg_data = message.get("data", {})

            # Handle authentication
            if msg_type == MessageType.AUTH.value:
                token = msg_data.get("token")
                if not await connection.handle_auth(token):
                    continue

            # Require authentication for other operations
            if not connection.authenticated and msg_type != MessageType.PING.value:
                await connection.send_message(MessageType.ERROR, {
                    "error": "Authentication required"
                })
                continue

            # Handle different message types
            if msg_type == MessageType.PING.value:
                await connection.send_message(MessageType.PONG, {})

            elif msg_type == MessageType.CHAT.value:
                await handle_chat_message(connection, msg_data)

            elif msg_type == MessageType.STREAM_START.value:
                await handle_stream_start(connection, msg_data)

            elif msg_type == MessageType.STREAM_STOP.value:
                connection.is_streaming = False

            elif msg_type == MessageType.SUBSCRIBE.value:
                topic = msg_data.get("topic")
                if topic:
                    await ws_manager.subscribe_to_topic(connection.client_id, topic)

            elif msg_type == MessageType.UNSUBSCRIBE.value:
                topic = msg_data.get("topic")
                if topic:
                    await ws_manager.unsubscribe_from_topic(connection.client_id, topic)

    except WebSocketDisconnect:
        ws_manager.disconnect(connection.client_id)
    except Exception as e:
        logger.error(f"WebSocket error for {connection.client_id}: {e}")
        await connection.send_message(MessageType.ERROR, {"error": str(e)})
        ws_manager.disconnect(connection.client_id)


async def handle_chat_message(connection: WebSocketConnection, data: Dict[str, Any]):
    """Handle chat message from client"""
    try:
        message = data.get("message")
        session_id = data.get("session_id") or connection.session_id

        if not message:
            await connection.send_message(MessageType.ERROR, {
                "error": "Message content required"
            })
            return

        # Get orchestrator
        orchestrator = await get_orchestrator()

        # Create conversation context
        context = ConversationContext(
            messages=[Message(role=MessageRole.USER, content=message)],
            session_id=session_id,
            user_id=connection.user_id
        )

        # Process request
        response = await orchestrator.process_request(
            request=message,
            context=context,
            stream=False
        )

        # Send response
        await connection.send_message(MessageType.CHAT_RESPONSE, {
            "response": response,
            "session_id": session_id
        })

        # Update metrics
        metrics = await get_metrics_collector()
        await metrics.record_request(
            session_id=session_id,
            user_id=connection.user_id,
            request_type="websocket_chat"
        )

    except Exception as e:
        logger.error(f"Chat message handling error: {e}")
        await connection.send_message(MessageType.ERROR, {
            "error": f"Failed to process message: {str(e)}"
        })


async def handle_stream_start(connection: WebSocketConnection, data: Dict[str, Any]):
    """Handle streaming request from client"""
    try:
        message = data.get("message")
        session_id = data.get("session_id") or connection.session_id

        if not message:
            await connection.send_message(MessageType.ERROR, {
                "error": "Message content required"
            })
            return

        connection.is_streaming = True

        # Get orchestrator
        orchestrator = await get_orchestrator()

        # Create conversation context
        context = ConversationContext(
            messages=[Message(role=MessageRole.USER, content=message)],
            session_id=session_id,
            user_id=connection.user_id
        )

        # Stream response
        async for chunk in orchestrator.stream_response(message, context):
            if not connection.is_streaming:
                break

            await connection.send_message(MessageType.STREAM_CHUNK, {
                "chunk": chunk,
                "session_id": session_id
            })

        # Send stream end
        await connection.send_message(MessageType.STREAM_END, {
            "session_id": session_id
        })

        connection.is_streaming = False

    except Exception as e:
        logger.error(f"Stream handling error: {e}")
        await connection.send_message(MessageType.ERROR, {
            "error": f"Stream failed: {str(e)}"
        })
        connection.is_streaming = False


# Event broadcasting functions
async def broadcast_agent_status(agent_id: str, status: str, details: Dict[str, Any]):
    """Broadcast agent status update"""
    await ws_manager.broadcast_to_topic(
        "agents",
        MessageType.AGENT_STATUS,
        {
            "agent_id": agent_id,
            "status": status,
            "details": details
        }
    )


async def broadcast_model_status(model_id: str, status: str, details: Dict[str, Any]):
    """Broadcast model status update"""
    await ws_manager.broadcast_to_topic(
        "models",
        MessageType.MODEL_STATUS,
        {
            "model_id": model_id,
            "status": status,
            "details": details
        }
    )


async def broadcast_metrics(metrics_data: Dict[str, Any]):
    """Broadcast system metrics"""
    await ws_manager.broadcast_to_topic(
        "metrics",
        MessageType.METRICS,
        metrics_data
    )