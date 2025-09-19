"""
Store Management API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict, Optional, Any
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr
from decimal import Decimal
import asyncpg
import os
import logging
import jwt
import traceback

from core.domain.models import StoreStatus, ProvinceType
from core.services.store_service import StoreService
from core.services.tenant_service import TenantService
from core.repositories.store_repository import StoreRepository
from core.repositories.tenant_repository import TenantRepository
from core.repositories.province_repository import ProvinceRepository
from api.tenant_endpoints import get_db_pool, SubscriptionRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/stores", tags=["stores"])
security = HTTPBearer()

# JWT Configuration (same as in admin_auth.py)
JWT_SECRET = os.getenv('JWT_SECRET', 'dev-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'

def decode_token(token: str) -> dict:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


# Pydantic Models for API
class StoreAddressModel(BaseModel):
    street: str
    city: str
    province: str
    postal_code: str
    country: str = "Canada"


class StoreHoursModel(BaseModel):
    monday: Dict[str, str] = {"open": "09:00", "close": "21:00"}
    tuesday: Dict[str, str] = {"open": "09:00", "close": "21:00"}
    wednesday: Dict[str, str] = {"open": "09:00", "close": "21:00"}
    thursday: Dict[str, str] = {"open": "09:00", "close": "21:00"}
    friday: Dict[str, str] = {"open": "09:00", "close": "22:00"}
    saturday: Dict[str, str] = {"open": "10:00", "close": "22:00"}
    sunday: Dict[str, str] = {"open": "11:00", "close": "20:00"}


class CreateStoreRequest(BaseModel):
    tenant_id: UUID
    province_code: str = Field(..., min_length=2, max_length=2, pattern="^[A-Z]{2}$")
    store_code: str = Field(..., min_length=2, max_length=20, pattern="^[A-Z0-9_-]+$")
    name: str = Field(..., min_length=1, max_length=100)
    address: StoreAddressModel
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    hours: Optional[StoreHoursModel] = None
    timezone: str = Field(default="America/Toronto", max_length=50)
    license_number: Optional[str] = Field(None, max_length=100)
    license_expiry: Optional[date] = None
    delivery_radius_km: int = Field(default=10, ge=0, le=100)
    delivery_enabled: bool = True
    pickup_enabled: bool = True
    kiosk_enabled: bool = False
    pos_enabled: bool = True
    ecommerce_enabled: bool = True
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)
    pos_integration: Optional[Dict[str, Any]] = Field(default_factory=dict)
    seo_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)


class UpdateStoreRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    address: Optional[StoreAddressModel] = None
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    hours: Optional[StoreHoursModel] = None
    timezone: Optional[str] = Field(None, max_length=50)
    license_number: Optional[str] = Field(None, max_length=100)
    license_expiry: Optional[date] = None
    delivery_radius_km: Optional[int] = Field(None, ge=0, le=100)
    delivery_enabled: Optional[bool] = None
    pickup_enabled: Optional[bool] = None
    kiosk_enabled: Optional[bool] = None
    pos_enabled: Optional[bool] = None
    ecommerce_enabled: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None
    pos_integration: Optional[Dict[str, Any]] = None
    seo_config: Optional[Dict[str, Any]] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)


class SuspendStoreRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)


class StoreResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    province_territory_id: UUID
    store_code: str
    name: str
    address: Optional[Dict[str, Any]] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    hours: Dict[str, Any] = {}
    timezone: str
    license_number: Optional[str] = None
    license_expiry: Optional[date] = None
    tax_rate: float
    delivery_radius_km: int = 0
    delivery_enabled: bool = False
    pickup_enabled: bool = True
    kiosk_enabled: bool = False
    pos_enabled: bool = True
    ecommerce_enabled: bool = False
    status: str
    settings: Dict[str, Any] = {}
    pos_integration: Dict[str, Any] = {}
    seo_config: Dict[str, Any] = {}
    location: Optional[Dict[str, float]] = None
    created_at: datetime
    updated_at: datetime




async def get_store_service() -> StoreService:
    """Dependency to get store service"""
    pool = await get_db_pool()
    store_repo = StoreRepository(pool)
    tenant_repo = TenantRepository(pool)
    province_repo = ProvinceRepository(pool)
    subscription_repo = SubscriptionRepository(pool)
    tenant_service = TenantService(tenant_repo, subscription_repo)
    return StoreService(store_repo, tenant_repo, province_repo, tenant_service)


@router.get("/", response_model=List[StoreResponse])
async def list_all_stores(
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant ID"),
    status: Optional[StoreStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: StoreService = Depends(get_store_service)
):
    """List all stores with optional filtering"""
    try:
        stores = await service.list_stores_by_tenant(
            tenant_id=tenant_id,
            status=status,
            limit=limit,
            offset=offset
        )
        
        return [
            StoreResponse(
                id=store.id,
                tenant_id=store.tenant_id,
                province_territory_id=store.province_territory_id,
                store_code=store.store_code,
                name=store.name,
                address=store.address.to_dict() if store.address else None,
                phone=store.phone,
                email=store.email,
                hours=store.hours or {},
                timezone=store.timezone,
                license_number=store.license_number,
                license_expiry=store.license_expiry,
                tax_rate=float(store.tax_rate),
                delivery_radius_km=store.delivery_radius_km,
                delivery_enabled=store.delivery_enabled,
                pickup_enabled=store.pickup_enabled,
                kiosk_enabled=store.kiosk_enabled,
                pos_enabled=store.pos_enabled,
                ecommerce_enabled=store.ecommerce_enabled,
                status=store.status.value,
                settings=store.settings or {},
                pos_integration=store.pos_integration or {},
                seo_config=store.seo_config or {},
                location=store.location.to_dict() if store.location else None,
                created_at=store.created_at,
                updated_at=store.updated_at
            )
            for store in stores
        ]
        
    except Exception as e:
        logger.error(f"Error listing all stores: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list stores")


@router.post("/", response_model=StoreResponse, status_code=status.HTTP_201_CREATED)
async def create_store(
    request: CreateStoreRequest,
    service: StoreService = Depends(get_store_service)
):
    """Create a new store"""
    try:
        store = await service.create_store(
            tenant_id=request.tenant_id,
            province_code=request.province_code,
            store_code=request.store_code,
            name=request.name,
            address=request.address.dict(),
            phone=request.phone,
            email=request.email,
            hours=request.hours.dict() if request.hours else None,
            timezone=request.timezone,
            license_number=request.license_number,
            license_expiry=request.license_expiry,
            delivery_radius_km=request.delivery_radius_km,
            delivery_enabled=request.delivery_enabled,
            pickup_enabled=request.pickup_enabled,
            kiosk_enabled=request.kiosk_enabled,
            pos_enabled=request.pos_enabled,
            ecommerce_enabled=request.ecommerce_enabled,
            settings=request.settings,
            pos_integration=request.pos_integration,
            seo_config=request.seo_config,
            latitude=request.latitude,
            longitude=request.longitude
        )
        
        return StoreResponse(
            id=store.id,
            tenant_id=store.tenant_id,
            province_territory_id=store.province_territory_id,
            store_code=store.store_code,
            name=store.name,
            address=store.address.to_dict() if store.address else None,
            phone=store.phone,
            email=store.email,
            hours=store.hours,
            timezone=store.timezone,
            license_number=store.license_number,
            license_expiry=store.license_expiry,
            tax_rate=float(store.tax_rate),
            delivery_radius_km=store.delivery_radius_km,
            delivery_enabled=store.delivery_enabled,
            pickup_enabled=store.pickup_enabled,
            kiosk_enabled=store.kiosk_enabled,
            pos_enabled=store.pos_enabled,
            ecommerce_enabled=store.ecommerce_enabled,
            status=store.status.value,
            settings=store.settings,
            pos_integration=store.pos_integration,
            seo_config=store.seo_config,
            location=store.location.to_dict() if store.location else None,
            created_at=store.created_at,
            updated_at=store.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating store: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create store")


@router.get("/{store_id}", response_model=StoreResponse)
async def get_store(
    store_id: UUID,
    service: StoreService = Depends(get_store_service)
):
    """Get store by ID"""
    try:
        store = await service.get_store(store_id)
        if not store:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
        
        return StoreResponse(
            id=store.id,
            tenant_id=store.tenant_id,
            province_territory_id=store.province_territory_id,
            store_code=store.store_code,
            name=store.name,
            address=store.address.to_dict() if store.address else None,
            phone=store.phone,
            email=store.email,
            hours=store.hours,
            timezone=store.timezone,
            license_number=store.license_number,
            license_expiry=store.license_expiry,
            tax_rate=float(store.tax_rate),
            delivery_radius_km=store.delivery_radius_km,
            delivery_enabled=store.delivery_enabled,
            pickup_enabled=store.pickup_enabled,
            kiosk_enabled=store.kiosk_enabled,
            pos_enabled=store.pos_enabled,
            ecommerce_enabled=store.ecommerce_enabled,
            status=store.status.value,
            settings=store.settings,
            pos_integration=store.pos_integration,
            seo_config=store.seo_config,
            location=store.location.to_dict() if store.location else None,
            created_at=store.created_at,
            updated_at=store.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting store: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get store")


@router.get("/by-code/{code}", response_model=StoreResponse)
async def get_store_by_code(
    code: str,
    service: StoreService = Depends(get_store_service)
):
    """Get store by store code"""
    try:
        # Use the service to find the store instead of direct DB access
        stores = await service.get_stores_by_tenant(None)  # Get all stores

        # Find the store with matching code
        store = None
        for s in stores:
            if s.store_code == code:
                store = s
                break

        if store:
            # Return the store found via service
            return store

        # Try direct DB query as fallback
        pool = await get_db_pool()

        query = """
            SELECT
                id, tenant_id, province_territory_id, store_code, name,
                address, phone, email, hours, timezone,
                license_number, license_expiry, tax_rate,
                delivery_radius_km, delivery_enabled, pickup_enabled,
                kiosk_enabled, pos_enabled, ecommerce_enabled,
                status, settings, pos_integration, seo_config,
                location, created_at, updated_at
            FROM stores
            WHERE store_code = $1
        """

        async with pool.acquire() as conn:
            result = await conn.fetchrow(query, code)

        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Store with code '{code}' not found")

        # Parse the result
        store_data = dict(result)

        return StoreResponse(
            id=store_data['id'],
            tenant_id=store_data['tenant_id'],
            province_territory_id=store_data['province_territory_id'],
            store_code=store_data['store_code'],
            name=store_data['name'],
            address=store_data['address'],
            phone=store_data['phone'],
            email=store_data['email'],
            hours=store_data['hours'],
            timezone=store_data['timezone'],
            license_number=store_data['license_number'],
            license_expiry=store_data['license_expiry'],
            tax_rate=float(store_data['tax_rate']) if store_data['tax_rate'] else 0.0,
            delivery_radius_km=store_data['delivery_radius_km'],
            delivery_enabled=store_data['delivery_enabled'],
            pickup_enabled=store_data['pickup_enabled'],
            kiosk_enabled=store_data['kiosk_enabled'],
            pos_enabled=store_data['pos_enabled'],
            ecommerce_enabled=store_data['ecommerce_enabled'],
            status=store_data['status'],
            settings=store_data['settings'],
            pos_integration=store_data['pos_integration'],
            seo_config=store_data['seo_config'],
            location=store_data['location'],
            created_at=store_data['created_at'],
            updated_at=store_data['updated_at']
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting store by code: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get store by code")


@router.put("/{store_id}", response_model=StoreResponse)
async def update_store(
    store_id: UUID,
    request: UpdateStoreRequest,
    service: StoreService = Depends(get_store_service)
):
    """Update store information"""
    try:
        store = await service.update_store(
            store_id=store_id,
            name=request.name,
            address=request.address.dict() if request.address else None,
            phone=request.phone,
            email=request.email,
            hours=request.hours.dict() if request.hours else None,
            timezone=request.timezone,
            license_number=request.license_number,
            license_expiry=request.license_expiry,
            delivery_radius_km=request.delivery_radius_km,
            delivery_enabled=request.delivery_enabled,
            pickup_enabled=request.pickup_enabled,
            kiosk_enabled=request.kiosk_enabled,
            pos_enabled=request.pos_enabled,
            ecommerce_enabled=request.ecommerce_enabled,
            settings=request.settings,
            pos_integration=request.pos_integration,
            seo_config=request.seo_config,
            latitude=request.latitude,
            longitude=request.longitude
        )
        
        return StoreResponse(
            id=store.id,
            tenant_id=store.tenant_id,
            province_territory_id=store.province_territory_id,
            store_code=store.store_code,
            name=store.name,
            address=store.address.to_dict() if store.address else None,
            phone=store.phone,
            email=store.email,
            hours=store.hours,
            timezone=store.timezone,
            license_number=store.license_number,
            license_expiry=store.license_expiry,
            tax_rate=float(store.tax_rate),
            delivery_radius_km=store.delivery_radius_km,
            delivery_enabled=store.delivery_enabled,
            pickup_enabled=store.pickup_enabled,
            kiosk_enabled=store.kiosk_enabled,
            pos_enabled=store.pos_enabled,
            ecommerce_enabled=store.ecommerce_enabled,
            status=store.status.value,
            settings=store.settings,
            pos_integration=store.pos_integration,
            seo_config=store.seo_config,
            location=store.location.to_dict() if store.location else None,
            created_at=store.created_at,
            updated_at=store.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating store: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update store")


@router.post("/{store_id}/suspend", response_model=StoreResponse)
async def suspend_store(
    store_id: UUID,
    request: SuspendStoreRequest,
    service: StoreService = Depends(get_store_service)
):
    """Suspend a store"""
    try:
        store = await service.suspend_store(store_id, request.reason)
        
        return StoreResponse(
            id=store.id,
            tenant_id=store.tenant_id,
            province_territory_id=store.province_territory_id,
            store_code=store.store_code,
            name=store.name,
            address=store.address.to_dict() if store.address else None,
            phone=store.phone,
            email=store.email,
            hours=store.hours,
            timezone=store.timezone,
            license_number=store.license_number,
            license_expiry=store.license_expiry,
            tax_rate=float(store.tax_rate),
            delivery_radius_km=store.delivery_radius_km,
            delivery_enabled=store.delivery_enabled,
            pickup_enabled=store.pickup_enabled,
            kiosk_enabled=store.kiosk_enabled,
            pos_enabled=store.pos_enabled,
            ecommerce_enabled=store.ecommerce_enabled,
            status=store.status.value,
            settings=store.settings,
            pos_integration=store.pos_integration,
            seo_config=store.seo_config,
            location=store.location.to_dict() if store.location else None,
            created_at=store.created_at,
            updated_at=store.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error suspending store: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to suspend store")


@router.post("/{store_id}/reactivate", response_model=StoreResponse)
async def reactivate_store(
    store_id: UUID,
    service: StoreService = Depends(get_store_service)
):
    """Reactivate a suspended store"""
    try:
        store = await service.reactivate_store(store_id)
        
        return StoreResponse(
            id=store.id,
            tenant_id=store.tenant_id,
            province_territory_id=store.province_territory_id,
            store_code=store.store_code,
            name=store.name,
            address=store.address.to_dict() if store.address else None,
            phone=store.phone,
            email=store.email,
            hours=store.hours,
            timezone=store.timezone,
            license_number=store.license_number,
            license_expiry=store.license_expiry,
            tax_rate=float(store.tax_rate),
            delivery_radius_km=store.delivery_radius_km,
            delivery_enabled=store.delivery_enabled,
            pickup_enabled=store.pickup_enabled,
            kiosk_enabled=store.kiosk_enabled,
            pos_enabled=store.pos_enabled,
            ecommerce_enabled=store.ecommerce_enabled,
            status=store.status.value,
            settings=store.settings,
            pos_integration=store.pos_integration,
            seo_config=store.seo_config,
            location=store.location.to_dict() if store.location else None,
            created_at=store.created_at,
            updated_at=store.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error reactivating store: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reactivate store")


@router.post("/{store_id}/close", response_model=StoreResponse)
async def close_store(
    store_id: UUID,
    service: StoreService = Depends(get_store_service)
):
    """Permanently close a store"""
    try:
        store = await service.close_store(store_id)
        
        return StoreResponse(
            id=store.id,
            tenant_id=store.tenant_id,
            province_territory_id=store.province_territory_id,
            store_code=store.store_code,
            name=store.name,
            address=store.address.to_dict() if store.address else None,
            phone=store.phone,
            email=store.email,
            hours=store.hours,
            timezone=store.timezone,
            license_number=store.license_number,
            license_expiry=store.license_expiry,
            tax_rate=float(store.tax_rate),
            delivery_radius_km=store.delivery_radius_km,
            delivery_enabled=store.delivery_enabled,
            pickup_enabled=store.pickup_enabled,
            kiosk_enabled=store.kiosk_enabled,
            pos_enabled=store.pos_enabled,
            ecommerce_enabled=store.ecommerce_enabled,
            status=store.status.value,
            settings=store.settings,
            pos_integration=store.pos_integration,
            seo_config=store.seo_config,
            location=store.location.to_dict() if store.location else None,
            created_at=store.created_at,
            updated_at=store.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error closing store: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to close store")


@router.get("/tenant/active", response_model=List[StoreResponse])
async def get_active_stores_by_tenant(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service: StoreService = Depends(get_store_service),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Get active stores for authenticated user based on their role:
    - Super Admin: Can see all active stores
    - Tenant Admin: Can see all stores for their tenant(s)
    - Store Manager: Can see only their assigned store(s)
    """
    try:
        # Decode the JWT token to get user info
        token = credentials.credentials
        payload = decode_token(token)
        user_id = UUID(payload['user_id'])
        user = None  # Initialize user variable
        
        async with db_pool.acquire() as conn:
            # Fetch user data with their role and associations
            user = await conn.fetchrow("""
                SELECT id, email, role, tenant_id, store_id
                FROM users
                WHERE id = $1
            """, user_id)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            stores = []
            
            # Super Admin - can see all active stores
            if user['role'] == 'super_admin':
                stores = await service.list_stores_by_tenant(
                    tenant_id=None,
                    status=StoreStatus.ACTIVE,
                    limit=100,
                    offset=0
                )
            
            # Tenant Admin - can see all stores for their tenant
            elif user['role'] == 'tenant_admin' and user['tenant_id']:
                # Get stores for the tenant
                stores = await service.list_stores_by_tenant(
                    tenant_id=user['tenant_id'],
                    status=StoreStatus.ACTIVE,
                    limit=100,
                    offset=0
                )
            
            # Store Manager - can see only their assigned store
            elif user['role'] == 'store_manager':
                logger.info(f"Store manager {user_id} fetching stores, store_id: {user.get('store_id')}")
                # Get stores the user has access to based on their store_id
                if user.get('store_id'):
                    store_records = await conn.fetch("""
                        SELECT * FROM stores
                        WHERE id = $1 AND status = 'active'
                    """, user['store_id'])
                    logger.info(f"Found {len(store_records)} store records for store manager")
                else:
                    store_records = []
                    logger.warning(f"Store manager {user_id} has no store_id assigned")
                
                # Convert to Store objects
                for record in store_records:
                    from core.domain.models import Store, Address, GeoLocation
                    import json

                    # Handle address field - could be dict or JSON string
                    address_data = record.get('address')
                    if address_data:
                        if isinstance(address_data, str):
                            address_data = json.loads(address_data)
                        address = Address(**address_data)
                    else:
                        address = None

                    # Handle JSON fields that might be strings
                    def parse_json_field(value, default=None):
                        if value is None:
                            return default or {}
                        if isinstance(value, str):
                            try:
                                return json.loads(value)
                            except json.JSONDecodeError:
                                return default or {}
                        return value

                    # Handle location if it exists
                    location = None
                    if record.get('latitude') and record.get('longitude'):
                        location = GeoLocation(
                            latitude=Decimal(str(record['latitude'])),
                            longitude=Decimal(str(record['longitude']))
                        )
                    
                    store = Store(
                        id=record['id'],
                        tenant_id=record['tenant_id'],
                        province_territory_id=record['province_territory_id'],
                        store_code=record['store_code'],
                        name=record['name'],
                        address=address,
                        phone=record.get('phone'),
                        email=record.get('email'),
                        hours=parse_json_field(record.get('hours'), {}),
                        timezone=record.get('timezone', 'America/Toronto'),
                        license_number=record.get('license_number'),
                        license_expiry=record.get('license_expiry'),
                        tax_rate=Decimal(str(record.get('tax_rate', 0.13))),
                        delivery_radius_km=record.get('delivery_radius_km', 0),
                        delivery_enabled=record.get('delivery_enabled', False),
                        pickup_enabled=record.get('pickup_enabled', True),
                        kiosk_enabled=record.get('kiosk_enabled', False),
                        pos_enabled=record.get('pos_enabled', True),
                        ecommerce_enabled=record.get('ecommerce_enabled', False),
                        status=StoreStatus(record.get('status', 'active')),
                        settings=parse_json_field(record.get('settings'), {}),
                        pos_integration=parse_json_field(record.get('pos_integration'), {}),
                        seo_config=parse_json_field(record.get('seo_config'), {}),
                        location=location,
                        created_at=record['created_at'],
                        updated_at=record['updated_at']
                    )
                    stores.append(store)
        
        return [
            StoreResponse(
                id=store.id,
                tenant_id=store.tenant_id,
                province_territory_id=store.province_territory_id,
                store_code=store.store_code,
                name=store.name,
                address=store.address.to_dict() if store.address else None,
                phone=store.phone,
                email=store.email,
                hours=store.hours or {},
                timezone=store.timezone,
                license_number=store.license_number,
                license_expiry=store.license_expiry,
                tax_rate=float(store.tax_rate),
                delivery_radius_km=store.delivery_radius_km,
                delivery_enabled=store.delivery_enabled,
                pickup_enabled=store.pickup_enabled,
                kiosk_enabled=store.kiosk_enabled,
                pos_enabled=store.pos_enabled,
                ecommerce_enabled=store.ecommerce_enabled,
                status=store.status.value,
                settings=store.settings or {},
                pos_integration=store.pos_integration or {},
                seo_config=store.seo_config or {},
                location=store.location.to_dict() if store.location else None,
                created_at=store.created_at,
                updated_at=store.updated_at
            )
            for store in stores
        ]
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the full error for debugging
        error_message = str(e)
        if "validation error" in error_message.lower():
            # Log the full validation error details
            logger.error(f"Validation error details: {e}")
        logger.error(f"Error getting active stores for user {user_id}: {error_message}\n{traceback.format_exc()}")

        # Only treat actual permission errors as 403
        if "permission denied" in error_message.lower() or "unauthorized" in error_message.lower():
            logger.warning(f"Permission denied for user {user_id}: {error_message}")
            # Provide specific error based on user role
            if user and user.get('role') == 'store_manager':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Store managers do not have permission to view tenants. You can only access your assigned store."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: Your role ({user.get('role', 'unknown')}) does not have permission for this action."
                )

        # Check for validation errors
        if "validation error" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Data validation error: {error_message}"
            )
        
        # Generic error with more context
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to retrieve stores: {error_message}"
        )


