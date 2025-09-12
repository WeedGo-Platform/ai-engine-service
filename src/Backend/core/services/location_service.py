"""
Location Service Module
Provides spatial calculations and location-based services following SOLID principles
"""

import math
from typing import Tuple, List, Dict, Optional, Any
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
import hashlib
import json
import asyncpg
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class DistanceUnit(Enum):
    """Enumeration for distance units"""
    KILOMETERS = 'km'
    MILES = 'mi'
    METERS = 'm'
    FEET = 'ft'


@dataclass
class Coordinates:
    """Value object for geographic coordinates"""
    latitude: float
    longitude: float
    
    def __post_init__(self):
        """Validate coordinates on initialization"""
        if not -90 <= self.latitude <= 90:
            raise ValueError(f"Invalid latitude: {self.latitude}. Must be between -90 and 90")
        if not -180 <= self.longitude <= 180:
            raise ValueError(f"Invalid longitude: {self.longitude}. Must be between -180 and 180")
    
    def to_tuple(self) -> Tuple[float, float]:
        """Convert to tuple (lat, lng)"""
        return (self.latitude, self.longitude)
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {"latitude": self.latitude, "longitude": self.longitude}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Coordinates':
        """Create from dictionary"""
        return cls(
            latitude=float(data.get('latitude', data.get('lat', 0))),
            longitude=float(data.get('longitude', data.get('lng', data.get('lon', 0))))
        )


@dataclass
class LocationBounds:
    """Value object for geographic bounding box"""
    north: float
    south: float
    east: float
    west: float
    
    def contains(self, coords: Coordinates) -> bool:
        """Check if coordinates are within bounds"""
        return (self.south <= coords.latitude <= self.north and 
                self.west <= coords.longitude <= self.east)
    
    def expand(self, kilometers: float) -> 'LocationBounds':
        """Expand bounds by given distance in kilometers"""
        lat_delta = kilometers / 111.0  # Approximate km per degree latitude
        lng_delta = kilometers / (111.0 * math.cos(math.radians((self.north + self.south) / 2)))
        
        return LocationBounds(
            north=self.north + lat_delta,
            south=self.south - lat_delta,
            east=self.east + lng_delta,
            west=self.west - lng_delta
        )


