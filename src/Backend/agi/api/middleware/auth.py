"""
Authentication Middleware for AGI API
Handles JWT token validation and role-based access control
"""

import jwt
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import hashlib
import secrets

from agi.core.interfaces import IUser
from agi.security import get_access_control, get_audit_logger
from agi.security.audit_logger import AuditEventType, AuditSeverity

logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = secrets.token_urlsafe(32)  # In production, load from environment
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Bearer token security
security = HTTPBearer()


class AuthenticationError(HTTPException):
    """Custom authentication error"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(HTTPException):
    """Custom authorization error"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


def create_access_token(
    user_id: str,
    username: str,
    roles: List[str] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token

    Args:
        user_id: User ID
        username: Username
        roles: User roles
        expires_delta: Token expiration time

    Returns:
        JWT token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": user_id,
        "username": username,
        "roles": roles or ["user"],
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """
    Create JWT refresh token

    Args:
        user_id: User ID

    Returns:
        JWT refresh token string
    """
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """
    Verify JWT token

    Args:
        token: JWT token string
        token_type: Expected token type

    Returns:
        Token payload

    Raises:
        AuthenticationError: If token is invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Check token type
        if payload.get("type") != token_type:
            raise AuthenticationError(f"Invalid token type. Expected {token_type}")

        return payload

    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> IUser:
    """
    Get current authenticated user from JWT token

    Args:
        credentials: Bearer token credentials

    Returns:
        Current user object

    Raises:
        AuthenticationError: If authentication fails
    """
    token = credentials.credentials

    # Verify token
    payload = verify_token(token)

    # Create user object from token payload
    user = IUser(
        id=payload.get("sub"),
        username=payload.get("username"),
        roles=payload.get("roles", ["user"]),
        permissions=payload.get("permissions", []),
        is_active=True
    )

    # Log authentication
    audit_logger = await get_audit_logger()
    await audit_logger.log_event(
        event_type=AuditEventType.AUTH_TOKEN_CREATED,
        user_id=user.id,
        severity=AuditSeverity.INFO,
        details={"username": user.username}
    )

    return user


async def require_role(required_role: str):
    """
    Dependency to require a specific role

    Args:
        required_role: Required role name

    Returns:
        Dependency function
    """
    async def role_checker(current_user: IUser = Depends(get_current_user)) -> IUser:
        if not current_user.has_role(required_role):
            # Log unauthorized access attempt
            audit_logger = await get_audit_logger()
            await audit_logger.log_event(
                event_type=AuditEventType.ACCESS_DENIED,
                user_id=current_user.id,
                severity=AuditSeverity.WARNING,
                details={
                    "required_role": required_role,
                    "user_roles": current_user.roles
                }
            )

            raise AuthorizationError(f"Role '{required_role}' required")

        return current_user

    return role_checker


async def require_permission(required_permission: str):
    """
    Dependency to require a specific permission

    Args:
        required_permission: Required permission name

    Returns:
        Dependency function
    """
    async def permission_checker(current_user: IUser = Depends(get_current_user)) -> IUser:
        if not current_user.has_permission(required_permission):
            # Log unauthorized access attempt
            audit_logger = await get_audit_logger()
            await audit_logger.log_event(
                event_type=AuditEventType.ACCESS_DENIED,
                user_id=current_user.id,
                severity=AuditSeverity.WARNING,
                details={
                    "required_permission": required_permission,
                    "user_permissions": current_user.permissions
                }
            )

            raise AuthorizationError(f"Permission '{required_permission}' required")

        return current_user

    return permission_checker


# Pre-defined role dependencies
require_admin = require_role("admin")
require_moderator = require_role("moderator")
require_developer = require_role("developer")


def create_api_key(user_id: str, key_name: str) -> tuple[str, str]:
    """
    Create API key for user

    Args:
        user_id: User ID
        key_name: Name for the API key

    Returns:
        Tuple of (api_key, key_hash)
    """
    # Generate random API key
    api_key = f"agi_{secrets.token_urlsafe(32)}"

    # Hash the key for storage
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    return api_key, key_hash


async def verify_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    """
    Verify API key

    Args:
        api_key: API key to verify

    Returns:
        Key information if valid, None otherwise
    """
    import asyncpg
    from datetime import timezone
    from agi.config.agi_config import get_config

    # Hash the provided key
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    try:
        # Get database configuration
        config = get_config().database

        # Connect to database
        conn = await asyncpg.connect(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=config.database
        )

        try:
            # Look up key in database
            key_data = await conn.fetchrow("""
                SELECT
                    id,
                    user_id,
                    name,
                    tenant_id,
                    permissions,
                    rate_limit,
                    is_active,
                    expires_at,
                    last_used
                FROM agi.api_keys
                WHERE key_hash = $1
                AND is_active = true
            """, key_hash)

            if not key_data:
                logger.debug(f"API key not found: hash={key_hash[:8]}...")
                return None

            # Check if key has expired
            if key_data['expires_at']:
                now = datetime.now(timezone.utc)
                if key_data['expires_at'].replace(tzinfo=timezone.utc) < now:
                    logger.warning(f"API key expired: id={key_data['id']}")
                    return None

            # Update last used timestamp
            await conn.execute("""
                UPDATE agi.api_keys
                SET last_used = CURRENT_TIMESTAMP
                WHERE id = $1
            """, key_data['id'])

            logger.info(f"API key authenticated successfully: {key_data['name']} (user: {key_data['user_id']})")

            return {
                "user_id": key_data['user_id'],
                "key_name": key_data['name'],
                "tenant_id": key_data['tenant_id'],
                "permissions": key_data['permissions'] or ["read"],
                "rate_limit": key_data['rate_limit'] or 60
            }

        finally:
            await conn.close()

    except Exception as e:
        logger.error(f"Error verifying API key: {e}")
        # Return None on error to deny access
        return None


class RateLimitMiddleware:
    """Rate limiting middleware"""

    def __init__(self, requests_per_minute: int = 60):
        """
        Initialize rate limiter

        Args:
            requests_per_minute: Maximum requests per minute
        """
        self.requests_per_minute = requests_per_minute
        self.request_counts: Dict[str, List[datetime]] = {}

    async def check_rate_limit(self, user_id: str) -> bool:
        """
        Check if user has exceeded rate limit

        Args:
            user_id: User ID to check

        Returns:
            True if within limit, False otherwise
        """
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)

        # Get user's request history
        if user_id not in self.request_counts:
            self.request_counts[user_id] = []

        # Remove old requests
        self.request_counts[user_id] = [
            timestamp for timestamp in self.request_counts[user_id]
            if timestamp > minute_ago
        ]

        # Check if limit exceeded
        if len(self.request_counts[user_id]) >= self.requests_per_minute:
            return False

        # Add current request
        self.request_counts[user_id].append(now)
        return True


# Global rate limiter instance
rate_limiter = RateLimitMiddleware()


async def check_rate_limit(current_user: IUser = Depends(get_current_user)) -> IUser:
    """
    Check rate limit for current user

    Args:
        current_user: Current authenticated user

    Returns:
        User if within rate limit

    Raises:
        HTTPException: If rate limit exceeded
    """
    if not await rate_limiter.check_rate_limit(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )

    return current_user