@router.get("/tenant/{tenant_id}", response_model=List[StoreResponse])
async def list_stores_by_tenant(
    tenant_id: UUID,
    status: Optional[StoreStatus] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: StoreService = Depends(get_store_service)
):
    """List stores for a tenant"""
    try:
        stores = await service.list_stores_by_tenant(
            tenant_id=tenant_id,
            status=status,
            limit=limit,
            offset=offset
        )
        
        return [
            StoreResponse(
                id=store.id,
                tenant_id=store.tenant_id,
                province_territory_id=store.province_territory_id,
                store_code=store.store_code,
                name=store.name,
                address=store.address.to_dict() if store.address else None,
                phone=store.phone,
                email=store.email,
                hours=store.hours or {},
                timezone=store.timezone,
                license_number=store.license_number,
                license_expiry=store.license_expiry,
                tax_rate=float(store.tax_rate),
                delivery_radius_km=store.delivery_radius_km,
                delivery_enabled=store.delivery_enabled,
                pickup_enabled=store.pickup_enabled,
                kiosk_enabled=store.kiosk_enabled,
                pos_enabled=store.pos_enabled,
                ecommerce_enabled=store.ecommerce_enabled,
                status=store.status.value,
                settings=store.settings or {},
                pos_integration=store.pos_integration or {},
                seo_config=store.seo_config or {},
                location=store.location.to_dict() if store.location else None,
                created_at=store.created_at,
                updated_at=store.updated_at
            )
            for store in stores
        ]
        
    except Exception as e:
        logger.error(f"Error listing stores: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list stores")


