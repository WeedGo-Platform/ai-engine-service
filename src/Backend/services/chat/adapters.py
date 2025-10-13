"""
Adapter implementations connecting existing systems to new interfaces.

These adapters bridge the gap between the legacy agent pool system
and the new clean architecture, following the Adapter pattern.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from .interfaces import (
    IAgentPoolAdapter,
    IHistoryProvider,
    IContextManager
)

logger = logging.getLogger(__name__)


class AgentPoolAdapter(IAgentPoolAdapter):
    """
    Adapter for the existing agent pool system.

    This adapter wraps the legacy agent_pool_manager to conform to
    our new interface, allowing us to gradually migrate without breaking changes.
    """

    def __init__(self, agent_pool_manager):
        """
        Initialize adapter with existing agent pool manager.

        Args:
            agent_pool_manager: The legacy AgentPoolManager instance
        """
        self.agent_pool = agent_pool_manager
        logger.info("AgentPoolAdapter initialized")

    async def generate_with_agent_pool(
        self,
        session_id: str,
        message: str,
        user_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate response using the agent pool system.

        This method adapts the legacy agent pool interface to our new contract.

        Args:
            session_id: Session identifier
            message: User's message
            user_id: Optional user identifier
            **kwargs: Additional parameters

        Returns:
            Dict containing response data with structured format
        """
        try:
            logger.debug(f"Generating message for session {session_id}")

            # Check if session exists in agent pool
            if session_id not in self.agent_pool.sessions:
                # Create session if it doesn't exist
                # Note: store_id and language go in metadata, not as direct parameters
                metadata = {
                    "store_id": kwargs.get("store_id"),
                    "language": kwargs.get("language", "en")
                }
                await self.agent_pool.create_session(
                    session_id=session_id,
                    agent_id=kwargs.get("agent_id", "dispensary"),
                    personality_id=kwargs.get("personality_id", "marcel"),
                    user_id=user_id,
                    metadata=metadata
                )

            # Use the agent pool's generate_message_with_products method
            # This is the correct path that includes product search
            response_data = await self.agent_pool.generate_message_with_products(
                session_id=session_id,
                message=message,
                user_id=user_id,
                store_id=kwargs.get("store_id"),
                language=kwargs.get("language", "en")
            )

            logger.debug(f"Agent pool returned response for session {session_id}")
            return response_data

        except Exception as e:
            logger.error(f"Error in agent pool adapter: {str(e)}", exc_info=True)
            raise

    async def switch_agent(
        self,
        session_id: str,
        agent_id: str,
        personality_id: Optional[str] = None
    ) -> bool:
        """
        Switch to a different agent for the session.

        Args:
            session_id: Session identifier
            agent_id: New agent identifier
            personality_id: New personality identifier

        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Switching agent for session {session_id} to {agent_id}/{personality_id}")

            # CRITICAL FIX: Check if session exists in agent pool first
            # The chat_service creates a session in its own memory, but the agent pool
            # maintains a separate session store. We need to ensure the session exists
            # in the agent pool before trying to update it.
            if session_id not in self.agent_pool.sessions:
                logger.warning(f"Session {session_id} not found in agent pool, creating it first")
                # Create the session in agent pool with the target agent/personality
                await self.agent_pool.create_session(
                    session_id=session_id,
                    agent_id=agent_id,
                    personality_id=personality_id or "marcel",
                    user_id=None,  # Will be set later if needed
                    metadata={}
                )
                logger.info(f"Created agent pool session {session_id} with {agent_id}/{personality_id}")
                return True

            # Use agent pool's switch_agent method (correct method name)
            success = await self.agent_pool.switch_agent(
                session_id=session_id,
                new_agent_id=agent_id,  # Parameter name is new_agent_id, not agent_id
                personality_id=personality_id
            )

            if success:
                logger.info(f"Successfully switched session {session_id} to {agent_id}/{personality_id}")
            else:
                logger.error(f"Failed to switch session {session_id} to {agent_id}/{personality_id}")

            return success

        except Exception as e:
            logger.error(f"Error switching agent: {str(e)}", exc_info=True)
            return False


class InMemoryHistoryProvider(IHistoryProvider):
    """
    In-memory implementation of history provider.

    This is a temporary implementation for MVP. In production, this should
    be replaced with a database-backed implementation (PostgreSQL, Redis, etc.)
    """

    def __init__(self):
        """Initialize in-memory storage"""
        self._history: Dict[str, List[Dict[str, Any]]] = {}  # session_id -> messages
        self._user_sessions: Dict[str, List[str]] = {}  # user_id -> session_ids
        logger.info("InMemoryHistoryProvider initialized")

    async def get_history(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get user's conversation history across all sessions.

        Args:
            user_id: User identifier
            limit: Maximum messages to return
            offset: Pagination offset

        Returns:
            List of message dictionaries with timestamps
        """
        try:
            # Get all sessions for user
            session_ids = self._user_sessions.get(user_id, [])

            # Collect all messages from all sessions
            all_messages = []
            for session_id in session_ids:
                messages = self._history.get(session_id, [])
                all_messages.extend(messages)

            # Sort by timestamp (most recent first)
            all_messages.sort(key=lambda m: m.get("timestamp", ""), reverse=True)

            # Apply pagination
            return all_messages[offset:offset + limit]

        except Exception as e:
            logger.error(f"Error getting history: {str(e)}", exc_info=True)
            return []

    async def get_session_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a specific session.

        Args:
            session_id: Session identifier
            limit: Maximum messages to return

        Returns:
            List of message dictionaries in chronological order
        """
        try:
            messages = self._history.get(session_id, [])

            # Return most recent messages in chronological order
            return messages[-limit:] if len(messages) > limit else messages

        except Exception as e:
            logger.error(f"Error getting session history: {str(e)}", exc_info=True)
            return []

    async def save_message(
        self,
        session_id: str,
        user_id: Optional[str],
        user_message: str,
        assistant_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save a message exchange to history.

        Args:
            session_id: Session identifier
            user_id: User identifier (if available)
            user_message: User's message
            assistant_response: Assistant's response
            metadata: Additional metadata

        Returns:
            bool: Success status
        """
        try:
            timestamp = datetime.utcnow().isoformat()

            # Create user message entry
            user_msg = {
                "role": "user",
                "content": user_message,
                "timestamp": timestamp,
                "session_id": session_id,
                "user_id": user_id
            }

            # Create assistant message entry
            assistant_msg = {
                "role": "assistant",
                "content": assistant_response,
                "timestamp": timestamp,
                "session_id": session_id,
                "metadata": metadata or {}
            }

            # Initialize session history if needed
            if session_id not in self._history:
                self._history[session_id] = []

            # Append messages
            self._history[session_id].append(user_msg)
            self._history[session_id].append(assistant_msg)

            # Track user sessions
            if user_id:
                if user_id not in self._user_sessions:
                    self._user_sessions[user_id] = []
                if session_id not in self._user_sessions[user_id]:
                    self._user_sessions[user_id].append(session_id)

            logger.debug(f"Saved message to history for session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving message: {str(e)}", exc_info=True)
            return False


