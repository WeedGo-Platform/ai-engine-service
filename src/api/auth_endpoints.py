"""
Authentication API Endpoints
Handles user registration, login, and session management
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import bcrypt
import re
import uuid
import json

from core.authentication import JWTAuthentication
from core.secure_database import SecureDatabase
from services.sales_conversion.services.user_profiler import UserProfiler
from services.sales_conversion.models import UserProfile, CustomerProfile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer()

# Initialize services
jwt_auth = JWTAuthentication()
db = SecureDatabase()
user_profiler = UserProfiler()


# Pydantic models for request/response
class UserRegistration(BaseModel):
    """User registration request model"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    phone: Optional[str] = Field(None, regex=r'^\+?1?\d{10,15}$')
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    date_of_birth: Optional[str] = None  # For age verification
    marketing_consent: bool = False
    terms_accepted: bool = Field(..., description="Must accept terms")
    
    @validator('password')
    def validate_password(cls, v):
        """Ensure password meets security requirements"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v
    
    @validator('date_of_birth')
    def validate_age(cls, v):
        """Ensure user is 21+ years old"""
        if v:
            try:
                dob = datetime.strptime(v, '%Y-%m-%d')
                age = (datetime.now() - dob).days / 365.25
                if age < 21:
                    raise ValueError('Must be 21 years or older')
            except ValueError as e:
                if 'Must be 21' in str(e):
                    raise
                raise ValueError('Invalid date format. Use YYYY-MM-DD')
        return v


class UserLogin(BaseModel):
    """User login request model"""
    email: EmailStr
    password: str
    remember_me: bool = False


class PasswordReset(BaseModel):
    """Password reset request model"""
    email: EmailStr


class PasswordUpdate(BaseModel):
    """Password update model"""
    reset_token: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_password(cls, v):
        """Ensure password meets security requirements"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class TokenRefresh(BaseModel):
    """Token refresh request model"""
    refresh_token: str


class UserProfileUpdate(BaseModel):
    """User profile update model"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    marketing_consent: Optional[bool] = None


# Helper functions
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def create_user_session(user_id: str, email: str, role: str = 'user') -> Dict[str, str]:
    """Create user session with tokens"""
    # Create access token
    access_token = jwt_auth.create_access_token({
        'user_id': user_id,
        'email': email,
        'role': role,
        'session_id': str(uuid.uuid4())
    })
    
    # Create refresh token
    refresh_token = jwt_auth.create_refresh_token({
        'user_id': user_id,
        'email': email
    })
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'bearer'
    }


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


# API Endpoints
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegistration):
    """
    Register a new user account
    
    - Validates email uniqueness
    - Enforces age verification (21+)
    - Creates user profile
    - Returns JWT tokens
    """
    try:
        # Check if user already exists
        existing_user = await db.fetch_one(
            "SELECT id FROM users WHERE email = %s",
            (user_data.email,)
        )
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        # Verify terms acceptance
        if not user_data.terms_accepted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Terms and conditions must be accepted"
            )
        
        # Calculate age verification
        age_verified = False
        if user_data.date_of_birth:
            dob = datetime.strptime(user_data.date_of_birth, '%Y-%m-%d')
            age = (datetime.now() - dob).days / 365.25
            age_verified = age >= 21
        
        # Hash password
        password_hash = hash_password(user_data.password)
        
        # Create user record
        user_id = str(uuid.uuid4())
        await db.execute(
            """
            INSERT INTO users (
                id, email, password_hash, phone, 
                first_name, last_name, date_of_birth,
                age_verified, marketing_consent, terms_accepted,
                created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user_id, user_data.email, password_hash, user_data.phone,
                user_data.first_name, user_data.last_name, user_data.date_of_birth,
                age_verified, user_data.marketing_consent, True,
                datetime.now(), datetime.now()
            )
        )
        
        # Create user profile for sales tracking
        session_id = str(uuid.uuid4())
        profile_id = user_profiler.create_profile(session_id, {
            'email': user_data.email,
            'phone': user_data.phone,
            'age_verified': age_verified,
            'customer_type': CustomerProfile.NEW_USER
        })
        
        # Link profile to user
        await db.execute(
            "UPDATE users SET profile_id = %s, session_id = %s WHERE id = %s",
            (profile_id, session_id, user_id)
        )
        
        # Create session tokens
        tokens = create_user_session(user_id, user_data.email)
        
        logger.info(f"User registered: {user_data.email}")
        
        return {
            'message': 'Registration successful',
            'user': {
                'id': user_id,
                'email': user_data.email,
                'first_name': user_data.first_name,
                'last_name': user_data.last_name,
                'age_verified': age_verified
            },
            'tokens': tokens
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )


