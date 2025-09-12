"""
Store Management API Endpoints
Handles multi-tenant store operations and store context management
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Header
from typing import List, Dict, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field
import asyncpg
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/stores", tags=["stores"])

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


# =====================================================
# Pydantic Models
# =====================================================

class StoreAddress(BaseModel):
    """Store address model"""
    street: str
    city: str
    province: str
    postal_code: str
    country: str = "Canada"


class StoreHours(BaseModel):
    """Store operating hours"""
    monday: Optional[Dict[str, str]] = None
    tuesday: Optional[Dict[str, str]] = None
    wednesday: Optional[Dict[str, str]] = None
    thursday: Optional[Dict[str, str]] = None
    friday: Optional[Dict[str, str]] = None
    saturday: Optional[Dict[str, str]] = None
    sunday: Optional[Dict[str, str]] = None


class StoreResponse(BaseModel):
    """Store response model"""
    id: UUID
    tenant_id: UUID
    tenant_code: Optional[str] = None
    store_code: str
    name: str
    address: Dict[str, Any]
    phone: Optional[str]
    email: Optional[str]
    timezone: str
    license_number: Optional[str]
    license_expiry: Optional[str]
    tax_rate: Optional[float]
    delivery_radius_km: Optional[int]
    delivery_enabled: bool
    pickup_enabled: bool
    kiosk_enabled: bool
    pos_enabled: bool
    ecommerce_enabled: bool
    status: str
    created_at: datetime
    updated_at: datetime


class StoreInventoryStats(BaseModel):
    """Store inventory statistics"""
    total_skus: int
    total_quantity: int
    low_stock_items: int
    out_of_stock_items: int
    total_value: float


class CreateStoreRequest(BaseModel):
    """Request model for creating a store"""
    tenant_id: UUID
    province_territory_id: UUID
    store_code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    address: StoreAddress
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    timezone: str = "America/Toronto"
    license_number: Optional[str] = Field(None, max_length=100)
    tax_rate: Optional[float] = Field(None, ge=0, le=100)
    delivery_radius_km: int = Field(10, ge=0)
    delivery_enabled: bool = True
    pickup_enabled: bool = True
    pos_enabled: bool = True
    ecommerce_enabled: bool = True


class UpdateStoreRequest(BaseModel):
    """Request model for updating a store"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    address: Optional[StoreAddress] = None
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    timezone: Optional[str] = None
    license_number: Optional[str] = Field(None, max_length=100)
    tax_rate: Optional[float] = Field(None, ge=0, le=100)
    delivery_radius_km: Optional[int] = Field(None, ge=0)
    delivery_enabled: Optional[bool] = None
    pickup_enabled: Optional[bool] = None
    pos_enabled: Optional[bool] = None
    ecommerce_enabled: Optional[bool] = None
    status: Optional[str] = Field(None, pattern="^(active|inactive|suspended)$")


# =====================================================
# Dependency Injection
# =====================================================

