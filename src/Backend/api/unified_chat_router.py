"""
Unified REST API Router for Chat Operations.

This router consolidates all chat-related REST endpoints into a single,
consistent API following RESTful principles and SOLID design.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Body, status
from fastapi.responses import StreamingResponse
import json

from services.chat import (
    get_chat_service,
    ChatRequest,
    ChatResponse,
    SessionCreateRequest,
    SessionUpdateRequest,
    ErrorResponse
)
from services.chat.models import WebSocketMessageType

logger = logging.getLogger(__name__)

# Create router with prefix and tags
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


# ============================================================
# Message Endpoints
# ============================================================

@router.post("/message", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def send_message(request: ChatRequest = Body(...)):
    """
    Send a chat message and receive a response.

    This is the primary REST endpoint for chat interactions. It provides
    a consistent interface regardless of the underlying agent/personality.

    **Request Body:**
    - message: User's message text (required)
    - session_id: Session identifier (optional, creates new session if not provided)
    - user_id: User identifier (optional)
    - store_id: Store context (optional)
    - language: Message language code (default: "en")
    - agent_id: Agent type to use (default: "dispensary")
    - personality_id: Personality variant (default: "marcel")
    - use_tools: Enable tool usage (default: true)
    - use_context: Include conversation context (default: true)
    - max_tokens: Maximum response tokens (default: 500)

    **Response:**
    - text: Assistant's response
    - products: List of product recommendations
    - quick_actions: List of quick action buttons
    - metadata: Response metadata (model, tokens, time, etc.)
    - session_id: Session identifier for subsequent messages

    **Example:**
    ```json
    {
        "message": "I want sativa pre-rolls",
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "language": "en"
    }
    ```
    """
    try:
        chat_service = get_chat_service()

        # If no session_id provided, create a new session
        if not request.session_id:
            logger.info("No session_id provided, creating new session")
            session_id = await chat_service.create_session(
                agent_id=request.agent_id,
                personality_id=request.personality_id,
                user_id=request.user_id,
                store_id=request.store_id,
                language=request.language
            )
        else:
            session_id = request.session_id

        # Process message through ChatService
        response_data = await chat_service.process_message(
            message=request.message,
            session_id=session_id,
            user_id=request.user_id,
            store_id=request.store_id,
            language=request.language,
            use_tools=request.use_tools,
            use_context=request.use_context,
            max_tokens=request.max_tokens
        )

        return response_data

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message"
        )


@router.post("/stream")
async def send_message_stream(request: ChatRequest = Body(...)):
    """
    Send a chat message and receive a streaming response.

    This endpoint provides Server-Sent Events (SSE) streaming for real-time
    response generation. Useful for displaying responses as they're generated.

    **Response Format (SSE):**
    Each event is a JSON object with:
    - type: "text" | "product" | "action" | "metadata" | "done"
    - content: Event-specific content
    - session_id: Session identifier
    - chunk_id: Sequence number

    **Example Stream:**
    ```
    data: {"type": "text", "content": "I found some", "chunk_id": 0}
    data: {"type": "text", "content": " great sativa pre-rolls!", "chunk_id": 1}
    data: {"type": "product", "content": {...}, "chunk_id": 2}
    data: {"type": "done", "content": null, "chunk_id": 3}
    ```
    """
    try:
        async def generate_stream():
            """Generator for SSE streaming"""
            try:
                chat_service = get_chat_service()

                # Create session if needed
                if not request.session_id:
                    session_id = await chat_service.create_session(
                        agent_id=request.agent_id,
                        personality_id=request.personality_id,
                        user_id=request.user_id,
                        store_id=request.store_id,
                        language=request.language
                    )
                else:
                    session_id = request.session_id

                # For now, get full response and stream it
                # TODO: Implement true streaming at the LLM level
                response_data = await chat_service.process_message(
                    message=request.message,
                    session_id=session_id,
                    user_id=request.user_id,
                    store_id=request.store_id,
                    language=request.language,
                    use_tools=request.use_tools,
                    use_context=request.use_context,
                    max_tokens=request.max_tokens
                )

                chunk_id = 0

                # Stream text response
                text = response_data.get("text", "")
                words = text.split()
                for i in range(0, len(words), 3):  # Stream 3 words at a time
                    chunk = " ".join(words[i:i+3])
                    if i + 3 < len(words):
                        chunk += " "
                    event = {
                        "type": "text",
                        "content": chunk,
                        "session_id": session_id,
                        "chunk_id": chunk_id
                    }
                    yield f"data: {json.dumps(event)}\n\n"
                    chunk_id += 1

                # Stream products
                for product in response_data.get("products", []):
                    event = {
                        "type": "product",
                        "content": product,
                        "session_id": session_id,
                        "chunk_id": chunk_id
                    }
                    yield f"data: {json.dumps(event)}\n\n"
                    chunk_id += 1

                # Stream quick actions
                for action in response_data.get("quick_actions", []):
                    event = {
                        "type": "action",
                        "content": action,
                        "session_id": session_id,
                        "chunk_id": chunk_id
                    }
                    yield f"data: {json.dumps(event)}\n\n"
                    chunk_id += 1

                # Stream metadata
                event = {
                    "type": "metadata",
                    "content": response_data.get("metadata", {}),
                    "session_id": session_id,
                    "chunk_id": chunk_id
                }
                yield f"data: {json.dumps(event)}\n\n"
                chunk_id += 1

                # Send done event
                event = {
                    "type": "done",
                    "content": None,
                    "session_id": session_id,
                    "chunk_id": chunk_id
                }
                yield f"data: {json.dumps(event)}\n\n"

            except Exception as e:
                logger.error(f"Error in stream: {str(e)}", exc_info=True)
                error_event = {
                    "type": "error",
                    "content": str(e),
                    "session_id": request.session_id or "unknown",
                    "chunk_id": -1
                }
                yield f"data: {json.dumps(error_event)}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except Exception as e:
        logger.error(f"Error setting up stream: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start streaming"
        )


# ============================================================
# Session Management Endpoints
# ============================================================

@router.post("/sessions", status_code=status.HTTP_201_CREATED)
async def create_session(request: SessionCreateRequest = Body(...)):
    """
    Create a new chat session.

    Sessions maintain conversation context and agent/personality configuration
    across multiple message exchanges.

    **Request Body:**
    - agent_id: Initial agent type (default: "dispensary")
    - personality_id: Initial personality (default: "marcel")
    - user_id: User identifier (optional)
    - store_id: Store context (optional)
    - language: Session language (default: "en")
    - metadata: Additional metadata (optional)

    **Response:**
    - session_id: Unique session identifier
    - created_at: Session creation timestamp
    """
    try:
        chat_service = get_chat_service()

        session_id = await chat_service.create_session(
            agent_id=request.agent_id,
            personality_id=request.personality_id,
            user_id=request.user_id,
            store_id=request.store_id,
            language=request.language,
            metadata=request.metadata
        )

        session_data = await chat_service.get_session(session_id)

        return {
            "session_id": session_id,
            "created_at": session_data["created_at"],
            "agent_id": session_data["agent_id"],
            "personality_id": session_data["personality_id"]
        }

    except Exception as e:
        logger.error(f"Error creating session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session"
        )


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """
    Get details for a specific session.

    Returns full session metadata including configuration and statistics.
    """
    try:
        chat_service = get_chat_service()
        session_data = await chat_service.get_session(session_id)
        return session_data

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    except Exception as e:
        logger.error(f"Error getting session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session"
        )


@router.patch("/sessions/{session_id}")
async def update_session(
    session_id: str,
    request: SessionUpdateRequest = Body(...)
):
    """
    Update session configuration.

    Allows hot-swapping agent/personality mid-conversation and updating
    other session settings.

    **Request Body:**
    - agent_id: New agent type (optional)
    - personality_id: New personality (optional)
    - store_id: New store context (optional)
    - language: New language (optional)
    - metadata: Metadata updates (optional)
    """
    try:
        chat_service = get_chat_service()

        success = await chat_service.update_session(
            session_id=session_id,
            agent_id=request.agent_id,
            personality_id=request.personality_id,
            store_id=request.store_id,
            language=request.language,
            metadata=request.metadata
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update session"
            )

        session_data = await chat_service.get_session(session_id)
        return session_data

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update session"
        )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str):
    """
    Delete a session and cleanup resources.

    This marks the session as inactive and clears conversation context.
    """
    try:
        chat_service = get_chat_service()
        success = await chat_service.delete_session(session_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session"
        )


@router.get("/sessions")
async def list_sessions(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    active_only: bool = Query(True, description="Only return active sessions")
):
    """
    List sessions, optionally filtered by user.

    Useful for retrieving all active conversations for a user or
    viewing session history.
    """
    try:
        chat_service = get_chat_service()
        sessions = await chat_service.list_sessions(
            user_id=user_id,
            active_only=active_only
        )

        return {
            "sessions": sessions,
            "total": len(sessions)
        }

    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list sessions"
        )


# ============================================================
# History Endpoints
# ============================================================

@router.get("/history/{user_id}")
async def get_user_history(
    user_id: str,
    limit: int = Query(20, ge=1, le=100, description="Maximum messages to return"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """
    Get conversation history for a user across all sessions.

    Returns messages in reverse chronological order (most recent first).
    """
    try:
        chat_service = get_chat_service()
        history = await chat_service.history.get_history(
            user_id=user_id,
            limit=limit,
            offset=offset
        )

        return {
            "user_id": user_id,
            "messages": history,
            "count": len(history),
            "offset": offset,
            "limit": limit
        }

    except Exception as e:
        logger.error(f"Error getting user history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user history"
        )


@router.get("/sessions/{session_id}/history")
async def get_session_history(
    session_id: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum messages to return")
):
    """
    Get conversation history for a specific session.

    Returns messages in chronological order.
    """
    try:
        chat_service = get_chat_service()
        history = await chat_service.history.get_session_history(
            session_id=session_id,
            limit=limit
        )

        return {
            "session_id": session_id,
            "messages": history,
            "count": len(history)
        }

    except Exception as e:
        logger.error(f"Error getting session history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session history"
        )


# ============================================================
# Health Check & Monitoring
# ============================================================

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint for monitoring.

    Returns service status and configuration.
    """
    try:
        from services.chat import get_container

        container = get_container()
        chat_service = container.get_chat_service()

        return {
            "status": "healthy",
            "service": "unified-chat-api",
            "version": "1.0.0",
            "initialized": chat_service is not None
        }

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return {
            "status": "unhealthy",
            "service": "unified-chat-api",
            "version": "1.0.0",
            "error": str(e)
        }


