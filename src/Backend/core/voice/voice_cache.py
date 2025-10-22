"""
Voice Synthesis Cache - Redis-backed audio caching
Caches synthesized audio to avoid regenerating identical requests
"""

import hashlib
import logging
import redis
from typing import Optional, Dict
from datetime import timedelta

logger = logging.getLogger(__name__)


class VoiceCache:
    """
    Redis-based cache for synthesized voice audio

    Features:
    - Content-based caching (hash of text + personality + settings)
    - Automatic expiration (default 7 days)
    - Size limits to prevent cache bloat
    - Cache statistics tracking
    - Efficient binary storage for audio data

    Cache Key Format:
        voice:audio:{hash}
        voice:metadata:{hash}
        voice:stats

    Example:
        cache = VoiceCache()

        # Try to get from cache
        audio = cache.get(text, personality_id, language)

        if audio is None:
            # Cache miss - synthesize
            audio = await synthesize_voice(...)
            cache.set(text, personality_id, language, audio, metadata)
    """

    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        ttl_days: int = 7,
        max_audio_size_mb: int = 10
    ):
        """
        Initialize voice cache

        Args:
            redis_host: Redis server hostname
            redis_port: Redis server port
            redis_db: Redis database number
            ttl_days: Time-to-live for cached audio (days)
            max_audio_size_mb: Maximum audio file size to cache (MB)
        """
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_db = redis_db
        self.ttl = timedelta(days=ttl_days)
        self.max_audio_size = max_audio_size_mb * 1024 * 1024  # Convert to bytes

        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=False  # We store binary data
            )
            # Test connection
            self.redis_client.ping()
            logger.info(
                f"✓ Voice cache connected to Redis "
                f"({redis_host}:{redis_port}/{redis_db})"
            )
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None

    def _generate_cache_key(
        self,
        text: str,
        personality_id: str,
        language: str = "en",
        speed: float = 1.0,
        pitch: float = 0.0,
        quality: str = "high"
    ) -> str:
        """
        Generate deterministic cache key from synthesis parameters

        Uses SHA256 hash of all parameters that affect output

        Args:
            text: Text to synthesize
            personality_id: Personality UUID
            language: Language code
            speed: Speech speed multiplier
            pitch: Pitch adjustment
            quality: Quality level

        Returns:
            Cache key string
        """
        # Normalize parameters
        text_normalized = text.strip().lower()

        # Create deterministic string from all parameters
        cache_string = f"{text_normalized}|{personality_id}|{language}|{speed}|{pitch}|{quality}"

        # Generate SHA256 hash
        hash_obj = hashlib.sha256(cache_string.encode('utf-8'))
        hash_key = hash_obj.hexdigest()[:16]  # Use first 16 chars for readability

        return hash_key

    def get(
        self,
        text: str,
        personality_id: str,
        language: str = "en",
        speed: float = 1.0,
        pitch: float = 0.0,
        quality: str = "high"
    ) -> Optional[Dict]:
        """
        Get cached audio if available

        Args:
            text: Text that was synthesized
            personality_id: Personality UUID
            language: Language code
            speed: Speech speed
            pitch: Pitch adjustment
            quality: Quality level

        Returns:
            Dict with audio_data and metadata, or None if cache miss
        """
        if not self.redis_client:
            return None

        try:
            # Generate cache key
            cache_key = self._generate_cache_key(
                text, personality_id, language, speed, pitch, quality
            )

            # Try to get audio data
            audio_key = f"voice:audio:{cache_key}"
            metadata_key = f"voice:metadata:{cache_key}"

            audio_data = self.redis_client.get(audio_key)
            metadata_data = self.redis_client.get(metadata_key)

            if audio_data and metadata_data:
                # Cache hit
                import json
                metadata = json.loads(metadata_data.decode('utf-8'))

                logger.info(
                    f"✓ Cache HIT: {cache_key[:8]}... "
                    f"({len(audio_data) / 1024:.1f}KB)"
                )

                # Update stats
                self._increment_stat("hits")

                return {
                    "audio_data": audio_data,
                    "metadata": metadata
                }
            else:
                # Cache miss
                logger.debug(f"✗ Cache MISS: {cache_key[:8]}...")
                self._increment_stat("misses")
                return None

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(
        self,
        text: str,
        personality_id: str,
        audio_data: bytes,
        metadata: Dict,
        language: str = "en",
        speed: float = 1.0,
        pitch: float = 0.0,
        quality: str = "high"
    ) -> bool:
        """
        Cache synthesized audio

        Args:
            text: Text that was synthesized
            personality_id: Personality UUID
            audio_data: Synthesized audio (WAV bytes)
            metadata: Audio metadata (provider, duration, sample_rate, etc.)
            language: Language code
            speed: Speech speed
            pitch: Pitch adjustment
            quality: Quality level

        Returns:
            True if cached successfully
        """
        if not self.redis_client:
            return False

        try:
            # Check audio size
            audio_size = len(audio_data)
            if audio_size > self.max_audio_size:
                logger.warning(
                    f"Audio too large to cache: {audio_size / 1024 / 1024:.1f}MB "
                    f"(max: {self.max_audio_size / 1024 / 1024:.1f}MB)"
                )
                return False

            # Generate cache key
            cache_key = self._generate_cache_key(
                text, personality_id, language, speed, pitch, quality
            )

            # Store audio data
            audio_key = f"voice:audio:{cache_key}"
            metadata_key = f"voice:metadata:{cache_key}"

            # Serialize metadata
            import json
            metadata_json = json.dumps(metadata).encode('utf-8')

            # Store with TTL
            ttl_seconds = int(self.ttl.total_seconds())

            self.redis_client.setex(audio_key, ttl_seconds, audio_data)
            self.redis_client.setex(metadata_key, ttl_seconds, metadata_json)

            logger.info(
                f"✓ Cached audio: {cache_key[:8]}... "
                f"({audio_size / 1024:.1f}KB, TTL: {self.ttl.days}d)"
            )

            # Update stats
            self._increment_stat("sets")

            return True

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def invalidate_personality(self, personality_id: str) -> int:
        """
        Invalidate all cached audio for a personality

        Useful when personality voice sample is updated or deleted

        Args:
            personality_id: Personality UUID

        Returns:
            Number of cache entries deleted
        """
        if not self.redis_client:
            return 0

        try:
            # Find all keys for this personality
            # Note: This uses pattern matching which can be slow on large datasets
            pattern = f"voice:*:*{personality_id}*"

            keys = []
            cursor = 0
            while True:
                cursor, batch_keys = self.redis_client.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )
                keys.extend(batch_keys)
                if cursor == 0:
                    break

            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(
                    f"✓ Invalidated {deleted} cache entries for "
                    f"personality {personality_id}"
                )
                return deleted
            else:
                logger.debug(f"No cache entries found for personality {personality_id}")
                return 0

        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return 0

    def clear_all(self) -> bool:
        """
        Clear all voice cache entries

        WARNING: This clears ALL voice cache data

        Returns:
            True if successful
        """
        if not self.redis_client:
            return False

        try:
            # Find all voice cache keys
            pattern = "voice:*"

            keys = []
            cursor = 0
            while True:
                cursor, batch_keys = self.redis_client.scan(
                    cursor=cursor,
                    match=pattern,
                    count=1000
                )
                keys.extend(batch_keys)
                if cursor == 0:
                    break

            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"✓ Cleared {deleted} cache entries")
                return True
            else:
                logger.debug("Cache already empty")
                return True

        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False

    def _increment_stat(self, stat_name: str):
        """Increment cache statistic counter"""
        if not self.redis_client:
            return

        try:
            self.redis_client.hincrby("voice:stats", stat_name, 1)
        except Exception:
            pass  # Stats are non-critical

    def get_stats(self) -> Dict:
        """
        Get cache statistics

        Returns:
            Dict with hits, misses, sets, and hit rate
        """
        if not self.redis_client:
            return {
                "enabled": False,
                "hits": 0,
                "misses": 0,
                "sets": 0,
                "hit_rate": 0.0
            }

        try:
            stats = self.redis_client.hgetall("voice:stats")

            # Decode bytes to integers
            hits = int(stats.get(b"hits", 0))
            misses = int(stats.get(b"misses", 0))
            sets = int(stats.get(b"sets", 0))

            total_requests = hits + misses
            hit_rate = (hits / total_requests * 100) if total_requests > 0 else 0.0

            return {
                "enabled": True,
                "hits": hits,
                "misses": misses,
                "sets": sets,
                "hit_rate": hit_rate,
                "total_requests": total_requests
            }

        except Exception as e:
            logger.error(f"Get stats error: {e}")
            return {
                "enabled": False,
                "error": str(e)
            }
