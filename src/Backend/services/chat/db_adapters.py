"""
PostgreSQL-backed adapter implementations for the unified chat service.

These adapters integrate with the existing DatabaseContextStore infrastructure,
ensuring conversation history and context are persisted to the database.
"""

import logging
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from .interfaces import (
    IAgentPoolAdapter,
    IHistoryProvider,
    IContextManager
)
from services.context.database_store import DatabaseContextStore

logger = logging.getLogger(__name__)


class PostgreSQLHistoryProvider(IHistoryProvider):
    """
    PostgreSQL-backed history provider.

    Stores conversation history in the existing ai_conversations and
    chat_interactions tables, ensuring data persistence and analytics.
    """

    def __init__(self, db_store: DatabaseContextStore):
        """
        Initialize with database store.

        Args:
            db_store: DatabaseContextStore instance
        """
        self.db = db_store
        logger.info("PostgreSQLHistoryProvider initialized")

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
            # Use the database store's get_recent_interactions method
            interactions = await self.db.get_recent_interactions(
                customer_id=user_id,
                limit=limit
            )

            # Format for our interface
            messages = []
            for interaction in interactions[offset:offset + limit]:
                # Add user message
                messages.append({
                    "role": "user",
                    "content": interaction.get("user_message", ""),
                    "timestamp": interaction.get("created_at"),
                    "session_id": interaction.get("session_id"),
                    "user_id": user_id
                })

                # Add assistant message
                messages.append({
                    "role": "assistant",
                    "content": interaction.get("ai_response", ""),
                    "timestamp": interaction.get("created_at"),
                    "session_id": interaction.get("session_id"),
                    "metadata": interaction.get("metadata", {})
                })

            logger.debug(f"Retrieved {len(messages)} messages for user {user_id}")
            return messages

        except Exception as e:
            logger.error(f"Error getting history for user {user_id}: {str(e)}", exc_info=True)
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
            # Get conversation from database
            conversation = await self.db.get_conversation(session_id)

            if not conversation:
                logger.debug(f"No conversation found for session {session_id}")
                return []

            # Extract messages from JSONB field
            messages = conversation.get("messages", [])

            # Return most recent messages up to limit
            result = messages[-limit:] if len(messages) > limit else messages

            logger.debug(f"Retrieved {len(result)} messages for session {session_id}")
            return result

        except Exception as e:
            logger.error(f"Error getting session history for {session_id}: {str(e)}", exc_info=True)
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

        This method saves to BOTH:
        1. ai_conversations table (messages JSONB array)
        2. chat_interactions table (for analytics)

        Args:
            session_id: Session identifier
            user_id: User identifier (if available)
            user_message: User's message
            assistant_response: Assistant's response
            metadata: Additional metadata (tokens, products, etc.)

        Returns:
            bool: Success status
        """
        try:
            timestamp = datetime.utcnow().isoformat()

            # Get existing conversation to update messages array
            existing_conversation = await self.db.get_conversation(session_id)

            if existing_conversation:
                # Append to existing messages
                # Database returns JSONB as dict/list, not string
                messages = existing_conversation.get("messages", [])
                context = existing_conversation.get("context", {})

                # Ensure messages is a list (defensive check)
                if not isinstance(messages, list):
                    logger.warning(f"messages is not a list for session {session_id}, resetting to empty list")
                    messages = []

                # Ensure context is a dict (defensive check)
                if not isinstance(context, dict):
                    logger.warning(f"context is not a dict for session {session_id}, resetting to empty dict")
                    context = {}
            else:
                # New conversation
                messages = []
                context = {}

            # Add user message
            messages.append({
                "role": "user",
                "content": user_message,
                "timestamp": timestamp
            })

            # Add assistant message
            messages.append({
                "role": "assistant",
                "content": assistant_response,
                "timestamp": timestamp,
                "metadata": metadata or {}
            })

            # Save to ai_conversations (messages JSONB)
            success = await self.db.save_conversation(
                session_id=session_id,
                messages=messages,
                context=context,
                customer_id=user_id
            )

            if not success:
                logger.error(f"Failed to save conversation for session {session_id}")
                return False

            # Also save to chat_interactions for analytics
            intent = metadata.get("intent") if metadata else None
            response_time = metadata.get("response_time") if metadata else None

            await self.db.add_interaction(
                session_id=session_id,
                customer_id=user_id,
                user_message=user_message,
                ai_response=assistant_response,
                intent=intent,
                response_time=response_time,
                metadata=metadata
            )

            logger.debug(f"Saved message exchange for session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving message for session {session_id}: {str(e)}", exc_info=True)
            return False


class PostgreSQLContextManager(IContextManager):
    """
    PostgreSQL-backed context manager.

    Stores conversation context in the ai_conversations.context JSONB field,
    ensuring context persists across server restarts.
    """

    def __init__(self, db_store: DatabaseContextStore):
        """
        Initialize with database store.

        Args:
            db_store: DatabaseContextStore instance
        """
        self.db = db_store
        logger.info("PostgreSQLContextManager initialized")

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
            # Get conversation from database
            conversation = await self.db.get_conversation(session_id)

            if not conversation:
                logger.debug(f"No context found for session {session_id}")
                return {
                    "messages": [],
                    "user_preferences": {},
                    "session_metadata": {}
                }

            # Extract recent messages
            messages = conversation.get("messages", [])
            recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages

            # Extract context
            context = conversation.get("context", {})

            # Load customer profile if customer_id available
            customer_id = conversation.get("customer_id")
            user_preferences = {}

            if customer_id:
                profile = await self.db.get_customer_profile(customer_id)
                if profile:
                    user_preferences = profile.get("preferences", {})

            return {
                "messages": recent_messages,
                "user_preferences": user_preferences,
                "session_metadata": context
            }

        except Exception as e:
            logger.error(f"Error getting context for session {session_id}: {str(e)}", exc_info=True)
            return {
                "messages": [],
                "user_preferences": {},
                "session_metadata": {}
            }

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
            # Get existing conversation
            conversation = await self.db.get_conversation(session_id)

            if conversation:
                # Merge context updates
                # Database returns JSONB as dict, not string
                existing_context = conversation.get("context", {})

                # Ensure existing_context is a dict (defensive check)
                if not isinstance(existing_context, dict):
                    logger.warning(f"existing_context is not a dict for session {session_id}, resetting to empty dict")
                    existing_context = {}

                # Merge the updates
                existing_context.update(context_updates)

                # Save back to database
                messages = conversation.get("messages", [])

                # Ensure messages is a list (defensive check)
                if not isinstance(messages, list):
                    logger.warning(f"messages is not a list for session {session_id}, resetting to empty list")
                    messages = []

                success = await self.db.save_conversation(
                    session_id=session_id,
                    messages=messages,
                    context=existing_context,
                    customer_id=conversation.get("customer_id")
                )

                if success:
                    logger.debug(f"Updated context for session {session_id}")
                return success
            else:
                # Create new conversation with context
                success = await self.db.save_conversation(
                    session_id=session_id,
                    messages=[],
                    context=context_updates,
                    customer_id=None
                )

                if success:
                    logger.debug(f"Created new conversation with context for session {session_id}")
                return success

        except Exception as e:
            logger.error(f"Error updating context for session {session_id}: {str(e)}", exc_info=True)
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
            # Get existing conversation
            conversation = await self.db.get_conversation(session_id)

            if not conversation:
                logger.debug(f"No conversation to clear for session {session_id}")
                return True

            # Clear context but keep messages
            messages = conversation.get("messages", [])
            success = await self.db.save_conversation(
                session_id=session_id,
                messages=messages,
                context={},  # Empty context
                customer_id=conversation.get("customer_id")
            )

            if success:
                logger.debug(f"Cleared context for session {session_id}")

            return success

        except Exception as e:
            logger.error(f"Error clearing context for session {session_id}: {str(e)}", exc_info=True)
            return False


# Re-export AgentPoolAdapter from adapters.py (no changes needed)
from .adapters import AgentPoolAdapter

__all__ = [
    "PostgreSQLHistoryProvider",
    "PostgreSQLContextManager",
    "AgentPoolAdapter"
]
