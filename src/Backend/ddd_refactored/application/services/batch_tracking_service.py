"""
Batch Tracking Application Service
Handles batch-specific operations (location, quality control, etc.)
Following DDD Application Service pattern
"""

from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime
import logging

from ...domain.inventory_management.entities.batch_tracking import BatchTracking
from ...domain.inventory_management.repositories import IBatchTrackingRepository

logger = logging.getLogger(__name__)


class BatchTrackingService:
    """Application service for batch tracking operations"""

    def __init__(self, batch_repo: IBatchTrackingRepository):
        self.batch_repo = batch_repo

    async def get_batch_details(
        self,
        batch_lot: str,
        store_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a batch

        Args:
            batch_lot: Batch lot number
            store_id: Store UUID

        Returns:
            Batch details as DTO or None if not found
        """
        try:
            batch = await self.batch_repo.find_by_lot(batch_lot, store_id)
            if not batch:
                return None

            return self._batch_to_dto(batch)

        except Exception as e:
            logger.error(f"Error getting batch details: {e}")
            raise

    async def move_batch_to_location(
        self,
        batch_lot: str,
        store_id: UUID,
        location_id: UUID
    ) -> Dict[str, Any]:
        """
        Move batch to shelf location

        Args:
            batch_lot: Batch lot number
            store_id: Store UUID
            location_id: Shelf location UUID

        Returns:
            Updated batch details
        """
        try:
            batch = await self.batch_repo.find_by_lot(batch_lot, store_id)
            if not batch:
                raise ValueError(f"Batch {batch_lot} not found")

            # Use domain method
            batch.move_to_location(location_id)

            # Save
            await self.batch_repo.save(batch)

            logger.info(f"Moved batch {batch_lot} to location {location_id}")

            return self._batch_to_dto(batch)

        except Exception as e:
            logger.error(f"Error moving batch to location: {e}")
            raise

    async def perform_quality_check(
        self,
        batch_lot: str,
        store_id: UUID,
        status: str,  # 'passed' or 'failed'
        checked_by: UUID,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform quality control check on batch

        Args:
            batch_lot: Batch lot number
            store_id: Store UUID
            status: QC status ('passed' or 'failed')
            checked_by: User who performed QC
            notes: Optional QC notes

        Returns:
            Updated batch details
        """
        try:
            batch = await self.batch_repo.find_by_lot(batch_lot, store_id)
            if not batch:
                raise ValueError(f"Batch {batch_lot} not found")

            # Use domain method (handles quarantine if failed)
            batch.perform_quality_check(status, checked_by, notes)

            # Save
            await self.batch_repo.save(batch)

            logger.info(
                f"Quality check on batch {batch_lot}: status={status}, "
                f"checked_by={checked_by}, quarantined={batch.is_quarantined}"
            )

            return {
                'batch_lot': batch.batch_lot,
                'quality_check_status': status,
                'is_quarantined': batch.is_quarantined,
                'quarantine_reason': batch.quarantine_reason,
                'checked_by': str(checked_by),
                'checked_at': batch.quality_check_date.isoformat() if batch.quality_check_date else None
            }

        except Exception as e:
            logger.error(f"Error performing quality check: {e}")
            raise

    async def adjust_batch_quantity(
        self,
        batch_lot: str,
        store_id: UUID,
        adjustment: int,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Manually adjust batch quantity

        Args:
            batch_lot: Batch lot number
            store_id: Store UUID
            adjustment: Quantity to add (positive) or remove (negative)
            reason: Reason for adjustment (e.g., 'damage', 'count correction')

        Returns:
            Updated batch details
        """
        try:
            batch = await self.batch_repo.find_by_lot(batch_lot, store_id)
            if not batch:
                raise ValueError(f"Batch {batch_lot} not found")

            old_quantity = batch.quantity_remaining

            if adjustment < 0:
                # Reduction - use consume or damage method
                if reason and 'damage' in reason.lower():
                    batch.damage(abs(adjustment), reason)
                else:
                    batch.consume(abs(adjustment))
            else:
                # Increase - add to quantity_remaining
                # (Note: BatchTracking entity doesn't have receive_additional yet,
                # so we'll modify directly)
                batch.quantity_remaining += adjustment
                batch.quantity_received += adjustment
                batch.mark_as_modified()

            # Save
            await self.batch_repo.save(batch)

            logger.info(
                f"Adjusted batch {batch_lot}: old={old_quantity}, "
                f"new={batch.quantity_remaining}, adjustment={adjustment}, reason={reason}"
            )

            return {
                'batch_lot': batch.batch_lot,
                'old_quantity': old_quantity,
                'new_quantity': batch.quantity_remaining,
                'adjustment': adjustment,
                'reason': reason
            }

        except Exception as e:
            logger.error(f"Error adjusting batch quantity: {e}")
            raise

    async def quarantine_batch(
        self,
        batch_lot: str,
        store_id: UUID,
        reason: str
    ) -> Dict[str, Any]:
        """
        Quarantine a batch

        Args:
            batch_lot: Batch lot number
            store_id: Store UUID
            reason: Reason for quarantine

        Returns:
            Updated batch details
        """
        try:
            batch = await self.batch_repo.find_by_lot(batch_lot, store_id)
            if not batch:
                raise ValueError(f"Batch {batch_lot} not found")

            # Use domain method
            batch.quarantine(reason)

            # Save
            await self.batch_repo.save(batch)

            logger.info(f"Quarantined batch {batch_lot}: reason={reason}")

            return self._batch_to_dto(batch)

        except Exception as e:
            logger.error(f"Error quarantining batch: {e}")
            raise

    async def release_from_quarantine(
        self,
        batch_lot: str,
        store_id: UUID
    ) -> Dict[str, Any]:
        """
        Release batch from quarantine

        Args:
            batch_lot: Batch lot number
            store_id: Store UUID

        Returns:
            Updated batch details
        """
        try:
            batch = await self.batch_repo.find_by_lot(batch_lot, store_id)
            if not batch:
                raise ValueError(f"Batch {batch_lot} not found")

            # Use domain method
            batch.release_from_quarantine()

            # Save
            await self.batch_repo.save(batch)

            logger.info(f"Released batch {batch_lot} from quarantine")

            return self._batch_to_dto(batch)

        except Exception as e:
            logger.error(f"Error releasing batch from quarantine: {e}")
            raise

    def _batch_to_dto(self, batch: BatchTracking) -> Dict[str, Any]:
        """Convert BatchTracking entity to DTO for API layer"""
        return {
            'id': str(batch.id),
            'store_id': str(batch.store_id),
            'sku': batch.sku,
            'batch_lot': batch.batch_lot,
            'gtin': batch.gtin,
            'quantity_received': batch.quantity_received,
            'quantity_remaining': batch.quantity_remaining,
            'quantity_damaged': batch.quantity_damaged,
            'quantity_expired': batch.quantity_expired,
            'unit_cost': float(batch.unit_cost),
            'total_cost': float(batch.total_cost),
            'received_date': batch.received_date.isoformat() if batch.received_date else None,
            'packaged_date': batch.packaged_date.isoformat() if batch.packaged_date else None,
            'production_date': batch.production_date.isoformat() if batch.production_date else None,
            'expiry_date': batch.expiry_date.isoformat() if batch.expiry_date else None,
            'is_expired': batch.is_expired(),
            'days_until_expiry': batch.days_until_expiry(),
            'is_near_expiry': batch.is_near_expiry(),
            'purchase_order_id': str(batch.purchase_order_id) if batch.purchase_order_id else None,
            'location_id': str(batch.location_id) if batch.location_id else None,
            'is_active': batch.is_active,
            'is_quarantined': batch.is_quarantined,
            'quarantine_reason': batch.quarantine_reason,
            'quality_check_status': batch.quality_check_status,
            'quality_check_date': batch.quality_check_date.isoformat() if batch.quality_check_date else None,
            'quality_check_by': str(batch.quality_check_by) if batch.quality_check_by else None,
            'quality_notes': batch.quality_notes,
            'utilization_rate': float(batch.get_utilization_rate()),
            'wastage_rate': float(batch.get_wastage_rate()),
            'remaining_value': float(batch.get_remaining_value()),
            'created_at': batch.created_at.isoformat(),
            'updated_at': batch.updated_at.isoformat()
        }


__all__ = ['BatchTrackingService']
