"""
Shelf Location API Endpoints
Handles warehouse shelf location management and inventory placement
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Header, Body
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field
from decimal import Decimal
import logging

from services.shelf_location_service import (
    ShelfLocationService,
    LocationType,
    MovementType,
    create_shelf_location_service
)
from database.connection import get_db_pool

logger = logging.getLogger(__name__)

# =====================================================
# Router Configuration
# =====================================================

router = APIRouter(
    prefix="/api/shelf-locations",
    tags=["shelf-locations"],
    responses={
        404: {"description": "Not found"},
        403: {"description": "Forbidden - Store access denied"},
        400: {"description": "Bad request"},
    }
)

# =====================================================
# Request/Response Models
# =====================================================

class CreateLocationRequest(BaseModel):
    """Request model for creating a shelf location"""
    zone: str = Field(..., min_length=1, max_length=50)
    aisle: Optional[str] = Field(None, max_length=50)
    shelf: Optional[str] = Field(None, max_length=50)
    bin: Optional[str] = Field(None, max_length=50)
    location_type: str = Field(default="standard")
    max_weight_kg: Optional[float] = Field(None, gt=0)
    max_volume_m3: Optional[float] = Field(None, gt=0)
    temperature_range: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class AssignInventoryRequest(BaseModel):
    """Request model for assigning inventory to location"""
    sku: str = Field(..., min_length=1)
    location_id: UUID
    quantity: int = Field(..., gt=0)
    batch_lot: Optional[str] = None
    is_primary: bool = False


class TransferInventoryRequest(BaseModel):
    """Request model for transferring inventory between locations"""
    sku: str = Field(..., min_length=1)
    from_location_id: UUID
    to_location_id: UUID
    quantity: int = Field(..., gt=0)
    batch_lot: Optional[str] = None
    notes: Optional[str] = None


class PickInventoryRequest(BaseModel):
    """Request model for picking inventory from location"""
    sku: str = Field(..., min_length=1)
    location_id: UUID
    quantity: int = Field(..., gt=0)
    batch_lot: Optional[str] = None
    order_id: Optional[UUID] = None


class LocationResponse(BaseModel):
    """Response model for shelf location"""
    id: UUID
    store_id: UUID
    zone: str
    aisle: Optional[str]
    shelf: Optional[str]
    bin: Optional[str]
    location_code: str
    location_type: str
    max_weight_kg: Optional[float]
    max_volume_m3: Optional[float]
    temperature_range: Optional[str]
    is_active: bool
    is_available: bool
    notes: Optional[str]


class InventoryLocationResponse(BaseModel):
    """Response model for inventory location assignment"""
    id: UUID
    sku: str
    quantity: int
    batch_lot: Optional[str]
    is_primary: bool
    location_code: str
    zone: str
    aisle: Optional[str]
    shelf: Optional[str]
    bin: Optional[str]
    location_type: str


# =====================================================
# Dependency Injection
# =====================================================

async def get_shelf_location_service() -> ShelfLocationService:
    """Dependency to get shelf location service instance"""
    db_pool = await get_db_pool()
    return create_shelf_location_service(db_pool)


async def verify_store_access(
    x_store_id: Optional[str] = Header(None, alias="X-Store-ID")
) -> UUID:
    """
    Verify store access and return validated store ID
    
    Args:
        x_store_id: Store ID from header
        
    Returns:
        Validated store UUID
        
    Raises:
        HTTPException if no valid store ID
    """
    if not x_store_id:
        raise HTTPException(
            status_code=400,
            detail="Store context required. Please provide X-Store-ID header"
        )
    
    try:
        return UUID(x_store_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid store ID in header")


# =====================================================
# Location Management Endpoints
# =====================================================

@router.post("/locations", response_model=Dict[str, Any])
async def create_location(
    request: CreateLocationRequest,
    store_id: UUID = Depends(verify_store_access),
    service: ShelfLocationService = Depends(get_shelf_location_service)
):
    """
    Create a new shelf location
    
    Args:
        request: Location details
        store_id: Store UUID from header
        
    Returns:
        Created location ID
    """
    try:
        location_type = LocationType(request.location_type)
        location_id = await service.create_location(
            store_id=store_id,
            zone=request.zone,
            aisle=request.aisle,
            shelf=request.shelf,
            bin=request.bin,
            location_type=location_type,
            max_weight_kg=request.max_weight_kg,
            max_volume_m3=request.max_volume_m3,
            temperature_range=request.temperature_range,
            notes=request.notes
        )
        
        return {
            'id': str(location_id),
            'message': 'Location created successfully'
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating location: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/locations/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: UUID,
    store_id: UUID = Depends(verify_store_access),
    service: ShelfLocationService = Depends(get_shelf_location_service)
):
    """
    Get shelf location details
    
    Args:
        location_id: Location UUID
        store_id: Store UUID from header
        
    Returns:
        Location details
    """
    try:
        location = await service.get_location(location_id)
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")
        
        # Verify location belongs to store
        if location['store_id'] != store_id:
            raise HTTPException(status_code=403, detail="Access denied to this location")
        
        return LocationResponse(**location)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting location: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/locations", response_model=Dict[str, Any])
async def list_locations(
    store_id: UUID = Depends(verify_store_access),
    location_type: Optional[str] = Query(None),
    is_available: Optional[bool] = Query(None),
    zone: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service: ShelfLocationService = Depends(get_shelf_location_service)
):
    """
    List shelf locations with filters
    
    Args:
        store_id: Store UUID from header
        location_type: Filter by location type
        is_available: Filter by availability
        zone: Filter by zone
        limit: Number of records to return
        offset: Number of records to skip
        
    Returns:
        Paginated location list
    """
    try:
        loc_type = LocationType(location_type) if location_type else None
        locations, total = await service.list_locations(
            store_id=store_id,
            location_type=loc_type,
            is_available=is_available,
            zone=zone,
            limit=limit,
            offset=offset
        )
        
        return {
            'items': [LocationResponse(**loc) for loc in locations],
            'total': total,
            'limit': limit,
            'offset': offset
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing locations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/locations/{location_id}/availability")
async def update_location_availability(
    location_id: UUID,
    is_available: bool = Body(...),
    store_id: UUID = Depends(verify_store_access),
    service: ShelfLocationService = Depends(get_shelf_location_service)
):
    """
    Update location availability status
    
    Args:
        location_id: Location UUID
        is_available: New availability status
        store_id: Store UUID from header
        
    Returns:
        Success status
    """
    try:
        success = await service.update_location_availability(location_id, is_available)
        if not success:
            raise HTTPException(status_code=404, detail="Location not found")
        
        return {'message': f'Location availability updated to {is_available}'}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating location availability: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# Inventory Assignment Endpoints
# =====================================================

@router.post("/assign-inventory")
async def assign_inventory_to_location(
    request: AssignInventoryRequest,
    store_id: UUID = Depends(verify_store_access),
    service: ShelfLocationService = Depends(get_shelf_location_service)
):
    """
    Assign inventory to a shelf location
    
    Args:
        request: Assignment details
        store_id: Store UUID from header
        
    Returns:
        Assignment ID
    """
    try:
        assignment_id = await service.assign_inventory_to_location(
            store_id=store_id,
            sku=request.sku,
            location_id=request.location_id,
            quantity=request.quantity,
            batch_lot=request.batch_lot,
            is_primary=request.is_primary
        )
        
        return {
            'id': str(assignment_id),
            'message': f'Assigned {request.quantity} units of {request.sku} to location'
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error assigning inventory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transfer-inventory")
async def transfer_inventory(
    request: TransferInventoryRequest,
    store_id: UUID = Depends(verify_store_access),
    service: ShelfLocationService = Depends(get_shelf_location_service)
):
    """
    Transfer inventory between locations
    
    Args:
        request: Transfer details
        store_id: Store UUID from header
        
    Returns:
        Success status
    """
    try:
        success = await service.transfer_inventory(
            store_id=store_id,
            sku=request.sku,
            from_location_id=request.from_location_id,
            to_location_id=request.to_location_id,
            quantity=request.quantity,
            batch_lot=request.batch_lot,
            notes=request.notes
        )
        
        if success:
            return {
                'message': f'Transferred {request.quantity} units of {request.sku}'
            }
        else:
            raise HTTPException(status_code=400, detail="Transfer failed")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error transferring inventory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pick-inventory")
async def pick_inventory(
    request: PickInventoryRequest,
    store_id: UUID = Depends(verify_store_access),
    service: ShelfLocationService = Depends(get_shelf_location_service)
):
    """
    Pick inventory from location (for orders)
    
    Args:
        request: Pick details
        store_id: Store UUID from header
        
    Returns:
        Success status
    """
    try:
        success = await service.pick_inventory(
            store_id=store_id,
            sku=request.sku,
            location_id=request.location_id,
            quantity=request.quantity,
            batch_lot=request.batch_lot,
            reference_id=request.order_id
        )
        
        if success:
            return {
                'message': f'Picked {request.quantity} units of {request.sku}'
            }
        else:
            raise HTTPException(status_code=400, detail="Pick failed")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error picking inventory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inventory-locations", response_model=List[InventoryLocationResponse])
async def get_inventory_locations(
    store_id: UUID = Depends(verify_store_access),
    sku: Optional[str] = Query(None),
    location_id: Optional[UUID] = Query(None),
    batch_lot: Optional[str] = Query(None),
    service: ShelfLocationService = Depends(get_shelf_location_service)
):
    """
    Get inventory location assignments
    
    Args:
        store_id: Store UUID from header
        sku: Filter by SKU
        location_id: Filter by location
        batch_lot: Filter by batch
        
    Returns:
        List of inventory location assignments
    """
    try:
        locations = await service.get_inventory_locations(
            store_id=store_id,
            sku=sku,
            location_id=location_id,
            batch_lot=batch_lot
        )
        
        return [InventoryLocationResponse(**loc) for loc in locations]
    except Exception as e:
        logger.error(f"Error getting inventory locations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggest-location/{sku}")
async def suggest_location_for_sku(
    sku: str,
    quantity: int = Query(..., gt=0),
    store_id: UUID = Depends(verify_store_access),
    service: ShelfLocationService = Depends(get_shelf_location_service)
):
    """
    Suggest best location for storing an SKU
    
    Args:
        sku: Product SKU
        quantity: Quantity to store
        store_id: Store UUID from header
        
    Returns:
        Suggested location ID
    """
    try:
        location_id = await service.suggest_location_for_sku(
            store_id=store_id,
            sku=sku,
            quantity=quantity
        )
        
        if location_id:
            location = await service.get_location(location_id)
            return {
                'location_id': str(location_id),
                'location_code': location['location_code'],
                'message': f'Suggested location for {sku}'
            }
        else:
            return {
                'location_id': None,
                'message': 'No suitable location found'
            }
    except Exception as e:
        logger.error(f"Error suggesting location: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/movement-history")
async def get_movement_history(
    store_id: UUID = Depends(verify_store_access),
    sku: Optional[str] = Query(None),
    location_id: Optional[UUID] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    service: ShelfLocationService = Depends(get_shelf_location_service)
):
    """
    Get inventory movement history
    
    Args:
        store_id: Store UUID from header
        sku: Filter by SKU
        location_id: Filter by location
        limit: Number of records to return
        
    Returns:
        Movement history list
    """
    try:
        history = await service.get_movement_history(
            store_id=store_id,
            sku=sku,
            location_id=location_id,
            limit=limit
        )
        
        return {
            'items': history,
            'total': len(history)
        }
    except Exception as e:
        logger.error(f"Error getting movement history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# Export Router
# =====================================================

def get_router() -> APIRouter:
    """Get configured router instance"""
    return router