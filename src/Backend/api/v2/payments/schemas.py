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
