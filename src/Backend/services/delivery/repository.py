"""
Delivery repository implementation
Handles all database operations for deliveries
"""

import asyncpg
import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import UUID

from .base import (
    IDeliveryRepository, Delivery, DeliveryStatus, Address, ProofOfDelivery,
    DeliveryMetrics, DeliveryNotFound, Location
)

logger = logging.getLogger(__name__)


class DeliveryRepository(IDeliveryRepository):
    """PostgreSQL implementation of delivery repository"""

    def __init__(self, db_pool: asyncpg.Pool):
        """Initialize with database connection pool"""
        self.db_pool = db_pool

    async def create(self, delivery: Delivery) -> Delivery:
        """Create a new delivery"""
        try:
            async with self.db_pool.acquire() as conn:
                # Log event
                await self._log_event(
                    conn, delivery.id, "delivery_created",
                    {"order_id": str(delivery.order_id)}
                )

                # Insert delivery record
                row = await conn.fetchrow("""
                    INSERT INTO deliveries (
                        id, order_id, store_id, status, customer_id,
                        customer_name, customer_phone, customer_email,
                        delivery_address, delivery_latitude, delivery_longitude,
                        delivery_notes, assigned_to, batch_id, batch_sequence,
                        delivery_fee, tip_amount, created_by
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
                        $13, $14, $15, $16, $17, $18
                    ) RETURNING *
                """,
                    delivery.id,
                    delivery.order_id,
                    delivery.store_id,
                    delivery.status.value,
                    delivery.customer_id,
                    delivery.customer_name,
                    delivery.customer_phone,
                    delivery.customer_email,
                    json.dumps(delivery.delivery_address.to_dict()),
                    delivery.delivery_address.location.latitude if delivery.delivery_address.location else None,
                    delivery.delivery_address.location.longitude if delivery.delivery_address.location else None,
                    delivery.delivery_address.notes,
                    delivery.assigned_to,
                    delivery.batch_id,
                    delivery.batch_sequence,
                    delivery.metrics.delivery_fee if delivery.metrics else Decimal("0"),
                    delivery.metrics.tip_amount if delivery.metrics else Decimal("0"),
                    delivery.assigned_to  # created_by
                )

                logger.info(f"Created delivery {delivery.id} for order {delivery.order_id}")
                return self._row_to_delivery(row)

        except Exception as e:
            logger.error(f"Error creating delivery: {str(e)}")
            raise

    async def get(self, delivery_id: UUID) -> Optional[Delivery]:
        """Get delivery by ID"""
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT * FROM deliveries WHERE id = $1
                """, delivery_id)

                if not row:
                    return None

                return self._row_to_delivery(row)

        except Exception as e:
            logger.error(f"Error fetching delivery {delivery_id}: {str(e)}")
            raise

    async def update(self, delivery: Delivery) -> Delivery:
        """Update delivery"""
        try:
            async with self.db_pool.acquire() as conn:
                # Get current status for comparison
                current = await conn.fetchval(
                    "SELECT status FROM deliveries WHERE id = $1",
                    delivery.id
                )

                if not current:
                    raise DeliveryNotFound(f"Delivery {delivery.id} not found")

                # Update delivery record
                row = await conn.fetchrow("""
                    UPDATE deliveries SET
                        status = $2,
                        assigned_to = $3,
                        delivery_notes = $4,
                        estimated_delivery_time = $5,
                        delivery_fee = $6,
                        tip_amount = $7,
                        signature_data = $8,
                        photo_proof_urls = $9,
                        id_verified = $10,
                        id_verification_type = $11,
                        id_verification_data = $12,
                        age_verified = $13,
                        rating = $14,
                        feedback = $15,
                        updated_at = CURRENT_TIMESTAMP,
                        updated_by = $16,

                        -- Update status timestamps
                        assigned_at = CASE WHEN $2 = 'assigned' AND assigned_at IS NULL THEN CURRENT_TIMESTAMP ELSE assigned_at END,
                        accepted_at = CASE WHEN $2 = 'accepted' AND accepted_at IS NULL THEN CURRENT_TIMESTAMP ELSE accepted_at END,
                        picked_up_at = CASE WHEN $2 = 'picked_up' AND picked_up_at IS NULL THEN CURRENT_TIMESTAMP ELSE picked_up_at END,
                        departed_at = CASE WHEN $2 = 'en_route' AND departed_at IS NULL THEN CURRENT_TIMESTAMP ELSE departed_at END,
                        arrived_at = CASE WHEN $2 = 'arrived' AND arrived_at IS NULL THEN CURRENT_TIMESTAMP ELSE arrived_at END,
                        completed_at = CASE WHEN $2 = 'completed' AND completed_at IS NULL THEN CURRENT_TIMESTAMP ELSE completed_at END,
                        cancelled_at = CASE WHEN $2 = 'cancelled' AND cancelled_at IS NULL THEN CURRENT_TIMESTAMP ELSE cancelled_at END
                    WHERE id = $1
                    RETURNING *
                """,
                    delivery.id,
                    delivery.status.value,
                    delivery.assigned_to,
                    delivery.delivery_address.notes,
                    delivery.metrics.estimated_time if delivery.metrics else None,
                    delivery.metrics.delivery_fee if delivery.metrics else Decimal("0"),
                    delivery.metrics.tip_amount if delivery.metrics else Decimal("0"),
                    delivery.proof.signature_data if delivery.proof else None,
                    delivery.proof.photo_urls if delivery.proof else None,
                    delivery.proof.id_verified if delivery.proof else False,
                    delivery.proof.id_verification_type if delivery.proof else None,
                    json.dumps(delivery.proof.id_verification_data) if delivery.proof and delivery.proof.id_verification_data else None,
                    delivery.proof.age_verified if delivery.proof else False,
                    delivery.metrics.rating if delivery.metrics else None,
                    delivery.metrics.feedback if delivery.metrics else None,
                    delivery.assigned_to  # updated_by
                )

                # Log status change
                if current != delivery.status.value:
                    await self._log_event(
                        conn, delivery.id, "status_changed",
                        {"from": current, "to": delivery.status.value},
                        delivery.assigned_to
                    )

                logger.info(f"Updated delivery {delivery.id} status to {delivery.status.value}")
                return self._row_to_delivery(row)

        except Exception as e:
            logger.error(f"Error updating delivery {delivery.id}: {str(e)}")
            raise

    async def list_active(self, store_id: UUID) -> List[Delivery]:
        """List active deliveries for a store"""
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM deliveries
                    WHERE store_id = $1
                    AND status NOT IN ('completed', 'failed', 'cancelled')
                    ORDER BY created_at DESC
                """, store_id)

                return [self._row_to_delivery(row) for row in rows]

        except Exception as e:
            logger.error(f"Error listing active deliveries: {str(e)}")
            raise

    async def list_by_status(self, status: DeliveryStatus, store_id: UUID) -> List[Delivery]:
        """List deliveries by status"""
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM deliveries
                    WHERE store_id = $1 AND status = $2
                    ORDER BY created_at DESC
                """, store_id, status.value)

                return [self._row_to_delivery(row) for row in rows]

        except Exception as e:
            logger.error(f"Error listing deliveries by status: {str(e)}")
            raise

    async def list_by_staff(self, staff_id: UUID, active_only: bool = True) -> List[Delivery]:
        """List deliveries assigned to staff member"""
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    SELECT * FROM deliveries
                    WHERE assigned_to = $1
                """
                if active_only:
                    query += " AND status NOT IN ('completed', 'failed', 'cancelled')"
                query += " ORDER BY created_at DESC"

                rows = await conn.fetch(query, staff_id)
                return [self._row_to_delivery(row) for row in rows]

        except Exception as e:
            logger.error(f"Error listing deliveries for staff {staff_id}: {str(e)}")
            raise

    async def update_status(
        self,
        delivery_id: UUID,
        status: DeliveryStatus,
        user_id: Optional[UUID] = None
    ) -> bool:
        """Update delivery status"""
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute("""
                    UPDATE deliveries
                    SET status = $2, updated_at = CURRENT_TIMESTAMP
                    WHERE id = $1
                """, delivery_id, status.value)

                if result:
                    await self._log_event(
                        conn, delivery_id, "status_changed",
                        {"status": status.value}, user_id
                    )
                    return True
                return False

        except Exception as e:
            logger.error(f"Error updating delivery status: {str(e)}")
            raise

    async def add_proof_of_delivery(
        self,
        delivery_id: UUID,
        proof: ProofOfDelivery
    ) -> bool:
        """Add proof of delivery"""
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute("""
                    UPDATE deliveries
                    SET
                        signature_data = $2,
                        signature_captured_at = $3,
                        photo_proof_urls = $4,
                        id_verified = $5,
                        id_verification_type = $6,
                        id_verification_data = $7,
                        age_verified = $8,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $1
                """,
                    delivery_id,
                    proof.signature_data,
                    proof.captured_at or datetime.utcnow(),
                    proof.photo_urls,
                    proof.id_verified,
                    proof.id_verification_type,
                    json.dumps(proof.id_verification_data) if proof.id_verification_data else None,
                    proof.age_verified
                )

                if result:
                    await self._log_event(
                        conn, delivery_id, "proof_added",
                        {"type": "signature" if proof.signature_data else "photo"}
                    )
                    return True
                return False

        except Exception as e:
            logger.error(f"Error adding proof of delivery: {str(e)}")
            raise

    async def get_batch_deliveries(self, batch_id: UUID) -> List[Delivery]:
        """Get all deliveries in a batch"""
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM deliveries
                    WHERE batch_id = $1
                    ORDER BY batch_sequence
                """, batch_id)

                return [self._row_to_delivery(row) for row in rows]

        except Exception as e:
            logger.error(f"Error fetching batch deliveries: {str(e)}")
            raise

    async def _log_event(
        self,
        conn: asyncpg.Connection,
        delivery_id: UUID,
        event_type: str,
        event_data: Dict = None,
        user_id: Optional[UUID] = None
    ):
        """Log delivery event"""
        try:
            await conn.execute("""
                INSERT INTO delivery_events (
                    delivery_id, event_type, event_data, performed_by
                ) VALUES ($1, $2, $3, $4)
            """,
                delivery_id,
                event_type,
                json.dumps(event_data or {}),
                user_id
            )
        except Exception as e:
            logger.warning(f"Failed to log delivery event: {str(e)}")

    def _row_to_delivery(self, row: asyncpg.Record) -> Delivery:
        """Convert database row to Delivery object"""
        # Parse address
        address = Address.from_dict(row['delivery_address'])
        if row['delivery_latitude'] and row['delivery_longitude']:
            address.location = Location(
                latitude=float(row['delivery_latitude']),
                longitude=float(row['delivery_longitude'])
            )

        # Parse proof of delivery
        proof = None
        if row.get('signature_data') or row.get('photo_proof_urls'):
            proof = ProofOfDelivery(
                signature_data=row.get('signature_data'),
                photo_urls=row.get('photo_proof_urls', []),
                id_verified=row.get('id_verified', False),
                id_verification_type=row.get('id_verification_type'),
                id_verification_data=json.loads(row['id_verification_data']) if row.get('id_verification_data') else None,
                age_verified=row.get('age_verified', False),
                captured_at=row.get('signature_captured_at')
            )

        # Parse metrics
        metrics = DeliveryMetrics(
            estimated_time=row.get('estimated_delivery_time'),
            actual_time=row.get('actual_delivery_time'),
            distance_km=float(row['distance_km']) if row.get('distance_km') else None,
            delivery_fee=row.get('delivery_fee', Decimal("0")),
            tip_amount=row.get('tip_amount', Decimal("0")),
            rating=row.get('rating'),
            feedback=row.get('feedback')
        )

        return Delivery(
            id=row['id'],
            order_id=row['order_id'],
            store_id=row['store_id'],
            status=DeliveryStatus(row['status']),
            customer_id=row['customer_id'],
            customer_name=row['customer_name'],
            customer_phone=row['customer_phone'],
            customer_email=row.get('customer_email'),
            delivery_address=address,
            assigned_to=row.get('assigned_to'),
            batch_id=row.get('batch_id'),
            batch_sequence=row.get('batch_sequence'),
            proof=proof,
            metrics=metrics,
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )