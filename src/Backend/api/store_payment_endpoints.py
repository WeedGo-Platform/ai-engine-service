"""
Store Payment Terminal and Device Management API Endpoints
Handles payment terminals and device registration for stores
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
import json
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime

import asyncpg
from core.authentication import get_current_user
import os

# Create database connection helper
async def get_db_connection():
    """Get async database connection"""
    return await asyncpg.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5434)),
        database=os.getenv('DB_NAME', 'ai_engine'),
        user=os.getenv('DB_USER', 'weedgo'),
        password=os.getenv('DB_PASSWORD', 'your_password_here')
    )

router = APIRouter(prefix="/api", tags=["store-payment"])


# =====================================================
# PYDANTIC MODELS
# =====================================================

class CloverTerminal(BaseModel):
    """Clover payment terminal configuration"""
    id: str
    terminal_id: str
    merchant_id: str
    name: str
    status: str = "active"
    last_seen: Optional[datetime] = None

class PaymentMethods(BaseModel):
    """Accepted payment methods"""
    tap: bool = True
    chip: bool = True
    swipe: bool = True
    cash: bool = True
    manual_entry: bool = False

class TipSettings(BaseModel):
    """Tip configuration"""
    enabled: bool = True
    options: List[int] = Field(default_factory=lambda: [15, 18, 20, 0])
    custom_tip: bool = True

class StorePaymentTerminals(BaseModel):
    """Store payment terminal settings"""
    provider: str = "clover"
    terminals: List[CloverTerminal] = Field(default_factory=list)
    default_terminal: Optional[str] = None
    accepted_methods: PaymentMethods = Field(default_factory=PaymentMethods)
    tip_settings: TipSettings = Field(default_factory=TipSettings)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class StoreDevice(BaseModel):
    """Store device configuration"""
    id: str
    name: str
    platform: str  # 'web' or 'tablet'
    app_type: str  # 'pos', 'kiosk', 'menu'
    device_id: str
    status: str = "active"
    last_activity: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class StoreDevices(BaseModel):
    """Store device settings"""
    devices: List[StoreDevice] = Field(default_factory=list)


# =====================================================
# PAYMENT TERMINAL ENDPOINTS
# =====================================================

@router.get("/stores/{store_id}/payment-terminals", response_model=StorePaymentTerminals)
async def get_store_payment_terminals(
    store_id: UUID
):
    """Get payment terminal settings for a store"""
    db = await get_db_connection()
    try:
        # First check if the store has a payment_terminals field in settings
        query = """
            SELECT settings
            FROM stores
            WHERE id = $1
        """

        result = await db.fetchrow(query, store_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store not found"
            )

        settings = result['settings'] or {}

        # Parse JSON if it's a string
        if isinstance(settings, str):
            settings = json.loads(settings) if settings else {}

        # Get payment terminal settings from the store settings
        payment_settings = settings.get('payment', {})

        # Return payment terminal configuration
        return StorePaymentTerminals(
            provider=payment_settings.get('provider', 'clover'),
            terminals=payment_settings.get('terminals', []),
            default_terminal=payment_settings.get('default_terminal'),
            accepted_methods=payment_settings.get('accepted_methods', {
                'tap': True,
                'chip': True,
                'swipe': True,
                'cash': True,
                'manual_entry': False
            }),
            tip_settings=payment_settings.get('tip_settings', {
                'enabled': True,
                'options': [15, 18, 20, 0],
                'custom_tip': True
            })
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving payment terminal settings: {str(e)}"
        )
    finally:
        await db.close()

@router.put("/stores/{store_id}/payment-terminals", response_model=StorePaymentTerminals)
async def update_store_payment_terminals(
    store_id: UUID,
    terminals: StorePaymentTerminals
):
    """Update payment terminal settings for a store"""
    db = await get_db_connection()
    try:
        # Get current store settings
        query = """
            SELECT settings
            FROM stores
            WHERE id = $1
        """

        result = await db.fetchrow(query, store_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store not found"
            )

        settings = result['settings'] or {}

        # Parse JSON if it's a string
        if isinstance(settings, str):
            settings = json.loads(settings) if settings else {}

        # Update payment terminal settings
        settings['payment'] = terminals.dict(exclude_unset=True)

        # Update database
        update_query = """
            UPDATE stores
            SET settings = $1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
            RETURNING settings
        """

        result = await db.fetchrow(update_query, json.dumps(settings), store_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store not found"
            )

        updated_settings = json.loads(result['settings']) if isinstance(result['settings'], str) else result['settings']
        payment_settings = updated_settings.get('payment', {})

        return StorePaymentTerminals(**payment_settings)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating payment terminal settings: {str(e)}"
        )
    finally:
        await db.close()


# =====================================================
# DEVICE MANAGEMENT ENDPOINTS
# =====================================================

@router.get("/stores/{store_id}/devices", response_model=StoreDevices)
async def get_store_devices(
    store_id: UUID
):
    """Get device settings for a store"""
    db = await get_db_connection()
    try:
        query = """
            SELECT settings
            FROM stores
            WHERE id = $1
        """

        result = await db.fetchrow(query, store_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store not found"
            )

        settings = result['settings'] or {}

        # Parse JSON if it's a string
        if isinstance(settings, str):
            settings = json.loads(settings) if settings else {}

        # Get device settings from the store settings
        device_settings = settings.get('devices', {})

        return StoreDevices(
            devices=device_settings.get('devices', [])
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving device settings: {str(e)}"
        )
    finally:
        await db.close()

@router.put("/stores/{store_id}/devices", response_model=StoreDevices)
async def update_store_devices(
    store_id: UUID,
    devices: StoreDevices
):
    """Update device settings for a store"""
    db = await get_db_connection()
    try:
        # Get current store settings
        query = """
            SELECT settings
            FROM stores
            WHERE id = $1
        """

        result = await db.fetchrow(query, store_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store not found"
            )

        settings = result['settings'] or {}

        # Parse JSON if it's a string
        if isinstance(settings, str):
            settings = json.loads(settings) if settings else {}

        # Update device settings
        settings['devices'] = devices.dict(exclude_unset=True)

        # Update database
        update_query = """
            UPDATE stores
            SET settings = $1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
            RETURNING settings
        """

        result = await db.fetchrow(update_query, json.dumps(settings), store_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store not found"
            )

        updated_settings = json.loads(result['settings']) if isinstance(result['settings'], str) else result['settings']
        device_settings = updated_settings.get('devices', {})

        return StoreDevices(**device_settings)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating device settings: {str(e)}"
        )
    finally:
        await db.close()

@router.post("/stores/{store_id}/devices/register")
async def register_device(
    store_id: UUID,
    device: Dict[str, Any]
):
    """Register a new device for a store"""
    db = await get_db_connection()
    try:
        # Get current store settings
        query = """
            SELECT settings
            FROM stores
            WHERE id = $1
        """

        result = await db.fetchrow(query, store_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store not found"
            )

        settings = result['settings'] or {}

        # Parse JSON if it's a string
        if isinstance(settings, str):
            settings = json.loads(settings) if settings else {}

        # Get current devices
        device_settings = settings.get('devices', {})
        devices = device_settings.get('devices', [])

        # Add new device
        new_device = {
            'id': f"device_{datetime.utcnow().timestamp()}",
            'name': device.get('name'),
            'platform': device.get('platform'),
            'app_type': device.get('app_type'),
            'device_id': device.get('device_id'),
            'status': 'active',
            'last_activity': datetime.utcnow().isoformat()
        }

        devices.append(new_device)
        device_settings['devices'] = devices
        settings['devices'] = device_settings

        # Update database
        update_query = """
            UPDATE stores
            SET settings = $1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
        """

        await db.execute(update_query, json.dumps(settings), store_id)

        return {
            "message": "Device registered successfully",
            "device": new_device
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registering device: {str(e)}"
        )
    finally:
        await db.close()

@router.delete("/stores/{store_id}/devices/{device_id}")
async def unregister_device(
    store_id: UUID,
    device_id: str
):
    """Unregister a device from a store"""
    db = await get_db_connection()
    try:
        # Get current store settings
        query = """
            SELECT settings
            FROM stores
            WHERE id = $1
        """

        result = await db.fetchrow(query, store_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store not found"
            )

        settings = result['settings'] or {}

        # Parse JSON if it's a string
        if isinstance(settings, str):
            settings = json.loads(settings) if settings else {}

        # Get current devices
        device_settings = settings.get('devices', {})
        devices = device_settings.get('devices', [])

        # Remove device
        devices = [d for d in devices if d.get('id') != device_id]
        device_settings['devices'] = devices
        settings['devices'] = device_settings

        # Update database
        update_query = """
            UPDATE stores
            SET settings = $1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
        """

        await db.execute(update_query, json.dumps(settings), store_id)

        return {"message": "Device unregistered successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error unregistering device: {str(e)}"
        )
    finally:
        await db.close()