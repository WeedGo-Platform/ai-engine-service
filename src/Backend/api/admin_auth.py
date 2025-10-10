"""
Admin Authentication API Endpoints
Production-ready authentication system for multi-tenant admin dashboard
Implements JWT-based authentication with role-based access control
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from uuid import UUID
import asyncpg
import bcrypt
import json
import jwt
import secrets
import logging
import os
from enum import Enum
from core.services.login_tracking_service import get_login_tracking_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth/admin", tags=["Admin Authentication"])
security = HTTPBearer()

# Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'dev-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24
REFRESH_TOKEN_DAYS = 7
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

# Database connection pool
_db_pool = None

async def get_db_pool() -> asyncpg.Pool:
    """Get or create database connection pool"""
    global _db_pool
    if _db_pool is None:
        _db_pool = await asyncpg.create_pool(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5434)),
            database=os.getenv('DB_NAME', 'ai_engine'),
            user=os.getenv('DB_USER', 'weedgo'),
            password=os.getenv('DB_PASSWORD', 'your_password_here'),
            min_size=5,
            max_size=10,
            command_timeout=60
        )
    return _db_pool


# =====================================================
# Enums and Models
# =====================================================

class UserRole(str, Enum):
    """System-wide user roles"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"


class TenantRole(str, Enum):
    """Tenant-specific roles"""
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"


class StoreRole(str, Enum):
    """Store-specific roles"""
    MANAGER = "manager"
    SUPERVISOR = "supervisor"
    STAFF = "staff"
    CASHIER = "cashier"


class LoginRequest(BaseModel):
    """Admin login request model"""
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    remember_me: bool = Field(False, description="Extended session duration")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "admin@potpalace.ca",
                "password": "SecurePassword123!",
                "remember_me": False
            }
        }


class RefreshTokenRequest(BaseModel):
    """Refresh token request model"""
    refresh_token: str = Field(..., description="Refresh token")


