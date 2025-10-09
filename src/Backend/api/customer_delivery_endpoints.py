"""
Customer-facing Delivery API endpoints
Provides public REST API for delivery zone lookup, fee calculation, and availability checks
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, List, Optional, Any
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field
import logging
from datetime import datetime

from database.connection import get_db_pool

logger = logging.getLogger(__name__)

# Create router for customer-facing delivery endpoints
# Note: Using /delivery prefix to match frontend expectations (frontend calls /delivery/*)
router = APIRouter(prefix="/delivery", tags=["customer-delivery"])


# Pydantic models for request/response
class DeliveryFeeRequest(BaseModel):
    """Request model for delivery fee calculation"""
    store_id: UUID
    address: Dict[str, Any] = Field(..., description="Delivery address with lat, lon, postal_code")
    order_subtotal: Optional[Decimal] = Field(None, description="Order subtotal for free delivery check")


class DeliveryFeeResponse(BaseModel):
    """Response model for delivery fee calculation"""
    success: bool
    delivery_fee: Decimal
    free_delivery_minimum: Optional[Decimal] = None
    is_free_delivery: bool = False
    delivery_time_minutes: int
    zone_name: str
    zone_type: str
    in_delivery_zone: bool


class DeliveryAvailabilityRequest(BaseModel):
    """Request model for delivery availability check"""
    store_id: UUID
    address: Dict[str, Any] = Field(..., description="Address with lat, lon or postal_code")


class DeliveryAvailabilityResponse(BaseModel):
    """Response model for delivery availability"""
    success: bool
    available: bool
    zone_id: Optional[UUID] = None
    zone_name: Optional[str] = None
    delivery_time_minutes: Optional[int] = None
    delivery_fee: Optional[Decimal] = None
    message: Optional[str] = None


class DeliveryZone(BaseModel):
    """Delivery zone model"""
    id: UUID
    zone_name: str
    zone_type: str
    radius_km: Optional[Decimal] = None
    postal_codes: Optional[List[str]] = None
    base_delivery_fee: Decimal
    free_delivery_minimum: Optional[Decimal] = None
    delivery_time_minutes: int
    available_days: List[int]
    delivery_hours: Optional[Dict[str, Any]] = None


@router.post("/calculate-fee", response_model=DeliveryFeeResponse)
async def calculate_delivery_fee(
    request: DeliveryFeeRequest
):
    """
    Calculate delivery fee for a given address and store

    This endpoint checks if the address is within any delivery zone for the store
    and calculates the appropriate delivery fee based on distance, zone type, and order subtotal.

    Args:
        request: DeliveryFeeRequest containing store_id, address, and optional order_subtotal

    Returns:
        DeliveryFeeResponse with calculated fee, delivery time, and zone information
    """
    try:
        store_id = request.store_id
        address = request.address
        order_subtotal = request.order_subtotal or Decimal("0")

        # Extract address components
        lat = address.get('lat') or address.get('latitude')
        lon = address.get('lon') or address.get('longitude') or address.get('lng')
        postal_code = address.get('postal_code') or address.get('postalCode')

        if not lat or not lon:
            raise HTTPException(
                status_code=400,
                detail="Address must include latitude and longitude coordinates"
            )

        # Find matching delivery zone
        # Priority: 1) Postal code exact match, 2) Radius-based, 3) Polygon-based
        query = """
        WITH address_point AS (
            SELECT ST_SetSRID(ST_MakePoint($2::float, $1::float), 4326) as point
        )
        SELECT
            dz.id,
            dz.zone_name,
            dz.zone_type,
            dz.radius_km,
            dz.base_delivery_fee,
            dz.free_delivery_minimum,
            dz.delivery_time_minutes,
            dz.postal_codes,
            CASE
                WHEN dz.zone_type = 'postal_codes' AND $3 = ANY(dz.postal_codes) THEN 1
                WHEN dz.zone_type = 'radius' AND
                     ST_DWithin(
                        ST_Transform(ST_SetSRID(ST_MakePoint(s.longitude, s.latitude), 4326), 3857),
                        ST_Transform((SELECT point FROM address_point), 3857),
                        dz.radius_km * 1000
                     ) THEN 2
                WHEN dz.zone_type = 'polygon' AND
                     ST_Contains(
                        ST_GeomFromGeoJSON(dz.polygon_coordinates::text),
                        (SELECT point FROM address_point)
                     ) THEN 3
                ELSE 999
            END as match_priority,
            ST_Distance(
                ST_Transform(ST_SetSRID(ST_MakePoint(s.longitude, s.latitude), 4326), 3857),
                ST_Transform((SELECT point FROM address_point), 3857)
            ) / 1000 as distance_km
        FROM delivery_zones dz
        JOIN stores s ON s.id = dz.store_id
        WHERE dz.store_id = $4
          AND dz.is_active = true
        ORDER BY match_priority ASC, distance_km ASC
        LIMIT 1
        """

        pool = await get_db_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchrow(
                query,
                lat, lon, postal_code, str(store_id)
            )

        if not result:
            # No delivery zone found - address is outside delivery area
            return DeliveryFeeResponse(
                success=True,
                delivery_fee=Decimal("0"),
                is_free_delivery=False,
                delivery_time_minutes=0,
                zone_name="Outside Delivery Area",
                zone_type="none",
                in_delivery_zone=False
            )

        # Calculate delivery fee
        base_fee = Decimal(str(result['base_delivery_fee']))
        free_delivery_min = Decimal(str(result['free_delivery_minimum'])) if result['free_delivery_minimum'] else None
        delivery_time = result['delivery_time_minutes'] or 60

        # Check if order qualifies for free delivery
        is_free_delivery = False
        if free_delivery_min and order_subtotal >= free_delivery_min:
            is_free_delivery = True
            base_fee = Decimal("0")

        return DeliveryFeeResponse(
            success=True,
            delivery_fee=base_fee,
            free_delivery_minimum=free_delivery_min,
            is_free_delivery=is_free_delivery,
            delivery_time_minutes=delivery_time,
            zone_name=result['zone_name'],
            zone_type=result['zone_type'],
            in_delivery_zone=True
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating delivery fee: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calculating delivery fee: {str(e)}")


@router.post("/check-availability", response_model=DeliveryAvailabilityResponse)
async def check_delivery_availability(
    request: DeliveryAvailabilityRequest
):
    """
    Check if delivery is available for a given address

    This endpoint verifies if the address falls within any active delivery zone
    for the specified store, and returns availability details.

    Args:
        request: DeliveryAvailabilityRequest with store_id and address

    Returns:
        DeliveryAvailabilityResponse with availability status and zone details
    """
    try:
        store_id = request.store_id
        address = request.address

        # Extract address components
        lat = address.get('lat') or address.get('latitude')
        lon = address.get('lon') or address.get('longitude') or address.get('lng')
        postal_code = address.get('postal_code') or address.get('postalCode')

        if not lat and not lon and not postal_code:
            raise HTTPException(
                status_code=400,
                detail="Address must include coordinates (lat/lon) or postal code"
            )

        # Check delivery availability
        query = """
        WITH address_point AS (
            SELECT ST_SetSRID(ST_MakePoint($2::float, $1::float), 4326) as point
        )
        SELECT
            dz.id,
            dz.zone_name,
            dz.delivery_time_minutes,
            dz.base_delivery_fee,
            dz.zone_type
        FROM delivery_zones dz
        JOIN stores s ON s.id = dz.store_id
        WHERE dz.store_id = $4
          AND dz.is_active = true
          AND (
              (dz.zone_type = 'postal_codes' AND $3 = ANY(dz.postal_codes))
              OR
              (dz.zone_type = 'radius' AND
               ST_DWithin(
                  ST_Transform(ST_SetSRID(ST_MakePoint(s.longitude, s.latitude), 4326), 3857),
                  ST_Transform((SELECT point FROM address_point), 3857),
                  dz.radius_km * 1000
               ))
              OR
              (dz.zone_type = 'polygon' AND
               ST_Contains(
                  ST_GeomFromGeoJSON(dz.polygon_coordinates::text),
                  (SELECT point FROM address_point)
               ))
          )
        LIMIT 1
        """

        pool = await get_db_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchrow(
                query,
                lat or 0, lon or 0, postal_code, str(store_id)
            )

        if result:
            return DeliveryAvailabilityResponse(
                success=True,
                available=True,
                zone_id=result['id'],
                zone_name=result['zone_name'],
                delivery_time_minutes=result['delivery_time_minutes'],
                delivery_fee=Decimal(str(result['base_delivery_fee'])),
                message="Delivery available in your area"
            )
        else:
            return DeliveryAvailabilityResponse(
                success=True,
                available=False,
                message="Sorry, delivery is not available in your area"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking delivery availability: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error checking availability: {str(e)}")


@router.get("/zones/{store_id}", response_model=List[DeliveryZone])
async def get_delivery_zones(
    store_id: UUID
):
    """
    Get all active delivery zones for a store

    Returns a list of delivery zones with their configuration, including:
    - Zone boundaries (radius, postal codes, or polygon)
    - Delivery fees
    - Free delivery thresholds
    - Estimated delivery times
    - Operating hours

    Args:
        store_id: UUID of the store

    Returns:
        List of DeliveryZone objects
    """
    try:
        query = """
        SELECT
            id,
            zone_name,
            zone_type,
            radius_km,
            postal_codes,
            base_delivery_fee,
            free_delivery_minimum,
            delivery_time_minutes,
            available_days,
            delivery_hours
        FROM delivery_zones
        WHERE store_id = $1
          AND is_active = true
        ORDER BY zone_name
        """

        pool = await get_db_pool()
        async with pool.acquire() as conn:
            results = await conn.fetch(query, str(store_id))

        zones = []
        for row in results:
            zones.append(DeliveryZone(
                id=row['id'],
                zone_name=row['zone_name'],
                zone_type=row['zone_type'],
                radius_km=Decimal(str(row['radius_km'])) if row['radius_km'] else None,
                postal_codes=row['postal_codes'],
                base_delivery_fee=Decimal(str(row['base_delivery_fee'])),
                free_delivery_minimum=Decimal(str(row['free_delivery_minimum'])) if row['free_delivery_minimum'] else None,
                delivery_time_minutes=row['delivery_time_minutes'] or 60,
                available_days=row['available_days'] or [0, 1, 2, 3, 4, 5, 6],
                delivery_hours=row['delivery_hours']
            ))

        return zones

    except Exception as e:
        logger.error(f"Error fetching delivery zones: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching delivery zones: {str(e)}")


# Export router
__all__ = ['router']
