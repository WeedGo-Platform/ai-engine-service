"""
Redis Cache Manager for Chat Service.

Provides high-performance caching layer with write-through to PostgreSQL,
combining the speed of Redis with the durability of PostgreSQL.
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import redis.asyncio as aioredis
from redis.asyncio import Redis
from redis.exceptions import RedisError

from .interfaces import IContextManager, IHistoryProvider
from .db_adapters import PostgreSQLContextManager, PostgreSQLHistoryProvider

logger = logging.getLogger(__name__)


class RedisCacheConfig:
    """Configuration for Redis cache"""
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        key_prefix: str = "chat:",
        ttl_seconds: int = 3600,  # 1 hour default TTL
        max_connections: int = 50
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.key_prefix = key_prefix
        self.ttl_seconds = ttl_seconds
        self.max_connections = max_connections


class RedisCacheContextManager(IContextManager):
    """
    Redis-cached context manager with PostgreSQL write-through.

    Strategy:
    - All reads check Redis first (fast)
    - Cache misses read from PostgreSQL and warm cache
    - All writes go to both Redis (fast) and PostgreSQL (durable)
    - Automatic cache invalidation and TTL management
    """

    def __init__(
        self,
        db_manager: PostgreSQLContextManager,
        config: Optional[RedisCacheConfig] = None
    ):
        """
        Initialize cache manager.

        Args:
            db_manager: PostgreSQL context manager for persistence
            config: Redis configuration
        """
        self.db = db_manager
        self.config = config or RedisCacheConfig()
        self.redis: Optional[Redis] = None
        self._lock = asyncio.Lock()
        self._cache_hits = 0
        self._cache_misses = 0
        logger.info(
            f"RedisCacheContextManager initialized "
            f"(host={self.config.host}, TTL={self.config.ttl_seconds}s)"
        )

    async def initialize(self):
        """Initialize Redis connection pool"""
        if self.redis is not None:
            logger.warning("Redis already initialized")
            return

        async with self._lock:
            if self.redis is not None:
                return

            try:
                self.redis = await aioredis.from_url(
                    f"redis://{self.config.host}:{self.config.port}/{self.config.db}",
                    password=self.config.password,
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=self.config.max_connections
                )

                # Test connection
                await self.redis.ping()
                logger.info("✅ Redis connection pool initialized")

            except Exception as e:
                logger.error(f"Failed to initialize Redis: {e}", exc_info=True)
                self.redis = None
                raise

    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            self.redis = None
            logger.info("Redis connection closed")

    def _make_key(self, session_id: str) -> str:
        """Generate Redis key for session context"""
        return f"{self.config.key_prefix}context:{session_id}"

    async def get_context(
        self,
        session_id: str,
        max_messages: int = 10
    ) -> Dict[str, Any]:
        """
        Get conversation context for a session.

        Reads from Redis cache first, falls back to PostgreSQL on miss.

        Args:
            session_id: Session identifier
            max_messages: Maximum recent messages to include

        Returns:
            Dict containing context data
        """
        try:
            # Try Redis first
            if self.redis:
                cache_key = self._make_key(session_id)
                cached_data = await self.redis.get(cache_key)

                if cached_data:
                    self._cache_hits += 1
                    logger.debug(f"Cache HIT for session {session_id}")
                    context = json.loads(cached_data)

                    # Apply max_messages limit
                    if "messages" in context:
                        context["messages"] = context["messages"][-max_messages:]

                    return context

            # Cache miss - read from database
            self._cache_misses += 1
            logger.debug(f"Cache MISS for session {session_id}")

            context = await self.db.get_context(session_id, max_messages)

            # Warm the cache
            if self.redis and context:
                await self._warm_cache(session_id, context)

            return context

        except RedisError as e:
            logger.warning(f"Redis error, falling back to database: {e}")
            # Fallback to database on Redis errors
            return await self.db.get_context(session_id, max_messages)

        except Exception as e:
            logger.error(f"Error getting context for {session_id}: {e}", exc_info=True)
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

        Write-through: Updates both Redis and PostgreSQL.

        Args:
            session_id: Session identifier
            context_updates: Context fields to update

        Returns:
            bool: Success status
        """
        try:
            # Write to database first (source of truth)
            db_success = await self.db.update_context(session_id, context_updates)

            if not db_success:
                logger.error(f"Database update failed for session {session_id}")
                return False

            # Update cache
            if self.redis:
                try:
                    # Get full context from database
                    full_context = await self.db.get_context(session_id)
                    await self._warm_cache(session_id, full_context)
                    logger.debug(f"Cache updated for session {session_id}")
                except RedisError as e:
                    logger.warning(f"Failed to update cache: {e}")
                    # Don't fail if cache update fails - database is updated

            return True

        except Exception as e:
            logger.error(f"Error updating context for {session_id}: {e}", exc_info=True)
            return False

    async def clear_context(self, session_id: str) -> bool:
        """
        Clear conversation context for a session.

        Clears both Redis cache and PostgreSQL.

        Args:
            session_id: Session identifier

        Returns:
            bool: Success status
        """
        try:
            # Clear from database
            db_success = await self.db.clear_context(session_id)

            # Invalidate cache
            if self.redis:
                try:
                    cache_key = self._make_key(session_id)
                    await self.redis.delete(cache_key)
                    logger.debug(f"Cache invalidated for session {session_id}")
                except RedisError as e:
                    logger.warning(f"Failed to invalidate cache: {e}")

            return db_success

        except Exception as e:
            logger.error(f"Error clearing context for {session_id}: {e}", exc_info=True)
            return False

    async def _warm_cache(self, session_id: str, context: Dict[str, Any]):
        """
        Warm the cache with context data.

        Args:
            session_id: Session identifier
            context: Context data to cache
        """
        try:
            if not self.redis:
                return

            cache_key = self._make_key(session_id)
            context_json = json.dumps(context)

            await self.redis.setex(
                cache_key,
                self.config.ttl_seconds,
                context_json
            )
            logger.debug(f"Cache warmed for session {session_id}")

        except Exception as e:
            logger.warning(f"Failed to warm cache: {e}")

    async def invalidate_session(self, session_id: str):
        """
        Manually invalidate cache for a session.

        Useful for forcing a fresh read from database.

        Args:
            session_id: Session identifier
        """
        if self.redis:
            try:
                cache_key = self._make_key(session_id)
                await self.redis.delete(cache_key)
                logger.debug(f"Cache manually invalidated for session {session_id}")
            except RedisError as e:
                logger.warning(f"Failed to invalidate cache: {e}")

    def get_cache_metrics(self) -> Dict[str, Any]:
        """
        Get cache performance metrics.

        Returns:
            Dict with cache statistics
        """
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "connected": self.redis is not None
        }

    async def reset_metrics(self):
        """Reset cache metrics counters"""
        self._cache_hits = 0
        self._cache_misses = 0
        logger.info("Cache metrics reset")
