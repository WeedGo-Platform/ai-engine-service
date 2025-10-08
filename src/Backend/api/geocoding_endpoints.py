"""
Geocoding and Address Autocomplete API Endpoints
Public endpoints for address search and geocoding using Mapbox
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import logging
import os

from services.geocoding.mapbox_service import MapboxGeocodingService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/geocoding", tags=["geocoding"])

# Initialize Mapbox service
mapbox_service = None


def get_mapbox_service() -> MapboxGeocodingService:
    """Get or create Mapbox geocoding service instance"""
    global mapbox_service
    if mapbox_service is None:
        api_key = os.getenv('MAPBOX_API_KEY', 'pk.eyJ1IjoiY2hhcnJjeSIsImEiOiJja2llcXF5eXcxNWx4MnlxeHAzbmJnY3g2In0.FC98EHBZh2apYVTNiuyNKg')
        mapbox_service = MapboxGeocodingService(api_key=api_key)
        logger.info("Initialized Mapbox geocoding service")
    return mapbox_service


# Pydantic Models
class AddressAutocompleteResponse(BaseModel):
    """Address autocomplete suggestion"""
    id: str
    place_name: str
    address: Dict[str, str]  # {street, city, province, postal_code, country}
    coordinates: Dict[str, float]  # {latitude, longitude}
    relevance: float


class AutocompleteRequest(BaseModel):
    """Request model for address autocomplete"""
    query: str = Field(..., min_length=3, max_length=200, description="Search query (min 3 characters)")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="User's latitude for proximity bias")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="User's longitude for proximity bias")
    limit: Optional[int] = Field(5, ge=1, le=10, description="Max suggestions (1-10)")


@router.get("/autocomplete", response_model=List[AddressAutocompleteResponse])
async def autocomplete_address(
    query: str = Query(..., min_length=3, max_length=200, description="Address search query"),
    latitude: Optional[float] = Query(None, ge=-90, le=90, description="User latitude for proximity"),
    longitude: Optional[float] = Query(None, ge=-180, le=180, description="User longitude for proximity"),
    limit: int = Query(5, ge=1, le=10, description="Max suggestions"),
    service: MapboxGeocodingService = Depends(get_mapbox_service)
):
    """
    Autocomplete address search for Canadian addresses

    This endpoint provides real-time address suggestions as the user types.
    Results are limited to Canadian addresses only.

    **Features:**
    - Search-as-you-type functionality
    - Proximity bias (results near user's location prioritized)
    - Rate-limited and cached for performance
    - Returns structured address data with coordinates

    **Example queries:**
    - "123 Main" → suggests "123 Main Street, Toronto, ON..."
    - "Yonge Toronto" → suggests addresses on Yonge St in Toronto
    - "M5V" → suggests addresses in postal code M5V

    **Rate Limiting:**
    - Backend rate limit: 100 requests/minute (shared across all users)
    - Cached results reduce API calls

    **Response includes:**
    - Full formatted address
    - Structured address components (street, city, province, postal code)
    - Geographic coordinates (latitude, longitude)
    - Relevance score (0-1, higher is more relevant)
    """
    try:
        # Validate query length
        if len(query) < 3:
            raise HTTPException(
                status_code=400,
                detail="Query must be at least 3 characters"
            )

        # Build proximity tuple if coordinates provided
        proximity = None
        if latitude is not None and longitude is not None:
            proximity = (latitude, longitude)

        # Call Mapbox autocomplete
        suggestions = await service.autocomplete_address(
            query=query,
            proximity=proximity,
            limit=limit
        )

        # Return suggestions (empty list if none found)
        return suggestions

    except Exception as e:
        logger.error(f"Autocomplete error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to search addresses. Please try again."
        )


@router.post("/autocomplete", response_model=List[AddressAutocompleteResponse])
async def autocomplete_address_post(
    request: AutocompleteRequest,
    service: MapboxGeocodingService = Depends(get_mapbox_service)
):
    """
    Autocomplete address search (POST variant)

    Same functionality as GET /autocomplete, but accepts a JSON request body.
    Useful for more complex queries or when query parameters are not ideal.
    """
    try:
        # Build proximity tuple if coordinates provided
        proximity = None
        if request.latitude is not None and request.longitude is not None:
            proximity = (request.latitude, request.longitude)

        # Call Mapbox autocomplete
        suggestions = await service.autocomplete_address(
            query=request.query,
            proximity=proximity,
            limit=request.limit or 5
        )

        return suggestions

    except Exception as e:
        logger.error(f"Autocomplete error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to search addresses. Please try again."
        )


@router.get("/health")
async def health_check(service: MapboxGeocodingService = Depends(get_mapbox_service)):
    """
    Health check endpoint for geocoding service

    Returns service status and basic statistics
    """
    try:
        stats = service.get_cache_stats()

        return {
            "status": "healthy",
            "service": "mapbox_geocoding",
            "api_key_configured": bool(service.api_key),
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
