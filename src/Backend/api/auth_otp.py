"""
OTP Authentication API Endpoints
One-time passcode login via SMS and Email
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any, Literal
from datetime import datetime
import logging
import asyncpg
import os
import uuid
import re

from core.authentication import JWTAuthentication
from services.otp_service import get_otp_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth/otp", tags=["OTP Authentication"])
security = HTTPBearer()

# Initialize services
jwt_auth = JWTAuthentication()
otp_service = get_otp_service()


# Pydantic models
class OTPRequest(BaseModel):
    """Request model for sending OTP"""
    identifier: str = Field(..., description="Email address or phone number")
    identifier_type: Literal['email', 'phone'] = Field(..., description="Type of identifier")
    purpose: Literal['login', 'verification', 'password_reset'] = Field(default='login')
    create_user_if_missing: bool = Field(
        default=True, 
        description="If True, creates user if not exists. Set to False during signup to prevent premature user creation."
    )
    
    @validator('identifier')
    def validate_identifier(cls, v, values):
        """Validate identifier based on type"""
        if 'identifier_type' in values:
            if values['identifier_type'] == 'email':
                # Basic email validation
                if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
                    raise ValueError('Invalid email format. Please provide a valid email address.')
            elif values['identifier_type'] == 'phone':
                # Basic phone validation - just check if it has digits
                cleaned = re.sub(r'\D', '', v)
                if len(cleaned) < 10:
                    raise ValueError(f'Phone number too short. Must be at least 10 digits. Received: {len(cleaned)} digits')
                if len(cleaned) > 15:
                    raise ValueError(f'Phone number too long. Maximum 15 digits allowed. Received: {len(cleaned)} digits')
        return v


class OTPVerify(BaseModel):
    """Request model for verifying OTP"""
    identifier: str = Field(..., description="Email address or phone number")
    identifier_type: Literal['email', 'phone'] = Field(..., description="Type of identifier")
    code: str = Field(..., min_length=4, max_length=10, description="OTP code")
    purpose: Literal['login', 'verification', 'password_reset'] = Field(default='login')
    create_user_if_missing: bool = Field(
        default=True,
        description="If True, creates user if not exists. Set to False during signup to prevent premature user creation."
    )


class OTPResponse(BaseModel):
    """Response model for OTP operations"""
    success: bool
    message: str
    expires_in_minutes: Optional[int] = None
    access_token: Optional[str] = None
    user: Optional[Dict[str, Any]] = None


# Database helper
async def get_db_connection():
    """Get database connection"""
    try:
        conn = await asyncpg.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5434)),
            database=os.getenv('DB_NAME', 'ai_engine'),
            user=os.getenv('DB_USER', 'weedgo'),
            password=os.getenv('DB_PASSWORD', 'weedgo123')
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed"
        )


async def get_or_create_user_by_identifier(
    identifier: str, 
    identifier_type: Literal['email', 'phone'],
    create_if_missing: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Get existing user or optionally create a new one based on identifier
    
    Args:
        identifier: Email address or phone number
        identifier_type: Type of identifier ('email' or 'phone')
        create_if_missing: If True, creates user if not found. If False, returns None.
                          Set to False during signup to avoid premature user creation.
    
    Returns:
        User dict if found/created, None otherwise
    """
    conn = None
    try:
        conn = await get_db_connection()
        
        # Check if user exists
        if identifier_type == 'email':
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE email = $1",
                identifier.lower()
            )
        else:
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE phone = $1",
                identifier
            )
        
        if user:
            return dict(user)
        
        # Only create user if explicitly allowed
        if not create_if_missing:
            logger.info(f"User not found for {identifier_type}: {identifier} (create_if_missing=False)")
            return None
        
        # Create new user if doesn't exist
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        if identifier_type == 'email':
            await conn.execute(
                """
                INSERT INTO users (
                    id, email, password_hash, session_id, 
                    email_verified, active, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                user_id, identifier.lower(), 'OTP_AUTH', session_id,
                True, True, datetime.now(), datetime.now()
            )
        else:
            await conn.execute(
                """
                INSERT INTO users (
                    id, phone, password_hash, session_id,
                    phone_verified, active, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                user_id, identifier, 'OTP_AUTH', session_id,
                True, True, datetime.now(), datetime.now()
            )
        
        # Fetch and return the new user
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE id = $1",
            user_id
        )
        
        logger.info(f"Created new user for {identifier_type}: {identifier}")
        return dict(user) if user else None
        
    except Exception as e:
        logger.error(f"User lookup/creation failed: {e}")
        return None
    finally:
        if conn:
            await conn.close()