class InMemoryContextManager(IContextManager):
    """
    In-memory implementation of context manager.

    Manages conversation context and user preferences. Like the history provider,
    this should be replaced with a proper storage backend in production.
    """

    def __init__(self):
        """Initialize in-memory storage"""
        self._context: Dict[str, Dict[str, Any]] = {}  # session_id -> context
        logger.info("InMemoryContextManager initialized")

    async def get_context(
        self,
        session_id: str,
        max_messages: int = 10
    ) -> Dict[str, Any]:
        """
        Get conversation context for a session.

        Args:
            session_id: Session identifier
            max_messages: Maximum recent messages to include

        Returns:
            Dict containing context data
        """
        try:
            context = self._context.get(session_id, {})

            return {
                "messages": context.get("messages", [])[-max_messages:],
                "user_preferences": context.get("user_preferences", {}),
                "session_metadata": context.get("session_metadata", {})
            }

        except Exception as e:
            logger.error(f"Error getting context: {str(e)}", exc_info=True)
            return {"messages": [], "user_preferences": {}, "session_metadata": {}}

    async def update_context(
        self,
        session_id: str,
        context_updates: Dict[str, Any]
    ) -> bool:
        """
        Update session context with new information.

        Args:
            session_id: Session identifier
            context_updates: Context fields to update

        Returns:
            bool: Success status
        """
        try:
            if session_id not in self._context:
                self._context[session_id] = {
                    "messages": [],
                    "user_preferences": {},
                    "session_metadata": {}
                }

            # Update context fields
            context = self._context[session_id]

            # Handle messages separately to append rather than replace
            if "messages" in context_updates:
                context["messages"].extend(context_updates["messages"])
                del context_updates["messages"]

            # Update other fields
            if "user_preferences" in context_updates:
                context["user_preferences"].update(context_updates["user_preferences"])
                del context_updates["user_preferences"]

            # Merge remaining updates into session_metadata
            context["session_metadata"].update(context_updates)

            logger.debug(f"Updated context for session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating context: {str(e)}", exc_info=True)
            return False

    async def clear_context(self, session_id: str) -> bool:
        """
        Clear conversation context for a session.

        Args:
            session_id: Session identifier

        Returns:
            bool: Success status
        """
        try:
            if session_id in self._context:
                del self._context[session_id]
                logger.debug(f"Cleared context for session {session_id}")

            return True

        except Exception as e:
            logger.error(f"Error clearing context: {str(e)}", exc_info=True)
            return False
