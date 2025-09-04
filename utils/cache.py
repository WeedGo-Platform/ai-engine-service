"""
Cache Manager - Redis-based caching with fallback
Implements decorator pattern for easy caching
"""

import json
import logging
import hashlib
from typing import Any, Optional
from functools import wraps

import redis.asyncio as redis
from config import settings

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Redis cache manager with automatic serialization
    Singleton pattern ensures single Redis connection
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize cache manager"""
        if self._initialized:
            return
        
        self._redis: Optional[redis.Redis] = None
        self._enabled = settings.ENABLE_CACHING
        self._initialized = True
    
    async def get_redis(self) -> redis.Redis:
        """Get or create Redis connection"""
        if not self._redis:
            try:
                self._redis = redis.from_url(
                    settings.redis_url,
                    decode_responses=True
                )
                await self._redis.ping()
                logger.info("Redis cache connected")
            except Exception as e:
                logger.warning(f"Redis connection failed: {str(e)}")
                self._enabled = False
        
        return self._redis
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self._enabled:
            return None
        
        try:
            redis_client = await self.get_redis()
            if not redis_client:
                return None
            
            value = await redis_client.get(key)
            
            if value:
                # Deserialize JSON
                return json.loads(value)
            
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600
    ) -> None:
        """Set value in cache with TTL"""
        if not self._enabled:
            return
        
        try:
            redis_client = await self.get_redis()
            if not redis_client:
                return
            
            # Serialize to JSON
            serialized = json.dumps(value)
            
            await redis_client.set(key, serialized, ex=ttl)
            
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
    
    async def delete(self, key: str) -> None:
        """Delete key from cache"""
        if not self._enabled:
            return
        
        try:
            redis_client = await self.get_redis()
            if not redis_client:
                return
            
            await redis_client.delete(key)
            
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
    
    async def clear_pattern(self, pattern: str) -> None:
        """Clear all keys matching pattern"""
        if not self._enabled:
            return
        
        try:
            redis_client = await self.get_redis()
            if not redis_client:
                return
            
            # Find all keys matching pattern
            keys = []
            async for key in redis_client.scan_iter(pattern):
                keys.append(key)
            
            # Delete in batch
            if keys:
                await redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache keys matching {pattern}")
            
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")
    
    async def cleanup(self):
        """Clean up resources"""
        if self._redis:
            await self._redis.close()
            self._redis = None
    
    @staticmethod
    def generate_key(*args, **kwargs) -> str:
        """Generate cache key from arguments"""
        # Combine args and kwargs
        key_data = {
            "args": args,
            "kwargs": kwargs
        }
        
        # Create hash
        key_str = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        
        return key_hash

def cached(ttl: int = 3600, key_prefix: str = ""):
    """
    Decorator for caching function results
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache keys
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{CacheManager.generate_key(*args, **kwargs)}"
            
            # Try to get from cache
            cache_manager = CacheManager()
            cached_result = await cache_manager.get(cache_key)
            
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Call function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator