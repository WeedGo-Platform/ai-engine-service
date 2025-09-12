"""
User Management API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from typing import Dict, Any, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
import asyncpg
import os
import logging

from core.repositories.user_repository import UserRepository
from core.services.login_tracking_service import get_login_tracking_service
from services.otp_service import get_otp_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/users", tags=["users"])


# Pydantic Models
class UserRegistrationRequest(BaseModel):
    tenant_id: UUID
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role: str = Field(default="user")


class UserResponse(BaseModel):
    id: UUID
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    is_active: bool
    tenant_role: Optional[str]


# Database connection pool (singleton)
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
            password=os.getenv('DB_PASSWORD', 'weedgo123'),
            min_size=10,
            max_size=20
        )
    return _db_pool


async def get_user_repository() -> UserRepository:
    """Dependency to get user repository"""
    pool = await get_db_pool()
    return UserRepository(pool)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    http_request: Request,
    request: UserRegistrationRequest,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Register a new user for a tenant"""
    try:
        # Validate password strength
        if len(request.password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Check if password has required complexity
        has_upper = any(c.isupper() for c in request.password)
        has_lower = any(c.islower() for c in request.password)
        has_digit = any(c.isdigit() for c in request.password)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError("Password must contain uppercase, lowercase, and numbers")
        
        # Create the user
        user = await user_repo.create_user(
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name,
            phone=request.phone
        )
        
        # Update user with tenant information
        tenant_user = await user_repo.update_user_tenant(
            user_id=user['id'],
            tenant_id=request.tenant_id,
            role=request.role
        )
        
        # Track initial registration as a login event
        client_ip = http_request.client.host if http_request.client else "unknown"
        user_agent = http_request.headers.get("user-agent", "unknown")
        
        db_pool = await get_db_pool()
        login_tracker = get_login_tracking_service(db_pool)
        await login_tracker.track_login(
            user_id=user['id'],
            tenant_id=request.tenant_id,
            ip_address=client_ip,
            user_agent=user_agent,
            login_successful=True,
            login_method='registration',
            metadata={
                'initial_registration': True,
                'role': request.role
            }
        )
        
        # Send verification OTP for email
        try:
            otp_service = get_otp_service()
            
            # Send email OTP
            await otp_service.create_otp(
                identifier=user['email'],
                identifier_type='email',
                purpose='verification',
                user_id=user['id'],
                ip_address=client_ip,
                user_agent=user_agent
            )
            logger.info(f"Email verification OTP sent to {user['email']}")
            
            # Send phone OTP if phone provided
            if request.phone:
                await otp_service.create_otp(
                    identifier=request.phone,
                    identifier_type='phone',
                    purpose='verification',
                    user_id=user['id'],
                    ip_address=client_ip,
                    user_agent=user_agent
                )
                logger.info(f"Phone verification OTP sent to {request.phone}")
                
        except Exception as e:
            logger.warning(f"Failed to send verification OTP: {e}")
            # Don't fail registration if OTP sending fails
        
        return UserResponse(
            id=user['id'],
            email=user['email'],
            first_name=user['first_name'],
            last_name=user['last_name'],
            phone=user.get('phone'),
            is_active=user.get('active', True),
            tenant_role=tenant_user.get('role') if tenant_user else request.role
        )
        
    except ValueError as e:
        # Handle validation errors and duplicate users
        error_msg = str(e)
        if 'already exists' in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Get user by ID"""
    try:
        user = await user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=user['id'],
            email=user['email'],
            first_name=user['first_name'],
            last_name=user['last_name'],
            phone=user.get('phone'),
            is_active=user.get('is_active', True),
            tenant_role=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user"
        )