@router.get("/{store_id}/validate-license")
async def validate_license(
    store_id: UUID,
    service: StoreService = Depends(get_store_service)
):
    """Validate store license"""
    try:
        is_valid = await service.validate_license(store_id)
        return {"license_valid": is_valid}
        
    except Exception as e:
        logger.error(f"Error validating license: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to validate license")


# =====================================================
# LOCATION-BASED ENDPOINTS
# =====================================================

from core.services.location_service import LocationService, Coordinates, DistanceUnit
from fastapi import Request, Header


class NearestStoresRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    limit: int = Field(default=5, ge=1, le=20)
    max_distance_km: float = Field(default=50.0, ge=1, le=200)


class NearestStoreResponse(BaseModel):
    store_id: UUID
    tenant_id: UUID
    store_name: str
    store_code: str
    distance_km: float
    bearing: float
    address: Dict[str, Any]
    phone: Optional[str]
    email: Optional[str]
    hours: Dict[str, Any]
    delivery_enabled: bool
    pickup_enabled: bool
    delivery_radius_km: int
    estimated_time_minutes: Optional[int] = None


class DeliveryAvailabilityRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class DeliveryAvailabilityResponse(BaseModel):
    available: bool
    distance_km: Optional[float] = None
    delivery_fee: Optional[float] = None
    minimum_order: Optional[float] = None
    estimated_minutes_min: Optional[int] = None
    estimated_minutes_max: Optional[int] = None
    zone_name: Optional[str] = None
    message: Optional[str] = None