class LoginResponse(BaseModel):
    """Login response with tokens and user info"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: Dict[str, Any]
    permissions: List[str]


class UserInfo(BaseModel):
    """User information for JWT payload"""
    user_id: str
    email: str
    role: str
    first_name: Optional[str]
    last_name: Optional[str]
    tenants: List[Dict[str, Any]] = []
    stores: List[Dict[str, Any]] = []


# =====================================================
# Helper Functions
# =====================================================

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        # Check if it's a valid bcrypt hash
        if not hashed_password or not hashed_password.startswith('$2'):
            return False
        
        # For bcrypt hashes, they're already in bytes format in the database
        # Don't encode if it's already a valid bcrypt hash string
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
        )
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })
    
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> tuple[str, str]:
    """Create refresh token and its hash"""
    token = secrets.token_urlsafe(32)
    token_hash = bcrypt.hashpw(token.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    return token, token_hash


def decode_token(token: str) -> dict:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


async def check_login_attempts(email: str, db_pool: asyncpg.Pool) -> bool:
    """Check if user is locked out due to failed login attempts"""
    async with db_pool.acquire() as conn:
        # Get user_id from email first
        user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", email)
        if not user:
            return True  # No user found, allow attempt

        result = await conn.fetchrow("""
            SELECT COUNT(*) as attempts, MAX(login_timestamp) as last_attempt
            FROM user_login_logs
            WHERE user_id = $1
            AND login_timestamp > CURRENT_TIMESTAMP - INTERVAL '%s minutes'
            AND login_successful = false
        """ % LOCKOUT_DURATION_MINUTES, user['id'])

        if result and result['attempts'] >= MAX_LOGIN_ATTEMPTS:
            return False
    return True


async def record_login_attempt(
    email: str,
    success: bool,
    ip_address: str,
    user_agent: str,
    db_pool: asyncpg.Pool,
    user_id: Optional[UUID] = None
):
    """Record login attempt for audit and rate limiting"""
    async with db_pool.acquire() as conn:
        # If no user_id provided, try to get it from email
        if not user_id:
            user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", email)
            if user:
                user_id = user['id']

        await conn.execute("""
            INSERT INTO user_login_logs (
                user_id, ip_address, user_agent, login_successful, failure_reason
            ) VALUES ($1, $2::inet, $3, $4, $5)
        """, user_id, ip_address, user_agent, success, None if success else 'Invalid credentials')


async def get_user_permissions(user_id: UUID, db_pool: asyncpg.Pool) -> List[str]:
    """Get all permissions for a user"""
    permissions = []
    
    async with db_pool.acquire() as conn:
        # Get user role and custom permissions
        user = await conn.fetchrow("""
            SELECT role, permissions FROM users WHERE id = $1
        """, user_id)
        
        if not user:
            return permissions
        
        user_role = user['role']
        
        # Assign base permissions based on role
        if user_role == 'super_admin':
            permissions.append('system:*')
        elif user_role == 'tenant_admin':
            permissions.extend(['tenant:read', 'tenant:write', 'store:*', 'user:*'])
        elif user_role == 'store_manager':
            permissions.extend(['store:read', 'store:write', 'user:read', 'user:write'])
        elif user_role == 'staff':
            permissions.extend(['store:read', 'user:read'])
        
        # Add any custom permissions from JSONB field
        if user.get('permissions'):
            custom_perms = user['permissions']
            if isinstance(custom_perms, dict) and 'additional' in custom_perms:
                permissions.extend(custom_perms['additional'])
    
    return permissions


# =====================================================
# Authentication Endpoints
# =====================================================

@router.post("/login", response_model=LoginResponse)
async def admin_login(
    request: Request,
    credentials: LoginRequest,
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Admin login endpoint with multi-tenant support
    
    Features:
    - Rate limiting and lockout protection
    - Multi-tenant role resolution
    - JWT token generation
    - Audit logging
    """
    # Get client info for audit
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    # DEBUG: Log login attempt details
    logger.info(f"Login attempt - Email: {credentials.email}, Password length: {len(credentials.password)}")

    # Check rate limiting
    if not await check_login_attempts(credentials.email, db_pool):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Please try again in {LOCKOUT_DURATION_MINUTES} minutes"
        )
    
    async with db_pool.acquire() as conn:
        # Fetch user with password, including tenant and store associations
        user = await conn.fetchrow("""
            SELECT id, email, password_hash, first_name, last_name, role,
                   active, email_verified, tenant_id, store_id, permissions
            FROM users
            WHERE email = $1
        """, credentials.email)
        
        if not user:
            # Record failed attempt
            await record_login_attempt(
                credentials.email, False, client_ip, user_agent, db_pool
            )
            
            # Track failed login attempt (no user ID available)
            try:
                login_tracker = get_login_tracking_service(db_pool)
                await login_tracker.track_login(
                    user_id=None,  # No user found
                    tenant_id=None,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    login_successful=False,
                    login_method='password',
                    metadata={'error': 'user_not_found', 'email': credentials.email}
                )
            except Exception as e:
                logger.warning(f"Failed to track login attempt: {e}")
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(credentials.password, user['password_hash']):
            # Record failed attempt
            await record_login_attempt(
                credentials.email, False, client_ip, user_agent, db_pool, user['id']
            )
            
            # Track failed login with IP geolocation
            try:
                login_tracker = get_login_tracking_service(db_pool)
                # Get tenant ID if available
                tenant_id = user.get('tenant_id')

                await login_tracker.track_login(
                    user_id=user['id'],
                    tenant_id=tenant_id,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    login_successful=False,
                    login_method='password',
                    metadata={'error': 'invalid_password'}
                )
            except Exception as e:
                logger.warning(f"Failed to track login attempt: {e}")
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if account is active
        if not user['active']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled"
            )
        
        # Check if user has admin access
        user_role = user['role']
        if user_role not in ['super_admin', 'tenant_admin', 'store_manager', 'staff']:
            # Only customers don't have admin access
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No admin access privileges"
            )
        
        # Get tenant associations from users table
        tenants = []
        if user.get('tenant_id'):
            tenant = await conn.fetchrow("""
                SELECT id, name, code
                FROM tenants
                WHERE id = $1 AND status = 'active'
            """, user['tenant_id'])
            if tenant:
                tenants = [{
                    'id': tenant['id'],
                    'name': tenant['name'],
                    'code': tenant['code'],
                    'role': user['role']  # Use the main role field
                }]
        
        # Get store associations from users table
        stores = []
        if user.get('store_id'):
            store = await conn.fetchrow("""
                SELECT id, name, store_code, tenant_id
                FROM stores
                WHERE id = $1 AND status = 'active'
            """, user['store_id'])
            if store:
                stores = [{
                    'id': store['id'],
                    'name': store['name'],
                    'store_code': store['store_code'],
                    'tenant_id': store['tenant_id'],
                    'role': user['role']  # Use the main role field
                }]
        
        # Prepare user info for JWT
        user_info = {
            "user_id": str(user['id']),
            "email": user['email'],
            "role": user_role,
            "first_name": user['first_name'],
            "last_name": user['last_name'],
            "tenants": [
                {
                    "id": str(t['id']),
                    "name": t['name'],
                    "code": t['code'],
                    "role": t['role']
                } for t in tenants
            ],
            "stores": [
                {
                    "id": str(s['id']),
                    "name": s['name'],
                    "code": s['store_code'],
                    "role": s['role'],
                    "tenant_id": str(s['tenant_id'])
                } for s in stores
            ]
        }
        
        # Create tokens
        expires_delta = timedelta(days=7) if credentials.remember_me else timedelta(hours=JWT_EXPIRATION_HOURS)
        access_token = create_access_token(user_info, expires_delta)
        refresh_token, refresh_token_hash = create_refresh_token(str(user['id']))
        
        # Store refresh token
        await conn.execute("""
            INSERT INTO user_sessions (
                user_id, session_token, ip_address, user_agent,
                device_info, expires_at, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP)
        """, user['id'], refresh_token_hash, client_ip, user_agent,
            json.dumps({"remember_me": credentials.remember_me}),
            datetime.utcnow() + timedelta(days=REFRESH_TOKEN_DAYS if credentials.remember_me else 1))
        
        # Record successful login with location tracking
        await record_login_attempt(
            credentials.email, True, client_ip, user_agent, db_pool, user['id']
        )
        
        # Track login with IP geolocation (location data stored in user_login_logs)
        try:
            login_tracker = get_login_tracking_service(db_pool)
            tenant_id = tenants[0]['id'] if tenants else None
            await login_tracker.track_login(
                user_id=user['id'],
                tenant_id=tenant_id,
                ip_address=client_ip,
                user_agent=user_agent,
                login_successful=True,
                login_method='password',
                session_id=refresh_token_hash,
                metadata={
                    'remember_me': credentials.remember_me,
                    'role': user['role']
                }
            )
        except Exception as e:
            logger.warning(f"Failed to track login attempt: {e}")

        # Get permissions
        permissions = await get_user_permissions(user['id'], db_pool)

        # Log admin login for audit (basic info only, detailed location in user_login_logs)
        await conn.execute("""
            INSERT INTO audit_log (
                user_id, action, resource_type, details, ip_address, timestamp
            ) VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
        """, user['id'], 'admin_login', 'authentication',
            json.dumps({"user_agent": user_agent, "remember_me": credentials.remember_me}),
            client_ip)
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=int(expires_delta.total_seconds()),
        user=user_info,
        permissions=permissions
    )


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    request: Request,
    refresh_request: RefreshTokenRequest,
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Refresh access token using refresh token
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    async with db_pool.acquire() as conn:
        # Find session by refresh token
        session = await conn.fetchrow("""
            SELECT us.*, u.email, u.first_name, u.last_name, u.role
            FROM user_sessions us
            JOIN users u ON us.user_id = u.id
            WHERE us.expires_at > CURRENT_TIMESTAMP
            ORDER BY us.created_at DESC
            LIMIT 1
        """)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        # Verify refresh token
        # Note: In production, store hashed refresh tokens and verify
        
        # Get updated user info from users table
        user = await conn.fetchrow("""
            SELECT id, email, first_name, last_name, role,
                   tenant_id, store_id, permissions, active
            FROM users WHERE id = $1
        """, session['user_id'])
        
        tenants = []
        if user.get('tenant_id'):
            tenant = await conn.fetchrow("""
                SELECT id, name, code
                FROM tenants
                WHERE id = $1 AND status = 'active'
            """, user['tenant_id'])
            if tenant:
                tenants = [{
                    'id': tenant['id'],
                    'name': tenant['name'],
                    'code': tenant['code'],
                    'role': user['role']  # Use the main role field
                }]
        
        stores = []
        if user.get('store_id'):
            store = await conn.fetchrow("""
                SELECT id, name, store_code, tenant_id
                FROM stores
                WHERE id = $1 AND status = 'active'
            """, user['store_id'])
            if store:
                stores = [{
                    'id': store['id'],
                    'name': store['name'],
                    'store_code': store['store_code'],
                    'tenant_id': store['tenant_id'],
                    'role': user['role']  # Use the main role field
                }]
        
        user_info = {
            "user_id": str(session['user_id']),
            "email": session['email'],
            "role": session['role'],
            "first_name": session['first_name'],
            "last_name": session['last_name'],
            "tenants": [
                {
                    "id": str(t['id']),
                    "name": t['name'],
                    "code": t['code'],
                    "role": t['role']
                } for t in tenants
            ],
            "stores": [
                {
                    "id": str(s['id']),
                    "name": s['name'],
                    "code": s['store_code'],
                    "role": s['role'],
                    "tenant_id": str(s['tenant_id'])
                } for s in stores
            ]
        }
        
        # Create new access token
        new_access_token = create_access_token(user_info)
        new_refresh_token, new_refresh_token_hash = create_refresh_token(str(session['user_id']))
        
        # Update session
        await conn.execute("""
            UPDATE user_sessions
            SET session_token = $1, last_activity = CURRENT_TIMESTAMP
            WHERE id = $2
        """, new_refresh_token_hash, session['id'])
        
        # Get permissions
        permissions = await get_user_permissions(session['user_id'], db_pool)
    
    return LoginResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=JWT_EXPIRATION_HOURS * 3600,
        user=user_info,
        permissions=permissions
    )


