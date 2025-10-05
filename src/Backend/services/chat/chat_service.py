"""
Core ChatService implementation following SOLID principles.

This service orchestrates all chat operations by coordinating between
the agent pool, session management, history tracking, and context management.
"""

import logging
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime

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
    ProductModel,
    QuickActionModel,
    ResponseMetadata,
    SessionCreateRequest,
    SessionUpdateRequest
)

logger = logging.getLogger(__name__)


class ChatService(IChatProcessor, ISessionManager):
    """
    Unified chat service implementing clean architecture principles.

    This service acts as the single source of truth for all chat operations,
    coordinating between various subsystems while maintaining separation of concerns.
    """

    def __init__(
        self,
        agent_pool_adapter: IAgentPoolAdapter,
        history_provider: IHistoryProvider,
        context_manager: IContextManager
    ):
        """
        Initialize ChatService with dependencies.

        Args:
            agent_pool_adapter: Adapter for agent pool interactions
            history_provider: Provider for conversation history
            context_manager: Manager for conversation context
        """
        self.agent_pool = agent_pool_adapter
        self.history = history_provider
        self.context = context_manager
        self._sessions: Dict[str, SessionModel] = {}
        logger.info("ChatService initialized with dependency injection")

    # ============================================================
    # IChatProcessor Implementation
    # ============================================================

    async def process_message(
        self,
        message: str,
        session_id: str,
        user_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a chat message and return structured response.

        This is the main entry point for all chat interactions, handling:
        - Message validation
        - Context retrieval
        - Agent pool interaction
        - History persistence
        - Response formatting

        Args:
            message: User's message text
            session_id: Session identifier
            user_id: Optional user identifier
            **kwargs: Additional context (store_id, language, etc.)

        Returns:
            Dict containing response data in ChatResponse format
        """
        try:
            start_time = datetime.utcnow()

            # Validate session exists
            if session_id not in self._sessions:
                logger.warning(f"Session {session_id} not found, creating new session")
                session_id = await self.create_session(
                    user_id=user_id,
                    **kwargs
                )

            session = self._sessions[session_id]

            # Get conversation context
            context_data = await self.context.get_context(
                session_id=session_id,
                max_messages=kwargs.get("max_messages", 10)
            )

            # Build complete request
            request_data = {
                "message": message,
                "session_id": session_id,
                "user_id": user_id or session.user_id,
                "store_id": kwargs.get("store_id", session.store_id),
                "language": kwargs.get("language", session.language),
                "agent_id": session.agent_id,
                "personality_id": session.personality_id,
                "use_tools": kwargs.get("use_tools", True),
                "use_context": kwargs.get("use_context", True),
                "max_tokens": kwargs.get("max_tokens", 500)
            }

            # Generate response through agent pool
            logger.info(f"Processing message for session {session_id} with agent {session.agent_id}/{session.personality_id}")
            response_data = await self.agent_pool.generate_with_agent_pool(**request_data)

            # Calculate response time
            response_time = (datetime.utcnow() - start_time).total_seconds()

            # Structure response
            structured_response = self._structure_response(
                response_data=response_data,
                session_id=session_id,
                response_time=response_time
            )

            # Save to history
            await self.history.save_message(
                session_id=session_id,
                user_id=user_id,
                user_message=message,
                assistant_response=structured_response["text"],
                metadata=structured_response.get("metadata", {})
            )

            # Update session activity
            session.updated_at = datetime.utcnow()
            session.message_count += 1

            logger.info(f"Message processed successfully in {response_time:.2f}s")
            return structured_response

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            raise

    # ============================================================
    # ISessionManager Implementation
    # ============================================================

    async def create_session(
        self,
        agent_id: str = "dispensary",
        personality_id: str = "marcel",
        user_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Create a new chat session.

        Args:
            agent_id: Agent type to use
            personality_id: Personality variant
            user_id: Optional user identifier
            **kwargs: Additional session metadata

        Returns:
            session_id: Unique session identifier
        """
        try:
            session_id = str(uuid.uuid4())

            # Create session model
            session = SessionModel(
                session_id=session_id,
                user_id=user_id,
                agent_id=agent_id,
                personality_id=personality_id,
                store_id=kwargs.get("store_id"),
                language=kwargs.get("language", "en"),
                metadata=kwargs.get("metadata", {})
            )

            # Store in memory
            self._sessions[session_id] = session

            # Initialize context
            await self.context.update_context(
                session_id=session_id,
                context_updates={
                    "agent_id": agent_id,
                    "personality_id": personality_id,
                    "created_at": session.created_at.isoformat()
                }
            )

            logger.info(f"Created session {session_id} with agent {agent_id}/{personality_id}")
            return session_id

        except Exception as e:
            logger.error(f"Error creating session: {str(e)}", exc_info=True)
            raise

    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve session details.

        Args:
            session_id: Session identifier

        Returns:
            Dict containing session data
        """
        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self._sessions[session_id]
        return session.model_dump()

    async def update_session(
        self,
        session_id: str,
        agent_id: Optional[str] = None,
        personality_id: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        Update session settings.

        Args:
            session_id: Session identifier
            agent_id: New agent type (if changing)
            personality_id: New personality (if changing)
            **kwargs: Other settings to update

        Returns:
            bool: Success status
        """
        try:
            if session_id not in self._sessions:
                raise ValueError(f"Session {session_id} not found")

            session = self._sessions[session_id]

            # Update agent/personality if provided
            if agent_id:
                old_agent = session.agent_id
                session.agent_id = agent_id
                logger.info(f"Updated session {session_id} agent: {old_agent} -> {agent_id}")

                # Switch agent in agent pool
                await self.agent_pool.switch_agent(
                    session_id=session_id,
                    agent_id=agent_id,
                    personality_id=personality_id or session.personality_id
                )

            if personality_id:
                old_personality = session.personality_id
                session.personality_id = personality_id
                logger.info(f"Updated session {session_id} personality: {old_personality} -> {personality_id}")

            # Update other fields
            if "store_id" in kwargs:
                session.store_id = kwargs["store_id"]
            if "language" in kwargs:
                session.language = kwargs["language"]
            if "metadata" in kwargs:
                session.metadata.update(kwargs["metadata"])

            session.updated_at = datetime.utcnow()

            # Update context
            await self.context.update_context(
                session_id=session_id,
                context_updates={
                    "agent_id": session.agent_id,
                    "personality_id": session.personality_id,
                    "updated_at": session.updated_at.isoformat()
                }
            )

            return True

        except Exception as e:
            logger.error(f"Error updating session: {str(e)}", exc_info=True)
            return False

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and cleanup resources.

        Args:
            session_id: Session identifier

        Returns:
            bool: Success status
        """
        try:
            if session_id not in self._sessions:
                logger.warning(f"Session {session_id} not found for deletion")
                return False

            # Mark session as inactive
            session = self._sessions[session_id]
            session.is_active = False

            # Clear context
            await self.context.clear_context(session_id)

            # Remove from memory
            del self._sessions[session_id]

            logger.info(f"Deleted session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting session: {str(e)}", exc_info=True)
            return False

    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List sessions, optionally filtered by user.

        Args:
            user_id: Filter by user ID
            active_only: Only return active sessions

        Returns:
            List of session dictionaries
        """
        sessions = []

        for session in self._sessions.values():
            # Apply filters
            if user_id and session.user_id != user_id:
                continue
            if active_only and not session.is_active:
                continue

            sessions.append(session.model_dump())

        return sessions

    # ============================================================
    # Private Helper Methods
    # ============================================================

    def _structure_response(
        self,
        response_data: Dict[str, Any],
        session_id: str,
        response_time: float
    ) -> Dict[str, Any]:
        """
        Structure raw agent pool response into ChatResponse format.

        Args:
            response_data: Raw response from agent pool
            session_id: Session identifier
            response_time: Response generation time

        Returns:
            Structured response dict
        """
        # Extract text response
        text = response_data.get("text", "")

        # Extract products
        products = []
        raw_products = response_data.get("products") or []
        for prod in raw_products:
            try:
                # Handle multiple image field naming conventions
                # API returns 'image', but model expects 'image_url'
                image_url = (
                    prod.get("image_url") or
                    prod.get("image") or
                    (prod.get("images")[0] if prod.get("images") and len(prod.get("images")) > 0 else None)
                )

                product_model = ProductModel(
                    id=prod.get("id", str(uuid.uuid4())),
                    name=prod.get("name", "Unknown"),
                    sku=prod.get("sku", ""),
                    type=prod.get("type", ""),
                    category=prod.get("category"),
                    price=float(prod.get("price", 0)),
                    thc=prod.get("thc"),
                    cbd=prod.get("cbd"),
                    description=prod.get("description"),
                    image_url=image_url,
                    in_stock=prod.get("in_stock", True),
                    quantity_available=prod.get("quantity_available", 0)
                )
                products.append(product_model.model_dump())
            except Exception as e:
                logger.warning(f"Failed to structure product: {str(e)}")

        # Extract quick actions
        quick_actions = []
        raw_actions = response_data.get("quick_actions") or []
        for action in raw_actions:
            try:
                action_model = QuickActionModel(
                    label=action.get("label", ""),
                    action=action.get("action", ""),
                    data=action.get("data")
                )
                quick_actions.append(action_model.model_dump())
            except Exception as e:
                logger.warning(f"Failed to structure quick action: {str(e)}")

        # Create metadata
        metadata = ResponseMetadata(
            model=response_data.get("model", "unknown"),
            tokens_used=response_data.get("tokens_used", 0),
            prompt_tokens=response_data.get("prompt_tokens", 0),
            completion_tokens=response_data.get("completion_tokens", 0),
            response_time=response_time,
            tool_calls=response_data.get("tool_calls", []),
            intent=response_data.get("intent"),
            confidence=response_data.get("confidence")
        )

        # Create structured response
        response = ChatResponse(
            text=text,
            products=products,
            quick_actions=quick_actions,
            metadata=metadata.model_dump(),
            session_id=session_id
        )

        return response.model_dump()