class HaversineCalculator:
    """
    Haversine distance calculator
    Implements the haversine formula for calculating distances between geographic points
    """
    
    EARTH_RADIUS_KM = 6371.0
    EARTH_RADIUS_MI = 3958.8
    
    @staticmethod
    def calculate_distance(
        point1: Coordinates,
        point2: Coordinates,
        unit: DistanceUnit = DistanceUnit.KILOMETERS
    ) -> float:
        """
        Calculate distance between two geographic points using haversine formula
        
        Args:
            point1: First coordinate point
            point2: Second coordinate point
            unit: Unit for distance (default: kilometers)
            
        Returns:
            Distance between points in specified unit
        """
        # Convert to radians
        lat1_rad = math.radians(point1.latitude)
        lat2_rad = math.radians(point2.latitude)
        delta_lat = math.radians(point2.latitude - point1.latitude)
        delta_lon = math.radians(point2.longitude - point1.longitude)
        
        # Haversine formula
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        # Calculate distance based on unit
        if unit == DistanceUnit.KILOMETERS:
            distance = HaversineCalculator.EARTH_RADIUS_KM * c
        elif unit == DistanceUnit.MILES:
            distance = HaversineCalculator.EARTH_RADIUS_MI * c
        elif unit == DistanceUnit.METERS:
            distance = HaversineCalculator.EARTH_RADIUS_KM * c * 1000
        elif unit == DistanceUnit.FEET:
            distance = HaversineCalculator.EARTH_RADIUS_MI * c * 5280
        else:
            distance = HaversineCalculator.EARTH_RADIUS_KM * c
        
        return round(distance, 2)
    
    @staticmethod
    def calculate_bearing(
        point1: Coordinates,
        point2: Coordinates
    ) -> float:
        """
        Calculate bearing between two points
        
        Args:
            point1: Starting point
            point2: Destination point
            
        Returns:
            Bearing in degrees (0-360)
        """
        lat1_rad = math.radians(point1.latitude)
        lat2_rad = math.radians(point2.latitude)
        delta_lon = math.radians(point2.longitude - point1.longitude)
        
        x = math.sin(delta_lon) * math.cos(lat2_rad)
        y = (math.cos(lat1_rad) * math.sin(lat2_rad) - 
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon))
        
        bearing = math.degrees(math.atan2(x, y))
        return (bearing + 360) % 360
    
    @staticmethod
    def calculate_destination(
        origin: Coordinates,
        bearing: float,
        distance_km: float
    ) -> Coordinates:
        """
        Calculate destination point given origin, bearing, and distance
        
        Args:
            origin: Starting coordinates
            bearing: Bearing in degrees
            distance_km: Distance in kilometers
            
        Returns:
            Destination coordinates
        """
        lat1_rad = math.radians(origin.latitude)
        lon1_rad = math.radians(origin.longitude)
        bearing_rad = math.radians(bearing)
        
        lat2_rad = math.asin(
            math.sin(lat1_rad) * math.cos(distance_km / HaversineCalculator.EARTH_RADIUS_KM) +
            math.cos(lat1_rad) * math.sin(distance_km / HaversineCalculator.EARTH_RADIUS_KM) * 
            math.cos(bearing_rad)
        )
        
        lon2_rad = lon1_rad + math.atan2(
            math.sin(bearing_rad) * math.sin(distance_km / HaversineCalculator.EARTH_RADIUS_KM) * 
            math.cos(lat1_rad),
            math.cos(distance_km / HaversineCalculator.EARTH_RADIUS_KM) - 
            math.sin(lat1_rad) * math.sin(lat2_rad)
        )
        
        return Coordinates(
            latitude=math.degrees(lat2_rad),
            longitude=math.degrees(lon2_rad)
        )
    
    @staticmethod
    def get_bounding_box(
        center: Coordinates,
        radius_km: float
    ) -> LocationBounds:
        """
        Calculate bounding box for a circular area
        
        Args:
            center: Center coordinates
            radius_km: Radius in kilometers
            
        Returns:
            Bounding box containing the circular area
        """
        # Calculate approximate bounding box
        lat_delta = radius_km / 111.0
        lng_delta = radius_km / (111.0 * math.cos(math.radians(center.latitude)))
        
        return LocationBounds(
            north=center.latitude + lat_delta,
            south=center.latitude - lat_delta,
            east=center.longitude + lng_delta,
            west=center.longitude - lng_delta
        )


