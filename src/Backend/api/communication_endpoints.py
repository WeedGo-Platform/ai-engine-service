"""
Communication API Endpoints
Handles broadcast messaging, templates, and customer communication preferences
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body, BackgroundTasks
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import json
import logging
import asyncpg
import os

# Database connection pool
db_pool = None

async def get_db_pool():
    """Get or create database connection pool"""
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(
            host=os.getenv('PG_HOST', 'localhost'),
            port=int(os.getenv('PG_PORT', '5434')),
            user=os.getenv('PG_USER', 'weedgo'),
            password=os.getenv('PG_PASSWORD', 'weedgo123'),
            database=os.getenv('PG_DATABASE', 'ai_engine'),
            min_size=5,
            max_size=20
        )
    return db_pool

# Stub authentication functions for now
from fastapi import Header
from typing import Optional

async def verify_token(authorization: Optional[str] = Header(None)):
    """Verify JWT token and return user data"""
    # TODO: Implement actual token verification
    # Extract token from Bearer header if present
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    else:
        token = None

    return {"user_id": "test-user", "role": "super_admin", "tenant_id": "test-tenant", "token": token}

def check_permission(role_required: str):
    """Check if user has required permission"""
    async def permission_checker(current_user: dict = Depends(verify_token)):
        # TODO: Implement actual permission checking
        return current_user
    return permission_checker

from services.communication.broadcast_service import BroadcastService
from services.communication.segmentation_service import SegmentationService
from services.communication.template_service import TemplateService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/communications", tags=["Communications"])


# =====================================================
# BROADCAST MANAGEMENT ENDPOINTS
# =====================================================

@router.post("/broadcasts")
async def create_broadcast(
    background_tasks: BackgroundTasks,
    broadcast_data: Dict[str, Any] = Body(...),
    token_data: dict = Depends(verify_token),
    db=Depends(get_db_pool)
):
    """
    Create a new broadcast campaign

    Required permissions: Super Admin, Tenant Admin, Store Manager
    """
    try:
        # Check permissions - simplified for now since verify_token returns a stub
        # TODO: Implement proper permission checking
        # if not check_permission(token_data, ["Super Admin", "Tenant Admin", "Store Manager"]):
        #     raise HTTPException(status_code=403, detail="Insufficient permissions")

        # Get store and tenant from context
        store_id = broadcast_data.get("store_id") or token_data.get("store_id")
        tenant_id = broadcast_data.get("tenant_id") or token_data.get("tenant_id")
        user_id = token_data.get("user_id")

        if not store_id:
            raise HTTPException(status_code=400, detail="Store ID is required")

        # Initialize service
        broadcast_service = BroadcastService(db)

        # Create broadcast
        broadcast_id = await broadcast_service.create_broadcast(
            name=broadcast_data["name"],
            store_id=store_id,
            tenant_id=tenant_id,
            created_by=user_id,
            channels=broadcast_data.get("channels", []),
            messages=broadcast_data.get("messages", {}),
            recipients=broadcast_data.get("recipients"),
            segment_criteria=broadcast_data.get("segment_criteria"),
            scheduled_at=broadcast_data.get("scheduled_at"),
            metadata=broadcast_data.get("metadata", {})
        )

        # Execute immediately if send_now is true
        if broadcast_data.get("send_now"):
            background_tasks.add_task(
                broadcast_service.execute_broadcast,
                broadcast_id
            )

        return {
            "success": True,
            "broadcast_id": broadcast_id,
            "message": "Broadcast created successfully"
        }

    except Exception as e:
        logger.error(f"Error creating broadcast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/broadcasts")
async def list_broadcasts(
    store_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    token_data: dict = Depends(verify_token),
    db=Depends(get_db_pool)
):
    """
    List broadcast campaigns

    Required permissions: Super Admin, Tenant Admin, Store Manager
    """
    try:
        # TODO: Implement proper permission checking
        # if not check_permission(token_data, ["Super Admin", "Tenant Admin", "Store Manager"]):
        #     raise HTTPException(status_code=403, detail="Insufficient permissions")

        # Use store from token if not provided
        if not store_id:
            store_id = token_data.get("store_id")

        async with db.acquire() as conn:
            query = """
                SELECT
                    b.id, b.name, b.description, b.status,
                    b.scheduled_at, b.started_at, b.completed_at,
                    b.total_recipients, b.successful_sends, b.failed_sends,
                    b.created_at, b.created_by,
                    u.email as created_by_name,
                    COUNT(DISTINCT bm.channel_type) as channel_count
                FROM broadcasts b
                LEFT JOIN users u ON b.created_by = u.id
                LEFT JOIN broadcast_messages bm ON b.id = bm.broadcast_id
                WHERE 1=1
            """
            params = []
            param_count = 1

            if store_id:
                query += f" AND b.store_id = ${param_count}"
                params.append(uuid.UUID(store_id))
                param_count += 1

            if status:
                query += f" AND b.status = ${param_count}"
                params.append(status)
                param_count += 1

            query += """
                GROUP BY b.id, u.email
                ORDER BY b.created_at DESC
                LIMIT $%d OFFSET $%d
            """ % (param_count, param_count + 1)
            params.extend([limit, offset])

            broadcasts = await conn.fetch(query, *params)

            # Get total count
            count_query = "SELECT COUNT(*) FROM broadcasts WHERE 1=1"
            count_params = []
            if store_id:
                count_query += " AND store_id = $1"
                count_params.append(uuid.UUID(store_id))
            if status:
                count_query += f" AND status = ${len(count_params) + 1}"
                count_params.append(status)

            total = await conn.fetchval(count_query, *count_params)

            return {
                "success": True,
                "broadcasts": [dict(b) for b in broadcasts],
                "total": total,
                "limit": limit,
                "offset": offset
            }

    except Exception as e:
        logger.error(f"Error listing broadcasts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/broadcasts/{broadcast_id}")
async def get_broadcast_details(
    broadcast_id: str,
    token_data: dict = Depends(verify_token),
    db=Depends(get_db_pool)
):
    """
    Get detailed information about a broadcast

    Required permissions: Super Admin, Tenant Admin, Store Manager
    """
    try:
        # TODO: Implement proper permission checking
        # if not check_permission(token_data, ["Super Admin", "Tenant Admin", "Store Manager"]):
        #     raise HTTPException(status_code=403, detail="Insufficient permissions")

        broadcast_service = BroadcastService(db)
        analytics = await broadcast_service.get_broadcast_analytics(broadcast_id)

        if "error" in analytics:
            raise HTTPException(status_code=404, detail=analytics["error"])

        return {
            "success": True,
            "data": analytics
        }

    except Exception as e:
        logger.error(f"Error getting broadcast details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/broadcasts/{broadcast_id}/execute")
async def execute_broadcast(
    broadcast_id: str,
    background_tasks: BackgroundTasks,
    token_data: dict = Depends(verify_token),
    db=Depends(get_db_pool)
):
    """
    Execute/Send a broadcast campaign

    Required permissions: Super Admin, Tenant Admin, Store Manager
    """
    try:
        # TODO: Implement proper permission checking
        # if not check_permission(token_data, ["Super Admin", "Tenant Admin", "Store Manager"]):
        #     raise HTTPException(status_code=403, detail="Insufficient permissions")

        broadcast_service = BroadcastService(db)

        # Execute in background
        background_tasks.add_task(
            broadcast_service.execute_broadcast,
            broadcast_id
        )

        return {
            "success": True,
            "message": "Broadcast execution started",
            "broadcast_id": broadcast_id
        }

    except Exception as e:
        logger.error(f"Error executing broadcast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/broadcasts/{broadcast_id}/pause")
async def pause_broadcast(
    broadcast_id: str,
    token_data: dict = Depends(verify_token),
    db=Depends(get_db_pool)
):
    """
    Pause an ongoing broadcast

    Required permissions: Super Admin, Tenant Admin, Store Manager
    """
    try:
        # TODO: Implement proper permission checking
        # if not check_permission(token_data, ["Super Admin", "Tenant Admin", "Store Manager"]):
        #     raise HTTPException(status_code=403, detail="Insufficient permissions")

        broadcast_service = BroadcastService(db)
        result = await broadcast_service.pause_broadcast(
            broadcast_id,
            token_data.get("user_id")
        )

        if not result:
            raise HTTPException(status_code=400, detail="Cannot pause broadcast")

        return {
            "success": True,
            "message": "Broadcast paused successfully"
        }

    except Exception as e:
        logger.error(f"Error pausing broadcast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/broadcasts/{broadcast_id}/resume")
async def resume_broadcast(
    broadcast_id: str,
    background_tasks: BackgroundTasks,
    token_data: dict = Depends(verify_token),
    db=Depends(get_db_pool)
):
    """
    Resume a paused broadcast

    Required permissions: Super Admin, Tenant Admin, Store Manager
    """
    try:
        # TODO: Implement proper permission checking
        # if not check_permission(token_data, ["Super Admin", "Tenant Admin", "Store Manager"]):
        #     raise HTTPException(status_code=403, detail="Insufficient permissions")

        broadcast_service = BroadcastService(db)
        result = await broadcast_service.resume_broadcast(
            broadcast_id,
            token_data.get("user_id")
        )

        if not result:
            raise HTTPException(status_code=400, detail="Cannot resume broadcast")

        return {
            "success": True,
            "message": "Broadcast resumed successfully"
        }

    except Exception as e:
        logger.error(f"Error resuming broadcast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/broadcasts/{broadcast_id}")
async def cancel_broadcast(
    broadcast_id: str,
    token_data: dict = Depends(verify_token),
    db=Depends(get_db_pool)
):
    """
    Cancel a broadcast campaign

    Required permissions: Super Admin, Tenant Admin, Store Manager
    """
    try:
        # TODO: Implement proper permission checking
        # if not check_permission(token_data, ["Super Admin", "Tenant Admin", "Store Manager"]):
        #     raise HTTPException(status_code=403, detail="Insufficient permissions")

        broadcast_service = BroadcastService(db)
        result = await broadcast_service.cancel_broadcast(
            broadcast_id,
            token_data.get("user_id")
        )

        if not result:
            raise HTTPException(status_code=400, detail="Cannot cancel broadcast")

        return {
            "success": True,
            "message": "Broadcast cancelled successfully"
        }

    except Exception as e:
        logger.error(f"Error cancelling broadcast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# RECIPIENT SEGMENTATION ENDPOINTS
# =====================================================

@router.get("/segments")
async def list_segments(
    store_id: Optional[str] = Query(None),
    include_predefined: bool = Query(True),
    token_data: dict = Depends(verify_token),
    db=Depends(get_db_pool)
):
    """
    List available customer segments

    Required permissions: Super Admin, Tenant Admin, Store Manager
    """
    try:
        # TODO: Implement proper permission checking
        # if not check_permission(token_data, ["Super Admin", "Tenant Admin", "Store Manager"]):
        #     raise HTTPException(status_code=403, detail="Insufficient permissions")

        if not store_id:
            store_id = token_data.get("store_id")

        segmentation_service = SegmentationService(db)

        segments = []

        # Get predefined segments
        if include_predefined:
            segments.extend(segmentation_service.get_predefined_segments())

        # Get custom segments
        if store_id:
            custom_segments = await segmentation_service.get_custom_segments(store_id)
            segments.extend(custom_segments)

        return {
            "success": True,
            "segments": segments
        }

    except Exception as e:
        logger.error(f"Error listing segments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/segments/preview")
async def preview_segment(
    segment_data: Dict[str, Any] = Body(...),
    token_data: dict = Depends(verify_token),
    db=Depends(get_db_pool)
):
    """
    Preview recipients in a segment

    Required permissions: Super Admin, Tenant Admin, Store Manager
    """
    try:
        # TODO: Implement proper permission checking
        # if not check_permission(token_data, ["Super Admin", "Tenant Admin", "Store Manager"]):
        #     raise HTTPException(status_code=403, detail="Insufficient permissions")

        store_id = segment_data.get("store_id") or token_data.get("store_id")
        if not store_id:
            raise HTTPException(status_code=400, detail="Store ID is required")

        segmentation_service = SegmentationService(db)

        # Get recipients
        recipients = await segmentation_service.get_segment_recipients(
            store_id=store_id,
            tenant_id=token_data.get("tenant_id"),
            segment_id=segment_data.get("segment_id"),
            criteria=segment_data.get("criteria"),
            limit=100  # Limit preview to 100 recipients
        )

        # Get count
        total_count = await segmentation_service.get_segment_count(
            store_id=store_id,
            tenant_id=token_data.get("tenant_id"),
            segment_id=segment_data.get("segment_id"),
            criteria=segment_data.get("criteria")
        )

        # Get analytics
        analytics = await segmentation_service.analyze_segment(
            store_id=store_id,
            segment_id=segment_data.get("segment_id"),
            criteria=segment_data.get("criteria")
        )

        return {
            "success": True,
            "preview": recipients[:10],  # Show first 10 for preview
            "total_count": total_count,
            "analytics": analytics
        }

    except Exception as e:
        logger.error(f"Error previewing segment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/segments/save")
async def save_custom_segment(
    segment_data: Dict[str, Any] = Body(...),
    token_data: dict = Depends(verify_token),
    db=Depends(get_db_pool)
):
    """
    Save a custom segment

    Required permissions: Super Admin, Tenant Admin, Store Manager
    """
    try:
        # TODO: Implement proper permission checking
        # if not check_permission(token_data, ["Super Admin", "Tenant Admin", "Store Manager"]):
        #     raise HTTPException(status_code=403, detail="Insufficient permissions")

        store_id = segment_data.get("store_id") or token_data.get("store_id")
        if not store_id:
            raise HTTPException(status_code=400, detail="Store ID is required")

        segmentation_service = SegmentationService(db)

        segment_id = await segmentation_service.save_custom_segment(
            name=segment_data["name"],
            description=segment_data.get("description", ""),
            store_id=store_id,
            tenant_id=token_data.get("tenant_id"),
            criteria=segment_data["criteria"],
            created_by=token_data.get("user_id")
        )

        return {
            "success": True,
            "segment_id": segment_id,
            "message": "Segment saved successfully"
        }

    except Exception as e:
        logger.error(f"Error saving segment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# TEMPLATE MANAGEMENT ENDPOINTS
# =====================================================

@router.get("/templates")
async def list_templates(
    store_id: Optional[str] = Query(None),
    channel_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    include_system: bool = Query(True),
    token_data: dict = Depends(verify_token),
    db=Depends(get_db_pool)
):
    """
    List message templates

    Required permissions: Super Admin, Tenant Admin, Store Manager
    """
    try:
        # TODO: Implement proper permission checking
        # if not check_permission(token_data, ["Super Admin", "Tenant Admin", "Store Manager"]):
        #     raise HTTPException(status_code=403, detail="Insufficient permissions")

        if not store_id:
            store_id = token_data.get("store_id")

        template_service = TemplateService(db)

        templates = await template_service.list_templates(
            store_id=store_id,
            tenant_id=token_data.get("tenant_id"),
            channel_type=channel_type,
            category=category,
            include_system=include_system
        )

        return {
            "success": True,
            "templates": templates
        }

    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates")
async def create_template(
    template_data: Dict[str, Any] = Body(...),
    token_data: dict = Depends(verify_token),
    db=Depends(get_db_pool)
):
    """
    Create a new message template

    Required permissions: Super Admin, Tenant Admin, Store Manager
    """
    try:
        # TODO: Implement proper permission checking
        # if not check_permission(token_data, ["Super Admin", "Tenant Admin", "Store Manager"]):
        #     raise HTTPException(status_code=403, detail="Insufficient permissions")

        template_service = TemplateService(db)

        template_id = await template_service.create_template(
            name=template_data["name"],
            channel_type=template_data["channel_type"],
            category=template_data.get("category", "general"),
            subject=template_data.get("subject"),
            content=template_data["content"],
            variables=template_data.get("variables", {}),
            store_id=template_data.get("store_id") or token_data.get("store_id"),
            tenant_id=template_data.get("tenant_id") or token_data.get("tenant_id"),
            created_by=token_data.get("user_id"),
            is_global=template_data.get("is_global", False) and check_permission(token_data, ["Super Admin"])
        )

        return {
            "success": True,
            "template_id": template_id,
            "message": "Template created successfully"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_id}/preview")
async def preview_template(
    template_id: str,
    sample_data: Optional[Dict[str, Any]] = None,
    token_data: dict = Depends(verify_token),
    db=Depends(get_db_pool)
):
    """
    Preview a template with sample data

    Required permissions: Super Admin, Tenant Admin, Store Manager
    """
    try:
        # TODO: Implement proper permission checking
        # if not check_permission(token_data, ["Super Admin", "Tenant Admin", "Store Manager"]):
        #     raise HTTPException(status_code=403, detail="Insufficient permissions")

        template_service = TemplateService(db)

        preview = await template_service.preview_template(
            template_id=template_id,
            sample_data=sample_data
        )

        if "error" in preview:
            raise HTTPException(status_code=400, detail=preview["error"])

        return {
            "success": True,
            "preview": preview
        }

    except Exception as e:
        logger.error(f"Error previewing template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/templates/{template_id}")
async def update_template(
    template_id: str,
    updates: Dict[str, Any] = Body(...),
    token_data: dict = Depends(verify_token),
    db=Depends(get_db_pool)
):
    """
    Update a message template

    Required permissions: Super Admin, Tenant Admin, Store Manager
    """
    try:
        # TODO: Implement proper permission checking
        # if not check_permission(token_data, ["Super Admin", "Tenant Admin", "Store Manager"]):
        #     raise HTTPException(status_code=403, detail="Insufficient permissions")

        template_service = TemplateService(db)

        result = await template_service.update_template(template_id, updates)

        if not result:
            raise HTTPException(status_code=404, detail="Template not found")

        return {
            "success": True,
            "message": "Template updated successfully"
        }

    except Exception as e:
        logger.error(f"Error updating template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str,
    token_data: dict = Depends(verify_token),
    db=Depends(get_db_pool)
):
    """
    Delete a message template

    Required permissions: Super Admin, Tenant Admin, Store Manager
    """
    try:
        # TODO: Implement proper permission checking
        # if not check_permission(token_data, ["Super Admin", "Tenant Admin", "Store Manager"]):
        #     raise HTTPException(status_code=403, detail="Insufficient permissions")

        template_service = TemplateService(db)

        result = await template_service.delete_template(template_id)

        if not result:
            raise HTTPException(status_code=404, detail="Template not found")

        return {
            "success": True,
            "message": "Template deleted successfully"
        }

    except Exception as e:
        logger.error(f"Error deleting template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# PREFERENCE MANAGEMENT ENDPOINTS
# =====================================================

@router.get("/preferences/{customer_id}")
async def get_communication_preferences(
    customer_id: str,
    token_data: dict = Depends(verify_token),
    db=Depends(get_db_pool)
):
    """
    Get customer communication preferences

    Required permissions: Any authenticated user (for own preferences) or Admin roles
    """
    try:
        # Check if accessing own preferences or has admin permission
        if customer_id != token_data.get("customer_id") and not check_permission(
            token_data, ["Super Admin", "Tenant Admin", "Store Manager"]
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        async with db.acquire() as conn:
            prefs = await conn.fetchrow("""
                SELECT * FROM communication_preferences
                WHERE customer_id = $1
            """, customer_id)

            if not prefs:
                # Return default preferences
                return {
                    "success": True,
                    "preferences": {
                        "channel_email": True,
                        "channel_sms": True,
                        "channel_push": True,
                        "promotional": True,
                        "transactional": True,
                        "alerts": True,
                        "frequency": "normal"
                    }
                }

            return {
                "success": True,
                "preferences": dict(prefs)
            }

    except Exception as e:
        logger.error(f"Error getting preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/preferences/{customer_id}")
async def update_communication_preferences(
    customer_id: str,
    preferences: Dict[str, Any] = Body(...),
    token_data: dict = Depends(verify_token),
    db=Depends(get_db_pool)
):
    """
    Update customer communication preferences

    Required permissions: Any authenticated user (for own preferences) or Admin roles
    """
    try:
        # Check if updating own preferences or has admin permission
        if customer_id != token_data.get("customer_id") and not check_permission(
            token_data, ["Super Admin", "Tenant Admin", "Store Manager"]
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        async with db.acquire() as conn:
            # Upsert preferences
            await conn.execute("""
                INSERT INTO communication_preferences (
                    customer_id, channel_email, channel_sms, channel_push,
                    promotional, transactional, alerts, frequency,
                    quiet_hours_enabled, quiet_hours_start, quiet_hours_end,
                    timezone, preferred_language
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ON CONFLICT (customer_id) DO UPDATE SET
                    channel_email = EXCLUDED.channel_email,
                    channel_sms = EXCLUDED.channel_sms,
                    channel_push = EXCLUDED.channel_push,
                    promotional = EXCLUDED.promotional,
                    transactional = EXCLUDED.transactional,
                    alerts = EXCLUDED.alerts,
                    frequency = EXCLUDED.frequency,
                    quiet_hours_enabled = EXCLUDED.quiet_hours_enabled,
                    quiet_hours_start = EXCLUDED.quiet_hours_start,
                    quiet_hours_end = EXCLUDED.quiet_hours_end,
                    timezone = EXCLUDED.timezone,
                    preferred_language = EXCLUDED.preferred_language,
                    updated_at = NOW()
            """, customer_id,
                preferences.get("channel_email", True),
                preferences.get("channel_sms", True),
                preferences.get("channel_push", True),
                preferences.get("promotional", True),
                preferences.get("transactional", True),
                preferences.get("alerts", True),
                preferences.get("frequency", "normal"),
                preferences.get("quiet_hours_enabled", False),
                preferences.get("quiet_hours_start"),
                preferences.get("quiet_hours_end"),
                preferences.get("timezone", "America/Toronto"),
                preferences.get("preferred_language", "en"))

            return {
                "success": True,
                "message": "Preferences updated successfully"
            }

    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/unsubscribe")
async def unsubscribe(
    unsubscribe_data: Dict[str, Any] = Body(...),
    db=Depends(get_db_pool)
):
    """
    Handle unsubscribe request

    Public endpoint - no authentication required
    """
    try:
        async with db.acquire() as conn:
            # Add to unsubscribe list
            await conn.execute("""
                INSERT INTO unsubscribe_list (
                    customer_id, email, phone_number, channel_type,
                    reason, additional_comments, unsubscribe_source
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, unsubscribe_data.get("customer_id"),
                unsubscribe_data.get("email"),
                unsubscribe_data.get("phone"),
                unsubscribe_data.get("channel_type", "all"),
                unsubscribe_data.get("reason"),
                unsubscribe_data.get("comments"),
                unsubscribe_data.get("source", "customer_request"))

            # Update preferences if customer_id provided
            if unsubscribe_data.get("customer_id"):
                channel_type = unsubscribe_data.get("channel_type", "all")
                if channel_type == "all":
                    await conn.execute("""
                        UPDATE communication_preferences
                        SET channel_email = false, channel_sms = false, channel_push = false
                        WHERE customer_id = $1
                    """, unsubscribe_data["customer_id"])
                elif channel_type in ["email", "sms", "push"]:
                    await conn.execute(f"""
                        UPDATE communication_preferences
                        SET channel_{channel_type} = false
                        WHERE customer_id = $1
                    """, unsubscribe_data["customer_id"])

            return {
                "success": True,
                "message": "You have been unsubscribed successfully"
            }

    except Exception as e:
        logger.error(f"Error processing unsubscribe: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# ANALYTICS ENDPOINTS
# =====================================================

@router.get("/analytics/overview")
async def get_communication_analytics(
    store_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    token_data: dict = Depends(verify_token),
    db=Depends(get_db_pool)
):
    """
    Get communication analytics overview

    Required permissions: Super Admin, Tenant Admin, Store Manager
    """
    try:
        # TODO: Implement proper permission checking
        # if not check_permission(token_data, ["Super Admin", "Tenant Admin", "Store Manager"]):
        #     raise HTTPException(status_code=403, detail="Insufficient permissions")

        if not store_id:
            store_id = token_data.get("store_id")

        async with db.acquire() as conn:
            # Get overview stats
            stats = await conn.fetchrow("""
                SELECT
                    COUNT(DISTINCT b.id) as total_campaigns,
                    SUM(b.successful_sends) as total_sent,
                    SUM(b.failed_sends) as total_failed,
                    AVG(CASE WHEN b.successful_sends > 0
                        THEN b.successful_sends::float / (b.successful_sends + b.failed_sends) * 100
                        ELSE 0 END) as avg_success_rate
                FROM broadcasts b
                WHERE b.store_id = $1
                AND ($2::timestamp IS NULL OR b.created_at >= $2)
                AND ($3::timestamp IS NULL OR b.created_at <= $3)
            """, uuid.UUID(store_id) if store_id else None,
                start_date, end_date)

            # Get channel breakdown
            channel_stats = await conn.fetch("""
                SELECT
                    bm.channel_type,
                    COUNT(DISTINCT bm.broadcast_id) as campaigns_used,
                    SUM(ca.email_sent + ca.sms_sent + ca.push_sent) as messages_sent,
                    AVG(CASE
                        WHEN bm.channel_type = 'email' THEN ca.email_open_rate
                        WHEN bm.channel_type = 'push' THEN ca.push_open_rate
                        ELSE 0
                    END) as avg_engagement_rate
                FROM broadcast_messages bm
                JOIN broadcasts b ON bm.broadcast_id = b.id
                LEFT JOIN communication_analytics ca ON b.id = ca.broadcast_id
                WHERE b.store_id = $1
                AND ($2::timestamp IS NULL OR b.created_at >= $2)
                AND ($3::timestamp IS NULL OR b.created_at <= $3)
                GROUP BY bm.channel_type
            """, uuid.UUID(store_id) if store_id else None,
                start_date, end_date)

            # Get cost summary
            cost_stats = await conn.fetchrow("""
                SELECT
                    SUM(ca.email_cost) as total_email_cost,
                    SUM(ca.sms_cost) as total_sms_cost,
                    SUM(ca.push_cost) as total_push_cost,
                    SUM(ca.total_cost) as total_cost
                FROM communication_analytics ca
                JOIN broadcasts b ON ca.broadcast_id = b.id
                WHERE b.store_id = $1
                AND ($2::timestamp IS NULL OR b.created_at >= $2)
                AND ($3::timestamp IS NULL OR b.created_at <= $3)
            """, uuid.UUID(store_id) if store_id else None,
                start_date, end_date)

            return {
                "success": True,
                "overview": dict(stats) if stats else {},
                "channel_breakdown": [dict(s) for s in channel_stats],
                "cost_summary": dict(cost_stats) if cost_stats else {}
            }

    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))