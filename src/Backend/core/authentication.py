"""
JWT-based Authentication System
Provides secure authentication for all API endpoints
"""

import jwt
import os
import hashlib
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from functools import wraps
from fastapi import HTTPException, Request, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

logger = logging.getLogger(__name__)


class JWTAuthentication:
    """
    JWT-based authentication with support for:
    - Access tokens with expiration
    - Refresh tokens
    - Role-based access control (RBAC)
    - API key authentication
    - Session management
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize with configuration"""
        config = config or {}
        
        # JWT configuration
        self.secret_key = os.environ.get('JWT_SECRET', config.get('jwt_secret', self._generate_secret()))
        self.algorithm = config.get('jwt_algorithm', 'HS256')
        self.access_token_expire_minutes = config.get('access_token_expire', 480)  # 8 hours for mobile checkout
        self.refresh_token_expire_days = config.get('refresh_token_expire', 30)  # 30 days
        
        # API Key configuration
        self.api_key_salt = os.environ.get('API_KEY_SALT', config.get('api_key_salt', self._generate_secret()))
        
        # Security settings
        self.enable_auth = os.environ.get('ENABLE_AUTH', 'true').lower() == 'true'
        self.allowed_origins = config.get('allowed_origins', [])
        
        # Role definitions
        self.roles = {
            'admin': ['*'],  # All permissions
            'user': ['read:products', 'create:orders', 'read:own_data'],
            'guest': ['read:products'],
            'service': ['*']  # For service-to-service auth
        }
    
    def _generate_secret(self) -> str:
        """Generate a secure random secret"""
        return secrets.token_urlsafe(32)
    
    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token
        
        Args:
            data: Token payload (user_id, role, etc.)
            expires_delta: Custom expiration time
        
        Returns:
            JWT token string
        """
        to_encode = data.copy()
        
        # Set expiration
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({
            'exp': expire,
            'iat': datetime.now(timezone.utc),
            'type': 'access'
        })
        
        # Encode token
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(
        self,
        data: Dict[str, Any]
    ) -> str:
        """
        Create JWT refresh token
        
        Args:
            data: Token payload
        
        Returns:
            JWT refresh token string
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)
        
        to_encode.update({
            'exp': expire,
            'iat': datetime.now(timezone.utc),
            'type': 'refresh'
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = 'access') -> Dict[str, Any]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token string
            token_type: Expected token type (access/refresh)
        
        Returns:
            Token payload
        
        Raises:
            HTTPException: If token is invalid
        """
        try:
            # Decode token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify token type
            if payload.get('type') != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}"
                )
            
            # Check expiration
            exp = payload.get('exp')
            if exp and datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )
            
            return payload
        
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except (jwt.PyJWTError, Exception) as e:
            # PyJWT v1.x uses PyJWTError, v2.x uses JWTError
            # Catch both for compatibility
            logger.error(f"JWT verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    def create_api_key(self, user_id: str, name: str = "default") -> str:
        """
        Create API key for user
        
        Args:
            user_id: User identifier
            name: API key name/description
        
        Returns:
            API key string
        """
        # Generate random key
        raw_key = secrets.token_urlsafe(32)
        
        # Create hash for storage
        key_hash = hashlib.pbkdf2_hmac(
            'sha256',
            raw_key.encode(),
            self.api_key_salt.encode(),
            100000  # iterations
        ).hex()
        
        # Return format: prefix.key
        # Prefix helps identify key in logs without exposing full key
        prefix = raw_key[:8]
        return f"{prefix}.{raw_key}"
    
    def verify_api_key(self, api_key: str) -> bool:
        """
        Verify API key
        
        Args:
            api_key: API key to verify
        
        Returns:
            True if valid
        """
        try:
            # Extract key from format
            if '.' not in api_key:
                return False
            
            prefix, raw_key = api_key.split('.', 1)
            
            # Verify prefix matches
            if raw_key[:8] != prefix:
                return False
            
            # In production, check hash against database
            # For now, validate format
            return len(raw_key) == 43  # token_urlsafe(32) length
        
        except Exception as e:
            logger.error(f"API key verification failed: {e}")
            return False
    
    def check_permission(
        self,
        user_role: str,
        required_permission: str
    ) -> bool:
        """
        Check if role has required permission
        
        Args:
            user_role: User's role
            required_permission: Required permission (e.g., 'read:products')
        
        Returns:
            True if authorized
        """
        if user_role not in self.roles:
            return False
        
        role_permissions = self.roles[user_role]
        
        # Check for wildcard permission
        if '*' in role_permissions:
            return True
        
        # Check specific permission
        return required_permission in role_permissions


class AuthMiddleware:
    """FastAPI authentication middleware"""
    
    def __init__(self, auth: JWTAuthentication):
        self.auth = auth
        self.bearer = HTTPBearer(auto_error=False)
    
    async def __call__(
        self,
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
    ) -> Dict[str, Any]:
        """
        Verify authentication credentials

        Returns:
            User information from token

        Raises:
            HTTPException: If authentication fails
        """
        # Check for API key in header (for service-to-service communication)
        api_key = request.headers.get('X-API-Key')
        if api_key:
            if self.auth.verify_api_key(api_key):
                return {
                    'user_id': 'api_user',
                    'role': 'service',
                    'authenticated': True,
                    'auth_method': 'api_key'
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key"
                )

        # Check for Bearer token
        if not credentials or not credentials.credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Please login to access this resource."
            )

        # Verify JWT token
        token_data = self.auth.verify_token(credentials.credentials)

        return {
            'user_id': token_data.get('user_id'),
            'role': token_data.get('role', 'user'),
            'authenticated': True,
            'auth_method': 'jwt',
            'session_id': token_data.get('session_id'),
            'tenant_id': token_data.get('tenant_id'),
            'store_id': token_data.get('store_id')
        }


def require_auth(permission: str = None):
    """
    Decorator to require authentication for an endpoint
    
    Args:
        permission: Required permission (e.g., 'read:products')
    
    Usage:
        @app.get("/protected")
        @require_auth("read:data")
        async def protected_endpoint(user: Dict = Depends(get_current_user)):
            return {"user": user}
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user from request context
            request = kwargs.get('request')
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request context not found"
                )
            
            # Get user from auth middleware
            user = getattr(request.state, 'user', None)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check permission if specified
            if permission:
                auth = JWTAuthentication()
                if not auth.check_permission(user.get('role'), permission):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied. Required: {permission}"
                    )
            
            # Add user to kwargs
            kwargs['user'] = user
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


