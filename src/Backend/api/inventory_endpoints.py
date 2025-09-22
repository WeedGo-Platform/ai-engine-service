"""
Inventory Management API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Header
from typing import List, Dict, Optional, Any
from datetime import date
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field
import logging

from services.inventory_service import InventoryService
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
            password=os.getenv('DB_PASSWORD', 'your_password_here'),
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
    shipped_qty: int = Field(gt=0)  # Required
    uom: str  # Required
    uom_conversion: float = Field(gt=0)  # Required
    uom_conversion_qty: float = Field(gt=0)  # Required


class CreatePurchaseOrderRequest(BaseModel):
    supplier_id: UUID
    items: List[PurchaseOrderItem]
    expected_date: date  # Required
    notes: Optional[str] = None  # Optional
    excel_filename: str  # Required for PO number generation
    store_id: Optional[UUID] = None  # Can be provided in body or header
    shipment_id: Optional[str] = None  # From ASN Excel
    container_id: Optional[str] = None  # From ASN Excel
    vendor: Optional[str] = None  # From ASN Excel
    ocs_order_number: Optional[str] = None  # Extracted from filename
    tenant_id: Optional[UUID] = None  # From store/context
    created_by: Optional[UUID] = None  # User ID from context


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
    x_store_id: Optional[str] = Header(None, alias="X-Store-ID"),
    service: InventoryService = Depends(get_inventory_service)
):
    """Create a new purchase order"""
    try:
        # Get store_id from request body or header
        store_id = request.store_id
        if not store_id and x_store_id and x_store_id.strip():
            try:
                store_id = UUID(x_store_id.strip())
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid store ID in header")

        if not store_id:
            raise HTTPException(status_code=400, detail="Store ID is required - please select a store")
        
        po_id = await service.create_purchase_order(
            supplier_id=request.supplier_id,
            items=[item.dict() for item in request.items],
            expected_date=request.expected_date,
            notes=request.notes,
            excel_filename=request.excel_filename,
            store_id=store_id,
            shipment_id=request.shipment_id,
            container_id=request.container_id,
            vendor=request.vendor,
            ocs_order_number=request.ocs_order_number,
            tenant_id=request.tenant_id,
            created_by=request.created_by
        )
        
        return {
            "success": True,
            "purchase_order_id": str(po_id),
            "message": f"Purchase order created with {len(request.items)} items"
        }
    except Exception as e:
        logger.error(f"Error creating purchase order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/purchase-orders/{po_id}/receive")
async def receive_purchase_order(
    po_id: UUID,
    request: ReceivePurchaseOrderRequest,
    service: InventoryService = Depends(get_inventory_service)
):
    """Process receipt of purchase order items"""
    try:
        success = await service.receive_purchase_order(
            po_id,
            [item.dict() for item in request.items]
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to receive purchase order"
            )
        
        return {
            "success": True,
            "message": f"Received {len(request.items)} items for PO {po_id}"
        }
    except Exception as e:
        logger.error(f"Error receiving purchase order: {str(e)}")
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
                pc.product_name,
                s.name as supplier_name
            FROM batch_tracking bt
            LEFT JOIN product_catalog pc ON bt.sku = pc.sku
            LEFT JOIN provincial_suppliers s ON bt.supplier_id = s.id
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
                po.notes,
                po.shipment_id,
                po.container_id,
                po.vendor
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
                poi.quantity_ordered,
                poi.quantity_received,
                poi.unit_cost,
                poi.line_total as total_cost,
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
                poi.uom_conversion_qty,
                opc.product_name as product_name
            FROM purchase_order_items poi
            LEFT JOIN ocs_product_catalog opc ON poi.sku = opc.ocs_variant_number
            WHERE poi.purchase_order_id = $1
        """
        
        items_rows = await conn.fetch(items_query, po_id)
        
        # Format the response
        po_data = dict(po_row)
        po_data['items'] = [dict(item) for item in items_rows]
        
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
                po.notes,
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
                     po.status, po.total_amount, po.notes
            ORDER BY po.order_date DESC
            LIMIT ${param_count + 1}
        """
        params.append(limit)
        
        results = await conn.fetch(query, *params)
        
        return {
            "count": len(results),
            "purchase_orders": [dict(row) for row in results]
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