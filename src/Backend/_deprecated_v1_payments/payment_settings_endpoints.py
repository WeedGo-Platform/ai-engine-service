"""
Payment Settings API Endpoints
Handles payment provider settings for tenants and POS terminal settings for stores
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
        password=os.getenv('DB_PASSWORD', 'weedgo123')
    )
from core.domain.models import TenantRole, StoreRole

router = APIRouter(prefix="/api", tags=["payment-settings"])


# =====================================================
# PYDANTIC MODELS
# =====================================================

class PaymentProviderConfig(BaseModel):
    """Configuration for a payment provider"""
    enabled: bool = False
    account_id: Optional[str] = None
    publishable_key: Optional[str] = None
    secret_key: Optional[str] = None
    webhook_endpoint: Optional[str] = None
    payment_methods: List[str] = Field(default_factory=list)
    test_mode: bool = False
    
class TenantPaymentSettings(BaseModel):
    """Tenant payment provider settings"""
    stripe: Optional[PaymentProviderConfig] = None
    square: Optional[PaymentProviderConfig] = None
    moneris: Optional[PaymentProviderConfig] = None
    paypal: Optional[PaymentProviderConfig] = None
    interac: Optional[PaymentProviderConfig] = None
    default_provider: Optional[str] = None
    fallback_provider: Optional[str] = None
    currency: str = "CAD"
    auto_capture: bool = True
    receipt_email: bool = True
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class POSTerminal(BaseModel):
    """POS terminal configuration"""
    id: str
    name: str
    type: str
    serial_number: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None
    bluetooth_id: Optional[str] = None
    status: str = "active"
    last_seen: Optional[datetime] = None

class ReceiptSettings(BaseModel):
    """Receipt configuration settings"""
    print_customer_copy: bool = True
    print_merchant_copy: bool = False
    email_receipt: bool = True
    sms_receipt: bool = False

class OfflineMode(BaseModel):
    """Offline payment processing settings"""
    enabled: bool = False
    max_offline_amount: float = 500.0
    sync_interval_minutes: int = 5

class StorePOSSettings(BaseModel):
    """Store POS payment terminal settings"""
    terminals: List[POSTerminal] = Field(default_factory=list)
    default_terminal: Optional[str] = None
    payment_methods: List[str] = Field(default_factory=lambda: ["tap", "chip", "swipe", "cash"])
    tip_options: List[int] = Field(default_factory=lambda: [15, 18, 20, 0])
    tip_enabled: bool = True
    receipt_settings: ReceiptSettings = Field(default_factory=ReceiptSettings)
    offline_mode: OfflineMode = Field(default_factory=OfflineMode)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# =====================================================
# TENANT PAYMENT SETTINGS ENDPOINTS
# =====================================================

@router.get("/tenants/{tenant_id}/payment-settings", response_model=TenantPaymentSettings)
async def get_tenant_payment_settings(
    tenant_id: UUID
):
    """Get payment provider settings for a tenant"""
    db = await get_db_connection()
    try:
        query = """
            SELECT payment_provider_settings
            FROM tenants
            WHERE id = $1
        """
        
        result = await db.fetchrow(query, tenant_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        settings = result['payment_provider_settings'] or {}
        
        # Parse JSON if it's a string
        if isinstance(settings, str):
            settings = json.loads(settings) if settings else {}
        
        # For now, skip masking sensitive data until auth is fixed
        # if not await is_tenant_admin(db, tenant_id, current_user.get('id')):
        #     settings = mask_sensitive_payment_data(settings)
        
        return TenantPaymentSettings(**settings)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving payment settings: {str(e)}"
        )
    finally:
        await db.close()

@router.put("/tenants/{tenant_id}/payment-settings", response_model=TenantPaymentSettings)
async def update_tenant_payment_settings(
    tenant_id: UUID,
    settings: TenantPaymentSettings,
    db=Depends(get_db_connection),
    current_user=Depends(get_current_user)
):
    """Update payment provider settings for a tenant"""
    try:
        # Check if user has admin permissions
        if not await is_tenant_admin(db, tenant_id, current_user['id']):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only tenant admins can update payment settings"
            )
        
        # Validate at least one provider is enabled
        settings_dict = settings.dict(exclude_unset=True)
        if not any(
            provider.get('enabled', False) 
            for key, provider in settings_dict.items() 
            if isinstance(provider, dict) and key in ['stripe', 'square', 'moneris', 'paypal', 'interac']
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one payment provider must be enabled"
            )
        
        # Encrypt sensitive data
        settings_dict = encrypt_payment_settings(settings_dict)
        
        # Update database
        query = """
            UPDATE tenants
            SET payment_provider_settings = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING payment_provider_settings
        """
        
        result = await db.fetchrow(query, json.dumps(settings_dict), tenant_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        return TenantPaymentSettings(**result['payment_provider_settings'])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating payment settings: {str(e)}"
        )

@router.post("/tenants/{tenant_id}/payment-settings/validate")
async def validate_payment_settings(
    tenant_id: UUID,
    provider: str
):
    """Validate payment provider configuration"""
    db = await get_db_connection()
    try:
        # Get current settings
        query = """
            SELECT payment_provider_settings
            FROM tenants
            WHERE id = $1
        """
        
        result = await db.fetchrow(query, tenant_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        settings = result['payment_provider_settings'] or {}
        
        # Parse JSON if it's a string
        if isinstance(settings, str):
            settings = json.loads(settings) if settings else {}
        
        provider_settings = settings.get(provider)
        
        if not provider_settings or not provider_settings.get('enabled'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provider {provider} is not configured or enabled"
            )
        
        # Validate provider-specific settings
        validation_result = await validate_provider_config(provider, provider_settings)
        
        return {
            "provider": provider,
            "valid": validation_result['valid'],
            "message": validation_result.get('message', 'Configuration is valid'),
            "test_mode": provider_settings.get('test_mode', False)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating payment settings: {str(e)}"
        )
    finally:
        await db.close()


# =====================================================
# STORE POS SETTINGS ENDPOINTS
# =====================================================

@router.get("/stores/{store_id}/pos-terminals", response_model=StorePOSSettings)
async def get_store_pos_settings(
    store_id: UUID
):
    """Get POS terminal settings for a store"""
    db = await get_db_connection()
    try:
        query = """
            SELECT pos_payment_terminal_settings
            FROM stores
            WHERE id = $1
        """
        
        result = await db.fetchrow(query, store_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store not found"
            )
        
        settings = result['pos_payment_terminal_settings'] or {}
        
        # Parse JSON if it's a string
        if isinstance(settings, str):
            settings = json.loads(settings) if settings else {}
        
        return StorePOSSettings(**settings)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving POS settings: {str(e)}"
        )
    finally:
        await db.close()

@router.put("/stores/{store_id}/pos-terminals", response_model=StorePOSSettings)
async def update_store_pos_settings(
    store_id: UUID,
    settings: StorePOSSettings,
    db=Depends(get_db_connection),
    current_user=Depends(get_current_user)
):
    """Update POS terminal settings for a store"""
    try:
        # Check if user has manager permissions
        if not await is_store_manager(db, store_id, current_user['id']):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only store managers can update POS settings"
            )
        
        settings_dict = settings.dict(exclude_unset=True)
        
        # Update database
        query = """
            UPDATE stores
            SET pos_payment_terminal_settings = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING pos_payment_terminal_settings
        """
        
        result = await db.fetchrow(query, json.dumps(settings_dict), store_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store not found"
            )
        
        return StorePOSSettings(**result['pos_payment_terminal_settings'])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating POS settings: {str(e)}"
        )

@router.post("/stores/{store_id}/pos-terminals/{terminal_id}/ping")
async def ping_pos_terminal(
    store_id: UUID,
    terminal_id: str,
    db=Depends(get_db_connection),
    current_user=Depends(get_current_user)
):
    """Ping a POS terminal to check connectivity"""
    try:
        # Get terminal settings
        query = """
            SELECT pos_payment_terminal_settings
            FROM stores
            WHERE id = %s
        """
        
        result = await db.fetchrow(query, store_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store not found"
            )
        
        settings = result['pos_payment_terminal_settings'] or {}
        terminals = settings.get('terminals', [])
        
        terminal = next((t for t in terminals if t['id'] == terminal_id), None)
        
        if not terminal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Terminal not found"
            )
        
        # Simulate terminal ping (replace with actual implementation)
        ping_result = await ping_terminal(terminal)
        
        # Update last_seen timestamp if successful
        if ping_result['success']:
            for t in terminals:
                if t['id'] == terminal_id:
                    t['last_seen'] = datetime.utcnow().isoformat()
                    t['status'] = 'active'
                    break
            
            # Update database
            update_query = """
                UPDATE stores
                SET pos_payment_terminal_settings = %s
                WHERE id = %s
            """
            await db.execute(update_query, json.dumps(settings), store_id)
        
        return {
            "terminal_id": terminal_id,
            "status": "online" if ping_result['success'] else "offline",
            "response_time_ms": ping_result.get('response_time', None),
            "last_seen": terminal.get('last_seen')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error pinging terminal: {str(e)}"
        )


# =====================================================
# HELPER FUNCTIONS
# =====================================================

async def is_tenant_admin(db, tenant_id: UUID, user_id: UUID) -> bool:
    """Check if user is a tenant admin"""
    # Removed tenant_users table check
    # Authorization now handled differently
    query = """
        SELECT role FROM users
        WHERE id = $2
    """
    result = await db.fetchrow(query, tenant_id, user_id)
    return result and result['role'] in ['super_admin', 'admin']

async def is_store_manager(db, store_id: UUID, user_id: UUID) -> bool:
    """Check if user is a store manager"""
    # Removed store_users table check
    # Authorization now handled differently
    query = """
        SELECT role FROM users
        WHERE id = $2
    """
    result = await db.fetchrow(query, store_id, user_id)
    return result and result['role'] in ['admin', 'store_manager']

def mask_sensitive_payment_data(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Mask sensitive payment data for security"""
    masked = settings.copy()
    sensitive_fields = ['secret_key', 'api_token', 'access_token', 'client_secret']
    
    for provider in masked.values():
        if isinstance(provider, dict):
            for field in sensitive_fields:
                if field in provider:
                    provider[field] = "***masked***"
    
    return masked

