"""
Interface definitions for chat system following Interface Segregation Principle.

These protocols define contracts that implementations must follow, allowing for
dependency inversion and easier testing/mocking.
"""

from typing import Protocol, List, Dict, Any, Optional
from datetime import datetime


class IChatProcessor(Protocol):
    """Interface for processing chat messages"""

    async def process_message(
        self,
        message: str,
        session_id: str,
        user_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a chat message and return response.

        Args:
            message: User's message text
            session_id: Unique session identifier
            user_id: Optional user identifier
            **kwargs: Additional context (store_id, language, etc.)

        Returns:
            Dict containing:
                - text: Response text
                - products: List of product recommendations
                - quick_actions: List of quick action buttons
                - metadata: Response metadata (tokens, time, model, etc.)
        """
        ...


class ISessionManager(Protocol):
    """Interface for managing chat sessions"""

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
        ...

    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve session details.

        Args:
            session_id: Session identifier

        Returns:
            Dict containing session metadata and settings
        """
        ...

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
        ...

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and cleanup resources.

        Args:
            session_id: Session identifier

        Returns:
            bool: Success status
        """
        ...

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
        ...


class IHistoryProvider(Protocol):
    """Interface for retrieving conversation history"""

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
        ...

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
        ...

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
            metadata: Additional metadata (tokens, products, etc.)

        Returns:
            bool: Success status
        """
        ...


class IContextManager(Protocol):
    """Interface for managing conversation context"""

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
            Dict containing:
                - messages: Recent message history
                - user_preferences: User preferences if available
                - session_metadata: Session-specific context
        """
        ...

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
        ...

    async def clear_context(self, session_id: str) -> bool:
        """
        Clear conversation context for a session.

        Args:
            session_id: Session identifier

        Returns:
            bool: Success status
        """
        ...


class IAgentPoolAdapter(Protocol):
    """Interface for interacting with the agent pool system"""

    async def generate_with_agent_pool(
        self,
        session_id: str,
        message: str,
        user_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate response using the agent pool system.

        Args:
            session_id: Session identifier
            message: User's message
            user_id: Optional user identifier
            **kwargs: Additional parameters

        Returns:
            Dict containing response data
        """
        ...

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
        ...
