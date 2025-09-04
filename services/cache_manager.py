#!/usr/bin/env python3
"""
Cache Manager for Intelligent Budtender
Implements Redis-based caching with intelligent TTL and invalidation
"""

import json
import hashlib
import logging
from typing import Optional, Any, Dict, List
from datetime import datetime, timedelta
import redis
from redis.exceptions import RedisError
import pickle

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Intelligent caching system for budtender responses
    Optimizes for common queries and recommendations
    """
    
    # Cache TTL strategy (in seconds)
    TTL_STRATEGY = {
        'product_search': 3600,        # 1 hour - products don't change often
        'recommendations': 1800,        # 30 min - based on knowledge graph
        'chat_response': 300,          # 5 min - for common questions
        'product_details': 3600,        # 1 hour
        'health_check': 10,            # 10 seconds
        'cart': 86400,                 # 24 hours - session-based
        'user_profile': 604800,        # 1 week
    }
    
    # Common queries that should always be cached
    COMMON_QUERIES = [
        "what do you recommend",
        "help with sleep",
        "something for pain",
        "first time",
        "energy",
        "anxiety relief",
        "best seller",
        "on sale",
        "indica vs sativa",
        "how much thc"
    ]
    
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379, redis_db: int = 0):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=False,  # We'll handle encoding
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            self.enabled = True
            logger.info(f"Cache manager connected to Redis at {redis_host}:{redis_port}")
        except (RedisError, ConnectionError) as e:
            logger.warning(f"Redis not available: {e}. Caching disabled.")
            self.redis_client = None
            self.enabled = False
    
    def _generate_cache_key(self, prefix: str, params: Dict) -> str:
        """
        Generate normalized cache key from parameters
        Ensures similar queries hit the same cache
        """
        # Normalize parameters
        normalized = {}
        for key, value in params.items():
            if isinstance(value, str):
                # Lowercase and strip whitespace
                normalized[key] = value.lower().strip()
            elif isinstance(value, (list, dict)):
                # Sort lists and dicts for consistency
                normalized[key] = json.dumps(value, sort_keys=True)
            else:
                normalized[key] = str(value)
        
        # Create hash of normalized params
        param_str = json.dumps(normalized, sort_keys=True)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
        
        return f"budtender:{prefix}:{param_hash}"
    
    def _should_cache_query(self, query: str) -> bool:
        """Determine if a query should be cached based on commonality"""
        query_lower = query.lower()
        
        # Check if it matches common queries
        for common in self.COMMON_QUERIES:
            if common in query_lower:
                return True
        
        # Don't cache very specific or personal queries
        personal_indicators = ['my order', 'my cart', 'last time', 'yesterday']
        for indicator in personal_indicators:
            if indicator in query_lower:
                return False
        
        # Cache general questions
        if '?' in query:
            return True
        
        return False
    
    async def get(self, cache_type: str, params: Dict) -> Optional[Any]:
        """
        Get cached value if available
        Returns None if not found or cache disabled
        """
        if not self.enabled:
            return None
        
        try:
            key = self._generate_cache_key(cache_type, params)
            cached_data = self.redis_client.get(key)
            
            if cached_data:
                # Increment hit counter for analytics
                self.redis_client.hincrby('cache:stats', f'{cache_type}:hits', 1)
                
                # Deserialize
                data = pickle.loads(cached_data)
                
                logger.debug(f"Cache hit for {key}")
                return data
            else:
                # Increment miss counter
                self.redis_client.hincrby('cache:stats', f'{cache_type}:misses', 1)
                return None
                
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(self, cache_type: str, params: Dict, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set cache value with appropriate TTL
        Returns True if successful
        """
        if not self.enabled:
            return False
        
        try:
            key = self._generate_cache_key(cache_type, params)
            
            # Use custom TTL or default for cache type
            if ttl is None:
                ttl = self.TTL_STRATEGY.get(cache_type, 600)  # Default 10 min
            
            # Serialize data
            serialized = pickle.dumps(value)
            
            # Set with expiration
            self.redis_client.setex(key, ttl, serialized)
            
            # Track cache size for monitoring
            self.redis_client.hincrby('cache:stats', 'total_keys', 1)
            
            logger.debug(f"Cache set for {key} with TTL {ttl}s")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def invalidate(self, pattern: str) -> int:
        """
        Invalidate cache entries matching pattern
        Returns number of keys deleted
        """
        if not self.enabled:
            return 0
        
        try:
            # Find matching keys
            keys = self.redis_client.keys(f"budtender:{pattern}:*")
            
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Invalidated {deleted} cache entries matching {pattern}")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return 0
    
    async def invalidate_product_caches(self, product_id: Optional[int] = None):
        """Invalidate all product-related caches"""
        if product_id:
            # Invalidate specific product
            await self.invalidate(f"product_details:{product_id}")
            await self.invalidate(f"product_search:*{product_id}*")
        else:
            # Invalidate all product caches
            await self.invalidate("product_details")
            await self.invalidate("product_search")
            await self.invalidate("recommendations")
    
    def warm_cache(self, common_intents: List[str]):
        """
        Pre-warm cache with common queries
        Called on startup to improve initial response times
        """
        if not self.enabled:
            return
        
        logger.info("Warming cache with common queries...")
        
        # Store common intent patterns
        for intent in common_intents:
            key = f"budtender:warm:{intent}"
            self.redis_client.setex(key, 3600, "warmed")
        
        logger.info(f"Cache warmed with {len(common_intents)} common patterns")
    
    def get_cache_stats(self) -> Dict:
        """Get cache performance statistics"""
        if not self.enabled:
            return {"enabled": False}
        
        try:
            stats = self.redis_client.hgetall('cache:stats')
            
            # Decode and convert to proper types
            decoded_stats = {}
            for key, value in stats.items():
                decoded_stats[key.decode()] = int(value)
            
            # Calculate hit rate
            total_hits = sum(v for k, v in decoded_stats.items() if 'hits' in k)
            total_misses = sum(v for k, v in decoded_stats.items() if 'misses' in k)
            
            if total_hits + total_misses > 0:
                hit_rate = total_hits / (total_hits + total_misses)
            else:
                hit_rate = 0
            
            # Get memory usage
            info = self.redis_client.info('memory')
            
            return {
                "enabled": True,
                "stats": decoded_stats,
                "hit_rate": f"{hit_rate:.2%}",
                "memory_used": info.get('used_memory_human', 'unknown'),
                "total_keys": self.redis_client.dbsize()
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"enabled": True, "error": str(e)}
    
    def clear_all(self) -> bool:
        """Clear all cache entries (use with caution)"""
        if not self.enabled:
            return False
        
        try:
            self.redis_client.flushdb()
            logger.warning("All cache entries cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

# Decorator for caching function results
def cached_result(cache_type: str, ttl: Optional[int] = None):
    """
    Decorator to cache function results
    Usage: @cached_result('product_search', ttl=3600)
    """
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            # Create cache manager if not exists
            if not hasattr(self, '_cache_manager'):
                self._cache_manager = CacheManager()
            
            # Generate cache params from function args
            cache_params = {
                'func': func.__name__,
                'args': str(args),
                'kwargs': str(kwargs)
            }
            
            # Try to get from cache
            cached = await self._cache_manager.get(cache_type, cache_params)
            if cached is not None:
                return cached
            
            # Execute function
            result = await func(self, *args, **kwargs)
            
            # Cache result
            await self._cache_manager.set(cache_type, cache_params, result, ttl)
            
            return result
        
        return wrapper
    return decorator

# Example usage
async def test_cache():
    """Test cache functionality"""
    cache = CacheManager()
    
    # Test basic operations
    test_params = {"query": "help with sleep", "customer_id": "test123"}
    test_value = {"response": "Try indica strains", "products": [1, 2, 3]}
    
    # Set cache
    await cache.set("chat_response", test_params, test_value)
    
    # Get from cache
    cached = await cache.get("chat_response", test_params)
    print(f"Cached value: {cached}")
    
    # Get stats
    stats = cache.get_cache_stats()
    print(f"Cache stats: {stats}")
    
    # Test invalidation
    deleted = await cache.invalidate("chat_response")
    print(f"Deleted {deleted} keys")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_cache())