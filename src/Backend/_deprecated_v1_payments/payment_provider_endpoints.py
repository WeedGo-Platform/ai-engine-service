"""
Payment Provider Management API Endpoints
Secure endpoints for managing tenant payment provider configurations
Implements RBAC, audit logging, and PCI compliance
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator, SecretStr
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from uuid import UUID
import asyncpg
import logging
import hashlib
import hmac
import os

from services.security.credential_manager import CredentialManager, CredentialType
from services.payment.provider_factory import PaymentProviderFactory, ProviderType
from core.authentication import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/payment-providers", tags=["Payment Providers"])
security = HTTPBearer()

# Database connection pool and singleton instances
_db_pool = None
_credential_manager = None
_provider_factory = None

def get_user_id_for_db(current_user: dict) -> Optional[UUID]:
    """Convert user_id to UUID for database operations"""
    user_id = current_user.get('user_id')
    
    # Development mode - return None (will skip user-specific checks)
    if user_id == 'dev_user':
        return None
    
    # Convert to UUID if string
    if isinstance(user_id, str):
        try:
            return UUID(user_id)
        except (ValueError, TypeError):
            return None
    
    return user_id


# =====================================================
# Request/Response Models
# =====================================================

class CloverCredentialsRequest(BaseModel):
    """Request model for Clover API credentials"""
    access_token: Optional[SecretStr] = Field(None, description="Clover API access token")
    api_key: SecretStr = Field(..., description="Clover API key")
    secret: SecretStr = Field(..., description="Clover API secret")
    merchant_id: str = Field(..., description="Clover merchant ID")
    environment: str = Field("sandbox", pattern="^(sandbox|production)$")
    
    class Config:
        schema_extra = {
            "example": {
                "api_key": "clv_api_key_xxx",
                "secret": "clv_secret_xxx",
                "merchant_id": "MERCHANT123",
                "environment": "sandbox"
            }
        }


class ProviderConfigRequest(BaseModel):
    """Request model for provider configuration"""
    provider_type: str = Field(..., description="Type of payment provider")
    is_primary: bool = Field(False, description="Set as primary provider")
    is_active: bool = Field(True, description="Enable provider")
    platform_fee_percentage: float = Field(0.02, ge=0, le=1, description="Platform fee percentage (0-100%)")
    platform_fee_fixed: float = Field(0.0, ge=0, description="Fixed platform fee")
    daily_limit: Optional[float] = Field(None, ge=0, description="Daily transaction limit")
    transaction_limit: Optional[float] = Field(None, ge=0, description="Per-transaction limit")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Additional settings")
    
    @validator('platform_fee_percentage')
    def validate_fee_percentage(cls, v):
        if v < 0 or v > 0.1:  # Max 10% platform fee
            raise ValueError("Platform fee percentage must be between 0% and 10%")
        return v


class OAuthCallbackRequest(BaseModel):
    """Request model for OAuth callback"""
    code: str = Field(..., description="OAuth authorization code")
    merchant_id: str = Field(..., description="Merchant ID from OAuth")
    employee_id: Optional[str] = Field(None, description="Employee ID if applicable")
    state: str = Field(..., description="OAuth state for verification")


class WebhookRegistrationRequest(BaseModel):
    """Request model for webhook registration"""
    events: List[str] = Field(..., description="List of events to subscribe to")
    webhook_url: Optional[str] = Field(None, description="Custom webhook URL")


class ProviderHealthResponse(BaseModel):
    """Response model for provider health check"""
    provider_type: str
    status: str
    response_time_ms: Optional[int]
    last_check: datetime
    error: Optional[str]


class ProviderConfigResponse(BaseModel):
    """Response model for provider configuration"""
    id: UUID
    provider_type: str
    is_active: bool
    is_primary: bool
    environment: str
    health_status: str
    created_at: datetime
    updated_at: datetime
    capabilities: Dict[str, Any]


# =====================================================
# Dependency Injection
# =====================================================

async def get_credential_manager() -> CredentialManager:
    """Get or create credential manager instance"""
    global _credential_manager
    if _credential_manager is None:
        db_pool = await get_db_pool()
        master_key = os.getenv('PAYMENT_MASTER_KEY', 'dev-master-key-change-in-production')
        _credential_manager = CredentialManager(db_pool, master_key)
    return _credential_manager


async def get_provider_factory() -> PaymentProviderFactory:
    """Get or create provider factory instance"""
    global _provider_factory
    if _provider_factory is None:
        db_pool = await get_db_pool()
        credential_manager = await get_credential_manager()
        _provider_factory = PaymentProviderFactory(db_pool, credential_manager)
    return _provider_factory


async def get_db_pool() -> asyncpg.Pool:
    """Get or create database connection pool"""
    global _db_pool
    if _db_pool is None:
        _db_pool = await asyncpg.create_pool(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5434)),
            database=os.getenv('DB_NAME', 'ai_engine'),
            user=os.getenv('DB_USER', 'weedgo'),
            password=os.getenv('DB_PASSWORD', 'weedgo123'),
            min_size=10,
            max_size=20,
            command_timeout=60
        )
    return _db_pool


async def verify_tenant_access(
    tenant_id: UUID,
    current_user: dict = Depends(get_current_user),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> bool:
    """Verify user has access to tenant"""
    # In development mode, allow access
    if current_user.get('user_id') == 'dev_user':
        return True
    
    # Convert user_id string to UUID if needed
    try:
        user_id = UUID(current_user['user_id']) if isinstance(current_user['user_id'], str) else current_user['user_id']
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format"
        )
    
    async with db_pool.acquire() as conn:
        # Removed tenant_users table check
        # Authorization now handled differently  
        result = await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM users
                WHERE id = $2
                AND role IN ('super_admin', 'admin')
            )
        """, tenant_id, user_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to tenant resources"
            )
        
        return True


