"""
User Payment Methods API Endpoints
Simple payment method management for customer profiles
"""

from fastapi import APIRouter, HTTPException, Header, Depends, status
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
import logging
import json

from database.connection import get_db_pool
from core.authentication import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["User Payment Methods"])


def get_user_uuid(current_user: Dict[str, Any]) -> UUID:
    """
    Extract UUID from current_user (always from validated JWT token)
    """
    user_id_str = current_user.get('user_id')

    if not user_id_str:
        logger.error(f"User ID not found in token. Token contents: {current_user}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token"
        )

    try:
        logger.info(f"Attempting to parse user_id: '{user_id_str}' (type: {type(user_id_str).__name__})")
        return UUID(user_id_str)
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid UUID in token: '{user_id_str}' (type: {type(user_id_str).__name__}, error: {str(e)})")
        logger.error(f"Full token contents: {current_user}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in authentication token"
        )


# Pydantic Models
class PaymentMethodCreate(BaseModel):
    """Create payment method request"""
    type: str = Field(..., pattern="^(cash|card|etransfer)$")
    nickname: Optional[str] = None
    is_default: bool = False

    # Card details (only for card type)
    card_brand: Optional[str] = None
    last4: Optional[str] = Field(None, min_length=4, max_length=4)
    card_exp_month: Optional[int] = Field(None, ge=1, le=12)
    card_exp_year: Optional[int] = Field(None, ge=2024)
    payment_token: Optional[str] = None


class PaymentMethodUpdate(BaseModel):
    """Update payment method request"""
    nickname: Optional[str] = None
    is_default: Optional[bool] = None


class PaymentMethodResponse(BaseModel):
    """Payment method response"""
    id: str
    type: str
    nickname: Optional[str]
    card_brand: Optional[str]
    last4: Optional[str]
    is_default: bool
    created_at: datetime


@router.get("/user-payment-methods", response_model=dict)
async def get_payment_methods(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get all payment methods for the current user"""
    try:
        user_id = get_user_uuid(current_user)
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT payment_methods
                FROM profiles
                WHERE user_id = $1
            """, user_id)

            if not row:
                # Create profile if it doesn't exist
                await conn.execute("""
                    INSERT INTO profiles (user_id, payment_methods)
                    VALUES ($1, '[]'::jsonb)
                    ON CONFLICT (user_id) DO NOTHING
                """, user_id)
                return {"payment_methods": []}

            # asyncpg returns JSONB as Python objects directly
            payment_methods = row["payment_methods"] if row["payment_methods"] else []

            # Ensure it's a list (in case it's a string)
            if isinstance(payment_methods, str):
                payment_methods = json.loads(payment_methods)

            return {"payment_methods": payment_methods}

    except Exception as e:
        logger.error(f"Failed to get payment methods: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve payment methods")


