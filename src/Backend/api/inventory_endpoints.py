"""
Inventory Management API Endpoints (V1 - Production)

⚠️ MIGRATION NOTICE:
This is the V1 inventory API, currently in production use.
A new V2 API using DDD architecture is available at /api/v2/inventory/*

V2 advantages:
- Domain-Driven Design with Inventory aggregate
- Rich business rule validation
- Stock level management with automatic status calculation
- Reserve/release operations for order fulfillment
- Better separation of concerns
- Event sourcing ready
- Pricing and margin calculations

Migration path:
- V1 endpoints remain stable and backward compatible
- V2 provides enhanced features and better architecture
- Gradually migrate applications to V2 endpoints
- V1 will be deprecated after 6 months notice
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Header
from typing import List, Dict, Optional, Any
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field
import logging

from services.inventory_service import InventoryService
from api.v2.dependencies import (
    get_purchase_order_service,
    get_inventory_management_service,
    get_batch_tracking_service
)
from ddd_refactored.application.services.purchase_order_service import PurchaseOrderApplicationService
from ddd_refactored.application.services.inventory_management_service import InventoryManagementService
from ddd_refactored.application.services.batch_tracking_service import BatchTrackingService
import asyncpg
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/inventory", tags=["inventory"])

# Database connection pool
db_pool = None

async def get_db_pool():
    """Get or create database connection pool"""
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5434)),
            database=os.getenv('DB_NAME', 'ai_engine'),
            user=os.getenv('DB_USER', 'weedgo'),
            password=os.getenv('DB_PASSWORD', 'weedgo123'),
            min_size=1,
            max_size=10
        )
    return db_pool


# Pydantic Models
class PurchaseOrderItem(BaseModel):
    sku: str
    quantity: int = Field(gt=0)
    unit_cost: float = Field(gt=0)
    batch_lot: str  # Required
    case_gtin: str  # Required
    packaged_on_date: date  # Required
    gtin_barcode: Optional[str] = None  # Optional - not in Excel data
    each_gtin: str  # Required
    vendor: str  # Required
    brand: str  # Required
    item_name: str  # Required - Product name from Excel
    shipped_qty: int = Field(gt=0)  # Required
    uom: str  # Required
    uom_conversion: float = Field(gt=0)  # Required
    uom_conversion_qty: float = Field(gt=0)  # Required


class ChargeItem(BaseModel):
    """Individual charge item (shipping, discount, express, etc.)"""
    description: str  # e.g., "Shipping", "Discount", "Express Delivery"
    amount: float  # Positive for charges, negative for discounts
    taxable: bool = True  # Whether this charge is subject to tax (default: True)


class CreatePurchaseOrderRequest(BaseModel):
    supplier_id: UUID
    items: List[PurchaseOrderItem]
    expected_date: date  # Required
    notes: Optional[str] = None  # Optional
    excel_filename: str  # Required for PO number generation
    store_id: Optional[UUID] = None  # Can be provided in body or header
    shipment_id: Optional[str] = None  # From ASN Excel
    container_id: Optional[str] = None  # From ASN Excel
    ocs_order_number: Optional[str] = None  # Extracted from filename
    tenant_id: Optional[UUID] = None  # From store/context
    created_by: Optional[UUID] = None  # User ID from context
    shipment_date: Optional[date] = None  # From ASN Excel
    charges: Optional[List[ChargeItem]] = []  # Multiple charges (shipping, discount, etc.)
    paid: bool = True  # Paid in full (default True)
    # Note: vendor field removed - it belongs at the item level (PurchaseOrderItem.vendor)


class ReceivePurchaseOrderItem(BaseModel):
    sku: str
    quantity_received: int = Field(ge=0)
    unit_cost: float = Field(gt=0)
    batch_lot: str  # Required
    case_gtin: str  # Required
    packaged_on_date: date  # Required
    gtin_barcode: Optional[str] = None  # Optional - not in Excel data
    each_gtin: str  # Required
    vendor: str  # Required
    brand: str  # Required
    item_name: Optional[str] = None  # Optional - product name


class ReceivePurchaseOrderRequest(BaseModel):
    items: List[ReceivePurchaseOrderItem]


class UpdateInventoryRequest(BaseModel):
    sku: str
    quantity_change: int
    transaction_type: str = Field(pattern="^(sale|purchase|adjustment|return)$")
    reference_id: Optional[UUID] = None
    notes: Optional[str] = None


async def get_inventory_service():
    """Get inventory service instance"""
    pool = await get_db_pool()
    conn = await pool.acquire()
    try:
        yield InventoryService(conn)
    finally:
        await pool.release(conn)


@router.get("/status/{sku}")
async def get_inventory_status(
    sku: str,
    service: InventoryService = Depends(get_inventory_service)
):
    """Get current inventory status for a SKU"""
    try:
        status = await service.get_inventory_status(sku)
        if not status:
            raise HTTPException(status_code=404, detail=f"SKU {sku} not found")
        return status
    except Exception as e:
        logger.error(f"Error getting inventory status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update")
async def update_inventory(
    request: UpdateInventoryRequest,
    service: InventoryService = Depends(get_inventory_service)
):
    """Update inventory levels"""
    try:
        success = await service.update_inventory(
            request.sku,
            request.quantity_change,
            request.transaction_type,
            request.reference_id,
            request.notes
        )
        
        if not success:
            raise HTTPException(
                status_code=400, 
                detail="Failed to update inventory. Check stock levels."
            )
        
        return {"success": True, "message": "Inventory updated successfully"}
    except Exception as e:
        logger.error(f"Error updating inventory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/purchase-orders")
async def create_purchase_order(
    request: CreatePurchaseOrderRequest,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_store_id: Optional[str] = Header(None, alias="X-Store-ID"),
    po_service: PurchaseOrderApplicationService = Depends(get_purchase_order_service)
):
    """
    Create a new purchase order using DDD architecture

    ⚡ REFACTORED: Now uses Domain-Driven Design application service
    - Maintains exact same API contract for backward compatibility
    - Internal implementation uses PurchaseOrder aggregate and repository
    - Business logic encapsulated in domain model
    """
    try:
        # Get user_id from header (authenticated user)
        user_id = UUID(x_user_id) if x_user_id else None

        # Get store_id from request body or header
        store_id = request.store_id
        if not store_id and x_store_id and x_store_id.strip():
            try:
                store_id = UUID(x_store_id.strip())
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid store ID in header")

        if not store_id:
            raise HTTPException(status_code=400, detail="Store ID is required - please select a store")

        # Fetch provincial tax rate for the store
        tax_rate = None
        try:
            from api.store_endpoints import get_db_pool
            db_pool = await get_db_pool()
            async with db_pool.acquire() as conn:
                tax_row = await conn.fetchrow(
                    """
                    SELECT pt.tax_rate
                    FROM stores s
                    JOIN provinces_territories pt ON s.province_territory_id = pt.id
                    WHERE s.id = $1
                    """,
                    store_id
                )
                if tax_row and tax_row['tax_rate']:
                    tax_rate = float(tax_row['tax_rate'])
        except Exception as e:
            logger.warning(f"Could not fetch tax rate for store {store_id}: {e}")
            # Continue without tax if fetching fails

        # Convert charges from Pydantic models to dicts
        charges_data = [charge.dict() for charge in request.charges] if request.charges else []

        # Call DDD application service (same contract as legacy service)
        result = await po_service.create_from_asn(
            supplier_id=request.supplier_id,
            items=[item.dict() for item in request.items],
            expected_date=request.expected_date,
            excel_filename=request.excel_filename,
            store_id=store_id,
            notes=request.notes,
            shipment_id=request.shipment_id,
            container_id=request.container_id,
            tenant_id=request.tenant_id,
            created_by=user_id,  # Use authenticated user from header
            charges=charges_data,  # Pass charges array
            paid=request.paid,  # Pass paid status
            tax_rate=tax_rate  # Pass provincial tax rate
        )

        # Return same response format as legacy service for API compatibility
        return {
            "success": True,
            "purchase_order_id": str(result['id']),
            "message": f"Purchase order created with {len(request.items)} items"
        }
    except ValueError as ve:
        # Business validation errors from domain
        logger.warning(f"Validation error creating purchase order: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error creating purchase order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/purchase-orders/{po_id}/receive")
async def receive_purchase_order(
    po_id: UUID,
    request: ReceivePurchaseOrderRequest,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_store_id: Optional[str] = Header(None, alias="X-Store-ID"),
    po_service: PurchaseOrderApplicationService = Depends(get_purchase_order_service),
    inv_service: InventoryManagementService = Depends(get_inventory_management_service)
):
    """
    Process receipt of purchase order items

    DDD Implementation:
    1. Updates PO status via PurchaseOrderApplicationService.receive_purchase_order()
    2. Updates inventory & batches via InventoryManagementService.receive_inventory()

    Orchestrates:
    - PurchaseOrder aggregate (domain model)
    - Inventory & BatchTracking aggregates
    - FIFO batch creation with weighted average cost
    - Auto-approval on receiving
    """
    try:
        logger.info(f"[DDD] Receiving PO {po_id} with {len(request.items)} items")

        # Parse headers
        user_id = UUID(x_user_id) if x_user_id else None
        store_id = UUID(x_store_id) if x_store_id else None

        if not store_id:
            raise HTTPException(
                status_code=400,
                detail="Store ID (X-Store-ID header) is required for receiving"
            )

        # Convert Pydantic models to dict for application service
        received_items = [item.dict() for item in request.items]

        # 1. Update PO status (via domain method PurchaseOrder.receive())
        po_result = await po_service.receive_purchase_order(
            po_id=po_id,
            received_items=received_items,
            received_by=user_id,
            auto_approve=True  # Auto-approve on receive (business rule)
        )

        logger.info(
            f"[DDD] PO {po_result['order_number']} received: "
            f"{po_result['total_received']} units, status: {po_result['status']}"
        )

        # 2. Update inventory & batches for each item
        batch_results = []
        for item in request.items:
            logger.debug(
                f"[DDD] Receiving inventory: SKU={item.sku}, "
                f"batch_lot={item.batch_lot}, qty={item.quantity_received}"
            )

            # Use InventoryManagementService to handle both inventory and batch updates
            # Convert date to datetime for the service (which expects Optional[datetime])
            packaged_datetime = datetime.combine(item.packaged_on_date, datetime.min.time()) if item.packaged_on_date else None

            inv_result = await inv_service.receive_inventory(
                store_id=store_id,
                sku=item.sku,
                batch_lot=item.batch_lot,
                quantity=item.quantity_received,
                unit_cost=Decimal(str(item.unit_cost)),
                purchase_order_id=po_id,
                case_gtin=item.case_gtin,
                gtin_barcode=item.gtin_barcode,
                each_gtin=item.each_gtin,
                packaged_on_date=packaged_datetime,
                product_name=item.item_name  # Pass item_name as product_name
            )

            batch_results.append({
                'sku': item.sku,
                'batch_lot': item.batch_lot,
                'quantity_received': item.quantity_received,
                'batch_id': inv_result.get('batch_id')
            })

        logger.info(
            f"[DDD] Successfully received PO {po_id}: "
            f"{len(batch_results)} batches created/updated"
        )

        return {
            'success': True,
            'message': f"Received {len(request.items)} items for PO {po_id}",
            'po_details': {
                'id': po_result['id'],
                'order_number': po_result['order_number'],
                'total_received': po_result['total_received'],
                'status': po_result['status'],
                'is_fully_received': po_result.get('is_fully_received', False),
                'received_by': str(user_id) if user_id else None,
                'received_at': po_result.get('received_at')
            },
            'batches': batch_results
        }

    except ValueError as ve:
        # Domain validation errors
        logger.warning(f"[DDD] Validation error receiving PO {po_id}: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"[DDD] Error receiving PO {po_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/low-stock")
async def get_low_stock_items(
    threshold: float = Query(1.0, ge=0.1, le=2.0),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get items at or below reorder point"""
    try:
        items = await service.get_low_stock_items(threshold)
        return {
            "count": len(items),
            "items": items
        }
    except Exception as e:
        logger.error(f"Error getting low stock items: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/value-report")
