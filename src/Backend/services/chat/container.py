"""
Dependency Injection Container for Chat Service.

This module provides a simple DI container that manages the lifecycle
of all chat service dependencies, following the Dependency Inversion Principle.
"""

import logging
import os
from typing import Optional

from .chat_service import ChatService
from .adapters import (
    AgentPoolAdapter,
    InMemoryHistoryProvider,
    InMemoryContextManager
)
from .db_adapters import (
    PostgreSQLHistoryProvider,
    PostgreSQLContextManager
)
from .interfaces import (
    IChatProcessor,
    ISessionManager,
    IHistoryProvider,
    IContextManager,
    IAgentPoolAdapter
)
from services.context.database_store import DatabaseContextStore
from .session_cleanup import SessionCleanupManager, SessionCleanupConfig
from .redis_cache import RedisCacheContextManager, RedisCacheConfig

logger = logging.getLogger(__name__)

# Environment variable to control storage backend
USE_DATABASE_STORAGE = os.getenv("USE_DATABASE_STORAGE", "true").lower() == "true"

# Session cleanup configuration
SESSION_TTL_MINUTES = int(os.getenv("SESSION_TTL_MINUTES", "60"))
CLEANUP_INTERVAL_SECONDS = int(os.getenv("CLEANUP_INTERVAL_SECONDS", "300"))
MAX_SESSION_AGE_HOURS = int(os.getenv("MAX_SESSION_AGE_HOURS", "24"))
ENABLE_SESSION_CLEANUP = os.getenv("ENABLE_SESSION_CLEANUP", "true").lower() == "true"

# Redis cache configuration
USE_REDIS_CACHE = os.getenv("USE_REDIS_CACHE", "true").lower() == "true"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_TTL_SECONDS = int(os.getenv("REDIS_TTL_SECONDS", "3600"))


