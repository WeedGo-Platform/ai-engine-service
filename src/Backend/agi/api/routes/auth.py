"""
Authentication Routes for AGI API
Handles login, logout, token refresh, and API key management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
import hashlib
import secrets

from agi.api.middleware.auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user,
    create_api_key,
    verify_api_key
)
from agi.core.interfaces import IUser
from agi.core.database import get_db_manager
from agi.security import get_audit_logger
from agi.security.audit_logger import AuditEventType, AuditSeverity

router = APIRouter(prefix="/api/v1/auth")


class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


class TokenRefreshRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str


class ApiKeyRequest(BaseModel):
    """API key creation request"""
    name: str
    permissions: Optional[list] = None


class ApiKeyResponse(BaseModel):
    """API key response"""
    api_key: str
    key_id: str
    name: str


# Mock user database (replace with real database in production)
MOCK_USERS = {
    "admin": {
        "id": "user_001",
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "roles": ["admin", "user"],
        "permissions": ["read", "write", "delete", "manage_users"]
    },
    "user": {
        "id": "user_002",
        "password_hash": hashlib.sha256("user123".encode()).hexdigest(),
        "roles": ["user"],
        "permissions": ["read", "write"]
    },
    "developer": {
        "id": "user_003",
        "password_hash": hashlib.sha256("dev123".encode()).hexdigest(),
        "roles": ["developer", "user"],
        "permissions": ["read", "write", "deploy"]
    }
}


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Login endpoint

    Args:
        request: Login credentials

    Returns:
        Access and refresh tokens
    """
    # Verify credentials (mock implementation)
    user_data = MOCK_USERS.get(request.username)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # Check password
    password_hash = hashlib.sha256(request.password.encode()).hexdigest()
    if password_hash != user_data["password_hash"]:
        # Log failed login attempt
        audit_logger = await get_audit_logger()
        await audit_logger.log_event(
            event_type=AuditEventType.AUTH_FAILED,
            user_id=request.username,
            severity=AuditSeverity.WARNING,
            details={"reason": "invalid_password"}
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # Create tokens
    access_token = create_access_token(
        user_id=user_data["id"],
        username=request.username,
        roles=user_data["roles"]
    )
    refresh_token = create_refresh_token(user_id=user_data["id"])

    # Log successful login
    audit_logger = await get_audit_logger()
    await audit_logger.log_event(
        event_type=AuditEventType.AUTH_LOGIN,
        user_id=user_data["id"],
        severity=AuditSeverity.INFO,
        details={"username": request.username}
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(request: TokenRefreshRequest):
    """
    Refresh access token

    Args:
        request: Refresh token

    Returns:
        New access and refresh tokens
    """
    # Verify refresh token
    try:
        payload = verify_token(request.refresh_token, token_type="refresh")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

    # Get user data (mock)
    user_id = payload["sub"]
    username = None
    roles = ["user"]

    for uname, udata in MOCK_USERS.items():
        if udata["id"] == user_id:
            username = uname
            roles = udata["roles"]
            break

    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Create new tokens
    access_token = create_access_token(
        user_id=user_id,
        username=username,
        roles=roles
    )
    refresh_token = create_refresh_token(user_id=user_id)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/logout")
async def logout(current_user: IUser = Depends(get_current_user)):
    """
    Logout endpoint

    Args:
        current_user: Current authenticated user

    Returns:
        Logout confirmation
    """
    # Log logout
    audit_logger = await get_audit_logger()
    await audit_logger.log_event(
        event_type=AuditEventType.AUTH_LOGOUT,
        user_id=current_user.id,
        severity=AuditSeverity.INFO,
        details={"username": current_user.username}
    )

    # In production, you would invalidate the token here
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user_info(current_user: IUser = Depends(get_current_user)):
    """
    Get current user information

    Args:
        current_user: Current authenticated user

    Returns:
        User information
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "roles": current_user.roles,
        "permissions": current_user.permissions,
        "is_active": current_user.is_active
    }


@router.post("/api-keys", response_model=ApiKeyResponse)
async def create_user_api_key(
    request: ApiKeyRequest,
    current_user: IUser = Depends(get_current_user)
):
    """
    Create API key for current user

    Args:
        request: API key details
        current_user: Current authenticated user

    Returns:
        Created API key
    """
    # Generate API key
    api_key, key_hash = create_api_key(current_user.id, request.name)

    # Store in database (mock for now)
    db_manager = await get_db_manager()
    key_id = f"key_{secrets.token_hex(8)}"

    # In production, store key_hash in database, not the actual key
    # await db_manager.execute(
    #     "INSERT INTO api_keys (id, user_id, key_hash, name) VALUES ($1, $2, $3, $4)",
    #     key_id, current_user.id, key_hash, request.name
    # )

    # Log API key creation
    audit_logger = await get_audit_logger()
    await audit_logger.log_event(
        event_type=AuditEventType.AUTH_TOKEN_CREATED,
        user_id=current_user.id,
        severity=AuditSeverity.INFO,
        details={"key_name": request.name, "key_id": key_id}
    )

    return ApiKeyResponse(
        api_key=api_key,
        key_id=key_id,
        name=request.name
    )


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: IUser = Depends(get_current_user)
):
    """
    Revoke API key

    Args:
        key_id: API key ID to revoke
        current_user: Current authenticated user

    Returns:
        Revocation confirmation
    """
    # In production, update database to mark key as revoked
    # db_manager = await get_db_manager()
    # await db_manager.execute(
    #     "UPDATE api_keys SET is_active = false WHERE id = $1 AND user_id = $2",
    #     key_id, current_user.id
    # )

    # Log API key revocation
    audit_logger = await get_audit_logger()
    await audit_logger.log_event(
        event_type=AuditEventType.AUTH_TOKEN_REVOKED,
        user_id=current_user.id,
        severity=AuditSeverity.INFO,
        details={"key_id": key_id}
    )

    return {"message": f"API key {key_id} revoked successfully"}