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

# =====================================================
# PAYMENT CONFIG ENDPOINT (for frontend compatibility)
# =====================================================

@router.get("/stores/{store_id}/payment-config")
async def get_store_payment_config(store_id: UUID):
    """Get payment configuration for a store (Clover config)"""
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

        # Get payment configuration
        payment_config = settings.get('payment', {})
        online_payment = settings.get('onlinePayment', {})

        # Return Clover-specific configuration for the frontend
        # Note: Database stores in camelCase
        return {
            "provider": payment_config.get('provider', online_payment.get('provider', 'clover')),
            "enabled": online_payment.get('enabled', False),
            "accessToken": online_payment.get('accessToken', online_payment.get('access_token', '')),
            "merchantId": online_payment.get('merchantId', online_payment.get('merchant_id', '')),
            "environment": online_payment.get('environment', 'sandbox'),
            "terminals": payment_config.get('terminals', []),
            "defaultTerminal": payment_config.get('default_terminal'),
            "acceptedMethods": payment_config.get('accepted_methods', {
                'tap': True,
                'chip': True,
                'swipe': True,
                'cash': True,
                'manual_entry': False
            }),
            "tipSettings": payment_config.get('tip_settings', {
                'enabled': True,
                'options': [15, 18, 20, 0],
                'custom_tip': True
            })
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving payment configuration: {str(e)}"
        )
    finally:
        await db.close()

@router.put("/stores/{store_id}/payment-config")
async def update_store_payment_config(
    store_id: UUID,
    config: Dict[str, Any]
):
    """Update payment configuration for a store"""
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

        # Update both payment and online payment settings based on provided config
        if 'payment' not in settings:
            settings['payment'] = {}
        if 'onlinePayment' not in settings:
            settings['onlinePayment'] = {}

        # Map frontend fields to backend structure
        if 'provider' in config:
            settings['payment']['provider'] = config['provider']
            settings['onlinePayment']['provider'] = config['provider']

        if 'enabled' in config:
            settings['onlinePayment']['enabled'] = config['enabled']

        if 'accessToken' in config:
            settings['onlinePayment']['access_token'] = config['accessToken']

        if 'merchantId' in config:
            settings['onlinePayment']['merchant_id'] = config['merchantId']

        if 'environment' in config:
            settings['onlinePayment']['environment'] = config['environment']

        if 'terminals' in config:
            settings['payment']['terminals'] = config['terminals']

        if 'defaultTerminal' in config:
            settings['payment']['default_terminal'] = config['defaultTerminal']

        if 'acceptedMethods' in config:
            settings['payment']['accepted_methods'] = config['acceptedMethods']

        if 'tipSettings' in config:
            settings['payment']['tip_settings'] = config['tipSettings']

        # Update database
        update_query = """
            UPDATE stores
            SET settings = $1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
        """

        await db.execute(update_query, json.dumps(settings), store_id)

        # Return updated config in frontend format
        return {
            "provider": settings['payment'].get('provider', settings['onlinePayment'].get('provider', 'clover')),
            "enabled": settings['onlinePayment'].get('enabled', False),
            "accessToken": settings['onlinePayment'].get('access_token', ''),
            "merchantId": settings['onlinePayment'].get('merchant_id', ''),
            "environment": settings['onlinePayment'].get('environment', 'sandbox'),
            "terminals": settings['payment'].get('terminals', []),
            "defaultTerminal": settings['payment'].get('default_terminal'),
            "acceptedMethods": settings['payment'].get('accepted_methods', {
                'tap': True,
                'chip': True,
                'swipe': True,
                'cash': True,
                'manual_entry': False
            }),
            "tipSettings": settings['payment'].get('tip_settings', {
                'enabled': True,
                'options': [15, 18, 20, 0],
                'custom_tip': True
            })
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating payment configuration: {str(e)}"
        )
    finally:
        await db.close()

# =====================================================
# ONLINE PAYMENT ENDPOINTS
# =====================================================

class OnlinePaymentConfig(BaseModel):
    """Online payment configuration for ecommerce"""
    enabled: bool = False
    provider: str = Field(default="clover", description="Payment provider (clover, moneris)")
    access_token: str = Field(default="", description="Encrypted access token for the provider")
    merchant_id: Optional[str] = Field(default=None, description="Merchant ID for Clover")
    environment: str = Field(default="sandbox", description="Environment: sandbox or production")
    webhook_url: Optional[str] = None
    supported_card_types: List[str] = Field(default_factory=lambda: ["visa", "mastercard", "amex"])
    require_3ds: bool = Field(default=False, description="Require 3D Secure authentication")
    platform_fee_percentage: float = Field(default=2.0, description="Platform fee percentage")
    platform_fee_fixed: float = Field(default=0.0, description="Fixed platform fee")


class TestPaymentConfigRequest(BaseModel):
    """Request model for testing payment configuration"""
    provider: str
    config: Dict[str, Any]


@router.get("/stores/{store_id}/online-payment", response_model=OnlinePaymentConfig)
async def get_store_online_payment_config(store_id: UUID):
    """Get online payment configuration for a store"""
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
        online_payment = settings.get('onlinePayment', {})

        return OnlinePaymentConfig(**online_payment)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving online payment configuration: {str(e)}"
        )
    finally:
        await db.close()


@router.put("/stores/{store_id}/online-payment", response_model=OnlinePaymentConfig)
async def update_store_online_payment_config(
    store_id: UUID,
    config: OnlinePaymentConfig
):
    """Update online payment configuration for a store"""
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

        # Update online payment settings
        settings['onlinePayment'] = config.dict()

        # Save updated settings
        update_query = """
            UPDATE stores
            SET settings = $1,
                updated_at = NOW()
            WHERE id = $2
        """

        await db.execute(update_query, json.dumps(settings), store_id)

        return config

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating online payment configuration: {str(e)}"
        )
    finally:
        await db.close()


@router.post("/stores/{store_id}/payment/test")
async def test_payment_configuration(
    store_id: UUID,
    request: TestPaymentConfigRequest
):
    """Test payment provider connection"""
    try:
        # Validate required fields
        if not request.config.get('accessToken'):
            return {
                "success": False,
                "message": "Access token is required"
            }

        # Import payment providers
        try:
            from services.payment.clover_provider import CloverProvider
            from services.payment.moneris_provider import MonerisProvider
        except ImportError as e:
            return {
                "success": False,
                "message": f"Payment provider module not found: {str(e)}"
            }

        # Initialize the appropriate provider
        provider_config = {
            'access_token': request.config.get('accessToken'),
            'merchant_id': request.config.get('merchantId'),
            'environment': request.config.get('environment', 'sandbox'),
            'store_id': str(store_id)
        }

        if request.provider == 'clover':
            provider = CloverProvider(provider_config)
        elif request.provider == 'moneris':
            # Add Moneris specific config
            provider_config['store_id'] = request.config.get('storeId')  # Moneris store ID
            provider_config['api_token'] = request.config.get('apiToken')
            provider = MonerisProvider(provider_config)
        else:
            return {
                "success": False,
                "message": f"Unsupported provider: {request.provider}"
            }

        # Test the connection
        try:
            is_healthy = await provider.health_check()
        except Exception as e:
            # If health check fails, return error details
            return {
                "success": False,
                "message": f"Connection test failed: {str(e)}"
            }

        if is_healthy:
            return {
                "success": True,
                "message": f"{request.provider.title()} connection successful"
            }
        else:
            return {
                "success": False,
                "message": "Failed to connect to payment provider - please check your credentials"
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error testing payment configuration: {str(e)}"
        )