# API Endpoints
@router.post("/send", response_model=OTPResponse)
async def send_otp(request: Request, otp_request: OTPRequest):
    """
    Send OTP to email or phone number
    
    This endpoint sends a one-time passcode to the specified identifier.
    The OTP can be used for login, verification, or password reset.
    
    Rate limiting is applied to prevent abuse.
    """
    try:
        # Get IP address for rate limiting
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get('User-Agent')
        
        # Get user if exists (or create if allowed)
        user = await get_or_create_user_by_identifier(
            otp_request.identifier, 
            otp_request.identifier_type,
            create_if_missing=otp_request.create_user_if_missing
        )
        
        user_id = user['id'] if user else None
        
        # Create and send OTP
        result = await otp_service.create_otp(
            identifier=otp_request.identifier,
            identifier_type=otp_request.identifier_type,
            purpose=otp_request.purpose,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if result.get('rate_limited'):
            # Calculate retry-after time (default to 5 minutes if not specified)
            retry_after = result.get('retry_after_seconds', 300)
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many OTP requests. Please try again in {retry_after // 60} minutes.",
                headers={"Retry-After": str(retry_after)}
            )
        
        if not result['success']:
            error_msg = result.get('error', 'Failed to send OTP')
            
            # Check if it's a provider failure (all providers failed)
            if 'All providers failed' in error_msg or 'provider' in error_msg.lower():
                # More user-friendly message for provider failures
                if otp_request.identifier_type == 'email':
                    detail = (
                        "We're experiencing temporary issues with our email service. "
                        "Our backup providers (AWS SES, SendGrid, Gmail SMTP) are all unavailable. "
                        "Please try again in a few moments, or contact support if this persists."
                    )
                else:
                    detail = (
                        "We're experiencing temporary issues with our SMS service. "
                        "Please try again in a few moments, or skip phone verification for now. "
                        "You can add your phone number later from your account settings."
                    )
            else:
                detail = error_msg
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=detail
            )
        
        return OTPResponse(
            success=True,
            message=result['message'],
            expires_in_minutes=result.get('expires_in_minutes')
        )
        
    except HTTPException:
        raise
    except ValueError as ve:
        logger.error(f"OTP validation error: {ve}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"OTP send failed: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send verification code: {type(e).__name__}"
        )


@router.post("/verify", response_model=OTPResponse)
async def verify_otp(otp_verify: OTPVerify):
    """
    Verify OTP and authenticate user
    
    This endpoint verifies the OTP code and returns an access token
    if successful. If the user doesn't exist, a new account is created.
    """
    try:
        # Verify OTP
        result = await otp_service.verify_otp(
            identifier=otp_verify.identifier,
            identifier_type=otp_verify.identifier_type,
            code=otp_verify.code,
            purpose=otp_verify.purpose
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error', 'Invalid verification code')
            )
        
        # Get or create user (only if create_user_if_missing is True)
        user = await get_or_create_user_by_identifier(
            otp_verify.identifier,
            otp_verify.identifier_type,
            create_if_missing=otp_verify.create_user_if_missing
        )
        
        if not user:
            # User doesn't exist and create_user_if_missing is False
            # This is expected during signup - verification is just for the identifier
            return OTPResponse(
                success=True,
                message="Verification successful",
                access_token=None,
                user=None
            )
        
        # Update verification status
        conn = None
        try:
            conn = await get_db_connection()
            
            if otp_verify.identifier_type == 'email':
                await conn.execute(
                    "UPDATE users SET email_verified = TRUE, last_login = $1 WHERE id = $2",
                    datetime.now(), user['id']
                )
            else:
                await conn.execute(
                    "UPDATE users SET phone_verified = TRUE, last_login = $1 WHERE id = $2",
                    datetime.now(), user['id']
                )
        finally:
            if conn:
                await conn.close()
        
        # Create JWT token (ensure all values are strings)
        access_token = jwt_auth.create_access_token({
            'user_id': str(user['id']),
            'email': user.get('email'),
            'phone': user.get('phone'),
            'session_id': str(user.get('session_id') or uuid.uuid4())
        })
        
        logger.info(f"OTP login successful for user {user['id']}")
        
        # Prepare user data for response (convert UUID to string)
        user_data = {
            'id': str(user['id']),
            'email': user.get('email'),
            'phone': user.get('phone'),
            'first_name': user.get('first_name'),
            'last_name': user.get('last_name'),
            'age_verified': user.get('age_verified', False),
            'email_verified': user.get('email_verified', False),
            'phone_verified': user.get('phone_verified', False)
        }
        
        return OTPResponse(
            success=True,
            message="Login successful",
            access_token=access_token,
            user=user_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OTP verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verification failed"
        )


@router.post("/resend", response_model=OTPResponse)
async def resend_otp(request: Request, otp_request: OTPRequest):
    """
    Resend OTP code
    
    This endpoint resends a new OTP code to the specified identifier.
    Previous unused codes are invalidated.
    """
    # This uses the same logic as send_otp
    return await send_otp(request, otp_request)


@router.get("/status/{identifier}")
async def check_otp_status(
    identifier: str,
    identifier_type: Literal['email', 'phone'] = 'email'
):
    """
    Check if there's an active OTP for the identifier
    
    This endpoint checks if there's a valid, unexpired OTP
    for the given identifier.
    """
    conn = None
    try:
        conn = await get_db_connection()
        
        # Check for active OTP
        otp_record = await conn.fetchrow(
            """
            SELECT expires_at, attempts, max_attempts
            FROM otp_codes
            WHERE identifier = $1
            AND identifier_type = $2
            AND verified = FALSE
            AND expires_at > CURRENT_TIMESTAMP
            ORDER BY created_at DESC
            LIMIT 1
            """,
            identifier, identifier_type
        )
        
        if otp_record:
            remaining_seconds = int((otp_record['expires_at'] - datetime.now()).total_seconds())
            remaining_attempts = otp_record['max_attempts'] - otp_record['attempts']
            
            return {
                'has_active_otp': True,
                'expires_in_seconds': remaining_seconds,
                'remaining_attempts': remaining_attempts
            }
        else:
            return {
                'has_active_otp': False
            }
            
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check OTP status"
        )
    finally:
        if conn:
            await conn.close()


@router.delete("/cleanup")
async def cleanup_expired_otps():
    """
    Cleanup expired OTP codes
    
    This endpoint removes expired OTP codes from the database.
    This is typically called by a scheduled job.
    """
    conn = None
    try:
        conn = await get_db_connection()
        
        # Call cleanup function
        await conn.execute("SELECT cleanup_expired_otp_codes()")
        
        logger.info("Expired OTP codes cleaned up")
        
        return {
            'success': True,
            'message': 'Expired OTP codes cleaned up'
        }
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cleanup failed"
        )
    finally:
        if conn:
            await conn.close()