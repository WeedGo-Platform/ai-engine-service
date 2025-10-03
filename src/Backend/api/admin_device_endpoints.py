"""
Admin Device Management API Endpoints
CRUD operations for managing devices in stores
"""

import asyncpg
import logging
import bcrypt
import json
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/admin/stores", tags=["⚙️ Admin - Device Management"])

# =====================================================
# REQUEST/RESPONSE MODELS
# =====================================================

class DeviceCreateRequest(BaseModel):
    """Request to create a new device"""
    device_id: str = Field(..., min_length=3, max_length=50, description="Unique device identifier")
    device_type: str = Field(..., description="Device type: kiosk, pos, or menu_display")
    name: str = Field(..., min_length=3, max_length=100, description="Human-readable device name")
    location: str = Field(..., min_length=2, max_length=100, description="Physical location")
    passcode: str = Field(..., min_length=4, max_length=10, description="4-digit passcode")
    permissions: Dict[str, Any] = Field(default_factory=dict, description="Device permissions")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Device configuration")

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "KIOSK-001",
                "device_type": "kiosk",
                "name": "Front Entrance Kiosk",
                "location": "Main Floor",
                "passcode": "1234",
                "permissions": {
                    "can_process_orders": True,
                    "can_access_inventory": True
                },
                "configuration": {
                    "idle_timeout": 120,
                    "enable_budtender": True
                }
            }
        }


class DeviceUpdateRequest(BaseModel):
    """Request to update device"""
    name: Optional[str] = None
    location: Optional[str] = None
    passcode: Optional[str] = Field(None, min_length=4, max_length=10)
    status: Optional[str] = Field(None, description="active or inactive")
    permissions: Optional[Dict[str, Any]] = None
    configuration: Optional[Dict[str, Any]] = None


class DeviceResponse(BaseModel):
    """Device information response"""
    device_id: str
    device_type: str
    name: str
    location: str
    status: str
    paired_at: Optional[str] = None
    last_seen: Optional[str] = None
    created_at: str
    updated_at: str
    permissions: Dict[str, Any]
    configuration: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)


# =====================================================
# DATABASE CONNECTION
# =====================================================

db_pool = None

async def get_db_pool():
    """Get or create database connection pool"""
    global db_pool
    if db_pool is None:
        import os
        db_pool = await asyncpg.create_pool(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5434)),
            database=os.getenv('DB_NAME', 'ai_engine'),
            user=os.getenv('DB_USER', 'weedgo'),
            password=os.getenv('DB_PASSWORD', 'your_password_here'),
            min_size=1,
            max_size=10
        )
    return db_pool


