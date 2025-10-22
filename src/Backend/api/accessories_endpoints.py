"""
Accessories and Paraphernalia API Endpoints
Handles barcode scanning, inventory management, and catalog operations
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import json
import base64
from decimal import Decimal

from services.barcode_lookup_service import get_lookup_service
from database.connection import get_db_connection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/accessories", tags=["accessories"])


# ============= Pydantic Models =============

class AccessoryCategory(BaseModel):
    """Category model for accessories"""
    id: Optional[int]
    name: str
    slug: str
    parent_id: Optional[int] = None
    description: Optional[str]
    icon: Optional[str]
    sort_order: int = 0
    is_active: bool = True


class AccessoryBase(BaseModel):
    """Base accessory model"""
    barcode: Optional[str]
    upc: Optional[str]
    sku: str
    name: str
    brand: Optional[str]
    category_id: Optional[int]
    subcategory: Optional[str] = None
    description: Optional[str]
    image_url: Optional[str]
    specifications: Optional[Dict[str, Any]] = {}
    materials: Optional[List[str]] = []
    dimensions: Optional[Dict[str, float]] = {}
    msrp: Optional[float]
    tags: Optional[List[str]] = []


class AccessoryInventory(BaseModel):
    """Inventory model for accessories"""
    store_id: str
    accessory_id: int
    quantity: int = 0
    cost_price: float
    retail_price: float
    sale_price: Optional[float]
    min_stock_level: int = 5
    max_stock_level: int = 100
    reorder_point: int = 10
    location: Optional[str]
    status: str = "active"


class BarcodeScanRequest(BaseModel):
    """Request model for barcode scanning"""
    barcode: str
    store_id: str
    scan_type: str = "intake"  # intake, sale, inventory_check


class BarcodeScanResponse(BaseModel):
    """Response model for barcode scan"""
    found: bool
    source: str  # cache, database, web, ocr, manual
    confidence: float
    data: Optional[Dict[str, Any]]
    requires_manual_entry: bool = False
    suggested_category: Optional[str]
    suggested_price: Optional[float]


class AccessoryIntakeRequest(BaseModel):
    """Request for adding accessory to inventory"""
    barcode: Optional[str]
    store_id: str
    name: str
    brand: Optional[str]
    category_id: Optional[int]
    subcategory: Optional[str] = None
    quantity: int
    cost_price: float
    retail_price: float
    supplier_id: Optional[int]
    image_url: Optional[str]
    description: Optional[str]
    location: Optional[str] = None  # Storage location (e.g., "Shelf A1", "Back Room")
    auto_create_catalog: bool = True


class InventoryAdjustment(BaseModel):
    """Inventory adjustment model"""
    store_id: str
    accessory_id: int
    adjustment_type: str  # add, remove, set, damage, loss
    quantity: int
    reason: Optional[str]
    notes: Optional[str]


class OCRRequest(BaseModel):
    """OCR extraction request"""
    image_data: str  # Base64 encoded image
    store_id: str
    document_type: str = "receipt"  # receipt, invoice, label


# ============= Barcode Scanning Endpoints =============

@router.post("/barcode/scan", response_model=BarcodeScanResponse)
async def scan_barcode(request: BarcodeScanRequest):
    """
    Scan a barcode and retrieve product information
    Uses multi-tier lookup: Cache → DB → Web → OCR
    """
    try:
        async with get_lookup_service() as lookup_service:
            result = await lookup_service.lookup_barcode(
                request.barcode,
                request.store_id
            )
            
            return BarcodeScanResponse(
                found=result.get('source') != 'not_found',
                source=result.get('source', 'unknown'),
                confidence=result.get('confidence', 0),
                data=result,
                requires_manual_entry=result.get('requires_manual_entry', False),
                suggested_category=result.get('category'),
                suggested_price=result.get('price')
            )
            
    except Exception as e:
        logger.error(f"Barcode scan error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/barcode/batch-scan")
async def batch_scan_barcodes(
    barcodes: List[str],
    store_id: str = Query(..., description="Store ID")
):
    """
    Scan multiple barcodes at once (for bulk intake)
    """
    results = []
    
    async with get_lookup_service() as lookup_service:
        for barcode in barcodes:
            try:
                result = await lookup_service.lookup_barcode(barcode, store_id)
                results.append({
                    'barcode': barcode,
                    'success': True,
                    'data': result
                })
            except Exception as e:
                results.append({
                    'barcode': barcode,
                    'success': False,
                    'error': str(e)
                })
    
    return {'results': results, 'total': len(barcodes)}


@router.post("/ocr/extract")
async def extract_from_image(request: OCRRequest):
    """
    Extract product information from image using OCR
    Used when barcode scan fails or for invoice processing
    """
    try:
        async with get_lookup_service() as lookup_service:
            result = await lookup_service.ocr_extract(
                request.image_data,
                request.store_id
            )
            
            return {
                'success': result.get('confidence', 0) > 0,
                'extracted_data': result,
                'confidence': result.get('confidence', 0),
                'requires_review': result.get('confidence', 0) < 0.8
            }
            
    except Exception as e:
        logger.error(f"OCR extraction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= Catalog Management Endpoints =============

@router.get("/catalog")
async def get_accessories_catalog(
    category_id: Optional[int] = None,
    brand: Optional[str] = None,
    search: Optional[str] = None,
    verified_only: bool = False,
    skip: int = 0,
    limit: int = 50
):
    """
    Get accessories from catalog with filtering
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            SELECT 
                a.id, a.barcode, a.sku, a.name, a.brand,
                a.description, a.image_url, a.msrp,
                a.specifications, a.verified, a.confidence_score,
                c.name as category_name
            FROM accessories_catalog a
            LEFT JOIN accessory_categories c ON a.category_id = c.id
            WHERE 1=1
        """
        params = []
        
        if category_id:
            query += " AND a.category_id = %s"
            params.append(category_id)
        
        if brand:
            query += " AND a.brand ILIKE %s"
            params.append(f"%{brand}%")
        
        if search:
            query += " AND (a.search_vector @@ plainto_tsquery('english', %s) OR a.name ILIKE %s)"
            params.extend([search, f"%{search}%"])
        
        if verified_only:
            query += " AND a.verified = true"
        
        query += " ORDER BY a.name LIMIT %s OFFSET %s"
        params.extend([limit, skip])
        
        cursor.execute(query, params)
        
        accessories = []
        for row in cursor.fetchall():
            accessories.append({
                'id': row[0],
                'barcode': row[1],
                'sku': row[2],
                'name': row[3],
                'brand': row[4],
                'description': row[5],
                'image_url': row[6],
                'msrp': float(row[7]) if row[7] else None,
                'specifications': row[8],
                'verified': row[9],
                'confidence_score': float(row[10]) if row[10] else None,
                'category': row[11]
            })
        
        return {
            'accessories': accessories,
            'total': len(accessories),
            'skip': skip,
            'limit': limit
        }
        
    finally:
        cursor.close()
        conn.close()


@router.post("/catalog")
async def add_to_catalog(accessory: AccessoryBase):
    """
    Add a new accessory to the catalog
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO accessories_catalog 
            (barcode, upc, sku, name, brand, category_id, subcategory, description,
             image_url, specifications, materials, dimensions, msrp, tags)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            accessory.barcode,
            accessory.upc,
            accessory.sku,
            accessory.name,
            accessory.brand,
            accessory.category_id,
            accessory.subcategory,
            accessory.description,
            accessory.image_url,
            json.dumps(accessory.specifications),
            accessory.materials,
            json.dumps(accessory.dimensions) if accessory.dimensions else None,
            accessory.msrp,
            accessory.tags
        ))
        
        accessory_id = cursor.fetchone()[0]
        conn.commit()
        
        return {
            'id': accessory_id,
            'message': 'Accessory added to catalog successfully'
        }
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding to catalog: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@router.put("/catalog/{accessory_id}")
async def update_catalog_item(accessory_id: int, accessory: AccessoryBase):
    """
    Update an accessory in the catalog
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE accessories_catalog SET
                barcode = %s, upc = %s, sku = %s, name = %s,
                brand = %s, category_id = %s, subcategory = %s, description = %s,
                image_url = %s, specifications = %s, materials = %s,
                dimensions = %s, msrp = %s, tags = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (
            accessory.barcode, accessory.upc, accessory.sku, accessory.name,
            accessory.brand, accessory.category_id, accessory.subcategory, accessory.description,
            accessory.image_url, json.dumps(accessory.specifications),
            accessory.materials,
            json.dumps(accessory.dimensions) if accessory.dimensions else None,
            accessory.msrp, accessory.tags, accessory_id
        ))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Accessory not found")
        
        conn.commit()
        return {'message': 'Accessory updated successfully'}
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating catalog: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


# ============= Inventory Management Endpoints =============

@router.post("/inventory/intake")
async def intake_accessory(request: AccessoryIntakeRequest):
    """
    Add accessories to inventory (receiving shipment)
    Creates catalog entry if needed
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if accessory exists in catalog
        accessory_id = None
        
        if request.barcode:
            cursor.execute(
                "SELECT id FROM accessories_catalog WHERE barcode = %s",
                (request.barcode,)
            )
            result = cursor.fetchone()
            if result:
                accessory_id = result[0]
        
        # Create catalog entry if needed
        if not accessory_id and request.auto_create_catalog:
            cursor.execute("""
                INSERT INTO accessories_catalog 
                (barcode, sku, name, brand, category_id, subcategory, description, image_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                request.barcode,
                f"ACC-{request.barcode[-8:]}" if request.barcode else f"ACC-{datetime.now().timestamp()}",
                request.name,
                request.brand,
                request.category_id,
                request.subcategory,
                request.description,
                request.image_url
            ))
            accessory_id = cursor.fetchone()[0]
        
        if not accessory_id:
            raise HTTPException(status_code=400, detail="Accessory not found in catalog")
        
        # Add to inventory
        cursor.execute("""
            INSERT INTO accessories_inventory
            (store_id, accessory_id, quantity, cost_price, retail_price, location)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (store_id, accessory_id) DO UPDATE SET
                quantity = accessories_inventory.quantity + EXCLUDED.quantity,
                cost_price = EXCLUDED.cost_price,
                retail_price = EXCLUDED.retail_price,
                location = COALESCE(EXCLUDED.location, accessories_inventory.location),
                last_restocked = CURRENT_TIMESTAMP
            RETURNING id, quantity
        """, (
            request.store_id,
            accessory_id,
            request.quantity,
            request.cost_price,
            request.retail_price,
            request.location
        ))
        
        inventory_id, new_quantity = cursor.fetchone()
        
        # Record movement
        cursor.execute("""
            INSERT INTO accessories_movements 
            (store_id, accessory_id, movement_type, quantity, unit_cost,
             reference_type, reason, quantity_after)
            VALUES (%s, %s, 'purchase', %s, %s, 'intake', 'Inventory intake', %s)
        """, (
            request.store_id,
            accessory_id,
            request.quantity,
            request.cost_price,
            new_quantity
        ))
        
        conn.commit()
        
        return {
            'success': True,
            'accessory_id': accessory_id,
            'inventory_id': inventory_id,
            'new_quantity': new_quantity,
            'message': f'Added {request.quantity} units to inventory'
        }
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Intake error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@router.get("/inventory/{store_id}")
async def get_store_inventory(
    store_id: str,
    category_id: Optional[int] = None,
    low_stock_only: bool = False,
    skip: int = 0,
    limit: int = 50
):
    """
    Get accessory inventory for a specific store
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            SELECT 
                i.id, i.accessory_id, a.name, a.brand, a.sku,
                a.barcode, a.image_url, c.name as category,
                i.quantity, i.reserved_quantity, i.available_quantity,
                i.cost_price, i.retail_price, i.sale_price,
                i.min_stock_level, i.status, i.location
            FROM accessories_inventory i
            JOIN accessories_catalog a ON i.accessory_id = a.id
            LEFT JOIN accessory_categories c ON a.category_id = c.id
            WHERE i.store_id = %s
        """
        params = [store_id]
        
        if category_id:
            query += " AND a.category_id = %s"
            params.append(category_id)
        
        if low_stock_only:
            query += " AND i.quantity <= i.min_stock_level"
        
        query += " ORDER BY a.name LIMIT %s OFFSET %s"
        params.extend([limit, skip])
        
        cursor.execute(query, params)
        
        inventory = []
        for row in cursor.fetchall():
            inventory.append({
                'id': row[0],
                'accessory_id': row[1],
                'name': row[2],
                'brand': row[3],
                'sku': row[4],
                'barcode': row[5],
                'image_url': row[6],
                'category': row[7],
                'quantity': row[8],
                'reserved': row[9],
                'available': row[10],
                'cost_price': float(row[11]) if row[11] else None,
                'retail_price': float(row[12]) if row[12] else None,
                'sale_price': float(row[13]) if row[13] else None,
                'min_stock': row[14],
                'status': row[15],
                'location': row[16]
            })
        
        return {
            'inventory': inventory,
            'total': len(inventory),
            'store_id': store_id
        }
        
    finally:
        cursor.close()
        conn.close()


@router.post("/inventory/adjust")
async def adjust_inventory(adjustment: InventoryAdjustment):
    """
    Adjust inventory levels (damage, loss, correction)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get current quantity
        cursor.execute("""
            SELECT quantity FROM accessories_inventory 
            WHERE store_id = %s AND accessory_id = %s
        """, (adjustment.store_id, adjustment.accessory_id))
        
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        
        current_qty = result[0]
        
        # Calculate new quantity
        if adjustment.adjustment_type == 'set':
            new_qty = adjustment.quantity
        elif adjustment.adjustment_type == 'add':
            new_qty = current_qty + adjustment.quantity
        elif adjustment.adjustment_type in ['remove', 'damage', 'loss']:
            new_qty = max(0, current_qty - adjustment.quantity)
        else:
            raise HTTPException(status_code=400, detail="Invalid adjustment type")
        
        # Update inventory
        cursor.execute("""
            UPDATE accessories_inventory 
            SET quantity = %s, updated_at = CURRENT_TIMESTAMP
            WHERE store_id = %s AND accessory_id = %s
        """, (new_qty, adjustment.store_id, adjustment.accessory_id))
        
        # Record movement
        cursor.execute("""
            INSERT INTO accessories_movements 
            (store_id, accessory_id, movement_type, quantity,
             reason, notes, quantity_before, quantity_after)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            adjustment.store_id,
            adjustment.accessory_id,
            adjustment.adjustment_type,
            adjustment.quantity if adjustment.adjustment_type != 'set' else new_qty - current_qty,
            adjustment.reason,
            adjustment.notes,
            current_qty,
            new_qty
        ))
        
        conn.commit()
        
        return {
            'success': True,
            'previous_quantity': current_qty,
            'new_quantity': new_qty,
            'adjustment': adjustment.quantity
        }
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Adjustment error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


# ============= Categories Management =============

@router.get("/categories")
async def get_categories():
    """
    Get all accessory categories
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, name, slug, parent_category_id, description,
                   icon, sort_order, is_active
            FROM accessory_categories
            WHERE is_active = true
            ORDER BY sort_order, name
        """)
        
        categories = []
        for row in cursor.fetchall():
            categories.append({
                'id': row[0],
                'name': row[1],
                'slug': row[2],
                'parent_id': row[3],
                'description': row[4],
                'icon': row[5],
                'sort_order': row[6],
                'is_active': row[7]
            })
        
        return categories
        
    finally:
        cursor.close()
        conn.close()


@router.post("/categories")
async def create_category(category: AccessoryCategory):
    """
    Create a new accessory category
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO accessory_categories
            (name, slug, parent_category_id, description, icon, sort_order, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            category.name, category.slug, category.parent_id,
            category.description, category.icon,
            category.sort_order, category.is_active
        ))
        
        category_id = cursor.fetchone()[0]
        conn.commit()
        
        return {
            'id': category_id,
            'message': 'Category created successfully'
        }
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating category: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


# ============= Reports and Analytics =============

@router.get("/reports/low-stock/{store_id}")
async def get_low_stock_report(store_id: str):
    """
    Get accessories that are low in stock
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                a.name, a.sku, a.barcode,
                i.quantity, i.min_stock_level, i.reorder_point,
                i.quantity - i.min_stock_level as shortage,
                c.name as category
            FROM accessories_inventory i
            JOIN accessories_catalog a ON i.accessory_id = a.id
            LEFT JOIN accessory_categories c ON a.category_id = c.id
            WHERE i.store_id = %s 
            AND i.quantity <= i.reorder_point
            ORDER BY shortage
        """, (store_id,))
        
        low_stock = []
        for row in cursor.fetchall():
            low_stock.append({
                'name': row[0],
                'sku': row[1],
                'barcode': row[2],
                'current_stock': row[3],
                'min_stock': row[4],
                'reorder_point': row[5],
                'shortage': abs(row[6]),
                'category': row[7]
            })
        
        return {
            'store_id': store_id,
            'low_stock_items': low_stock,
            'total_items': len(low_stock)
        }
        
    finally:
        cursor.close()
        conn.close()


@router.get("/reports/inventory-value/{store_id}")
async def get_inventory_value(store_id: str):
    """
    Calculate total inventory value for accessories
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                SUM(i.quantity * i.cost_price) as total_cost,
                SUM(i.quantity * i.retail_price) as total_retail,
                SUM(i.quantity * COALESCE(i.sale_price, i.retail_price)) as total_sale,
                COUNT(DISTINCT i.accessory_id) as unique_items,
                SUM(i.quantity) as total_units
            FROM accessories_inventory i
            WHERE i.store_id = %s AND i.status = 'active'
        """, (store_id,))
        
        row = cursor.fetchone()
        
        return {
            'store_id': store_id,
            'total_cost_value': float(row[0]) if row[0] else 0,
            'total_retail_value': float(row[1]) if row[1] else 0,
            'total_sale_value': float(row[2]) if row[2] else 0,
            'potential_profit': float(row[1] - row[0]) if row[0] and row[1] else 0,
            'unique_items': row[3] or 0,
            'total_units': row[4] or 0
        }
        
    finally:
        cursor.close()
        conn.close()