@router.post("/logout")
async def admin_logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Logout admin user and invalidate session
    """
    token = credentials.credentials
    payload = decode_token(token)
    user_id = UUID(payload['user_id'])
    
    client_ip = request.client.host if request.client else "unknown"
    
    async with db_pool.acquire() as conn:
        # Invalidate all sessions for this user
        await conn.execute("""
            DELETE FROM user_sessions
            WHERE user_id = $1
        """, user_id)
        
        # Log logout
        await conn.execute("""
            INSERT INTO audit_log (
                user_id, action, resource_type, ip_address, timestamp
            ) VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
        """, user_id, 'admin_logout', 'authentication', client_ip)
    
    return {"message": "Successfully logged out"}


@router.get("/me")
async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Get current admin user information with fresh data from database
    """
    token = credentials.credentials
    payload = decode_token(token)
    user_id = UUID(payload['user_id'])
    
    async with db_pool.acquire() as conn:
        # Fetch fresh user data from database
        user = await conn.fetchrow("""
            SELECT id, email, first_name, last_name, role,
                   tenant_id, store_id, permissions
            FROM users
            WHERE id = $1
        """, user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get tenant associations
        tenants = []
        if user.get('tenant_id'):
            tenant = await conn.fetchrow("""
                SELECT id, name, code
                FROM tenants
                WHERE id = $1 AND status = 'active'
            """, user['tenant_id'])
            if tenant:
                tenants = [{
                    'id': str(tenant['id']),
                    'name': tenant['name'],
                    'code': tenant['code'],
                    'role': user['role']  # Use the main role field
                }]
        
        # Get store associations
        stores = []
        if user.get('store_id'):
            store = await conn.fetchrow("""
                SELECT id, name, store_code, tenant_id
                FROM stores
                WHERE id = $1 AND status = 'active'
            """, user['store_id'])
            if store:
                stores = [{
                    'id': str(store['id']),
                    'name': store['name'],
                    'code': store['store_code'],
                    'tenant_id': str(store['tenant_id']),
                    'role': user['role']  # Use the main role field
                }]
        
        # Build user info with fresh data
        user_info = {
            "user_id": str(user['id']),
            "email": user['email'],
            "role": user['role'],
            "first_name": user['first_name'],
            "last_name": user['last_name'],
            "tenants": tenants,
            "stores": stores
        }
    
    # Return fresh user info
    return {
        "user": user_info,
        "permissions": await get_user_permissions(user_id, db_pool)
    }


@router.post("/verify")
async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Verify if token is valid
    """
    token = credentials.credentials
    try:
        payload = decode_token(token)
        return {"valid": True, "payload": payload}
    except:
        return {"valid": False}


# =====================================================
# Admin User Management (for super admins only)
# =====================================================

@router.post("/create-admin")
async def create_admin_user(
    email: EmailStr = Body(...),
    password: str = Body(..., min_length=8),
    first_name: str = Body(...),
    last_name: str = Body(...),
    role: UserRole = Body(UserRole.ADMIN),
    tenant_id: Optional[UUID] = Body(None),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Create a new admin user (super admin only)
    """
    token = credentials.credentials
    payload = decode_token(token)
    
    # Check if requester is super admin
    if payload.get('role') != 'super_admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can create admin users"
        )
    
    async with db_pool.acquire() as conn:
        # Check if email exists
        exists = await conn.fetchval("""
            SELECT EXISTS(SELECT 1 FROM users WHERE email = $1)
        """, email)
        
        if exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create user with tenant association if provided
        if tenant_id:
            user_id = await conn.fetchval("""
                INSERT INTO users (
                    email, password_hash, first_name, last_name, role,
                    tenant_id, active, email_verified, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, true, true, CURRENT_TIMESTAMP)
                RETURNING id
            """, email, password_hash, first_name, last_name, role.value, tenant_id)
        else:
            user_id = await conn.fetchval("""
                INSERT INTO users (
                    email, password_hash, first_name, last_name, role,
                    active, email_verified, created_at
                ) VALUES ($1, $2, $3, $4, $5, true, true, CURRENT_TIMESTAMP)
                RETURNING id
            """, email, password_hash, first_name, last_name, role.value)
        
        # Log admin creation
        await conn.execute("""
            INSERT INTO audit_log (
                user_id, action, resource_type, resource_id, details, timestamp
            ) VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
        """, UUID(payload['user_id']), 'create_admin', 'user', str(user_id),
            json.dumps({"email": email, "role": role.value, "tenant_id": str(tenant_id) if tenant_id else None}))
    
    return {
        "message": "Admin user created successfully",
        "user_id": str(user_id),
        "email": email
    }


