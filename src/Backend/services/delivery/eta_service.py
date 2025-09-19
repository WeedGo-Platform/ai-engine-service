"""
ETA calculation service for deliveries
Uses various methods for time estimation
"""

import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict, Any
from uuid import UUID

from .base import IETAService, Location

logger = logging.getLogger(__name__)


class ETAService(IETAService):
    """Service for calculating delivery ETAs"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize ETA service with optional API key for external services"""
        self.api_key = api_key
        # Average speeds in km/h for different modes
        self.default_speeds = {
            'driving': 30,  # City driving with traffic
            'walking': 5,
            'cycling': 15
        }

    async def calculate_eta(
        self,
        origin: Location,
        destination: Location,
        mode: str = "driving"
    ) -> Tuple[datetime, float]:
        """Calculate ETA and distance between two locations"""
        try:
            # Calculate distance using Haversine formula
            distance_km = origin.distance_to(destination)

            # Try to get ETA from external service if API key available
            if self.api_key:
                external_eta = await self._get_external_eta(origin, destination, mode)
                if external_eta:
                    return external_eta

            # Fallback to simple calculation
            speed_kmh = self.default_speeds.get(mode, 30)

            # Add buffer for stops, traffic lights, etc.
            buffer_factor = 1.3 if mode == 'driving' else 1.1

            # Calculate travel time in hours
            travel_time_hours = (distance_km / speed_kmh) * buffer_factor

            # Convert to minutes and create ETA
            travel_time_minutes = int(travel_time_hours * 60)
            eta = datetime.utcnow() + timedelta(minutes=travel_time_minutes)

            logger.debug(f"Calculated ETA: {travel_time_minutes} minutes for {distance_km:.2f} km")
            return eta, distance_km

        except Exception as e:
            logger.error(f"Error calculating ETA: {str(e)}")
            # Return conservative estimate on error
            return datetime.utcnow() + timedelta(minutes=45), 0

    async def update_eta(self, delivery_id: UUID) -> datetime:
        """Update delivery ETA based on current location"""
        # This would be implemented with actual delivery data
        # For now, return a placeholder
        return datetime.utcnow() + timedelta(minutes=30)

    async def _get_external_eta(
        self,
        origin: Location,
        destination: Location,
        mode: str
    ) -> Optional[Tuple[datetime, float]]:
        """Get ETA from external service (Google Maps, Mapbox, etc.)"""
        try:
            # Example using OpenRouteService (free tier available)
            if not self.api_key:
                return None

            url = "https://api.openrouteservice.org/v2/directions/driving-car"

            headers = {
                'Authorization': self.api_key,
                'Content-Type': 'application/json'
            }

            body = {
                "coordinates": [
                    [origin.longitude, origin.latitude],
                    [destination.longitude, destination.latitude]
                ]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=body) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'routes' in data and data['routes']:
                            route = data['routes'][0]
                            duration_seconds = route['summary']['duration']
                            distance_meters = route['summary']['distance']

                            eta = datetime.utcnow() + timedelta(seconds=duration_seconds)
                            distance_km = distance_meters / 1000.0

                            return eta, distance_km

        except Exception as e:
            logger.warning(f"External ETA service failed: {str(e)}")
            return None

    async def calculate_batch_route(
        self,
        origin: Location,
        destinations: list[Location],
        mode: str = "driving"
    ) -> Dict[str, Any]:
        """Calculate optimized route for multiple deliveries"""
        try:
            total_distance = 0.0
            total_time_minutes = 0
            route_order = []
            etas = []

            current_location = origin
            remaining_destinations = destinations.copy()

            # Simple nearest neighbor algorithm
            while remaining_destinations:
                nearest = None
                nearest_distance = float('inf')
                nearest_index = -1

                # Find nearest destination
                for i, dest in enumerate(remaining_destinations):
                    distance = current_location.distance_to(dest)
                    if distance < nearest_distance:
                        nearest_distance = distance
                        nearest = dest
                        nearest_index = i

                if nearest:
                    # Calculate ETA for this segment
                    eta, distance = await self.calculate_eta(current_location, nearest, mode)

                    total_distance += distance
                    travel_minutes = int((eta - datetime.utcnow()).total_seconds() / 60)
                    total_time_minutes += travel_minutes

                    route_order.append(nearest_index)
                    etas.append(eta)

                    # Move to next location
                    current_location = nearest
                    remaining_destinations.pop(nearest_index)

            return {
                'route_order': route_order,
                'total_distance_km': round(total_distance, 2),
                'total_time_minutes': total_time_minutes,
                'etas': etas,
                'optimized': True
            }

        except Exception as e:
            logger.error(f"Error calculating batch route: {str(e)}")
            return {
                'route_order': list(range(len(destinations))),
                'total_distance_km': 0,
                'total_time_minutes': len(destinations) * 30,
                'etas': [datetime.utcnow() + timedelta(minutes=30*i) for i in range(1, len(destinations)+1)],
                'optimized': False
            }

    def estimate_preparation_time(self, item_count: int) -> int:
        """Estimate preparation time based on number of items"""
        # Base time + per item time
        base_minutes = 5
        per_item_minutes = 1
        max_minutes = 30

        estimated = base_minutes + (item_count * per_item_minutes)
        return min(estimated, max_minutes)

    def adjust_eta_for_conditions(
        self,
        base_eta: datetime,
        weather: Optional[str] = None,
        traffic_level: Optional[str] = None
    ) -> datetime:
        """Adjust ETA based on external conditions"""
        adjustment_minutes = 0

        # Weather adjustments
        weather_adjustments = {
            'rain': 10,
            'heavy_rain': 20,
            'snow': 25,
            'storm': 30
        }
        if weather:
            adjustment_minutes += weather_adjustments.get(weather.lower(), 0)

        # Traffic adjustments
        traffic_adjustments = {
            'light': 0,
            'moderate': 5,
            'heavy': 15,
            'severe': 25
        }
        if traffic_level:
            adjustment_minutes += traffic_adjustments.get(traffic_level.lower(), 0)

        return base_eta + timedelta(minutes=adjustment_minutes)