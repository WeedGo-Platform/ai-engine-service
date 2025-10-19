"""
Payment Session Endpoints
Handles payment session creation for Clover and other payment providers
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime, timedelta
import json
import os
import httpx
import socket
import logging
import psycopg2.extras
from database.connection import get_db_connection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/payment", tags=["payment-session"])


class CreateSessionRequest(BaseModel):
    """Request model for creating a payment session"""
    amount: int  # Amount in cents
    currency: str = "CAD"
    storeId: str
    metadata: Optional[Dict[str, Any]] = None


class CreateCardTokenRequest(BaseModel):
    """Request model for creating a card token"""
    card: Dict[str, str]  # Contains number, exp_month, exp_year, cvv, zip
    storeId: str


class CreateChargeRequest(BaseModel):
    """Request model for creating a charge"""
    amount: int  # Amount in cents
    currency: str = "CAD"
    source: str  # Token from card tokenization
    storeId: str
    description: Optional[str] = None


class PaymentSessionResponse(BaseModel):
    """Response model for payment session"""
    sessionId: str
    publicKey: str
    amount: int
    currency: str
    expiresAt: str


@router.post("/create-card-token")
async def create_card_token(request: CreateCardTokenRequest):
    """
    Create a card token using Clover's tokenization API
    """
    try:
        # Get store payment configuration from database
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            cursor.execute(
                """
                SELECT settings->'onlinePayment' as online_payment_settings
                FROM stores
                WHERE id = %s
                """,
                (request.storeId,)
            )
            result = cursor.fetchone()

            if not result or not result['online_payment_settings']:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Store payment configuration not found"
                )

            payment_settings = result['online_payment_settings']

            # Extract Clover configuration
            public_key = payment_settings.get('accessToken') or payment_settings.get('access_token')
            environment = payment_settings.get('environment', 'sandbox')

            if not public_key:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment credentials not configured"
                )

            # Determine Clover API URL based on environment
            if environment == 'production':
                api_url = "https://token.clover.com/v1/tokens"
            else:
                api_url = "https://token-sandbox.dev.clover.com/v1/tokens"

            # Create token with Clover API
            # Force IPv4 to avoid IPv6 timeout issues
            transport = httpx.AsyncHTTPTransport(local_address="0.0.0.0")
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0), transport=transport) as client:
                logger.info(f"Attempting to tokenize card with Clover API at {api_url}")
                response = await client.post(
                    api_url,
                    headers={
                        "apikey": public_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "card": {
                            "number": request.card['number'],
                            "exp_month": request.card['exp_month'],
                            "exp_year": request.card['exp_year'],
                            "cvv": request.card['cvv'],
                            "zip": request.card.get('zip', '')
                        }
                    }
                )

                if response.status_code != 200:
                    error_data = response.json()
                    logger.error(f"Clover tokenization failed: {error_data}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=error_data.get('message', 'Failed to tokenize card')
                    )

                token_data = response.json()
                return {"token": token_data['id']}

        finally:
            cursor.close()
            conn.close()

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error creating card token: {str(e)}\nTraceback: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating card token: {str(e)}"
        )


@router.post("/create-charge")
async def create_charge(request: CreateChargeRequest):
    """
    Create a charge using the tokenized card
    """
    try:
        # Get store payment configuration from database
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            cursor.execute(
                """
                SELECT settings->'onlinePayment' as online_payment_settings
                FROM stores
                WHERE id = %s
                """,
                (request.storeId,)
            )
            result = cursor.fetchone()

            if not result or not result['online_payment_settings']:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Store payment configuration not found"
                )

            payment_settings = result['online_payment_settings']

            # Extract Clover configuration
            merchant_id = payment_settings.get('merchantId') or payment_settings.get('merchant_id')
            environment = payment_settings.get('environment', 'sandbox')

            # Check if we have a private OAuth token
            private_key = payment_settings.get('privateKey') or payment_settings.get('private_key') or payment_settings.get('oauthToken')

            if not merchant_id or not private_key:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment credentials not configured. OAuth token required for creating charges."
                )

            # Determine Clover API URL based on environment
            if environment == 'production':
                api_url = "https://scl.clover.com/v1/charges"
            else:
                api_url = "https://scl-sandbox.dev.clover.com/v1/charges"

            # Create charge with Clover API
            # Force IPv4 to avoid IPv6 timeout issues
            transport = httpx.AsyncHTTPTransport(local_address="0.0.0.0")
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0), transport=transport) as client:
                logger.info(f"Attempting to create charge with Clover API at {api_url}")
                response = await client.post(
                    api_url,
                    headers={
                        "Authorization": f"Bearer {private_key}",
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    json={
                        "amount": request.amount,
                        "currency": request.currency.lower(),
                        "source": request.source,
                        "description": request.description or f"Payment for order"
                    }
                )

                if response.status_code not in [200, 201]:
                    try:
                        error_data = response.json()
                        logger.error(f"Clover charge creation failed: Status={response.status_code}, Error={error_data}")
                        error_message = error_data.get('error', {}).get('message') or error_data.get('message', 'Payment failed')
                    except Exception:
                        logger.error(f"Clover charge creation failed: Status={response.status_code}, Response={response.text}")
                        error_message = f"Payment failed with status {response.status_code}"

                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=error_message
                    )

                charge_data = response.json()
                return {
                    "id": charge_data['id'],
                    "amount": charge_data['amount'],
                    "currency": charge_data['currency'],
                    "status": charge_data['status'],
                    "paid": charge_data.get('paid', False),
                    "captured": charge_data.get('captured', False),
                    "created": charge_data.get('created'),
                    "outcome": charge_data.get('outcome', {})
                }

        finally:
            cursor.close()
            conn.close()

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error creating charge: {str(e)}\nTraceback: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing payment: {str(e)}"
        )


@router.post("/create-session", response_model=PaymentSessionResponse)
async def create_payment_session(request: CreateSessionRequest):
    """
    Legacy endpoint for payment session creation (kept for compatibility)
    """
    try:
        session_id = f"session_{uuid4().hex}"
        expires_at = datetime.utcnow() + timedelta(minutes=15)

        return PaymentSessionResponse(
            sessionId=session_id,
            publicKey="",
            amount=request.amount,
            currency=request.currency,
            expiresAt=expires_at.isoformat()
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating payment session: {str(e)}"
        )