class ChatServiceContainer:
    """
    Simple dependency injection container for chat services.

    This container manages the creation and lifecycle of all chat-related
    services, ensuring dependencies are properly wired and singleton instances
    are maintained where appropriate.
    """

    def __init__(self):
        """Initialize empty container"""
        self._chat_service: Optional[ChatService] = None
        self._agent_pool_adapter: Optional[IAgentPoolAdapter] = None
        self._history_provider: Optional[IHistoryProvider] = None
        self._context_manager: Optional[IContextManager] = None
        self._db_store: Optional[DatabaseContextStore] = None
        self._cleanup_manager: Optional[SessionCleanupManager] = None
        logger.info(
            f"ChatServiceContainer initialized "
            f"(USE_DATABASE_STORAGE={USE_DATABASE_STORAGE}, "
            f"SESSION_CLEANUP={ENABLE_SESSION_CLEANUP})"
        )

    def register_agent_pool(self, agent_pool_manager):
        """
        Register the existing agent pool manager.

        This creates an adapter that bridges the legacy agent pool to our new interface.

        Args:
            agent_pool_manager: The AgentPoolManager instance from the existing system
        """
        self._agent_pool_adapter = AgentPoolAdapter(agent_pool_manager)
        logger.info("Agent pool adapter registered")

    def get_agent_pool_adapter(self) -> IAgentPoolAdapter:
        """Get or create agent pool adapter"""
        if self._agent_pool_adapter is None:
            raise RuntimeError(
                "Agent pool not registered. Call register_agent_pool() first."
            )
        return self._agent_pool_adapter

    async def get_database_store(self) -> DatabaseContextStore:
        """
        Get or create database store.

        Initializes connection pool on first access.

        Returns:
            DatabaseContextStore: Initialized database store
        """
        if self._db_store is None:
            self._db_store = DatabaseContextStore()
            await self._db_store.initialize()
            logger.info("DatabaseContextStore initialized with connection pool")
        return self._db_store

    def get_history_provider(self) -> IHistoryProvider:
        """
        Get or create history provider.

        Returns PostgreSQL-backed provider if USE_DATABASE_STORAGE=true,
        otherwise returns in-memory implementation.
        """
        if self._history_provider is None:
            if USE_DATABASE_STORAGE:
                # Database provider requires DatabaseContextStore
                # Note: The db_store will be initialized lazily on first use
                if self._db_store is None:
                    import asyncio
                    # Create and initialize db store synchronously
                    self._db_store = DatabaseContextStore()
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # If loop is running, we can't initialize here
                            # It will be initialized on first async call
                            logger.warning("Event loop running, database will initialize on first use")
                        else:
                            loop.run_until_complete(self._db_store.initialize())
                    except RuntimeError:
                        # No event loop, will initialize later
                        logger.info("No event loop yet, database will initialize on first use")

                self._history_provider = PostgreSQLHistoryProvider(self._db_store)
                logger.info("History provider created (PostgreSQL)")
            else:
                self._history_provider = InMemoryHistoryProvider()
                logger.info("History provider created (in-memory)")
        return self._history_provider

    def get_context_manager(self) -> IContextManager:
        """
        Get or create context manager.

        Returns appropriate implementation based on configuration:
        - USE_DATABASE_STORAGE=true + USE_REDIS_CACHE=true: Redis cache with PostgreSQL backend
        - USE_DATABASE_STORAGE=true + USE_REDIS_CACHE=false: PostgreSQL only
        - USE_DATABASE_STORAGE=false: In-memory
        """
        if self._context_manager is None:
            if USE_DATABASE_STORAGE:
                # Ensure database store is initialized
                if self._db_store is None:
                    import asyncio
                    self._db_store = DatabaseContextStore()
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            logger.warning("Event loop running, database will initialize on first use")
                        else:
                            loop.run_until_complete(self._db_store.initialize())
                    except RuntimeError:
                        logger.info("No event loop yet, database will initialize on first use")

                # Create PostgreSQL context manager
                pg_context_manager = PostgreSQLContextManager(self._db_store)

                # Wrap with Redis cache if enabled
                if USE_REDIS_CACHE:
                    redis_config = RedisCacheConfig(
                        host=REDIS_HOST,
                        port=REDIS_PORT,
                        db=REDIS_DB,
                        password=REDIS_PASSWORD,
                        ttl_seconds=REDIS_TTL_SECONDS
                    )

                    self._context_manager = RedisCacheContextManager(
                        db_manager=pg_context_manager,
                        config=redis_config
                    )
                    logger.info("Context manager created (Redis cache + PostgreSQL)")

                    # Initialize Redis asynchronously if possible
                    try:
                        import asyncio
                        loop = asyncio.get_event_loop()
                        if not loop.is_running():
                            loop.run_until_complete(self._context_manager.initialize())
                    except Exception as e:
                        logger.warning(f"Redis initialization deferred: {e}")
                else:
                    self._context_manager = pg_context_manager
                    logger.info("Context manager created (PostgreSQL)")
            else:
                self._context_manager = InMemoryContextManager()
                logger.info("Context manager created (in-memory)")
        return self._context_manager

    def get_chat_service(self) -> ChatService:
        """
        Get or create the main ChatService instance.

        This is a singleton - the same instance is returned on subsequent calls.

        Returns:
            ChatService: Fully wired chat service instance
        """
        if self._chat_service is None:
            # Wire up all dependencies
            agent_pool = self.get_agent_pool_adapter()
            history = self.get_history_provider()
            context = self.get_context_manager()

            # Create chat service with dependencies
            self._chat_service = ChatService(
                agent_pool_adapter=agent_pool,
                history_provider=history,
                context_manager=context
            )
            logger.info("ChatService created and wired with dependencies")

        return self._chat_service

    def get_cleanup_manager(self) -> Optional[SessionCleanupManager]:
        """
        Get or create the session cleanup manager.

        Returns:
            SessionCleanupManager: Cleanup manager instance or None if disabled
        """
        if not ENABLE_SESSION_CLEANUP:
            return None

        if self._cleanup_manager is None:
            # Create cleanup configuration
            config = SessionCleanupConfig(
                session_ttl_minutes=SESSION_TTL_MINUTES,
                cleanup_interval_seconds=CLEANUP_INTERVAL_SECONDS,
                max_session_age_hours=MAX_SESSION_AGE_HOURS,
                enable_cleanup=ENABLE_SESSION_CLEANUP
            )

            # Create cleanup manager (requires chat service)
            chat_service = self.get_chat_service()
            self._cleanup_manager = SessionCleanupManager(
                chat_service=chat_service,
                config=config
            )
            logger.info("SessionCleanupManager created")

        return self._cleanup_manager

    async def start_cleanup_manager(self):
        """Start the session cleanup background task"""
        cleanup_manager = self.get_cleanup_manager()
        if cleanup_manager:
            await cleanup_manager.start()

    async def stop_cleanup_manager(self):
        """Stop the session cleanup background task"""
        if self._cleanup_manager:
            await self._cleanup_manager.stop()

    async def reset(self):
        """
        Reset the container, clearing all instances.

        Useful for testing or when reconfiguring the system.
        Properly closes database connections and stops cleanup tasks before clearing.
        """
        # Stop cleanup manager if running
        if self._cleanup_manager is not None:
            await self._cleanup_manager.stop()

        # Close database connections if they exist
        if self._db_store is not None:
            await self._db_store.close()

        self._chat_service = None
        self._agent_pool_adapter = None
        self._history_provider = None
        self._context_manager = None
        self._db_store = None
        self._cleanup_manager = None
        logger.info("ChatServiceContainer reset")


# Global container instance
_container: Optional[ChatServiceContainer] = None


def get_container() -> ChatServiceContainer:
    """
    Get the global container instance.

    Creates a new container if one doesn't exist.

    Returns:
        ChatServiceContainer: The global container
    """
    global _container
    if _container is None:
        _container = ChatServiceContainer()
        logger.info("Global container created")
    return _container


def initialize_chat_service(agent_pool_manager) -> ChatService:
    """
    Convenience function to initialize and get the chat service.

    This is the main entry point for setting up the chat system.

    Args:
        agent_pool_manager: The existing agent pool manager

    Returns:
        ChatService: Fully configured chat service
    """
    container = get_container()
    container.register_agent_pool(agent_pool_manager)
    return container.get_chat_service()


def get_chat_service() -> ChatService:
    """
    Get the chat service from the global container.

    Returns:
        ChatService: The chat service instance

    Raises:
        RuntimeError: If chat service hasn't been initialized
    """
    container = get_container()
    try:
        return container.get_chat_service()
    except RuntimeError as e:
        raise RuntimeError(
            "Chat service not initialized. Call initialize_chat_service() first."
        ) from e