@router.post("/login")
async def login(credentials: UserLogin):
    """
    Authenticate user and create session
    
    - Validates credentials
    - Updates last login
    - Returns JWT tokens
    """
    try:
        # Fetch user
        user = await db.fetch_one(
            """
            SELECT id, email, password_hash, first_name, last_name, 
                   age_verified, role, profile_id, session_id
            FROM users 
            WHERE email = %s AND active = true
            """,
            (credentials.email,)
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(credentials.password, user['password_hash']):
            # Log failed attempt
            await db.execute(
                """
                INSERT INTO login_attempts (user_id, email, success, ip_address, timestamp)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user['id'], credentials.email, False, '0.0.0.0', datetime.now())
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Update last login
        await db.execute(
            "UPDATE users SET last_login = %s WHERE id = %s",
            (datetime.now(), user['id'])
        )
        
        # Log successful login
        await db.execute(
            """
            INSERT INTO login_attempts (user_id, email, success, ip_address, timestamp)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user['id'], credentials.email, True, '0.0.0.0', datetime.now())
        )
        
        # Create or update user profile session
        if user['session_id']:
            # Load existing profile
            profile = user_profiler.get_profile(user['session_id'])
            if profile:
                user_profiler.update_profile(user['session_id'], {
                    'last_login': datetime.now().isoformat()
                })
        
        # Create session tokens
        tokens = create_user_session(
            user['id'], 
            user['email'], 
            user.get('role', 'user')
        )
        
        # Add extended expiry for remember me
        if credentials.remember_me:
            tokens['access_token'] = jwt_auth.create_access_token(
                {
                    'user_id': user['id'],
                    'email': user['email'],
                    'role': user.get('role', 'user'),
                    'session_id': user['session_id'] or str(uuid.uuid4())
                },
                expires_delta=timedelta(days=30)
            )
        
        logger.info(f"User logged in: {credentials.email}")
        
        return {
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'age_verified': user['age_verified']
            },
            'tokens': tokens
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )


@router.post("/logout")
async def logout(current_user: Dict = Depends(get_current_user)):
    """
    Logout user and invalidate session
    
    - Invalidates current token
    - Clears session data
    """
    try:
        # Add token to blacklist
        await db.execute(
            """
            INSERT INTO token_blacklist (token_id, user_id, expires_at)
            VALUES (%s, %s, %s)
            """,
            (
                current_user.get('jti', str(uuid.uuid4())),
                current_user['user_id'],
                datetime.fromtimestamp(current_user['exp'])
            )
        )
        
        logger.info(f"User logged out: {current_user['email']}")
        
        return {'message': 'Logout successful'}
        
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/refresh")
async def refresh_token(token_data: TokenRefresh):
    """
    Refresh access token using refresh token
    
    - Validates refresh token
    - Issues new access token
    """
    try:
        # Verify refresh token
        payload = jwt_auth.verify_refresh_token(token_data.refresh_token)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new access token
        access_token = jwt_auth.create_access_token({
            'user_id': payload['user_id'],
            'email': payload['email'],
            'role': payload.get('role', 'user'),
            'session_id': payload.get('session_id', str(uuid.uuid4()))
        })
        
        return {
            'access_token': access_token,
            'token_type': 'bearer'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed"
        )


