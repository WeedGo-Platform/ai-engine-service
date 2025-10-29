"""
Mapbox Geocoding Service
Integrates with Mapbox Geocoding API for address-to-coordinates conversion
Includes in-memory caching for performance and API quota optimization
Includes token bucket rate limiting to prevent quota exhaustion
"""

import aiohttp
import asyncio
import logging
import hashlib
import time
from typing import Optional, Dict, Any, Tuple, List
from decimal import Decimal
from collections import deque
import os

logger = logging.getLogger(__name__)


class TokenBucketRateLimiter:
    """
    Token Bucket Rate Limiter
    Ensures API calls stay within quota limits using token bucket algorithm
    """

    def __init__(
        self,
        max_requests: int = 100,
        time_window: int = 60,
        burst_size: Optional[int] = None
    ):
        """
        Initialize rate limiter

        Args:
            max_requests: Maximum requests allowed per time window
            time_window: Time window in seconds (default: 60s)
            burst_size: Maximum burst size (default: same as max_requests)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.burst_size = burst_size or max_requests
        self.tokens = float(self.burst_size)
        self.last_refill = time.time()
        self.request_history: deque = deque(maxlen=1000)
        self._lock = asyncio.Lock()

    def _refill_tokens(self) -> None:
        """Refill tokens based on time elapsed"""
        now = time.time()
        elapsed = now - self.last_refill

        # Calculate tokens to add based on elapsed time
        tokens_to_add = (elapsed / self.time_window) * self.max_requests
        self.tokens = min(self.burst_size, self.tokens + tokens_to_add)
        self.last_refill = now

    async def acquire(self, tokens: int = 1) -> bool:
        """
        Acquire tokens (wait if necessary)

        Args:
            tokens: Number of tokens to acquire (default: 1)

        Returns:
            True when tokens are acquired
        """
        async with self._lock:
            while True:
                self._refill_tokens()

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    self.request_history.append(time.time())
                    return True

                # Calculate wait time for next token
                tokens_needed = tokens - self.tokens
                wait_time = (tokens_needed / self.max_requests) * self.time_window

                logger.warning(
                    f"Rate limit approaching - waiting {wait_time:.2f}s "
                    f"(tokens: {self.tokens:.2f}/{self.burst_size})"
                )

                # Wait for tokens to refill
                await asyncio.sleep(min(wait_time, 1.0))

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        now = time.time()
        recent_requests = [
            ts for ts in self.request_history
            if now - ts < self.time_window
        ]

        return {
            "available_tokens": round(self.tokens, 2),
            "max_tokens": self.burst_size,
            "requests_last_window": len(recent_requests),
            "max_requests_per_window": self.max_requests,
            "time_window_seconds": self.time_window,
            "utilization_percent": round(
                (len(recent_requests) / self.max_requests) * 100, 1
            )
        }


class MapboxGeocodingService:
    """
    Mapbox Geocoding Service
    Handles forward and reverse geocoding using Mapbox API
    Includes in-memory caching for performance optimization
    Includes token bucket rate limiting to prevent quota exhaustion
    """

    BASE_URL = "https://api.mapbox.com/geocoding/v5/mapbox.places"

    # Mapbox free tier: 100,000 requests/month ≈ 3,280/day ≈ 137/hour ≈ 2.28/minute
    # Conservative limit: 100 requests per minute (allows bursts, stays well under quota)
    DEFAULT_RATE_LIMIT = 100  # requests per minute
    DEFAULT_TIME_WINDOW = 60  # seconds

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit: Optional[int] = None,
        time_window: Optional[int] = None
    ):
        """
        Initialize Mapbox service with caching and rate limiting

        Args:
            api_key: Mapbox API access token. If not provided, reads from env var MAPBOX_API_KEY
            rate_limit: Maximum requests per time window (default: 100/minute)
            time_window: Time window in seconds (default: 60s)
        """
        self.api_key = api_key or os.getenv('MAPBOX_API_KEY')
        if not self.api_key:
            logger.warning("Mapbox API key not configured. Geocoding will not work.")

        # In-memory cache for geocoding results (key: address_hash, value: (coords, timestamp))
        self._cache: Dict[str, Tuple[Tuple[Decimal, Decimal], float]] = {}
        self._cache_ttl = 86400  # 24 hours in seconds
        self._api_call_count = 0
        self._cache_hit_count = 0

        # Rate limiter to prevent quota exhaustion
        self._rate_limiter = TokenBucketRateLimiter(
            max_requests=rate_limit or self.DEFAULT_RATE_LIMIT,
            time_window=time_window or self.DEFAULT_TIME_WINDOW,
            burst_size=rate_limit or self.DEFAULT_RATE_LIMIT
        )
        self._rate_limit_hits = 0  # Track how many times we hit the rate limit

    def _generate_cache_key(self, street: str, city: str, province: str, postal_code: str) -> str:
        """Generate a cache key from address components"""
        # Normalize address components
        normalized = f"{street.lower().strip()}|{city.lower().strip()}|{province.upper().strip()}|{postal_code.upper().replace(' ', '')}"
        return hashlib.sha256(normalized.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[Tuple[Decimal, Decimal]]:
        """Retrieve coordinates from in-memory cache if not expired"""
        if cache_key in self._cache:
            coords, timestamp = self._cache[cache_key]
            # Check if cache entry is still valid
            if time.time() - timestamp < self._cache_ttl:
                self._cache_hit_count += 1
                logger.debug(f"Cache hit for address (hit rate: {self.get_cache_hit_rate():.1f}%)")
                return coords
            else:
                # Remove expired entry
                del self._cache[cache_key]
        return None

    def _add_to_cache(self, cache_key: str, coords: Tuple[Decimal, Decimal]) -> None:
        """Add coordinates to in-memory cache"""
        self._cache[cache_key] = (coords, time.time())
        # Limit cache size to 1000 entries (prevent memory bloat)
        if len(self._cache) > 1000:
            # Remove oldest entries
            sorted_cache = sorted(self._cache.items(), key=lambda x: x[1][1])
            self._cache = dict(sorted_cache[-1000:])

    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate percentage"""
        total_requests = self._api_call_count + self._cache_hit_count
        if total_requests == 0:
            return 0.0
        return (self._cache_hit_count / total_requests) * 100

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get caching and rate limiting statistics"""
        rate_stats = self._rate_limiter.get_stats()

        return {
            # Cache statistics
            "cache_size": len(self._cache),
            "api_calls": self._api_call_count,
            "cache_hits": self._cache_hit_count,
            "cache_hit_rate": f"{self.get_cache_hit_rate():.1f}%",
            "cache_ttl_hours": self._cache_ttl / 3600,

            # Rate limiting statistics
            "rate_limit_available_tokens": rate_stats["available_tokens"],
            "rate_limit_max_tokens": rate_stats["max_tokens"],
            "rate_limit_requests_last_window": rate_stats["requests_last_window"],
            "rate_limit_max_per_window": rate_stats["max_requests_per_window"],
            "rate_limit_utilization": f"{rate_stats['utilization_percent']}%",
            "rate_limit_delays": self._rate_limit_hits
        }

    async def geocode_address(
        self,
        street: str,
        city: str,
        province: str,
        postal_code: str
    ) -> Optional[Tuple[Decimal, Decimal]]:
        """
        Geocode a Canadian address to coordinates with caching

        Args:
            street: Street address
            city: City name
            province: Province code (e.g., 'ON', 'BC', 'QC')
            postal_code: Canadian postal code

        Returns:
            Tuple of (latitude, longitude) as Decimal, or None if not found

        Note:
            - Country is always Canada (Canadian-only service)
            - Results are cached in memory for 24 hours
            - Cache reduces API calls and improves performance
        """
        if not self.api_key:
            logger.error("Mapbox API key not configured")
            return None

        # Check cache first
        cache_key = self._generate_cache_key(street, city, province, postal_code)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result

        try:
            # Build address query for Canadian address
            # Format: "street, city, province postal_code, Canada"
            address_parts = []
            if street:
                address_parts.append(street)
            if city:
                address_parts.append(city)
            if province and postal_code:
                address_parts.append(f"{province} {postal_code}")
            elif province:
                address_parts.append(province)
            elif postal_code:
                address_parts.append(postal_code)

            # Always append Canada (cannabis delivery is Canada-only)
            address_parts.append("Canada")

            query = ", ".join(address_parts)

            # Acquire rate limit token (will wait if necessary)
            await self._rate_limiter.acquire()

            # Increment API call counter
            self._api_call_count += 1

            # Make API request with retry logic for 429 responses
            max_retries = 3
            retry_delay = 1.0

            for attempt in range(max_retries):
                url = f"{self.BASE_URL}/{query}.json"
                params = {
                    'access_token': self.api_key,
                    'country': 'CA',  # Always Canada - cannabis delivery restriction
                    'limit': 1,
                    'types': 'address,place',  # Focus on addresses
                    'autocomplete': 'false'  # We want exact matches only (string not bool)
                }

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        # Handle rate limit exceeded (429)
                        if response.status == 429:
                            self._rate_limit_hits += 1
                            if attempt < max_retries - 1:
                                # Exponential backoff
                                wait_time = retry_delay * (2 ** attempt)
                                logger.warning(
                                    f"Mapbox rate limit exceeded (429) - "
                                    f"retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})"
                                )
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                logger.error("Mapbox rate limit exceeded - max retries reached")
                                return None

                        # Handle other errors
                        if response.status != 200:
                            logger.error(f"Mapbox API error: {response.status}")
                            return None

                        data = await response.json()

                        if not data.get('features'):
                            logger.warning(f"No results found for address: {query}")
                            return None

                        # Get first result
                        feature = data['features'][0]
                        coordinates = feature.get('geometry', {}).get('coordinates', [])

                        if len(coordinates) != 2:
                            logger.error(f"Invalid coordinates format: {coordinates}")
                            return None

                        # Mapbox returns [longitude, latitude]
                        longitude, latitude = coordinates

                        # Log the matched address for verification
                        place_name = feature.get('place_name', 'Unknown')
                        relevance = feature.get('relevance', 0)
                        logger.info(f"Geocoded '{query}' to ({latitude}, {longitude}) - Matched: '{place_name}' (relevance: {relevance})")

                        result = (Decimal(str(latitude)), Decimal(str(longitude)))

                        # Add to cache
                        self._add_to_cache(cache_key, result)

                        return result

        except aiohttp.ClientError as e:
            logger.error(f"HTTP error geocoding address: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error geocoding address: {e}")
            return None

    async def reverse_geocode(
        self,
        latitude: float,
        longitude: float
    ) -> Optional[Dict[str, str]]:
        """
        Reverse geocode coordinates to address

        Args:
            latitude: Latitude
            longitude: Longitude

        Returns:
            Dictionary with address components, or None if not found
        """
        if not self.api_key:
            logger.error("Mapbox API key not configured")
            return None

        try:
            # Acquire rate limit token (will wait if necessary)
            await self._rate_limiter.acquire()

            # Increment API call counter
            self._api_call_count += 1

            # Make API request with retry logic for 429 responses
            max_retries = 3
            retry_delay = 1.0

            for attempt in range(max_retries):
                # Format: longitude,latitude (note the order!)
                url = f"{self.BASE_URL}/{longitude},{latitude}.json"
                params = {
                    'access_token': self.api_key,
                    'types': 'address',
                    'limit': 1
                }

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        # Handle rate limit exceeded (429)
                        if response.status == 429:
                            self._rate_limit_hits += 1
                            if attempt < max_retries - 1:
                                # Exponential backoff
                                wait_time = retry_delay * (2 ** attempt)
                                logger.warning(
                                    f"Mapbox rate limit exceeded (429) - "
                                    f"retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})"
                                )
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                logger.error("Mapbox rate limit exceeded - max retries reached")
                                return None

                        # Handle other errors
                        if response.status != 200:
                            logger.error(f"Mapbox API error: {response.status}")
                            return None

                        data = await response.json()

                        if not data.get('features'):
                            logger.warning(f"No results found for coordinates: ({latitude}, {longitude})")
                            return None

                        # Parse address components
                        feature = data['features'][0]
                        context = {item['id'].split('.')[0]: item['text']
                                  for item in feature.get('context', [])}

                        address = {
                            'street': feature.get('text', ''),
                            'address_number': feature.get('address', ''),
                            'city': context.get('place', ''),
                            'province': context.get('region', ''),
                            'postal_code': context.get('postcode', ''),
                            'country': context.get('country', ''),
                            'full_address': feature.get('place_name', '')
                        }

                        # Combine address number and street
                        if address['address_number']:
                            address['street'] = f"{address['address_number']} {address['street']}"

                        return address

        except aiohttp.ClientError as e:
            logger.error(f"HTTP error reverse geocoding: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error reverse geocoding: {e}")
            return None

    async def autocomplete_address(
        self,
        query: str,
        proximity: Optional[Tuple[float, float]] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Autocomplete address search for Canadian addresses

        Args:
            query: Partial address search query (e.g., "123 Main", "Toronto ON")
            proximity: Optional (latitude, longitude) tuple to bias results
            limit: Maximum number of suggestions to return (default: 5, max: 10)

        Returns:
            List of address suggestions with structured data

        Example response:
            [
                {
                    "id": "address.123",
                    "place_name": "123 Main Street, Toronto, Ontario M5V 3A8, Canada",
                    "address": {
                        "street": "123 Main Street",
                        "city": "Toronto",
                        "province": "ON",
                        "postal_code": "M5V 3A8",
                        "country": "Canada"
                    },
                    "coordinates": {
                        "latitude": 43.6532,
                        "longitude": -79.3832
                    },
                    "relevance": 0.95
                }
            ]
        """
        if not self.api_key:
            logger.error("Mapbox API key not configured")
            return []

        # Limit max suggestions to 10 (Mapbox API limit)
        limit = min(limit, 10)

        try:
            # Acquire rate limit token
            await self._rate_limiter.acquire()
            self._api_call_count += 1

            # Build query URL
            url = f"{self.BASE_URL}/{query}.json"

            params = {
                'access_token': self.api_key,
                'country': 'CA',  # Canada only
                'types': 'address,place',  # Focus on addresses and places
                'autocomplete': 'true',  # Enable autocomplete
                'limit': limit,
                'language': 'en'  # English results
            }

            # Add proximity bias if provided (biases results near customer location)
            if proximity:
                lat, lng = proximity
                params['proximity'] = f"{lng},{lat}"  # Mapbox uses lng,lat order

            # Make API request with retry logic
            max_retries = 3
            retry_delay = 1.0

            for attempt in range(max_retries):
                # Create session with longer timeout for slow networks
                timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=20)
                connector = aiohttp.TCPConnector(ssl=False)  # Disable SSL verification temporarily
                
                async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                    async with session.get(url, params=params) as response:
                        # Handle rate limit
                        if response.status == 429:
                            self._rate_limit_hits += 1
                            if attempt < max_retries - 1:
                                wait_time = retry_delay * (2 ** attempt)
                                logger.warning(f"Mapbox rate limit - retrying in {wait_time}s")
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                logger.error("Mapbox rate limit - max retries reached")
                                return []

                        if response.status != 200:
                            logger.error(f"Mapbox autocomplete error: {response.status}")
                            return []

                        data = await response.json()

                        if not data.get('features'):
                            return []

                        # Parse results into structured format
                        suggestions = []
                        for feature in data['features']:
                            # Extract coordinates (Mapbox returns [lng, lat])
                            coords = feature.get('geometry', {}).get('coordinates', [])
                            if len(coords) != 2:
                                continue

                            longitude, latitude = coords

                            # Extract address components from context
                            context = {
                                item['id'].split('.')[0]: item['text']
                                for item in feature.get('context', [])
                            }

                            # Build structured address
                            address_number = feature.get('address', '')
                            street_name = feature.get('text', '')
                            street = f"{address_number} {street_name}" if address_number else street_name

                            suggestion = {
                                'id': feature.get('id', ''),
                                'place_name': feature.get('place_name', ''),
                                'address': {
                                    'street': street,
                                    'city': context.get('place', ''),
                                    'province': context.get('region', ''),
                                    'postal_code': context.get('postcode', ''),
                                    'country': context.get('country', 'Canada')
                                },
                                'coordinates': {
                                    'latitude': latitude,
                                    'longitude': longitude
                                },
                                'relevance': feature.get('relevance', 0)
                            }

                            suggestions.append(suggestion)

                        logger.info(f"Autocomplete returned {len(suggestions)} suggestions for '{query}'")
                        return suggestions

        except aiohttp.ClientError as e:
            logger.error(f"HTTP error in autocomplete: {e}")
            logger.error(f"Failed to connect to Mapbox API - check network connectivity and firewall settings")
            return []
        except asyncio.TimeoutError as e:
            logger.error(f"Timeout error in autocomplete: {e}")
            logger.error(f"Mapbox API request timed out after 10 seconds - check network connectivity")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in autocomplete: {e}", exc_info=True)
            return []

    async def validate_api_key(self) -> bool:
        """
        Validate that the API key works with a Canadian address

        Returns:
            True if API key is valid, False otherwise
        """
        if not self.api_key:
            return False

        try:
            # Test with a known Canadian address
            result = await self.geocode_address(
                street="1 Yonge Street",
                city="Toronto",
                province="ON",
                postal_code="M5E 1W7"
            )
            return result is not None
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False