class StoreInventoryStats(BaseModel):
    """Store inventory statistics"""
    total_skus: int
    total_quantity: int
    low_stock_items: int
    out_of_stock_items: int
    total_value: float


async def get_location_service() -> LocationService:
    """Dependency to get location service"""
    pool = await get_db_pool()
    return LocationService(pool)


@router.post("/nearest", response_model=List[NearestStoreResponse])
async def find_nearest_stores(
    request_data: NearestStoresRequest,
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant ID"),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-Id"),
    request: Request = None,
    service: LocationService = Depends(get_location_service)
):
    """
    Find nearest stores to given coordinates
    
    This endpoint finds the nearest stores based on geographic location.
    It uses PostGIS spatial queries for efficient distance calculations.
    """
    try:
        # Use tenant ID from header if not provided in query
        effective_tenant_id = tenant_id or (UUID(x_tenant_id) if x_tenant_id else None)
        
        # Create coordinates object
        customer_location = Coordinates(
            latitude=request_data.latitude,
            longitude=request_data.longitude
        )
        
        # Find nearest stores
        stores = await service.find_nearest_stores(
            customer_location=customer_location,
            tenant_id=str(effective_tenant_id) if effective_tenant_id else None,
            limit=request_data.limit,
            max_distance_km=request_data.max_distance_km
        )
        
        # Log access for analytics
        session_id = request.headers.get("X-Session-Id") if request else None
        await service.log_location_access(
            user_id=None,  # Could get from auth if implemented
            session_id=session_id,
            action="search",
            customer_location=customer_location,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("User-Agent") if request else None
        )
        
        # Map to response model
        return [
            NearestStoreResponse(
                store_id=store['store_id'],
                tenant_id=store['tenant_id'],
                store_name=store['store_name'],
                store_code=store['store_code'],
                distance_km=store['distance_km'],
                bearing=store.get('bearing', 0),
                address=store['address'],
                phone=store['phone'],
                email=store['email'],
                hours=store['hours'],
                delivery_enabled=store['delivery_enabled'],
                pickup_enabled=store['pickup_enabled'],
                delivery_radius_km=store['delivery_radius_km'],
                estimated_time_minutes=30 + int(store['distance_km'] * 2)  # Simple estimate
            )
            for store in stores
        ]
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error finding nearest stores: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to find nearest stores"
        )


