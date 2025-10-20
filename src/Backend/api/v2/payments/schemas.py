"""
Payment API V2 Schemas

Pydantic models for V2 payment endpoints.
"""

from pydantic import BaseModel, Field, validator
from uuid import UUID
from decimal import Decimal
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ProviderType(str, Enum):
    """Supported payment providers"""
    CLOVER = "clover"
    MONERIS = "moneris"
    INTERAC = "interac"


class PaymentStatusEnum(str, Enum):
    """Payment transaction statuses"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    VOIDED = "voided"
    REFUNDED = "refunded"


class CreatePaymentRequest(BaseModel):
    """Request to create a payment transaction"""
    amount: Decimal = Field(..., gt=0, description="Payment amount (must be positive)")
    currency: str = Field(default='CAD', pattern='^(CAD|USD)$', description="Currency code")
    payment_method_id: UUID = Field(..., description="Payment method UUID")
    provider_type: ProviderType = Field(..., description="Payment provider to use")
    order_id: Optional[UUID] = Field(None, description="Optional order reference")
    idempotency_key: Optional[str] = Field(None, max_length=100, description="Idempotency key to prevent duplicates")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

    @validator('amount')
    def validate_amount_precision(cls, v):
        """Ensure amount has max 2 decimal places"""
        if v.as_tuple().exponent < -2:
            raise ValueError('Amount can have at most 2 decimal places')
        return v

    class Config:
        schema_extra = {
            "example": {
                "amount": 99.99,
                "currency": "CAD",
                "payment_method_id": "123e4567-e89b-12d3-a456-426614174000",
                "provider_type": "clover",
                "order_id": "223e4567-e89b-12d3-a456-426614174001",
                "idempotency_key": "order-2025-01-18-abc123"
            }
        }


class PaymentResponse(BaseModel):
    """Payment transaction response"""
    id: UUID
    transaction_reference: str
    store_id: UUID
    amount: Decimal
    currency: str
    status: PaymentStatusEnum
    provider_transaction_id: Optional[str]
    error_code: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    @classmethod
    def from_entity(cls, transaction):
        """
        Create from PaymentTransaction entity.

        Args:
            transaction: PaymentTransaction domain entity

        Returns:
            PaymentResponse instance
        """
        return cls(
            id=transaction.id,
            transaction_reference=str(transaction.transaction_reference),
            store_id=transaction.store_id,
            amount=transaction.amount.amount,
            currency=transaction.amount.currency,
            status=transaction.status.value,
            provider_transaction_id=transaction.provider_transaction_id,
            error_code=transaction.error_code,
            error_message=transaction.error_message,
            created_at=transaction.created_at,
            completed_at=transaction.completed_at
        )

    class Config:
        schema_extra = {
            "example": {
                "id": "323e4567-e89b-12d3-a456-426614174002",
                "transaction_reference": "TXN-20250118-A3F9B2C1",
                "store_id": "423e4567-e89b-12d3-a456-426614174003",
                "amount": 99.99,
                "currency": "CAD",
                "status": "completed",
                "provider_transaction_id": "ch_1ABC23DEF456",
                "error_code": None,
                "error_message": None,
                "created_at": "2025-01-18T10:30:00Z",
                "completed_at": "2025-01-18T10:30:02Z"
            }
        }


class TransactionListResponse(BaseModel):
    """Paginated list of transactions"""
    transactions: list[PaymentResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


class CreateRefundRequest(BaseModel):
    """Request to create a refund"""
    amount: Decimal = Field(..., gt=0, description="Refund amount (must be positive)")
    currency: str = Field(default='CAD', pattern='^(CAD|USD)$')
    reason: str = Field(..., min_length=1, max_length=500, description="Reason for refund")
    notes: Optional[str] = Field(None, max_length=1000, description="Optional notes")

    @validator('amount')
    def validate_amount_precision(cls, v):
        """Ensure amount has max 2 decimal places"""
        if v.as_tuple().exponent < -2:
            raise ValueError('Amount can have at most 2 decimal places')
        return v

    class Config:
        schema_extra = {
            "example": {
                "amount": 50.00,
                "currency": "CAD",
                "reason": "Customer requested refund",
                "notes": "Defective product"
            }
        }


class RefundResponse(BaseModel):
    """Refund response"""
    id: UUID
    refund_reference: str
    transaction_id: UUID
    amount: Decimal
    currency: str
    status: str
    reason: str
    created_at: datetime
    completed_at: Optional[datetime]

    @classmethod
    def from_entity(cls, refund):
        """
        Create from PaymentRefund entity.

        Args:
            refund: PaymentRefund domain entity

        Returns:
            RefundResponse instance
        """
        return cls(
            id=refund.id,
            refund_reference=refund.refund_reference,
            transaction_id=refund.transaction_id,
            amount=refund.amount.amount,
            currency=refund.amount.currency,
            status=refund.status,
            reason=refund.reason or '',
            created_at=refund.created_at,
            completed_at=refund.completed_at
        )

    class Config:
        schema_extra = {
            "example": {
                "id": "523e4567-e89b-12d3-a456-426614174004",
                "refund_reference": "REF-A3F9B2C1",
                "transaction_id": "323e4567-e89b-12d3-a456-426614174002",
                "amount": 50.00,
                "currency": "CAD",
                "status": "completed",
                "reason": "Customer requested refund",
                "created_at": "2025-01-18T11:00:00Z",
                "completed_at": "2025-01-18T11:00:03Z"
            }
        }


class ProviderConfigRequest(BaseModel):
    """Request to configure payment provider for a store"""
    provider_type: ProviderType
    merchant_id: str = Field(..., min_length=1, max_length=255)
    api_key: str = Field(..., min_length=1, description="API key or access token")
    environment: str = Field(default='sandbox', pattern='^(sandbox|production)$')
    is_active: bool = Field(default=True)

    class Config:
        schema_extra = {
            "example": {
                "provider_type": "clover",
                "merchant_id": "ABCD1234567",
                "api_key": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "environment": "sandbox",
                "is_active": True
            }
        }


class ProviderConfigResponse(BaseModel):
    """Provider configuration response"""
    id: UUID
    store_id: UUID
    provider_type: str
    merchant_id: str
    environment: str
    is_active: bool
    created_at: datetime

    class Config:
        schema_extra = {
            "example": {
                "id": "623e4567-e89b-12d3-a456-426614174005",
                "store_id": "423e4567-e89b-12d3-a456-426614174003",
                "provider_type": "clover",
                "merchant_id": "ABCD1234567",
                "environment": "sandbox",
                "is_active": True,
                "created_at": "2025-01-18T09:00:00Z"
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    error_code: str
    details: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
                "error": "Transaction not found",
                "error_code": "TRANSACTION_NOT_FOUND",
                "details": {"transaction_id": "invalid-uuid"}
            }
        }


# ============================================================================
# Payment Provider Management Schemas
# ============================================================================

class EnvironmentType(str, Enum):
    """Provider environment types"""
    SANDBOX = "sandbox"
    PRODUCTION = "production"


class ProviderHealthStatus(str, Enum):
    """Provider health check statuses"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class CreateProviderRequest(BaseModel):
    """Request to create a payment provider configuration"""
    provider_type: ProviderType = Field(..., description="Type of payment provider")
    merchant_id: str = Field(..., min_length=1, max_length=255, description="Merchant/Store ID from provider")
    api_key: str = Field(..., min_length=1, max_length=500, description="API key or access token (will be encrypted)")
    api_secret: Optional[str] = Field(None, max_length=500, description="API secret key if required (will be encrypted)")
    environment: EnvironmentType = Field(default=EnvironmentType.SANDBOX, description="Environment (sandbox or production)")
    is_active: bool = Field(default=True, description="Whether provider is active")
    webhook_secret: Optional[str] = Field(None, max_length=255, description="Webhook signing secret")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional provider-specific configuration")

    @validator('api_key', 'api_secret')
    def validate_no_whitespace(cls, v):
        """Ensure no leading/trailing whitespace in credentials"""
        if v and v != v.strip():
            raise ValueError('Credentials cannot have leading or trailing whitespace')
        return v.strip() if v else v

    class Config:
        schema_extra = {
            "example": {
                "provider_type": "clover",
                "merchant_id": "ABCD1234567",
                "api_key": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "api_secret": "secret_key_here",
                "environment": "sandbox",
                "is_active": True,
                "webhook_secret": "whsec_abc123",
                "metadata": {
                    "location_id": "LOC123",
                    "supports_tap": True
                }
            }
        }