async def get_inventory_value_report(
    service: InventoryService = Depends(get_inventory_service)
):
    """Get inventory valuation report"""
    try:
        report = await service.get_inventory_value_report()
        return report
    except Exception as e:
        logger.error(f"Error getting inventory value report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check")
async def check_inventory_exists(
    sku: str = Query(..., description="SKU to check"),
    store_id: str = Query(..., description="Store ID (required)"),
    batch_lot: Optional[str] = Query(None, description="Batch lot to check"),
    service: InventoryService = Depends(get_inventory_service)
):
    """Check if a SKU (and optionally batch lot) exists in inventory for a specific store"""
    try:
        # Validate store_id is a valid UUID
        try:
            from uuid import UUID
            UUID(store_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid store_id format: {store_id}. Must be a valid UUID."
            )

        conn = service.db

        # Verify store exists
        store_check = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM stores WHERE id = $1::uuid)",
            store_id
        )
        if not store_check:
            raise HTTPException(
                status_code=404,
                detail=f"Store with ID {store_id} does not exist"
            )

        if batch_lot:
            # Check for specific SKU + BatchLot combination in this store
            query = """
                SELECT EXISTS(
                    SELECT 1
                    FROM batch_tracking
                    WHERE LOWER(TRIM(sku)) = LOWER(TRIM($1))
                    AND batch_lot = $2
                    AND store_id = $3::uuid
                    AND quantity_remaining > 0
                ) as exists
            """
            result = await conn.fetchrow(query, sku, batch_lot, store_id)
        else:
            # Check for SKU only in this store
            query = """
                SELECT EXISTS(
                    SELECT 1
                    FROM ocs_inventory
                    WHERE LOWER(TRIM(sku)) = LOWER(TRIM($1))
                    AND store_id = $2::uuid
                    AND quantity_on_hand > 0
                ) as exists
            """
            result = await conn.fetchrow(query, sku, store_id)

        return {
            "exists": result['exists'],
            "sku": sku,
            "batch_lot": batch_lot,
            "store_id": store_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking inventory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batch/{batch_lot}")
async def get_batch_details(
    batch_lot: str,
    service: InventoryService = Depends(get_inventory_service)
):
    """Get detailed information for a specific batch including GTIN data"""
    try:
        conn = service.db
        query = """
            SELECT
                bt.*,
                pc.product_name
            FROM batch_tracking bt
            LEFT JOIN product_catalog pc ON bt.sku = pc.sku
            WHERE bt.batch_lot = $1
        """

        result = await conn.fetchrow(query, batch_lot)

        if not result:
            raise HTTPException(status_code=404, detail=f"Batch {batch_lot} not found")

        return dict(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting batch details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_inventory_products(
    q: Optional[str] = Query(None, description="Search term"),
    category: Optional[str] = Query(None, description="Product category"),
    in_stock: bool = Query(True, description="Only show in-stock items"),
    limit: int = Query(50, ge=1, le=200),
    service: InventoryService = Depends(get_inventory_service)
):
    """Search products with inventory information"""
    try:
        products = await service.search_inventory_products(
            search_term=q,
            category=category,
            in_stock_only=in_stock,
            limit=limit
        )
        
        return {
            "count": len(products),
            "products": products
        }
    except Exception as e:
        logger.error(f"Error searching inventory products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suppliers")
async def get_suppliers(
    service: InventoryService = Depends(get_inventory_service)
):
    """Get list of suppliers"""
    try:
        conn = service.db
        query = """
            SELECT 
                id,
                name,
                contact_person,
                email,
                phone,
                payment_terms,
                is_active
            FROM provincial_suppliers
            WHERE is_active = true
            ORDER BY name
        """
        
        results = await conn.fetch(query)
        return {
            "count": len(results),
            "suppliers": [dict(row) for row in results]
        }
    except Exception as e:
        logger.error(f"Error getting suppliers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/purchase-orders/{po_id}")
async def get_purchase_order_details(
    po_id: UUID,
    service: InventoryService = Depends(get_inventory_service)
):
    """Get purchase order details with items"""
    try:
        conn = service.db
        
        # Get purchase order details
        po_query = """
            SELECT
                po.id,
                po.po_number,
                po.supplier_id,
                s.name as supplier_name,
                po.order_date,
                po.expected_date,
                po.received_date,
                po.status,
                po.total_amount,
                po.subtotal,
                po.tax_amount,
                po.notes,
                po.shipment_id,
                po.container_id,
                po.charges,
                po.paid,
                po.created_by,
                po.received_by,
                po.approved_by
            FROM purchase_orders po
            JOIN provincial_suppliers s ON po.supplier_id = s.id
            WHERE po.id = $1
        """
        
        po_row = await conn.fetchrow(po_query, po_id)
        
        if not po_row:
            raise HTTPException(status_code=404, detail="Purchase order not found")
        
        # Get purchase order items
        items_query = """
            SELECT
                poi.id,
                poi.sku,
                poi.item_name,
                poi.quantity_ordered,
                poi.quantity_received,
                poi.unit_cost,
                poi.total_cost,
                poi.batch_lot,
                poi.case_gtin,
                poi.gtin_barcode,
                poi.each_gtin,
                poi.vendor,
                poi.brand,
                poi.packaged_on_date,
                poi.shipped_qty,
                poi.uom,
                poi.uom_conversion,
                poi.uom_conversion_qty
            FROM purchase_order_items poi
            WHERE poi.purchase_order_id = $1
        """
        
        items_rows = await conn.fetch(items_query, po_id)

        # Format the response
        po_data = dict(po_row)
        po_data['items'] = [dict(item) for item in items_rows]

        # Parse JSONB charges field if present (asyncpg returns it as JSON string)
        if po_data.get('charges'):
            import json
            try:
                if isinstance(po_data['charges'], str):
                    po_data['charges'] = json.loads(po_data['charges'])
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Failed to parse charges for PO {po_id}")
                po_data['charges'] = []
        else:
            po_data['charges'] = []

        return po_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching purchase order details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/purchase-orders")
async def get_purchase_orders(
    status: Optional[str] = Query(None, pattern="^(pending|partial|received|cancelled)$"),
    supplier_id: Optional[UUID] = None,
    store_id: Optional[UUID] = Query(None, description="Store UUID"),
    x_store_id: Optional[str] = Header(None, alias="X-Store-ID"),
    limit: int = Query(50, ge=1, le=200),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get list of purchase orders for a specific store"""
    try:
        # Determine which store_id to use (query param takes precedence over header)
        effective_store_id = store_id
        if not effective_store_id and x_store_id:
            try:
                effective_store_id = UUID(x_store_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid X-Store-ID header format")

        conn = service.db
        query = """
            SELECT
                po.id,
                po.po_number,
                po.supplier_id,
                s.name as supplier_name,
                po.order_date,
                po.expected_date,
                po.received_date,
                po.status,
                po.total_amount,
                po.subtotal,
                po.tax_amount,
                po.notes,
                po.charges,
                po.paid,
                po.created_by,
                po.received_by,
                po.approved_by,
                COUNT(poi.id) as item_count
            FROM purchase_orders po
            JOIN provincial_suppliers s ON po.supplier_id = s.id
            LEFT JOIN purchase_order_items poi ON po.id = poi.purchase_order_id
            WHERE 1=1
        """

        params = []
        param_count = 0

        # Filter by store_id if provided
        if effective_store_id:
            param_count += 1
            query += f" AND po.store_id = ${param_count}"
            params.append(effective_store_id)

        if status:
            param_count += 1
            query += f" AND po.status = ${param_count}"
            params.append(status)

        if supplier_id:
            param_count += 1
            query += f" AND po.supplier_id = ${param_count}"
            params.append(supplier_id)
        
        query += f"""
            GROUP BY po.id, po.po_number, po.supplier_id, s.name,
                     po.order_date, po.expected_date, po.received_date,
                     po.status, po.total_amount, po.subtotal, po.tax_amount, po.notes,
                     po.charges, po.paid, po.created_by, po.received_by, po.approved_by
            ORDER BY po.order_date DESC
            LIMIT ${param_count + 1}
        """
        params.append(limit)
        
        results = await conn.fetch(query, *params)

        # Parse JSONB charges field for each PO (asyncpg returns it as JSON string)
        import json
        purchase_orders = []
        for row in results:
            po_dict = dict(row)
            if po_dict.get('charges'):
                try:
                    if isinstance(po_dict['charges'], str):
                        po_dict['charges'] = json.loads(po_dict['charges'])
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Failed to parse charges for PO {po_dict.get('id')}")
                    po_dict['charges'] = []
            else:
                po_dict['charges'] = []
            purchase_orders.append(po_dict)

        return {
            "count": len(results),
            "purchase_orders": purchase_orders
        }
    except Exception as e:
        logger.error(f"Error getting purchase orders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/purchase-orders/{po_id}/status")
async def update_purchase_order_status(
    po_id: UUID,
    status: str = Query(..., pattern="^(pending|partial|received|cancelled)$"),
    service: InventoryService = Depends(get_inventory_service)
):
    """Update purchase order status (approve, cancel, etc.)"""
    try:
        conn = service.db
        
        # If changing to 'received', trigger inventory update
        if status == 'received':
            # Get all items from the purchase order including GTIN fields
            items_query = """
                SELECT
                    sku,
                    batch_lot,
                    quantity_ordered,
                    unit_cost,
                    case_gtin,
                    packaged_on_date,
                    gtin_barcode,
                    each_gtin
                FROM purchase_order_items
                WHERE purchase_order_id = $1
            """
            
            items = await conn.fetch(items_query, po_id)
            
            if items:
                # Prepare items for receive function
                received_items = [
                    {
                        'sku': item['sku'],
                        'quantity_received': item['quantity_ordered'],  # Use ordered quantity as received
                        'unit_cost': float(item['unit_cost']),
                        'batch_lot': item['batch_lot'],
                        'case_gtin': item.get('case_gtin'),
                        'packaged_on_date': item.get('packaged_on_date'),
                        'gtin_barcode': item.get('gtin_barcode'),
                        'each_gtin': item.get('each_gtin')
                    }
                    for item in items
                ]
                
                # Call the receive_purchase_order function to update inventory
                success = await service.receive_purchase_order(po_id, received_items)
                
                if not success:
                    raise HTTPException(
                        status_code=400,
                        detail="Failed to update inventory for received items"
                    )
                
                # Get the updated PO info
                result_query = """
                    SELECT id, po_number, status 
                    FROM purchase_orders 
                    WHERE id = $1
                """
                result = await conn.fetchrow(result_query, po_id)
                
                return {
                    "success": True,
                    "message": f"Purchase order {result['po_number']} received and inventory updated",
                    "po_id": str(result['id']),
                    "po_number": result['po_number'],
                    "new_status": result['status'],
                    "items_received": len(items)
                }
        else:
            # For cancelled status, append '-cancelled' to PO number if not already present
            if status == 'cancelled':
                # First check current PO number
                check_query = """
                    SELECT po_number FROM purchase_orders WHERE id = $1
                """
                current_po = await conn.fetchrow(check_query, po_id)

                if current_po and not current_po['po_number'].endswith('-cancelled'):
                    # Update both status and PO number
                    query = """
                        UPDATE purchase_orders
                        SET status = $1,
                            po_number = po_number || '-cancelled',
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = $2
                        RETURNING id, po_number, status
                    """
                else:
                    # Just update status if already has '-cancelled' suffix
                    query = """
                        UPDATE purchase_orders
                        SET status = $1,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = $2
                        RETURNING id, po_number, status
                    """
            else:
                # For other status changes, just update the status
                query = """
                    UPDATE purchase_orders
                    SET status = $1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $2
                    RETURNING id, po_number, status
                """

            result = await conn.fetchrow(query, status, po_id)

            if not result:
                raise HTTPException(status_code=404, detail=f"Purchase order {po_id} not found")
            
            return {
                "success": True,
                "message": f"Purchase order {result['po_number']} status updated to {status}",
                "po_id": str(result['id']),
                "po_number": result['po_number'],
                "new_status": result['status']
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating purchase order status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Store for tracking imported ASN files (in production, use database)
imported_asn_files = set()


@router.post("/asn/check-duplicate")
async def check_asn_duplicate(
    filename: str = Query(..., description="ASN filename to check")
):
    """Check if an ASN file has already been imported"""
    try:
        is_duplicate = filename in imported_asn_files
        return {
            "filename": filename,
            "is_duplicate": is_duplicate,
            "message": f"File '{filename}' {'has already been imported' if is_duplicate else 'has not been imported'}"
        }
    except Exception as e:
        logger.error(f"Error checking ASN duplicate: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/asn/mark-imported")
async def mark_asn_imported(
    filename: str = Query(..., description="ASN filename to mark as imported")
):
    """Mark an ASN file as imported"""
    try:
        imported_asn_files.add(filename)
        return {
            "success": True,
            "filename": filename,
            "message": f"File '{filename}' marked as imported"
        }
    except Exception as e:
        logger.error(f"Error marking ASN as imported: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{sku}/image")
async def get_product_image(
    sku: str,
    service: InventoryService = Depends(get_inventory_service)
):
    """Get product image URL from product catalog"""
    try:
        conn = service.db
        # First try exact match with case-insensitive comparison
        query = """
            SELECT 
                pc.product_name,
                pc.image_url,
                pc.category,
                pc.brand,
                pc.unit_price as retail_price
            FROM ocs_product_catalog pc
            WHERE LOWER(TRIM(pc.ocs_variant_number)) = LOWER(TRIM($1))
            LIMIT 1
        """
        
        result = await conn.fetchrow(query, sku)
        
        # If no match, try with normalized SKU (replace underscores)
        if not result:
            # Normalize the SKU - convert to lowercase and standardize format
            normalized_sku = sku.lower().replace('_', '')
            query_normalized = """
                SELECT 
                    pc.product_name,
                    pc.image_url,
                    pc.category,
                    pc.brand,
                    pc.unit_price as retail_price
                FROM ocs_product_catalog pc
                WHERE LOWER(REPLACE(pc.ocs_variant_number, '_', '')) = $1
                LIMIT 1
            """
            result = await conn.fetchrow(query_normalized, normalized_sku)
        
        if not result:
            # Return default placeholder if product not found
            return {
                "sku": sku,
                "product_name": "Unknown Product",
                "image_url": None,
                "category": None,
                "brand": None,
                "retail_price": None
            }
        
        return dict(result)
    except Exception as e:
        logger.error(f"Error getting product image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))