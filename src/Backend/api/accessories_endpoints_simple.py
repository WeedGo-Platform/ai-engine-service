"""
Simple Accessories Management API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query
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
            SELECT id, name, slug, icon, sort_order
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
                'sort_order': row[4]
            })
        
        cursor.close()
        conn.close()
        
        return categories
        
    except Exception as e:
        logger.error(f"Categories fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))