"""
Inventory Repository - Interface and Implementation
Following Repository Pattern from DDD Architecture

Maps Inventory aggregate to ocs_inventory table
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
import asyncpg
import logging

from ..entities.inventory import Inventory

logger = logging.getLogger(__name__)


class IInventoryRepository(ABC):
    """Repository interface for inventory operations"""

    @abstractmethod
    async def save(self, inventory: Inventory) -> UUID:
        """
        Save (insert or update) an inventory record

        Args:
            inventory: Inventory entity

        Returns:
            UUID of the saved inventory
        """
        pass

    @abstractmethod
    async def find_by_id(self, inventory_id: UUID) -> Optional[Inventory]:
        """Get inventory by ID"""
        pass

    @abstractmethod
    async def find_by_sku(self, store_id: UUID, sku: str) -> Optional[Inventory]:
        """Get inventory by SKU for a specific store"""
        pass

    @abstractmethod
    async def find_all_for_store(
        self,
        store_id: UUID,
        in_stock_only: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[Inventory]:
        """Get all inventory for a store"""
        pass

    @abstractmethod
    async def delete(self, inventory_id: UUID) -> bool:
        """Delete inventory record"""
        pass


class AsyncPGInventoryRepository(IInventoryRepository):
    """AsyncPG implementation of inventory repository"""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool

    async def save(self, inventory: Inventory) -> UUID:
        """
        Save inventory to database

        Handles both INSERT (new inventory) and UPDATE (existing inventory)
        """
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Check if inventory exists
                exists = await conn.fetchval(
                    "SELECT id FROM ocs_inventory WHERE store_id = $1 AND sku = $2",
                    inventory.store_id,
                    inventory.sku
                )

                if exists:
                    # Update existing inventory
                    await self._update_inventory(conn, inventory)
                    return exists
                else:
                    # Insert new inventory
                    return await self._insert_inventory(conn, inventory)

    async def _insert_inventory(self, conn: asyncpg.Connection, inventory: Inventory) -> UUID:
        """Insert new inventory"""
        query = """
            INSERT INTO ocs_inventory (
                id, store_id, sku, quantity_on_hand, quantity_reserved,
                reorder_point, reorder_quantity, last_restocked, running_balance,
                created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id
        """

        inventory_id = await conn.fetchval(
            query,
            inventory.id,
            inventory.store_id,
            inventory.sku,
            inventory.quantity_on_hand,
            inventory.quantity_reserved,
            inventory.reorder_point,
            inventory.reorder_quantity,
            inventory.last_restocked,
            inventory.quantity_on_hand,  # running_balance = quantity_on_hand initially
            inventory.created_at,
            inventory.updated_at
        )

        logger.info(f"Inserted new inventory for SKU {inventory.sku} (ID: {inventory_id})")
        return inventory_id

    async def _update_inventory(self, conn: asyncpg.Connection, inventory: Inventory) -> None:
        """Update existing inventory"""
        query = """
            UPDATE ocs_inventory
            SET quantity_on_hand = $3,
                quantity_reserved = $4,
                reorder_point = $5,
                reorder_quantity = $6,
                last_restocked = $7,
                running_balance = $8,
                updated_at = $9
            WHERE store_id = $1 AND sku = $2
        """

        await conn.execute(
            query,
            inventory.store_id,
            inventory.sku,
            inventory.quantity_on_hand,
            inventory.quantity_reserved,
            inventory.reorder_point,
            inventory.reorder_quantity,
            inventory.last_restocked,
            inventory.quantity_on_hand,  # running_balance = quantity_on_hand
            datetime.utcnow()
        )

        logger.info(f"Updated inventory for SKU {inventory.sku}")

    async def find_by_id(self, inventory_id: UUID) -> Optional[Inventory]:
        """Get inventory by ID"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM ocs_inventory WHERE id = $1",
                inventory_id
            )

            if not row:
                return None

            return self._map_to_entity(row)

    async def find_by_sku(self, store_id: UUID, sku: str) -> Optional[Inventory]:
        """Get inventory by SKU for a specific store"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM ocs_inventory WHERE store_id = $1 AND sku = $2",
                store_id,
                sku
            )

            if not row:
                return None

            return self._map_to_entity(row)

    async def find_all_for_store(
        self,
        store_id: UUID,
        in_stock_only: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[Inventory]:
        """Get all inventory for a store"""
        query = "SELECT * FROM ocs_inventory WHERE store_id = $1"

        if in_stock_only:
            query += " AND quantity_on_hand > 0"

        query += f" ORDER BY sku LIMIT ${2} OFFSET ${3}"

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, store_id, limit, offset)
            return [self._map_to_entity(row) for row in rows]

    async def delete(self, inventory_id: UUID) -> bool:
        """Delete inventory record"""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM ocs_inventory WHERE id = $1",
                inventory_id
            )

            return result == "DELETE 1"

    def _map_to_entity(self, row: asyncpg.Record) -> Inventory:
        """
        Map database record to Inventory entity
        """
        return Inventory(
            id=row['id'],
            store_id=row['store_id'],
            sku=row['sku'],
            quantity_on_hand=row['quantity_on_hand'],
            quantity_reserved=row.get('quantity_reserved', 0),
            reorder_point=row.get('reorder_point', 0),
            reorder_quantity=row.get('reorder_quantity', 0),
            last_restocked=row.get('last_restocked'),
            created_at=row.get('created_at', datetime.utcnow()),
            updated_at=row.get('updated_at', datetime.utcnow())
        )


__all__ = [
    'IInventoryRepository',
    'AsyncPGInventoryRepository'
]
