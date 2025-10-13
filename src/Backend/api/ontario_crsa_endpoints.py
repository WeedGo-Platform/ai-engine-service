"""
Ontario CRSA API Endpoints
Provides license validation, store search, and tenant linking for Ontario cannabis retailers
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
import asyncpg
import os

from core.domain.models import CRSAVerificationStatus
from core.repositories.ontario_crsa_repository import OntarioCRSARepository
from core.services.ontario_crsa_service import OntarioCRSAService
from services.ontario_crsa_sync_service import get_sync_service

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/crsa", tags=["ontario-crsa"])

# Database connection pool (singleton)
_db_pool: Optional[asyncpg.Pool] = None


async def get_db_pool() -> asyncpg.Pool:
    """Get or create database connection pool"""
    global _db_pool
    if _db_pool is None:
        _db_pool = await asyncpg.create_pool(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5434)),
            user=os.getenv('DB_USER', 'weedgo'),
            password=os.getenv('DB_PASSWORD', 'weedgo123'),
            database=os.getenv('DB_NAME', 'ai_engine'),
            min_size=2,
            max_size=10
        )
    return _db_pool


async def get_crsa_service() -> OntarioCRSAService:
    """Dependency injection for CRSA service"""
    pool = await get_db_pool()
    repository = OntarioCRSARepository(pool)
    return OntarioCRSAService(repository)


# Request/Response Models

class LicenseValidationRequest(BaseModel):
    """Request model for license validation"""
    license_number: str = Field(..., description="Ontario cannabis retail license number")


class LicenseValidationResponse(BaseModel):
    """Response model for license validation"""
    is_valid: bool
    license_number: Optional[str] = None
    store_name: Optional[str] = None
    address: Optional[str] = None
    municipality: Optional[str] = None
    store_status: Optional[str] = None
    website: Optional[str] = None
    error_message: Optional[str] = None
    auto_fill_data: Optional[Dict[str, Any]] = None


class StoreSearchRequest(BaseModel):
    """Request model for store search"""
    query: str = Field(..., min_length=2, description="Search term (store name or address)")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    authorized_only: bool = Field(default=True, description="Only return authorized stores")


class StoreSearchResult(BaseModel):
    """Search result model"""
    id: str
    license_number: str
    store_name: str
    address: str
    municipality: Optional[str] = None
    store_status: str
    website: Optional[str] = None
    is_available: bool


class StoreListResponse(BaseModel):
    """Response model for store listings"""
    stores: List[StoreSearchResult]
    total: int
    limit: int
    offset: int


class LinkTenantRequest(BaseModel):
    """Request model for linking tenant to CRSA record"""
    license_number: str
    tenant_id: str


class UnlinkTenantRequest(BaseModel):
    """Request model for unlinking tenant from CRSA record"""
    license_number: str
    tenant_id: str


class VerifyLicenseRequest(BaseModel):
    """Request model for manual license verification"""
    license_number: str
    verified_by_user_id: str


class CRSAStatisticsResponse(BaseModel):
    """Response model for CRSA statistics"""
    total_stores: int
    authorized_count: int
    pending_count: int
    cancelled_count: int
    signed_up_count: int
    available_for_signup: int
    last_sync_time: Optional[str] = None
    municipality_count: int


# API Endpoints

@router.post("/validate", response_model=LicenseValidationResponse)
async def validate_license(
    request: LicenseValidationRequest,
    service: OntarioCRSAService = Depends(get_crsa_service)
):
    """
    Validate an Ontario cannabis retail license number

    This endpoint checks if:
    - License exists in AGCO database
    - Store is authorized to open
    - License is not already linked to another tenant

    Returns auto-fill data if validation succeeds.
    """
    try:
        # Validate license
        validation = await service.validate_license(request.license_number)

        # If valid, get auto-fill data
        auto_fill_data = None
        if validation.is_valid and validation.crsa_record:
            auto_fill_data = await service.auto_fill_tenant_info(request.license_number)

        # Build response
        response = {
            "is_valid": validation.is_valid,
            "error_message": validation.error_message
        }

        if validation.crsa_record:
            response.update({
                "license_number": validation.crsa_record.license_number,
                "store_name": validation.crsa_record.store_name,
                "address": validation.crsa_record.address,
                "municipality": validation.crsa_record.municipality or validation.crsa_record.first_nation,
                "store_status": validation.crsa_record.store_application_status,
                "website": validation.crsa_record.website,
                "auto_fill_data": auto_fill_data
            })

        return response

    except Exception as e:
        logger.error(f"Error validating license: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate license"
        )


@router.post("/search", response_model=StoreListResponse)
async def search_stores(
    request: StoreSearchRequest,
    service: OntarioCRSAService = Depends(get_crsa_service)
):
    """
    Search for stores by name or address

    Uses fuzzy matching to find stores even with typos or partial matches.
    """
    try:
        stores = await service.search_stores(
            query=request.query,
            limit=request.limit,
            authorized_only=request.authorized_only
        )

        # Convert to response format
        results = [
            StoreSearchResult(
                id=str(store.id),
                license_number=store.license_number,
                store_name=store.store_name,
                address=store.address,
                municipality=store.municipality or store.first_nation,
                store_status=store.store_application_status,
                website=store.website,
                is_available=store.is_available_for_signup()
            )
            for store in stores
        ]

        return {
            "stores": results,
            "total": len(results),
            "limit": request.limit,
            "offset": 0
        }

    except Exception as e:
        logger.error(f"Error searching stores: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search stores"
        )


@router.get("/stores/available", response_model=StoreListResponse)
async def list_available_stores(
    limit: int = 100,
    offset: int = 0,
    service: OntarioCRSAService = Depends(get_crsa_service)
):
    """
    List all stores available for tenant signup

    Returns authorized stores that are not yet linked to a tenant.
    """
    try:
        stores = await service.list_available_stores(limit=limit, offset=offset)

        results = [
            StoreSearchResult(
                id=str(store.id),
                license_number=store.license_number,
                store_name=store.store_name,
                address=store.address,
                municipality=store.municipality or store.first_nation,
                store_status=store.store_application_status,
                website=store.website,
                is_available=True  # All are available in this list
            )
            for store in stores
        ]

        return {
            "stores": results,
            "total": len(results),
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Error listing available stores: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list available stores"
        )


@router.get("/stores/municipality/{municipality}", response_model=StoreListResponse)
async def list_stores_by_municipality(
    municipality: str,
    limit: int = 100,
    offset: int = 0,
    service: OntarioCRSAService = Depends(get_crsa_service)
):
    """
    List all stores in a specific municipality
    """
    try:
        stores = await service.list_by_municipality(
            municipality=municipality,
            limit=limit,
            offset=offset
        )

        results = [
            StoreSearchResult(
                id=str(store.id),
                license_number=store.license_number,
                store_name=store.store_name,
                address=store.address,
                municipality=store.municipality or store.first_nation,
                store_status=store.store_application_status,
                website=store.website,
                is_available=store.is_available_for_signup()
            )
            for store in stores
        ]

        return {
            "stores": results,
            "total": len(results),
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Error listing stores by municipality: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list stores in {municipality}"
        )


@router.get("/stores/{license_number}")
async def get_store_by_license(
    license_number: str,
    service: OntarioCRSAService = Depends(get_crsa_service)
):
    """
    Get detailed store information by license number
    """
    try:
        store = await service.get_store_info(license_number)

        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Store with license {license_number} not found"
            )

        return {
            "id": str(store.id),
            "license_number": store.license_number,
            "store_name": store.store_name,
            "address": store.address,
            "municipality": store.municipality,
            "first_nation": store.first_nation,
            "store_application_status": store.store_application_status,
            "website": store.website,
            "linked_tenant_id": str(store.linked_tenant_id) if store.linked_tenant_id else None,
            "verification_status": store.verification_status.value,
            "is_active": store.is_active,
            "is_authorized": store.is_authorized(),
            "is_available": store.is_available_for_signup(),
            "last_synced_at": store.last_synced_at.isoformat() if store.last_synced_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting store by license: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get store information"
        )


@router.post("/link-tenant")
async def link_tenant_to_crsa(
    request: LinkTenantRequest,
    service: OntarioCRSAService = Depends(get_crsa_service)
):
    """
    Link a CRSA record to a tenant during signup

    This should be called when a tenant successfully signs up with a valid license.
    """
    try:
        tenant_id = UUID(request.tenant_id)
        updated_record = await service.link_to_tenant(request.license_number, tenant_id)

        return {
            "success": True,
            "message": f"License {request.license_number} linked to tenant {request.tenant_id}",
            "store_name": updated_record.store_name,
            "license_number": updated_record.license_number
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error linking tenant to CRSA: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to link tenant to CRSA record"
        )


@router.post("/unlink-tenant")
async def unlink_tenant_from_crsa(
    request: UnlinkTenantRequest,
    service: OntarioCRSAService = Depends(get_crsa_service)
):
    """
    Unlink a CRSA record from a tenant

    This should be used when a tenant account is deleted or needs to be re-assigned.
    """
    try:
        tenant_id = UUID(request.tenant_id)
        updated_record = await service.unlink_from_tenant(request.license_number, tenant_id)

        return {
            "success": True,
            "message": f"License {request.license_number} unlinked from tenant {request.tenant_id}",
            "store_name": updated_record.store_name,
            "license_number": updated_record.license_number
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error unlinking tenant from CRSA: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unlink tenant from CRSA record"
        )


@router.post("/verify-license")
async def verify_license_manually(
    request: VerifyLicenseRequest,
    service: OntarioCRSAService = Depends(get_crsa_service)
):
    """
    Manually verify a license (admin action)

    This endpoint allows admins to verify licenses that may require manual review.
    """
    try:
        verified_by_user_id = UUID(request.verified_by_user_id)
        updated_record = await service.verify_license(
            request.license_number,
            verified_by_user_id
        )

        return {
            "success": True,
            "message": f"License {request.license_number} verified successfully",
            "store_name": updated_record.store_name,
            "license_number": updated_record.license_number,
            "verification_status": updated_record.verification_status.value,
            "verified_at": updated_record.verification_date.isoformat() if updated_record.verification_date else None
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error verifying license: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify license"
        )


@router.get("/statistics", response_model=CRSAStatisticsResponse)
async def get_statistics(
    service: OntarioCRSAService = Depends(get_crsa_service)
):
    """
    Get CRSA database statistics

    Returns counts and statistics about the CRSA database.
    """
    try:
        stats = await service.get_statistics()
        return stats

    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get CRSA statistics"
        )


@router.get("/check-availability/{license_number}")
async def check_license_availability(
    license_number: str,
    service: OntarioCRSAService = Depends(get_crsa_service)
):
    """
    Quick check if a license is available for signup

    Returns a simple boolean indicating availability.
    """
    try:
        is_available = await service.check_license_availability(license_number)

        return {
            "license_number": license_number,
            "is_available": is_available
        }

    except Exception as e:
        logger.error(f"Error checking license availability: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check license availability"
        )


# Health check endpoint
@router.get("/health")
async def health_check():
    """
    Health check for CRSA API
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")

        return {
            "status": "healthy",
            "service": "ontario-crsa",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"CRSA health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CRSA service unavailable"
        )


