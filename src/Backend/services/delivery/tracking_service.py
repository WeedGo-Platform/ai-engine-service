"""
Real-time tracking service for deliveries
Handles GPS updates, geofencing, and location history
"""

import asyncpg
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from uuid import UUID

from .base import (
    ITrackingService, IGeofenceService, Location, Delivery,
    DeliveryStatus
)

logger = logging.getLogger(__name__)


class TrackingService(ITrackingService, IGeofenceService):
    """Combined tracking and geofencing service"""

    def __init__(self, db_pool: asyncpg.Pool):
        """Initialize with database connection pool"""
        self.db_pool = db_pool
        self._websocket_connections: Dict[UUID, Set] = {}

    async def update_location(self, delivery_id: UUID, location: Location) -> bool:
        """Update delivery location"""
        try:
            async with self.db_pool.acquire() as conn:
                # Insert tracking point
                await conn.execute("""
                    INSERT INTO delivery_tracking (
                        delivery_id, latitude, longitude,
                        accuracy_meters, altitude_meters,
                        speed_kmh, heading, provider,
                        recorded_at, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                    delivery_id,
                    location.latitude,
                    location.longitude,
                    location.accuracy_meters,
                    location.altitude_meters,
                    getattr(location, 'speed_kmh', None),
                    getattr(location, 'heading', None),
                    getattr(location, 'provider', 'gps'),
                    location.timestamp,
                    json.dumps(getattr(location, 'metadata', {}))
                )

                # Update staff location
                await self._update_staff_location(conn, delivery_id, location)

                # Check geofences
                await self._check_geofences(conn, delivery_id, location)

                logger.debug(f"Updated location for delivery {delivery_id}")
                return True

        except Exception as e:
            logger.error(f"Error updating location: {str(e)}")
            return False

    async def get_current_location(self, delivery_id: UUID) -> Optional[Location]:
        """Get current location of delivery"""
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT latitude, longitude, accuracy_meters,
                           altitude_meters, recorded_at
                    FROM delivery_tracking
                    WHERE delivery_id = $1
                    ORDER BY recorded_at DESC
                    LIMIT 1
                """, delivery_id)

                if row:
                    return Location(
                        latitude=float(row['latitude']),
                        longitude=float(row['longitude']),
                        accuracy_meters=row['accuracy_meters'],
                        altitude_meters=row['altitude_meters'],
                        timestamp=row['recorded_at']
                    )
                return None

        except Exception as e:
            logger.error(f"Error getting current location: {str(e)}")
            return None

    async def get_location_history(
        self,
        delivery_id: UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Location]:
        """Get location history for delivery"""
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    SELECT latitude, longitude, accuracy_meters,
                           altitude_meters, speed_kmh, heading, recorded_at
                    FROM delivery_tracking
                    WHERE delivery_id = $1
                """
                params = [delivery_id]

                if start_time:
                    query += f" AND recorded_at >= ${len(params) + 1}"
                    params.append(start_time)

                if end_time:
                    query += f" AND recorded_at <= ${len(params) + 1}"
                    params.append(end_time)

                query += " ORDER BY recorded_at DESC"

                rows = await conn.fetch(query, *params)

                return [
                    Location(
                        latitude=float(row['latitude']),
                        longitude=float(row['longitude']),
                        accuracy_meters=row['accuracy_meters'],
                        altitude_meters=row['altitude_meters'],
                        timestamp=row['recorded_at']
                    )
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Error getting location history: {str(e)}")
            return []

    async def check_arrival(self, location: Location, delivery: Delivery) -> bool:
        """Check if driver has arrived at delivery location"""
        try:
            if not delivery.delivery_address.location:
                return False

            distance = location.distance_to(delivery.delivery_address.location)
            # Consider arrived if within 100 meters
            arrived = distance <= 0.1  # 0.1 km = 100 meters

            if arrived:
                async with self.db_pool.acquire() as conn:
                    # Update delivery status to arrived
                    await conn.execute("""
                        UPDATE deliveries
                        SET status = 'arrived', arrived_at = CURRENT_TIMESTAMP
                        WHERE id = $1 AND status = 'en_route'
                    """, delivery.id)

                    # Log event
                    await conn.execute("""
                        INSERT INTO delivery_events (
                            delivery_id, event_type, event_data
                        ) VALUES ($1, 'arrived', $2)
                    """,
                        delivery.id,
                        json.dumps({'location': location.to_dict()})
                    )

                logger.info(f"Delivery {delivery.id} has arrived")
            return arrived

        except Exception as e:
            logger.error(f"Error checking arrival: {str(e)}")
            return False

    async def create_geofence(
        self,
        delivery_id: UUID,
        center: Location,
        radius_meters: int = 100
    ) -> UUID:
        """Create geofence for delivery"""
        try:
            async with self.db_pool.acquire() as conn:
                fence_id = await conn.fetchval("""
                    INSERT INTO delivery_geofences (
                        delivery_id, center_latitude, center_longitude,
                        radius_meters, fence_type
                    ) VALUES ($1, $2, $3, $4, 'arrival')
                    RETURNING id
                """,
                    delivery_id,
                    center.latitude,
                    center.longitude,
                    radius_meters
                )

                logger.info(f"Created geofence {fence_id} for delivery {delivery_id}")
                return fence_id

        except Exception as e:
            logger.error(f"Error creating geofence: {str(e)}")
            raise

    async def check_geofence(self, location: Location, geofence_id: UUID) -> bool:
        """Check if location is within geofence"""
        try:
            async with self.db_pool.acquire() as conn:
                fence = await conn.fetchrow("""
                    SELECT center_latitude, center_longitude, radius_meters
                    FROM delivery_geofences
                    WHERE id = $1
                """, geofence_id)

                if not fence:
                    return False

                center = Location(
                    latitude=float(fence['center_latitude']),
                    longitude=float(fence['center_longitude'])
                )

                distance = location.distance_to(center)
                # Convert radius to km for comparison
                within_fence = distance <= (fence['radius_meters'] / 1000.0)

                if within_fence:
                    # Update geofence entry time
                    await conn.execute("""
                        UPDATE delivery_geofences
                        SET entered_at = CURRENT_TIMESTAMP
                        WHERE id = $1 AND entered_at IS NULL
                    """, geofence_id)

                return within_fence

        except Exception as e:
            logger.error(f"Error checking geofence: {str(e)}")
            return False

    async def _update_staff_location(
        self,
        conn: asyncpg.Connection,
        delivery_id: UUID,
        location: Location
    ):
        """Update staff member's current location"""
        try:
            # Get staff ID from delivery
            staff_id = await conn.fetchval("""
                SELECT assigned_to FROM deliveries WHERE id = $1
            """, delivery_id)

            if staff_id:
                await conn.execute("""
                    UPDATE staff_delivery_status
                    SET
                        current_latitude = $2,
                        current_longitude = $3,
                        last_location_update = CURRENT_TIMESTAMP
                    WHERE user_id = $1
                """,
                    staff_id,
                    location.latitude,
                    location.longitude
                )

        except Exception as e:
            logger.warning(f"Failed to update staff location: {str(e)}")

    async def _check_geofences(
        self,
        conn: asyncpg.Connection,
        delivery_id: UUID,
        location: Location
    ):
        """Check all geofences for a delivery"""
        try:
            fences = await conn.fetch("""
                SELECT id, center_latitude, center_longitude,
                       radius_meters, notify_on_enter, auto_complete_on_enter
                FROM delivery_geofences
                WHERE delivery_id = $1 AND entered_at IS NULL
            """, delivery_id)

            for fence in fences:
                center = Location(
                    latitude=float(fence['center_latitude']),
                    longitude=float(fence['center_longitude'])
                )

                distance = location.distance_to(center)
                if distance <= (fence['radius_meters'] / 1000.0):
                    # Inside geofence
                    await conn.execute("""
                        UPDATE delivery_geofences
                        SET entered_at = CURRENT_TIMESTAMP
                        WHERE id = $1
                    """, fence['id'])

                    # Log event
                    await conn.execute("""
                        INSERT INTO delivery_events (
                            delivery_id, event_type, event_data
                        ) VALUES ($1, 'geofence_entered', $2)
                    """,
                        delivery_id,
                        json.dumps({'geofence_id': str(fence['id'])})
                    )

                    # Auto-complete if configured
                    if fence['auto_complete_on_enter']:
                        await conn.execute("""
                            UPDATE deliveries
                            SET status = 'arrived', arrived_at = CURRENT_TIMESTAMP
                            WHERE id = $1
                        """, delivery_id)

        except Exception as e:
            logger.warning(f"Failed to check geofences: {str(e)}")

    async def get_tracking_stats(self, delivery_id: UUID) -> Dict:
        """Get tracking statistics for a delivery"""
        try:
            async with self.db_pool.acquire() as conn:
                stats = await conn.fetchrow("""
                    SELECT
                        COUNT(*) as total_points,
                        MIN(recorded_at) as first_location,
                        MAX(recorded_at) as last_location,
                        AVG(speed_kmh) as avg_speed,
                        MAX(speed_kmh) as max_speed
                    FROM delivery_tracking
                    WHERE delivery_id = $1
                """, delivery_id)

                # Calculate total distance traveled
                locations = await self.get_location_history(delivery_id)
                total_distance = 0.0
                if len(locations) > 1:
                    for i in range(1, len(locations)):
                        total_distance += locations[i].distance_to(locations[i-1])

                return {
                    'total_points': stats['total_points'],
                    'first_location': stats['first_location'].isoformat() if stats['first_location'] else None,
                    'last_location': stats['last_location'].isoformat() if stats['last_location'] else None,
                    'avg_speed_kmh': float(stats['avg_speed']) if stats['avg_speed'] else 0,
                    'max_speed_kmh': float(stats['max_speed']) if stats['max_speed'] else 0,
                    'total_distance_km': round(total_distance, 2)
                }

        except Exception as e:
            logger.error(f"Error getting tracking stats: {str(e)}")
            return {}

    async def cleanup_old_tracking_data(self, days_to_keep: int = 30):
        """Clean up old tracking data"""
        try:
            async with self.db_pool.acquire() as conn:
                cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

                deleted = await conn.execute("""
                    DELETE FROM delivery_tracking
                    WHERE recorded_at < $1
                """, cutoff_date)

                logger.info(f"Deleted {deleted} old tracking records")
                return deleted

        except Exception as e:
            logger.error(f"Error cleaning up tracking data: {str(e)}")
            return 0