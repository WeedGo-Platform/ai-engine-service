"""
Redis Verification Store
Production-ready verification code storage using Redis
Replaces in-memory storage for horizontal scalability
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import redis
from redis import Redis, ConnectionPool
import os

logger = logging.getLogger(__name__)


class RedisVerificationStore:
    """
    Redis-based verification code storage
    Provides distributed, scalable storage for verification codes and tokens
    """

    def __init__(self, redis_client: Optional[Redis] = None):
        """
        Initialize Redis verification store

        Args:
            redis_client: Optional Redis client instance (creates new if None)
        """
        if redis_client:
            self.redis = redis_client
        else:
            # Create Redis connection from environment variables
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            redis_db = int(os.getenv('REDIS_DB', 0))
            redis_password = os.getenv('REDIS_PASSWORD')

            # Create connection pool for better performance
            pool = ConnectionPool(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True,  # Automatically decode responses to strings
                max_connections=50,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )

            self.redis = Redis(connection_pool=pool)

        # Test connection
        try:
            self.redis.ping()
            logger.info(f"Redis verification store connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def store_verification_code(
        self,
        verification_id: str,
        code_hash: str,
        email: str,
        store_info: Dict[str, Any],
        verification_tier: str,
        phone: Optional[str] = None,
        expiry_minutes: int = 5,
        max_attempts: int = 3
    ) -> bool:
        """
        Store verification code in Redis

        Args:
            verification_id: Unique verification ID
            code_hash: SHA-256 hash of verification code
            email: User's email address
            store_info: Store information from CRSA
            verification_tier: "auto_approved" or "manual_review"
            phone: Optional phone number
            expiry_minutes: Minutes until code expires
            max_attempts: Maximum verification attempts

        Returns:
            True if stored successfully, False otherwise
        """
        try:
            verification_data = {
                'verification_id': verification_id,
                'code_hash': code_hash,
                'email': email,
                'store_info': json.dumps(store_info),
                'verification_tier': verification_tier,
                'phone': phone or '',
                'attempts': 0,
                'max_attempts': max_attempts,
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(minutes=expiry_minutes)).isoformat(),
                'verified': False
            }

            # Store in Redis with expiry
            key = f"verification:{verification_id}"
            pipe = self.redis.pipeline()
            pipe.hmset(key, verification_data)
            pipe.expire(key, expiry_minutes * 60)  # Set TTL in seconds
            pipe.execute()

            logger.info(f"Stored verification code in Redis: {verification_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to store verification code in Redis: {e}")
            return False

    def get_verification_code(self, verification_id: str) -> Optional[Dict[str, Any]]:
        """
        Get verification code data from Redis

        Args:
            verification_id: Verification ID

        Returns:
            Verification data dictionary or None if not found
        """
        try:
            key = f"verification:{verification_id}"
            data = self.redis.hgetall(key)

            if not data:
                return None

            # Parse store_info JSON
            if 'store_info' in data:
                data['store_info'] = json.loads(data['store_info'])

            # Convert string numbers to integers
            if 'attempts' in data:
                data['attempts'] = int(data['attempts'])
            if 'max_attempts' in data:
                data['max_attempts'] = int(data['max_attempts'])

            # Convert verified to boolean
            if 'verified' in data:
                data['verified'] = data['verified'].lower() == 'true'

            return data

        except Exception as e:
            logger.error(f"Failed to get verification code from Redis: {e}")
            return None

    def increment_attempts(self, verification_id: str) -> int:
        """
        Increment verification attempts counter

        Args:
            verification_id: Verification ID

        Returns:
            New attempt count
        """
        try:
            key = f"verification:{verification_id}"
            attempts = self.redis.hincrby(key, 'attempts', 1)
            logger.info(f"Incremented attempts for {verification_id}: {attempts}")
            return attempts

        except Exception as e:
            logger.error(f"Failed to increment attempts in Redis: {e}")
            return 0

    def mark_verified(self, verification_id: str) -> bool:
        """
        Mark verification code as verified

        Args:
            verification_id: Verification ID

        Returns:
            True if marked successfully, False otherwise
        """
        try:
            key = f"verification:{verification_id}"
            self.redis.hset(key, 'verified', 'true')
            logger.info(f"Marked verification as verified: {verification_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to mark verification in Redis: {e}")
            return False

    def delete_verification_code(self, verification_id: str) -> bool:
        """
        Delete verification code from Redis

        Args:
            verification_id: Verification ID

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            key = f"verification:{verification_id}"
            self.redis.delete(key)
            logger.info(f"Deleted verification code: {verification_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete verification code from Redis: {e}")
            return False

    # Password setup tokens

    def store_password_token(
        self,
        token: str,
        tenant_id: str,
        email: str,
        expiry_hours: int = 24
    ) -> bool:
        """
        Store password setup token in Redis

        Args:
            token: Password setup token
            tenant_id: Tenant ID
            email: User's email address
            expiry_hours: Hours until token expires

        Returns:
            True if stored successfully, False otherwise
        """
        try:
            token_data = {
                'token': token,
                'tenant_id': tenant_id,
                'email': email,
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(hours=expiry_hours)).isoformat(),
                'used': False
            }

            # Store in Redis with expiry
            key = f"password_token:{token}"
            pipe = self.redis.pipeline()
            pipe.hmset(key, token_data)
            pipe.expire(key, expiry_hours * 3600)  # Set TTL in seconds
            pipe.execute()

            logger.info(f"Stored password token in Redis for tenant {tenant_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to store password token in Redis: {e}")
            return False

    def get_password_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get password token data from Redis

        Args:
            token: Password setup token

        Returns:
            Token data dictionary or None if not found
        """
        try:
            key = f"password_token:{token}"
            data = self.redis.hgetall(key)

            if not data:
                return None

            # Convert used to boolean
            if 'used' in data:
                data['used'] = data['used'].lower() == 'true'

            return data

        except Exception as e:
            logger.error(f"Failed to get password token from Redis: {e}")
            return None

    def mark_password_token_used(self, token: str) -> bool:
        """
        Mark password token as used

        Args:
            token: Password setup token

        Returns:
            True if marked successfully, False otherwise
        """
        try:
            key = f"password_token:{token}"
            self.redis.hset(key, 'used', 'true')
            logger.info(f"Marked password token as used: {token}")
            return True

        except Exception as e:
            logger.error(f"Failed to mark password token in Redis: {e}")
            return False

    # Rate limiting

    def check_rate_limit(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """
        Check if request is within rate limit

        Args:
            identifier: Unique identifier (e.g., email address)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            True if within rate limit, False if exceeded
        """
        try:
            key = f"rate_limit:{identifier}"
            current = self.redis.get(key)

            if current is None:
                # First request in window
                pipe = self.redis.pipeline()
                pipe.set(key, 1)
                pipe.expire(key, window_seconds)
                pipe.execute()
                return True

            current_count = int(current)
            if current_count >= max_requests:
                logger.warning(f"Rate limit exceeded for {identifier}: {current_count}/{max_requests}")
                return False

            # Increment counter
            self.redis.incr(key)
            return True

        except Exception as e:
            logger.error(f"Failed to check rate limit in Redis: {e}")
            # Fail open - allow request if Redis is unavailable
            return True

    def cleanup_expired(self) -> int:
        """
        Cleanup expired verification codes (Redis TTL handles this automatically)
        This method is provided for compatibility with in-memory store

        Returns:
            Number of keys cleaned up (always 0 for Redis with TTL)
        """
        logger.info("Redis TTL handles automatic cleanup")
        return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics

        Returns:
            Statistics dictionary
        """
        try:
            verification_keys = len(self.redis.keys("verification:*"))
            password_keys = len(self.redis.keys("password_token:*"))
            rate_limit_keys = len(self.redis.keys("rate_limit:*"))

            return {
                'storage_type': 'redis',
                'active_verifications': verification_keys,
                'active_password_tokens': password_keys,
                'active_rate_limits': rate_limit_keys,
                'redis_info': self.redis.info('memory')
            }

        except Exception as e:
            logger.error(f"Failed to get stats from Redis: {e}")
            return {'error': str(e)}


# Global singleton instance
_redis_store: Optional[RedisVerificationStore] = None


def get_redis_verification_store(redis_client: Optional[Redis] = None) -> RedisVerificationStore:
    """Get or create Redis verification store singleton"""
    global _redis_store

    if _redis_store is None:
        _redis_store = RedisVerificationStore(redis_client)

    return _redis_store