@router.get("/{store_id}/delivery-availability", response_model=DeliveryAvailabilityResponse)
async def check_delivery_availability(
    store_id: UUID,
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    request: Request = None,
    service: LocationService = Depends(get_location_service)
):
    """
    Check if delivery is available from store to given location
    
    This endpoint checks delivery availability based on store's delivery zones
    and radius configuration.
    """
    try:
        # Create coordinates object
        customer_location = Coordinates(latitude=latitude, longitude=longitude)
        
        # Check delivery availability
        result = await service.check_delivery_availability(
            store_id=str(store_id),
            customer_location=customer_location
        )
        
        # Log access
        session_id = request.headers.get("X-Session-Id") if request else None
        await service.log_location_access(
            user_id=None,
            session_id=session_id,
            action="delivery_check",
            customer_location=customer_location,
            store_id=str(store_id),
            distance_km=result.get('distance_km'),
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("User-Agent") if request else None
        )
        
        # Build response
        response = DeliveryAvailabilityResponse(
            available=result['available'],
            distance_km=result.get('distance_km'),
            delivery_fee=result.get('delivery_fee'),
            minimum_order=result.get('minimum_order'),
            estimated_minutes_min=result.get('estimated_minutes_min'),
            estimated_minutes_max=result.get('estimated_minutes_max'),
            zone_name=result.get('zone_name')
        )
        
        # Add helpful message
        if not response.available:
            if response.distance_km:
                response.message = f"Delivery not available to this location. Distance: {response.distance_km}km"
            else:
                response.message = "Delivery service not available for this store"
        else:
            response.message = f"Delivery available! Estimated time: {response.estimated_minutes_min}-{response.estimated_minutes_max} minutes"
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error checking delivery availability: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to check delivery availability"
        )