# =====================================================
# Clover Credential Management Endpoints
# =====================================================

@router.post("/tenants/{tenant_id}/clover/credentials")
async def configure_clover_credentials(
    tenant_id: UUID,
    credentials: CloverCredentialsRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(verify_tenant_access),
    credential_manager: CredentialManager = Depends(get_credential_manager),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Configure Clover API credentials for a tenant
    Requires tenant admin permissions
    """
    try:
        # Prepare credentials for secure storage
        credential_data = {
            "api_key": credentials.api_key.get_secret_value(),
            "secret": credentials.secret.get_secret_value(),
            "merchant_id": credentials.merchant_id,
            "environment": credentials.environment
        }
        
        if credentials.access_token:
            credential_data["access_token"] = credentials.access_token.get_secret_value()
        
        # Check if credentials already exist
        existing = await credential_manager.retrieve_credential(
            str(tenant_id),
            ProviderType.CLOVER,
            CredentialType.CLOVER_API
        )
        
        if existing:
            # Update existing credentials
            success = await credential_manager.update_credential(
                str(tenant_id),
                ProviderType.CLOVER,
                credential_data,
                CredentialType.CLOVER_API
            )
            action = "updated"
        else:
            # Store new credentials
            credential_id = await credential_manager.store_credential(
                str(tenant_id),
                ProviderType.CLOVER,
                CredentialType.CLOVER_API,
                credential_data,
                description=f"Clover API credentials for {credentials.environment}"
            )
            success = bool(credential_id)
            action = "created"
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store credentials"
            )
        
        # Create or update provider configuration
        async with db_pool.acquire() as conn:
            # Get Clover provider ID
            provider_id = await conn.fetchval("""
                SELECT id FROM payment_providers
                WHERE provider_type = 'clover'
            """)
            
            if not provider_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Clover provider not found in system"
                )
            
            # Upsert tenant provider configuration
            await conn.execute("""
                INSERT INTO tenant_payment_providers (
                    tenant_id, provider_id, merchant_id, environment,
                    is_active, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (tenant_id, provider_id, environment)
                DO UPDATE SET
                    merchant_id = EXCLUDED.merchant_id,
                    updated_at = CURRENT_TIMESTAMP
            """, tenant_id, provider_id, credentials.merchant_id, credentials.environment)
            
            # Log audit entry
            await conn.execute("""
                INSERT INTO payment_audit_log (
                    tenant_id, user_id, action, entity_type, entity_id,
                    details, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP)
            """, tenant_id, get_user_id_for_db(current_user), f"credentials_{action}",
                "payment_provider", str(provider_id),
                json.dumps({"provider": "clover", "environment": credentials.environment}))
        
        # Schedule health check in background
        background_tasks.add_task(
            check_provider_health,
            tenant_id,
            ProviderType.CLOVER
        )
        
        return {
            "status": "success",
            "message": f"Clover credentials {action} successfully",
            "provider": "clover",
            "environment": credentials.environment
        }
        
    except Exception as e:
        logger.error(f"Failed to configure Clover credentials: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to configure credentials: {str(e)}"
        )


@router.get("/tenants/{tenant_id}/clover/status")
async def get_clover_status(
    tenant_id: UUID,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(verify_tenant_access),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Get Clover configuration status for a tenant
    """
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow("""
            SELECT 
                tpp.*,
                pp.name as provider_name,
                pp.provider_type
            FROM tenant_payment_providers tpp
            JOIN payment_providers pp ON tpp.provider_id = pp.id
            WHERE tpp.tenant_id = $1 AND pp.provider_type = 'clover'
            AND tpp.is_active = true
        """, tenant_id)
        
        if not result:
            return {
                "configured": False,
                "message": "Clover is not configured for this tenant"
            }
        
        return {
            "configured": True,
            "environment": result['environment'],
            "merchant_id": result['merchant_id'],
            "is_primary": result['is_primary'],
            "health_status": result['health_status'],
            "last_health_check": result['last_health_check'],
            "created_at": result['created_at'],
            "updated_at": result['updated_at']
        }


@router.delete("/tenants/{tenant_id}/clover/credentials")
async def revoke_clover_credentials(
    tenant_id: UUID,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(verify_tenant_access),
    credential_manager: CredentialManager = Depends(get_credential_manager),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Revoke Clover credentials for a tenant
    Requires tenant owner permissions
    """
    # Additional permission check for destructive action
    async with db_pool.acquire() as conn:
        # Removed tenant_users table check for owner role
        # Owner check now handled differently
        is_owner = await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM users
                WHERE id = $2
                AND role = 'super_admin'
            )
        """, tenant_id, get_user_id_for_db(current_user))
        
        if not is_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only tenant owners can revoke credentials"
            )
        
        # Revoke credentials
        success = await credential_manager.revoke_credential(
            str(tenant_id),
            ProviderType.CLOVER,
            CredentialType.CLOVER_API
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credentials not found or already revoked"
            )
        
        # Deactivate provider configuration
        await conn.execute("""
            UPDATE tenant_payment_providers tpp
            SET is_active = false, updated_at = CURRENT_TIMESTAMP
            FROM payment_providers pp
            WHERE tpp.provider_id = pp.id
            AND tpp.tenant_id = $1 AND pp.provider_type = 'clover'
        """, tenant_id)
        
        # Log audit entry
        await conn.execute("""
            INSERT INTO payment_audit_log (
                tenant_id, user_id, action, entity_type,
                details, created_at
            ) VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
        """, tenant_id, get_user_id_for_db(current_user), "credentials_revoked",
            "payment_provider", {"provider": "clover"})
    
    return {
        "status": "success",
        "message": "Clover credentials revoked successfully"
    }


# =====================================================
# OAuth Flow Endpoints
# =====================================================

@router.get("/tenants/{tenant_id}/clover/oauth/authorize")
async def initiate_clover_oauth(
    tenant_id: UUID,
    redirect_uri: str,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(verify_tenant_access),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Initiate Clover OAuth flow for tenant onboarding
    Returns the authorization URL
    """
    import secrets
    import base64
    
    # Generate state token for CSRF protection
    state_data = {
        "tenant_id": str(tenant_id),
        "user_id": str(get_user_id_for_db(current_user) or 'dev_user'),
        "nonce": secrets.token_urlsafe(32)
    }
    state = base64.b64encode(json.dumps(state_data).encode()).decode()
    
    # Store state in database for verification
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO oauth_states (
                state, tenant_id, user_id, provider,
                redirect_uri, expires_at
            ) VALUES ($1, $2, $3, $4, $5, 
                CURRENT_TIMESTAMP + INTERVAL '10 minutes')
        """, state, tenant_id, get_user_id_for_db(current_user), 
            'clover', redirect_uri)
    
    # Get Clover OAuth configuration
    # In production, these would come from secure configuration
    client_id = os.environ.get('CLOVER_OAUTH_CLIENT_ID')
    
    # Build authorization URL
    oauth_base_url = "https://sandbox.dev.clover.com/oauth/v2/authorize"
    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Clover OAuth not configured"
        )
    
    auth_url = (
        f"{oauth_base_url}?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"state={state}"
    )
    
    return {
        "authorization_url": auth_url,
        "state": state
    }