@router.post("/user-payment-methods", response_model=dict)
async def add_payment_method(
    payment: PaymentMethodCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Add a new payment method for the current user"""
    try:
        user_id = get_user_uuid(current_user)
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            # Generate new payment method ID
            method_id = str(uuid4())

            # Create new payment method object
            new_method = {
                "id": method_id,
                "type": payment.type,
                "nickname": payment.nickname,
                "card_brand": payment.card_brand,
                "last4": payment.last4,
                "card_exp_month": payment.card_exp_month,
                "card_exp_year": payment.card_exp_year,
                "is_default": payment.is_default,
                "created_at": datetime.now(timezone.utc).isoformat()
            }

            # Check if user exists
            user_exists = await conn.fetchrow("""
                SELECT id FROM users WHERE id = $1
            """, user_id)

            if not user_exists:
                raise HTTPException(
                    status_code=404,
                    detail=f"User {user_id} not found. Please authenticate first."
                )

            # Ensure profile exists (will only work if user exists due to FK constraint)
            await conn.execute("""
                INSERT INTO profiles (user_id, payment_methods)
                VALUES ($1, '[]'::jsonb)
                ON CONFLICT (user_id) DO NOTHING
            """, user_id)

            # If setting as default, unset other defaults
            if payment.is_default:
                await conn.execute("""
                    UPDATE profiles
                    SET payment_methods = (
                        SELECT COALESCE(jsonb_agg(
                            jsonb_set(method, '{is_default}', 'false'::jsonb)
                        ), '[]'::jsonb)
                        FROM jsonb_array_elements(payment_methods) AS method
                    )
                    WHERE user_id = $1
                """, user_id)

            # Append new payment method to array
            await conn.execute("""
                UPDATE profiles
                SET payment_methods = COALESCE(payment_methods, '[]'::jsonb) || $2::jsonb
                WHERE user_id = $1
            """, user_id, json.dumps(new_method))

            return new_method

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add payment method: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add payment method: {str(e)}")


@router.put("/user-payment-methods/{payment_id}", response_model=dict)
async def update_payment_method(
    payment_id: str,
    payment: PaymentMethodUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update a payment method"""
    try:
        user_id = get_user_uuid(current_user)
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            # If setting as default, unset other defaults first
            if payment.is_default:
                await conn.execute("""
                    UPDATE profiles
                    SET payment_methods = (
                        SELECT jsonb_agg(
                            CASE
                                WHEN method->>'id' = $2 THEN method
                                ELSE jsonb_set(method, '{is_default}', 'false'::jsonb)
                            END
                        )
                        FROM jsonb_array_elements(payment_methods) AS method
                    )
                    WHERE user_id = $1
                """, user_id, payment_id)

            # Update the payment method
            update_query = """
                UPDATE profiles
                SET payment_methods = (
                    SELECT jsonb_agg(
                        CASE
                            WHEN method->>'id' = $2 THEN
                                method
                                """ + (f"|| jsonb_build_object('nickname', ${3})" if payment.nickname is not None else "") + """
                                """ + (f"|| jsonb_build_object('is_default', ${4 if payment.nickname is not None else 3})" if payment.is_default is not None else "") + """
                            ELSE method
                        END
                    )
                    FROM jsonb_array_elements(payment_methods) AS method
                )
                WHERE user_id = $1
                RETURNING (
                    SELECT method
                    FROM jsonb_array_elements(payment_methods) AS method
                    WHERE method->>'id' = $2
                    LIMIT 1
                )
            """

            params = [user_id, payment_id]
            if payment.nickname is not None:
                params.append(payment.nickname)
            if payment.is_default is not None:
                params.append(payment.is_default)

            row = await conn.fetchrow(update_query, *params)

            if not row or not row[0]:
                raise HTTPException(status_code=404, detail="Payment method not found")

            return row[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update payment method: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update payment method")


@router.delete("/user-payment-methods/{payment_id}")
async def delete_payment_method(
    payment_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a payment method"""
    try:
        user_id = get_user_uuid(current_user)
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            # Remove payment method from array
            await conn.execute("""
                UPDATE profiles
                SET payment_methods = (
                    SELECT COALESCE(jsonb_agg(method), '[]'::jsonb)
                    FROM jsonb_array_elements(payment_methods) AS method
                    WHERE method->>'id' != $2
                )
                WHERE user_id = $1
            """, user_id, payment_id)

            return {"success": True, "message": "Payment method deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete payment method: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete payment method")


@router.post("/user-payment-methods/{payment_id}/default")
async def set_default_payment(
    payment_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Set a payment method as default"""
    try:
        user_id = get_user_uuid(current_user)
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            # Set the specified method as default, unset others
            await conn.execute("""
                UPDATE profiles
                SET payment_methods = (
                    SELECT jsonb_agg(
                        jsonb_set(method, '{is_default}',
                            CASE WHEN method->>'id' = $2 THEN 'true'::jsonb ELSE 'false'::jsonb END
                        )
                    )
                    FROM jsonb_array_elements(payment_methods) AS method
                )
                WHERE user_id = $1
            """, user_id, payment_id)

            return {"success": True, "message": "Default payment method updated"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set default payment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to set default payment")
