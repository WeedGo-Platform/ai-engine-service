"""
Inventory Management Application Service
Orchestrates use cases for inventory and batch tracking
Following DDD Application Service pattern
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
import logging

from ...domain.inventory_management.entities.inventory import Inventory
from ...domain.inventory_management.entities.batch_tracking import BatchTracking
from ...domain.inventory_management.repositories import (
    IInventoryRepository,
    IBatchTrackingRepository
)

logger = logging.getLogger(__name__)


class InventoryManagementService:
    """
    Application service for inventory operations

    Orchestrates between Inventory and BatchTracking aggregates
    Maintains business rules and transaction boundaries
    """

    def __init__(
        self,
        inventory_repo: IInventoryRepository,
        batch_repo: IBatchTrackingRepository
    ):
        self.inventory_repo = inventory_repo
        self.batch_repo = batch_repo

    async def receive_inventory(
        self,
        store_id: UUID,
        sku: str,
        batch_lot: str,
        quantity: int,
        unit_cost: Decimal,
        purchase_order_id: UUID,
        case_gtin: Optional[str] = None,
        gtin_barcode: Optional[str] = None,
        each_gtin: Optional[str] = None,
        packaged_on_date: Optional[datetime] = None,
        product_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Receive inventory from purchase order

        Business Logic:
        1. Update ocs_inventory.quantity_on_hand (increase)
        2. Create or update batch_tracking record (UPSERT on batch_lot)
        3. If batch exists, merge quantities with weighted average cost

        Args:
            store_id: Store UUID
            sku: Product SKU
            batch_lot: Unique batch identifier
            quantity: Quantity received
            unit_cost: Cost per unit
            purchase_order_id: Source PO
            case_gtin: Optional GTIN for case
            gtin_barcode: Optional barcode GTIN
            each_gtin: Optional GTIN for each unit
            packaged_on_date: Optional packaging date
            product_name: Optional product name

        Returns:
            Dict with inventory_id, batch_id, and new quantities
        """
        try:
            # Get or create inventory record
            inventory = await self.inventory_repo.find_by_sku(store_id, sku)
            if not inventory:
                inventory = Inventory.create(
                    store_id=store_id,
                    sku=sku,
                    product_name=product_name or sku  # Use SKU as fallback if no product name
                )

            # Increase inventory quantity
            inventory.receive_stock(quantity=quantity, unit_cost=unit_cost, purchase_order_id=purchase_order_id)

            # Get existing batch (if any)
            batch = await self.batch_repo.find_by_lot(batch_lot, store_id)

            if batch:
                # Existing batch - merge quantities with weighted average cost
                logger.info(
                    f"Merging into existing batch {batch_lot}: "
                    f"existing qty={batch.quantity_remaining}, new qty={quantity}"
                )

                # Calculate weighted average cost
                old_total_cost = batch.unit_cost * Decimal(batch.quantity_remaining)
                new_total_cost = unit_cost * Decimal(quantity)
                total_quantity = batch.quantity_remaining + quantity

                weighted_avg_cost = (old_total_cost + new_total_cost) / Decimal(total_quantity)

                # Update batch
                batch.quantity_received += quantity
                batch.quantity_remaining += quantity
                batch.unit_cost = weighted_avg_cost
                batch.mark_as_modified()

            else:
                # New batch
                logger.info(f"Creating new batch {batch_lot} with qty={quantity}")

                batch = BatchTracking.create(
                    store_id=store_id,
                    sku=sku,
                    batch_lot=batch_lot,
                    quantity_received=quantity,
                    unit_cost=unit_cost,
                    purchase_order_id=purchase_order_id
                )

                # Set GTIN if provided
                if case_gtin or gtin_barcode:
                    batch.gtin = case_gtin or gtin_barcode

                # Set dates if provided
                if packaged_on_date:
                    batch.packaged_date = packaged_on_date

            # Save both aggregates
            inventory_id = await self.inventory_repo.save(inventory)
            batch_id = await self.batch_repo.save(batch)

            logger.info(
                f"Received inventory: SKU={sku}, Batch={batch_lot}, "
                f"Qty={quantity}, New Total={inventory.quantity_on_hand}"
            )

            return {
                'inventory_id': str(inventory_id),
                'batch_id': str(batch_id),
                'new_quantity_on_hand': inventory.quantity_on_hand,
                'batch_quantity_remaining': batch.quantity_remaining,
                'batch_unit_cost': float(batch.unit_cost)
            }

        except Exception as e:
            logger.error(f"Error receiving inventory: {e}")
            raise

    async def consume_inventory_fifo(
        self,
        store_id: UUID,
        sku: str,
        quantity: int
    ) -> Dict[str, Any]:
        """
        Consume inventory using FIFO (First In, First Out)

        Used by POS sales, returns, damage, etc.

        Business Logic:
        1. Reduce ocs_inventory.quantity_on_hand
        2. Get active batches ordered by created_at ASC (oldest first)
        3. Consume from batches in FIFO order
        4. Set batch.is_active = False when quantity_remaining = 0

        Args:
            store_id: Store UUID
            sku: Product SKU
            quantity: Quantity to consume

        Returns:
            Dict with total consumed, affected batches, new inventory level

        Raises:
            ValueError: If insufficient inventory
        """
        try:
            # Get inventory record
            inventory = await self.inventory_repo.find_by_sku(store_id, sku)
            if not inventory:
                raise ValueError(f"Inventory not found for SKU {sku}")

            # Check if enough stock
            if not inventory.can_reduce(quantity):
                raise ValueError(
                    f"Insufficient inventory for SKU {sku}: "
                    f"need {quantity}, have {inventory.quantity_on_hand}"
                )

            # Reduce inventory level
            inventory.reduce(quantity)

            # Get active batches in FIFO order (oldest first)
            active_batches = await self.batch_repo.find_active_for_sku(
                store_id, sku, order_by="created_at"
            )

            if not active_batches:
                raise ValueError(f"No active batches found for SKU {sku}")

            # Consume from batches using FIFO
            remaining_to_consume = quantity
            consumed_batches = []

            for batch in active_batches:
                if remaining_to_consume <= 0:
                    break

                # Consume what we can from this batch
                consumed = min(batch.quantity_remaining, remaining_to_consume)
                batch.consume(consumed)
                remaining_to_consume -= consumed

                consumed_batches.append({
                    'batch_lot': batch.batch_lot,
                    'consumed': consumed,
                    'remaining': batch.quantity_remaining,
                    'is_depleted': batch.quantity_remaining == 0
                })

                # Save batch
                await self.batch_repo.save(batch)

            # Save inventory
            await self.inventory_repo.save(inventory)

            logger.info(
                f"Consumed inventory: SKU={sku}, Qty={quantity}, "
                f"Batches affected={len(consumed_batches)}, "
                f"New Total={inventory.quantity_on_hand}"
            )

            return {
                'total_consumed': quantity,
                'batches_affected': consumed_batches,
                'new_inventory_level': inventory.quantity_on_hand
            }

        except Exception as e:
            logger.error(f"Error consuming inventory: {e}")
            raise

    async def search_inventory(
        self,
        store_id: UUID,
        search_term: Optional[str] = None,
        in_stock_only: bool = True,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search inventory with filters

        Args:
            store_id: Store UUID
            search_term: Optional search term (not implemented yet)
            in_stock_only: Only return items with stock
            limit: Max results

        Returns:
            List of inventory DTOs
        """
        try:
            inventories = await self.inventory_repo.find_all_for_store(
                store_id, in_stock_only, limit
            )

            return [self._inventory_to_dto(inv) for inv in inventories]

        except Exception as e:
            logger.error(f"Error searching inventory: {e}")
            raise

    async def adjust_inventory(
        self,
        store_id: UUID,
        sku: str,
        adjustment: int,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Manually adjust inventory quantity

        Used for stock counts, corrections, damage write-offs

        Args:
            store_id: Store UUID
            sku: Product SKU
            adjustment: Quantity to add (positive) or remove (negative)
            reason: Reason for adjustment

        Returns:
            Dict with old and new quantities
        """
        try:
            inventory = await self.inventory_repo.find_by_sku(store_id, sku)
            if not inventory:
                raise ValueError(f"Inventory not found for SKU {sku}")

            old_quantity = inventory.quantity_on_hand

            if adjustment > 0:
                inventory.receive(adjustment)
            else:
                inventory.reduce(abs(adjustment))

            await self.inventory_repo.save(inventory)

            logger.info(
                f"Adjusted inventory: SKU={sku}, Adjustment={adjustment}, "
                f"Old={old_quantity}, New={inventory.quantity_on_hand}, "
                f"Reason={reason or 'N/A'}"
            )

            return {
                'sku': sku,
                'old_quantity': old_quantity,
                'new_quantity': inventory.quantity_on_hand,
                'adjustment': adjustment,
                'reason': reason
            }

        except Exception as e:
            logger.error(f"Error adjusting inventory: {e}")
            raise

    def _inventory_to_dto(self, inventory: Inventory) -> Dict[str, Any]:
        """Convert Inventory entity to DTO for API layer"""
        return {
            'id': str(inventory.id),
            'store_id': str(inventory.store_id),
            'sku': inventory.sku,
            'quantity_on_hand': inventory.quantity_on_hand,
            'quantity_reserved': inventory.quantity_reserved,
            'quantity_available': inventory.get_available_quantity(),
            'reorder_point': inventory.reorder_point,
            'reorder_quantity': inventory.reorder_quantity,
            'is_low_stock': inventory.is_low_stock(),
            'last_restocked': inventory.last_restocked.isoformat() if inventory.last_restocked else None,
            'created_at': inventory.created_at.isoformat(),
            'updated_at': inventory.updated_at.isoformat()
        }


__all__ = ['InventoryManagementService']
