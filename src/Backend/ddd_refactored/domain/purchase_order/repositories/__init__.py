"""
Purchase Order Repository - Interface and Implementation
Following Repository Pattern from DDD Architecture

Maps PurchaseOrder aggregate to database tables
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal
import asyncpg
import logging

from ..entities.purchase_order import PurchaseOrder
from ..value_objects.order_status import PurchaseOrderStatus, ApprovalStatus, PaymentTerms

logger = logging.getLogger(__name__)


class IPurchaseOrderRepository(ABC):
    """Repository interface for Purchase Order operations"""

    @abstractmethod
    async def save(self, purchase_order: PurchaseOrder) -> UUID:
        """
        Save (insert or update) a purchase order

        Args:
            purchase_order: PurchaseOrder aggregate root

        Returns:
            UUID of the saved purchase order
        """
        pass

    @abstractmethod
    async def find_by_id(self, po_id: UUID) -> Optional[PurchaseOrder]:
        """Get purchase order by ID"""
        pass

    @abstractmethod
    async def find_by_order_number(self, order_number: str) -> Optional[PurchaseOrder]:
        """Get purchase order by order number"""
        pass

    @abstractmethod
    async def find_all(
        self,
        store_id: Optional[UUID] = None,
        supplier_id: Optional[UUID] = None,
        status: Optional[PurchaseOrderStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[PurchaseOrder]:
        """Find purchase orders with filtering"""
        pass

    @abstractmethod
    async def delete(self, po_id: UUID) -> bool:
        """Delete purchase order (soft delete)"""
        pass

    @abstractmethod
    async def save_line_items(self, po_id: UUID, items: List[Dict[str, Any]]) -> int:
        """
        Save purchase order line items

        Args:
            po_id: Purchase order UUID
            items: List of item dictionaries from ASN

        Returns:
            Number of items saved
        """
        pass


class AsyncPGPurchaseOrderRepository(IPurchaseOrderRepository):
    """AsyncPG implementation of purchase order repository"""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool

    def _map_status_to_db(self, domain_status: PurchaseOrderStatus) -> str:
        """
        Map domain status to database status (Anti-Corruption Layer)

        Database constraint only allows: 'pending', 'partial', 'received', 'cancelled'
        Domain model has richer status values for business logic

        Args:
            domain_status: Rich domain status from PurchaseOrderStatus enum

        Returns:
            Database-compatible status string
        """
        status_mapping = {
            PurchaseOrderStatus.DRAFT: "pending",
            PurchaseOrderStatus.SUBMITTED: "pending",
            PurchaseOrderStatus.APPROVED: "pending",
            PurchaseOrderStatus.SENT_TO_SUPPLIER: "pending",
            PurchaseOrderStatus.CONFIRMED: "pending",
            PurchaseOrderStatus.PARTIALLY_RECEIVED: "partial",
            PurchaseOrderStatus.FULLY_RECEIVED: "received",
            PurchaseOrderStatus.CLOSED: "received",
            PurchaseOrderStatus.CANCELLED: "cancelled"
        }

        db_status = status_mapping.get(domain_status, "pending")
        logger.debug(f"Mapping domain status {domain_status.value} to database status {db_status}")
        return db_status

    def _map_status_from_db(self, db_status: str) -> PurchaseOrderStatus:
        """
        Map database status to domain status

        Args:
            db_status: Database status string

        Returns:
            Domain PurchaseOrderStatus enum
        """
        status_mapping = {
            "pending": PurchaseOrderStatus.DRAFT,
            "partial": PurchaseOrderStatus.PARTIALLY_RECEIVED,
            "received": PurchaseOrderStatus.FULLY_RECEIVED,
            "cancelled": PurchaseOrderStatus.CANCELLED
        }

        return status_mapping.get(db_status, PurchaseOrderStatus.DRAFT)

    async def save(self, purchase_order: PurchaseOrder) -> UUID:
        """
        Save purchase order aggregate to database

        Maps aggregate root to purchase_orders and purchase_order_items tables
        """
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Check if PO exists
                exists = await conn.fetchval(
                    "SELECT COUNT(*) FROM purchase_orders WHERE id = $1",
                    purchase_order.id
                )

                if exists:
                    # Update existing PO
                    await self._update_purchase_order(conn, purchase_order)
                else:
                    # Insert new PO
                    await self._insert_purchase_order(conn, purchase_order)

                logger.info(f"Saved purchase order {purchase_order.order_number} (ID: {purchase_order.id})")
                return purchase_order.id

    async def _insert_purchase_order(self, conn: asyncpg.Connection, po: PurchaseOrder):
        """Insert new purchase order"""
        query = """
            INSERT INTO purchase_orders (
                id, po_number, supplier_id, order_date, expected_date, status,
                total_amount, subtotal, tax_amount, notes, store_id, shipment_id, container_id,
                charges, paid, created_by, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
        """

        # Map domain status to database status using Anti-Corruption Layer
        db_status = self._map_status_to_db(po.status)

        # Convert charges to JSON if present
        import json
        charges_json = json.dumps(po.metadata.get('charges', [])) if po.metadata.get('charges') else None

        await conn.execute(
            query,
            po.id,
            po.order_number,
            po.supplier_id,
            po.order_date,
            po.expected_delivery_date,
            db_status,  # Use mapped database status
            po.total_amount,
            po.subtotal,
            po.tax_amount,
            po.internal_notes,
            po.store_id,
            po.metadata.get('shipment_id'),
            po.metadata.get('container_id'),
            charges_json,  # JSONB charges
            po.metadata.get('paid', False),  # Boolean paid status
            po.created_by,
            po.created_at,
            po.updated_at
        )

    async def _update_purchase_order(self, conn: asyncpg.Connection, po: PurchaseOrder):
        """Update existing purchase order"""
        query = """
            UPDATE purchase_orders
            SET status = $2,
                total_amount = $3,
                notes = $4,
                expected_date = $5,
                received_date = $6,
                received_by = $7,
                approved_by = $8,
                updated_at = $9
            WHERE id = $1
        """

        # Map domain status to database status using Anti-Corruption Layer
        db_status = self._map_status_to_db(po.status)

        await conn.execute(
            query,
            po.id,
            db_status,  # Use mapped database status
            po.total_amount,
            po.internal_notes,
            po.expected_delivery_date,
            po.received_at,  # Maps to received_date in DB
            po.received_by,
            po.approved_by,
            datetime.utcnow()
        )

    async def find_by_id(self, po_id: UUID) -> Optional[PurchaseOrder]:
        """Get purchase order by ID"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM purchase_orders WHERE id = $1",
                po_id
            )

            if not row:
                return None

            return await self._map_to_aggregate(conn, row)

    async def find_by_order_number(self, order_number: str) -> Optional[PurchaseOrder]:
        """Get purchase order by order number"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM purchase_orders WHERE po_number = $1",
                order_number
            )

            if not row:
                return None

            return await self._map_to_aggregate(conn, row)

    async def find_all(
        self,
        store_id: Optional[UUID] = None,
        supplier_id: Optional[UUID] = None,
        status: Optional[PurchaseOrderStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[PurchaseOrder]:
        """Find purchase orders with filtering"""
        query = "SELECT * FROM purchase_orders WHERE 1=1"
        params = []

        if store_id:
            params.append(store_id)
            query += f" AND store_id = ${len(params)}"

        if supplier_id:
            params.append(supplier_id)
            query += f" AND supplier_id = ${len(params)}"

        if status:
            # Map domain status to database status for filtering
            db_status = self._map_status_to_db(status)
            params.append(db_status)
            query += f" AND status = ${len(params)}"

        params.append(limit)
        params.append(offset)
        query += f" ORDER BY created_at DESC LIMIT ${len(params)-1} OFFSET ${len(params)}"

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

            purchase_orders = []
            for row in rows:
                po = await self._map_to_aggregate(conn, row)
                if po:
                    purchase_orders.append(po)

            return purchase_orders

    async def delete(self, po_id: UUID) -> bool:
        """Soft delete purchase order"""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE purchase_orders
                SET status = 'cancelled', updated_at = $2
                WHERE id = $1
                """,
                po_id,
                datetime.utcnow()
            )

            return result == "UPDATE 1"

    async def save_line_items(self, po_id: UUID, items: List[Dict[str, Any]]) -> int:
        """
        Save purchase order line items to purchase_order_items table

        Maintains compatibility with existing database schema
        """
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                items_saved = 0

                for item in items:
                    # Insert line item with only sku column (ocs_sku has been removed)
                    item_query = """
                        INSERT INTO purchase_order_items
                        (purchase_order_id, sku, item_name, batch_lot, quantity_ordered,
                         unit_cost, total_cost, case_gtin, gtin_barcode, each_gtin,
                         vendor, brand, packaged_on_date,
                         shipped_qty, uom, uom_conversion, uom_conversion_qty)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                    """

                    sku_value = item['sku']
                    gtin_barcode_value = item.get('gtin_barcode')
                    unit_cost = Decimal(str(item['unit_cost']))
                    # Frontend sends 'quantity_ordered' (mapped from Excel shipped_qty)
                    quantity = item.get('quantity_ordered') or item.get('quantity')
                    total_cost = unit_cost * Decimal(str(quantity))

                    logger.info(
                        f"Saving line item {sku_value}: "
                        f"qty={quantity}, unit_cost={unit_cost}, total_cost={total_cost}, "
                        f"gtin_barcode={gtin_barcode_value}, "
                        f"case_gtin={item.get('case_gtin')}"
                    )

                    await conn.execute(
                        item_query,
                        po_id,
                        sku_value,  # sku column
                        item.get('item_name'),
                        item['batch_lot'],
                        quantity,
                        unit_cost,
                        total_cost,  # quantity_ordered * unit_cost
                        item['case_gtin'],
                        gtin_barcode_value,
                        item['each_gtin'],
                        item['vendor'],
                        item['brand'],
                        item['packaged_on_date'],
                        item['shipped_qty'],
                        item['uom'],
                        Decimal(str(item['uom_conversion'])),
                        item['uom_conversion_qty']
                    )

                    items_saved += 1

                logger.info(f"Saved {items_saved} line items for PO {po_id}")
                return items_saved

    async def _map_to_aggregate(self, conn: asyncpg.Connection, row: asyncpg.Record) -> PurchaseOrder:
        """
        Map database record to PurchaseOrder aggregate

        Reconstructs the aggregate from database tables
        """
        # Map database status back to domain status using Anti-Corruption Layer
        domain_status = self._map_status_from_db(row['status']) if row['status'] else PurchaseOrderStatus.DRAFT

        # Create PurchaseOrder instance from database data
        po = PurchaseOrder(
            id=row['id'],
            store_id=row['store_id'],
            tenant_id=row.get('tenant_id'),  # May not exist in current schema
            supplier_id=row['supplier_id'],
            supplier_name='',  # Supplier name retrieved from suppliers table if needed
            order_number=row['po_number'],
            status=domain_status,  # Use mapped domain status
            order_date=row['order_date'],
            expected_delivery_date=row.get('expected_date'),
            total_amount=Decimal(str(row['total_amount'])) if row['total_amount'] else Decimal('0'),
            internal_notes=row.get('notes'),
            created_by=row.get('created_by'),
            created_at=row.get('created_at', datetime.utcnow()),
            updated_at=row.get('updated_at', datetime.utcnow()),
        )

        # Set audit fields (received/approved tracking)
        po.received_at = row.get('received_date')  # DB column: received_date
        po.received_by = row.get('received_by')
        po.approved_by = row.get('approved_by')

        # Store additional metadata
        po.metadata['shipment_id'] = row.get('shipment_id')
        po.metadata['container_id'] = row.get('container_id')

        # Load line items count (from purchase_order_items table)
        items_count = await conn.fetchval(
            "SELECT COUNT(*) FROM purchase_order_items WHERE purchase_order_id = $1",
            row['id']
        )
        po.total_line_items = items_count or 0

        return po


__all__ = [
    'IPurchaseOrderRepository',
    'AsyncPGPurchaseOrderRepository'
]
