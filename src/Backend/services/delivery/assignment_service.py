"""
Assignment service for managing delivery assignments to staff
"""

import asyncpg
import logging
from typing import List, Optional
from uuid import UUID

from .base import (
    IAssignmentService, StaffMember, StaffStatus,
    Location, StaffNotAvailable
)

logger = logging.getLogger(__name__)


class AssignmentService(IAssignmentService):
    """Service for managing delivery assignments"""

    def __init__(self, db_pool: asyncpg.Pool):
        """Initialize with database connection pool"""
        self.db_pool = db_pool

    async def assign_to_staff(self, delivery_id: UUID, staff_id: UUID) -> bool:
        """Manually assign delivery to staff member"""
        try:
            async with self.db_pool.acquire() as conn:
                # Check staff availability
                available = await conn.fetchval("""
                    SELECT is_available
                    FROM staff_delivery_status
                    WHERE user_id = $1
                """, staff_id)

                if not available:
                    # Create staff delivery status if doesn't exist
                    await conn.execute("""
                        INSERT INTO staff_delivery_status (user_id, is_available)
                        VALUES ($1, true)
                        ON CONFLICT (user_id) DO UPDATE
                        SET is_available = true
                    """, staff_id)

                # Update delivery assignment
                result = await conn.execute("""
                    UPDATE deliveries
                    SET
                        assigned_to = $2,
                        status = 'assigned',
                        assigned_at = CURRENT_TIMESTAMP
                    WHERE id = $1
                """, delivery_id, staff_id)

                # Update staff delivery count
                await conn.execute("""
                    UPDATE staff_delivery_status
                    SET
                        current_deliveries = current_deliveries + 1,
                        current_status = 'busy'
                    WHERE user_id = $1
                """, staff_id)

                logger.info(f"Assigned delivery {delivery_id} to staff {staff_id}")
                return result is not None

        except Exception as e:
            logger.error(f"Error assigning delivery: {str(e)}")
            return False

    async def batch_assign(
        self,
        delivery_ids: List[UUID],
        staff_id: UUID
    ) -> List[UUID]:
        """Assign multiple deliveries to staff"""
        assigned = []
        for delivery_id in delivery_ids:
            if await self.assign_to_staff(delivery_id, staff_id):
                assigned.append(delivery_id)
        return assigned

    async def get_available_staff(self, store_id: UUID) -> List[StaffMember]:
        """Get list of available staff members"""
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT
                        u.id, u.first_name, u.last_name, u.email, u.phone,
                        sds.is_available, sds.current_status, sds.current_deliveries,
                        sds.max_deliveries, sds.current_latitude, sds.current_longitude,
                        sds.deliveries_today, sds.deliveries_completed
                    FROM users u
                    LEFT JOIN staff_delivery_status sds ON u.id = sds.user_id
                    WHERE u.store_id = $1
                    AND u.role IN ('staff', 'admin', 'driver', 'manager')
                    AND u.active = true
                    ORDER BY
                        CASE WHEN sds.is_available THEN 0 ELSE 1 END,
                        sds.current_deliveries ASC
                """, store_id)

                staff_members = []
                for row in rows:
                    location = None
                    if row['current_latitude'] and row['current_longitude']:
                        location = Location(
                            latitude=float(row['current_latitude']),
                            longitude=float(row['current_longitude'])
                        )

                    member = StaffMember(
                        id=row['id'],
                        name=f"{row['first_name']} {row['last_name']}",
                        phone=row['phone'] or '',
                        email=row['email'],
                        status=StaffStatus(row['current_status']) if row['current_status'] else StaffStatus.OFFLINE,
                        current_location=location,
                        current_deliveries=row['current_deliveries'] or 0,
                        max_deliveries=row['max_deliveries'] or 5,
                        is_available=row['is_available'] or False,
                        deliveries_today=row['deliveries_today'] or 0,
                        deliveries_completed=row['deliveries_completed'] or 0
                    )
                    staff_members.append(member)

                return staff_members

        except Exception as e:
            logger.error(f"Error getting available staff: {str(e)}")
            return []

    async def get_staff_member(self, staff_id: UUID) -> Optional[StaffMember]:
        """Get specific staff member details"""
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT
                        u.id, u.first_name, u.last_name, u.email, u.phone,
                        sds.is_available, sds.current_status, sds.current_deliveries,
                        sds.max_deliveries, sds.current_latitude, sds.current_longitude,
                        sds.deliveries_today, sds.deliveries_completed
                    FROM users u
                    LEFT JOIN staff_delivery_status sds ON u.id = sds.user_id
                    WHERE u.id = $1
                """, staff_id)

                if not row:
                    return None

                location = None
                if row['current_latitude'] and row['current_longitude']:
                    location = Location(
                        latitude=float(row['current_latitude']),
                        longitude=float(row['current_longitude'])
                    )

                return StaffMember(
                    id=row['id'],
                    name=f"{row['first_name']} {row['last_name']}",
                    phone=row['phone'] or '',
                    email=row['email'],
                    status=StaffStatus(row['current_status']) if row['current_status'] else StaffStatus.OFFLINE,
                    current_location=location,
                    current_deliveries=row['current_deliveries'] or 0,
                    max_deliveries=row['max_deliveries'] or 5,
                    is_available=row['is_available'] or False,
                    deliveries_today=row['deliveries_today'] or 0,
                    deliveries_completed=row['deliveries_completed'] or 0
                )

        except Exception as e:
            logger.error(f"Error getting staff member: {str(e)}")
            return None

    async def update_staff_status(
        self,
        staff_id: UUID,
        status: StaffStatus,
        is_available: Optional[bool] = None
    ) -> bool:
        """Update staff availability status"""
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    INSERT INTO staff_delivery_status (user_id, current_status, is_available)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (user_id) DO UPDATE
                    SET
                        current_status = $2,
                        is_available = COALESCE($3, staff_delivery_status.is_available),
                        updated_at = CURRENT_TIMESTAMP
                """

                await conn.execute(
                    query,
                    staff_id,
                    status.value,
                    is_available if is_available is not None else (status == StaffStatus.AVAILABLE)
                )

                logger.info(f"Updated staff {staff_id} status to {status.value}")
                return True

        except Exception as e:
            logger.error(f"Error updating staff status: {str(e)}")
            return False

    async def increment_staff_deliveries(self, staff_id: UUID) -> bool:
        """Increment staff delivery count"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE staff_delivery_status
                    SET
                        current_deliveries = current_deliveries + 1,
                        deliveries_today = deliveries_today + 1
                    WHERE user_id = $1
                """, staff_id)
                return True

        except Exception as e:
            logger.error(f"Error incrementing staff deliveries: {str(e)}")
            return False

    async def decrement_staff_deliveries(self, staff_id: UUID) -> bool:
        """Decrement staff delivery count"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE staff_delivery_status
                    SET
                        current_deliveries = GREATEST(0, current_deliveries - 1),
                        current_status = CASE
                            WHEN current_deliveries <= 1 THEN 'available'
                            ELSE current_status
                        END
                    WHERE user_id = $1
                """, staff_id)
                return True

        except Exception as e:
            logger.error(f"Error decrementing staff deliveries: {str(e)}")
            return False

    async def complete_delivery_for_staff(self, staff_id: UUID) -> bool:
        """Mark a delivery as completed for staff metrics"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE staff_delivery_status
                    SET
                        current_deliveries = GREATEST(0, current_deliveries - 1),
                        deliveries_completed = deliveries_completed + 1,
                        current_status = CASE
                            WHEN current_deliveries <= 1 THEN 'available'
                            ELSE current_status
                        END
                    WHERE user_id = $1
                """, staff_id)
                return True

        except Exception as e:
            logger.error(f"Error completing delivery for staff: {str(e)}")
            return False