async def get_current_store(
    x_store_id: Optional[str] = Header(None, alias="X-Store-ID")
) -> Optional[UUID]:
    """Get current store ID from request header"""
    if x_store_id:
        try:
            return UUID(x_store_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid store ID format")
    return None


async def require_store_context(
    store_id: Optional[UUID] = Depends(get_current_store)
) -> UUID:
    """Require store context for the request"""
    if not store_id:
        raise HTTPException(
            status_code=400,
            detail="Store context required. Please set X-Store-ID header."
        )
    return store_id


# =====================================================
# Store Management Endpoints
# =====================================================

@router.get("/", response_model=List[StoreResponse])
async def get_stores(
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant ID"),
    status: Optional[str] = Query(None, pattern="^(active|inactive|suspended)$"),
    province_id: Optional[UUID] = Query(None, description="Filter by province/territory")
):
    """Get all stores with optional filtering"""
    pool = await get_db_pool()
    
    try:
        async with pool.acquire() as conn:
            query = """
                SELECT 
                    s.id,
                    s.tenant_id,
                    s.store_code,
                    s.name,
                    s.address,
                    s.phone,
                    s.email,
                    s.timezone,
                    s.license_number,
                    s.license_expiry,
                    s.tax_rate,
                    s.delivery_radius_km,
                    s.delivery_enabled,
                    s.pickup_enabled,
                    s.kiosk_enabled,
                    s.pos_enabled,
                    s.ecommerce_enabled,
                    s.status,
                    s.created_at,
                    s.updated_at
                FROM stores s
                WHERE 1=1
            """
            
            params = []
            param_count = 0
            
            if tenant_id:
                param_count += 1
                query += f" AND s.tenant_id = ${param_count}"
                params.append(tenant_id)
            
            if status:
                param_count += 1
                query += f" AND s.status = ${param_count}"
                params.append(status)
            
            if province_id:
                param_count += 1
                query += f" AND s.province_territory_id = ${param_count}"
                params.append(province_id)
            
            query += " ORDER BY s.name ASC"
            
            rows = await conn.fetch(query, *params)
            
            stores = []
            for row in rows:
                store_dict = dict(row)
                # Format license_expiry as string if it exists
                if store_dict.get('license_expiry'):
                    store_dict['license_expiry'] = store_dict['license_expiry'].isoformat()
                stores.append(StoreResponse(**store_dict))
            
            return stores
            
    except Exception as e:
        logger.error(f"Error fetching stores: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{store_id}", response_model=StoreResponse)
async def get_store(store_id: UUID):
    """Get a specific store by ID"""
    pool = await get_db_pool()
    
    try:
        async with pool.acquire() as conn:
            query = """
                SELECT 
                    s.id,
                    s.tenant_id,
                    t.code as tenant_code,
                    s.store_code,
                    s.name,
                    s.address,
                    s.phone,
                    s.email,
                    s.timezone,
                    s.license_number,
                    s.license_expiry,
                    s.tax_rate,
                    s.delivery_radius_km,
                    s.delivery_enabled,
                    s.pickup_enabled,
                    s.kiosk_enabled,
                    s.pos_enabled,
                    s.ecommerce_enabled,
                    s.status,
                    s.created_at,
                    s.updated_at
                FROM stores s
                JOIN tenants t ON s.tenant_id = t.id
                WHERE s.id = $1
            """
            
            row = await conn.fetchrow(query, store_id)
            
            if not row:
                raise HTTPException(status_code=404, detail="Store not found")
            
            store_dict = dict(row)
            # Format license_expiry as string if it exists
            if store_dict.get('license_expiry'):
                store_dict['license_expiry'] = store_dict['license_expiry'].isoformat()
            
            return StoreResponse(**store_dict)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching store {store_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-code/{store_code}", response_model=StoreResponse)
async def get_store_by_code(store_code: str):
    """Get a specific store by store code"""
    pool = await get_db_pool()
    
    try:
        async with pool.acquire() as conn:
            query = """
                SELECT 
                    s.id,
                    s.tenant_id,
                    t.code as tenant_code,
                    s.store_code,
                    s.name,
                    s.address,
                    s.phone,
                    s.email,
                    s.timezone,
                    s.license_number,
                    s.license_expiry,
                    s.tax_rate,
                    s.delivery_radius_km,
                    s.delivery_enabled,
                    s.pickup_enabled,
                    s.kiosk_enabled,
                    s.pos_enabled,
                    s.ecommerce_enabled,
                    s.status,
                    s.created_at,
                    s.updated_at
                FROM stores s
                JOIN tenants t ON s.tenant_id = t.id
                WHERE s.store_code = $1
            """
            
            row = await conn.fetchrow(query, store_code)
            
            if not row:
                raise HTTPException(status_code=404, detail="Store not found")
            
            store_dict = dict(row)
            # Format license_expiry as string if it exists
            if store_dict.get('license_expiry'):
                store_dict['license_expiry'] = store_dict['license_expiry'].isoformat()
            
            return StoreResponse(**store_dict)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching store by code {store_code}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=StoreResponse)
async def create_store(request: CreateStoreRequest):
    """Create a new store"""
    pool = await get_db_pool()
    
    try:
        async with pool.acquire() as conn:
            # Check if store code already exists
            check_query = "SELECT id FROM stores WHERE store_code = $1"
            existing = await conn.fetchval(check_query, request.store_code)
            
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Store code '{request.store_code}' already exists"
                )
            
            # Create the store
            insert_query = """
                INSERT INTO stores (
                    tenant_id,
                    province_territory_id,
                    store_code,
                    name,
                    address,
                    phone,
                    email,
                    timezone,
                    license_number,
                    tax_rate,
                    delivery_radius_km,
                    delivery_enabled,
                    pickup_enabled,
                    pos_enabled,
                    ecommerce_enabled
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                    $11, $12, $13, $14, $15
                ) RETURNING *
            """
            
            row = await conn.fetchrow(
                insert_query,
                request.tenant_id,
                request.province_territory_id,
                request.store_code,
                request.name,
                request.address.dict() if request.address else {},
                request.phone,
                request.email,
                request.timezone,
                request.license_number,
                request.tax_rate,
                request.delivery_radius_km,
                request.delivery_enabled,
                request.pickup_enabled,
                request.pos_enabled,
                request.ecommerce_enabled
            )
            
            store_dict = dict(row)
            if store_dict.get('license_expiry'):
                store_dict['license_expiry'] = store_dict['license_expiry'].isoformat()
            
            logger.info(f"Created store {store_dict['id']} with code {request.store_code}")
            return StoreResponse(**store_dict)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating store: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{store_id}", response_model=StoreResponse)