@router.get("/profile")
async def get_profile(current_user: Dict = Depends(get_current_user)):
    """
    Get current user profile
    
    - Returns user details
    - Returns preferences and settings
    """
    try:
        # Fetch user details
        user = await db.fetch_one(
            """
            SELECT id, email, phone, first_name, last_name,
                   age_verified, created_at, last_login, session_id
            FROM users
            WHERE id = %s
            """,
            (current_user['user_id'],)
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get user profile from profiler
        profile_data = {}
        if user['session_id']:
            profile_data = user_profiler.get_profile(user['session_id']) or {}
        
        return {
            'user': {
                'id': user['id'],
                'email': user['email'],
                'phone': user['phone'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'age_verified': user['age_verified'],
                'created_at': user['created_at'].isoformat(),
                'last_login': user['last_login'].isoformat() if user['last_login'] else None
            },
            'profile': {
                'preferences': profile_data.get('preferences', {}),
                'language': profile_data.get('language', 'en'),
                'timezone': profile_data.get('timezone'),
                'customer_type': profile_data.get('customer_type'),
                'experience_level': profile_data.get('experience_level'),
                'preferred_categories': profile_data.get('preferred_categories', []),
                'preferred_effects': profile_data.get('preferred_effects', [])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile fetch failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch profile"
        )


@router.put("/profile")
async def update_profile(
    profile_update: UserProfileUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Update user profile
    
    - Updates user details
    - Updates preferences
    """
    try:
        # Update user details
        update_fields = []
        update_values = []
        
        if profile_update.first_name is not None:
            update_fields.append("first_name = %s")
            update_values.append(profile_update.first_name)
        
        if profile_update.last_name is not None:
            update_fields.append("last_name = %s")
            update_values.append(profile_update.last_name)
        
        if profile_update.phone is not None:
            update_fields.append("phone = %s")
            update_values.append(profile_update.phone)
        
        if profile_update.marketing_consent is not None:
            update_fields.append("marketing_consent = %s")
            update_values.append(profile_update.marketing_consent)
        
        if update_fields:
            update_fields.append("updated_at = %s")
            update_values.append(datetime.now())
            update_values.append(current_user['user_id'])
            
            await db.execute(
                f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s",
                tuple(update_values)
            )
        
        # Update user profile preferences
        user = await db.fetch_one(
            "SELECT session_id FROM users WHERE id = %s",
            (current_user['user_id'],)
        )
        
        if user and user['session_id']:
            profile_data = {}
            
            if profile_update.preferences:
                profile_data['preferences'] = profile_update.preferences
            
            if profile_update.language:
                profile_data['language'] = profile_update.language
            
            if profile_update.timezone:
                profile_data['timezone'] = profile_update.timezone
            
            if profile_data:
                user_profiler.update_profile(user['session_id'], profile_data)
        
        return {'message': 'Profile updated successfully'}
        
    except Exception as e:
        logger.error(f"Profile update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.post("/verify-age")
async def verify_age(
    date_of_birth: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Verify user age for compliance
    
    - Validates user is 21+
    - Updates age verification status
    """
    try:
        # Parse and validate date
        dob = datetime.strptime(date_of_birth, '%Y-%m-%d')
        age = (datetime.now() - dob).days / 365.25
        
        if age < 21:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Must be 21 years or older to access this service"
            )
        
        # Update user record
        await db.execute(
            """
            UPDATE users 
            SET date_of_birth = %s, age_verified = true, updated_at = %s
            WHERE id = %s
            """,
            (date_of_birth, datetime.now(), current_user['user_id'])
        )
        
        # Update profile
        user = await db.fetch_one(
            "SELECT session_id FROM users WHERE id = %s",
            (current_user['user_id'],)
        )
        
        if user and user['session_id']:
            user_profiler.update_profile(user['session_id'], {
                'age_verified': True
            })
        
        logger.info(f"Age verified for user: {current_user['email']}")
        
        return {
            'message': 'Age verification successful',
            'age_verified': True
        }
        
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    except Exception as e:
        logger.error(f"Age verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Age verification failed"
        )