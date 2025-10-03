"""
Unified Chat Service Module

This module provides a clean, SOLID-compliant architecture for chat operations.
All chat endpoints should route through the ChatService for consistency.

Quick Start:
    from services.chat import initialize_chat_service, get_chat_service
    from services.agent_pool_manager import get_agent_pool

    # Initialize once at startup
    agent_pool = get_agent_pool()
    initialize_chat_service(agent_pool)

    # Use in endpoints
    chat_service = get_chat_service()
    response = await chat_service.process_message(
        message="I want sativa pre-rolls",
        session_id=session_id
    )
"""

from .interfaces import (
    IChatProcessor,
    ISessionManager,
    IHistoryProvider,
    IContextManager,
    IAgentPoolAdapter
)
from .models import (
    ChatRequest,
    ChatResponse,
    SessionModel,
    MessageModel,
    WebSocketMessageType,
    ProductModel,
    QuickActionModel,
    ResponseMetadata,
    SessionCreateRequest,
    SessionUpdateRequest,
    StreamChunk,
    ErrorResponse
)
from .chat_service import ChatService
from .adapters import (
    AgentPoolAdapter,
    InMemoryHistoryProvider,
    InMemoryContextManager
)
from .container import (
    ChatServiceContainer,
    get_container,
    initialize_chat_service,
    get_chat_service
)

__all__ = [
    # Interfaces
    "IChatProcessor",
    "ISessionManager",
    "IHistoryProvider",
    "IContextManager",
    "IAgentPoolAdapter",
    # Models
    "ChatRequest",
    "ChatResponse",
    "SessionModel",
    "MessageModel",
    "WebSocketMessageType",
    "ProductModel",
    "QuickActionModel",
    "ResponseMetadata",
    "SessionCreateRequest",
    "SessionUpdateRequest",
    "StreamChunk",
    "ErrorResponse",
    # Core Service
    "ChatService",
    # Adapters
    "AgentPoolAdapter",
    "InMemoryHistoryProvider",
    "InMemoryContextManager",
    # Container & Factory
    "ChatServiceContainer",
    "get_container",
    "initialize_chat_service",
    "get_chat_service",
]
