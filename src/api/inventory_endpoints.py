"""
Inventory Management API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query
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
    batch_lot: Optional[str] = None
    expiry_date: Optional[date] = None


class CreatePurchaseOrderRequest(BaseModel):
    supplier_id: UUID
    items: List[PurchaseOrderItem]
    expected_date: Optional[date] = None
    notes: Optional[str] = None


class ReceivePurchaseOrderItem(BaseModel):
    sku: str
    quantity_received: int = Field(ge=0)
    unit_cost: float = Field(gt=0)
    batch_lot: Optional[str] = None
    expiry_date: Optional[date] = None


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
    service: InventoryService = Depends(get_inventory_service)
):
    """Create a new purchase order"""
    try:
        po_id = await service.create_purchase_order(
            request.supplier_id,
            [item.dict() for item in request.items],
            request.expected_date,
            request.notes
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
            FROM suppliers
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


@router.get("/purchase-orders")
async def get_purchase_orders(
    status: Optional[str] = Query(None, pattern="^(pending|partial|received|cancelled)$"),
    supplier_id: Optional[UUID] = None,
    limit: int = Query(50, ge=1, le=200),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get list of purchase orders"""
    try:
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
            JOIN suppliers s ON po.supplier_id = s.id
            LEFT JOIN purchase_order_items poi ON po.id = poi.purchase_order_id
            WHERE 1=1
        """
        
        params = []
        param_count = 0
        
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