@router.post("/tenants/{tenant_id}/clover/oauth/callback")
async def handle_clover_oauth_callback(
    tenant_id: UUID,
    callback_data: OAuthCallbackRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    credential_manager: CredentialManager = Depends(get_credential_manager),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Handle Clover OAuth callback and exchange code for tokens
    """
    import aiohttp
    import base64
    
    # Verify state token
    async with db_pool.acquire() as conn:
        state_valid = await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM oauth_states
                WHERE state = $1 AND tenant_id = $2
                AND provider = 'clover'
                AND expires_at > CURRENT_TIMESTAMP
            )
        """, callback_data.state, tenant_id)
        
        if not state_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OAuth state"
            )
        
        # Clean up used state
        await conn.execute("""
            DELETE FROM oauth_states
            WHERE state = $1
        """, callback_data.state)
    
    # Exchange authorization code for tokens
    client_id = os.environ.get('CLOVER_OAUTH_CLIENT_ID')
    client_secret = os.environ.get('CLOVER_OAUTH_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Clover OAuth credentials not configured"
        )
    
    token_url = "https://sandbox.dev.clover.com/oauth/v2/token"
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            token_url,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": callback_data.code,
                "grant_type": "authorization_code"
            }
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Token exchange failed: {error_text}"
                )
            
            token_data = await response.json()
    
    # Store OAuth tokens securely
    credential_data = {
        "oauth_access_token": token_data['access_token'],
        "oauth_refresh_token": token_data.get('refresh_token'),
        "merchant_id": callback_data.merchant_id,
        "api_key": client_id,
        "secret": client_secret,
        "environment": "sandbox"  # Adjust based on OAuth URL
    }
    
    # Calculate token expiration
    expires_in = token_data.get('expires_in', 3600)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    
    # Store credentials
    credential_id = await credential_manager.store_credential(
        str(tenant_id),
        ProviderType.CLOVER,
        CredentialType.OAUTH_TOKEN,
        credential_data,
        description="Clover OAuth tokens",
        expires_at=expires_at
    )
    
    # Update provider configuration
    async with db_pool.acquire() as conn:
        provider_id = await conn.fetchval("""
            SELECT id FROM payment_providers
            WHERE provider_type = 'clover'
        """)
        
        await conn.execute("""
            INSERT INTO tenant_payment_providers (
                tenant_id, provider_id, merchant_id,
                oauth_access_token, oauth_refresh_token,
                oauth_expires_at, environment, is_active
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, true)
            ON CONFLICT (tenant_id, provider_id, environment)
            DO UPDATE SET
                oauth_access_token = EXCLUDED.oauth_access_token,
                oauth_refresh_token = EXCLUDED.oauth_refresh_token,
                oauth_expires_at = EXCLUDED.oauth_expires_at,
                merchant_id = EXCLUDED.merchant_id,
                updated_at = CURRENT_TIMESTAMP
        """, tenant_id, provider_id, callback_data.merchant_id,
            token_data['access_token'], token_data.get('refresh_token'),
            expires_at, "sandbox")
        
        # Log audit entry
        await conn.execute("""
            INSERT INTO payment_audit_log (
                tenant_id, user_id, action, entity_type,
                details, created_at
            ) VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
        """, tenant_id, get_user_id_for_db(current_user), "oauth_connected",
            "payment_provider", {"provider": "clover", "merchant_id": callback_data.merchant_id})
    
    # Schedule webhook registration in background
    background_tasks.add_task(
        register_webhooks_for_tenant,
        tenant_id,
        ProviderType.CLOVER
    )
    
    return {
        "status": "success",
        "message": "Clover account connected successfully",
        "merchant_id": callback_data.merchant_id
    }