@router.get("/metrics", status_code=status.HTTP_200_OK)
async def get_metrics():
    """
    Get comprehensive metrics for the chat system.

    Returns metrics including:
    - Active session count
    - Cache performance (if Redis enabled)
    - Cleanup statistics
    - Storage configuration
    """
    try:
        from services.chat import get_container
        from services.chat.container import (
            USE_DATABASE_STORAGE,
            USE_REDIS_CACHE,
            ENABLE_SESSION_CLEANUP
        )

        container = get_container()
        chat_service = container.get_chat_service()

        metrics = {
            "service": "unified-chat-api",
            "version": "1.0.0",
            "storage": {
                "database_enabled": USE_DATABASE_STORAGE,
                "redis_cache_enabled": USE_REDIS_CACHE,
                "type": _get_storage_type()
            },
            "sessions": {
                "active_count": len(chat_service._sessions),
                "cleanup_enabled": ENABLE_SESSION_CLEANUP
            }
        }

        # Add cache metrics if Redis is enabled
        if USE_REDIS_CACHE:
            try:
                from services.chat.redis_cache import RedisCacheContextManager
                context_manager = container.get_context_manager()
                if isinstance(context_manager, RedisCacheContextManager):
                    metrics["cache"] = context_manager.get_cache_metrics()
            except Exception as e:
                logger.warning(f"Failed to get cache metrics: {e}")
                metrics["cache"] = {"error": str(e)}

        # Add cleanup metrics
        cleanup_manager = container.get_cleanup_manager()
        if cleanup_manager:
            metrics["cleanup"] = cleanup_manager.get_metrics()

        return metrics

    except Exception as e:
        logger.error(f"Failed to get metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve metrics"
        )


def _get_storage_type() -> str:
    """Determine current storage configuration"""
    from services.chat.container import USE_DATABASE_STORAGE, USE_REDIS_CACHE

    if USE_DATABASE_STORAGE:
        if USE_REDIS_CACHE:
            return "hybrid (Redis cache + PostgreSQL)"
        return "PostgreSQL"
    return "in-memory"


@router.post("/cache/invalidate/{session_id}", status_code=status.HTTP_200_OK)
async def invalidate_cache(session_id: str):
    """
    Manually invalidate cache for a specific session.

    Useful for forcing a fresh read from database or debugging.
    Only works if Redis cache is enabled.
    """
    try:
        from services.chat import get_container
        from services.chat.redis_cache import RedisCacheContextManager

        container = get_container()
        context_manager = container.get_context_manager()

        if not isinstance(context_manager, RedisCacheContextManager):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Redis cache not enabled"
            )

        await context_manager.invalidate_session(session_id)

        return {
            "message": f"Cache invalidated for session {session_id}",
            "session_id": session_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to invalidate cache: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to invalidate cache"
        )