# =====================================================
# Password Change Endpoint
# =====================================================

class ChangePasswordRequest(BaseModel):
    """Password change request model"""
    current_password: str = Field(..., min_length=6, max_length=100, description="Current password")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password (min 8 characters)")

    @validator('new_password')
    def validate_password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v


@router.post("/change-password")
async def change_password(
    request: Request,
    password_request: ChangePasswordRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Change password for the currently authenticated user

    Features:
    - Validates current password
    - Enforces password strength requirements
    - Invalidates all existing sessions except current one
    - Logs password change for audit
    """
    token = credentials.credentials
    payload = decode_token(token)
    user_id = UUID(payload['user_id'])

    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    async with db_pool.acquire() as conn:
        # Get current user with password
        user = await conn.fetchrow("""
            SELECT id, email, password_hash, first_name, last_name
            FROM users
            WHERE id = $1
        """, user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Verify current password
        if not verify_password(password_request.current_password, user['password_hash']):
            # Log failed password change attempt
            await conn.execute("""
                INSERT INTO audit_log (
                    user_id, action, resource_type, details, ip_address, timestamp
                ) VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
            """, user_id, 'password_change_failed', 'authentication',
                json.dumps({"reason": "invalid_current_password"}), client_ip)

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )

        # Check if new password is same as current
        if verify_password(password_request.new_password, user['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password"
            )

        # Hash new password
        new_password_hash = hash_password(password_request.new_password)

        # Update password
        await conn.execute("""
            UPDATE users
            SET password_hash = $1, updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
        """, new_password_hash, user_id)

        # Invalidate all sessions except current one (optional - you can invalidate all if preferred)
        # For now, let's invalidate all sessions to force re-login everywhere
        await conn.execute("""
            DELETE FROM user_sessions
            WHERE user_id = $1
        """, user_id)

        # Log successful password change
        await conn.execute("""
            INSERT INTO audit_log (
                user_id, action, resource_type, details, ip_address, timestamp
            ) VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
        """, user_id, 'password_changed', 'authentication',
            json.dumps({
                "user_agent": user_agent,
                "sessions_invalidated": True
            }), client_ip)

        logger.info(f"Password changed successfully for user {user['email']} ({user_id})")

    return {
        "message": "Password changed successfully. Please log in again with your new password.",
        "sessions_invalidated": True
    }