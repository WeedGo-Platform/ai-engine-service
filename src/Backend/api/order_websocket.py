"""
Order Tracking WebSocket endpoints
Provides real-time order status updates to mobile clients
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Dict, Set
from uuid import UUID
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/orders", tags=["order-tracking"])


class OrderTrackingManager:
    """Manages WebSocket connections for order tracking"""

    def __init__(self):
        # Map of order_id -> set of WebSocket connections
        self.order_connections: Dict[str, Set[WebSocket]] = {}
        # Map of user_id -> set of WebSocket connections (for user's all orders)
        self.user_connections: Dict[str, Set[WebSocket]] = {}
        # Map of WebSocket -> subscribed order_ids
        self.connection_subscriptions: Dict[WebSocket, Set[str]] = {}

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.connection_subscriptions[websocket] = set()
        logger.info("New order tracking connection established")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection and clean up subscriptions"""
        # Get all orders this connection was subscribed to
        subscribed_orders = self.connection_subscriptions.get(websocket, set())

        # Remove from each order's connection set
        for order_id in subscribed_orders:
            if order_id in self.order_connections:
                self.order_connections[order_id].discard(websocket)
                if not self.order_connections[order_id]:
                    del self.order_connections[order_id]

        # Clean up connection tracking
        if websocket in self.connection_subscriptions:
            del self.connection_subscriptions[websocket]

        logger.info(f"Order tracking connection closed (was subscribed to {len(subscribed_orders)} orders)")

    def subscribe_to_order(self, websocket: WebSocket, order_id: str):
        """Subscribe a WebSocket to order updates"""
        if order_id not in self.order_connections:
            self.order_connections[order_id] = set()

        self.order_connections[order_id].add(websocket)
        self.connection_subscriptions[websocket].add(order_id)
        logger.info(f"Connection subscribed to order {order_id}")

    def unsubscribe_from_order(self, websocket: WebSocket, order_id: str):
        """Unsubscribe a WebSocket from order updates"""
        if order_id in self.order_connections:
            self.order_connections[order_id].discard(websocket)
            if not self.order_connections[order_id]:
                del self.order_connections[order_id]

        if websocket in self.connection_subscriptions:
            self.connection_subscriptions[websocket].discard(order_id)

        logger.info(f"Connection unsubscribed from order {order_id}")

    async def broadcast_to_order(self, order_id: str, message: dict):
        """Broadcast a message to all connections watching an order"""
        connections = self.order_connections.get(order_id, set())

        if not connections:
            logger.debug(f"No connections watching order {order_id}")
            return

        logger.info(f"Broadcasting to {len(connections)} connections for order {order_id}: {message.get('type')}")

        # Send to all connections, remove dead ones
        dead_connections = set()
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to connection: {e}")
                dead_connections.add(connection)

        # Clean up dead connections
        for dead in dead_connections:
            self.disconnect(dead)

    async def send_to_connection(self, websocket: WebSocket, message: dict):
        """Send a message to a specific connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.disconnect(websocket)


# Global manager instance
manager = OrderTrackingManager()


@router.websocket("/track")
async def track_orders_websocket(
    websocket: WebSocket,
    token: str = Query(None)
):
    """
    WebSocket endpoint for real-time order tracking

    Client sends:
        - {"type": "subscribe", "order_id": "uuid"}
        - {"type": "unsubscribe", "order_id": "uuid"}
        - {"type": "ping"}

    Server sends:
        - {"type": "order_update", "order_id": "uuid", "status": "...", "timestamp": "...", "message": "..."}
        - {"type": "location_update", "order_id": "uuid", "latitude": 0.0, "longitude": 0.0}
        - {"type": "delivery_complete", "order_id": "uuid", "timestamp": "..."}
        - {"type": "order_cancelled", "order_id": "uuid", "reason": "...", "timestamp": "..."}
        - {"type": "pong"}
        - {"type": "error", "message": "..."}
    """
    await manager.connect(websocket)

    try:
        # Send welcome message
        await manager.send_to_connection(websocket, {
            "type": "connected",
            "message": "Order tracking connected"
        })

        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                message = json.loads(data)

                message_type = message.get("type")

                if message_type == "subscribe":
                    # Subscribe to order updates
                    order_id = message.get("order_id")
                    if order_id:
                        manager.subscribe_to_order(websocket, order_id)
                        await manager.send_to_connection(websocket, {
                            "type": "subscribed",
                            "order_id": order_id
                        })
                    else:
                        await manager.send_to_connection(websocket, {
                            "type": "error",
                            "message": "order_id required for subscribe"
                        })

                elif message_type == "unsubscribe":
                    # Unsubscribe from order updates
                    order_id = message.get("order_id")
                    if order_id:
                        manager.unsubscribe_from_order(websocket, order_id)
                        await manager.send_to_connection(websocket, {
                            "type": "unsubscribed",
                            "order_id": order_id
                        })

                elif message_type == "ping":
                    # Respond to ping with pong
                    await manager.send_to_connection(websocket, {
                        "type": "pong"
                    })

                else:
                    logger.warning(f"Unknown message type: {message_type}")

            except WebSocketDisconnect:
                logger.info("Client disconnected")
                break
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                await manager.send_to_connection(websocket, {
                    "type": "error",
                    "message": "Invalid JSON"
                })
            except Exception as e:
                logger.error(f"Error handling message: {e}")

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected during setup")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)


# Helper functions for broadcasting (called by order_service)
async def broadcast_order_status_update(order_id: str, status: str, message: str = None, estimated_time: str = None):
    """Broadcast order status update to all watching clients"""
    from datetime import datetime

    await manager.broadcast_to_order(order_id, {
        "type": "order_update",
        "order_id": order_id,
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "message": message,
        "estimated_time": estimated_time
    })


async def broadcast_delivery_location_update(order_id: str, latitude: float, longitude: float):
    """Broadcast delivery driver location update"""
    await manager.broadcast_to_order(order_id, {
        "type": "location_update",
        "order_id": order_id,
        "latitude": latitude,
        "longitude": longitude
    })


async def broadcast_delivery_complete(order_id: str):
    """Broadcast delivery completion"""
    from datetime import datetime

    await manager.broadcast_to_order(order_id, {
        "type": "delivery_complete",
        "order_id": order_id,
        "timestamp": datetime.utcnow().isoformat()
    })


async def broadcast_order_cancelled(order_id: str, reason: str = None):
    """Broadcast order cancellation"""
    from datetime import datetime

    await manager.broadcast_to_order(order_id, {
        "type": "order_cancelled",
        "order_id": order_id,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat()
    })


# Export router and manager
__all__ = ['router', 'manager', 'broadcast_order_status_update', 'broadcast_delivery_location_update',
           'broadcast_delivery_complete', 'broadcast_order_cancelled']
