"""
Guest Checkout API Endpoints
Handles anonymous checkout with user creation and email verification
"""

from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from datetime import datetime, timezone
from uuid import uuid4
from pydantic import BaseModel, Field, EmailStr
import logging
import secrets

from database.connection import get_db_pool

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/checkout", tags=["Guest Checkout"])


# Pydantic Models
class GuestCheckoutRequest(BaseModel):
    """Guest checkout user information"""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    tenant_id: Optional[str] = None  # If known from context


class GuestCheckoutResponse(BaseModel):
    """Response after guest checkout attempt"""
    success: bool
    user_id: Optional[str] = None
    user_exists: bool = False
    message: str
    requires_login: bool = False


async def send_verification_email(email: str, first_name: str, token: str):
    """Send password setup/verification email"""
    # TODO: Integrate with actual email service
    # For now, just log the verification link
    verification_link = f"https://app.weedgo.com/verify-email?token={token}"

    logger.info(f"""
    ========================================
    VERIFICATION EMAIL
    ========================================
    To: {email}
    Subject: Set up your WeedGo account password

    Hi {first_name},

    Thank you for your order! To complete your account setup and
    track your orders, please set up your password:

    {verification_link}

    This link will expire in 24 hours.

    Best regards,
    WeedGo Team
    ========================================
    """)

    # TODO: Replace with actual email sending
    # await email_service.send_template(
    #     to=email,
    #     template="password_setup",
    #     context={
    #         "first_name": first_name,
    #         "verification_link": verification_link
    #     }
    # )


@router.post("/guest-user", response_model=GuestCheckoutResponse)
async def create_guest_checkout_user(
    request: GuestCheckoutRequest,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
):
    """
    Create or validate user for guest checkout

    Flow:
    1. Check if user exists by email/phone for tenant
    2. If exists → Return user_exists=True, requires_login=True
    3. If not → Create passwordless user + profile + send verification email
    """
    try:
        pool = await get_db_pool()
        tenant_id = request.tenant_id or x_tenant_id

        async with pool.acquire() as conn:
            # Check if user exists by email OR phone for this tenant
            existing_user = await conn.fetchrow("""
                SELECT id, email, phone, first_name, last_name
                FROM users
                WHERE (email = $1 OR phone = $2)
                AND (tenant_id = $3 OR tenant_id IS NULL)
                AND active = true
                LIMIT 1
            """, request.email, request.phone, tenant_id)

            if existing_user:
                # User already exists - they should login instead
                logger.info(f"User exists: {existing_user['email']} - requiring login")
                return GuestCheckoutResponse(
                    success=False,
                    user_id=None,
                    user_exists=True,
                    message=f"An account with this email/phone already exists. Please login to continue.",
                    requires_login=True
                )

            # Create new user (passwordless initially)
            user_id = uuid4()
            verification_token = secrets.token_urlsafe(32)

            # Generate temporary password hash (will be replaced when user sets password)
            temp_password_hash = f"UNVERIFIED_{secrets.token_hex(16)}"

            await conn.execute("""
                INSERT INTO users (
                    id, email, phone, first_name, last_name,
                    password_hash, tenant_id, active, email_verified,
                    role, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW())
            """, user_id, request.email, request.phone, request.first_name,
                request.last_name, temp_password_hash, tenant_id,
                True, False, 'customer')

            # Create profile for the user
            await conn.execute("""
                INSERT INTO profiles (
                    user_id, first_name, last_name, phone,
                    payment_methods, created_at
                ) VALUES ($1, $2, $3, $4, '[]'::jsonb, NOW())
            """, user_id, request.first_name, request.last_name,
                request.phone)

            # Store verification token (you may want a separate table for this)
            # For now, we'll use the session or send directly

            # Send verification email
            await send_verification_email(
                email=request.email,
                first_name=request.first_name,
                token=verification_token
            )

            logger.info(f"Created guest checkout user: {user_id} - {request.email}")

            return GuestCheckoutResponse(
                success=True,
                user_id=str(user_id),
                user_exists=False,
                message=f"Account created successfully! Check your email to set up your password.",
                requires_login=False
            )

    except Exception as e:
        logger.error(f"Failed to create guest checkout user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process checkout: {str(e)}"
        )


@router.get("/check-user/{email}")
async def check_user_exists(
    email: str,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
):
    """Quick check if user exists by email"""
    try:
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            existing_user = await conn.fetchrow("""
                SELECT id, email, first_name, last_name
                FROM users
                WHERE email = $1
                AND (tenant_id = $2 OR tenant_id IS NULL)
                AND active = true
            """, email, x_tenant_id)

            return {
                "exists": existing_user is not None,
                "requires_login": existing_user is not None
            }

    except Exception as e:
        logger.error(f"Failed to check user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