class UpdateProviderRequest(BaseModel):
    """Request to update a payment provider configuration"""
    merchant_id: Optional[str] = Field(None, min_length=1, max_length=255)
    api_key: Optional[str] = Field(None, min_length=1, max_length=500)
    api_secret: Optional[str] = Field(None, max_length=500)
    environment: Optional[EnvironmentType] = None
    is_active: Optional[bool] = None
    webhook_secret: Optional[str] = Field(None, max_length=255)
    metadata: Optional[Dict[str, Any]] = None

    @validator('api_key', 'api_secret')
    def validate_no_whitespace(cls, v):
        """Ensure no leading/trailing whitespace in credentials"""
        if v and v != v.strip():
            raise ValueError('Credentials cannot have leading or trailing whitespace')
        return v.strip() if v else v

    class Config:
        schema_extra = {
            "example": {
                "api_key": "new_api_key_here",
                "is_active": False,
                "metadata": {
                    "supports_contactless": True
                }
            }
        }


class ProviderResponse(BaseModel):
    """Payment provider configuration response"""
    id: UUID
    tenant_id: UUID
    store_id: Optional[UUID] = None
    provider_type: ProviderType
    merchant_id: str
    environment: EnvironmentType
    is_active: bool
    health_status: Optional[ProviderHealthStatus] = None
    last_health_check: Optional[datetime] = None
    has_credentials: bool = Field(..., description="Whether credentials are configured (never expose actual credentials)")
    has_webhook_secret: bool = Field(..., description="Whether webhook secret is configured")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        schema_extra = {
            "example": {
                "id": "623e4567-e89b-12d3-a456-426614174005",
                "tenant_id": "523e4567-e89b-12d3-a456-426614174004",
                "store_id": "423e4567-e89b-12d3-a456-426614174003",
                "provider_type": "clover",
                "merchant_id": "ABCD1234567",
                "environment": "sandbox",
                "is_active": True,
                "health_status": "healthy",
                "last_health_check": "2025-01-19T10:30:00Z",
                "has_credentials": True,
                "has_webhook_secret": True,
                "metadata": {
                    "location_id": "LOC123",
                    "supports_tap": True
                },
                "created_at": "2025-01-18T09:00:00Z",
                "updated_at": "2025-01-19T10:00:00Z"
            }
        }


