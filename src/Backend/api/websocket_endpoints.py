"""
WebSocket API Endpoints
Real-time notification endpoints for users and admins
"""

import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException, status
from fastapi.security import HTTPBearer

from services.websocket_manager import get_connection_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])
security = HTTPBearer()


# =====================================================
# Authentication Helpers
# =====================================================

async def verify_admin_token(token: str) -> Optional[dict]:
    """
    Verify admin JWT token for WebSocket connection

    Args:
        token: JWT token from query parameter

    Returns:
        User dict if valid, None otherwise
    """
    try:
        from core.authentication import get_auth

        auth = get_auth()
        payload = auth.verify_token(token)

        if not payload:
            return None

        # Check admin role
        allowed_roles = ['super_admin', 'tenant_admin', 'admin', 'superadmin']
        if payload.get('role') not in allowed_roles:
            return None

        return {
            'user_id': payload.get('user_id'),
            'email': payload.get('email'),
            'role': payload.get('role'),
            'first_name': payload.get('first_name'),
            'last_name': payload.get('last_name')
        }

    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None


# =====================================================
# WebSocket Endpoints
# =====================================================

@router.websocket("/notifications/user")
async def user_notifications_websocket(
    websocket: WebSocket,
    identifier: str = Query(..., description="Email or session_id")
):
    """
    WebSocket endpoint for user notifications

    Users connect with their email or session_id to receive:
    - Verification code notifications
    - Signup progress updates
    - System messages

    Query Parameters:
        identifier: Email address or session_id

    Example:
        ws://localhost:5024/ws/notifications/user?identifier=user@store.com
    """
    manager = get_connection_manager()

    try:
        await manager.connect_user(websocket, identifier)

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Receive messages (primarily for keep-alive)
                data = await websocket.receive_text()

                # Echo back as heartbeat
                await websocket.send_json({
                    "type": "heartbeat",
                    "message": "Connection active",
                    "received": data
                })

            except WebSocketDisconnect:
                logger.info(f"User {identifier} disconnected")
                break
            except Exception as e:
                logger.error(f"Error in user websocket loop: {e}")
                break

    except Exception as e:
        logger.error(f"Error establishing user websocket: {e}")

    finally:
        manager.disconnect(websocket)


@router.websocket("/notifications/admin")
async def admin_notifications_websocket(
    websocket: WebSocket,
    token: str = Query(..., description="JWT authentication token")
):
    """
    WebSocket endpoint for admin notifications

    Admins connect with JWT token to receive:
    - New account review notifications
    - Review action updates (approvals/rejections)
    - System messages

    Query Parameters:
        token: JWT authentication token

    Example:
        ws://localhost:5024/ws/notifications/admin?token=eyJhbGc...
    """
    manager = get_connection_manager()

    # Verify admin token
    user = await verify_admin_token(token)
    if not user:
        logger.warning("Invalid admin token for WebSocket connection")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        await manager.connect_admin(websocket, user['email'])

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Receive messages (primarily for keep-alive)
                data = await websocket.receive_text()

                # Echo back as heartbeat
                await websocket.send_json({
                    "type": "heartbeat",
                    "message": "Connection active",
                    "admin": True,
                    "received": data
                })

            except WebSocketDisconnect:
                logger.info(f"Admin {user['email']} disconnected")
                break
            except Exception as e:
                logger.error(f"Error in admin websocket loop: {e}")
                break

    except Exception as e:
        logger.error(f"Error establishing admin websocket: {e}")

    finally:
        manager.disconnect(websocket)


@router.websocket("/notifications/public")
async def public_notifications_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for public system notifications

    No authentication required. Receives only:
    - System-wide announcements
    - Maintenance notifications
    - General status updates

    Example:
        ws://localhost:5024/ws/notifications/public
    """
    manager = get_connection_manager()

    try:
        await websocket.accept()

        logger.info("Public WebSocket connected")

        # Send welcome message
        await websocket.send_json({
            "type": "system_message",
            "message": "Connected to WeedGo public notification service"
        })

        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_text()

                # Echo back as heartbeat
                await websocket.send_json({
                    "type": "heartbeat",
                    "message": "Connection active",
                    "received": data
                })

            except WebSocketDisconnect:
                logger.info("Public WebSocket disconnected")
                break
            except Exception as e:
                logger.error(f"Error in public websocket loop: {e}")
                break

    except Exception as e:
        logger.error(f"Error establishing public websocket: {e}")

    finally:
        # No need to track public connections in manager
        pass


# =====================================================
# Connection Status Endpoint
# =====================================================

@router.get("/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics

    Returns:
        Connection counts and active users
    """
    manager = get_connection_manager()
    stats = manager.get_connection_stats()

    return {
        "success": True,
        "stats": stats
    }
