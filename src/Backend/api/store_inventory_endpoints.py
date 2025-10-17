"""
Store-Aware Inventory API Endpoints
Handles multi-tenant inventory operations with store context
Follows SOLID principles and clean architecture patterns
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Header, Body
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date
from pydantic import BaseModel, Field
from decimal import Decimal
import logging

import asyncpg
import os

from services.store_inventory_service import (
    StoreInventoryService,
    TransactionType,
    create_store_inventory_service
)

logger = logging.getLogger(__name__)

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
            min_size=10,
            max_size=20
        )
    return db_pool

async def get_current_store(x_store_id: Optional[str] = Header(None)):
    """Get current store from header"""
    if not x_store_id:
        raise HTTPException(status_code=400, detail="X-Store-ID header is required")
    return {"id": x_store_id}

# =====================================================
# Router Configuration
# =====================================================

router = APIRouter(
    prefix="/api/store-inventory",
    tags=["store-inventory"],
    responses={
        404: {"description": "Not found"},
        403: {"description": "Forbidden - Store access denied"},
        400: {"description": "Bad request"},
    }
)

# =====================================================
# Request/Response Models
# =====================================================

class InventoryUpdateRequest(BaseModel):
    """Request model for inventory updates"""
    sku: str
    quantity_change: int
    transaction_type: str
    reference_id: Optional[UUID] = None
    notes: Optional[str] = None
    batch_lot: Optional[str] = None


class PurchaseOrderItemRequest(BaseModel):
    """Request model for purchase order items"""
    sku: str
    quantity: int = Field(gt=0)
    unit_cost: Decimal = Field(ge=0)
    batch_lot: str  # Required
    case_gtin: str  # Required
    gtin_barcode: str  # Required
    each_gtin: str  # Required
    vendor: str  # Required
    brand: str  # Required
    packaged_on_date: date  # Required
    shipped_qty: int  # Required
    uom: str  # Required
    uom_conversion: float  # Required
    uom_conversion_qty: float  # Required
    notes: Optional[str] = None  # Optional


class CreatePurchaseOrderRequest(BaseModel):
    """Request model for creating purchase orders"""
    supplier_id: UUID
    items: List[PurchaseOrderItemRequest]
    expected_date: date  # Required
    notes: Optional[str] = None  # Optional
    excel_filename: str  # Required for PO number generation


class ReceivePurchaseOrderRequest(BaseModel):
    """Request model for receiving purchase orders"""
    items: List[Dict[str, Any]]
    receive_date: date  # Required
    notes: Optional[str] = None  # Optional


class TransferRequest(BaseModel):
    """Request model for inventory transfers"""
    to_store_id: UUID
    items: List[Dict[str, Any]]
    notes: Optional[str] = None


class InventoryFilterParams(BaseModel):
    """Query parameters for inventory filtering"""
    category: Optional[str] = None
    brand: Optional[str] = None
    low_stock: Optional[bool] = False
    out_of_stock: Optional[bool] = False
    search: Optional[str] = None


# =====================================================
# Dependency Injection
# =====================================================

async def get_store_inventory_service() -> StoreInventoryService:
    """Dependency to get store inventory service instance"""
    db_pool = await get_db_pool()
    return create_store_inventory_service(db_pool)


async def verify_store_access(
    store_id: Optional[UUID] = None,
    x_store_id: Optional[str] = Header(None, alias="X-Store-ID")
) -> UUID:
    """
    Verify store access and return validated store ID
    
    Args:
        store_id: Store ID from request body/params
        x_store_id: Store ID from header
        
    Returns:
        Validated store UUID
        
    Raises:
        HTTPException if no valid store ID or access denied
    """
    # Priority: explicit store_id > header store_id
    if store_id:
        # TODO: Verify user has access to this store
        return store_id
    
    if x_store_id:
        try:
            return UUID(x_store_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid store ID in header")
    
    raise HTTPException(
        status_code=400, 
        detail="Store context required. Please select a store or provide X-Store-ID header"
    )


# =====================================================
# Inventory Query Endpoints
# =====================================================

@router.get("/")
async def get_inventory_by_category(
    store_id: UUID = Depends(verify_store_access),
    category: Optional[str] = Query(None),
    sub_category: Optional[str] = Query(None),
    sub_sub_category: Optional[str] = Query(None),
    service: StoreInventoryService = Depends(get_store_inventory_service)
) -> Dict[str, Any]:
    """
    Get inventory products filtered by category hierarchy
    Used by pricing UI for category drill-down

    Args:
        store_id: Store UUID
        category: Top-level category (e.g., "Flower")
        sub_category: Sub-category (e.g., "Pre-Rolls")
        sub_sub_category: Sub-sub-category (e.g., "Blended Pre-Rolls")

    Returns:
        List of products matching the category filters
    """
    try:
        async with service.db_pool.acquire() as conn:
            # Build query with category filters
            query = """
                SELECT
                    i.id,
                    i.sku,
                    i.product_name,
                    i.unit_cost,
                    i.retail_price,
                    i.override_price,
                    i.retail_price_dynamic,
                    i.quantity_available,
                    pc.category,
                    pc.sub_category,
                    pc.sub_sub_category,
                    pc.brand,
                    pc.image_url,
                    CASE
                        WHEN i.unit_cost > 0
                        THEN ((COALESCE(i.override_price, i.retail_price) - i.unit_cost) / i.unit_cost) * 100
                        ELSE 0
                    END as current_markup
                FROM ocs_inventory i
                INNER JOIN ocs_product_catalog pc ON LOWER(TRIM(i.sku)) = LOWER(TRIM(pc.ocs_variant_number))
                WHERE i.store_id = $1
            """

            params = [store_id]
            param_count = 1

            if category:
                param_count += 1
                query += f" AND pc.category = ${param_count}"
                params.append(category)

            if sub_category:
                param_count += 1
                query += f" AND pc.sub_category = ${param_count}"
                params.append(sub_category)

            if sub_sub_category:
                param_count += 1
                query += f" AND pc.sub_sub_category = ${param_count}"
                params.append(sub_sub_category)

            query += " ORDER BY pc.category, pc.sub_category, pc.sub_sub_category, i.product_name"

            results = await conn.fetch(query, *params)

            # Convert to dict and convert Decimal fields to float for frontend
            inventory = []
            for row in results:
                item = dict(row)
                # Convert price fields from Decimal to float
                if item.get('unit_cost'):
                    item['unit_cost'] = float(item['unit_cost'])
                if item.get('retail_price'):
                    item['retail_price'] = float(item['retail_price'])
                if item.get('override_price'):
                    item['override_price'] = float(item['override_price'])
                if item.get('retail_price_dynamic'):
                    item['retail_price_dynamic'] = float(item['retail_price_dynamic'])
                if item.get('current_markup'):
                    item['current_markup'] = float(item['current_markup'])
                inventory.append(item)

            return {'inventory': inventory}

    except Exception as e:
        logger.error(f"Error getting inventory by category: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{sku}")
async def get_inventory_status(
    sku: str,
    store_id: UUID = Depends(verify_store_access),
    service: StoreInventoryService = Depends(get_store_inventory_service)
) -> Dict[str, Any]:
    """
    Get current inventory status for a SKU in a specific store
    
    Args:
        sku: Product SKU
        store_id: Store UUID (from header or query)
        
    Returns:
        Inventory status details
    """
    try:
        result = await service.get_store_inventory_status(store_id, sku)
        if not result:
            raise HTTPException(
                status_code=404, 
                detail=f"SKU {sku} not found in store inventory"
            )
        return result
    except Exception as e:
        logger.error(f"Error getting inventory status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_store_inventory(
    store_id: UUID = Depends(verify_store_access),
    category: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    low_stock: bool = Query(False),
    out_of_stock: bool = Query(False),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service: StoreInventoryService = Depends(get_store_inventory_service)
) -> Dict[str, Any]:
    """
    Get paginated inventory list for a store with filters
    
    Args:
        store_id: Store UUID
        category: Filter by product category
        brand: Filter by brand
        low_stock: Show only low stock items
        out_of_stock: Show only out of stock items
        search: Search term for SKU or product name
        limit: Number of records to return
        offset: Number of records to skip
        
    Returns:
        Paginated inventory list with total count
    """
    try:
        filters = {
            'category': category,
            'brand': brand,
            'low_stock': low_stock,
            'out_of_stock': out_of_stock,
            'search': search
        }
        
        items, total = await service.get_store_inventory_list(
            store_id, filters, limit, offset
        )
        
        return {
            'items': items,
            'total': total,
            'limit': limit,
            'offset': offset
        }
    except Exception as e:
        logger.error(f"Error listing store inventory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_inventory_statistics(
    store_id: UUID = Depends(verify_store_access),
    service: StoreInventoryService = Depends(get_store_inventory_service)
) -> Dict[str, Any]:
    """
    Get inventory statistics for a store
    
    Args:
        store_id: Store UUID
        
    Returns:
        Inventory statistics
    """
    try:
        stats = await service.get_store_inventory_stats(store_id)
        return stats
    except Exception as e:
        logger.error(f"Error getting inventory stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# Inventory Update Endpoints
# =====================================================

@router.post("/update")
async def update_inventory(
    request: InventoryUpdateRequest,
    store_id: UUID = Depends(verify_store_access),
    service: StoreInventoryService = Depends(get_store_inventory_service)
) -> Dict[str, Any]:
    """
    Update inventory levels for a specific store
    
    Args:
        request: Inventory update details
        store_id: Store UUID
        
    Returns:
        Updated inventory status
    """
    try:
        # Convert string to TransactionType enum
        try:
            transaction_type = TransactionType(request.transaction_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid transaction type: {request.transaction_type}"
            )
        
        result = await service.update_store_inventory(
            store_id=store_id,
            sku=request.sku,
            quantity_change=request.quantity_change,
            transaction_type=transaction_type,
            reference_id=request.reference_id,
            notes=request.notes,
            batch_lot=request.batch_lot
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating inventory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/adjust")
async def adjust_inventory(
    sku: str = Body(...),
    adjustment: int = Body(...),
    reason: str = Body(...),
    store_id: UUID = Depends(verify_store_access),
    service: StoreInventoryService = Depends(get_store_inventory_service)
) -> Dict[str, Any]:
    """
    Make inventory adjustment for cycle counts or corrections

    Args:
        sku: Product SKU
        adjustment: Quantity adjustment (positive or negative)
        reason: Reason for adjustment
        store_id: Store UUID

    Returns:
        Updated inventory status
    """
    try:
        result = await service.update_store_inventory(
            store_id=store_id,
            sku=sku,
            quantity_change=adjustment,
            transaction_type=TransactionType.ADJUSTMENT,
            notes=f"Manual adjustment: {reason}"
        )

        return result
    except Exception as e:
        logger.error(f"Error adjusting inventory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-adjust")
async def batch_adjust_inventory(
    sku: str = Body(...),
    store_id: UUID = Body(None),
    batch_adjustments: List[Dict[str, Any]] = Body(...),
    retail_price: Optional[Decimal] = Body(None),
    reorder_point: Optional[int] = Body(None),
    reorder_quantity: Optional[int] = Body(None),
    is_available: Optional[bool] = Body(None),
    x_store_id: Optional[str] = Header(None, alias="X-Store-ID"),
    service: StoreInventoryService = Depends(get_store_inventory_service)
) -> Dict[str, Any]:
    """
    Make batch-level inventory adjustments for a SKU

    Args:
        sku: Product SKU
        store_id: Store UUID from body
        batch_adjustments: List of batch adjustments with batch_lot, adjustment, reason
        retail_price: Optional new retail price
        reorder_point: Optional new reorder point
        reorder_quantity: Optional new reorder quantity
        is_available: Optional availability status
        x_store_id: Store ID from header (fallback)

    Returns:
        Updated inventory status
    """
    try:
        # Determine store ID
        final_store_id = store_id
        if not final_store_id and x_store_id:
            try:
                final_store_id = UUID(x_store_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid store ID in header")

        if not final_store_id:
            raise HTTPException(status_code=400, detail="Store ID required")

        # Process each batch adjustment
        total_adjustment = 0
        for batch in batch_adjustments:
            if batch['adjustment'] != 0:
                # Update batch tracking quantity
                await service.adjust_batch_quantity(
                    store_id=final_store_id,
                    sku=sku,
                    batch_lot=batch['batch_lot'],
                    adjustment=batch['adjustment'],
                    reason=batch['reason']
                )
                total_adjustment += batch['adjustment']

        # Update inventory totals
        if total_adjustment != 0:
            await service.update_store_inventory(
                store_id=final_store_id,
                sku=sku,
                quantity_change=total_adjustment,
                transaction_type=TransactionType.ADJUSTMENT,
                notes=f"Batch-level adjustments: {len(batch_adjustments)} batches"
            )

        # Update inventory settings if provided
        if any([retail_price is not None, reorder_point is not None,
                reorder_quantity is not None, is_available is not None]):
            await service.update_inventory_settings(
                store_id=final_store_id,
                sku=sku,
                retail_price=retail_price,
                reorder_point=reorder_point,
                reorder_quantity=reorder_quantity,
                is_available=is_available
            )

        # Return updated inventory status
        result = await service.get_store_inventory_status(final_store_id, sku)
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in batch inventory adjustment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# Purchase Order Endpoints
# =====================================================

@router.post("/purchase-orders")
async def create_purchase_order(
    request: CreatePurchaseOrderRequest,
    store_id: UUID = Depends(verify_store_access),
    service: StoreInventoryService = Depends(get_store_inventory_service)
) -> Dict[str, Any]:
    """
    Create a new purchase order for a store
    
    Args:
        request: Purchase order details
        store_id: Store UUID
        
    Returns:
        Created purchase order ID
    """
    try:
        # Convert request items to dict format
        items = [item.dict() for item in request.items]
        
        po_id = await service.create_store_purchase_order(
            store_id=store_id,
            supplier_id=request.supplier_id,
            items=items,
            expected_date=request.expected_date,
            notes=request.notes
        )
        
        return {
            'id': str(po_id),
            'message': 'Purchase order created successfully'
        }
    except Exception as e:
        logger.error(f"Error creating purchase order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/purchase-orders/{po_id}/receive")
async def receive_purchase_order(
    po_id: UUID,
    request: ReceivePurchaseOrderRequest,
    store_id: UUID = Depends(verify_store_access),
    service: StoreInventoryService = Depends(get_store_inventory_service)
) -> Dict[str, Any]:
    """
    Receive items from a purchase order
    
    Args:
        po_id: Purchase order UUID
        request: Received items details
        store_id: Store UUID
        
    Returns:
        Success status
    """
    try:
        success = await service.receive_store_purchase_order(
            store_id=store_id,
            po_id=po_id,
            received_items=request.items,
            receive_date=request.receive_date
        )
        
        if success:
            return {
                'message': 'Purchase order received successfully',
                'po_id': str(po_id)
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to receive purchase order"
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error receiving purchase order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# Transfer Endpoints
# =====================================================

@router.post("/transfers")
async def create_inventory_transfer(
    request: TransferRequest,
    store_id: UUID = Depends(verify_store_access),
    service: StoreInventoryService = Depends(get_store_inventory_service)
) -> Dict[str, Any]:
    """
    Create inventory transfer between stores
    
    Args:
        request: Transfer details
        store_id: Source store UUID
        
    Returns:
        Transfer ID
    """
    try:
        transfer_id = await service.create_store_transfer(
            from_store_id=store_id,
            to_store_id=request.to_store_id,
            items=request.items,
            notes=request.notes
        )
        
        return {
            'id': str(transfer_id),
            'message': 'Transfer created successfully'
        }
    except Exception as e:
        logger.error(f"Error creating transfer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# Batch Operations
# =====================================================

@router.post("/batch-update")
async def batch_update_inventory(
    updates: List[InventoryUpdateRequest],
    store_id: UUID = Depends(verify_store_access),
    service: StoreInventoryService = Depends(get_store_inventory_service)
) -> Dict[str, Any]:
    """
    Batch update multiple inventory items
    
    Args:
        updates: List of inventory updates
        store_id: Store UUID
        
    Returns:
        Results of batch update
    """
    try:
        results = []
        errors = []
        
        for update in updates:
            try:
                transaction_type = TransactionType(update.transaction_type)
                result = await service.update_store_inventory(
                    store_id=store_id,
                    sku=update.sku,
                    quantity_change=update.quantity_change,
                    transaction_type=transaction_type,
                    reference_id=update.reference_id,
                    notes=update.notes,
                    batch_lot=update.batch_lot
                )
                results.append({
                    'sku': update.sku,
                    'success': True,
                    'new_quantity': result['quantity_available']
                })
            except Exception as e:
                errors.append({
                    'sku': update.sku,
                    'error': str(e)
                })
        
        return {
            'successful': results,
            'failed': errors,
            'total_processed': len(updates)
        }
    except Exception as e:
        logger.error(f"Error in batch update: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# Pricing Endpoints
# =====================================================

@router.get("/pricing/settings")
async def get_pricing_settings(
    store_id: UUID = Depends(verify_store_access),
    service: StoreInventoryService = Depends(get_store_inventory_service)
):
    """Get store pricing settings including default markup"""
    try:
        async with service.db_pool.acquire() as conn:
            # Try to get existing settings from store_settings table
            query = """
                SELECT value
                FROM store_settings
                WHERE store_id = $1
                AND category = 'pricing'
                AND key = 'default_markup'
            """
            result = await conn.fetchrow(query, store_id)

            if result and result['value']:
                # Parse the JSON string if needed and return directly
                import json
                value_data = result['value']
                if isinstance(value_data, str):
                    value_data = json.loads(value_data)
                return value_data
            else:
                # Return default settings if none exist
                return {
                    'default_markup_percentage': 25.0,
                    'default_markup_enabled': True
                }
    except Exception as e:
        logger.error(f"Error getting pricing settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pricing/settings")
async def update_pricing_settings(
    settings: Dict[str, Any] = Body(...),
    store_id: UUID = Depends(verify_store_access),
    service: StoreInventoryService = Depends(get_store_inventory_service)
):
    """Update store pricing settings"""
    try:
        async with service.db_pool.acquire() as conn:
            # Upsert settings into store_settings table
            query = """
                INSERT INTO store_settings (store_id, category, key, value)
                VALUES ($1, 'pricing', 'default_markup', $2::jsonb)
                ON CONFLICT (store_id, category, key)
                DO UPDATE SET
                    value = $2::jsonb,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING value
            """

            import json
            settings_json = json.dumps(settings)
            result = await conn.fetchrow(query, store_id, settings_json)
            return result['value']
    except Exception as e:
        logger.error(f"Error updating pricing settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pricing/categories")
async def get_pricing_categories(
    store_id: UUID = Depends(verify_store_access),
    service: StoreInventoryService = Depends(get_store_inventory_service)
):
    """Get category hierarchy with pricing rules and product counts"""
    try:
        async with service.db_pool.acquire() as conn:
            # Get product counts and pricing stats by category
            # Query FROM inventory (source of truth per store) JOIN catalog (for category lookup)
            stats_query = """
                SELECT
                    pc.category,
                    pc.sub_category,
                    pc.sub_sub_category,
                    COUNT(i.id) as product_count,
                    AVG(
                        CASE
                            WHEN i.unit_cost > 0
                            THEN ((COALESCE(i.override_price, i.retail_price) - i.unit_cost) / i.unit_cost) * 100
                            ELSE 0
                        END
                    ) as avg_markup,
                    COUNT(CASE WHEN i.override_price IS NOT NULL THEN 1 END) as override_count
                FROM ocs_inventory i
                INNER JOIN ocs_product_catalog pc ON LOWER(TRIM(i.sku)) = LOWER(TRIM(pc.ocs_variant_number))
                WHERE i.store_id = $1 AND pc.category IS NOT NULL
                GROUP BY pc.category, pc.sub_category, pc.sub_sub_category
                ORDER BY pc.category, pc.sub_category, pc.sub_sub_category
            """

            stats = await conn.fetch(stats_query, store_id)

            # Get pricing rules for this store
            pricing_query = """
                SELECT
                    category,
                    sub_category,
                    sub_sub_category,
                    markup_percentage
                FROM pricing_rules
                WHERE store_id = $1
            """

            pricing_rules = await conn.fetch(pricing_query, store_id)

            # Build pricing lookup
            pricing_map = {}
            for rule in pricing_rules:
                key = (
                    rule['category'] or '',
                    rule['sub_category'] or '',
                    rule['sub_sub_category'] or ''
                )
                pricing_map[key] = rule['markup_percentage']

            # Build hierarchical structure with stats
            hierarchy = {}
            for stat in stats:
                category = stat['category']
                sub_category = stat['sub_category']
                sub_sub_category = stat['sub_sub_category']

                # Initialize category if not exists
                if category not in hierarchy:
                    hierarchy[category] = {
                        'name': category,
                        'product_count': 0,
                        'avg_markup': 0,
                        'override_count': 0,
                        'markup': pricing_map.get((category, '', ''), None),
                        'subcategories': {}
                    }

                if sub_category:
                    # Initialize subcategory if not exists
                    if sub_category not in hierarchy[category]['subcategories']:
                        hierarchy[category]['subcategories'][sub_category] = {
                            'name': sub_category,
                            'product_count': 0,
                            'avg_markup': 0,
                            'override_count': 0,
                            'markup': pricing_map.get((category, sub_category, ''), None),
                            'subsubcategories': {}
                        }

                    if sub_sub_category:
                        # Add sub-sub-category with stats
                        hierarchy[category]['subcategories'][sub_category]['subsubcategories'][sub_sub_category] = {
                            'name': sub_sub_category,
                            'product_count': stat['product_count'],
                            'avg_markup': float(stat['avg_markup']) if stat['avg_markup'] else 0,
                            'override_count': stat['override_count'],
                            'markup': pricing_map.get((category, sub_category, sub_sub_category), None)
                        }
                        # Aggregate to subcategory
                        hierarchy[category]['subcategories'][sub_category]['product_count'] += stat['product_count']
                        hierarchy[category]['subcategories'][sub_category]['override_count'] += stat['override_count']
                    else:
                        # Direct subcategory stats (no sub-sub-category)
                        hierarchy[category]['subcategories'][sub_category]['product_count'] += stat['product_count']
                        hierarchy[category]['subcategories'][sub_category]['override_count'] += stat['override_count']
                        if stat['avg_markup']:
                            hierarchy[category]['subcategories'][sub_category]['avg_markup'] = float(stat['avg_markup'])

                    # Aggregate to category
                    hierarchy[category]['product_count'] += stat['product_count']
                    hierarchy[category]['override_count'] += stat['override_count']
                else:
                    # Direct category stats (no subcategory)
                    hierarchy[category]['product_count'] += stat['product_count']
                    hierarchy[category]['override_count'] += stat['override_count']
                    if stat['avg_markup']:
                        hierarchy[category]['avg_markup'] = float(stat['avg_markup'])

            # Calculate weighted average markups for categories and subcategories
            for category, cat_data in hierarchy.items():
                if cat_data['subcategories']:
                    total_products = sum(sub.get('product_count', 0) for sub in cat_data['subcategories'].values())
                    if total_products > 0:
                        weighted_sum = sum(
                            sub.get('product_count', 0) * sub.get('avg_markup', 0)
                            for sub in cat_data['subcategories'].values()
                        )
                        cat_data['avg_markup'] = weighted_sum / total_products

                    # Calculate weighted average for subcategories with sub-sub-categories
                    for sub_key, sub_data in cat_data['subcategories'].items():
                        if sub_data.get('subsubcategories'):
                            total_sub_products = sum(
                                subsub.get('product_count', 0)
                                for subsub in sub_data['subsubcategories'].values()
                            )
                            if total_sub_products > 0:
                                weighted_sub_sum = sum(
                                    subsub.get('product_count', 0) * subsub.get('avg_markup', 0)
                                    for subsub in sub_data['subsubcategories'].values()
                                )
                                sub_data['avg_markup'] = weighted_sub_sum / total_sub_products

            return {'categories': hierarchy}
    except Exception as e:
        logger.error(f"Error getting pricing categories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pricing/update")
async def update_pricing_rule(
    pricing_data: Dict[str, Any] = Body(...),
    store_id: UUID = Depends(verify_store_access),
    service: StoreInventoryService = Depends(get_store_inventory_service)
):
    """Update pricing rule for a category or specific SKU"""
    try:
        async with service.db_pool.acquire() as conn:
            if 'sku' in pricing_data:
                # Update specific product pricing override
                query = """
                    UPDATE ocs_inventory
                    SET
                        retail_price = unit_cost * (1 + $2::numeric / 100),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE store_id = $1 AND sku = $3
                    RETURNING sku, retail_price
                """
                result = await conn.fetchrow(
                    query,
                    store_id,
                    pricing_data['markup_percentage'],
                    pricing_data['sku']
                )
            else:
                # Upsert category pricing rule
                query = """
                    INSERT INTO pricing_rules (
                        store_id, category, sub_category, sub_sub_category, markup_percentage
                    )
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (store_id, category, sub_category, sub_sub_category)
                    DO UPDATE SET
                        markup_percentage = $5,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id, markup_percentage
                """

                result = await conn.fetchrow(
                    query,
                    store_id,
                    pricing_data.get('category'),
                    pricing_data.get('sub_category'),
                    pricing_data.get('sub_sub_category'),
                    pricing_data['markup_percentage']
                )

                # Also update all affected products if requested
                if pricing_data.get('apply_to_products', False):
                    update_query = """
                        UPDATE ocs_inventory i
                        SET
                            retail_price = i.unit_cost * (1 + $5::numeric / 100),
                            updated_at = CURRENT_TIMESTAMP
                        FROM ocs_product_catalog pc
                        WHERE i.store_id = $1
                        AND i.sku = pc.ocs_variant_number
                        AND ($2::text IS NULL OR pc.category = $2)
                        AND ($3::text IS NULL OR pc.sub_category = $3)
                        AND ($4::text IS NULL OR pc.sub_sub_category = $4)
                    """

                    await conn.execute(
                        update_query,
                        store_id,
                        pricing_data.get('category'),
                        pricing_data.get('sub_category'),
                        pricing_data.get('sub_sub_category'),
                        pricing_data['markup_percentage']
                    )

            return {'success': True, 'result': dict(result) if result else None}
    except Exception as e:
        logger.error(f"Error updating pricing rule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/product-pricing/{sku}")
async def get_product_pricing(
    sku: str,
    store_id: UUID = Depends(verify_store_access),
    service: StoreInventoryService = Depends(get_store_inventory_service)
):
    """Get pricing information for a specific SKU"""
    try:
        async with service.db_pool.acquire() as conn:
            # Get inventory and product info
            query = """
                SELECT
                    i.sku,
                    i.unit_cost,
                    i.retail_price,
                    pc.category,
                    pc.sub_category,
                    pc.sub_sub_category
                FROM ocs_inventory i
                LEFT JOIN ocs_product_catalog pc ON i.sku = pc.ocs_variant_number
                WHERE i.store_id = $1 AND i.sku = $2
            """

            product = await conn.fetchrow(query, store_id, sku)

            # If product doesn't exist in inventory, check catalog
            if not product:
                catalog_query = """
                    SELECT
                        ocs_variant_number as sku,
                        category,
                        sub_category,
                        sub_sub_category
                    FROM ocs_product_catalog
                    WHERE ocs_variant_number = $1
                """
                product = await conn.fetchrow(catalog_query, sku)

            if not product:
                return {
                    'sku': sku,
                    'override_price': None,
                    'category_pricing': None
                }

            # Check for override price (if retail price differs from calculated)
            override_price = None
            if product.get('retail_price') and product.get('unit_cost'):
                expected_markup = await get_category_markup(
                    conn, store_id,
                    product.get('category'),
                    product.get('sub_category'),
                    product.get('sub_sub_category')
                )
                expected_price = float(product['unit_cost']) * (1 + expected_markup / 100)
                if abs(float(product['retail_price']) - expected_price) > 0.01:
                    override_price = float(product['retail_price'])

            # Get category pricing rules
            pricing_rules_query = """
                SELECT
                    CASE
                        WHEN sub_sub_category IS NOT NULL THEN 'sub_sub_category'
                        WHEN sub_category IS NOT NULL THEN 'sub_category'
                        ELSE 'category'
                    END as level,
                    markup_percentage
                FROM pricing_rules
                WHERE store_id = $1
                AND ($2::text IS NULL OR category = $2 OR category IS NULL)
                AND ($3::text IS NULL OR sub_category = $3 OR sub_category IS NULL)
                AND ($4::text IS NULL OR sub_sub_category = $4 OR sub_sub_category IS NULL)
                ORDER BY
                    CASE
                        WHEN sub_sub_category IS NOT NULL THEN 3
                        WHEN sub_category IS NOT NULL THEN 2
                        ELSE 1
                    END DESC
            """

            pricing_rules = await conn.fetch(
                pricing_rules_query,
                store_id,
                product.get('category'),
                product.get('sub_category'),
                product.get('sub_sub_category')
            )

            category_pricing = {
                'category_markup': None,
                'sub_category_markup': None,
                'sub_sub_category_markup': None
            }

            for rule in pricing_rules:
                if rule['level'] == 'category':
                    category_pricing['category_markup'] = float(rule['markup_percentage'])
                elif rule['level'] == 'sub_category':
                    category_pricing['sub_category_markup'] = float(rule['markup_percentage'])
                elif rule['level'] == 'sub_sub_category':
                    category_pricing['sub_sub_category_markup'] = float(rule['markup_percentage'])

            return {
                'sku': sku,
                'override_price': override_price,
                'category_pricing': category_pricing
            }
    except Exception as e:
        logger.error(f"Error getting product pricing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_category_markup(conn, store_id, category, sub_category, sub_sub_category):
    """Helper function to get the applicable markup for a category"""
    # Check for most specific rule first
    query = """
        SELECT markup_percentage
        FROM pricing_rules
        WHERE store_id = $1
        AND ($2::text IS NULL OR category = $2)
        AND ($3::text IS NULL OR sub_category = $3)
        AND ($4::text IS NULL OR sub_sub_category = $4)
        ORDER BY
            CASE
                WHEN sub_sub_category IS NOT NULL THEN 3
                WHEN sub_category IS NOT NULL THEN 2
                ELSE 1
            END DESC
        LIMIT 1
    """

    result = await conn.fetchrow(query, store_id, category, sub_category, sub_sub_category)

    if result:
        return float(result['markup_percentage'])

    # Fall back to default markup
    settings_query = """
        SELECT value->>'default_markup_percentage' as markup
        FROM store_settings
        WHERE store_id = $1 AND category = 'pricing' AND key = 'default_markup'
    """

    settings = await conn.fetchrow(settings_query, store_id)
    if settings and settings['markup']:
        return float(settings['markup'])

    return 25.0  # Default fallback


# =====================================================
# Export Router
# =====================================================

def get_router() -> APIRouter:
    """Get configured router instance"""
    return router