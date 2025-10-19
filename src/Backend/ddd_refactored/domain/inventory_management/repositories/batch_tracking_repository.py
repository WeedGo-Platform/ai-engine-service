"""
BatchTracking Repository - Interface and Implementation
Following Repository Pattern from DDD Architecture
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
import asyncpg
import logging

from ..entities.batch_tracking import BatchTracking

logger = logging.getLogger(__name__)


class IBatchTrackingRepository(ABC):
    """Repository interface for batch tracking operations"""

    @abstractmethod
    async def save(self, batch: BatchTracking) -> UUID:
        """
        Save (insert or update) a batch

        Args:
            batch: BatchTracking entity

        Returns:
            UUID of the saved batch
        """
        pass

    @abstractmethod
    async def find_by_id(self, batch_id: UUID) -> Optional[BatchTracking]:
        """Get batch by ID"""
        pass

    @abstractmethod
    async def find_by_lot(self, batch_lot: str, store_id: UUID) -> Optional[BatchTracking]:
        """Get batch by lot number and store"""
        pass

    @abstractmethod
    async def find_active_for_sku(
        self,
        store_id: UUID,
        sku: str,
        order_by: str = "created_at"  # FIFO
    ) -> List[BatchTracking]:
        """
        Get active batches for SKU ordered for consumption (FIFO)

        Args:
            store_id: Store UUID
            sku: Product SKU
            order_by: Field to order by (default: created_at for FIFO)

        Returns:
            List of BatchTracking entities ordered oldest first
        """
        pass

    @abstractmethod
    async def find_all(
        self,
        store_id: Optional[UUID] = None,
        sku: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[BatchTracking]:
        """Find batches with filtering"""
        pass

    @abstractmethod
    async def delete(self, batch_id: UUID) -> bool:
        """Soft delete batch (set is_active = false)"""
        pass


class AsyncPGBatchTrackingRepository(IBatchTrackingRepository):
    """AsyncPG implementation of batch tracking repository"""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool

    async def save(self, batch: BatchTracking) -> UUID:
        """
        Save batch to database

        Handles both INSERT (new batch) and UPDATE (existing batch)
        Uses batch_lot uniqueness constraint for UPSERT behavior
        """
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Check if batch exists by batch_lot (unique constraint)
                exists = await conn.fetchval(
                    "SELECT id FROM batch_tracking WHERE batch_lot = $1 AND store_id = $2",
                    batch.batch_lot,
                    batch.store_id
                )

                if exists:
                    # Update existing batch
                    await self._update_batch(conn, batch)
                    return exists
                else:
                    # Insert new batch
                    return await self._insert_batch(conn, batch)

    async def _insert_batch(self, conn: asyncpg.Connection, batch: BatchTracking) -> UUID:
        """Insert new batch"""
        query = """
            INSERT INTO batch_tracking (
                id, store_id, sku, batch_lot, quantity_received, quantity_remaining,
                unit_cost, received_date, purchase_order_id, location_id,
                case_gtin, packaged_on_date, gtin_barcode, each_gtin,
                is_active, is_quarantined, quarantine_reason,
                quality_check_status, quality_check_date, quality_check_by, quality_notes,
                created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17,
                $18, $19, $20, $21, $22, $23
            )
            RETURNING id
        """

        batch_id = await conn.fetchval(
            query,
            batch.id,
            batch.store_id,
            batch.sku,
            batch.batch_lot,
            batch.quantity_received,
            batch.quantity_remaining,
            batch.unit_cost,
            batch.received_date,
            batch.purchase_order_id,
            batch.location_id,
            batch.gtin,  # Maps to case_gtin in DB
            batch.packaged_date,
            batch.gtin,  # Maps to gtin_barcode in DB
            batch.gtin,  # Maps to each_gtin in DB (simplified for now)
            batch.is_active,
            batch.is_quarantined,
            batch.quarantine_reason,
            batch.quality_check_status,
            batch.quality_check_date,
            batch.quality_check_by,
            batch.quality_notes,
            batch.created_at,
            batch.updated_at
        )

        logger.info(f"Inserted new batch {batch.batch_lot} (ID: {batch_id})")
        return batch_id

    async def _update_batch(self, conn: asyncpg.Connection, batch: BatchTracking) -> None:
        """Update existing batch"""
        query = """
            UPDATE batch_tracking
            SET quantity_received = $2,
                quantity_remaining = $3,
                unit_cost = $4,
                location_id = $5,
                is_active = $6,
                is_quarantined = $7,
                quarantine_reason = $8,
                quality_check_status = $9,
                quality_check_date = $10,
                quality_check_by = $11,
                quality_notes = $12,
                updated_at = $13
            WHERE batch_lot = $14 AND store_id = $15
        """

        await conn.execute(
            query,
            batch.quantity_received,
            batch.quantity_remaining,
            batch.unit_cost,
            batch.location_id,
            batch.is_active,
            batch.is_quarantined,
            batch.quarantine_reason,
            batch.quality_check_status,
            batch.quality_check_date,
            batch.quality_check_by,
            batch.quality_notes,
            datetime.utcnow(),
            batch.batch_lot,
            batch.store_id
        )

        logger.info(f"Updated batch {batch.batch_lot}")

    async def find_by_id(self, batch_id: UUID) -> Optional[BatchTracking]:
        """Get batch by ID"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM batch_tracking WHERE id = $1",
                batch_id
            )

            if not row:
                return None

            return self._map_to_entity(row)

    async def find_by_lot(self, batch_lot: str, store_id: UUID) -> Optional[BatchTracking]:
        """Get batch by lot number and store"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM batch_tracking WHERE batch_lot = $1 AND store_id = $2",
                batch_lot,
                store_id
            )

            if not row:
                return None

            return self._map_to_entity(row)

    async def find_active_for_sku(
        self,
        store_id: UUID,
        sku: str,
        order_by: str = "created_at"
    ) -> List[BatchTracking]:
        """
        Get active batches for SKU ordered for FIFO consumption

        Orders by created_at ASC (oldest first) for FIFO inventory management
        """
        async with self.db_pool.acquire() as conn:
            # Validate order_by to prevent SQL injection
            allowed_orders = ["created_at", "received_date", "packaged_on_date"]
            if order_by not in allowed_orders:
                order_by = "created_at"

            query = f"""
                SELECT * FROM batch_tracking
                WHERE store_id = $1 AND sku = $2
                      AND is_active = true AND quantity_remaining > 0
                      AND is_quarantined = false
                ORDER BY {order_by} ASC
            """

            rows = await conn.fetch(query, store_id, sku)
            return [self._map_to_entity(row) for row in rows]

    async def find_all(
        self,
        store_id: Optional[UUID] = None,
        sku: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[BatchTracking]:
        """Find batches with filtering"""
        query = "SELECT * FROM batch_tracking WHERE 1=1"
        params = []

        if store_id:
            params.append(store_id)
            query += f" AND store_id = ${len(params)}"

        if sku:
            params.append(sku)
            query += f" AND sku = ${len(params)}"

        if is_active is not None:
            params.append(is_active)
            query += f" AND is_active = ${len(params)}"

        params.append(limit)
        params.append(offset)
        query += f" ORDER BY created_at DESC LIMIT ${len(params)-1} OFFSET ${len(params)}"

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [self._map_to_entity(row) for row in rows]

    async def delete(self, batch_id: UUID) -> bool:
        """Soft delete batch (set is_active = false)"""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE batch_tracking
                SET is_active = false, updated_at = $2
                WHERE id = $1
                """,
                batch_id,
                datetime.utcnow()
            )

            return result == "UPDATE 1"

    def _map_to_entity(self, row: asyncpg.Record) -> BatchTracking:
        """
        Map database record to BatchTracking entity

        Handles field name differences between DB schema and entity
        """
        return BatchTracking(
            id=row['id'],
            store_id=row['store_id'],
            sku=row['sku'],
            batch_lot=row['batch_lot'],
            gtin=row.get('case_gtin') or row.get('gtin_barcode'),  # Prefer case_gtin
            quantity_received=row['quantity_received'],
            quantity_remaining=row['quantity_remaining'],
            unit_cost=Decimal(str(row['unit_cost'])) if row['unit_cost'] else Decimal('0'),
            received_date=row['received_date'],
            purchase_order_id=row.get('purchase_order_id'),
            location_id=row.get('location_id'),
            packaged_date=row.get('packaged_on_date'),
            is_active=row.get('is_active', True),
            is_quarantined=row.get('is_quarantined', False),
            quarantine_reason=row.get('quarantine_reason'),
            quality_check_status=row.get('quality_check_status', 'pending'),
            quality_check_date=row.get('quality_check_date'),
            quality_check_by=row.get('quality_check_by'),
            quality_notes=row.get('quality_notes'),
            created_at=row.get('created_at', datetime.utcnow()),
            updated_at=row.get('updated_at', datetime.utcnow())
        )


__all__ = [
    'IBatchTrackingRepository',
    'AsyncPGBatchTrackingRepository'
]
