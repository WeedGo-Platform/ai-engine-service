"""
Customer Authentication API Endpoints
Handles customer registration, login, and session management
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import bcrypt
import uuid
import json
import asyncpg

from core.authentication import JWTAuthentication

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth/customer", tags=["Customer Authentication"])
security = HTTPBearer()

# Initialize JWT authentication
jwt_auth = JWTAuthentication()


# Pydantic models for request/response
class UserRegistration(BaseModel):
    """User registration request model"""
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    date_of_birth: str = Field(..., description="Format: YYYY-MM-DD")
    phone: str = Field(..., min_length=10, max_length=15)
    
    @validator('date_of_birth')
    def validate_age(cls, v):
        """Ensure user is 21+ years old"""
        try:
            dob = datetime.strptime(v, '%Y-%m-%d')
            age = (datetime.now() - dob).days / 365.25
            if age < 21:
                raise ValueError('Must be 21 years or older')
            return v
        except ValueError as e:
            if 'Must be 21' in str(e):
                raise
            raise ValueError('Invalid date format. Use YYYY-MM-DD')


class UserLogin(BaseModel):
    """User login request model"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response model"""
    message: str
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


# Database connection helper
async def get_db_connection():
    """Get database connection"""
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5434,
            database='ai_engine',
            user='weedgo',
            password='weedgo123'
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed"
        )


# Helper functions
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user from token"""
    token = credentials.credentials
    
    try:
        payload = jwt_auth.verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return payload
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )


async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Get current user from token if provided, otherwise return None"""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = jwt_auth.verify_token(token)
        return payload if payload else None
    except Exception:
        return None


# API Endpoints
@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegistration):
    """
    Register a new user account
    
    Required fields:
    - email: Valid email address
    - password: Minimum 6 characters
    - first_name: User's first name
    - last_name: User's last name
    - date_of_birth: YYYY-MM-DD format (must be 21+)
    - phone: Phone number
    """
    conn = None
    try:
        conn = await get_db_connection()
        
        # Check if user already exists
        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1",
            user_data.email
        )
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        # Verify age
        dob = datetime.strptime(user_data.date_of_birth, '%Y-%m-%d')
        age = (datetime.now() - dob).days / 365.25
        age_verified = age >= 21
        
        # Hash password
        password_hash = hash_password(user_data.password)
        
        # Create user record
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        await conn.execute(
            """
            INSERT INTO users (
                id, email, password_hash, phone, 
                first_name, last_name, date_of_birth,
                age_verified, session_id, active,
                role, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """,
            user_id, user_data.email, password_hash, user_data.phone,
            user_data.first_name, user_data.last_name, dob.date(),  # Convert to date object
            age_verified, session_id, True,
            'customer',  # Explicitly set role to customer
            datetime.now(), datetime.now()
        )
        
        # Create JWT token
        access_token = jwt_auth.create_access_token({
            'user_id': user_id,
            'email': user_data.email,
            'session_id': session_id
        })
        
        logger.info(f"User registered: {user_data.email}")
        
        return LoginResponse(
            message="Registration successful",
            access_token=access_token,
            user={
                'id': user_id,
                'email': user_data.email,
                'first_name': user_data.first_name,
                'last_name': user_data.last_name,
                'phone': user_data.phone,
                'age_verified': age_verified
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )
    finally:
        if conn:
            await conn.close()


@router.post("/login", response_model=LoginResponse)
async def login(credentials: UserLogin):
    """
    Authenticate user and create session
    
    Required fields:
    - email: Registered email address
    - password: User password
    """
    conn = None
    try:
        conn = await get_db_connection()
        
        # Fetch user
        user = await conn.fetchrow(
            """
            SELECT id, email, password_hash, first_name, last_name, 
                   phone, age_verified, session_id, role, tenant_id, store_id
            FROM users 
            WHERE email = $1 AND active = true
            """,
            credentials.email
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(credentials.password, user['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Update last login
        await conn.execute(
            "UPDATE users SET last_login = $1 WHERE id = $2",
            datetime.now(), user['id']
        )
        
        # Create JWT token with role and context
        access_token = jwt_auth.create_access_token({
            'user_id': user['id'],
            'email': user['email'],
            'session_id': user['session_id'] or str(uuid.uuid4()),
            'role': user['role'],
            'tenant_id': user['tenant_id'],
            'store_id': user['store_id']
        })
        
        logger.info(f"User logged in: {credentials.email}")
        
        return LoginResponse(
            message="Login successful",
            access_token=access_token,
            user={
                'id': user['id'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'phone': user['phone'],
                'age_verified': user['age_verified']
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )
    finally:
        if conn:
            await conn.close()


@router.post("/logout")
async def logout(current_user: Dict = Depends(get_current_user)):
    """
    Logout user
    
    Requires authentication token in header
    """
    # In a simple implementation, logout is handled client-side by removing the token
    # For server-side tracking, you could add token to a blacklist
    
    logger.info(f"User logged out: {current_user.get('email')}")
    
    return {
        'message': 'Logout successful',
        'email': current_user.get('email')
    }


@router.get("/verify")
async def verify_token(current_user: Dict = Depends(get_current_user)):
    """
    Verify if token is valid
    
    Requires authentication token in header
    """
    conn = None
    try:
        conn = await get_db_connection()
        
        # Get user details
        user = await conn.fetchrow(
            """
            SELECT id, email, first_name, last_name, phone, age_verified
            FROM users
            WHERE id = $1 AND active = true
            """,
            current_user['user_id']
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            'valid': True,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'phone': user['phone'],
                'age_verified': user['age_verified']
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verification failed"
        )
    finally:
        if conn:
            await conn.close()


@router.get("/me")
async def get_current_user_info(current_user: Dict = Depends(get_current_user)):
    """
    Get current user information
    
    Requires authentication token in header
    """
    conn = None
    try:
        conn = await get_db_connection()
        
        # Get user details
        user = await conn.fetchrow(
            """
            SELECT id, email, first_name, last_name, phone, 
                   date_of_birth, age_verified, created_at, last_login
            FROM users
            WHERE id = $1
            """,
            current_user['user_id']
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            'id': user['id'],
            'email': user['email'],
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'phone': user['phone'],
            'date_of_birth': user['date_of_birth'].isoformat() if user['date_of_birth'] else None,
            'age_verified': user['age_verified'],
            'member_since': user['created_at'].isoformat() if user['created_at'] else None,
            'last_login': user['last_login'].isoformat() if user['last_login'] else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )
    finally:
        if conn:
            await conn.close()