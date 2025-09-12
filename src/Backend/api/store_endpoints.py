"""
Store Management API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Header, status
from typing import List, Dict, Optional, Any
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr
from decimal import Decimal
import asyncpg
import os
import logging

from core.domain.models import StoreStatus, ProvinceType
from core.services.store_service import StoreService
from core.services.tenant_service import TenantService
from core.repositories.store_repository import StoreRepository
from core.repositories.tenant_repository import TenantRepository
from core.repositories.province_repository import ProvinceRepository
from api.tenant_endpoints import get_db_pool, SubscriptionRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/stores", tags=["stores"])


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
    address: Optional[Dict[str, Any]]
    phone: Optional[str]
    email: Optional[str]
    hours: Dict[str, Any]
    timezone: str
    license_number: Optional[str]
    license_expiry: Optional[date]
    tax_rate: float
    delivery_radius_km: int
    delivery_enabled: bool
    pickup_enabled: bool
    kiosk_enabled: bool
    pos_enabled: bool
    ecommerce_enabled: bool
    status: str
    settings: Dict[str, Any]
    pos_integration: Dict[str, Any]
    seo_config: Dict[str, Any]
    location: Optional[Dict[str, float]]
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
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant ID"),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-Id"),
    service: StoreService = Depends(get_store_service)
):
    """Get active stores for a tenant"""
    try:
        # Use tenant ID from header if not provided in query
        effective_tenant_id = tenant_id or (UUID(x_tenant_id) if x_tenant_id else None)
        
        if not effective_tenant_id:
            # Return all active stores if no tenant specified
            stores = await service.list_stores_by_tenant(
                tenant_id=None,
                status=StoreStatus.ACTIVE,
                limit=100,
                offset=0
            )
        else:
            stores = await service.list_stores_by_tenant(
                tenant_id=effective_tenant_id,
                status=StoreStatus.ACTIVE,
                limit=100,
                offset=0
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
            for store in stores
        ]
        
    except Exception as e:
        logger.error(f"Error getting active stores: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get active stores")


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