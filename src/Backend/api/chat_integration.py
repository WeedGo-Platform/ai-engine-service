"""
Chat Integration Module - Wires unified chat service into existing servers.

This module provides convenience functions to integrate the new unified
chat service into both main_server.py and api_server.py without breaking changes.
"""

import logging
from fastapi import FastAPI, WebSocket
from typing import Optional

from services.chat import initialize_chat_service, get_chat_service
from services.agent_pool_manager import get_agent_pool

from .unified_chat_router import router as unified_router
from .unified_chat_websocket import handle_websocket_connection

logger = logging.getLogger(__name__)


async def initialize_unified_chat_system():
    """
    Initialize the unified chat system with database storage and session cleanup.

    This should be called once at application startup, after the agent pool
    is initialized.

    Example:
        # In main_server.py or api_server.py startup
        agent_pool = get_agent_pool()
        await initialize_unified_chat_system()
    """
    try:
        # Get existing agent pool
        agent_pool = get_agent_pool()

        if not agent_pool:
            logger.error("Agent pool not initialized - cannot initialize chat service")
            raise RuntimeError("Agent pool must be initialized before chat service")

        # Initialize chat service with agent pool
        chat_service = initialize_chat_service(agent_pool)

        # Start session cleanup manager
        from services.chat import get_container
        container = get_container()
        await container.start_cleanup_manager()

        logger.info("✅ Unified chat system initialized successfully")
        logger.info(f"   - ChatService: {chat_service is not None}")
        logger.info(f"   - Agent Pool: {agent_pool is not None}")
        logger.info(f"   - Database Storage: Enabled")
        logger.info(f"   - Session Cleanup: Started")

        return chat_service

    except Exception as e:
        logger.error(f"Failed to initialize unified chat system: {str(e)}", exc_info=True)
        raise


def register_unified_chat_routes(app: FastAPI):
    """
    Register all unified chat routes with a FastAPI application.

    This includes:
    - Unified REST API routes (/api/v1/chat/*)
    - Unified WebSocket endpoint

    Args:
        app: FastAPI application instance

    Example:
        app = FastAPI()
        register_unified_chat_routes(app)
    """
    try:
        # Register unified REST API
        app.include_router(unified_router)
        logger.info("✅ Registered unified REST API routes: /api/v1/chat/*")

        # Register unified WebSocket endpoint
        @app.websocket("/api/v1/chat/ws")
        async def unified_websocket(
            websocket: WebSocket,
            session_id: Optional[str] = None
        ):
            """
            Unified WebSocket endpoint for real-time chat.

            Accepts optional session_id query parameter to resume existing sessions.

            Example:
                ws://localhost:5024/api/v1/chat/ws
                ws://localhost:5024/api/v1/chat/ws?session_id=550e8400-e29b-41d4-a716-446655440000
            """
            await handle_websocket_connection(websocket, session_id)

        logger.info("✅ Registered unified WebSocket endpoint: /api/v1/chat/ws")

        # Log all registered routes
        logger.info("📋 Unified Chat System Routes:")
        logger.info("   REST API:")
        logger.info("     POST   /api/v1/chat/message         - Send message")
        logger.info("     POST   /api/v1/chat/stream          - Stream response")
        logger.info("     POST   /api/v1/chat/sessions        - Create session")
        logger.info("     GET    /api/v1/chat/sessions/{id}   - Get session")
        logger.info("     PATCH  /api/v1/chat/sessions/{id}   - Update session")
        logger.info("     DELETE /api/v1/chat/sessions/{id}   - Delete session")
        logger.info("     GET    /api/v1/chat/sessions        - List sessions")
        logger.info("     GET    /api/v1/chat/history/{user}  - User history")
        logger.info("     GET    /api/v1/chat/sessions/{id}/history - Session history")
        logger.info("     GET    /api/v1/chat/health          - Health check")
        logger.info("     GET    /api/v1/chat/metrics         - System metrics")
        logger.info("")
        logger.info("   WebSocket:")
        logger.info("     WS     /api/v1/chat/ws              - Real-time chat")

    except Exception as e:
        logger.error(f"Failed to register unified chat routes: {str(e)}", exc_info=True)
        raise


def get_unified_chat_status() -> dict:
    """
    Get status information about the unified chat system.

    Returns:
        dict: Status information including initialization state, active connections, etc.
    """
    try:
        from services.chat import get_container
        from .unified_chat_websocket import get_active_connections

        container = get_container()
        chat_service = container.get_chat_service()

        status = {
            "initialized": chat_service is not None,
            "chat_service": {
                "active": chat_service is not None,
                "type": type(chat_service).__name__
            },
            "dependencies": {
                "agent_pool_adapter": container._agent_pool_adapter is not None,
                "history_provider": container._history_provider is not None,
                "context_manager": container._context_manager is not None
            }
        }

        # Add WebSocket connection count if available
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Can't call async from sync context while loop is running
                status["websocket_connections"] = "N/A (async context)"
            else:
                conn_count = loop.run_until_complete(get_active_connections())
                status["websocket_connections"] = conn_count
        except Exception:
            status["websocket_connections"] = "unavailable"

        return status

    except Exception as e:
        logger.error(f"Error getting chat status: {str(e)}", exc_info=True)
        return {
            "initialized": False,
            "error": str(e)
        }


# ============================================================
# Convenience Functions for Migration
# ============================================================

# Migration guide removed - legacy compatibility has been removed