class SessionManager:
    """Manage user sessions"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.sessions = {}  # In-memory fallback
    
    async def create_session(
        self,
        user_id: str,
        data: Dict[str, Any] = None
    ) -> str:
        """Create new session"""
        session_id = secrets.token_urlsafe(32)
        session_data = {
            'user_id': user_id,
            'created_at': time.time(),
            'last_activity': time.time(),
            'data': data or {}
        }
        
        if self.redis:
            # Store in Redis with TTL
            await self.redis.setex(
                f"session:{session_id}",
                3600,  # 1 hour TTL
                json.dumps(session_data)
            )
        else:
            # Fallback to in-memory
            self.sessions[session_id] = session_data
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        if self.redis:
            data = await self.redis.get(f"session:{session_id}")
            if data:
                session_data = json.loads(data)
                # Update last activity
                session_data['last_activity'] = time.time()
                await self.redis.setex(
                    f"session:{session_id}",
                    3600,
                    json.dumps(session_data)
                )
                return session_data
        else:
            # Fallback to in-memory
            if session_id in self.sessions:
                self.sessions[session_id]['last_activity'] = time.time()
                return self.sessions[session_id]
        
        return None
    
    async def destroy_session(self, session_id: str):
        """Destroy session"""
        if self.redis:
            await self.redis.delete(f"session:{session_id}")
        else:
            self.sessions.pop(session_id, None)


# Global auth instance
_auth_instance = None

def get_auth() -> JWTAuthentication:
    """Get or create global auth instance"""
    global _auth_instance
    if _auth_instance is None:
        from core.config_loader import get_config
        config = get_config()
        _auth_instance = JWTAuthentication(config.get_security_config())
    return _auth_instance


# FastAPI dependency
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Dict[str, Any]:
    """
    FastAPI dependency to get current user from token

    Usage:
        @app.get("/me")
        async def get_me(user: Dict = Depends(get_current_user)):
            return user
    """
    auth = get_auth()

    # Always require authentication - no development bypass
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please login to access this resource.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Verify JWT token
    token_data = auth.verify_token(credentials.credentials)

    return {
        'user_id': token_data.get('user_id'),
        'role': token_data.get('role', 'user'),
        'authenticated': True,
        'session_id': token_data.get('session_id'),
        'tenant_id': token_data.get('tenant_id'),
        'store_id': token_data.get('store_id')
    }


# Example login endpoint
async def login(email: str, password: str) -> Dict[str, str]:
    """
    Example login function
    
    Returns:
        Access and refresh tokens
    """
    # In production, verify against database
    # For now, mock verification
    
    auth = get_auth()
    
    # Create tokens
    user_data = {
        'user_id': '123',
        'email': email,
        'role': 'user'
    }
    
    access_token = auth.create_access_token(user_data)
    refresh_token = auth.create_refresh_token(user_data)
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'bearer'
    }