# =====================================================
# Sync Management Endpoints (Admin Only)
# =====================================================

@router.post("/admin/sync/manual")
async def trigger_manual_sync(csv_path: Optional[str] = None):
    """
    Trigger a manual CRSA data sync

    This endpoint allows administrators to manually trigger a data sync.
    Optionally provide a CSV file path to import a specific file.

    Args:
        csv_path: Optional path to CSV file to import

    Returns:
        Sync results including success status and statistics
    """
    try:
        sync_service = get_sync_service()
        result = await sync_service.manual_sync(csv_path)

        return {
            "success": result.get("success", False),
            "message": "Sync completed" if result.get("success") else "Sync failed",
            **result
        }

    except Exception as e:
        logger.error(f"Manual sync failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger manual sync: {str(e)}"
        )


@router.get("/admin/sync/history")
async def get_sync_history(limit: int = 20):
    """
    Get recent sync history

    Returns the most recent sync operations with their status and statistics.

    Args:
        limit: Maximum number of records to return (default: 20)

    Returns:
        List of sync history records
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT
                    id,
                    sync_date,
                    success,
                    records_processed,
                    records_inserted,
                    records_updated,
                    records_skipped,
                    error_message,
                    csv_source,
                    duration_seconds,
                    created_at
                FROM crsa_sync_history
                ORDER BY sync_date DESC
                LIMIT $1
            """, limit)

            history = [
                {
                    "id": row["id"],
                    "sync_date": row["sync_date"].isoformat() if row["sync_date"] else None,
                    "success": row["success"],
                    "records_processed": row["records_processed"],
                    "records_inserted": row["records_inserted"],
                    "records_updated": row["records_updated"],
                    "records_skipped": row["records_skipped"],
                    "error_message": row["error_message"],
                    "csv_source": row["csv_source"],
                    "duration_seconds": float(row["duration_seconds"]) if row["duration_seconds"] else None,
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None
                }
                for row in rows
            ]

            return {
                "history": history,
                "total": len(history)
            }

    except Exception as e:
        logger.error(f"Failed to get sync history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sync history"
        )


@router.get("/admin/sync/statistics")
async def get_sync_statistics():
    """
    Get sync statistics for the last 30 days

    Returns:
        Aggregated statistics about sync operations
    """
    try:
        sync_service = get_sync_service()
        stats = await sync_service.get_sync_statistics()

        return {
            "period": "last_30_days",
            **stats
        }

    except Exception as e:
        logger.error(f"Failed to get sync statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sync statistics"
        )


@router.get("/admin/sync/status")
async def get_sync_status():
    """
    Get current sync service status

    Returns information about the scheduler and last sync time.
    """
    try:
        sync_service = get_sync_service()

        return {
            "scheduler_running": sync_service.is_running,
            "last_sync_time": sync_service.last_sync_time.isoformat() if sync_service.last_sync_time else None,
            "csv_directory": str(sync_service.csv_download_dir)
        }

    except Exception as e:
        logger.error(f"Failed to get sync status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sync status"
        )
