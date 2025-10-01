"""
Device Management API Endpoints
Handles device registration, pairing, and management for kiosk, POS, and menu displays
"""

import asyncpg
import logging
import bcrypt
import jwt
import json
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/kiosk/device", tags=["🖥️ Device Management"])

# JWT Secret - in production, use environment variable
SECRET_KEY = "your-secret-key-here-change-in-production"  # TODO: Move to env

# =====================================================
# REQUEST/RESPONSE MODELS
# =====================================================

class DevicePairRequest(BaseModel):
    """Request to pair a device"""
    device_id: str = Field(..., description="Device ID assigned by admin")
    passcode: str = Field(..., min_length=4, max_length=10, description="4-digit passcode")
    device_info: Dict[str, Any] = Field(default_factory=dict, description="Hardware information")

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "KIOSK-001",
                "passcode": "1234",
                "device_info": {
                    "hardware_id": "expo-session-abc123",
                    "platform": "ios",
                    "app_version": "1.0.0",
                    "model": "iPad Pro"
                }
            }
        }


class DevicePairResponse(BaseModel):
    """Response from successful device pairing"""
    success: bool
    tenant_id: Optional[str] = None
    store_id: Optional[str] = None
    device_token: Optional[str] = None
    device_config: Optional[Dict[str, Any]] = None
    tenant_config: Optional[Dict[str, Any]] = None
    store_config: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None


class DeviceHeartbeatRequest(BaseModel):
    """Device heartbeat with metrics"""
    status: str = "active"
    metrics: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "status": "active",
                "metrics": {
                    "sessions_today": 45,
                    "orders_today": 12,
                    "last_activity": "2025-10-01T15:45:00Z"
                }
            }
        }


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
            password=os.getenv('DB_PASSWORD', 'weedgo123'),
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