class GeocodingService:
    """
    Service for geocoding addresses to coordinates
    Implements caching and multiple provider support
    """
    
    def __init__(self, db_pool: Optional[asyncpg.Pool] = None):
        """Initialize geocoding service with optional database pool for caching"""
        self.db_pool = db_pool
        self.cache_enabled = db_pool is not None
    
    def _normalize_address(self, address: str) -> str:
        """Normalize address for consistent caching"""
        # Convert to lowercase, remove extra spaces
        normalized = ' '.join(address.lower().split())
        # Remove common punctuation
        for char in [',', '.', '-', '#']:
            normalized = normalized.replace(char, ' ')
        normalized = ' '.join(normalized.split())
        return normalized
    
    def _get_cache_key(self, address: str) -> str:
        """Generate cache key for address"""
        normalized = self._normalize_address(address)
        return hashlib.sha256(normalized.encode()).hexdigest()
    
    async def geocode_address(
        self,
        address: str,
        city: Optional[str] = None,
        province: Optional[str] = None,
        postal_code: Optional[str] = None,
        country: str = "Canada"
    ) -> Optional[Coordinates]:
        """
        Geocode an address to coordinates
        
        Args:
            address: Street address
            city: City name
            province: Province/state
            postal_code: Postal/ZIP code
            country: Country name
            
        Returns:
            Coordinates if found, None otherwise
        """
        # Build full address
        address_parts = [part for part in [address, city, province, postal_code, country] if part]
        full_address = ", ".join(address_parts)
        
        # Check cache first
        if self.cache_enabled:
            cached = await self._get_cached_coordinates(full_address)
            if cached:
                logger.info(f"Using cached coordinates for: {full_address}")
                return cached
        
        # For production, integrate with real geocoding service
        # This is a placeholder that would call Google Maps, Mapbox, or Nominatim
        coordinates = await self._call_geocoding_api(full_address)
        
        # Cache the result
        if coordinates and self.cache_enabled:
            await self._cache_coordinates(full_address, coordinates)
        
        return coordinates
    
    async def _get_cached_coordinates(self, address: str) -> Optional[Coordinates]:
        """Retrieve cached coordinates from database"""
        if not self.db_pool:
            return None
        
        cache_key = self._get_cache_key(address)
        
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT latitude, longitude 
                    FROM geocoding_cache 
                    WHERE address_hash = $1 
                      AND expires_at > CURRENT_TIMESTAMP
                """, cache_key)
                
                if row:
                    return Coordinates(
                        latitude=float(row['latitude']),
                        longitude=float(row['longitude'])
                    )
        except Exception as e:
            logger.error(f"Error retrieving cached coordinates: {e}")
        
        return None
    
    async def _cache_coordinates(
        self,
        address: str,
        coordinates: Coordinates,
        provider: str = "manual",
        confidence: float = 1.0
    ):
        """Cache coordinates in database"""
        if not self.db_pool:
            return
        
        cache_key = self._get_cache_key(address)
        
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO geocoding_cache 
                    (address_hash, full_address, latitude, longitude, location, 
                     provider, confidence_score, expires_at)
                    VALUES ($1, $2, $3, $4, 
                            ST_SetSRID(ST_MakePoint($4, $3), 4326)::geography,
                            $5, $6, CURRENT_TIMESTAMP + INTERVAL '90 days')
                    ON CONFLICT (address_hash) 
                    DO UPDATE SET 
                        latitude = EXCLUDED.latitude,
                        longitude = EXCLUDED.longitude,
                        location = EXCLUDED.location,
                        updated_at = CURRENT_TIMESTAMP,
                        expires_at = CURRENT_TIMESTAMP + INTERVAL '90 days'
                """, cache_key, address, coordinates.latitude, coordinates.longitude,
                    provider, confidence)
        except Exception as e:
            logger.error(f"Error caching coordinates: {e}")
    
    async def _call_geocoding_api(self, address: str) -> Optional[Coordinates]:
        """
        Call external geocoding API
        This is a placeholder for integration with real geocoding services
        """
        # For development/testing, return approximate coordinates for major Canadian cities
        test_locations = {
            "toronto": Coordinates(43.6532, -79.3832),
            "vancouver": Coordinates(49.2827, -123.1207),
            "montreal": Coordinates(45.5017, -73.5673),
            "calgary": Coordinates(51.0447, -114.0719),
            "ottawa": Coordinates(45.4215, -75.6972),
            "edmonton": Coordinates(53.5461, -113.4938),
            "winnipeg": Coordinates(49.8951, -97.1384),
            "quebec": Coordinates(46.8139, -71.2080),
            "halifax": Coordinates(44.6488, -63.5752),
            "victoria": Coordinates(48.4284, -123.3656),
        }
        
        # Check if address contains any test city
        address_lower = address.lower()
        for city, coords in test_locations.items():
            if city in address_lower:
                return coords
        
        # Default to Toronto for testing
        logger.warning(f"Using default coordinates for: {address}")
        return test_locations["toronto"]
    
    async def reverse_geocode(
        self,
        coordinates: Coordinates
    ) -> Optional[Dict[str, str]]:
        """
        Reverse geocode coordinates to address
        
        Args:
            coordinates: Geographic coordinates
            
        Returns:
            Address components dictionary
        """
        # Check cache first
        if self.cache_enabled:
            cached = await self._get_cached_address(coordinates)
            if cached:
                return cached
        
        # Call reverse geocoding API (placeholder)
        address = await self._call_reverse_geocoding_api(coordinates)
        
        # Cache the result
        if address and self.cache_enabled:
            await self._cache_address(coordinates, address)
        
        return address
    
    async def _get_cached_address(self, coordinates: Coordinates) -> Optional[Dict[str, str]]:
        """Retrieve cached address from database"""
        if not self.db_pool:
            return None
        
        try:
            async with self.db_pool.acquire() as conn:
                # Look for nearby cached reverse geocoding results
                row = await conn.fetchrow("""
                    SELECT raw_response
                    FROM geocoding_cache
                    WHERE ST_DWithin(
                        location,
                        ST_SetSRID(ST_MakePoint($2, $1), 4326)::geography,
                        100  -- Within 100 meters
                    )
                    AND raw_response IS NOT NULL
                    AND expires_at > CURRENT_TIMESTAMP
                    ORDER BY ST_Distance(
                        location,
                        ST_SetSRID(ST_MakePoint($2, $1), 4326)::geography
                    )
                    LIMIT 1
                """, coordinates.latitude, coordinates.longitude)
                
                if row and row['raw_response']:
                    return json.loads(row['raw_response'])
        except Exception as e:
            logger.error(f"Error retrieving cached address: {e}")
        
        return None
    
    async def _cache_address(self, coordinates: Coordinates, address: Dict[str, str]):
        """Cache reverse geocoded address"""
        if not self.db_pool:
            return
        
        full_address = f"{address.get('street', '')}, {address.get('city', '')}, {address.get('province', '')}"
        cache_key = self._get_cache_key(full_address)
        
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO geocoding_cache 
                    (address_hash, full_address, latitude, longitude, location, 
                     raw_response, provider, expires_at)
                    VALUES ($1, $2, $3, $4, 
                            ST_SetSRID(ST_MakePoint($4, $3), 4326)::geography,
                            $5, 'reverse', CURRENT_TIMESTAMP + INTERVAL '90 days')
                    ON CONFLICT (address_hash) DO NOTHING
                """, cache_key, full_address, coordinates.latitude, coordinates.longitude,
                    json.dumps(address))
        except Exception as e:
            logger.error(f"Error caching address: {e}")
    
    async def _call_reverse_geocoding_api(self, coordinates: Coordinates) -> Optional[Dict[str, str]]:
        """
        Call external reverse geocoding API
        Placeholder for real service integration
        """
        # Return mock address for testing
        return {
            "street": "123 Main Street",
            "city": "Toronto",
            "province": "Ontario",
            "postal_code": "M5V 3A8",
            "country": "Canada"
        }


class LocationService:
    """
    Main location service orchestrator
    Combines distance calculation, geocoding, and spatial queries
    """
    
    def __init__(self, db_pool: Optional[asyncpg.Pool] = None):
        """Initialize location service with optional database pool"""
        self.db_pool = db_pool
        self.calculator = HaversineCalculator()
        self.geocoder = GeocodingService(db_pool)
    
    async def find_nearest_stores(
        self,
        customer_location: Coordinates,
        tenant_id: Optional[str] = None,
        limit: int = 5,
        max_distance_km: float = 50.0
    ) -> List[Dict[str, Any]]:
        """
        Find nearest stores to customer location
        
        Args:
            customer_location: Customer's coordinates
            tenant_id: Optional tenant filter
            limit: Maximum number of stores to return
            max_distance_km: Maximum search radius in kilometers
            
        Returns:
            List of stores with distance information
        """
        if not self.db_pool:
            return []
        
        try:
            async with self.db_pool.acquire() as conn:
                # Use the database function for efficient spatial query
                rows = await conn.fetch("""
                    SELECT * FROM find_nearest_stores($1, $2, $3, $4, $5)
                """, customer_location.latitude, customer_location.longitude,
                    tenant_id, limit, max_distance_km)
                
                stores = []
                for row in rows:
                    store = dict(row)
                    # Add bearing for navigation
                    store_coords = Coordinates(
                        latitude=float(json.loads(store['address']).get('latitude', 0)),
                        longitude=float(json.loads(store['address']).get('longitude', 0))
                    )
                    store['bearing'] = self.calculator.calculate_bearing(
                        customer_location, store_coords
                    )
                    stores.append(store)
                
                return stores
        except Exception as e:
            logger.error(f"Error finding nearest stores: {e}")
            return []
    
    async def check_delivery_availability(
        self,
        store_id: str,
        customer_location: Coordinates
    ) -> Dict[str, Any]:
        """
        Check if delivery is available to customer location
        
        Args:
            store_id: Store UUID
            customer_location: Customer's coordinates
            
        Returns:
            Delivery availability information
        """
        if not self.db_pool:
            return {"available": False, "error": "Database not available"}
        
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT * FROM check_delivery_availability($1, $2, $3)
                """, store_id, customer_location.latitude, customer_location.longitude)
                
                if row:
                    return dict(row)
                return {"available": False}
        except Exception as e:
            logger.error(f"Error checking delivery availability: {e}")
            return {"available": False, "error": str(e)}
    
    async def log_location_access(
        self,
        user_id: Optional[str],
        session_id: Optional[str],
        action: str,
        customer_location: Optional[Coordinates],
        store_id: Optional[str] = None,
        distance_km: Optional[float] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Log location access for audit and analytics
        
        Args:
            user_id: User UUID if authenticated
            session_id: Session identifier
            action: Action performed (search, select, delivery_check)
            customer_location: Customer's coordinates
            store_id: Selected store if applicable
            distance_km: Distance to store if applicable
            ip_address: Client IP address
            user_agent: Client user agent string
        """
        if not self.db_pool:
            return
        
        try:
            async with self.db_pool.acquire() as conn:
                location_point = None
                if customer_location:
                    location_point = f"POINT({customer_location.longitude} {customer_location.latitude})"
                
                await conn.execute("""
                    INSERT INTO location_access_log 
                    (user_id, session_id, action, customer_location, 
                     selected_store_id, distance_km, ip_address, user_agent)
                    VALUES ($1, $2, $3, 
                            CASE WHEN $4 IS NOT NULL 
                                 THEN ST_GeogFromText($4)
                                 ELSE NULL END,
                            $5, $6, $7, $8)
                """, user_id, session_id, action, location_point,
                    store_id, distance_km, ip_address, user_agent)
        except Exception as e:
            logger.error(f"Error logging location access: {e}")
    
    def calculate_distance(
        self,
        point1: Coordinates,
        point2: Coordinates,
        unit: DistanceUnit = DistanceUnit.KILOMETERS
    ) -> float:
        """
        Calculate distance between two points
        
        Args:
            point1: First coordinate point
            point2: Second coordinate point
            unit: Distance unit (default: kilometers)
            
        Returns:
            Distance in specified unit
        """
        return self.calculator.calculate_distance(point1, point2, unit)
    
    def get_bounding_box(
        self,
        center: Coordinates,
        radius_km: float
    ) -> LocationBounds:
        """
        Get bounding box for circular area
        
        Args:
            center: Center coordinates
            radius_km: Radius in kilometers
            
        Returns:
            Bounding box
        """
        return self.calculator.get_bounding_box(center, radius_km)