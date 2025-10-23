"""
OCS Management API Endpoints

Provides endpoints for OCS credential management, manual submissions,
audit logs, and compliance monitoring.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime
import logging
import os

from core.authentication import get_current_user, require_roles
from services.ocs_auth_service import OCSAuthService
from services.ocs_inventory_position_service import OCSInventoryPositionService
from services.ocs_inventory_event_service import OCSInventoryEventService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ocs", tags=["OCS Compliance"])


# Pydantic models
class OCSCredentialsRequest(BaseModel):
    """Request model for storing OCS credentials"""
    tenant_id: str = Field(..., description="Tenant UUID")
    client_id: str = Field(..., description="OCS OAuth client ID")
    client_secret: str = Field(..., description="OCS OAuth client secret")


class StoreOCSConfigRequest(BaseModel):
    """Request model for store OCS configuration"""
    ocs_key: str = Field(..., description="OCS hash key for the store")
    license_number: str = Field(..., description="CRSA license number")


class ManualPositionSubmitRequest(BaseModel):
    """Request model for manual position submission"""
    store_id: str = Field(..., description="Store UUID")
    snapshot_date: Optional[date] = Field(None, description="Snapshot date (default: today)")


class RetryEventsRequest(BaseModel):
    """Request model for retrying failed events"""
    tenant_id: str = Field(..., description="Tenant UUID")
    limit: int = Field(50, ge=1, le=100, description="Max events to retry")


# Dependency for database pool (from your existing setup)
async def get_db_pool():
    """Get database pool - implement based on your existing setup"""
    import asyncpg
    return await asyncpg.create_pool(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5434)),
        database=os.getenv('DB_NAME', 'ai_engine'),
        user=os.getenv('DB_USER', 'weedgo'),
        password=os.getenv('DB_PASSWORD', 'your_password_here'),
        min_size=2,
        max_size=10
    )


@router.post("/credentials", status_code=status.HTTP_201_CREATED)
async def store_ocs_credentials(
    request: OCSCredentialsRequest,
    current_user: dict = Depends(get_current_user),
    db_pool = Depends(get_db_pool)
):
    """
    Store OCS OAuth credentials for a tenant
    
    **Required Role**: Super Admin
    
    Credentials are encrypted using bcrypt before storage.
    """
    # Verify super admin
    if current_user.get('role') != 'super_admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can manage OCS credentials"
        )
    
    try:
        auth_service = OCSAuthService(db_pool)
        
        # Validate credentials first
        is_valid = await auth_service.validate_credentials(
            request.client_id,
            request.client_secret
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OCS credentials - failed to authenticate with OCS API"
            )
        
        # Store credentials
        success = await auth_service.store_credentials(
            tenant_id=request.tenant_id,
            client_id=request.client_id,
            client_secret=request.client_secret
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store OCS credentials"
            )
        
        return {
            "success": True,
            "message": "OCS credentials stored successfully",
            "tenant_id": request.tenant_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error storing OCS credentials: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/stores/{store_id}/config")
async def update_store_ocs_config(
    store_id: str,
    request: StoreOCSConfigRequest,
    current_user: dict = Depends(get_current_user),
    db_pool = Depends(get_db_pool)
):
    """
    Update OCS configuration for a store
    
    **Required Role**: Tenant Admin or Super Admin
    
    Sets the OCS hash key and CRSA license number for the store.
    """
    try:
        async with db_pool.acquire() as conn:
            # Verify store belongs to user's tenant (unless super admin)
            if current_user.get('role') != 'super_admin':
                store = await conn.fetchrow(
                    "SELECT tenant_id FROM stores WHERE id = $1",
                    store_id
                )
                
                if not store or store['tenant_id'] != current_user.get('tenant_id'):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied to this store"
                    )
            
            # Update store configuration
            await conn.execute("""
                UPDATE stores
                SET 
                    ocs_key = $1,
                    license_number = $2,
                    updated_at = NOW()
                WHERE id = $3
            """, request.ocs_key, request.license_number, store_id)
        
        return {
            "success": True,
            "message": "Store OCS configuration updated",
            "store_id": store_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating store OCS config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/position/history/{store_id}")
async def get_position_history(
    store_id: str,
    limit: int = 30,
    current_user: dict = Depends(get_current_user),
    db_pool = Depends(get_db_pool)
):
    """
    Get inventory position submission history for a store
    
    **Required Role**: Tenant Admin or Super Admin
    """
    try:
        position_service = OCSInventoryPositionService(
            db_pool,
            OCSAuthService(db_pool)
        )
        
        history = await position_service.get_submission_history(store_id, limit)
        
        return {
            "success": True,
            "store_id": store_id,
            "history": history
        }
        
    except Exception as e:
        logger.error(f"Error getting position history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/position/submit")
async def submit_position_manually(
    request: ManualPositionSubmitRequest,
    current_user: dict = Depends(get_current_user),
    db_pool = Depends(get_db_pool)
):
    """
    Manually trigger inventory position submission
    
    **Required Role**: Tenant Admin or Super Admin
    
    Useful for testing or submitting missed snapshots.
    """
    try:
        # Get store's tenant_id
        async with db_pool.acquire() as conn:
            store = await conn.fetchrow(
                "SELECT tenant_id FROM stores WHERE id = $1",
                request.store_id
            )
            
            if not store:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Store not found"
                )
            
            tenant_id = store['tenant_id']
        
        # Submit position
        auth_service = OCSAuthService(db_pool)
        position_service = OCSInventoryPositionService(db_pool, auth_service)
        
        result = await position_service.submit_daily_position(
            tenant_id=tenant_id,
            store_id=request.store_id,
            snapshot_date=request.snapshot_date
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error', 'Submission failed')
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting position: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/events/history/{store_id}")
async def get_event_history(
    store_id: str,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db_pool = Depends(get_db_pool)
):
    """
    Get inventory event submission history for a store
    
    **Required Role**: Tenant Admin or Super Admin
    """
    try:
        event_service = OCSInventoryEventService(
            db_pool,
            OCSAuthService(db_pool)
        )
        
        history = await event_service.get_event_history(store_id, limit)
        
        return {
            "success": True,
            "store_id": store_id,
            "history": history
        }
        
    except Exception as e:
        logger.error(f"Error getting event history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/events/retry")
async def retry_failed_events(
    request: RetryEventsRequest,
    current_user: dict = Depends(get_current_user),
    db_pool = Depends(get_db_pool)
):
    """
    Retry failed event submissions
    
    **Required Role**: Super Admin
    
    Retries up to `limit` failed events for the specified tenant.
    """
    if current_user.get('role') != 'super_admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can retry failed events"
        )
    
    try:
        event_service = OCSInventoryEventService(
            db_pool,
            OCSAuthService(db_pool)
        )
        
        result = await event_service.retry_failed_events(
            tenant_id=request.tenant_id,
            limit=request.limit
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error retrying events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/audit")
async def get_audit_logs(
    limit: int = 100,
    operation: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db_pool = Depends(get_db_pool)
):
    """
    Get OCS audit logs
    
    **Required Role**: Super Admin
    
    Returns audit trail of OCS operations.
    """
    if current_user.get('role') != 'super_admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can view audit logs"
        )
    
    try:
        async with db_pool.acquire() as conn:
            query = """
                SELECT 
                    id,
                    operation,
                    status,
                    details,
                    created_at
                FROM ocs_audit_log
                WHERE 1=1
            """
            params = []
            
            if operation:
                query += " AND operation = $" + str(len(params) + 1)
                params.append(operation)
            
            if status:
                query += " AND status = $" + str(len(params) + 1)
                params.append(status)
            
            query += " ORDER BY created_at DESC LIMIT $" + str(len(params) + 1)
            params.append(limit)
            
            logs = await conn.fetch(query, *params)
        
        return {
            "success": True,
            "logs": [dict(log) for log in logs]
        }
        
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/status/{tenant_id}")
async def get_ocs_status(
    tenant_id: str,
    current_user: dict = Depends(get_current_user),
    db_pool = Depends(get_db_pool)
):
    """
    Get OCS integration status for a tenant
    
    **Required Role**: Tenant Admin or Super Admin
    
    Returns configuration status, recent submissions, and error summary.
    """
    try:
        async with db_pool.acquire() as conn:
            # Check if credentials are configured
            creds = await conn.fetchrow("""
                SELECT 
                    client_id_encrypted IS NOT NULL as has_credentials,
                    token_expires_at
                FROM ocs_oauth_tokens
                WHERE tenant_id = $1
            """, tenant_id)
            
            # Get OCS-enabled stores count
            stores_count = await conn.fetchval("""
                SELECT COUNT(*)
                FROM stores
                WHERE tenant_id = $1
                AND ocs_key IS NOT NULL
                AND license_number IS NOT NULL
            """, tenant_id)
            
            # Get recent submission stats
            recent_positions = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
                FROM ocs_inventory_position_log
                WHERE tenant_id = $1
                AND submitted_at >= NOW() - INTERVAL '7 days'
            """, tenant_id)
            
            recent_events = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
                FROM ocs_inventory_event_log
                WHERE tenant_id = $1
                AND submitted_at >= NOW() - INTERVAL '7 days'
            """, tenant_id)
        
        return {
            "success": True,
            "tenant_id": tenant_id,
            "status": {
                "credentials_configured": creds['has_credentials'] if creds else False,
                "token_valid": creds and creds['token_expires_at'] and creds['token_expires_at'] > datetime.utcnow() if creds else False,
                "enabled_stores": stores_count,
                "last_7_days": {
                    "positions": dict(recent_positions) if recent_positions else {"total": 0, "success": 0, "failed": 0},
                    "events": dict(recent_events) if recent_events else {"total": 0, "success": 0, "failed": 0}
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting OCS status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