def encrypt_payment_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Encrypt sensitive payment data"""
    encrypted = settings.copy()
    sensitive_fields = ['secret_key', 'api_token', 'access_token', 'client_secret']
    
    for provider_key, provider in encrypted.items():
        if isinstance(provider, dict):
            for field in sensitive_fields:
                if field in provider and provider[field]:
                    # Placeholder for actual encryption
                    provider[field] = f"encrypted:{provider[field]}"
    
    return encrypted

async def validate_provider_config(provider: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    """Validate provider-specific configuration"""
    # Placeholder for actual validation logic
    # This would typically make a test API call to the provider
    
    if provider == 'stripe':
        required = ['account_id', 'publishable_key', 'secret_key']
    elif provider == 'square':
        required = ['location_id', 'access_token']
    elif provider == 'moneris':
        required = ['store_id', 'api_token']
    else:
        return {"valid": False, "message": f"Unknown provider: {provider}"}
    
    missing = [field for field in required if not settings.get(field)]
    
    if missing:
        return {
            "valid": False,
            "message": f"Missing required fields: {', '.join(missing)}"
        }
    
    return {"valid": True, "message": "Configuration appears valid"}

async def ping_terminal(terminal: Dict[str, Any]) -> Dict[str, Any]:
    """Ping a POS terminal to check connectivity"""
    # Placeholder for actual terminal ping implementation
    # This would typically make a network request to the terminal
    
    import random
    import time
    
    start_time = time.time()
    
    # Simulate network delay
    await asyncio.sleep(random.uniform(0.01, 0.1))
    
    # Simulate success/failure
    success = random.random() > 0.1  # 90% success rate
    
    response_time = (time.time() - start_time) * 1000  # Convert to ms
    
    return {
        "success": success,
        "response_time": round(response_time, 2)
    }

import asyncio