@router.post("/{store_id}/select")
async def select_store_for_session(
    store_id: UUID,
    latitude: Optional[float] = Query(None, ge=-90, le=90),
    longitude: Optional[float] = Query(None, ge=-180, le=180),
    session_id: Optional[str] = Header(None, alias="X-Session-Id"),
    request: Request = None,
    service: LocationService = Depends(get_location_service)
):
    """
    Select a store for the current session
    
    This endpoint records store selection for analytics and session management.
    """
    try:
        # Create coordinates if provided
        customer_location = None
        if latitude is not None and longitude is not None:
            customer_location = Coordinates(latitude=latitude, longitude=longitude)
        
        # Calculate distance if location provided
        distance_km = None
        if customer_location:
            # Get store location from database
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                store_data = await conn.fetchrow(
                    "SELECT latitude, longitude FROM stores WHERE id = $1",
                    store_id
                )
                if store_data and store_data['latitude'] and store_data['longitude']:
                    store_coords = Coordinates(
                        latitude=float(store_data['latitude']),
                        longitude=float(store_data['longitude'])
                    )
                    distance_km = service.calculate_distance(
                        customer_location, 
                        store_coords,
                        DistanceUnit.KILOMETERS
                    )
        
        # Log store selection
        await service.log_location_access(
            user_id=None,
            session_id=session_id,
            action="select",
            customer_location=customer_location,
            store_id=str(store_id),
            distance_km=distance_km,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("User-Agent") if request else None
        )
        
        # Store selection in session (could be Redis in production)
        return {
            "success": True,
            "store_id": str(store_id),
            "session_id": session_id,
            "distance_km": distance_km,
            "message": "Store selected successfully"
        }
        
    except Exception as e:
        logger.error(f"Error selecting store: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to select store"
        )


@router.post("/geocode")
async def geocode_address(
    street: str = Query(..., description="Street address"),
    city: str = Query(..., description="City"),
    province: str = Query(..., description="Province/State"),
    postal_code: Optional[str] = Query(None, description="Postal code"),
    country: str = Query(default="Canada", description="Country"),
    service: LocationService = Depends(get_location_service)
):
    """
    Geocode an address to coordinates
    
    This endpoint converts a street address to geographic coordinates.
    Results are cached for performance.
    """
    try:
        coordinates = await service.geocoder.geocode_address(
            address=street,
            city=city,
            province=province,
            postal_code=postal_code,
            country=country
        )
        
        if not coordinates:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Could not geocode the provided address"
            )
        
        return {
            "latitude": coordinates.latitude,
            "longitude": coordinates.longitude,
            "formatted_address": f"{street}, {city}, {province} {postal_code or ''}, {country}".strip()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error geocoding address: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to geocode address"
        )


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
                            (SELECT retail_price FROM ocs_product_catalog WHERE ocs_variant_number = si.sku LIMIT 1)
                        )), 0) as total_value
                FROM ocs_inventory si
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