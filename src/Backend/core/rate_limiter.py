"""
Rate Limiting System
Prevents abuse and DoS attacks through intelligent rate limiting
"""

import time
import asyncio
import hashlib
import json
from typing import Dict, Any, Optional, Tuple
from collections import defaultdict, deque
from datetime import datetime, timedelta
from fastapi import HTTPException, Request, status
from functools import wraps
import logging
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Advanced rate limiter with multiple algorithms:
    - Token bucket
    - Sliding window
    - Fixed window
    - Leaky bucket
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize rate limiter
        
        Args:
            redis_client: Redis client for distributed rate limiting
        """
        self.redis = redis_client
        self.local_storage = defaultdict(lambda: defaultdict(dict))
        
        # Default limits
        self.default_limits = {
            'global': (60, 60),  # 60 requests per 60 seconds
            'api': (100, 60),    # 100 API calls per minute
            'auth': (5, 60),     # 5 auth attempts per minute
            'expensive': (10, 60),  # 10 expensive operations per minute
        }
        
        # Burst allowance
        self.burst_multiplier = 1.5
        
        # Track violations for temporary bans
        self.violations = defaultdict(int)
        self.banned_until = {}
    
    def get_client_id(self, request: Request) -> str:
        """
        Get unique client identifier from request
        
        Args:
            request: FastAPI request object
        
        Returns:
            Client identifier
        """
        # Try to get authenticated user ID
        if hasattr(request.state, 'user'):
            user = request.state.user
            if user and user.get('user_id'):
                return f"user:{user['user_id']}"
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else '127.0.0.1'
        
        # Include user agent for better fingerprinting
        user_agent = request.headers.get('User-Agent', 'unknown')
        fingerprint = f"{client_ip}:{user_agent}"
        
        # Hash for privacy
        return hashlib.md5(fingerprint.encode()).hexdigest()
    
    async def check_rate_limit(
        self,
        client_id: str,
        resource: str = 'global',
        limit: Optional[Tuple[int, int]] = None,
        algorithm: str = 'sliding_window'
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if client has exceeded rate limit
        
        Args:
            client_id: Client identifier
            resource: Resource being accessed
            limit: (requests, seconds) tuple
            algorithm: Rate limiting algorithm
        
        Returns:
            (allowed, info) tuple
        """
        # Skip rate limiting if disabled
        import os
        if os.getenv('DISABLE_RATE_LIMIT', '').lower() == 'true':
            return True, {'requests_remaining': float('inf'), 'reset_at': None}
        
        # Check if client is banned
        if client_id in self.banned_until:
            ban_until = self.banned_until[client_id]
            if time.time() < ban_until:
                remaining = int(ban_until - time.time())
                return False, {
                    'banned': True,
                    'retry_after': remaining,
                    'reason': 'Temporary ban due to repeated violations'
                }
            else:
                # Ban expired
                del self.banned_until[client_id]
                self.violations[client_id] = 0
        
        # Get rate limit for resource
        if limit is None:
            limit = self.default_limits.get(resource, (60, 60))
        
        max_requests, time_window = limit
        
        # Apply algorithm
        if algorithm == 'token_bucket':
            return await self._token_bucket(client_id, resource, max_requests, time_window)
        elif algorithm == 'sliding_window':
            return await self._sliding_window(client_id, resource, max_requests, time_window)
        elif algorithm == 'fixed_window':
            return await self._fixed_window(client_id, resource, max_requests, time_window)
        else:
            return await self._leaky_bucket(client_id, resource, max_requests, time_window)
    
    async def _token_bucket(
        self,
        client_id: str,
        resource: str,
        max_tokens: int,
        refill_time: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Token bucket algorithm
        Allows burst traffic up to bucket capacity
        """
        now = time.time()
        key = f"rate_limit:token:{client_id}:{resource}"
        
        if self.redis:
            # Distributed implementation
            pipe = self.redis.pipeline()
            await pipe.hgetall(key)
            result = await pipe.execute()
            bucket_data = result[0] if result else {}
            
            if bucket_data:
                tokens = float(bucket_data.get(b'tokens', max_tokens))
                last_refill = float(bucket_data.get(b'last_refill', now))
            else:
                tokens = max_tokens
                last_refill = now
            
            # Refill tokens
            time_passed = now - last_refill
            tokens_to_add = (time_passed / refill_time) * max_tokens
            tokens = min(max_tokens * self.burst_multiplier, tokens + tokens_to_add)
            
            if tokens >= 1:
                # Consume token
                tokens -= 1
                
                # Update bucket
                pipe = self.redis.pipeline()
                await pipe.hset(key, mapping={
                    'tokens': tokens,
                    'last_refill': now
                })
                await pipe.expire(key, refill_time * 2)
                await pipe.execute()
                
                return True, {
                    'tokens_remaining': int(tokens),
                    'refill_in': refill_time
                }
            else:
                # Calculate retry time
                tokens_needed = 1 - tokens
                retry_after = (tokens_needed / max_tokens) * refill_time
                
                return False, {
                    'tokens_remaining': 0,
                    'retry_after': int(retry_after)
                }
        else:
            # Local implementation
            bucket = self.local_storage[client_id][resource]
            
            if 'tokens' not in bucket:
                bucket['tokens'] = max_tokens
                bucket['last_refill'] = now
            
            # Refill tokens
            time_passed = now - bucket['last_refill']
            tokens_to_add = (time_passed / refill_time) * max_tokens
            bucket['tokens'] = min(max_tokens * self.burst_multiplier, bucket['tokens'] + tokens_to_add)
            bucket['last_refill'] = now
            
            if bucket['tokens'] >= 1:
                bucket['tokens'] -= 1
                return True, {
                    'tokens_remaining': int(bucket['tokens']),
                    'refill_in': refill_time
                }
            else:
                tokens_needed = 1 - bucket['tokens']
                retry_after = (tokens_needed / max_tokens) * refill_time
                
                return False, {
                    'tokens_remaining': 0,
                    'retry_after': int(retry_after)
                }
    
    async def _sliding_window(
        self,
        client_id: str,
        resource: str,
        max_requests: int,
        time_window: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Sliding window algorithm
        Most accurate but more memory intensive
        """
        now = time.time()
        window_start = now - time_window
        key = f"rate_limit:sliding:{client_id}:{resource}"
        
        if self.redis:
            # Distributed implementation using sorted sets
            pipe = self.redis.pipeline()
            
            # Remove old entries
            await pipe.zremrangebyscore(key, 0, window_start)
            
            # Count requests in window
            await pipe.zcard(key)
            
            # Execute pipeline
            results = await pipe.execute()
            request_count = results[1] if len(results) > 1 else 0
            
            if request_count < max_requests:
                # Add new request
                await self.redis.zadd(key, {str(now): now})
                await self.redis.expire(key, time_window)
                
                return True, {
                    'requests_remaining': max_requests - request_count - 1,
                    'reset_in': time_window
                }
            else:
                # Get oldest request time
                oldest = await self.redis.zrange(key, 0, 0, withscores=True)
                if oldest:
                    oldest_time = oldest[0][1]
                    retry_after = int(time_window - (now - oldest_time))
                else:
                    retry_after = time_window
                
                return False, {
                    'requests_remaining': 0,
                    'retry_after': retry_after
                }
        else:
            # Local implementation
            if resource not in self.local_storage[client_id]:
                self.local_storage[client_id][resource] = deque()
            
            window = self.local_storage[client_id][resource]
            
            # Remove old entries
            while window and window[0] < window_start:
                window.popleft()
            
            if len(window) < max_requests:
                window.append(now)
                return True, {
                    'requests_remaining': max_requests - len(window),
                    'reset_in': time_window
                }
            else:
                retry_after = int(time_window - (now - window[0]))
                return False, {
                    'requests_remaining': 0,
                    'retry_after': retry_after
                }
    
    async def _fixed_window(
        self,
        client_id: str,
        resource: str,
        max_requests: int,
        time_window: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Fixed window algorithm
        Simple but can allow 2x requests at window boundary
        """
        now = time.time()
        window_id = int(now / time_window)
        key = f"rate_limit:fixed:{client_id}:{resource}:{window_id}"
        
        if self.redis:
            # Distributed implementation
            count = await self.redis.incr(key)
            
            if count == 1:
                # First request in window
                await self.redis.expire(key, time_window)
            
            if count <= max_requests:
                return True, {
                    'requests_remaining': max_requests - count,
                    'reset_in': time_window - (int(now) % time_window)
                }
            else:
                return False, {
                    'requests_remaining': 0,
                    'retry_after': time_window - (int(now) % time_window)
                }
        else:
            # Local implementation
            window_data = self.local_storage[client_id][resource]
            
            if window_data.get('window_id') != window_id:
                # New window
                window_data['window_id'] = window_id
                window_data['count'] = 0
            
            window_data['count'] += 1
            
            if window_data['count'] <= max_requests:
                return True, {
                    'requests_remaining': max_requests - window_data['count'],
                    'reset_in': time_window - (int(now) % time_window)
                }
            else:
                return False, {
                    'requests_remaining': 0,
                    'retry_after': time_window - (int(now) % time_window)
                }
    
    async def _leaky_bucket(
        self,
        client_id: str,
        resource: str,
        max_requests: int,
        leak_rate: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Leaky bucket algorithm
        Smooth rate limiting with consistent output rate
        """
        now = time.time()
        key = f"rate_limit:leaky:{client_id}:{resource}"
        
        if self.redis:
            # Distributed implementation
            bucket_data = await self.redis.hgetall(key)
            
            if bucket_data:
                level = float(bucket_data.get(b'level', 0))
                last_leak = float(bucket_data.get(b'last_leak', now))
            else:
                level = 0
                last_leak = now
            
            # Leak water
            time_passed = now - last_leak
            leaked = (time_passed / leak_rate) * max_requests
            level = max(0, level - leaked)
            
            if level < max_requests:
                # Add water
                level += 1
                
                # Update bucket
                await self.redis.hset(key, mapping={
                    'level': level,
                    'last_leak': now
                })
                await self.redis.expire(key, leak_rate * 2)
                
                return True, {
                    'capacity_remaining': int(max_requests - level),
                    'leak_rate': leak_rate
                }
            else:
                # Bucket full
                retry_after = (1 / max_requests) * leak_rate
                
                return False, {
                    'capacity_remaining': 0,
                    'retry_after': int(retry_after)
                }
        else:
            # Local implementation
            bucket = self.local_storage[client_id][resource]
            
            if 'level' not in bucket:
                bucket['level'] = 0
                bucket['last_leak'] = now
            
            # Leak water
            time_passed = now - bucket['last_leak']
            leaked = (time_passed / leak_rate) * max_requests
            bucket['level'] = max(0, bucket['level'] - leaked)
            bucket['last_leak'] = now
            
            if bucket['level'] < max_requests:
                bucket['level'] += 1
                return True, {
                    'capacity_remaining': int(max_requests - bucket['level']),
                    'leak_rate': leak_rate
                }
            else:
                retry_after = (1 / max_requests) * leak_rate
                return False, {
                    'capacity_remaining': 0,
                    'retry_after': int(retry_after)
                }
    
    async def record_violation(self, client_id: str):
        """
        Record rate limit violation
        Temporary ban after repeated violations
        """
        self.violations[client_id] += 1
        
        # Ban thresholds
        if self.violations[client_id] >= 10:
            # 1 hour ban
            self.banned_until[client_id] = time.time() + 3600
            logger.warning(f"Client {client_id} banned for 1 hour due to repeated violations")
        elif self.violations[client_id] >= 5:
            # 5 minute ban
            self.banned_until[client_id] = time.time() + 300
            logger.warning(f"Client {client_id} banned for 5 minutes due to violations")


class RateLimitMiddleware:
    """FastAPI rate limiting middleware"""
    
    def __init__(
        self,
        rate_limiter: RateLimiter,
        resource: str = 'global',
        limit: Optional[Tuple[int, int]] = None,
        algorithm: str = 'sliding_window'
    ):
        self.rate_limiter = rate_limiter
        self.resource = resource
        self.limit = limit
        self.algorithm = algorithm
    
    async def __call__(self, request: Request, call_next):
        """Process request with rate limiting"""
        client_id = self.rate_limiter.get_client_id(request)
        
        # Check rate limit
        allowed, info = await self.rate_limiter.check_rate_limit(
            client_id,
            self.resource,
            self.limit,
            self.algorithm
        )
        
        if not allowed:
            # Record violation
            await self.rate_limiter.record_violation(client_id)
            
            # Return 429 Too Many Requests
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=info,
                headers={
                    'Retry-After': str(info.get('retry_after', 60)),
                    'X-RateLimit-Limit': str(self.limit[0] if self.limit else 60),
                    'X-RateLimit-Remaining': '0',
                    'X-RateLimit-Reset': str(int(time.time()) + info.get('retry_after', 60))
                }
            )
        
        # Add rate limit headers
        response = await call_next(request)
        response.headers['X-RateLimit-Limit'] = str(self.limit[0] if self.limit else 60)
        response.headers['X-RateLimit-Remaining'] = str(info.get('requests_remaining', 0))
        response.headers['X-RateLimit-Reset'] = str(int(time.time()) + info.get('reset_in', 60))
        
        return response


def rate_limit(
    resource: str = 'api',
    requests: int = 60,
    seconds: int = 60,
    algorithm: str = 'sliding_window'
):
    """
    Decorator for rate limiting endpoints
    
    Args:
        resource: Resource identifier
        requests: Maximum requests allowed
        seconds: Time window in seconds
        algorithm: Rate limiting algorithm
    
    Usage:
        @app.get("/api/data")
        @rate_limit(resource="data", requests=10, seconds=60)
        async def get_data():
            return {"data": "value"}
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find the Request object in arguments
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            for key, value in kwargs.items():
                if isinstance(value, Request):
                    request = value
                    break
            
            if not request:
                # No request object found, skip rate limiting
                return await func(*args, **kwargs)
            
            # Get or create rate limiter
            if not hasattr(request.app.state, 'rate_limiter'):
                request.app.state.rate_limiter = RateLimiter()
            
            rate_limiter = request.app.state.rate_limiter
            client_id = rate_limiter.get_client_id(request)
            
            # Check rate limit
            allowed, info = await rate_limiter.check_rate_limit(
                client_id,
                resource,
                (requests, seconds),
                algorithm
            )
            
            if not allowed:
                await rate_limiter.record_violation(client_id)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=info,
                    headers={'Retry-After': str(info.get('retry_after', 60))}
                )
            
            # Add rate limit info to response
            result = await func(*args, **kwargs)
            
            if hasattr(result, 'headers'):
                result.headers['X-RateLimit-Remaining'] = str(info.get('requests_remaining', 0))
            
            return result
        
        return wrapper
    return decorator


# Global rate limiter instance
_rate_limiter_instance = None

async def get_rate_limiter() -> RateLimiter:
    """Get or create global rate limiter instance"""
    global _rate_limiter_instance
    if _rate_limiter_instance is None:
        # Try to connect to Redis
        try:
            redis_client = await redis.from_url('redis://localhost:6379')
            await redis_client.ping()
            logger.info("Connected to Redis for distributed rate limiting")
        except Exception as e:
            logger.warning(f"Redis not available, using local rate limiting: {e}")
            redis_client = None
        
        _rate_limiter_instance = RateLimiter(redis_client)
    
    return _rate_limiter_instance