class ProviderListResponse(BaseModel):
    """Paginated list of payment providers"""
    providers: list[ProviderResponse]
    total: int
    limit: int = 50
    offset: int = 0

    class Config:
        schema_extra = {
            "example": {
                "providers": [],
                "total": 0,
                "limit": 50,
                "offset": 0
            }
        }


class ProviderHealthCheckResponse(BaseModel):
    """Health check response for a payment provider"""
    provider_id: UUID
    provider_type: ProviderType
    status: ProviderHealthStatus
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")
    error_message: Optional[str] = None
    last_successful_transaction: Optional[datetime] = None
    checked_at: datetime

    class Config:
        schema_extra = {
            "example": {
                "provider_id": "623e4567-e89b-12d3-a456-426614174005",
                "provider_type": "clover",
                "status": "healthy",
                "response_time_ms": 245,
                "error_message": None,
                "last_successful_transaction": "2025-01-19T09:45:00Z",
                "checked_at": "2025-01-19T10:30:00Z"
            }
        }


class CloverOAuthInitiateResponse(BaseModel):
    """Response for Clover OAuth initiation"""
    authorization_url: str = Field(..., description="URL to redirect user for OAuth authorization")
    state: str = Field(..., description="State parameter for CSRF protection")

    class Config:
        schema_extra = {
            "example": {
                "authorization_url": "https://sandbox.dev.clover.com/oauth/authorize?client_id=ABC123&state=xyz789",
                "state": "xyz789"
            }
        }


class CloverOAuthCallbackRequest(BaseModel):
    """Request from Clover OAuth callback"""
    code: str = Field(..., description="Authorization code from Clover")
    merchant_id: str = Field(..., description="Clover merchant ID")
    state: str = Field(..., description="State parameter for CSRF validation")

    class Config:
        schema_extra = {
            "example": {
                "code": "auth_code_abc123",
                "merchant_id": "MERCHANT123",
                "state": "xyz789"
            }
        }