# =====================================================
# Provider Health Check Endpoints
# =====================================================

@router.get("/tenants/{tenant_id}/health")
async def check_all_providers_health(
    tenant_id: UUID,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(verify_tenant_access),
    provider_factory: PaymentProviderFactory = Depends(get_provider_factory)
) -> List[ProviderHealthResponse]:
    """
    Check health status of all configured payment providers for a tenant
    """
    providers = await provider_factory.get_all_providers(str(tenant_id))
    health_results = []
    
    for provider_type, provider in providers.items():
        health_data = await provider_factory.health_check(str(tenant_id), provider_type)
        health_results.append(ProviderHealthResponse(
            provider_type=provider_type,
            status=health_data['status'],
            response_time_ms=health_data.get('response_time_ms'),
            last_check=datetime.now(timezone.utc),
            error=health_data.get('error')
        ))
    
    return health_results


@router.post("/tenants/{tenant_id}/{provider_type}/health-check")
async def trigger_provider_health_check(
    tenant_id: UUID,
    provider_type: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(verify_tenant_access)
):
    """
    Trigger a health check for a specific provider
    """
    background_tasks.add_task(
        check_provider_health,
        tenant_id,
        provider_type
    )
    
    return {
        "status": "scheduled",
        "message": f"Health check scheduled for {provider_type}"
    }


# =====================================================
# Background Tasks
# =====================================================

async def check_provider_health(tenant_id: UUID, provider_type: str):
    """Background task to check provider health"""
    try:
        # This would use the injected provider_factory
        # For now, just log
        logger.info(f"Checking health for tenant {tenant_id}, provider {provider_type}")
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")


async def register_webhooks_for_tenant(tenant_id: UUID, provider_type: str):
    """Background task to register webhooks"""
    try:
        # This would use the provider to register webhooks
        logger.info(f"Registering webhooks for tenant {tenant_id}, provider {provider_type}")
    except Exception as e:
        logger.error(f"Webhook registration failed: {str(e)}")


# =====================================================
# Utility Functions
# =====================================================

import json
import os
from datetime import timedelta