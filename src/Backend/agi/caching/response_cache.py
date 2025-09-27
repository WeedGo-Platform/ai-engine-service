"""
Response Caching Layer
Intelligent caching for API responses with TTL, invalidation, and warming
"""

import asyncio
import hashlib
import json
import logging
import pickle
from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import redis.asyncio as redis
from collections import OrderedDict

from agi.core.database import get_db_manager
from agi.analytics import get_metrics_collector
from agi.config.agi_config import get_config

logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """Cache strategies"""
    LRU = "lru"           # Least Recently Used
    LFU = "lfu"           # Least Frequently Used
    FIFO = "fifo"         # First In First Out
    TTL = "ttl"           # Time To Live based
    ADAPTIVE = "adaptive" # Adaptive based on usage patterns


class CacheLevel(Enum):
    """Cache storage levels"""
    MEMORY = "memory"     # In-memory cache
    REDIS = "redis"       # Redis cache
    DATABASE = "database" # Database cache
    HYBRID = "hybrid"     # Multi-level cache


@dataclass
class CacheEntry:
    """Single cache entry"""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    size_bytes: int = 0


@dataclass
class CacheStats:
    """Cache statistics"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    evictions: int = 0
    average_response_time_ms: float = 0
    memory_usage_bytes: int = 0
    entries_count: int = 0


class MemoryCache:
    """In-memory cache implementation"""

    def __init__(self, max_size: int = 1000, strategy: CacheStrategy = CacheStrategy.LRU):
        self.max_size = max_size
        self.strategy = strategy
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.access_frequency: Dict[str, int] = {}
        self.stats = CacheStats()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            entry = self.cache[key]

            # Check expiration
            if entry.expires_at and datetime.utcnow() > entry.expires_at:
                await self.delete(key)
                self.stats.cache_misses += 1
                return None

            # Update access info
            entry.access_count += 1
            entry.last_accessed = datetime.utcnow()
            self.access_frequency[key] = self.access_frequency.get(key, 0) + 1

            # Move to end for LRU
            if self.strategy == CacheStrategy.LRU:
                self.cache.move_to_end(key)

            self.stats.cache_hits += 1
            self.stats.total_requests += 1

            return entry.value

        self.stats.cache_misses += 1
        self.stats.total_requests += 1
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Set value in cache"""
        try:
            # Calculate size
            size_bytes = len(pickle.dumps(value))

            # Check if we need to evict
            if len(self.cache) >= self.max_size:
                await self._evict()

            # Create entry
            expires_at = None
            if ttl:
                expires_at = datetime.utcnow() + timedelta(seconds=ttl)

            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                metadata=metadata or {},
                size_bytes=size_bytes
            )

            self.cache[key] = entry
            self.access_frequency[key] = 0

            self.stats.entries_count = len(self.cache)
            self.stats.memory_usage_bytes += size_bytes

            return True

        except Exception as e:
            logger.error(f"Failed to set cache entry: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete entry from cache"""
        if key in self.cache:
            entry = self.cache[key]
            self.stats.memory_usage_bytes -= entry.size_bytes
            del self.cache[key]

            if key in self.access_frequency:
                del self.access_frequency[key]

            self.stats.entries_count = len(self.cache)
            return True

        return False

    async def _evict(self):
        """Evict entry based on strategy"""
        if not self.cache:
            return

        if self.strategy == CacheStrategy.LRU:
            # Remove least recently used (first item)
            key = next(iter(self.cache))
            await self.delete(key)

        elif self.strategy == CacheStrategy.LFU:
            # Remove least frequently used
            if self.access_frequency:
                key = min(self.access_frequency, key=self.access_frequency.get)
                await self.delete(key)

        elif self.strategy == CacheStrategy.FIFO:
            # Remove oldest (first item)
            key = next(iter(self.cache))
            await self.delete(key)

        elif self.strategy == CacheStrategy.TTL:
            # Remove expired entries first
            now = datetime.utcnow()
            for key, entry in list(self.cache.items()):
                if entry.expires_at and now > entry.expires_at:
                    await self.delete(key)
                    break
            else:
                # No expired entries, use FIFO
                key = next(iter(self.cache))
                await self.delete(key)

        self.stats.evictions += 1

    async def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
        self.access_frequency.clear()
        self.stats = CacheStats()

    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        return self.stats


class RedisCache:
    """Redis-based cache implementation"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self.stats = CacheStats()
        self.prefix = "agi:cache:"

    async def initialize(self):
        """Initialize Redis connection"""
        if not self.redis:
            config = get_config()
            self.redis = await redis.from_url(
                f"redis://{config.redis.host}:{config.redis.port}/{config.redis.db}",
                decode_responses=True
            )

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        if not self.redis:
            await self.initialize()

        full_key = f"{self.prefix}{key}"

        try:
            data = await self.redis.get(full_key)
            if data:
                self.stats.cache_hits += 1
                self.stats.total_requests += 1

                # Update access count
                await self.redis.hincrby(f"{full_key}:meta", "access_count", 1)

                return pickle.loads(data.encode('latin-1')) if isinstance(data, str) else pickle.loads(data)

        except Exception as e:
            logger.error(f"Redis get error: {e}")

        self.stats.cache_misses += 1
        self.stats.total_requests += 1
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Set value in Redis"""
        if not self.redis:
            await self.initialize()

        full_key = f"{self.prefix}{key}"

        try:
            # Serialize value
            serialized = pickle.dumps(value).decode('latin-1')

            # Set with TTL if provided
            if ttl:
                await self.redis.setex(full_key, ttl, serialized)
            else:
                await self.redis.set(full_key, serialized)

            # Store metadata
            if metadata:
                await self.redis.hset(f"{full_key}:meta", mapping=metadata)
                if ttl:
                    await self.redis.expire(f"{full_key}:meta", ttl)

            self.stats.entries_count += 1
            return True

        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete from Redis"""
        if not self.redis:
            await self.initialize()

        full_key = f"{self.prefix}{key}"

        try:
            result = await self.redis.delete(full_key, f"{full_key}:meta")
            if result > 0:
                self.stats.entries_count -= 1
                return True

        except Exception as e:
            logger.error(f"Redis delete error: {e}")

        return False

    async def clear(self):
        """Clear all cache entries"""
        if not self.redis:
            await self.initialize()

        try:
            pattern = f"{self.prefix}*"
            cursor = 0

            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await self.redis.delete(*keys)
                if cursor == 0:
                    break

            self.stats = CacheStats()

        except Exception as e:
            logger.error(f"Redis clear error: {e}")


class ResponseCache:
    """
    Multi-level response caching system
    Features: intelligent caching, TTL management, cache warming, invalidation
    """

    def __init__(
        self,
        cache_level: CacheLevel = CacheLevel.HYBRID,
        memory_size: int = 1000,
        default_ttl: int = 3600
    ):
        self.cache_level = cache_level
        self.default_ttl = default_ttl

        # Initialize cache layers
        self.memory_cache = MemoryCache(max_size=memory_size)
        self.redis_cache = None
        self.cache_patterns: Dict[str, Dict[str, Any]] = {}
        self.invalidation_rules: List[Callable] = []

        # Cache warmup queue
        self.warmup_queue: List[Tuple[str, Callable]] = []

    async def initialize(self):
        """Initialize cache system"""
        if self.cache_level in [CacheLevel.REDIS, CacheLevel.HYBRID]:
            self.redis_cache = RedisCache()
            await self.redis_cache.initialize()

        logger.info(f"Response cache initialized with {self.cache_level.value} strategy")

    async def get(self, key: str) -> Optional[Any]:
        """Get cached response"""
        cache_key = self._generate_key(key)

        # Try memory cache first
        if self.cache_level in [CacheLevel.MEMORY, CacheLevel.HYBRID]:
            value = await self.memory_cache.get(cache_key)
            if value is not None:
                return value

        # Try Redis cache
        if self.cache_level in [CacheLevel.REDIS, CacheLevel.HYBRID] and self.redis_cache:
            value = await self.redis_cache.get(cache_key)
            if value is not None:
                # Promote to memory cache in hybrid mode
                if self.cache_level == CacheLevel.HYBRID:
                    await self.memory_cache.set(cache_key, value, ttl=300)
                return value

        # Try database cache
        if self.cache_level in [CacheLevel.DATABASE, CacheLevel.HYBRID]:
            value = await self._get_from_database(cache_key)
            if value is not None:
                # Promote to faster caches
                if self.cache_level == CacheLevel.HYBRID:
                    await self.memory_cache.set(cache_key, value, ttl=300)
                    if self.redis_cache:
                        await self.redis_cache.set(cache_key, value, ttl=self.default_ttl)
                return value

        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Cache a response"""
        cache_key = self._generate_key(key)
        ttl = ttl or self.default_ttl

        success = True

        # Store in appropriate cache levels
        if self.cache_level in [CacheLevel.MEMORY, CacheLevel.HYBRID]:
            success &= await self.memory_cache.set(cache_key, value, ttl=ttl)

        if self.cache_level in [CacheLevel.REDIS, CacheLevel.HYBRID] and self.redis_cache:
            success &= await self.redis_cache.set(cache_key, value, ttl=ttl)

        if self.cache_level in [CacheLevel.DATABASE, CacheLevel.HYBRID]:
            success &= await self._store_in_database(cache_key, value, ttl, tags)

        # Record pattern for analysis
        self._record_pattern(key, ttl)

        return success

    async def invalidate(self, pattern: Optional[str] = None, tags: Optional[List[str]] = None):
        """Invalidate cache entries"""
        invalidated = 0

        if pattern:
            # Invalidate by pattern
            if self.cache_level in [CacheLevel.MEMORY, CacheLevel.HYBRID]:
                for key in list(self.memory_cache.cache.keys()):
                    if pattern in key:
                        await self.memory_cache.delete(key)
                        invalidated += 1

            if self.cache_level in [CacheLevel.REDIS, CacheLevel.HYBRID] and self.redis_cache:
                # Redis pattern matching
                await self.redis_cache.clear()  # Simplified - could use pattern matching

        if tags:
            # Invalidate by tags (requires tag tracking)
            await self._invalidate_by_tags(tags)

        logger.info(f"Invalidated {invalidated} cache entries")

    async def cache_function(
        self,
        func: Callable,
        *args,
        cache_key: Optional[str] = None,
        ttl: Optional[int] = None,
        **kwargs
    ) -> Any:
        """Cache function results"""
        # Generate cache key from function and args
        if not cache_key:
            cache_key = self._generate_function_key(func, args, kwargs)

        # Check cache
        cached = await self.get(cache_key)
        if cached is not None:
            return cached

        # Execute function
        result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

        # Cache result
        await self.set(cache_key, result, ttl=ttl)

        return result

    async def warm_cache(self, keys: List[Tuple[str, Callable]]):
        """Warm cache with pre-computed values"""
        warmed = 0

        for key, func in keys:
            try:
                result = await func() if asyncio.iscoroutinefunction(func) else func()
                await self.set(key, result)
                warmed += 1
            except Exception as e:
                logger.error(f"Failed to warm cache for {key}: {e}")

        logger.info(f"Warmed {warmed} cache entries")

    def add_invalidation_rule(self, rule: Callable[[str, Any], bool]):
        """Add custom invalidation rule"""
        self.invalidation_rules.append(rule)

    def _generate_key(self, key: str) -> str:
        """Generate normalized cache key"""
        return hashlib.md5(key.encode()).hexdigest()

    def _generate_function_key(self, func: Callable, args: tuple, kwargs: dict) -> str:
        """Generate cache key for function"""
        key_parts = [
            func.__module__,
            func.__name__,
            str(args),
            str(sorted(kwargs.items()))
        ]
        key_str = ":".join(key_parts)
        return self._generate_key(key_str)

    def _record_pattern(self, key: str, ttl: int):
        """Record cache pattern for analysis"""
        pattern = key.split(":")[0] if ":" in key else key

        if pattern not in self.cache_patterns:
            self.cache_patterns[pattern] = {
                "count": 0,
                "total_ttl": 0,
                "last_accessed": datetime.utcnow()
            }

        self.cache_patterns[pattern]["count"] += 1
        self.cache_patterns[pattern]["total_ttl"] += ttl
        self.cache_patterns[pattern]["last_accessed"] = datetime.utcnow()

    async def _get_from_database(self, key: str) -> Optional[Any]:
        """Get cached value from database"""
        try:
            db = await get_db_manager()
            result = await db.fetchone(
                """
                SELECT value FROM agi.response_cache
                WHERE key = $1 AND expires_at > NOW()
                """,
                key
            )

            if result:
                return pickle.loads(result['value'])

        except Exception as e:
            logger.error(f"Database cache get error: {e}")

        return None

    async def _store_in_database(
        self,
        key: str,
        value: Any,
        ttl: int,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Store value in database cache"""
        try:
            db = await get_db_manager()
            expires_at = datetime.utcnow() + timedelta(seconds=ttl)

            await db.execute(
                """
                INSERT INTO agi.response_cache
                (key, value, tags, expires_at, created_at)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (key) DO UPDATE SET
                    value = $2,
                    tags = $3,
                    expires_at = $4
                """,
                key,
                pickle.dumps(value),
                tags or [],
                expires_at,
                datetime.utcnow()
            )

            return True

        except Exception as e:
            logger.error(f"Database cache store error: {e}")
            return False

    async def _invalidate_by_tags(self, tags: List[str]):
        """Invalidate cache entries by tags"""
        try:
            db = await get_db_manager()
            await db.execute(
                """
                DELETE FROM agi.response_cache
                WHERE tags && $1
                """,
                tags
            )
        except Exception as e:
            logger.error(f"Tag invalidation error: {e}")

    def analyze_patterns(self) -> Dict[str, Any]:
        """Analyze cache usage patterns"""
        if not self.cache_patterns:
            return {}

        patterns = []
        for pattern, stats in self.cache_patterns.items():
            patterns.append({
                "pattern": pattern,
                "frequency": stats["count"],
                "avg_ttl": stats["total_ttl"] / stats["count"] if stats["count"] > 0 else 0,
                "last_accessed": stats["last_accessed"].isoformat()
            })

        # Sort by frequency
        patterns.sort(key=lambda x: x["frequency"], reverse=True)

        return {
            "top_patterns": patterns[:10],
            "total_patterns": len(patterns),
            "cache_efficiency": self.get_efficiency()
        }

    def get_efficiency(self) -> float:
        """Calculate cache efficiency"""
        stats = self.get_stats()
        if stats["total_requests"] == 0:
            return 0.0

        return stats["cache_hits"] / stats["total_requests"]

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        memory_stats = self.memory_cache.get_stats() if self.memory_cache else CacheStats()
        redis_stats = self.redis_cache.stats if self.redis_cache else CacheStats()

        return {
            "cache_level": self.cache_level.value,
            "total_requests": memory_stats.total_requests + redis_stats.total_requests,
            "cache_hits": memory_stats.cache_hits + redis_stats.cache_hits,
            "cache_misses": memory_stats.cache_misses + redis_stats.cache_misses,
            "memory_entries": memory_stats.entries_count,
            "redis_entries": redis_stats.entries_count,
            "memory_usage_mb": memory_stats.memory_usage_bytes / (1024 * 1024),
            "evictions": memory_stats.evictions + redis_stats.evictions,
            "patterns_tracked": len(self.cache_patterns)
        }

    async def cleanup_expired(self):
        """Clean up expired cache entries"""
        try:
            # Clean database cache
            db = await get_db_manager()
            result = await db.execute(
                """
                DELETE FROM agi.response_cache
                WHERE expires_at < NOW()
                """
            )
            logger.info(f"Cleaned up expired database cache entries")

            # Memory cache handles expiration on access
            # Redis handles expiration automatically

        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")


# Global cache instance
_response_cache: Optional[ResponseCache] = None


async def get_response_cache() -> ResponseCache:
    """Get singleton response cache instance"""
    global _response_cache
    if _response_cache is None:
        config = get_config()
        _response_cache = ResponseCache(
            cache_level=CacheLevel.HYBRID,
            memory_size=1000,
            default_ttl=3600
        )
        await _response_cache.initialize()
    return _response_cache