async def get_db():
    """Get database connection from pool"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        yield conn


# =====================================================
# UTILITY FUNCTIONS
# =====================================================

def hash_passcode(passcode: str) -> str:
    """Hash passcode using bcrypt"""
    return bcrypt.hashpw(passcode.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')


async def verify_admin_access(
    store_id: str,
    authorization: Optional[str],
    x_tenant_id: Optional[str],
    db: asyncpg.Connection
) -> bool:
    """
    Verify admin has access to this store

    TODO: Implement proper admin authentication
    For now, just check if store exists and matches tenant
    """
    try:
        query = """
            SELECT id, tenant_id
            FROM stores
            WHERE id = $1
            AND ($2::UUID IS NULL OR tenant_id = $2::UUID)
        """
        row = await db.fetchrow(query, UUID(store_id), UUID(x_tenant_id) if x_tenant_id else None)
        return row is not None
    except Exception as e:
        logger.error(f"Error verifying admin access: {e}")
        return False


# =====================================================
# API ENDPOINTS
# =====================================================

@router.post("/{store_id}/devices", response_model=DeviceResponse, status_code=201)
async def create_device(
    store_id: str,
    request: DeviceCreateRequest,
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-Id"),
    db: asyncpg.Connection = Depends(get_db)
):
    """
    Create a new device for a store

    **Requires:** Admin authentication (Authorization header)

    **Flow:**
    1. Verify admin has access to store
    2. Validate device_type
    3. Check if device_id already exists in store
    4. Hash passcode
    5. Add device to store.settings.devices array
    6. Return device info
    """
    try:
        # Verify admin access
        has_access = await verify_admin_access(store_id, authorization, x_tenant_id, db)
        if not has_access:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to manage devices for this store. Please contact your administrator."
            )

        # Validate device type
        valid_types = ['kiosk', 'pos', 'menu_display']
        if request.device_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid device type '{request.device_type}'. Must be one of: {', '.join(valid_types)}"
            )

        # Normalize device_id to uppercase
        device_id = request.device_id.upper()

        # Get current store settings
        query = "SELECT settings FROM stores WHERE id = $1"
        row = await db.fetchrow(query, UUID(store_id))

        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"Store with ID '{store_id}' not found. Please verify the store exists."
            )

        settings = json.loads(row['settings']) if isinstance(row['settings'], str) else (row['settings'] or {})
        devices = settings.get('devices', [])

        # Check if device already exists
        if any(d['device_id'] == device_id for d in devices):
            raise HTTPException(
                status_code=409,
                detail=f"Device ID '{device_id}' already exists in this store. Please choose a different Device ID."
            )

        # Hash passcode
        passcode_hash = hash_passcode(request.passcode)

        # Create device object
        now = datetime.utcnow().isoformat()
        new_device = {
            'device_id': device_id,
            'device_type': request.device_type,
            'name': request.name,
            'location': request.location,
            'passcode_hash': passcode_hash,
            'status': 'pending_pairing',
            'paired_at': None,
            'last_seen': None,
            'created_at': now,
            'created_by': 'admin',  # TODO: Get from auth context
            'updated_at': now,
            'metadata': {},
            'permissions': request.permissions,
            'configuration': request.configuration,
        }

        # Add device to array
        devices.append(new_device)
        settings['devices'] = devices

        # Update store
        update_query = """
            UPDATE stores
            SET settings = $1, updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
        """
        await db.execute(update_query, json.dumps(settings), UUID(store_id))

        logger.info(f"Device created: {device_id} in store {store_id}")

        # Return device (without passcode_hash)
        response_device = {k: v for k, v in new_device.items() if k != 'passcode_hash'}
        return DeviceResponse(**response_device)

    except HTTPException:
        raise
    except asyncpg.exceptions.PostgresError as e:
        logger.error(f"Database error creating device: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="A database error occurred while creating the device. Please try again or contact support."
        )
    except Exception as e:
        logger.error(f"Unexpected error creating device: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while creating the device. Please try again or contact support if the issue persists."
        )


@router.get("/{store_id}/devices", response_model=List[DeviceResponse])
async def list_devices(
    store_id: str,
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-Id"),
    db: asyncpg.Connection = Depends(get_db)
):
    """
    List all devices for a store

    Returns all devices configured for the store
    """
    try:
        # Verify admin access
        has_access = await verify_admin_access(store_id, authorization, x_tenant_id, db)
        if not has_access:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to access devices for this store."
            )

        # Get store settings
        query = "SELECT settings FROM stores WHERE id = $1"
        row = await db.fetchrow(query, UUID(store_id))

        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"Store with ID '{store_id}' not found."
            )

        settings = json.loads(row['settings']) if isinstance(row['settings'], str) else (row['settings'] or {})
        devices = settings.get('devices', [])

        # Remove passcode_hash from response
        response_devices = [
            {k: v for k, v in device.items() if k != 'passcode_hash'}
            for device in devices
        ]

        return [DeviceResponse(**device) for device in response_devices]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing devices: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving devices. Please try again."
        )


@router.get("/{store_id}/devices/{device_id}", response_model=DeviceResponse)
async def get_device(
    store_id: str,
    device_id: str,
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-Id"),
    db: asyncpg.Connection = Depends(get_db)
):
    """Get specific device details"""
    try:
        # Verify admin access
        has_access = await verify_admin_access(store_id, authorization, x_tenant_id, db)
        if not has_access:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to access devices for this store."
            )

        # Get store settings
        query = "SELECT settings FROM stores WHERE id = $1"
        row = await db.fetchrow(query, UUID(store_id))

        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"Store with ID '{store_id}' not found."
            )

        settings = json.loads(row['settings']) if isinstance(row['settings'], str) else (row['settings'] or {})
        devices = settings.get('devices', [])

        # Find device
        device_id_upper = device_id.upper()
        device = next((d for d in devices if d['device_id'] == device_id_upper), None)

        if not device:
            raise HTTPException(
                status_code=404,
                detail=f"Device '{device_id}' not found in this store."
            )

        # Remove passcode_hash
        response_device = {k: v for k, v in device.items() if k != 'passcode_hash'}
        return DeviceResponse(**response_device)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving the device. Please try again."
        )


@router.put("/{store_id}/devices/{device_id}", response_model=DeviceResponse)
async def update_device(
    store_id: str,
    device_id: str,
    request: DeviceUpdateRequest,
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-Id"),
    db: asyncpg.Connection = Depends(get_db)
):
    """
    Update device information

    Can update: name, location, passcode, status, permissions, configuration
    """
    try:
        # Verify admin access
        has_access = await verify_admin_access(store_id, authorization, x_tenant_id, db)
        if not has_access:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to access devices for this store."
            )

        # Get store settings
        query = "SELECT settings FROM stores WHERE id = $1"
        row = await db.fetchrow(query, UUID(store_id))

        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"Store with ID '{store_id}' not found."
            )

        settings = json.loads(row['settings']) if isinstance(row['settings'], str) else (row['settings'] or {})
        devices = settings.get('devices', [])

        # Find device
        device_id_upper = device_id.upper()
        device_index = next((i for i, d in enumerate(devices) if d['device_id'] == device_id_upper), None)

        if device_index is None:
            raise HTTPException(status_code=404, detail="Device not found")

        # Update device fields
        device = devices[device_index]

        if request.name is not None:
            device['name'] = request.name

        if request.location is not None:
            device['location'] = request.location

        if request.passcode is not None:
            device['passcode_hash'] = hash_passcode(request.passcode)

        if request.status is not None:
            if request.status not in ['active', 'inactive', 'pending_pairing']:
                raise HTTPException(status_code=400, detail="Invalid status")
            device['status'] = request.status

        if request.permissions is not None:
            device['permissions'] = {**device.get('permissions', {}), **request.permissions}

        if request.configuration is not None:
            device['configuration'] = {**device.get('configuration', {}), **request.configuration}

        device['updated_at'] = datetime.utcnow().isoformat()

        # Update store
        update_query = """
            UPDATE stores
            SET settings = $1, updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
        """
        await db.execute(update_query, json.dumps(settings), UUID(store_id))

        logger.info(f"Device updated: {device_id} in store {store_id}")

        # Return device (without passcode_hash)
        response_device = {k: v for k, v in device.items() if k != 'passcode_hash'}
        return DeviceResponse(**response_device)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating device: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while updating the device. Please try again."
        )


@router.delete("/{store_id}/devices/{device_id}")
async def delete_device(
    store_id: str,
    device_id: str,
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-Id"),
    db: asyncpg.Connection = Depends(get_db)
):
    """Delete a device from store"""
    try:
        # Verify admin access
        has_access = await verify_admin_access(store_id, authorization, x_tenant_id, db)
        if not has_access:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to access devices for this store."
            )

        # Get store settings
        query = "SELECT settings FROM stores WHERE id = $1"
        row = await db.fetchrow(query, UUID(store_id))

        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"Store with ID '{store_id}' not found."
            )

        settings = json.loads(row['settings']) if isinstance(row['settings'], str) else (row['settings'] or {})
        devices = settings.get('devices', [])

        # Find and remove device
        device_id_upper = device_id.upper()
        original_count = len(devices)
        devices = [d for d in devices if d['device_id'] != device_id_upper]

        if len(devices) == original_count:
            raise HTTPException(status_code=404, detail="Device not found")

        settings['devices'] = devices

        # Update store
        update_query = """
            UPDATE stores
            SET settings = $1, updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
        """
        await db.execute(update_query, json.dumps(settings), UUID(store_id))

        logger.info(f"Device deleted: {device_id} from store {store_id}")

        return {
            "success": True,
            "message": f"Device '{device_id}' deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting device: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while deleting the device. Please try again."
        )


# Export router
__all__ = ['router']
