"""
Purchase Order Application Service
Orchestrates use cases for purchase order management
Following DDD Application Service pattern
"""

from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import date, datetime
from decimal import Decimal
import logging

from ...domain.purchase_order.entities.purchase_order import PurchaseOrder
from ...domain.purchase_order.value_objects.order_status import PurchaseOrderStatus
from ...domain.purchase_order.repositories import IPurchaseOrderRepository

logger = logging.getLogger(__name__)


class PurchaseOrderApplicationService:
    """
    Application service for purchase order operations

    Orchestrates use cases by:
    1. Accepting DTOs/primitives from API layer
    2. Creating/loading domain aggregates
    3. Invoking domain methods
    4. Persisting via repositories
    5. Returning DTOs/primitives to API layer
    """

    def __init__(self, repository: IPurchaseOrderRepository):
        self.repository = repository

    async def create_from_asn(
        self,
        supplier_id: UUID,
        items: List[Dict[str, Any]],
        expected_date: date,
        excel_filename: str,
        store_id: UUID,
        notes: Optional[str] = None,
        shipment_id: Optional[str] = None,
        container_id: Optional[str] = None,
        vendor: Optional[str] = None,
        tenant_id: Optional[UUID] = None,
        created_by: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Create purchase order from ASN (Advance Shipping Notice) import

        This maintains the same contract as InventoryService.create_purchase_order()
        but uses DDD domain model internally

        Args:
            supplier_id: Supplier UUID
            items: List of ASN items with SKU, quantity, cost, batch info
            expected_date: Expected delivery date
            excel_filename: ASN Excel filename for PO number generation
            store_id: Store UUID
            notes: Optional internal notes
            shipment_id: Optional shipment ID from ASN
            container_id: Optional container ID from ASN
            vendor: Vendor name from ASN
            tenant_id: Optional tenant ID
            created_by: Optional user ID who created PO

        Returns:
            Dict with 'id' and 'po_number' keys (same as legacy service)

        Raises:
            ValueError: If PO already exists for this filename or validation fails
        """
        try:
            # 1. Generate PO number (same logic as legacy service)
            po_number = self._generate_po_number(excel_filename)

            # 2. Check for duplicates
            existing_po = await self.repository.find_by_order_number(po_number)
            if existing_po:
                raise ValueError(
                    f"Purchase order already exists for file: {excel_filename}. "
                    f"This file has already been imported."
                )

            # 3. Calculate total amount
            total_amount = sum(
                Decimal(str(item['quantity'])) * Decimal(str(item['unit_cost']))
                for item in items
            )

            # 4. Create PurchaseOrder aggregate using domain factory method
            purchase_order = PurchaseOrder.create(
                store_id=store_id,
                tenant_id=tenant_id or store_id,  # Default to store_id if not provided
                supplier_id=supplier_id,
                supplier_name=vendor or "Unknown Supplier",
                order_number=po_number,
                expected_delivery_date=expected_date,
                total_amount=total_amount,
                internal_notes=notes,
                created_by=created_by
            )

            # 5. Store additional metadata from ASN
            purchase_order.metadata['shipment_id'] = shipment_id
            purchase_order.metadata['container_id'] = container_id
            purchase_order.metadata['excel_filename'] = excel_filename
            purchase_order.metadata['item_count'] = len(items)

            # Store items data for persistence (repository will handle line items)
            purchase_order.metadata['items'] = items

            # 6. Save via repository
            po_id = await self.repository.save(purchase_order)

            # 7. Also need to save line items (for now, do this directly until we refactor fully)
            # NOTE: In full DDD, line items would be part of the aggregate
            # For now, we'll add a method to handle this in the repository
            await self._save_line_items(po_id, items)

            logger.info(
                f"Created purchase order {po_number} with {len(items)} items "
                f"via DDD application service"
            )

            # 8. Return same format as legacy service for API compatibility
            return {
                'id': po_id,
                'po_number': po_number
            }

        except ValueError as ve:
            # Business validation errors
            logger.warning(f"Validation error creating purchase order: {ve}")
            raise
        except Exception as e:
            logger.error(f"Error creating purchase order from ASN: {e}")
            raise

    async def get_purchase_order(self, po_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get purchase order by ID

        Args:
            po_id: Purchase order UUID

        Returns:
            Dict representation of purchase order or None
        """
        try:
            po = await self.repository.find_by_id(po_id)
            if not po:
                return None

            return self._to_dto(po)

        except Exception as e:
            logger.error(f"Error getting purchase order {po_id}: {e}")
            raise

    async def list_purchase_orders(
        self,
        store_id: Optional[UUID] = None,
        supplier_id: Optional[UUID] = None,
        status: Optional[PurchaseOrderStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List purchase orders with filtering

        Args:
            store_id: Optional filter by store
            supplier_id: Optional filter by supplier
            status: Optional filter by status
            limit: Max results
            offset: Pagination offset

        Returns:
            List of purchase order DTOs
        """
        try:
            pos = await self.repository.find_all(
                store_id=store_id,
                supplier_id=supplier_id,
                status=status,
                limit=limit,
                offset=offset
            )

            return [self._to_dto(po) for po in pos]

        except Exception as e:
            logger.error(f"Error listing purchase orders: {e}")
            raise

    def _generate_po_number(self, excel_filename: str) -> str:
        """
        Generate PO number from Excel filename
        Same logic as legacy service for consistency

        Args:
            excel_filename: Name of ASN Excel file

        Returns:
            PO number in format: PO-YYYYMMDD-filename
        """
        # Clean up filename: remove ASN_ prefix and file extension
        clean_filename = excel_filename
        if clean_filename and clean_filename.startswith('ASN_'):
            clean_filename = clean_filename[4:]
        if clean_filename and clean_filename.endswith('.xlsx'):
            clean_filename = clean_filename[:-5]
        elif clean_filename and clean_filename.endswith('.xls'):
            clean_filename = clean_filename[:-4]

        po_number = f"PO-{datetime.now().strftime('%Y%m%d')}-{clean_filename}"
        return po_number

    async def _save_line_items(self, po_id: UUID, items: List[Dict[str, Any]]):
        """
        Save purchase order line items

        Uses repository to persist line items from ASN data
        Maintains compatibility with existing database schema

        TODO: Refactor to use PurchaseOrderLineItem value objects within aggregate
        """
        return await self.repository.save_line_items(po_id, items)

    def _to_dto(self, po: PurchaseOrder) -> Dict[str, Any]:
        """
        Convert PurchaseOrder aggregate to DTO for API layer

        Args:
            po: PurchaseOrder aggregate

        Returns:
            Dictionary representation
        """
        return {
            'id': str(po.id),
            'order_number': po.order_number,
            'store_id': str(po.store_id),
            'tenant_id': str(po.tenant_id) if po.tenant_id else None,
            'supplier_id': str(po.supplier_id),
            'supplier_name': po.supplier_name,
            'status': po.status.value if hasattr(po.status, 'value') else str(po.status),
            'order_date': po.order_date.isoformat() if po.order_date else None,
            'expected_delivery_date': po.expected_delivery_date.isoformat() if po.expected_delivery_date else None,
            'total_amount': float(po.total_amount) if po.total_amount else 0.0,
            'internal_notes': po.internal_notes,
            'created_by': str(po.created_by) if po.created_by else None,
            'created_at': po.created_at.isoformat() if po.created_at else None,
            'updated_at': po.updated_at.isoformat() if po.updated_at else None,
            'metadata': po.metadata
        }


__all__ = ['PurchaseOrderApplicationService']