def verify_passcode(passcode: str, hashed: str) -> bool:
    """Verify passcode against bcrypt hash"""
    try:
        return bcrypt.checkpw(passcode.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        logger.error(f"Error verifying passcode: {e}")
        return False


def generate_device_token(payload: Dict[str, Any]) -> str:
    """Generate JWT token for device (never expires per requirements)"""
    token_payload = {
        **payload,
        'iat': datetime.utcnow(),
        # No exp field = token never expires
    }
    return jwt.encode(token_payload, SECRET_KEY, algorithm='HS256')


def verify_device_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode device token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {e}")
        return None


async def find_device_in_stores(db: asyncpg.Connection, device_id: str) -> Optional[Dict[str, Any]]:
    """Find device across all stores"""
    query = """
        SELECT
            s.id as store_id,
            s.tenant_id,
            s.settings as settings,
            s.name as store_name,
            s.address,
            s.phone,
            s.email,
            s.hours,
            s.tax_rate,
            s.timezone,
            t.name as tenant_name,
            t.code as tenant_code,
            t.logo_url as tenant_logo,
            t.settings as tenant_settings
        FROM stores s
        JOIN tenants t ON s.tenant_id = t.id
        WHERE s.settings->'devices' @> $1::jsonb
        AND s.status = 'active'
        LIMIT 1
    """

    # Create JSONB query for device_id
    device_query = json.dumps([{"device_id": device_id}])

    row = await db.fetchrow(query, device_query)

    if not row:
        return None

    # Parse settings and find the specific device
    settings = json.loads(row['settings']) if isinstance(row['settings'], str) else row['settings']
    devices = settings.get('devices', [])

    device = next((d for d in devices if d['device_id'] == device_id), None)

    if not device:
        return None

    return {
        'store_id': str(row['store_id']),
        'tenant_id': str(row['tenant_id']),
        'store_name': row['store_name'],
        'store_address': row['address'],
        'store_phone': row['phone'],
        'store_email': row['email'],
        'store_hours': row['hours'],
        'store_tax_rate': float(row['tax_rate']) if row['tax_rate'] else 0.13,
        'store_timezone': row['timezone'],
        'tenant_name': row['tenant_name'],
        'tenant_code': row['tenant_code'],
        'tenant_logo': row['tenant_logo'],
        'tenant_settings': row['tenant_settings'],
        'device': device,
    }


async def update_device_metadata(
    db: asyncpg.Connection,
    store_id: str,
    device_id: str,
    updates: Dict[str, Any]
) -> bool:
    """Update device metadata in store settings"""
    try:
        # Get current settings
        query = "SELECT settings FROM stores WHERE id = $1"
        row = await db.fetchrow(query, UUID(store_id))

        if not row:
            return False

        settings = json.loads(row['settings']) if isinstance(row['settings'], str) else row['settings']
        devices = settings.get('devices', [])

        # Find and update device
        device_updated = False
        for device in devices:
            if device['device_id'] == device_id:
                device.update(updates)
                device['updated_at'] = datetime.utcnow().isoformat()
                device_updated = True
                break

        if not device_updated:
            return False

        # Update store settings
        update_query = """
            UPDATE stores
            SET settings = $1, updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
        """
        await db.execute(update_query, json.dumps(settings), UUID(store_id))

        return True

    except Exception as e:
        logger.error(f"Error updating device metadata: {e}")
        return False


# =====================================================
# API ENDPOINTS
# =====================================================

@router.post("/pair", response_model=DevicePairResponse)
async def pair_device(
    request: DevicePairRequest,
    db: asyncpg.Connection = Depends(get_db)
):
    """
    Pair a device with store/tenant using Device ID and Passcode

    **Flow:**
    1. Find device in stores.settings.devices by device_id
    2. Verify passcode (no lockout per requirements)
    3. Validate device status is active
    4. Generate device token (never expires)
    5. Update device metadata (paired_at, last_seen, hardware_id)
    6. Return tenant_id, store_id, and full configuration

    **Note:** Location is info-only, not used for verification
    """
    try:
        logger.info(f"Device pairing requested for device_id: {request.device_id}")

        # 1. Find device across all stores
        result = await find_device_in_stores(db, request.device_id.upper())

        if not result:
            logger.warning(f"Device not found: {request.device_id}")
            return DevicePairResponse(
                success=False,
                error="device_not_found",
                message=f"Device '{request.device_id}' not found in any store. Please contact admin."
            )

        device = result['device']

        # 2. Check device status
        if device.get('status') == 'inactive':
            logger.warning(f"Device is inactive: {request.device_id}")
            return DevicePairResponse(
                success=False,
                error="device_inactive",
                message="This device has been deactivated. Please contact admin."
            )

        # 3. Verify passcode (no lockout policy)
        passcode_hash = device.get('passcode_hash')
        if not passcode_hash:
            logger.error(f"Device has no passcode set: {request.device_id}")
            return DevicePairResponse(
                success=False,
                error="device_not_configured",
                message="Device is not properly configured. Please contact admin."
            )

        if not verify_passcode(request.passcode, passcode_hash):
            logger.warning(f"Invalid passcode for device: {request.device_id}")
            return DevicePairResponse(
                success=False,
                error="invalid_passcode",
                message="Invalid passcode. Please try again."
            )

        # 4. Generate device token (never expires)
        device_token = generate_device_token({
            'device_id': request.device_id.upper(),
            'tenant_id': result['tenant_id'],
            'store_id': result['store_id'],
            'device_type': device.get('device_type', 'kiosk'),
        })

        # 5. Update device metadata
        now = datetime.utcnow().isoformat()
        metadata_updates = {
            'paired_at': device.get('paired_at') or now,  # Keep original if already paired
            'last_seen': now,
            'status': 'active',
            'metadata': {
                **device.get('metadata', {}),
                **request.device_info,
                'last_pairing': now,
            }
        }

        await update_device_metadata(
            db,
            result['store_id'],
            request.device_id.upper(),
            metadata_updates
        )

        # 6. Build response
        logger.info(f"Device paired successfully: {request.device_id} -> Store: {result['store_id']}")

        return DevicePairResponse(
            success=True,
            tenant_id=result['tenant_id'],
            store_id=result['store_id'],
            device_token=device_token,
            device_config={
                'device_id': device['device_id'],
                'device_type': device['device_type'],
                'name': device['name'],
                'location': device['location'],
                'permissions': device.get('permissions', {}),
                'configuration': device.get('configuration', {}),
                'status': 'active',
                'paired_at': now,
            },
            tenant_config={
                'tenant_id': result['tenant_id'],
                'name': result['tenant_name'],
                'code': result['tenant_code'],
                'logo_url': result['tenant_logo'],
                'settings': result.get('tenant_settings', {}),
            },
            store_config={
                'store_id': result['store_id'],
                'name': result['store_name'],
                'address': result.get('store_address', {}),
                'phone': result.get('store_phone'),
                'email': result.get('store_email'),
                'hours': result.get('store_hours', {}),
                'tax_rate': result.get('store_tax_rate', 0.13),
                'timezone': result.get('store_timezone', 'America/Toronto'),
            },
        )

    except Exception as e:
        logger.error(f"Error during device pairing: {e}", exc_info=True)
        return DevicePairResponse(
            success=False,
            error="server_error",
            message="An error occurred during pairing. Please try again."
        )


@router.post("/heartbeat")
async def device_heartbeat(
    request: DeviceHeartbeatRequest,
    authorization: Optional[str] = Header(None),
    x_device_id: Optional[str] = Header(None, alias="X-Device-Id"),
    db: asyncpg.Connection = Depends(get_db)
):
    """
    Device heartbeat to update last_seen and report metrics

    Sends periodic heartbeat to:
    - Update device last_seen timestamp
    - Report device metrics (sessions, orders, etc.)
    - Check for configuration updates
    """
    try:
        # Verify device token
        if not authorization or not authorization.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization token")

        token = authorization.split(' ')[1]
        payload = verify_device_token(token)

        if not payload:
            raise HTTPException(status_code=401, detail="Invalid device token")

        device_id = payload.get('device_id') or x_device_id

        if not device_id:
            raise HTTPException(status_code=400, detail="Device ID required")

        # Find device
        result = await find_device_in_stores(db, device_id)

        if not result:
            raise HTTPException(status_code=404, detail="Device not found")

        # Update last_seen and metrics
        await update_device_metadata(
            db,
            result['store_id'],
            device_id,
            {
                'last_seen': datetime.utcnow().isoformat(),
                'status': request.status,
                'metadata': {
                    **result['device'].get('metadata', {}),
                    'last_heartbeat': datetime.utcnow().isoformat(),
                    'metrics': request.metrics,
                }
            }
        )

        logger.debug(f"Heartbeat received from device: {device_id}")

        return {
            "success": True,
            "message": "Heartbeat received",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing heartbeat: {e}")
        raise HTTPException(status_code=500, detail="Failed to process heartbeat")


@router.get("/info")
async def get_device_info(
    authorization: Optional[str] = Header(None),
    x_device_id: Optional[str] = Header(None, alias="X-Device-Id"),
    db: asyncpg.Connection = Depends(get_db)
):
    """
    Get current device configuration

    Returns latest device configuration from server
    Useful for checking if device needs to update settings
    """
    try:
        # Verify device token
        if not authorization or not authorization.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization token")

        token = authorization.split(' ')[1]
        payload = verify_device_token(token)

        if not payload:
            raise HTTPException(status_code=401, detail="Invalid device token")

        device_id = payload.get('device_id') or x_device_id

        if not device_id:
            raise HTTPException(status_code=400, detail="Device ID required")

        # Find device
        result = await find_device_in_stores(db, device_id)

        if not result:
            raise HTTPException(status_code=404, detail="Device not found")

        device = result['device']

        return {
            "success": True,
            "device_config": {
                'device_id': device['device_id'],
                'device_type': device['device_type'],
                'name': device['name'],
                'location': device['location'],
                'permissions': device.get('permissions', {}),
                'configuration': device.get('configuration', {}),
                'status': device.get('status'),
                'paired_at': device.get('paired_at'),
                'last_seen': device.get('last_seen'),
            },
            "tenant_id": result['tenant_id'],
            "store_id": result['store_id'],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get device info")


# Export router
__all__ = ['router']
