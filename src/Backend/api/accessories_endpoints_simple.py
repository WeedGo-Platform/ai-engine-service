"""
Simple Accessories Management API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import psycopg2
from datetime import datetime

# Use simple lookup service
from services.barcode_lookup_simple import get_simple_lookup

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/accessories", tags=["Accessories"])

# Database config
DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'ai_engine',
    'user': 'weedgo',
    'password': 'weedgo123'
}

# Request/Response Models
class BarcodeScanRequest(BaseModel):
    barcode: str
    store_id: Optional[str] = "store-001"

class BarcodeScanResponse(BaseModel):
    found: bool
    source: str
    confidence: float
    data: Dict[str, Any]
    requires_manual_entry: bool
    message: Optional[str] = None

@router.post("/barcode/scan", response_model=BarcodeScanResponse)
async def scan_barcode(request: BarcodeScanRequest):
    """Scan a barcode and retrieve product information"""
    try:
        lookup_service = get_simple_lookup()
        result = await lookup_service.lookup_barcode(
            request.barcode,
            request.store_id
        )
        
        return BarcodeScanResponse(**result)
        
    except Exception as e:
        logger.error(f"Barcode scan error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/inventory")
async def get_inventory(
    store_id: str = Query("store-001"),
    category_id: Optional[int] = None
):
    """Get accessories inventory"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        query = """
            SELECT 
                ai.id, ac.barcode, ac.sku, ac.name, ac.brand,
                ai.quantity, ai.retail_price, cat.name as category
            FROM accessories_inventory ai
            JOIN accessories_catalog ac ON ai.accessory_id = ac.id
            LEFT JOIN accessory_categories cat ON ac.category_id = cat.id
            WHERE ai.store_id = %s
        """
        params = [store_id]
        
        if category_id:
            query += " AND ac.category_id = %s"
            params.append(category_id)
            
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        items = []
        for row in rows:
            items.append({
                'id': row[0],
                'barcode': row[1],
                'sku': row[2],
                'name': row[3],
                'brand': row[4],
                'quantity': row[5],
                'price': float(row[6]) if row[6] else 0,
                'category': row[7]
            })
        
        cursor.close()
        conn.close()
        
        return {
            'store_id': store_id,
            'total_items': len(items),
            'items': items
        }
        
    except Exception as e:
        logger.error(f"Inventory fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories")
async def get_categories():
    """Get all accessory categories"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, slug, icon, sort_order, description, is_active
            FROM accessory_categories
            ORDER BY sort_order, name
        """)
        
        rows = cursor.fetchall()
        categories = []
        
        for row in rows:
            categories.append({
                'id': row[0],
                'name': row[1],
                'slug': row[2],
                'icon': row[3],
                'sort_order': row[4],
                'description': row[5],
                'is_active': row[6]
            })
        
        cursor.close()
        conn.close()
        
        return categories
        
    except Exception as e:
        logger.error(f"Categories fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/categories")
async def create_category(
    name: str = Body(...),
    slug: str = Body(...),
    icon: str = Body(''),
    description: str = Body(''),
    sort_order: int = Body(0),
    is_active: bool = Body(True)
):
    """Create a new accessory category"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO accessory_categories (name, slug, icon, description, sort_order, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, name, slug, icon, description, sort_order, is_active
        """, (name, slug, icon, description, sort_order, is_active))
        
        row = cursor.fetchone()
        conn.commit()
        
        category = {
            'id': row[0],
            'name': row[1],
            'slug': row[2],
            'icon': row[3],
            'description': row[4],
            'sort_order': row[5],
            'is_active': row[6]
        }
        
        cursor.close()
        conn.close()
        
        logger.info(f"Created category: {name}")
        return category
        
    except Exception as e:
        logger.error(f"Category creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/categories/{category_id}")
async def update_category(
    category_id: int,
    name: str = Body(...),
    slug: str = Body(...),
    icon: str = Body(''),
    description: str = Body(''),
    sort_order: int = Body(0),
    is_active: bool = Body(True)
):
    """Update an existing accessory category"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE accessory_categories
            SET name = %s, slug = %s, icon = %s, description = %s, sort_order = %s, is_active = %s
            WHERE id = %s
            RETURNING id, name, slug, icon, description, sort_order, is_active
        """, (name, slug, icon, description, sort_order, is_active, category_id))
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Category not found")
        
        conn.commit()
        
        category = {
            'id': row[0],
            'name': row[1],
            'slug': row[2],
            'icon': row[3],
            'description': row[4],
            'sort_order': row[5],
            'is_active': row[6]
        }
        
        cursor.close()
        conn.close()
        
        logger.info(f"Updated category {category_id}: {name}")
        return category
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Category update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/categories/{category_id}")
async def delete_category(category_id: int):
    """Delete an accessory category"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check if category is in use
        cursor.execute("""
            SELECT COUNT(*) FROM accessories_catalog WHERE category_id = %s
        """, (category_id,))
        
        count = cursor.fetchone()[0]
        if count > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot delete category: {count} products are using this category"
            )
        
        # Delete category
        cursor.execute("""
            DELETE FROM accessory_categories WHERE id = %s RETURNING id
        """, (category_id,))
        
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Category not found")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Deleted category {category_id}")
        return {"success": True, "message": "Category deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Category deletion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))