async def update_store(store_id: UUID, request: UpdateStoreRequest):
    """Update a store"""
    pool = await get_db_pool()
    
    try:
        async with pool.acquire() as conn:
            # Build dynamic update query
            update_fields = []
            params = [store_id]
            param_count = 1
            
            if request.name is not None:
                param_count += 1
                update_fields.append(f"name = ${param_count}")
                params.append(request.name)
            
            if request.address is not None:
                param_count += 1
                update_fields.append(f"address = ${param_count}")
                params.append(request.address.dict())
            
            if request.phone is not None:
                param_count += 1
                update_fields.append(f"phone = ${param_count}")
                params.append(request.phone)
            
            if request.email is not None:
                param_count += 1
                update_fields.append(f"email = ${param_count}")
                params.append(request.email)
            
            if request.timezone is not None:
                param_count += 1
                update_fields.append(f"timezone = ${param_count}")
                params.append(request.timezone)
            
            if request.license_number is not None:
                param_count += 1
                update_fields.append(f"license_number = ${param_count}")
                params.append(request.license_number)
            
            if request.tax_rate is not None:
                param_count += 1
                update_fields.append(f"tax_rate = ${param_count}")
                params.append(request.tax_rate)
            
            if request.delivery_radius_km is not None:
                param_count += 1
                update_fields.append(f"delivery_radius_km = ${param_count}")
                params.append(request.delivery_radius_km)
            
            if request.delivery_enabled is not None:
                param_count += 1
                update_fields.append(f"delivery_enabled = ${param_count}")
                params.append(request.delivery_enabled)
            
            if request.pickup_enabled is not None:
                param_count += 1
                update_fields.append(f"pickup_enabled = ${param_count}")
                params.append(request.pickup_enabled)
            
            if request.pos_enabled is not None:
                param_count += 1
                update_fields.append(f"pos_enabled = ${param_count}")
                params.append(request.pos_enabled)
            
            if request.ecommerce_enabled is not None:
                param_count += 1
                update_fields.append(f"ecommerce_enabled = ${param_count}")
                params.append(request.ecommerce_enabled)
            
            if request.status is not None:
                param_count += 1
                update_fields.append(f"status = ${param_count}")
                params.append(request.status)
            
            if not update_fields:
                raise HTTPException(status_code=400, detail="No fields to update")
            
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            
            update_query = f"""
                UPDATE stores
                SET {', '.join(update_fields)}
                WHERE id = $1
                RETURNING *
            """
            
            row = await conn.fetchrow(update_query, *params)
            
            if not row:
                raise HTTPException(status_code=404, detail="Store not found")
            
            store_dict = dict(row)
            if store_dict.get('license_expiry'):
                store_dict['license_expiry'] = store_dict['license_expiry'].isoformat()
            
            logger.info(f"Updated store {store_id}")
            return StoreResponse(**store_dict)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating store {store_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{store_id}/inventory/stats", response_model=StoreInventoryStats)
async def get_store_inventory_stats(store_id: UUID):
    """Get inventory statistics for a store"""
    pool = await get_db_pool()
    
    try:
        async with pool.acquire() as conn:
            query = """
                SELECT 
                    COUNT(DISTINCT sku) as total_skus,
                    COALESCE(SUM(quantity_on_hand), 0) as total_quantity,
                    COUNT(CASE WHEN quantity_available <= min_stock_level THEN 1 END) as low_stock_items,
                    COUNT(CASE WHEN quantity_available = 0 THEN 1 END) as out_of_stock_items,
                    COALESCE(SUM(quantity_on_hand * 
                        COALESCE(override_price, 
                            (SELECT retail_price FROM product_catalog WHERE ocs_variant_number = si.sku LIMIT 1)
                        )), 0) as total_value
                FROM store_inventory si
                WHERE store_id = $1 AND is_available = true
            """
            
            row = await conn.fetchrow(query, store_id)
            
            if not row:
                return StoreInventoryStats(
                    total_skus=0,
                    total_quantity=0,
                    low_stock_items=0,
                    out_of_stock_items=0,
                    total_value=0
                )
            
            return StoreInventoryStats(**dict(row))
            
    except Exception as e:
        logger.error(f"Error fetching inventory stats for store {store_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{store_id}/set-active")
async def set_active_store(store_id: UUID):
    """Set a store as the active store for the current session"""
    pool = await get_db_pool()
    
    try:
        async with pool.acquire() as conn:
            # Verify store exists and is active
            query = """
                SELECT id, name, status 
                FROM stores 
                WHERE id = $1
            """
            
            row = await conn.fetchrow(query, store_id)
            
            if not row:
                raise HTTPException(status_code=404, detail="Store not found")
            
            if row['status'] != 'active':
                raise HTTPException(
                    status_code=400, 
                    detail=f"Store {row['name']} is not active"
                )
            
            return {
                "success": True,
                "store_id": str(store_id),
                "store_name": row['name'],
                "message": f"Active store set to {row['name']}"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting active store {store_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/accessible")
async def get_user_accessible_stores(
    user_id: Optional[UUID] = Query(None, description="User ID to check access for")
):
    """Get stores accessible by a user"""
    pool = await get_db_pool()
    
    try:
        async with pool.acquire() as conn:
            if user_id:
                # Get stores where user has access
                # Removed store_users table reference
                query = """
                    SELECT DISTINCT
                        s.id,
                        s.tenant_id,
                        s.store_code,
                        s.name,
                        s.address,
                        s.status,
                        NULL as user_role
                    FROM stores s
                    WHERE s.status = 'active'
                    ORDER BY s.name ASC
                """
                rows = await conn.fetch(query)
            else:
                # Get all active stores if no user specified
                query = """
                    SELECT 
                        s.id,
                        s.tenant_id,
                        s.store_code,
                        s.name,
                        s.address,
                        s.status
                    FROM stores s
                    WHERE s.status = 'active'
                    ORDER BY s.name ASC
                """
                rows = await conn.fetch(query)
            
            stores = []
            for row in rows:
                store_dict = dict(row)
                stores.append({
                    "id": str(store_dict['id']),
                    "tenant_id": str(store_dict['tenant_id']),
                    "store_code": store_dict['store_code'],
                    "name": store_dict['name'],
                    "address": store_dict['address'],
                    "status": store_dict['status'],
                    "user_role": store_dict.get('user_role')
                })
            
            return {
                "stores": stores,
                "count": len(stores)
            }
            
    except Exception as e:
        logger.error(f"Error fetching accessible stores: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))