"""
WebSocket Manager Service
Handles real-time notifications for verification codes and admin alerts
Supports both user-facing notifications and admin dashboard updates
"""

import logging
import json
from typing import Dict, Set, Optional, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from enum import Enum

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """Types of WebSocket notifications"""
    VERIFICATION_CODE = "verification_code"
    SIGNUP_PROGRESS = "signup_progress"
    ADMIN_NEW_REVIEW = "admin_new_review"
    ADMIN_REVIEW_UPDATE = "admin_review_update"
    SYSTEM_MESSAGE = "system_message"


class ConnectionManager:
    """
    Manages WebSocket connections for real-time notifications

    Supports multiple connection types:
    - User connections (identified by email or session_id)
    - Admin connections (receive all review notifications)
    - Anonymous connections (receive system messages only)
    """

    def __init__(self):
        # Active connections by type
        self.user_connections: Dict[str, Set[WebSocket]] = {}  # email/session -> websockets
        self.admin_connections: Set[WebSocket] = set()
        self.all_connections: Set[WebSocket] = set()

        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}

        logger.info("WebSocket ConnectionManager initialized")

    async def connect_user(self, websocket: WebSocket, identifier: str):
        """
        Connect a user websocket

        Args:
            websocket: WebSocket connection
            identifier: User identifier (email or session_id)
        """
        await websocket.accept()

        if identifier not in self.user_connections:
            self.user_connections[identifier] = set()

        self.user_connections[identifier].add(websocket)
        self.all_connections.add(websocket)

        # Store metadata
        self.connection_metadata[websocket] = {
            "type": "user",
            "identifier": identifier,
            "connected_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        }

        logger.info(f"User WebSocket connected: {identifier}")

        # Send connection confirmation
        await self.send_to_websocket(websocket, {
            "type": NotificationType.SYSTEM_MESSAGE,
            "message": "Connected to WeedGo notification service",
            "timestamp": datetime.utcnow().isoformat()
        })

    async def connect_admin(self, websocket: WebSocket, admin_email: str):
        """
        Connect an admin websocket

        Args:
            websocket: WebSocket connection
            admin_email: Admin user email
        """
        await websocket.accept()

        self.admin_connections.add(websocket)
        self.all_connections.add(websocket)

        # Store metadata
        self.connection_metadata[websocket] = {
            "type": "admin",
            "email": admin_email,
            "connected_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        }

        logger.info(f"Admin WebSocket connected: {admin_email}")

        # Send connection confirmation
        await self.send_to_websocket(websocket, {
            "type": NotificationType.SYSTEM_MESSAGE,
            "message": "Connected to WeedGo admin notification service",
            "admin": True,
            "timestamp": datetime.utcnow().isoformat()
        })

    def disconnect(self, websocket: WebSocket):
        """
        Disconnect a websocket

        Args:
            websocket: WebSocket to disconnect
        """
        # Remove from all collections
        self.all_connections.discard(websocket)
        self.admin_connections.discard(websocket)

        # Remove from user connections
        identifier = None
        for user_id, connections in self.user_connections.items():
            if websocket in connections:
                connections.discard(websocket)
                identifier = user_id
                if not connections:
                    del self.user_connections[user_id]
                break

        # Remove metadata
        metadata = self.connection_metadata.pop(websocket, {})
        conn_type = metadata.get('type', 'unknown')

        logger.info(f"WebSocket disconnected: {conn_type} - {identifier or metadata.get('email', 'unknown')}")

    async def send_to_websocket(self, websocket: WebSocket, data: dict):
        """
        Send data to a specific websocket

        Args:
            websocket: Target websocket
            data: Data to send
        """
        try:
            await websocket.send_json(data)

            # Update last activity
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]["last_activity"] = datetime.utcnow().isoformat()

        except Exception as e:
            logger.error(f"Error sending to websocket: {e}")
            self.disconnect(websocket)

    async def send_to_user(self, identifier: str, data: dict):
        """
        Send data to all connections for a specific user

        Args:
            identifier: User identifier (email or session_id)
            data: Data to send
        """
        if identifier not in self.user_connections:
            logger.debug(f"No active connections for user: {identifier}")
            return

        connections = list(self.user_connections[identifier])  # Copy to avoid modification during iteration

        for websocket in connections:
            await self.send_to_websocket(websocket, data)

        logger.info(f"Sent notification to user {identifier} ({len(connections)} connections)")

    async def send_to_admins(self, data: dict):
        """
        Send data to all admin connections

        Args:
            data: Data to send
        """
        if not self.admin_connections:
            logger.debug("No active admin connections")
            return

        connections = list(self.admin_connections)  # Copy to avoid modification during iteration

        for websocket in connections:
            await self.send_to_websocket(websocket, data)

        logger.info(f"Sent notification to admins ({len(connections)} connections)")

    async def broadcast(self, data: dict):
        """
        Broadcast data to all connections

        Args:
            data: Data to send
        """
        if not self.all_connections:
            logger.debug("No active connections for broadcast")
            return

        connections = list(self.all_connections)  # Copy to avoid modification during iteration

        for websocket in connections:
            await self.send_to_websocket(websocket, data)

        logger.info(f"Broadcast notification to all connections ({len(connections)})")

    async def send_verification_code(self, email: str, code: str, verification_id: str):
        """
        Send verification code to user via WebSocket

        Args:
            email: User email
            code: Verification code
            verification_id: Verification session ID
        """
        notification = {
            "type": NotificationType.VERIFICATION_CODE,
            "code": code,
            "verification_id": verification_id,
            "email": email,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Your verification code is: {code}"
        }

        await self.send_to_user(email, notification)

    async def send_signup_progress(self, identifier: str, step: str, message: str, data: Optional[dict] = None):
        """
        Send signup progress update to user

        Args:
            identifier: User identifier (email or session_id)
            step: Current signup step
            message: Progress message
            data: Optional additional data
        """
        notification = {
            "type": NotificationType.SIGNUP_PROGRESS,
            "step": step,
            "message": message,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.send_to_user(identifier, notification)

    async def notify_admin_new_review(self, tenant_id: str, store_name: str, license_number: str, email: str):
        """
        Notify admins of new account pending review

        Args:
            tenant_id: Tenant ID
            store_name: Store name
            license_number: CRSA license number
            email: Contact email
        """
        notification = {
            "type": NotificationType.ADMIN_NEW_REVIEW,
            "tenant_id": tenant_id,
            "store_name": store_name,
            "license_number": license_number,
            "email": email,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"New account pending review: {store_name}"
        }

        await self.send_to_admins(notification)

    async def notify_admin_review_update(self, tenant_id: str, action: str, admin_email: str):
        """
        Notify admins of review action (approval/rejection)

        Args:
            tenant_id: Tenant ID
            action: Action taken (approved/rejected)
            admin_email: Admin who performed action
        """
        notification = {
            "type": NotificationType.ADMIN_REVIEW_UPDATE,
            "tenant_id": tenant_id,
            "action": action,
            "admin_email": admin_email,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Account {action} by {admin_email}"
        }

        await self.send_to_admins(notification)

    def get_connection_stats(self) -> dict:
        """
        Get connection statistics

        Returns:
            Dictionary with connection counts
        """
        return {
            "total_connections": len(self.all_connections),
            "user_connections": sum(len(conns) for conns in self.user_connections.values()),
            "unique_users": len(self.user_connections),
            "admin_connections": len(self.admin_connections),
            "active_users": list(self.user_connections.keys())
        }


# Global singleton instance
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """Get or create connection manager singleton"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager
