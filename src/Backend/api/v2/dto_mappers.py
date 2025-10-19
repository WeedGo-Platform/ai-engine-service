"""
DTO Mappers for V2 API
Converts Domain objects to Data Transfer Objects (API responses)
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field
from decimal import Decimal
from uuid import UUID


# Payment DTOs
class MoneyDTO(BaseModel):
    """Money value object DTO"""
    amount: float
    currency: str = "CAD"

    class Config:
        json_schema_extra = {
            "example": {
                "amount": 99.99,
                "currency": "CAD"
            }
        }


class RefundDTO(BaseModel):
    """Refund entity DTO"""
    id: str
    refund_amount: MoneyDTO
    refund_reason: str
    refund_notes: Optional[str] = None
    status: str
    requested_at: datetime
    completed_at: Optional[datetime] = None
    requested_by: Optional[str] = None


class PaymentTransactionDTO(BaseModel):
    """Payment transaction aggregate DTO"""
    # Identifiers
    id: str
    order_id: str
    store_id: str
    tenant_id: str
    customer_id: Optional[str] = None

    # Payment details
    amount: float
    currency: str
    status: str
    payment_method: str
    provider: str

    # Gateway details
    transaction_id: Optional[str] = None
    authorization_code: Optional[str] = None

    # Refunds
    refunded_amount: float = 0.0
    refunds: List[RefundDTO] = Field(default_factory=list)

    # Timestamps
    created_at: datetime
    updated_at: datetime
    authorized_at: Optional[datetime] = None
    captured_at: Optional[datetime] = None

    # Failure details (if applicable)
    failure_reason: Optional[str] = None

    # Domain events (for debugging/monitoring)
    events: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "order_id": "order-123",
                "store_id": "store-456",
                "tenant_id": "tenant-789",
                "amount": 99.99,
                "currency": "CAD",
                "status": "captured",
                "payment_method": "credit_card",
                "provider": "stripe",
                "transaction_id": "txn_abc123",
                "refunded_amount": 0.0,
                "refunds": [],
                "created_at": "2025-10-09T12:00:00Z",
                "updated_at": "2025-10-09T12:00:00Z",
                "events": ["PaymentInitiated", "PaymentCaptured"]
            }
        }


class PaymentListDTO(BaseModel):
    """List of payment transactions"""
    payments: List[PaymentTransactionDTO]
    total: int
    page: int = 1
    page_size: int = 50


# Mapper functions
def map_money_to_dto(money) -> MoneyDTO:
    """Convert Money value object to DTO"""
    if not money:
        return MoneyDTO(amount=0.0, currency="CAD")

    return MoneyDTO(
        amount=float(money.amount),
        currency=money.currency
    )


def map_refund_to_dto(refund) -> RefundDTO:
    """Convert Refund entity to DTO"""
    return RefundDTO(
        id=str(refund.id),
        refund_amount=map_money_to_dto(refund.refund_amount),
        refund_reason=refund.refund_reason.value if hasattr(refund.refund_reason, 'value') else str(refund.refund_reason),
        refund_notes=refund.refund_notes,
        status=refund.status,
        requested_at=refund.requested_at,
        completed_at=refund.completed_at,
        requested_by=str(refund.requested_by) if refund.requested_by else None
    )


def map_payment_to_dto(payment) -> PaymentTransactionDTO:
    """
    Convert PaymentTransaction aggregate to DTO

    This is the main mapper that transforms the rich domain model
    into a lightweight API response
    """
    # Handle dict input (from database)
    if isinstance(payment, dict):
        return PaymentTransactionDTO(
            id=str(payment.get("id", "")),
            order_id=str(payment.get("order_id", "")),
            store_id=str(payment.get("store_id", "")),
            tenant_id=str(payment.get("tenant_id", "")),
            customer_id=str(payment.get("customer_id")) if payment.get("customer_id") else None,
            amount=float(payment.get("amount", 0)),
            currency=payment.get("currency", "CAD"),
            status=payment.get("status", "pending"),
            payment_method=payment.get("payment_method", ""),
            provider=payment.get("provider", ""),
            transaction_id=payment.get("transaction_id"),
            authorization_code=payment.get("authorization_code"),
            refunded_amount=float(payment.get("refunded_amount", 0)),
            refunds=[],
            created_at=payment.get("created_at", datetime.utcnow()),
            updated_at=payment.get("updated_at", datetime.utcnow()),
            authorized_at=payment.get("authorized_at"),
            captured_at=payment.get("captured_at"),
            failure_reason=payment.get("failure_reason"),
            events=payment.get("events", [])
        )

    # Handle domain object
    return PaymentTransactionDTO(
        # Identifiers
        id=str(payment.id),
        order_id=str(payment.order_id),
        store_id=str(payment.store_id),
        tenant_id=str(payment.tenant_id),
        customer_id=str(payment.customer_id) if payment.customer_id else None,

        # Payment details
        amount=float(payment.payment_amount.amount),
        currency=payment.payment_amount.currency,
        status=payment.payment_status.value,
        payment_method=payment.payment_method_details.payment_method.value,
        provider=payment.payment_provider.value,

        # Gateway details
        transaction_id=payment.gateway_transaction_id,
        authorization_code=payment.authorization_code,

        # Refunds
        refunded_amount=float(payment.refunded_amount.amount) if payment.refunded_amount else 0.0,
        refunds=[map_refund_to_dto(r) for r in payment.refunds] if payment.refunds else [],

        # Timestamps
        created_at=payment.created_at,
        updated_at=payment.updated_at,
        authorized_at=payment.authorized_at,
        captured_at=payment.captured_at,

        # Failure details
        failure_reason=payment.failure_reason,

        # Events (for debugging)
        events=[type(event).__name__ for event in payment.domain_events] if hasattr(payment, 'domain_events') else []
    )


def map_payment_list_to_dto(
    payments: List,
    total: int,
    page: int = 1,
    page_size: int = 50
) -> PaymentListDTO:
    """Convert list of payments to paginated DTO"""
    return PaymentListDTO(
        payments=[map_payment_to_dto(p) for p in payments],
        total=total,
        page=page,
        page_size=page_size
    )


# Request DTOs (for incoming data)
class ProcessPaymentRequest(BaseModel):
    """Request to process a payment"""
    order_id: str = Field(..., description="Order ID for this payment")
    amount: float = Field(..., gt=0, description="Payment amount (must be positive)")
    currency: str = Field(default="CAD", description="Currency code")
    payment_method: str = Field(..., description="Payment method (credit_card, debit_card, cash, etc.)")
    card_token: Optional[str] = Field(None, description="Tokenized card reference (for card payments)")
    customer_id: Optional[str] = Field(None, description="Customer ID (optional)")

    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "order-123-456",
                "amount": 99.99,
                "currency": "CAD",
                "payment_method": "credit_card",
                "card_token": "tok_1234567890",
                "customer_id": "customer-abc"
            }
        }


class RefundPaymentRequest(BaseModel):
    """Request to refund a payment"""
    amount: Optional[float] = Field(None, description="Refund amount (None = full refund)")
    reason: str = Field(..., description="Reason for refund")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")

    class Config:
        json_schema_extra = {
            "example": {
                "amount": 49.99,
                "reason": "customer_request",
                "notes": "Customer requested partial refund"
            }
        }


# ============================================================================
# Order Management DTOs
# ============================================================================

class OrderLineDTO(BaseModel):
    """Order line item DTO"""
    line_number: int
    sku: str
    product_name: str
    product_type: str
    quantity: int
    unit_price: float
    discount_amount: float = 0.0
    tax_amount: float = 0.0
    line_total: float = 0.0

    # Cannabis specific
    thc_percentage: Optional[float] = None
    cbd_percentage: Optional[float] = None
    product_category: Optional[str] = None

    # Fulfillment
    fulfilled_quantity: int = 0
    is_fulfilled: bool = False


class OrderTotalsDTO(BaseModel):
    """Order financial totals DTO"""
    subtotal: float
    tax_amount: float
    discount_amount: float
    delivery_fee: float
    tip_amount: float
    total_amount: float


class OrderStatusTransitionDTO(BaseModel):
    """Order status transition DTO"""
    from_status: str
    to_status: str
    transitioned_at: datetime
    transitioned_by: Optional[str] = None
    reason: Optional[str] = None


class OrderDTO(BaseModel):
    """Order aggregate DTO"""
    # Identifiers
    id: str
    order_number: str
    store_id: str
    customer_id: Optional[str] = None

    # Status
    status: str
    payment_status: str
    fulfillment_status: str

    # Order details
    order_type: str
    delivery_method: str

    # Line items
    items: List[OrderLineDTO] = Field(default_factory=list)

    # Financial
    totals: OrderTotalsDTO

    # Payment
    payment_method: Optional[str] = None
    payment_transaction_id: Optional[str] = None

    # Delivery/Pickup
    delivery_address: Optional[Dict[str, Any]] = None
    delivery_instructions: Optional[str] = None
    pickup_time: Optional[datetime] = None
    estimated_delivery_time: Optional[datetime] = None
    actual_delivery_time: Optional[datetime] = None

    # Customer info
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None

    # Notes
    customer_notes: Optional[str] = None
    internal_notes: Optional[str] = None
    cancellation_reason: Optional[str] = None

    # Status history
    status_history: List[OrderStatusTransitionDTO] = Field(default_factory=list)

    # Timestamps
    created_at: datetime
    updated_at: datetime
    confirmed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    # Domain events
    events: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "order_number": "ORD-2025-10-ABC12",
                "store_id": "store-123",
                "customer_id": "customer-456",
                "status": "confirmed",
                "payment_status": "paid",
                "fulfillment_status": "unfulfilled",
                "order_type": "online",
                "delivery_method": "delivery",
                "items": [
                    {
                        "line_number": 1,
                        "sku": "PROD-001",
                        "product_name": "Blue Dream 3.5g",
                        "product_type": "cannabis",
                        "quantity": 2,
                        "unit_price": 35.00,
                        "tax_amount": 9.10,
                        "line_total": 79.10
                    }
                ],
                "totals": {
                    "subtotal": 70.00,
                    "tax_amount": 9.10,
                    "discount_amount": 0.00,
                    "delivery_fee": 5.00,
                    "tip_amount": 0.00,
                    "total_amount": 84.10
                },
                "created_at": "2025-10-09T12:00:00Z",
                "updated_at": "2025-10-09T12:00:00Z",
                "events": ["OrderCreated", "OrderConfirmed"]
            }
        }


class OrderListDTO(BaseModel):
    """List of orders"""
    orders: List[OrderDTO]
    total: int
    page: int = 1
    page_size: int = 50


# Order Request DTOs
class CreateOrderRequest(BaseModel):
    """Request to create a new order"""
    store_id: str = Field(..., description="Store ID")
    order_type: str = Field(default="online", description="Order type (online, in_store, kiosk, phone, mobile_app)")
    delivery_method: str = Field(default="pickup", description="Delivery method (pickup, delivery, curbside, in_store)")
    customer_id: Optional[str] = Field(None, description="Customer ID (optional for guest checkout)")
    customer_name: Optional[str] = Field(None, description="Customer name")
    customer_email: Optional[str] = Field(None, description="Customer email")
    customer_phone: Optional[str] = Field(None, description="Customer phone")
    customer_notes: Optional[str] = Field(None, max_length=500, description="Customer notes")

    class Config:
        json_schema_extra = {
            "example": {
                "store_id": "store-123",
                "order_type": "online",
                "delivery_method": "delivery",
                "customer_email": "customer@example.com",
                "customer_phone": "+1-416-555-0123"
            }
        }


class AddOrderItemRequest(BaseModel):
    """Request to add item to order"""
    sku: str = Field(..., description="Product SKU")
    product_name: str = Field(..., description="Product name")
    product_type: str = Field(..., description="Product type (cannabis, accessory)")
    quantity: int = Field(..., gt=0, description="Quantity (must be positive)")
    unit_price: float = Field(..., gt=0, description="Unit price")
    tax_rate: float = Field(default=13.0, description="Tax rate percentage")

    # Cannabis specific
    thc_percentage: Optional[float] = Field(None, description="THC percentage")
    cbd_percentage: Optional[float] = Field(None, description="CBD percentage")
    product_category: Optional[str] = Field(None, description="Product category")

    class Config:
        json_schema_extra = {
            "example": {
                "sku": "PROD-001",
                "product_name": "Blue Dream 3.5g",
                "product_type": "cannabis",
                "quantity": 2,
                "unit_price": 35.00,
                "thc_percentage": 22.5,
                "cbd_percentage": 0.5
            }
        }


class UpdateOrderStatusRequest(BaseModel):
    """Request to update order status"""
    action: str = Field(..., description="Action to perform (confirm, start_processing, mark_ready, mark_out_for_delivery, complete, cancel)")
    reason: Optional[str] = Field(None, description="Reason for status change")
    cancelled_by: Optional[str] = Field(None, description="User ID who cancelled the order")

    class Config:
        json_schema_extra = {
            "example": {
                "action": "confirm",
                "reason": "Payment confirmed"
            }
        }


class SetDeliveryAddressRequest(BaseModel):
    """Request to set delivery address"""
    street: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    province: str = Field(..., description="Province/State")
    postal_code: str = Field(..., description="Postal code")
    country: str = Field(default="Canada", description="Country")
    unit: Optional[str] = Field(None, description="Unit/Apartment number")
    delivery_instructions: Optional[str] = Field(None, max_length=500, description="Delivery instructions")

    class Config:
        json_schema_extra = {
            "example": {
                "street": "123 Main St",
                "city": "Toronto",
                "province": "ON",
                "postal_code": "M5V 3A8",
                "country": "Canada",
                "delivery_instructions": "Ring doorbell"
            }
        }


# Order Mapper Functions
def map_order_line_to_dto(line) -> OrderLineDTO:
    """Convert OrderLine entity to DTO"""
    return OrderLineDTO(
        line_number=line.line_number,
        sku=line.sku,
        product_name=line.product_name,
        product_type=line.product_type,
        quantity=line.quantity,
        unit_price=float(line.unit_price),
        discount_amount=float(line.discount_amount),
        tax_amount=float(line.tax_amount),
        line_total=float(line.line_total),
        thc_percentage=float(line.thc_percentage) if line.thc_percentage else None,
        cbd_percentage=float(line.cbd_percentage) if line.cbd_percentage else None,
        product_category=line.product_category,
        fulfilled_quantity=line.fulfilled_quantity,
        is_fulfilled=line.is_fulfilled
    )


def map_order_to_dto(order) -> OrderDTO:
    """
    Convert Order aggregate to DTO

    Transforms rich domain model to clean API response
    """
    # Handle dict input (from database)
    if isinstance(order, dict):
        return OrderDTO(
            id=str(order.get("id", "")),
            order_number=order.get("order_number", ""),
            store_id=str(order.get("store_id", "")),
            customer_id=str(order.get("customer_id")) if order.get("customer_id") else None,
            status=order.get("status", "pending"),
            payment_status=order.get("payment_status", "pending"),
            fulfillment_status=order.get("fulfillment_status", "unfulfilled"),
            order_type=order.get("order_type", "online"),
            delivery_method=order.get("delivery_method", "pickup"),
            items=[],
            totals=OrderTotalsDTO(
                subtotal=float(order.get("subtotal", 0)),
                tax_amount=float(order.get("tax_amount", 0)),
                discount_amount=float(order.get("discount_amount", 0)),
                delivery_fee=float(order.get("delivery_fee", 0)),
                tip_amount=float(order.get("tip_amount", 0)),
                total_amount=float(order.get("total_amount", 0))
            ),
            payment_method=order.get("payment_method"),
            payment_transaction_id=str(order.get("payment_transaction_id")) if order.get("payment_transaction_id") else None,
            delivery_address=order.get("delivery_address"),
            customer_name=order.get("customer_name"),
            customer_email=order.get("customer_email"),
            customer_phone=order.get("customer_phone"),
            customer_notes=order.get("customer_notes"),
            created_at=order.get("created_at", datetime.utcnow()),
            updated_at=order.get("updated_at", datetime.utcnow()),
            confirmed_at=order.get("confirmed_at"),
            completed_at=order.get("completed_at"),
            cancelled_at=order.get("cancelled_at"),
            status_history=[],
            events=order.get("events", [])
        )

    # Handle domain object
    totals = order.get_totals()

    return OrderDTO(
        # Identifiers
        id=str(order.id),
        order_number=order.order_number,
        store_id=str(order.store_id),
        customer_id=str(order.customer_id) if order.customer_id else None,

        # Status
        status=order.status.value,
        payment_status=order.payment_status.value,
        fulfillment_status=order.fulfillment_status.value,

        # Order details
        order_type=order.order_type.value,
        delivery_method=order.delivery_method.value,

        # Line items
        items=[map_order_line_to_dto(item) for item in order.items],

        # Financial
        totals=OrderTotalsDTO(
            subtotal=float(totals.subtotal),
            tax_amount=float(totals.tax_amount),
            discount_amount=float(totals.discount_amount),
            delivery_fee=float(totals.delivery_fee),
            tip_amount=float(totals.tip_amount),
            total_amount=float(totals.total_amount)
        ),

        # Payment
        payment_method=order.payment_method,
        payment_transaction_id=str(order.payment_transaction_id) if order.payment_transaction_id else None,

        # Delivery/Pickup
        delivery_address=order.delivery_address,
        delivery_instructions=order.delivery_instructions,
        pickup_time=order.pickup_time,
        estimated_delivery_time=order.estimated_delivery_time,
        actual_delivery_time=order.actual_delivery_time,

        # Customer info
        customer_name=order.customer_name,
        customer_email=order.customer_email,
        customer_phone=order.customer_phone,

        # Notes
        customer_notes=order.customer_notes,
        internal_notes=order.internal_notes,
        cancellation_reason=order.cancellation_reason,

        # Status history
        status_history=[
            OrderStatusTransitionDTO(
                from_status=t.from_status.value,
                to_status=t.to_status.value,
                transitioned_at=t.transitioned_at,
                transitioned_by=t.transitioned_by,
                reason=t.reason
            )
            for t in order.status_history
        ],

        # Timestamps
        created_at=order.created_at,
        updated_at=order.updated_at,
        confirmed_at=order.confirmed_at,
        completed_at=order.completed_at,
        cancelled_at=order.cancelled_at,

        # Events (for debugging)
        events=[type(event).__name__ for event in order.domain_events] if hasattr(order, 'domain_events') else []
    )


def map_order_list_to_dto(
    orders: List,
    total: int,
    page: int = 1,
    page_size: int = 50
) -> OrderListDTO:
    """Convert list of orders to paginated DTO"""
    return OrderListDTO(
        orders=[map_order_to_dto(o) for o in orders],
        total=total,
        page=page,
        page_size=page_size
    )


# ============================================================================
# Inventory Management DTOs
# ============================================================================

class StockLevelDTO(BaseModel):
    """Stock level information DTO"""
    quantity_on_hand: int
    quantity_available: int
    quantity_reserved: int
    status: str  # in_stock, low_stock, out_of_stock
    needs_reorder: bool
    reorder_amount: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "quantity_on_hand": 100,
                "quantity_available": 85,
                "quantity_reserved": 15,
                "status": "in_stock",
                "needs_reorder": False,
                "reorder_amount": 0
            }
        }


class InventoryDTO(BaseModel):
    """Inventory aggregate DTO"""
    # Identifiers
    id: str
    store_id: str
    sku: str
    product_name: Optional[str] = None

    # Stock Levels
    quantity_on_hand: int
    quantity_available: int
    quantity_reserved: int
    stock_status: str

    # Pricing
    unit_cost: float
    retail_price: float
    retail_price_dynamic: Optional[float] = None
    override_price: Optional[float] = None
    effective_price: float
    margin_percentage: float

    # Stock Management
    reorder_point: int
    reorder_quantity: int
    min_stock_level: int
    max_stock_level: int
    needs_reorder: bool

    # GTIN Codes
    case_gtin: Optional[str] = None
    each_gtin: Optional[str] = None

    # Status
    is_available: bool
    is_overstocked: bool

    # Dates
    last_restock_date: Optional[datetime] = None
    last_sale_date: Optional[datetime] = None
    last_count_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Calculated values
    inventory_value_cost: float
    inventory_value_retail: float

    # Domain events
    events: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "store_id": "store-123",
                "sku": "PROD-001",
                "product_name": "Blue Dream 3.5g",
                "quantity_on_hand": 100,
                "quantity_available": 85,
                "quantity_reserved": 15,
                "stock_status": "in_stock",
                "unit_cost": 20.00,
                "retail_price": 35.00,
                "effective_price": 35.00,
                "margin_percentage": 42.86,
                "reorder_point": 20,
                "reorder_quantity": 50,
                "min_stock_level": 10,
                "max_stock_level": 200,
                "needs_reorder": False,
                "is_available": True,
                "is_overstocked": False,
                "inventory_value_cost": 2000.00,
                "inventory_value_retail": 3500.00,
                "created_at": "2025-10-09T12:00:00Z",
                "updated_at": "2025-10-09T12:00:00Z",
                "events": []
            }
        }


class InventoryListDTO(BaseModel):
    """List of inventory items"""
    items: List[InventoryDTO]
    total: int
    page: int = 1
    page_size: int = 50
    low_stock_count: int = 0
    out_of_stock_count: int = 0


# Inventory Request DTOs
class CreateInventoryRequest(BaseModel):
    """Request to create inventory item"""
    store_id: str = Field(..., description="Store ID")
    sku: str = Field(..., description="Product SKU")
    product_name: str = Field(..., description="Product name")
    initial_quantity: int = Field(default=0, ge=0, description="Initial stock quantity")
    unit_cost: float = Field(default=0.0, ge=0, description="Unit cost")
    retail_price: float = Field(default=0.0, ge=0, description="Retail price")
    reorder_point: int = Field(default=10, ge=0, description="Reorder point threshold")
    reorder_quantity: int = Field(default=50, gt=0, description="Reorder quantity")
    min_stock_level: int = Field(default=5, ge=0, description="Minimum stock level")
    max_stock_level: int = Field(default=100, gt=0, description="Maximum stock level")

    class Config:
        json_schema_extra = {
            "example": {
                "store_id": "store-123",
                "sku": "PROD-001",
                "product_name": "Blue Dream 3.5g",
                "initial_quantity": 100,
                "unit_cost": 20.00,
                "retail_price": 35.00,
                "reorder_point": 20,
                "reorder_quantity": 50
            }
        }


class AdjustStockRequest(BaseModel):
    """Request to adjust stock levels"""
    adjustment: int = Field(..., description="Stock adjustment (+/-)")
    reason: str = Field(..., min_length=3, max_length=200, description="Reason for adjustment")

    class Config:
        json_schema_extra = {
            "example": {
                "adjustment": -5,
                "reason": "Damaged products removed from inventory"
            }
        }


class ReceiveStockRequest(BaseModel):
    """Request to receive stock"""
    quantity: int = Field(..., gt=0, description="Quantity received")
    unit_cost: Optional[float] = Field(None, ge=0, description="Unit cost (for weighted average)")
    purchase_order_id: Optional[str] = Field(None, description="Purchase order ID")

    class Config:
        json_schema_extra = {
            "example": {
                "quantity": 50,
                "unit_cost": 19.50,
                "purchase_order_id": "PO-2025-001"
            }
        }


class ReserveStockRequest(BaseModel):
    """Request to reserve stock"""
    quantity: int = Field(..., gt=0, description="Quantity to reserve")
    reservation_id: str = Field(..., description="Reservation/Order ID")

    class Config:
        json_schema_extra = {
            "example": {
                "quantity": 2,
                "reservation_id": "order-123-456"
            }
        }


class UpdatePricingRequest(BaseModel):
    """Request to update pricing"""
    retail_price: Optional[float] = Field(None, ge=0, description="New retail price")
    unit_cost: Optional[float] = Field(None, ge=0, description="New unit cost")
    override_price: Optional[float] = Field(None, ge=0, description="Manual price override")
    dynamic_price: Optional[float] = Field(None, ge=0, description="Dynamic pricing value")

    class Config:
        json_schema_extra = {
            "example": {
                "retail_price": 36.00,
                "unit_cost": 19.00
            }
        }


class UpdateReorderLevelsRequest(BaseModel):
    """Request to update reorder levels"""
    reorder_point: Optional[int] = Field(None, ge=0, description="Reorder point")
    reorder_quantity: Optional[int] = Field(None, gt=0, description="Reorder quantity")
    min_stock: Optional[int] = Field(None, ge=0, description="Minimum stock level")
    max_stock: Optional[int] = Field(None, gt=0, description="Maximum stock level")

    class Config:
        json_schema_extra = {
            "example": {
                "reorder_point": 25,
                "reorder_quantity": 75,
                "max_stock": 250
            }
        }


class PerformCycleCountRequest(BaseModel):
    """Request to perform cycle count"""
    counted_quantity: int = Field(..., ge=0, description="Actual counted quantity")
    adjusted_by: str = Field(..., description="User ID performing count")
    notes: Optional[str] = Field(None, max_length=500, description="Count notes")

    class Config:
        json_schema_extra = {
            "example": {
                "counted_quantity": 98,
                "adjusted_by": "user-123",
                "notes": "Weekly cycle count"
            }
        }


# Inventory Mapper Functions
def map_inventory_to_dto(inventory) -> InventoryDTO:
    """
    Convert Inventory aggregate to DTO

    Transforms rich domain model to clean API response
    """
    # Handle dict input (from database)
    if isinstance(inventory, dict):
        return InventoryDTO(
            id=str(inventory.get("id", "")),
            store_id=str(inventory.get("store_id", "")),
            sku=inventory.get("sku", ""),
            product_name=inventory.get("product_name"),
            quantity_on_hand=inventory.get("quantity_on_hand", 0),
            quantity_available=inventory.get("quantity_available", 0),
            quantity_reserved=inventory.get("quantity_reserved", 0),
            stock_status=inventory.get("stock_status", "out_of_stock"),
            unit_cost=float(inventory.get("unit_cost", 0)),
            retail_price=float(inventory.get("retail_price", 0)),
            retail_price_dynamic=float(inventory.get("retail_price_dynamic")) if inventory.get("retail_price_dynamic") else None,
            override_price=float(inventory.get("override_price")) if inventory.get("override_price") else None,
            effective_price=float(inventory.get("effective_price", inventory.get("retail_price", 0))),
            margin_percentage=float(inventory.get("margin_percentage", 0)),
            reorder_point=inventory.get("reorder_point", 0),
            reorder_quantity=inventory.get("reorder_quantity", 0),
            min_stock_level=inventory.get("min_stock_level", 0),
            max_stock_level=inventory.get("max_stock_level", 100),
            needs_reorder=inventory.get("needs_reorder", False),
            case_gtin=inventory.get("case_gtin"),
            each_gtin=inventory.get("each_gtin"),
            is_available=inventory.get("is_available", True),
            is_overstocked=inventory.get("is_overstocked", False),
            last_restock_date=inventory.get("last_restock_date"),
            last_sale_date=inventory.get("last_sale_date"),
            last_count_date=inventory.get("last_count_date"),
            created_at=inventory.get("created_at", datetime.utcnow()),
            updated_at=inventory.get("updated_at", datetime.utcnow()),
            inventory_value_cost=float(inventory.get("inventory_value_cost", 0)),
            inventory_value_retail=float(inventory.get("inventory_value_retail", 0)),
            events=inventory.get("events", [])
        )

    # Handle domain object
    return InventoryDTO(
        # Identifiers
        id=str(inventory.id),
        store_id=str(inventory.store_id),
        sku=inventory.sku,
        product_name=inventory.product_name,

        # Stock Levels
        quantity_on_hand=inventory.quantity_on_hand,
        quantity_available=inventory.quantity_available,
        quantity_reserved=inventory.quantity_reserved,
        stock_status=inventory.get_stock_status().value,

        # Pricing
        unit_cost=float(inventory.unit_cost),
        retail_price=float(inventory.retail_price),
        retail_price_dynamic=float(inventory.retail_price_dynamic) if inventory.retail_price_dynamic else None,
        override_price=float(inventory.override_price) if inventory.override_price else None,
        effective_price=float(inventory.get_effective_price()),
        margin_percentage=float(inventory.get_margin()),

        # Stock Management
        reorder_point=inventory.reorder_point,
        reorder_quantity=inventory.reorder_quantity,
        min_stock_level=inventory.min_stock_level,
        max_stock_level=inventory.max_stock_level,
        needs_reorder=inventory.needs_reorder(),

        # GTIN
        case_gtin=inventory.case_gtin,
        each_gtin=inventory.each_gtin,

        # Status
        is_available=inventory.is_available,
        is_overstocked=inventory.is_overstocked(),

        # Dates
        last_restock_date=inventory.last_restock_date,
        last_sale_date=inventory.last_sale_date,
        last_count_date=inventory.last_count_date,
        created_at=inventory.created_at,
        updated_at=inventory.updated_at,

        # Calculated values
        inventory_value_cost=float(inventory.get_inventory_value()),
        inventory_value_retail=float(inventory.get_retail_value()),

        # Events (for debugging)
        events=[type(event).__name__ for event in inventory.domain_events] if hasattr(inventory, 'domain_events') else []
    )


def map_inventory_list_to_dto(
    items: List,
    total: int,
    page: int = 1,
    page_size: int = 50
) -> InventoryListDTO:
    """Convert list of inventory items to paginated DTO"""
    inventory_dtos = [map_inventory_to_dto(i) for i in items]
    
    # Calculate counts
    low_stock_count = sum(1 for i in inventory_dtos if i.stock_status == "low_stock")
    out_of_stock_count = sum(1 for i in inventory_dtos if i.stock_status == "out_of_stock")
    
    return InventoryListDTO(
        items=inventory_dtos,
        total=total,
        page=page,
        page_size=page_size,
        low_stock_count=low_stock_count,
        out_of_stock_count=out_of_stock_count
    )


# ============================================================================
# Product Catalog DTOs
# ============================================================================

class CannabinoidRangeDTO(BaseModel):
    """Cannabinoid content DTO"""
    thc_min: Optional[float] = None
    thc_max: Optional[float] = None
    cbd_min: Optional[float] = None
    cbd_max: Optional[float] = None
    total_cannabinoids: Optional[float] = None
    thc_range_display: str = "N/A"
    cbd_range_display: str = "N/A"
    potency_level: str = "Unknown"
    is_high_thc: bool = False
    is_high_cbd: bool = False
    is_balanced: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "thc_min": 20.0,
                "thc_max": 25.0,
                "cbd_min": 0.0,
                "cbd_max": 1.0,
                "thc_range_display": "20%-25%",
                "cbd_range_display": "0%-1%",
                "potency_level": "Very Strong",
                "is_high_thc": True,
                "is_high_cbd": False,
                "is_balanced": False
            }
        }


class TerpeneProfileDTO(BaseModel):
    """Terpene profile DTO"""
    primary_terpenes: List[str] = Field(default_factory=list)
    terpene_percentages: Optional[Dict[str, float]] = None
    aroma_notes: Optional[List[str]] = None
    flavor_notes: Optional[List[str]] = None
    dominant_terpene: Optional[str] = None
    common_effects: List[str] = Field(default_factory=list)
    display_string: str = "Unknown terpene profile"

    class Config:
        json_schema_extra = {
            "example": {
                "primary_terpenes": ["Limonene", "Myrcene", "Caryophyllene"],
                "dominant_terpene": "Limonene",
                "aroma_notes": ["Citrus", "Earthy", "Pine"],
                "flavor_notes": ["Lemon", "Spicy", "Herbal"],
                "common_effects": ["uplifting", "relaxing", "stress-relief"],
                "display_string": "Dominant: Limonene, Myrcene, Caryophyllene"
            }
        }


class ProductCategoryDTO(BaseModel):
    """Product category DTO"""
    name: str
    code: str
    type: str  # cannabis, accessories, merchandise, wellness
    description: Optional[str] = None
    parent_category: Optional[str] = None
    full_path: Optional[str] = None
    breadcrumb: Optional[List[str]] = None
    sort_order: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Dried Flower",
                "code": "dried_flower",
                "type": "cannabis",
                "description": "Dried cannabis flower",
                "parent_category": "Cannabis",
                "full_path": "cannabis/dried_flower",
                "sort_order": 1
            }
        }


class ProductAttributesDTO(BaseModel):
    """Product attributes DTO"""
    product_form: str  # dried_flower, pre_roll, oil, edible, etc.
    cannabinoid_range: CannabinoidRangeDTO
    terpene_profile: Optional[TerpeneProfileDTO] = None
    volume_ml: Optional[float] = None
    pieces: Optional[int] = None
    unit_of_measure: str = "g"
    allergens: Optional[List[str]] = None
    ingredients: Optional[List[str]] = None

    # Calculated/helper fields
    is_edible: bool = False
    is_inhalable: bool = False
    is_topical: bool = False
    requires_device: bool = False
    onset_time: str = "Varies"
    duration: str = "Varies"
    serving_size: str = "See package instructions"

    class Config:
        json_schema_extra = {
            "example": {
                "product_form": "dried_flower",
                "cannabinoid_range": {
                    "thc_min": 20.0,
                    "thc_max": 25.0,
                    "potency_level": "Very Strong"
                },
                "unit_of_measure": "g",
                "is_inhalable": True,
                "onset_time": "5-10 minutes",
                "duration": "1-3 hours",
                "serving_size": "0.25g (starter dose)"
            }
        }


class OcsProductDTO(BaseModel):
    """OCS Product aggregate DTO"""
    # Identifiers
    id: str
    ocs_variant_number: str  # Primary SKU

    # Product Information
    ocs_product_name: str
    product_name: str
    brand_name: str

    # Categorization
    category: Optional[ProductCategoryDTO] = None
    subcategory: Optional[str] = None

    # Cannabis Attributes
    plant_type: Optional[str] = None  # indica, sativa, hybrid, cbd, ruderalis
    product_form: Optional[str] = None
    product_attributes: Optional[ProductAttributesDTO] = None

    # Cannabinoid Content (shortcut fields for easy access)
    thc_min: Optional[float] = None
    thc_max: Optional[float] = None
    cbd_min: Optional[float] = None
    cbd_max: Optional[float] = None
    total_mg: Optional[float] = None

    # Terpenes
    terpene_profile: Optional[TerpeneProfileDTO] = None

    # Physical Attributes
    volume_ml: Optional[float] = None
    pieces: Optional[int] = None
    unit_of_measure: Optional[str] = None

    # Pricing
    price_per_unit: Optional[float] = None
    msrp_price: Optional[float] = None
    price_per_gram: Optional[float] = None

    # Product Details
    image_url: Optional[str] = None
    description: Optional[str] = None
    allergens: Optional[str] = None
    ingredients: Optional[str] = None

    # Status
    is_active: bool = True
    is_available: bool = True
    discontinued: bool = False
    discontinued_date: Optional[datetime] = None

    # Import Tracking
    last_import_date: Optional[datetime] = None
    import_source: Optional[str] = None

    # Calculated Fields
    potency_level: str = "Unknown"
    is_high_thc: bool = False
    is_high_cbd: bool = False
    is_balanced: bool = False

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Domain events
    events: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "ocs_variant_number": "OCS-12345",
                "ocs_product_name": "Blue Dream - Dried Flower",
                "product_name": "Blue Dream",
                "brand_name": "Broken Coast",
                "subcategory": "dried_flower",
                "plant_type": "hybrid",
                "product_form": "dried_flower",
                "thc_min": 20.0,
                "thc_max": 25.0,
                "cbd_min": 0.0,
                "cbd_max": 1.0,
                "unit_of_measure": "g",
                "price_per_unit": 35.00,
                "price_per_gram": 10.00,
                "image_url": "https://example.com/products/blue-dream.jpg",
                "potency_level": "Very Strong",
                "is_high_thc": True,
                "is_active": True,
                "is_available": True,
                "created_at": "2025-10-09T12:00:00Z",
                "updated_at": "2025-10-09T12:00:00Z"
            }
        }


class ProductListDTO(BaseModel):
    """List of products"""
    products: List[OcsProductDTO]
    total: int
    page: int = 1
    page_size: int = 50
    # Filter counts
    active_count: int = 0
    discontinued_count: int = 0
    high_thc_count: int = 0
    high_cbd_count: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "products": [],
                "total": 150,
                "page": 1,
                "page_size": 50,
                "active_count": 140,
                "discontinued_count": 10,
                "high_thc_count": 85,
                "high_cbd_count": 15
            }
        }


# Product Request DTOs
class ImportProductRequest(BaseModel):
    """Request to import product from OCS"""
    ocs_variant_number: str = Field(..., description="OCS variant number (SKU)")
    ocs_product_name: str = Field(..., description="Official OCS product name")
    product_name: str = Field(..., description="Display name")
    brand_name: str = Field(..., description="Brand name")

    # Optional fields
    subcategory: Optional[str] = Field(None, description="Product subcategory")
    plant_type: Optional[str] = Field(None, description="Plant type (indica/sativa/hybrid/cbd)")
    product_form: Optional[str] = Field(None, description="Product form (dried_flower, oil, etc.)")

    # Cannabinoid content
    thc_min: Optional[float] = Field(None, ge=0, le=100, description="Min THC percentage")
    thc_max: Optional[float] = Field(None, ge=0, le=100, description="Max THC percentage")
    cbd_min: Optional[float] = Field(None, ge=0, le=100, description="Min CBD percentage")
    cbd_max: Optional[float] = Field(None, ge=0, le=100, description="Max CBD percentage")
    total_mg: Optional[float] = Field(None, ge=0, description="Total cannabinoids in mg")

    # Physical attributes
    volume_ml: Optional[float] = Field(None, gt=0, description="Volume in ml")
    pieces: Optional[int] = Field(None, gt=0, description="Number of pieces")
    unit_of_measure: Optional[str] = Field(None, description="Unit of measure")

    # Pricing
    price_per_unit: Optional[float] = Field(None, ge=0, description="Price per unit")
    msrp_price: Optional[float] = Field(None, ge=0, description="MSRP")

    # Product details
    image_url: Optional[str] = Field(None, description="Image URL")
    description: Optional[str] = Field(None, max_length=2000, description="Product description")
    allergens: Optional[str] = Field(None, description="Allergen information")
    ingredients: Optional[str] = Field(None, description="Ingredients list")

    class Config:
        json_schema_extra = {
            "example": {
                "ocs_variant_number": "OCS-12345",
                "ocs_product_name": "Blue Dream - Dried Flower 3.5g",
                "product_name": "Blue Dream",
                "brand_name": "Broken Coast",
                "subcategory": "dried_flower",
                "plant_type": "hybrid",
                "thc_min": 20.0,
                "thc_max": 25.0,
                "cbd_min": 0.0,
                "cbd_max": 1.0,
                "price_per_unit": 35.00,
                "unit_of_measure": "g"
            }
        }


class UpdateProductRequest(BaseModel):
    """Request to update product information"""
    product_name: Optional[str] = Field(None, description="Display name")
    description: Optional[str] = Field(None, max_length=2000, description="Product description")
    image_url: Optional[str] = Field(None, description="Image URL")
    subcategory: Optional[str] = Field(None, description="Product subcategory")

    # Cannabinoid content
    thc_min: Optional[float] = Field(None, ge=0, le=100, description="Min THC percentage")
    thc_max: Optional[float] = Field(None, ge=0, le=100, description="Max THC percentage")
    cbd_min: Optional[float] = Field(None, ge=0, le=100, description="Min CBD percentage")
    cbd_max: Optional[float] = Field(None, ge=0, le=100, description="Max CBD percentage")

    # Pricing
    price_per_unit: Optional[float] = Field(None, ge=0, description="Price per unit")
    msrp_price: Optional[float] = Field(None, ge=0, description="MSRP")

    class Config:
        json_schema_extra = {
            "example": {
                "product_name": "Blue Dream Premium",
                "description": "Premium quality Blue Dream strain with high THC content",
                "thc_min": 22.0,
                "thc_max": 27.0,
                "price_per_unit": 38.00
            }
        }


class UpdateProductPricingRequest(BaseModel):
    """Request to update product pricing"""
    price_per_unit: Optional[float] = Field(None, ge=0, description="Price per unit")
    msrp_price: Optional[float] = Field(None, ge=0, description="MSRP")

    class Config:
        json_schema_extra = {
            "example": {
                "price_per_unit": 36.50,
                "msrp_price": 40.00
            }
        }


class SetTerpeneProfileRequest(BaseModel):
    """Request to set terpene profile"""
    primary_terpenes: List[str] = Field(..., min_items=1, max_items=10, description="Primary terpenes")
    terpene_percentages: Optional[Dict[str, float]] = Field(None, description="Terpene percentages")
    aroma_notes: Optional[List[str]] = Field(None, description="Aroma notes")
    flavor_notes: Optional[List[str]] = Field(None, description="Flavor notes")

    class Config:
        json_schema_extra = {
            "example": {
                "primary_terpenes": ["Limonene", "Myrcene", "Caryophyllene"],
                "terpene_percentages": {
                    "Limonene": 1.2,
                    "Myrcene": 0.8,
                    "Caryophyllene": 0.5
                },
                "aroma_notes": ["Citrus", "Earthy", "Pine"],
                "flavor_notes": ["Lemon", "Spicy", "Herbal"]
            }
        }


# Product Mapper Functions
def map_cannabinoid_range_to_dto(cannabinoid_range) -> CannabinoidRangeDTO:
    """Convert CannabinoidRange value object to DTO"""
    if not cannabinoid_range:
        return CannabinoidRangeDTO()

    return CannabinoidRangeDTO(
        thc_min=float(cannabinoid_range.thc_min) if cannabinoid_range.thc_min else None,
        thc_max=float(cannabinoid_range.thc_max) if cannabinoid_range.thc_max else None,
        cbd_min=float(cannabinoid_range.cbd_min) if cannabinoid_range.cbd_min else None,
        cbd_max=float(cannabinoid_range.cbd_max) if cannabinoid_range.cbd_max else None,
        total_cannabinoids=float(cannabinoid_range.total_cannabinoids) if cannabinoid_range.total_cannabinoids else None,
        thc_range_display=cannabinoid_range.get_thc_range_string(),
        cbd_range_display=cannabinoid_range.get_cbd_range_string(),
        potency_level=cannabinoid_range.get_potency_level(),
        is_high_thc=cannabinoid_range.is_high_thc(),
        is_high_cbd=cannabinoid_range.is_high_cbd(),
        is_balanced=cannabinoid_range.is_balanced()
    )


def map_terpene_profile_to_dto(terpene_profile) -> Optional[TerpeneProfileDTO]:
    """Convert TerpeneProfile value object to DTO"""
    if not terpene_profile:
        return None

    # Convert Decimal terpene percentages to float
    terpene_percentages = None
    if terpene_profile.terpene_percentages:
        terpene_percentages = {
            k: float(v) for k, v in terpene_profile.terpene_percentages.items()
        }

    return TerpeneProfileDTO(
        primary_terpenes=terpene_profile.primary_terpenes,
        terpene_percentages=terpene_percentages,
        aroma_notes=terpene_profile.aroma_notes,
        flavor_notes=terpene_profile.flavor_notes,
        dominant_terpene=terpene_profile.get_dominant_terpene(),
        common_effects=terpene_profile.get_common_effects(),
        display_string=terpene_profile.to_display_string()
    )


def map_product_to_dto(product) -> OcsProductDTO:
    """
    Convert OcsProduct aggregate to DTO

    Transforms rich domain model to clean API response
    """
    # Handle dict input (from database)
    if isinstance(product, dict):
        return OcsProductDTO(
            id=str(product.get("id", "")),
            ocs_variant_number=product.get("ocs_variant_number", ""),
            ocs_product_name=product.get("ocs_product_name", ""),
            product_name=product.get("product_name", ""),
            brand_name=product.get("brand_name", ""),
            subcategory=product.get("subcategory"),
            plant_type=product.get("plant_type"),
            product_form=product.get("product_form"),
            thc_min=float(product.get("thc_min")) if product.get("thc_min") else None,
            thc_max=float(product.get("thc_max")) if product.get("thc_max") else None,
            cbd_min=float(product.get("cbd_min")) if product.get("cbd_min") else None,
            cbd_max=float(product.get("cbd_max")) if product.get("cbd_max") else None,
            total_mg=float(product.get("total_mg")) if product.get("total_mg") else None,
            volume_ml=float(product.get("volume_ml")) if product.get("volume_ml") else None,
            pieces=product.get("pieces"),
            unit_of_measure=product.get("unit_of_measure"),
            price_per_unit=float(product.get("price_per_unit")) if product.get("price_per_unit") else None,
            msrp_price=float(product.get("msrp_price")) if product.get("msrp_price") else None,
            image_url=product.get("image_url"),
            description=product.get("description"),
            allergens=product.get("allergens"),
            ingredients=product.get("ingredients"),
            is_active=product.get("is_active", True),
            is_available=product.get("is_available", True),
            discontinued=product.get("discontinued", False),
            discontinued_date=product.get("discontinued_date"),
            last_import_date=product.get("last_import_date"),
            import_source=product.get("import_source"),
            created_at=product.get("created_at", datetime.utcnow()),
            updated_at=product.get("updated_at", datetime.utcnow()),
            events=product.get("events", [])
        )

    # Handle domain object
    return OcsProductDTO(
        # Identifiers
        id=str(product.id),
        ocs_variant_number=product.ocs_variant_number,

        # Product Information
        ocs_product_name=product.ocs_product_name,
        product_name=product.product_name,
        brand_name=product.brand_name,

        # Categorization
        subcategory=product.subcategory,

        # Cannabis Attributes
        plant_type=product.plant_type.to_display_string() if product.plant_type else None,
        product_form=product.product_form.value if product.product_form else None,
        product_attributes=None,  # Could be expanded if needed

        # Cannabinoid Content
        thc_min=float(product.thc_min) if product.thc_min else None,
        thc_max=float(product.thc_max) if product.thc_max else None,
        cbd_min=float(product.cbd_min) if product.cbd_min else None,
        cbd_max=float(product.cbd_max) if product.cbd_max else None,
        total_mg=float(product.total_mg) if product.total_mg else None,

        # Terpenes
        terpene_profile=map_terpene_profile_to_dto(product.terpene_profile),

        # Physical Attributes
        volume_ml=float(product.volume_ml) if product.volume_ml else None,
        pieces=product.pieces,
        unit_of_measure=product.unit_of_measure,

        # Pricing
        price_per_unit=float(product.price_per_unit) if product.price_per_unit else None,
        msrp_price=float(product.msrp_price) if product.msrp_price else None,
        price_per_gram=float(product.get_price_per_gram()) if product.get_price_per_gram() else None,

        # Product Details
        image_url=product.image_url,
        description=product.description,
        allergens=product.allergens,
        ingredients=product.ingredients,

        # Status
        is_active=product.is_active,
        is_available=product.is_available,
        discontinued=product.discontinued,
        discontinued_date=product.discontinued_date,

        # Import Tracking
        last_import_date=product.last_import_date,
        import_source=product.import_source,

        # Calculated Fields
        potency_level=product.get_potency_level(),
        is_high_thc=product.is_high_thc(),
        is_high_cbd=product.is_high_cbd(),
        is_balanced=product.is_balanced(),

        # Timestamps
        created_at=product.created_at,
        updated_at=product.updated_at,

        # Events (for debugging)
        events=[type(event).__name__ for event in product.domain_events] if hasattr(product, 'domain_events') else []
    )


def map_product_list_to_dto(
    products: List,
    total: int,
    page: int = 1,
    page_size: int = 50
) -> ProductListDTO:
    """Convert list of products to paginated DTO"""
    product_dtos = [map_product_to_dto(p) for p in products]

    # Calculate counts
    active_count = sum(1 for p in product_dtos if p.is_active)
    discontinued_count = sum(1 for p in product_dtos if p.discontinued)
    high_thc_count = sum(1 for p in product_dtos if p.is_high_thc)
    high_cbd_count = sum(1 for p in product_dtos if p.is_high_cbd)

    return ProductListDTO(
        products=product_dtos,
        total=total,
        page=page,
        page_size=page_size,
        active_count=active_count,
        discontinued_count=discontinued_count,
        high_thc_count=high_thc_count,
        high_cbd_count=high_cbd_count
    )


# ============================================================================
# Tenant Management DTOs
# ============================================================================

class GeoLocationDTO(BaseModel):
    """Geographic location DTO"""
    latitude: float
    longitude: float
    address_text: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "latitude": 43.6532,
                "longitude": -79.3832,
                "address_text": "123 Main St, Toronto, ON"
            }
        }


class OperatingHoursDTO(BaseModel):
    """Operating hours for a specific day"""
    open_time: Optional[str] = None  # "09:00"
    close_time: Optional[str] = None  # "21:00"
    is_open: bool = True
    is_24_hours: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "open_time": "09:00",
                "close_time": "21:00",
                "is_open": True,
                "is_24_hours": False
            }
        }


class TenantDTO(BaseModel):
    """Tenant aggregate DTO"""
    # Identifiers
    id: str
    code: str
    name: str

    # Subscription
    subscription_tier: str
    max_stores: int

    # Status
    status: str
    is_active: bool
    is_suspended: bool

    # Limits and features (based on subscription tier)
    ai_personality_limit_per_store: int
    can_add_unlimited_stores: bool

    # Contact Information
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    billing_email: Optional[str] = None

    # Settings
    settings: Dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime
    updated_at: datetime
    suspended_at: Optional[datetime] = None

    # Domain events
    events: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "code": "WG001",
                "name": "WeedGo Toronto",
                "subscription_tier": "professional_and_growing_business",
                "max_stores": 12,
                "status": "active",
                "is_active": True,
                "is_suspended": False,
                "ai_personality_limit_per_store": 3,
                "can_add_unlimited_stores": False,
                "contact_email": "contact@weedgo.ca",
                "contact_phone": "+1-416-555-0100",
                "created_at": "2025-10-09T12:00:00Z",
                "updated_at": "2025-10-09T12:00:00Z",
                "events": ["TenantCreated"]
            }
        }


class StoreDTO(BaseModel):
    """Store entity DTO"""
    # Identifiers
    id: str
    tenant_id: str
    province_territory_id: str
    store_code: str
    name: str

    # Contact Information
    address: Optional[Dict[str, Any]] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    location: Optional[GeoLocationDTO] = None

    # Operating Hours
    hours: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    timezone: str = "America/Toronto"

    # License & Compliance
    license_number: Optional[str] = None
    license_expiry: Optional[str] = None  # ISO date string
    is_license_valid: bool = False
    license_expiring_soon: bool = False

    # Tax Settings
    tax_rate: float = 13.0

    # Sales Channels
    delivery_enabled: bool = True
    delivery_radius_km: int = 10
    pickup_enabled: bool = True
    kiosk_enabled: bool = False
    pos_enabled: bool = True
    ecommerce_enabled: bool = True
    at_least_one_channel_enabled: bool = True

    # Status
    status: str
    is_active: bool
    is_operational: bool  # Active + valid license

    # Settings
    settings: Dict[str, Any] = Field(default_factory=dict)
    pos_integration: Dict[str, Any] = Field(default_factory=dict)
    pos_payment_terminal_settings: Dict[str, Any] = Field(default_factory=dict)
    seo_config: Dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Domain events
    events: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "tenant_id": "tenant-123",
                "province_territory_id": "prov-ON",
                "store_code": "WG-TOR-001",
                "name": "WeedGo Toronto Downtown",
                "address": {
                    "street": "123 Main St",
                    "city": "Toronto",
                    "province": "ON",
                    "postal_code": "M5V 3A8",
                    "country": "Canada"
                },
                "phone": "+1-416-555-0123",
                "email": "downtown@weedgo.ca",
                "location": {
                    "latitude": 43.6532,
                    "longitude": -79.3832
                },
                "hours": {
                    "monday": {"open_time": "09:00", "close_time": "21:00", "is_open": True},
                    "tuesday": {"open_time": "09:00", "close_time": "21:00", "is_open": True}
                },
                "license_number": "LIC-ON-12345",
                "license_expiry": "2026-12-31",
                "is_license_valid": True,
                "tax_rate": 13.0,
                "delivery_enabled": True,
                "delivery_radius_km": 10,
                "pickup_enabled": True,
                "pos_enabled": True,
                "ecommerce_enabled": True,
                "status": "active",
                "is_active": True,
                "is_operational": True,
                "created_at": "2025-10-09T12:00:00Z",
                "updated_at": "2025-10-09T12:00:00Z",
                "events": ["StoreCreated"]
            }
        }


class StoreContextDTO(BaseModel):
    """Store context value object DTO"""
    user_id: str
    current_store_id: Optional[str] = None
    current_tenant_id: Optional[str] = None
    store_name: Optional[str] = None
    tenant_name: Optional[str] = None
    has_store_selected: bool = False
    has_tenant_selected: bool = False
    is_multi_store_context: bool = False
    display_text: str = "No Store Selected"

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-123",
                "current_store_id": "store-456",
                "current_tenant_id": "tenant-789",
                "store_name": "WeedGo Toronto Downtown",
                "tenant_name": "WeedGo Toronto",
                "has_store_selected": True,
                "has_tenant_selected": True,
                "is_multi_store_context": False,
                "display_text": "WeedGo Toronto Downtown (WeedGo Toronto)"
            }
        }


class TenantListDTO(BaseModel):
    """List of tenants"""
    tenants: List[TenantDTO]
    total: int
    page: int = 1
    page_size: int = 50
    active_count: int = 0
    suspended_count: int = 0


class StoreListDTO(BaseModel):
    """List of stores"""
    stores: List[StoreDTO]
    total: int
    page: int = 1
    page_size: int = 50
    active_count: int = 0
    inactive_count: int = 0
    license_expiring_count: int = 0


# Tenant Request DTOs
class CreateTenantRequest(BaseModel):
    """Request to create a new tenant"""
    name: str = Field(..., min_length=3, max_length=200, description="Tenant name")
    code: str = Field(..., min_length=2, max_length=50, description="Unique tenant code")
    subscription_tier: str = Field(
        default="community_and_new_business",
        description="Subscription tier (community_and_new_business, small_business, professional_and_growing_business, enterprise)"
    )
    contact_email: Optional[str] = Field(None, description="Contact email")
    contact_phone: Optional[str] = Field(None, description="Contact phone")
    billing_email: Optional[str] = Field(None, description="Billing email")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "WeedGo Toronto",
                "code": "WG001",
                "subscription_tier": "professional_and_growing_business",
                "contact_email": "contact@weedgo.ca",
                "contact_phone": "+1-416-555-0100",
                "billing_email": "billing@weedgo.ca"
            }
        }


class UpgradeSubscriptionRequest(BaseModel):
    """Request to upgrade subscription tier"""
    new_tier: str = Field(
        ...,
        description="New subscription tier (small_business, professional_and_growing_business, enterprise)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "new_tier": "enterprise"
            }
        }


class SuspendTenantRequest(BaseModel):
    """Request to suspend tenant"""
    reason: str = Field(..., min_length=10, max_length=500, description="Reason for suspension")

    class Config:
        json_schema_extra = {
            "example": {
                "reason": "Non-payment of subscription fees"
            }
        }


# Store Request DTOs
class CreateStoreRequest(BaseModel):
    """Request to create a new store"""
    tenant_id: str = Field(..., description="Tenant ID")
    province_territory_id: str = Field(..., description="Province/Territory ID")
    store_code: str = Field(..., min_length=2, max_length=50, description="Unique store code")
    name: str = Field(..., min_length=3, max_length=200, description="Store name")

    # Contact
    phone: Optional[str] = Field(None, description="Store phone")
    email: Optional[str] = Field(None, description="Store email")

    # Address
    street: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, description="City")
    province: Optional[str] = Field(None, description="Province")
    postal_code: Optional[str] = Field(None, description="Postal code")
    country: str = Field(default="Canada", description="Country")

    # License
    license_number: Optional[str] = Field(None, description="License number")
    license_expiry: Optional[str] = Field(None, description="License expiry date (YYYY-MM-DD)")

    # Tax
    tax_rate: float = Field(default=13.0, ge=0, le=100, description="Tax rate percentage")

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "tenant-123",
                "province_territory_id": "prov-ON",
                "store_code": "WG-TOR-001",
                "name": "WeedGo Toronto Downtown",
                "phone": "+1-416-555-0123",
                "email": "downtown@weedgo.ca",
                "street": "123 Main St",
                "city": "Toronto",
                "province": "ON",
                "postal_code": "M5V 3A8",
                "license_number": "LIC-ON-12345",
                "license_expiry": "2026-12-31",
                "tax_rate": 13.0
            }
        }


class UpdateStoreLicenseRequest(BaseModel):
    """Request to update store license"""
    license_number: str = Field(..., description="License number")
    license_expiry: str = Field(..., description="License expiry date (YYYY-MM-DD)")

    class Config:
        json_schema_extra = {
            "example": {
                "license_number": "LIC-ON-12345-RENEWED",
                "license_expiry": "2027-12-31"
            }
        }


class UpdateStoreChannelsRequest(BaseModel):
    """Request to update store sales channels"""
    delivery_enabled: Optional[bool] = Field(None, description="Enable delivery")
    delivery_radius_km: Optional[int] = Field(None, ge=1, le=100, description="Delivery radius in km")
    pickup_enabled: Optional[bool] = Field(None, description="Enable pickup")
    kiosk_enabled: Optional[bool] = Field(None, description="Enable kiosk")
    pos_enabled: Optional[bool] = Field(None, description="Enable POS")
    ecommerce_enabled: Optional[bool] = Field(None, description="Enable e-commerce")

    class Config:
        json_schema_extra = {
            "example": {
                "delivery_enabled": True,
                "delivery_radius_km": 15,
                "pickup_enabled": True,
                "ecommerce_enabled": True
            }
        }


class UpdateStoreHoursRequest(BaseModel):
    """Request to update store operating hours"""
    hours: Dict[str, Dict[str, Any]] = Field(..., description="Operating hours by day of week")

    class Config:
        json_schema_extra = {
            "example": {
                "hours": {
                    "monday": {"open_time": "09:00", "close_time": "21:00", "is_open": True},
                    "tuesday": {"open_time": "09:00", "close_time": "21:00", "is_open": True},
                    "wednesday": {"open_time": "09:00", "close_time": "21:00", "is_open": True},
                    "thursday": {"open_time": "09:00", "close_time": "22:00", "is_open": True},
                    "friday": {"open_time": "09:00", "close_time": "22:00", "is_open": True},
                    "saturday": {"open_time": "10:00", "close_time": "22:00", "is_open": True},
                    "sunday": {"open_time": "11:00", "close_time": "20:00", "is_open": True}
                }
            }
        }


class UpdateStoreLocationRequest(BaseModel):
    """Request to update store geographic location"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")
    address_text: Optional[str] = Field(None, description="Human-readable address")

    class Config:
        json_schema_extra = {
            "example": {
                "latitude": 43.6532,
                "longitude": -79.3832,
                "address_text": "123 Main St, Toronto, ON M5V 3A8"
            }
        }


# Tenant Mapper Functions
def map_tenant_to_dto(tenant) -> TenantDTO:
    """
    Convert Tenant aggregate to DTO

    Transforms rich domain model to clean API response
    """
    # Handle dict input (from database)
    if isinstance(tenant, dict):
        return TenantDTO(
            id=str(tenant.get("id", "")),
            code=tenant.get("code", ""),
            name=tenant.get("name", ""),
            subscription_tier=tenant.get("subscription_tier", "community_and_new_business"),
            max_stores=tenant.get("max_stores", 1),
            status=tenant.get("status", "active"),
            is_active=tenant.get("status") == "active",
            is_suspended=tenant.get("status") == "suspended",
            ai_personality_limit_per_store=tenant.get("ai_personality_limit_per_store", 1),
            can_add_unlimited_stores=tenant.get("subscription_tier") == "enterprise",
            contact_email=tenant.get("contact_email"),
            contact_phone=tenant.get("contact_phone"),
            billing_email=tenant.get("billing_email"),
            settings=tenant.get("settings", {}),
            created_at=tenant.get("created_at", datetime.utcnow()),
            updated_at=tenant.get("updated_at", datetime.utcnow()),
            suspended_at=tenant.get("suspended_at"),
            events=tenant.get("events", [])
        )

    # Handle domain object
    return TenantDTO(
        # Identifiers
        id=str(tenant.id),
        code=tenant.code,
        name=tenant.name,

        # Subscription
        subscription_tier=tenant.subscription_tier.value,
        max_stores=tenant.max_stores,

        # Status
        status=tenant.status.value,
        is_active=tenant.is_active(),
        is_suspended=tenant.is_suspended(),

        # Limits
        ai_personality_limit_per_store=tenant.get_ai_personality_limit(),
        can_add_unlimited_stores=tenant.can_add_unlimited_stores(),

        # Contact
        contact_email=tenant.contact_email,
        contact_phone=tenant.contact_phone,
        billing_email=tenant.billing_email,

        # Settings
        settings=tenant.settings,

        # Timestamps
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
        suspended_at=tenant.suspended_at,

        # Events (for debugging)
        events=[type(event).__name__ for event in tenant.domain_events] if hasattr(tenant, 'domain_events') else []
    )


def map_store_to_dto(store) -> StoreDTO:
    """
    Convert Store entity to DTO

    Transforms rich domain model to clean API response
    """
    # Handle dict input (from database)
    if isinstance(store, dict):
        from datetime import date

        license_expiry = store.get("license_expiry")
        is_license_valid = False
        license_expiring_soon = False

        if license_expiry:
            if isinstance(license_expiry, str):
                from datetime import datetime
                license_expiry_date = datetime.fromisoformat(license_expiry).date()
            else:
                license_expiry_date = license_expiry

            is_license_valid = license_expiry_date > date.today()
            days_until_expiry = (license_expiry_date - date.today()).days
            license_expiring_soon = 0 < days_until_expiry <= 30

        return StoreDTO(
            id=str(store.get("id", "")),
            tenant_id=str(store.get("tenant_id", "")),
            province_territory_id=str(store.get("province_territory_id", "")),
            store_code=store.get("store_code", ""),
            name=store.get("name", ""),
            address=store.get("address"),
            phone=store.get("phone"),
            email=store.get("email"),
            location=None,  # Would need to parse from DB
            hours=store.get("hours", {}),
            timezone=store.get("timezone", "America/Toronto"),
            license_number=store.get("license_number"),
            license_expiry=license_expiry.isoformat() if license_expiry else None,
            is_license_valid=is_license_valid,
            license_expiring_soon=license_expiring_soon,
            tax_rate=float(store.get("tax_rate", 13.0)),
            delivery_enabled=store.get("delivery_enabled", True),
            delivery_radius_km=store.get("delivery_radius_km", 10),
            pickup_enabled=store.get("pickup_enabled", True),
            kiosk_enabled=store.get("kiosk_enabled", False),
            pos_enabled=store.get("pos_enabled", True),
            ecommerce_enabled=store.get("ecommerce_enabled", True),
            at_least_one_channel_enabled=any([
                store.get("delivery_enabled"),
                store.get("pickup_enabled"),
                store.get("kiosk_enabled"),
                store.get("pos_enabled"),
                store.get("ecommerce_enabled")
            ]),
            status=store.get("status", "active"),
            is_active=store.get("status") == "active",
            is_operational=store.get("status") == "active" and is_license_valid,
            settings=store.get("settings", {}),
            pos_integration=store.get("pos_integration", {}),
            pos_payment_terminal_settings=store.get("pos_payment_terminal_settings", {}),
            seo_config=store.get("seo_config", {}),
            created_at=store.get("created_at", datetime.utcnow()),
            updated_at=store.get("updated_at", datetime.utcnow()),
            events=store.get("events", [])
        )

    # Handle domain object
    location_dto = None
    if store.location:
        location_dto = GeoLocationDTO(
            latitude=float(store.location.latitude),
            longitude=float(store.location.longitude),
            address_text=store.location.address_text if hasattr(store.location, 'address_text') else None
        )

    return StoreDTO(
        # Identifiers
        id=str(store.id),
        tenant_id=str(store.tenant_id),
        province_territory_id=str(store.province_territory_id),
        store_code=store.store_code,
        name=store.name,

        # Contact
        address=store.address.to_dict() if store.address and hasattr(store.address, 'to_dict') else None,
        phone=store.phone,
        email=store.email,
        location=location_dto,

        # Operating Hours
        hours=store.hours,
        timezone=store.timezone,

        # License
        license_number=store.license_number,
        license_expiry=store.license_expiry.isoformat() if store.license_expiry else None,
        is_license_valid=store.is_license_valid(),
        license_expiring_soon=store.is_license_expiring_soon() if hasattr(store, 'is_license_expiring_soon') else False,

        # Tax
        tax_rate=float(store.tax_rate),

        # Channels
        delivery_enabled=store.delivery_enabled,
        delivery_radius_km=store.delivery_radius_km,
        pickup_enabled=store.pickup_enabled,
        kiosk_enabled=store.kiosk_enabled,
        pos_enabled=store.pos_enabled,
        ecommerce_enabled=store.ecommerce_enabled,
        at_least_one_channel_enabled=any([
            store.delivery_enabled,
            store.pickup_enabled,
            store.kiosk_enabled,
            store.pos_enabled,
            store.ecommerce_enabled
        ]),

        # Status
        status=store.status.value,
        is_active=store.status.value == "active",
        is_operational=store.is_operational(),

        # Settings
        settings=store.settings,
        pos_integration=store.pos_integration,
        pos_payment_terminal_settings=store.pos_payment_terminal_settings,
        seo_config=store.seo_config,

        # Timestamps
        created_at=store.created_at,
        updated_at=store.updated_at,

        # Events (for debugging)
        events=[type(event).__name__ for event in store.domain_events] if hasattr(store, 'domain_events') else []
    )


def map_store_context_to_dto(store_context) -> StoreContextDTO:
    """
    Convert StoreContext value object to DTO
    """
    # Handle dict input
    if isinstance(store_context, dict):
        return StoreContextDTO(
            user_id=str(store_context.get("user_id", "")),
            current_store_id=str(store_context.get("current_store_id")) if store_context.get("current_store_id") else None,
            current_tenant_id=str(store_context.get("current_tenant_id")) if store_context.get("current_tenant_id") else None,
            store_name=store_context.get("store_name"),
            tenant_name=store_context.get("tenant_name"),
            has_store_selected=store_context.get("has_store_selected", False),
            has_tenant_selected=store_context.get("has_tenant_selected", False),
            is_multi_store_context=store_context.get("is_multi_store_context", False),
            display_text=store_context.get("display_text", "No Store Selected")
        )

    # Handle domain object
    return StoreContextDTO(
        user_id=str(store_context.user_id),
        current_store_id=str(store_context.current_store_id) if store_context.current_store_id else None,
        current_tenant_id=str(store_context.current_tenant_id) if store_context.current_tenant_id else None,
        store_name=store_context.store_name,
        tenant_name=store_context.tenant_name,
        has_store_selected=store_context.has_store_selected(),
        has_tenant_selected=store_context.has_tenant_selected(),
        is_multi_store_context=store_context.is_multi_store_context(),
        display_text=store_context.get_display_text()
    )


def map_tenant_list_to_dto(
    tenants: List,
    total: int,
    page: int = 1,
    page_size: int = 50
) -> TenantListDTO:
    """Convert list of tenants to paginated DTO"""
    tenant_dtos = [map_tenant_to_dto(t) for t in tenants]

    # Calculate counts
    active_count = sum(1 for t in tenant_dtos if t.is_active)
    suspended_count = sum(1 for t in tenant_dtos if t.is_suspended)

    return TenantListDTO(
        tenants=tenant_dtos,
        total=total,
        page=page,
        page_size=page_size,
        active_count=active_count,
        suspended_count=suspended_count
    )


def map_store_list_to_dto(
    stores: List,
    total: int,
    page: int = 1,
    page_size: int = 50
) -> StoreListDTO:
    """Convert list of stores to paginated DTO"""
    store_dtos = [map_store_to_dto(s) for s in stores]

    # Calculate counts
    active_count = sum(1 for s in store_dtos if s.is_active)
    inactive_count = sum(1 for s in store_dtos if not s.is_active)
    license_expiring_count = sum(1 for s in store_dtos if s.license_expiring_soon)

    return StoreListDTO(
        stores=store_dtos,
        total=total,
        page=page,
        page_size=page_size,
        active_count=active_count,
        inactive_count=inactive_count,
        license_expiring_count=license_expiring_count
    )


# ============================================================================
# Pricing & Promotions DTOs
# ============================================================================

class PricingTierDTO(BaseModel):
    """Pricing tier DTO for bulk discounts"""
    min_quantity: float
    max_quantity: Optional[float] = None
    discount_percentage: Optional[float] = None
    fixed_price: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "min_quantity": 10.0,
                "max_quantity": 50.0,
                "discount_percentage": 10.0
            }
        }


class BulkDiscountRuleDTO(BaseModel):
    """Bulk discount rule DTO"""
    product_sku: str
    base_price: float
    tiers: List[PricingTierDTO] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "product_sku": "PROD-001",
                "base_price": 35.00,
                "tiers": [
                    {"min_quantity": 10.0, "max_quantity": 25.0, "discount_percentage": 10.0},
                    {"min_quantity": 25.0, "max_quantity": 50.0, "discount_percentage": 15.0},
                    {"min_quantity": 50.0, "discount_percentage": 20.0}
                ]
            }
        }


class PriceScheduleDTO(BaseModel):
    """Time-based price schedule DTO"""
    name: str
    discount_type: str  # percentage, fixed_amount
    discount_value: float
    start_time: datetime
    end_time: datetime
    days_of_week: Optional[List[int]] = None  # 0=Monday, 6=Sunday
    start_hour: Optional[int] = None  # 0-23
    end_hour: Optional[int] = None  # 0-23
    is_recurring: bool = False
    is_active_now: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Happy Hour Special",
                "discount_type": "percentage",
                "discount_value": 15.0,
                "start_time": "2025-10-09T15:00:00Z",
                "end_time": "2025-12-31T18:00:00Z",
                "days_of_week": [0, 1, 2, 3, 4],  # Monday-Friday
                "start_hour": 15,
                "end_hour": 18,
                "is_recurring": True,
                "is_active_now": False
            }
        }


class ProductPriceDTO(BaseModel):
    """Product price entity DTO"""
    product_sku: str
    product_name: str
    cost_price: float
    base_price: float
    markup_percentage: float
    current_price: float  # After schedules/overrides
    bulk_discount_rule: Optional[BulkDiscountRuleDTO] = None
    price_schedules: List[PriceScheduleDTO] = Field(default_factory=list)
    active_schedule: Optional[str] = None  # Name of currently active schedule

    class Config:
        json_schema_extra = {
            "example": {
                "product_sku": "PROD-001",
                "product_name": "Blue Dream 3.5g",
                "cost_price": 20.00,
                "base_price": 35.00,
                "markup_percentage": 75.0,
                "current_price": 35.00,
                "bulk_discount_rule": {
                    "product_sku": "PROD-001",
                    "base_price": 35.00,
                    "tiers": [
                        {"min_quantity": 10.0, "discount_percentage": 10.0}
                    ]
                },
                "price_schedules": [],
                "active_schedule": None
            }
        }


class PricingRuleDTO(BaseModel):
    """Pricing rule aggregate DTO"""
    # Identifiers
    id: str
    store_id: str
    tenant_id: str
    rule_name: str

    # Pricing Strategy
    pricing_strategy: str  # cost_plus, competitive, value_based, dynamic, tiered
    default_markup_percentage: float

    # Product Prices
    product_prices: List[ProductPriceDTO] = Field(default_factory=list)

    # Status
    is_active: bool = True

    # Timestamps
    created_at: datetime
    updated_at: datetime
    activated_at: Optional[datetime] = None

    # Domain events
    events: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "store_id": "store-123",
                "tenant_id": "tenant-456",
                "rule_name": "Standard Cannabis Pricing",
                "pricing_strategy": "cost_plus",
                "default_markup_percentage": 50.0,
                "product_prices": [
                    {
                        "product_sku": "PROD-001",
                        "product_name": "Blue Dream 3.5g",
                        "cost_price": 20.00,
                        "base_price": 35.00,
                        "markup_percentage": 75.0,
                        "current_price": 35.00
                    }
                ],
                "is_active": True,
                "created_at": "2025-10-09T12:00:00Z",
                "updated_at": "2025-10-09T12:00:00Z",
                "events": ["PricingRuleCreated", "PricingRuleActivated"]
            }
        }


class PricingRuleListDTO(BaseModel):
    """List of pricing rules"""
    rules: List[PricingRuleDTO]
    total: int
    page: int = 1
    page_size: int = 50
    active_count: int = 0
    inactive_count: int = 0


class DiscountCodeDTO(BaseModel):
    """Discount code entity DTO"""
    code: str
    max_uses: Optional[int] = None
    current_uses: int = 0
    customer_segment: str  # all, new_customer, returning, vip, medical, recreational
    specific_customer_id: Optional[str] = None
    is_active: bool = True
    remaining_uses: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "code": "WELCOME25",
                "max_uses": 100,
                "current_uses": 23,
                "customer_segment": "new_customer",
                "is_active": True,
                "remaining_uses": 77
            }
        }


class DiscountConditionDTO(BaseModel):
    """Discount condition DTO"""
    min_purchase_amount: Optional[float] = None
    min_quantity: Optional[int] = None
    required_customer_segment: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "min_purchase_amount": 50.00,
                "min_quantity": 2,
                "required_customer_segment": "vip",
                "valid_from": "2025-10-09T00:00:00Z",
                "valid_until": "2025-12-31T23:59:59Z"
            }
        }


class PromotionDTO(BaseModel):
    """Promotion aggregate DTO"""
    # Identifiers
    id: str
    store_id: str
    tenant_id: str
    promotion_name: str
    description: Optional[str] = None

    # Status
    status: str  # draft, scheduled, active, paused, expired, cancelled

    # Discount Configuration
    discount_type: str  # percentage, fixed_amount, bogo, bulk_discount, bundle
    discount_value: float

    # BOGO Configuration (if applicable)
    bogo_buy_quantity: Optional[int] = None
    bogo_get_quantity: Optional[int] = None

    # Applicability
    applicable_to: str  # all_products, specific_skus, category, brand, type
    specific_skus: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    brand: Optional[str] = None

    # Customer Targeting
    customer_segment: str  # all, new_customer, returning, vip, medical, recreational

    # Discount Codes
    discount_codes: List[DiscountCodeDTO] = Field(default_factory=list)
    requires_code: bool = False

    # Stacking
    can_stack: bool = False
    priority: int = 0  # Higher priority promotions apply first

    # Date Range
    start_date: datetime
    end_date: datetime
    is_active_now: bool = False

    # Conditions
    conditions: Optional[DiscountConditionDTO] = None

    # Usage Statistics
    total_uses: int = 0
    total_discount_amount: float = 0.0

    # Timestamps
    created_at: datetime
    updated_at: datetime
    activated_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None

    # Domain events
    events: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "store_id": "store-123",
                "tenant_id": "tenant-456",
                "promotion_name": "Black Friday 2025",
                "description": "25% off all products for Black Friday",
                "status": "active",
                "discount_type": "percentage",
                "discount_value": 25.0,
                "applicable_to": "all_products",
                "customer_segment": "all",
                "requires_code": False,
                "can_stack": False,
                "priority": 10,
                "start_date": "2025-11-29T00:00:00Z",
                "end_date": "2025-11-30T23:59:59Z",
                "is_active_now": False,
                "total_uses": 0,
                "total_discount_amount": 0.0,
                "created_at": "2025-10-09T12:00:00Z",
                "updated_at": "2025-10-09T12:00:00Z",
                "events": ["PromotionCreated"]
            }
        }


class PromotionListDTO(BaseModel):
    """List of promotions"""
    promotions: List[PromotionDTO]
    total: int
    page: int = 1
    page_size: int = 50
    active_count: int = 0
    scheduled_count: int = 0
    expired_count: int = 0


# Pricing & Promotions Request DTOs
class CreatePricingRuleRequest(BaseModel):
    """Request to create a pricing rule"""
    store_id: str = Field(..., description="Store ID")
    rule_name: str = Field(..., min_length=3, max_length=200, description="Rule name")
    pricing_strategy: str = Field(
        default="cost_plus",
        description="Pricing strategy (cost_plus, competitive, value_based, dynamic, tiered)"
    )
    default_markup_percentage: float = Field(
        default=50.0,
        ge=0,
        le=1000,
        description="Default markup percentage"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "store_id": "store-123",
                "rule_name": "Standard Cannabis Pricing",
                "pricing_strategy": "cost_plus",
                "default_markup_percentage": 50.0
            }
        }


class AddProductPriceRequest(BaseModel):
    """Request to add product price to pricing rule"""
    product_sku: str = Field(..., description="Product SKU")
    product_name: str = Field(..., description="Product name")
    cost_price: float = Field(..., gt=0, description="Cost price")
    markup_percentage: Optional[float] = Field(None, ge=0, le=1000, description="Markup percentage (uses rule default if not provided)")

    class Config:
        json_schema_extra = {
            "example": {
                "product_sku": "PROD-001",
                "product_name": "Blue Dream 3.5g",
                "cost_price": 20.00,
                "markup_percentage": 75.0
            }
        }


class UpdateProductPriceRequest(BaseModel):
    """Request to update product price in pricing rule"""
    cost_price: Optional[float] = Field(None, gt=0, description="New cost price")
    markup_percentage: Optional[float] = Field(None, ge=0, le=1000, description="New markup percentage")

    class Config:
        json_schema_extra = {
            "example": {
                "cost_price": 19.00,
                "markup_percentage": 80.0
            }
        }


class AddBulkDiscountRequest(BaseModel):
    """Request to add bulk discount rule"""
    tiers: List[Dict[str, Any]] = Field(..., min_items=1, description="Discount tiers")

    class Config:
        json_schema_extra = {
            "example": {
                "tiers": [
                    {
                        "min_quantity": 10.0,
                        "max_quantity": 25.0,
                        "discount_percentage": 10.0
                    },
                    {
                        "min_quantity": 25.0,
                        "max_quantity": 50.0,
                        "discount_percentage": 15.0
                    },
                    {
                        "min_quantity": 50.0,
                        "discount_percentage": 20.0
                    }
                ]
            }
        }


class AddPriceScheduleRequest(BaseModel):
    """Request to add time-based price schedule"""
    name: str = Field(..., min_length=3, max_length=100, description="Schedule name")
    discount_type: str = Field(..., description="Discount type (percentage, fixed_amount)")
    discount_value: float = Field(..., gt=0, description="Discount value")
    start_time: datetime = Field(..., description="Schedule start time")
    end_time: datetime = Field(..., description="Schedule end time")
    days_of_week: Optional[List[int]] = Field(None, description="Days of week (0=Monday, 6=Sunday)")
    start_hour: Optional[int] = Field(None, ge=0, le=23, description="Start hour (0-23)")
    end_hour: Optional[int] = Field(None, ge=0, le=23, description="End hour (0-23)")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Happy Hour Special",
                "discount_type": "percentage",
                "discount_value": 15.0,
                "start_time": "2025-10-09T15:00:00Z",
                "end_time": "2025-12-31T18:00:00Z",
                "days_of_week": [0, 1, 2, 3, 4],
                "start_hour": 15,
                "end_hour": 18
            }
        }


class CreatePromotionRequest(BaseModel):
    """Request to create a promotion"""
    store_id: str = Field(..., description="Store ID")
    promotion_name: str = Field(..., min_length=3, max_length=200, description="Promotion name")
    description: Optional[str] = Field(None, max_length=1000, description="Promotion description")
    discount_type: str = Field(..., description="Discount type (percentage, fixed_amount, bogo, bulk_discount, bundle)")
    discount_value: float = Field(..., gt=0, description="Discount value")

    # BOGO fields
    bogo_buy_quantity: Optional[int] = Field(None, gt=0, description="BOGO buy quantity")
    bogo_get_quantity: Optional[int] = Field(None, gt=0, description="BOGO get quantity")

    # Applicability
    applicable_to: str = Field(
        default="all_products",
        description="Product applicability (all_products, specific_skus, category, brand, type)"
    )
    specific_skus: Optional[List[str]] = Field(None, description="Specific product SKUs (if applicable_to=specific_skus)")
    category: Optional[str] = Field(None, description="Category filter (if applicable_to=category)")
    brand: Optional[str] = Field(None, description="Brand filter (if applicable_to=brand)")

    # Customer targeting
    customer_segment: str = Field(
        default="all",
        description="Customer segment (all, new_customer, returning, vip, medical, recreational)"
    )

    # Date range
    start_date: datetime = Field(..., description="Promotion start date")
    end_date: datetime = Field(..., description="Promotion end date")

    # Advanced
    can_stack: bool = Field(default=False, description="Allow stacking with other promotions")
    priority: int = Field(default=0, ge=0, le=100, description="Priority (0-100)")

    class Config:
        json_schema_extra = {
            "example": {
                "store_id": "store-123",
                "promotion_name": "Black Friday 2025",
                "description": "25% off all products for Black Friday",
                "discount_type": "percentage",
                "discount_value": 25.0,
                "applicable_to": "all_products",
                "customer_segment": "all",
                "start_date": "2025-11-29T00:00:00Z",
                "end_date": "2025-11-30T23:59:59Z",
                "can_stack": False,
                "priority": 10
            }
        }


class GenerateDiscountCodeRequest(BaseModel):
    """Request to generate discount code"""
    code: str = Field(..., min_length=3, max_length=50, description="Discount code (will be uppercased)")
    max_uses: Optional[int] = Field(None, gt=0, description="Maximum uses (None = unlimited)")
    customer_segment: str = Field(
        default="all",
        description="Customer segment (all, new_customer, returning, vip, medical, recreational)"
    )
    specific_customer_id: Optional[str] = Field(None, description="Specific customer ID (for personalized codes)")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "WELCOME25",
                "max_uses": 100,
                "customer_segment": "new_customer"
            }
        }


class ApplyDiscountCodeRequest(BaseModel):
    """Request to apply discount code"""
    code: str = Field(..., description="Discount code")
    customer_id: str = Field(..., description="Customer ID")
    order_amount: float = Field(..., gt=0, description="Order amount")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "WELCOME25",
                "customer_id": "customer-123",
                "order_amount": 100.00
            }
        }


class UpdatePromotionStatusRequest(BaseModel):
    """Request to update promotion status"""
    action: str = Field(
        ...,
        description="Action (schedule, activate, pause, resume, expire, cancel)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "action": "activate"
            }
        }


class CalculateDiscountRequest(BaseModel):
    """Request to calculate discount for order"""
    order_amount: float = Field(..., gt=0, description="Order amount")
    quantity: int = Field(..., gt=0, description="Product quantity")
    customer_id: Optional[str] = Field(None, description="Customer ID")
    discount_code: Optional[str] = Field(None, description="Discount code (if applicable)")

    class Config:
        json_schema_extra = {
            "example": {
                "order_amount": 100.00,
                "quantity": 3,
                "customer_id": "customer-123",
                "discount_code": "WELCOME25"
            }
        }


# Pricing & Promotions Mapper Functions
def map_pricing_tier_to_dto(tier) -> PricingTierDTO:
    """Convert PricingTier value object to DTO"""
    return PricingTierDTO(
        min_quantity=float(tier.min_quantity),
        max_quantity=float(tier.max_quantity) if tier.max_quantity else None,
        discount_percentage=float(tier.discount_percentage) if tier.discount_percentage else None,
        fixed_price=float(tier.fixed_price) if tier.fixed_price else None
    )


def map_bulk_discount_rule_to_dto(bulk_rule) -> BulkDiscountRuleDTO:
    """Convert BulkDiscountRule value object to DTO"""
    if not bulk_rule:
        return None

    return BulkDiscountRuleDTO(
        product_sku=bulk_rule.product_sku,
        base_price=float(bulk_rule.base_price),
        tiers=[map_pricing_tier_to_dto(tier) for tier in bulk_rule.tiers]
    )


def map_price_schedule_to_dto(schedule, current_time: datetime = None) -> PriceScheduleDTO:
    """Convert PriceSchedule value object to DTO"""
    if current_time is None:
        current_time = datetime.utcnow()

    return PriceScheduleDTO(
        name=schedule.name,
        discount_type=schedule.discount_type.value if hasattr(schedule.discount_type, 'value') else str(schedule.discount_type),
        discount_value=float(schedule.discount_value),
        start_time=schedule.start_time,
        end_time=schedule.end_time,
        days_of_week=schedule.days_of_week,
        start_hour=schedule.start_hour,
        end_hour=schedule.end_hour,
        is_recurring=schedule.days_of_week is not None or schedule.start_hour is not None,
        is_active_now=schedule.is_active(current_time) if hasattr(schedule, 'is_active') else False
    )


def map_product_price_to_dto(product_price, current_time: datetime = None) -> ProductPriceDTO:
    """Convert ProductPrice entity to DTO"""
    # Get active schedule name if any
    active_schedule = None
    if product_price.price_schedules:
        for schedule in product_price.price_schedules:
            if hasattr(schedule, 'is_active') and schedule.is_active(current_time or datetime.utcnow()):
                active_schedule = schedule.name
                break

    return ProductPriceDTO(
        product_sku=product_price.product_sku,
        product_name=product_price.product_name,
        cost_price=float(product_price.cost_price),
        base_price=float(product_price.base_price),
        markup_percentage=float(product_price.markup_percentage),
        current_price=float(product_price.get_current_price(current_time or datetime.utcnow())) if hasattr(product_price, 'get_current_price') else float(product_price.base_price),
        bulk_discount_rule=map_bulk_discount_rule_to_dto(product_price.bulk_discount_rule) if product_price.bulk_discount_rule else None,
        price_schedules=[map_price_schedule_to_dto(s, current_time) for s in product_price.price_schedules] if product_price.price_schedules else [],
        active_schedule=active_schedule
    )


def map_pricing_rule_to_dto(pricing_rule) -> PricingRuleDTO:
    """
    Convert PricingRule aggregate to DTO

    Transforms rich domain model to clean API response
    """
    # Handle dict input (from database)
    if isinstance(pricing_rule, dict):
        return PricingRuleDTO(
            id=str(pricing_rule.get("id", "")),
            store_id=str(pricing_rule.get("store_id", "")),
            tenant_id=str(pricing_rule.get("tenant_id", "")),
            rule_name=pricing_rule.get("rule_name", ""),
            pricing_strategy=pricing_rule.get("pricing_strategy", "cost_plus"),
            default_markup_percentage=float(pricing_rule.get("default_markup_percentage", 50.0)),
            product_prices=[],  # Would need to parse from DB
            is_active=pricing_rule.get("is_active", True),
            created_at=pricing_rule.get("created_at", datetime.utcnow()),
            updated_at=pricing_rule.get("updated_at", datetime.utcnow()),
            activated_at=pricing_rule.get("activated_at"),
            events=pricing_rule.get("events", [])
        )

    # Handle domain object
    current_time = datetime.utcnow()

    return PricingRuleDTO(
        # Identifiers
        id=str(pricing_rule.id),
        store_id=str(pricing_rule.store_id),
        tenant_id=str(pricing_rule.tenant_id),
        rule_name=pricing_rule.rule_name,

        # Pricing Strategy
        pricing_strategy=pricing_rule.pricing_strategy.value,
        default_markup_percentage=float(pricing_rule.default_markup_percentage),

        # Product Prices
        product_prices=[map_product_price_to_dto(pp, current_time) for pp in pricing_rule.product_prices],

        # Status
        is_active=pricing_rule.is_active,

        # Timestamps
        created_at=pricing_rule.created_at,
        updated_at=pricing_rule.updated_at,
        activated_at=pricing_rule.activated_at if hasattr(pricing_rule, 'activated_at') else None,

        # Events (for debugging)
        events=[type(event).__name__ for event in pricing_rule.domain_events] if hasattr(pricing_rule, 'domain_events') else []
    )


def map_pricing_rule_list_to_dto(
    rules: List,
    total: int,
    page: int = 1,
    page_size: int = 50
) -> PricingRuleListDTO:
    """Convert list of pricing rules to paginated DTO"""
    rule_dtos = [map_pricing_rule_to_dto(r) for r in rules]

    # Calculate counts
    active_count = sum(1 for r in rule_dtos if r.is_active)
    inactive_count = sum(1 for r in rule_dtos if not r.is_active)

    return PricingRuleListDTO(
        rules=rule_dtos,
        total=total,
        page=page,
        page_size=page_size,
        active_count=active_count,
        inactive_count=inactive_count
    )


def map_discount_code_to_dto(discount_code) -> DiscountCodeDTO:
    """Convert DiscountCode entity to DTO"""
    remaining_uses = None
    if discount_code.max_uses:
        remaining_uses = discount_code.max_uses - discount_code.current_uses

    return DiscountCodeDTO(
        code=discount_code.code,
        max_uses=discount_code.max_uses,
        current_uses=discount_code.current_uses,
        customer_segment=discount_code.customer_segment.value if hasattr(discount_code.customer_segment, 'value') else str(discount_code.customer_segment),
        specific_customer_id=str(discount_code.specific_customer_id) if discount_code.specific_customer_id else None,
        is_active=discount_code.is_active if hasattr(discount_code, 'is_active') else True,
        remaining_uses=remaining_uses
    )


def map_discount_condition_to_dto(condition) -> Optional[DiscountConditionDTO]:
    """Convert DiscountCondition value object to DTO"""
    if not condition:
        return None

    return DiscountConditionDTO(
        min_purchase_amount=float(condition.min_purchase_amount) if condition.min_purchase_amount else None,
        min_quantity=condition.min_quantity,
        required_customer_segment=condition.required_customer_segment.value if condition.required_customer_segment and hasattr(condition.required_customer_segment, 'value') else None,
        valid_from=condition.valid_from,
        valid_until=condition.valid_until
    )


def map_promotion_to_dto(promotion) -> PromotionDTO:
    """
    Convert Promotion aggregate to DTO

    Transforms rich domain model to clean API response
    """
    # Handle dict input (from database)
    if isinstance(promotion, dict):
        return PromotionDTO(
            id=str(promotion.get("id", "")),
            store_id=str(promotion.get("store_id", "")),
            tenant_id=str(promotion.get("tenant_id", "")),
            promotion_name=promotion.get("promotion_name", ""),
            description=promotion.get("description"),
            status=promotion.get("status", "draft"),
            discount_type=promotion.get("discount_type", "percentage"),
            discount_value=float(promotion.get("discount_value", 0)),
            bogo_buy_quantity=promotion.get("bogo_buy_quantity"),
            bogo_get_quantity=promotion.get("bogo_get_quantity"),
            applicable_to=promotion.get("applicable_to", "all_products"),
            specific_skus=promotion.get("specific_skus", []),
            category=promotion.get("category"),
            brand=promotion.get("brand"),
            customer_segment=promotion.get("customer_segment", "all"),
            discount_codes=[],  # Would need to parse from DB
            requires_code=promotion.get("requires_code", False),
            can_stack=promotion.get("can_stack", False),
            priority=promotion.get("priority", 0),
            start_date=promotion.get("start_date", datetime.utcnow()),
            end_date=promotion.get("end_date", datetime.utcnow()),
            is_active_now=promotion.get("status") == "active",
            conditions=None,
            total_uses=promotion.get("total_uses", 0),
            total_discount_amount=float(promotion.get("total_discount_amount", 0)),
            created_at=promotion.get("created_at", datetime.utcnow()),
            updated_at=promotion.get("updated_at", datetime.utcnow()),
            activated_at=promotion.get("activated_at"),
            paused_at=promotion.get("paused_at"),
            events=promotion.get("events", [])
        )

    # Handle domain object
    current_time = datetime.utcnow()
    is_active_now = (
        promotion.status.value == "active" and
        promotion.start_date <= current_time <= promotion.end_date
    )

    return PromotionDTO(
        # Identifiers
        id=str(promotion.id),
        store_id=str(promotion.store_id),
        tenant_id=str(promotion.tenant_id),
        promotion_name=promotion.promotion_name,
        description=promotion.description if hasattr(promotion, 'description') else None,

        # Status
        status=promotion.status.value,

        # Discount Configuration
        discount_type=promotion.discount_type.value,
        discount_value=float(promotion.discount_value),

        # BOGO
        bogo_buy_quantity=promotion.bogo_buy_quantity,
        bogo_get_quantity=promotion.bogo_get_quantity,

        # Applicability
        applicable_to=promotion.applicable_to.value if hasattr(promotion.applicable_to, 'value') else str(promotion.applicable_to),
        specific_skus=list(promotion.specific_skus) if promotion.specific_skus else [],
        category=promotion.category,
        brand=promotion.brand,

        # Customer Targeting
        customer_segment=promotion.customer_segment.value if hasattr(promotion.customer_segment, 'value') else str(promotion.customer_segment),

        # Discount Codes
        discount_codes=[map_discount_code_to_dto(code) for code in promotion.discount_codes] if promotion.discount_codes else [],
        requires_code=promotion.requires_code,

        # Stacking
        can_stack=promotion.can_stack,
        priority=promotion.priority,

        # Date Range
        start_date=promotion.start_date,
        end_date=promotion.end_date,
        is_active_now=is_active_now,

        # Conditions
        conditions=map_discount_condition_to_dto(promotion.conditions) if hasattr(promotion, 'conditions') and promotion.conditions else None,

        # Usage Statistics
        total_uses=promotion.total_uses if hasattr(promotion, 'total_uses') else 0,
        total_discount_amount=float(promotion.total_discount_amount) if hasattr(promotion, 'total_discount_amount') else 0.0,

        # Timestamps
        created_at=promotion.created_at,
        updated_at=promotion.updated_at,
        activated_at=promotion.activated_at if hasattr(promotion, 'activated_at') else None,
        paused_at=promotion.paused_at if hasattr(promotion, 'paused_at') else None,

        # Events (for debugging)
        events=[type(event).__name__ for event in promotion.domain_events] if hasattr(promotion, 'domain_events') else []
    )


def map_promotion_list_to_dto(
    promotions: List,
    total: int,
    page: int = 1,
    page_size: int = 50
) -> PromotionListDTO:
    """Convert list of promotions to paginated DTO"""
    promotion_dtos = [map_promotion_to_dto(p) for p in promotions]

    # Calculate counts
    active_count = sum(1 for p in promotion_dtos if p.is_active_now)
    scheduled_count = sum(1 for p in promotion_dtos if p.status == "scheduled")
    expired_count = sum(1 for p in promotion_dtos if p.status == "expired")

    return PromotionListDTO(
        promotions=promotion_dtos,
        total=total,
        page=page,
        page_size=page_size,
        active_count=active_count,
        scheduled_count=scheduled_count,
        expired_count=expired_count
    )


# ============================================================================
# Delivery Management DTOs
# ============================================================================

class GeoCoordinatesDTO(BaseModel):
    """Geographic coordinates DTO"""
    latitude: float
    longitude: float

    class Config:
        json_schema_extra = {
            "example": {
                "latitude": 43.6532,
                "longitude": -79.3832
            }
        }


class DeliveryAddressDTO(BaseModel):
    """Delivery address DTO"""
    street_address: str
    city: str
    province: str
    postal_code: str
    country: str = "Canada"
    unit: Optional[str] = None
    coordinates: Optional[GeoCoordinatesDTO] = None
    delivery_instructions: Optional[str] = None
    buzzer_code: Optional[str] = None
    full_address: str = ""
    short_address: str = ""
    is_geocoded: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "street_address": "123 Main St",
                "city": "Toronto",
                "province": "ON",
                "postal_code": "M5V 3A8",
                "country": "Canada",
                "unit": "Apt 101",
                "coordinates": {
                    "latitude": 43.6532,
                    "longitude": -79.3832
                },
                "delivery_instructions": "Ring doorbell, leave at door",
                "buzzer_code": "1234",
                "full_address": "Apt 101 - 123 Main St, Toronto, ON M5V 3A8, Canada",
                "short_address": "123 Main St, Toronto",
                "is_geocoded": True
            }
        }


class DeliveryZoneDTO(BaseModel):
    """Delivery zone DTO"""
    zone_name: str
    zone_code: str
    delivery_fee: float
    estimated_minutes_min: int
    estimated_minutes_max: int
    postal_code_prefixes: Optional[List[str]] = None
    max_deliveries_per_hour: Optional[int] = None
    is_active: bool = True
    estimated_time_range: str = ""

    class Config:
        json_schema_extra = {
            "example": {
                "zone_name": "Downtown Toronto",
                "zone_code": "DT-TOR",
                "delivery_fee": 5.00,
                "estimated_minutes_min": 20,
                "estimated_minutes_max": 40,
                "postal_code_prefixes": ["M5V", "M5H", "M5G"],
                "max_deliveries_per_hour": 20,
                "is_active": True,
                "estimated_time_range": "20-40 minutes"
            }
        }


class DeliveryTimeWindowDTO(BaseModel):
    """Delivery time window DTO"""
    window_start: datetime
    window_end: datetime
    is_guaranteed: bool = False
    duration_minutes: int = 0
    is_current: bool = False
    is_past: bool = False
    is_future: bool = False
    display_text: str = ""

    class Config:
        json_schema_extra = {
            "example": {
                "window_start": "2025-10-09T14:00:00Z",
                "window_end": "2025-10-09T16:00:00Z",
                "is_guaranteed": True,
                "duration_minutes": 120,
                "is_current": False,
                "is_past": False,
                "is_future": True,
                "display_text": "02:00 PM - 04:00 PM (Guaranteed)"
            }
        }


class RouteStopDTO(BaseModel):
    """Route stop DTO"""
    delivery_id: str
    address: DeliveryAddressDTO
    sequence: int
    estimated_arrival: datetime
    estimated_duration_minutes: int = 5

    class Config:
        json_schema_extra = {
            "example": {
                "delivery_id": "delivery-123",
                "address": {
                    "street_address": "123 Main St",
                    "city": "Toronto",
                    "province": "ON",
                    "postal_code": "M5V 3A8",
                    "full_address": "123 Main St, Toronto, ON M5V 3A8, Canada"
                },
                "sequence": 1,
                "estimated_arrival": "2025-10-09T14:30:00Z",
                "estimated_duration_minutes": 5
            }
        }


class OptimizedRouteDTO(BaseModel):
    """Optimized route DTO"""
    stops: List[RouteStopDTO] = Field(default_factory=list)
    total_distance_km: float
    total_duration_minutes: int
    optimized_at: datetime
    stop_count: int = 0
    estimated_completion_time: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "stops": [
                    {
                        "delivery_id": "delivery-123",
                        "sequence": 1,
                        "estimated_arrival": "2025-10-09T14:30:00Z"
                    }
                ],
                "total_distance_km": 12.5,
                "total_duration_minutes": 45,
                "optimized_at": "2025-10-09T14:00:00Z",
                "stop_count": 3,
                "estimated_completion_time": "2025-10-09T15:15:00Z"
            }
        }


class DeliveryDriverDTO(BaseModel):
    """Delivery driver DTO"""
    id: str
    name: str
    phone: str
    email: str
    status: str  # available, on_delivery, break, offline
    vehicle_type: str  # car, bike, scooter, walking, van
    vehicle_plate: Optional[str] = None
    current_location: Optional[GeoCoordinatesDTO] = None
    last_location_update: Optional[datetime] = None
    total_deliveries: int = 0
    rating: float = 5.0
    drivers_license: Optional[str] = None
    license_expiry: Optional[datetime] = None
    is_available: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "id": "driver-123",
                "name": "John Driver",
                "phone": "+1-416-555-0199",
                "email": "john.driver@example.com",
                "status": "available",
                "vehicle_type": "car",
                "vehicle_plate": "ABC 1234",
                "total_deliveries": 150,
                "rating": 4.8,
                "is_available": True
            }
        }


class DeliveryDTO(BaseModel):
    """Delivery aggregate DTO"""
    # Identifiers
    id: str
    order_id: str
    store_id: str
    tenant_id: str
    customer_id: Optional[str] = None

    # Status
    status: str  # pending, assigned, picked_up, in_transit, arrived, delivered, failed, cancelled, returned
    priority: str  # standard, express, same_day, scheduled

    # Delivery details
    delivery_address: DeliveryAddressDTO
    pickup_address: Optional[DeliveryAddressDTO] = None

    # Zone and fee
    delivery_zone: Optional[DeliveryZoneDTO] = None
    delivery_fee: float = 0.0

    # Time window
    delivery_time_window: Optional[DeliveryTimeWindowDTO] = None
    estimated_delivery_time: Optional[datetime] = None
    actual_delivery_time: Optional[datetime] = None

    # Driver assignment
    assigned_driver_id: Optional[str] = None
    assigned_driver_name: Optional[str] = None

    # Tracking
    current_location: Optional[GeoCoordinatesDTO] = None
    route: Optional[OptimizedRouteDTO] = None
    distance_to_destination_km: Optional[float] = None

    # Completion
    signature: Optional[str] = None  # Base64 encoded
    photo_proof: Optional[str] = None  # URL
    recipient_name: Optional[str] = None

    # Failure details
    failure_reason: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    # Timestamps
    created_at: datetime
    updated_at: datetime
    assigned_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    arrived_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    # Notes
    delivery_notes: Optional[str] = None
    driver_notes: Optional[str] = None

    # Calculated fields
    is_on_time: bool = True
    can_be_cancelled: bool = True
    elapsed_time_minutes: Optional[int] = None

    # Domain events
    events: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "order_id": "order-123",
                "store_id": "store-456",
                "tenant_id": "tenant-789",
                "status": "in_transit",
                "priority": "standard",
                "delivery_address": {
                    "street_address": "123 Main St",
                    "city": "Toronto",
                    "province": "ON",
                    "postal_code": "M5V 3A8",
                    "full_address": "123 Main St, Toronto, ON M5V 3A8, Canada"
                },
                "delivery_zone": {
                    "zone_name": "Downtown Toronto",
                    "zone_code": "DT-TOR",
                    "delivery_fee": 5.00,
                    "estimated_time_range": "20-40 minutes"
                },
                "delivery_fee": 5.00,
                "assigned_driver_id": "driver-123",
                "assigned_driver_name": "John Driver",
                "distance_to_destination_km": 2.5,
                "retry_count": 0,
                "is_on_time": True,
                "can_be_cancelled": False,
                "created_at": "2025-10-09T12:00:00Z",
                "updated_at": "2025-10-09T14:30:00Z",
                "events": ["DeliveryCreated", "DriverAssigned", "DeliveryStarted"]
            }
        }


class DeliveryListDTO(BaseModel):
    """List of deliveries"""
    deliveries: List[DeliveryDTO]
    total: int
    page: int = 1
    page_size: int = 50
    pending_count: int = 0
    in_transit_count: int = 0
    delivered_count: int = 0
    failed_count: int = 0


class DriverListDTO(BaseModel):
    """List of drivers"""
    drivers: List[DeliveryDriverDTO]
    total: int
    available_count: int = 0
    on_delivery_count: int = 0
    offline_count: int = 0


# Delivery Request DTOs
class CreateDeliveryRequest(BaseModel):
    """Request to create a delivery"""
    order_id: str = Field(..., description="Order ID")
    store_id: str = Field(..., description="Store ID")
    customer_id: Optional[str] = Field(None, description="Customer ID")
    priority: str = Field(default="standard", description="Priority (standard, express, same_day, scheduled)")

    # Delivery address
    street_address: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    province: str = Field(..., description="Province")
    postal_code: str = Field(..., description="Postal code")
    country: str = Field(default="Canada", description="Country")
    unit: Optional[str] = Field(None, description="Unit/Apartment")
    delivery_instructions: Optional[str] = Field(None, max_length=500, description="Delivery instructions")
    buzzer_code: Optional[str] = Field(None, description="Buzzer code")

    # Delivery notes
    delivery_notes: Optional[str] = Field(None, max_length=500, description="Delivery notes")

    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "order-123",
                "store_id": "store-456",
                "priority": "standard",
                "street_address": "123 Main St",
                "city": "Toronto",
                "province": "ON",
                "postal_code": "M5V 3A8",
                "unit": "Apt 101",
                "delivery_instructions": "Ring doorbell, leave at door"
            }
        }


class AssignDriverRequest(BaseModel):
    """Request to assign driver to delivery"""
    driver_id: str = Field(..., description="Driver ID")
    estimated_delivery_time: Optional[datetime] = Field(None, description="Estimated delivery time")

    class Config:
        json_schema_extra = {
            "example": {
                "driver_id": "driver-123",
                "estimated_delivery_time": "2025-10-09T15:00:00Z"
            }
        }


class UpdateLocationRequest(BaseModel):
    """Request to update delivery location"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")

    class Config:
        json_schema_extra = {
            "example": {
                "latitude": 43.6532,
                "longitude": -79.3832
            }
        }


class CompleteDeliveryRequest(BaseModel):
    """Request to complete delivery"""
    signature: Optional[str] = Field(None, description="Base64 encoded signature")
    photo_proof: Optional[str] = Field(None, description="Photo proof URL")
    recipient_name: Optional[str] = Field(None, description="Recipient name")

    class Config:
        json_schema_extra = {
            "example": {
                "signature": "data:image/png;base64,iVBORw0KGgoAAAANS...",
                "recipient_name": "Jane Doe"
            }
        }


class FailDeliveryRequest(BaseModel):
    """Request to fail delivery"""
    failure_reason: str = Field(..., min_length=5, max_length=500, description="Failure reason")

    class Config:
        json_schema_extra = {
            "example": {
                "failure_reason": "Customer not available, no answer at door"
            }
        }


class SetDeliveryZoneRequest(BaseModel):
    """Request to set delivery zone"""
    zone_name: str = Field(..., description="Zone name")
    zone_code: str = Field(..., description="Zone code")
    delivery_fee: float = Field(..., ge=0, description="Delivery fee")
    estimated_minutes_min: int = Field(..., gt=0, description="Min estimated minutes")
    estimated_minutes_max: int = Field(..., gt=0, description="Max estimated minutes")
    postal_code_prefixes: Optional[List[str]] = Field(None, description="Postal code prefixes")

    class Config:
        json_schema_extra = {
            "example": {
                "zone_name": "Downtown Toronto",
                "zone_code": "DT-TOR",
                "delivery_fee": 5.00,
                "estimated_minutes_min": 20,
                "estimated_minutes_max": 40,
                "postal_code_prefixes": ["M5V", "M5H", "M5G"]
            }
        }


class SetTimeWindowRequest(BaseModel):
    """Request to set delivery time window"""
    window_start: datetime = Field(..., description="Window start time")
    window_end: datetime = Field(..., description="Window end time")
    is_guaranteed: bool = Field(default=False, description="Guaranteed delivery")

    class Config:
        json_schema_extra = {
            "example": {
                "window_start": "2025-10-09T14:00:00Z",
                "window_end": "2025-10-09T16:00:00Z",
                "is_guaranteed": True
            }
        }


class CreateDriverRequest(BaseModel):
    """Request to create a driver"""
    name: str = Field(..., min_length=2, max_length=100, description="Driver name")
    phone: str = Field(..., description="Phone number")
    email: str = Field(..., description="Email address")
    vehicle_type: str = Field(..., description="Vehicle type (car, bike, scooter, walking, van)")
    vehicle_plate: Optional[str] = Field(None, description="Vehicle plate number")
    drivers_license: Optional[str] = Field(None, description="Driver's license number")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Driver",
                "phone": "+1-416-555-0199",
                "email": "john.driver@example.com",
                "vehicle_type": "car",
                "vehicle_plate": "ABC 1234",
                "drivers_license": "D1234567"
            }
        }


class UpdateDriverStatusRequest(BaseModel):
    """Request to update driver status"""
    status: str = Field(..., description="Status (available, on_delivery, break, offline)")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "available"
            }
        }


class UpdateDriverLocationRequest(BaseModel):
    """Request to update driver location"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")

    class Config:
        json_schema_extra = {
            "example": {
                "latitude": 43.6532,
                "longitude": -79.3832
            }
        }


# Delivery Mapper Functions
def map_geo_coordinates_to_dto(coordinates) -> Optional[GeoCoordinatesDTO]:
    """Convert GeoCoordinates value object to DTO"""
    if not coordinates:
        return None

    return GeoCoordinatesDTO(
        latitude=float(coordinates.latitude),
        longitude=float(coordinates.longitude)
    )


def map_delivery_address_to_dto(address) -> DeliveryAddressDTO:
    """Convert DeliveryAddress value object to DTO"""
    if isinstance(address, dict):
        return DeliveryAddressDTO(
            street_address=address.get("street_address", ""),
            city=address.get("city", ""),
            province=address.get("province", ""),
            postal_code=address.get("postal_code", ""),
            country=address.get("country", "Canada"),
            unit=address.get("unit"),
            coordinates=map_geo_coordinates_to_dto(address.get("coordinates")),
            delivery_instructions=address.get("delivery_instructions"),
            buzzer_code=address.get("buzzer_code"),
            full_address=address.get("full_address", ""),
            short_address=address.get("short_address", ""),
            is_geocoded=address.get("is_geocoded", False)
        )

    return DeliveryAddressDTO(
        street_address=address.street_address,
        city=address.city,
        province=address.province,
        postal_code=address.postal_code,
        country=address.country,
        unit=address.unit,
        coordinates=map_geo_coordinates_to_dto(address.coordinates),
        delivery_instructions=address.delivery_instructions,
        buzzer_code=address.buzzer_code,
        full_address=address.get_full_address() if hasattr(address, 'get_full_address') else "",
        short_address=address.get_short_address() if hasattr(address, 'get_short_address') else "",
        is_geocoded=address.is_geocoded() if hasattr(address, 'is_geocoded') else False
    )


def map_delivery_zone_to_dto(zone) -> Optional[DeliveryZoneDTO]:
    """Convert DeliveryZone value object to DTO"""
    if not zone:
        return None

    return DeliveryZoneDTO(
        zone_name=zone.zone_name,
        zone_code=zone.zone_code,
        delivery_fee=float(zone.delivery_fee),
        estimated_minutes_min=zone.estimated_minutes_min,
        estimated_minutes_max=zone.estimated_minutes_max,
        postal_code_prefixes=list(zone.postal_code_prefixes) if zone.postal_code_prefixes else None,
        max_deliveries_per_hour=zone.max_deliveries_per_hour,
        is_active=zone.is_active,
        estimated_time_range=zone.get_estimated_time_range() if hasattr(zone, 'get_estimated_time_range') else ""
    )


def map_delivery_time_window_to_dto(window) -> Optional[DeliveryTimeWindowDTO]:
    """Convert DeliveryTimeWindow value object to DTO"""
    if not window:
        return None

    return DeliveryTimeWindowDTO(
        window_start=window.window_start,
        window_end=window.window_end,
        is_guaranteed=window.is_guaranteed,
        duration_minutes=window.get_duration_minutes() if hasattr(window, 'get_duration_minutes') else 0,
        is_current=window.is_current() if hasattr(window, 'is_current') else False,
        is_past=window.is_past() if hasattr(window, 'is_past') else False,
        is_future=window.is_future() if hasattr(window, 'is_future') else False,
        display_text=window.get_display_text() if hasattr(window, 'get_display_text') else ""
    )


def map_route_stop_to_dto(stop) -> RouteStopDTO:
    """Convert RouteStop value object to DTO"""
    return RouteStopDTO(
        delivery_id=str(stop.delivery_id),
        address=map_delivery_address_to_dto(stop.address),
        sequence=stop.sequence,
        estimated_arrival=stop.estimated_arrival,
        estimated_duration_minutes=stop.estimated_duration_minutes
    )


def map_optimized_route_to_dto(route) -> Optional[OptimizedRouteDTO]:
    """Convert OptimizedRoute value object to DTO"""
    if not route:
        return None

    return OptimizedRouteDTO(
        stops=[map_route_stop_to_dto(stop) for stop in route.stops],
        total_distance_km=float(route.total_distance_km),
        total_duration_minutes=route.total_duration_minutes,
        optimized_at=route.optimized_at,
        stop_count=route.get_stop_count() if hasattr(route, 'get_stop_count') else len(route.stops),
        estimated_completion_time=route.get_estimated_completion_time() if hasattr(route, 'get_estimated_completion_time') else None
    )


def map_delivery_driver_to_dto(driver) -> DeliveryDriverDTO:
    """Convert DeliveryDriver entity to DTO"""
    if isinstance(driver, dict):
        return DeliveryDriverDTO(
            id=str(driver.get("id", "")),
            name=driver.get("name", ""),
            phone=driver.get("phone", ""),
            email=driver.get("email", ""),
            status=driver.get("status", "available"),
            vehicle_type=driver.get("vehicle_type", "car"),
            vehicle_plate=driver.get("vehicle_plate"),
            current_location=map_geo_coordinates_to_dto(driver.get("current_location")),
            last_location_update=driver.get("last_location_update"),
            total_deliveries=driver.get("total_deliveries", 0),
            rating=float(driver.get("rating", 5.0)),
            drivers_license=driver.get("drivers_license"),
            license_expiry=driver.get("license_expiry"),
            is_available=driver.get("status") == "available"
        )

    return DeliveryDriverDTO(
        id=str(driver.id),
        name=driver.name,
        phone=driver.phone,
        email=driver.email,
        status=driver.status.value if hasattr(driver.status, 'value') else str(driver.status),
        vehicle_type=driver.vehicle_type.value if hasattr(driver.vehicle_type, 'value') else str(driver.vehicle_type),
        vehicle_plate=driver.vehicle_plate,
        current_location=map_geo_coordinates_to_dto(driver.current_location),
        last_location_update=driver.last_location_update,
        total_deliveries=driver.total_deliveries,
        rating=float(driver.rating),
        drivers_license=driver.drivers_license,
        license_expiry=driver.license_expiry,
        is_available=driver.is_available() if hasattr(driver, 'is_available') else False
    )


def map_delivery_to_dto(delivery) -> DeliveryDTO:
    """
    Convert Delivery aggregate to DTO

    Transforms rich domain model to clean API response
    """
    # Handle dict input (from database)
    if isinstance(delivery, dict):
        return DeliveryDTO(
            id=str(delivery.get("id", "")),
            order_id=str(delivery.get("order_id", "")),
            store_id=str(delivery.get("store_id", "")),
            tenant_id=str(delivery.get("tenant_id", "")),
            customer_id=str(delivery.get("customer_id")) if delivery.get("customer_id") else None,
            status=delivery.get("status", "pending"),
            priority=delivery.get("priority", "standard"),
            delivery_address=map_delivery_address_to_dto(delivery.get("delivery_address", {})),
            pickup_address=map_delivery_address_to_dto(delivery.get("pickup_address")) if delivery.get("pickup_address") else None,
            delivery_zone=map_delivery_zone_to_dto(delivery.get("delivery_zone")),
            delivery_fee=float(delivery.get("delivery_fee", 0)),
            delivery_time_window=map_delivery_time_window_to_dto(delivery.get("delivery_time_window")),
            estimated_delivery_time=delivery.get("estimated_delivery_time"),
            actual_delivery_time=delivery.get("actual_delivery_time"),
            assigned_driver_id=str(delivery.get("assigned_driver_id")) if delivery.get("assigned_driver_id") else None,
            assigned_driver_name=delivery.get("assigned_driver_name"),
            current_location=map_geo_coordinates_to_dto(delivery.get("current_location")),
            route=map_optimized_route_to_dto(delivery.get("route")),
            distance_to_destination_km=float(delivery.get("distance_to_destination_km")) if delivery.get("distance_to_destination_km") else None,
            signature=delivery.get("signature"),
            photo_proof=delivery.get("photo_proof"),
            recipient_name=delivery.get("recipient_name"),
            failure_reason=delivery.get("failure_reason"),
            retry_count=delivery.get("retry_count", 0),
            max_retries=delivery.get("max_retries", 3),
            created_at=delivery.get("created_at", datetime.utcnow()),
            updated_at=delivery.get("updated_at", datetime.utcnow()),
            assigned_at=delivery.get("assigned_at"),
            picked_up_at=delivery.get("picked_up_at"),
            started_at=delivery.get("started_at"),
            arrived_at=delivery.get("arrived_at"),
            completed_at=delivery.get("completed_at"),
            cancelled_at=delivery.get("cancelled_at"),
            delivery_notes=delivery.get("delivery_notes"),
            driver_notes=delivery.get("driver_notes"),
            is_on_time=delivery.get("is_on_time", True),
            can_be_cancelled=delivery.get("can_be_cancelled", True),
            elapsed_time_minutes=delivery.get("elapsed_time_minutes"),
            events=delivery.get("events", [])
        )

    # Handle domain object
    return DeliveryDTO(
        # Identifiers
        id=str(delivery.id),
        order_id=str(delivery.order_id),
        store_id=str(delivery.store_id),
        tenant_id=str(delivery.tenant_id),
        customer_id=str(delivery.customer_id) if delivery.customer_id else None,

        # Status
        status=delivery.status.value,
        priority=delivery.priority.value,

        # Delivery details
        delivery_address=map_delivery_address_to_dto(delivery.delivery_address),
        pickup_address=map_delivery_address_to_dto(delivery.pickup_address) if delivery.pickup_address else None,

        # Zone and fee
        delivery_zone=map_delivery_zone_to_dto(delivery.delivery_zone),
        delivery_fee=float(delivery.delivery_fee),

        # Time window
        delivery_time_window=map_delivery_time_window_to_dto(delivery.delivery_time_window),
        estimated_delivery_time=delivery.estimated_delivery_time,
        actual_delivery_time=delivery.actual_delivery_time,

        # Driver assignment
        assigned_driver_id=str(delivery.assigned_driver_id) if delivery.assigned_driver_id else None,
        assigned_driver_name=delivery.assigned_driver_name,

        # Tracking
        current_location=map_geo_coordinates_to_dto(delivery.current_location),
        route=map_optimized_route_to_dto(delivery.route),
        distance_to_destination_km=float(delivery.distance_to_destination_km) if delivery.distance_to_destination_km else None,

        # Completion
        signature=delivery.signature,
        photo_proof=delivery.photo_proof,
        recipient_name=delivery.recipient_name,

        # Failure details
        failure_reason=delivery.failure_reason,
        retry_count=delivery.retry_count,
        max_retries=delivery.max_retries,

        # Timestamps
        created_at=delivery.created_at,
        updated_at=delivery.updated_at,
        assigned_at=delivery.assigned_at,
        picked_up_at=delivery.picked_up_at,
        started_at=delivery.started_at,
        arrived_at=delivery.arrived_at,
        completed_at=delivery.completed_at,
        cancelled_at=delivery.cancelled_at,

        # Notes
        delivery_notes=delivery.delivery_notes,
        driver_notes=delivery.driver_notes,

        # Calculated fields
        is_on_time=delivery.is_on_time() if hasattr(delivery, 'is_on_time') else True,
        can_be_cancelled=delivery.can_be_cancelled() if hasattr(delivery, 'can_be_cancelled') else True,
        elapsed_time_minutes=delivery.get_elapsed_time_minutes() if hasattr(delivery, 'get_elapsed_time_minutes') else None,

        # Events (for debugging)
        events=[type(event).__name__ for event in delivery.domain_events] if hasattr(delivery, 'domain_events') else []
    )


def map_delivery_list_to_dto(
    deliveries: List,
    total: int,
    page: int = 1,
    page_size: int = 50
) -> DeliveryListDTO:
    """Convert list of deliveries to paginated DTO"""
    delivery_dtos = [map_delivery_to_dto(d) for d in deliveries]

    # Calculate counts
    pending_count = sum(1 for d in delivery_dtos if d.status == "pending")
    in_transit_count = sum(1 for d in delivery_dtos if d.status in ["assigned", "picked_up", "in_transit"])
    delivered_count = sum(1 for d in delivery_dtos if d.status == "delivered")
    failed_count = sum(1 for d in delivery_dtos if d.status == "failed")

    return DeliveryListDTO(
        deliveries=delivery_dtos,
        total=total,
        page=page,
        page_size=page_size,
        pending_count=pending_count,
        in_transit_count=in_transit_count,
        delivered_count=delivered_count,
        failed_count=failed_count
    )


def map_driver_list_to_dto(
    drivers: List,
    total: int
) -> DriverListDTO:
    """Convert list of drivers to DTO"""
    driver_dtos = [map_delivery_driver_to_dto(d) for d in drivers]

    # Calculate counts
    available_count = sum(1 for d in driver_dtos if d.status == "available")
    on_delivery_count = sum(1 for d in driver_dtos if d.status == "on_delivery")
    offline_count = sum(1 for d in driver_dtos if d.status == "offline")

    return DriverListDTO(
        drivers=driver_dtos,
        total=total,
        available_count=available_count,
        on_delivery_count=on_delivery_count,
        offline_count=offline_count
    )


# ============================================================================
# COMMUNICATION MANAGEMENT DTOs
# ============================================================================

class MessageContentDTO(BaseModel):
    """Message content DTO"""
    subject: Optional[str] = None
    body: str
    html_body: Optional[str] = None
    template_variables: Optional[Dict[str, Any]] = None
    attachment_urls: Optional[List[str]] = None
    has_attachments: bool = False


class RecipientDTO(BaseModel):
    """Recipient DTO"""
    recipient_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    device_token: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: str = "Customer"
    language: str = "en"
    timezone: str = "America/Toronto"


class DeliverySettingsDTO(BaseModel):
    """Delivery settings DTO"""
    send_immediately: bool = True
    scheduled_time: Optional[datetime] = None
    max_retries: int = 3
    retry_interval_minutes: int = 5
    max_sends_per_minute: Optional[int] = None
    delivery_window_start_hour: Optional[int] = None
    delivery_window_end_hour: Optional[int] = None
    is_in_delivery_window: bool = True


class BroadcastFilterDTO(BaseModel):
    """Broadcast filter DTO"""
    audience_segment: str  # all_customers, new_customers, vip_customers, etc.
    min_order_count: Optional[int] = None
    max_order_count: Optional[int] = None
    min_total_spent: Optional[float] = None
    last_order_days_ago_min: Optional[int] = None
    last_order_days_ago_max: Optional[int] = None
    cities: Optional[List[str]] = None
    provinces: Optional[List[str]] = None
    postal_code_prefixes: Optional[List[str]] = None
    opted_in_only: bool = True
    exclude_unsubscribed: bool = True


class MessageTemplateDTO(BaseModel):
    """Message template DTO"""
    template_name: str
    template_category: str  # transactional, promotional, informational, reminder, alert
    subject_template: Optional[str] = None
    body_template: str
    required_variables: Optional[List[str]] = None
    all_variables: List[str] = Field(default_factory=list)
    language: str = "en"


class MessageDTO(BaseModel):
    """Individual message DTO"""
    id: str
    recipient: RecipientDTO
    status: str  # pending, queued, sent, delivered, read, failed, bounced, unsubscribed
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    retry_count: int = 0
    provider_message_id: Optional[str] = None
    can_retry: bool = False


class BroadcastDTO(BaseModel):
    """Broadcast aggregate DTO"""
    id: str
    store_id: str
    tenant_id: str
    broadcast_name: str
    description: Optional[str] = None
    
    status: str  # draft, scheduled, sending, sent, completed, cancelled, failed
    message_type: str  # sms, email, push_notification, in_app, whatsapp
    message_category: str  # transactional, promotional, informational, reminder, alert
    message_priority: str  # low, normal, high, urgent
    
    message_content: Optional[MessageContentDTO] = None
    template_used: Optional[str] = None
    
    audience_filter: Optional[BroadcastFilterDTO] = None
    total_recipients: int = 0
    
    messages: List[MessageDTO] = Field(default_factory=list)
    
    delivery_settings: Optional[DeliverySettingsDTO] = None
    
    # Statistics
    total_sent: int = 0
    total_delivered: int = 0
    total_failed: int = 0
    total_read: int = 0
    success_rate: float = 0.0
    delivery_rate: float = 0.0
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    scheduled_time: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    created_by: Optional[str] = None
    
    # Calculated fields
    is_ready_to_send: bool = False
    validation_errors: List[str] = Field(default_factory=list)
    
    # Domain events
    events: List[str] = Field(default_factory=list)


class BroadcastListDTO(BaseModel):
    """Paginated broadcast list DTO"""
    broadcasts: List[BroadcastDTO]
    total: int
    page: int
    page_size: int
    
    # Status counts
    draft_count: int = 0
    scheduled_count: int = 0
    sending_count: int = 0
    completed_count: int = 0
    cancelled_count: int = 0


class BroadcastStatsDTO(BaseModel):
    """Broadcast statistics DTO"""
    broadcast_id: str
    broadcast_name: str
    
    total_recipients: int
    total_sent: int
    total_delivered: int
    total_failed: int
    total_read: int
    
    success_rate: float
    delivery_rate: float
    read_rate: float
    
    avg_delivery_time_seconds: Optional[float] = None
    failed_messages: List[MessageDTO] = Field(default_factory=list)
    retryable_messages_count: int = 0


# Communication Request DTOs

class CreateBroadcastRequest(BaseModel):
    """Request to create a broadcast"""
    store_id: str
    broadcast_name: str
    description: Optional[str] = None
    
    message_type: str  # sms, email, push_notification, in_app, whatsapp
    message_category: str  # transactional, promotional, informational, reminder, alert
    message_priority: str = "normal"  # low, normal, high, urgent
    
    # Message content
    subject: Optional[str] = None
    body: str
    html_body: Optional[str] = None
    template_variables: Optional[Dict[str, Any]] = None
    attachment_urls: Optional[List[str]] = None
    
    # Or use template
    template_name: Optional[str] = None
    
    # Audience filter
    audience_segment: str = "all_customers"
    min_order_count: Optional[int] = None
    max_order_count: Optional[int] = None
    min_total_spent: Optional[float] = None
    last_order_days_ago_min: Optional[int] = None
    last_order_days_ago_max: Optional[int] = None
    cities: Optional[List[str]] = None
    provinces: Optional[List[str]] = None
    postal_code_prefixes: Optional[List[str]] = None
    opted_in_only: bool = True
    exclude_unsubscribed: bool = True


class ScheduleBroadcastRequest(BaseModel):
    """Request to schedule a broadcast"""
    scheduled_time: datetime
    send_immediately: bool = False
    max_retries: int = 3
    retry_interval_minutes: int = 5
    max_sends_per_minute: Optional[int] = None
    delivery_window_start_hour: Optional[int] = None
    delivery_window_end_hour: Optional[int] = None


class AddRecipientsRequest(BaseModel):
    """Request to add recipients to broadcast"""
    recipients: List[Dict[str, Any]]  # List of recipient data


class UpdateMessageStatusRequest(BaseModel):
    """Request to update message status"""
    message_id: str
    status: str  # sent, delivered, read, failed
    provider_message_id: Optional[str] = None
    failure_reason: Optional[str] = None


class CreateMessageTemplateRequest(BaseModel):
    """Request to create message template"""
    template_name: str
    template_category: str  # transactional, promotional, informational, reminder, alert
    subject_template: Optional[str] = None
    body_template: str
    required_variables: Optional[List[str]] = None
    language: str = "en"


class TestBroadcastRequest(BaseModel):
    """Request to send test broadcast"""
    test_recipients: List[Dict[str, Any]]  # List of test recipient data


# Communication Mapper Functions

def map_message_content_to_dto(message_content) -> MessageContentDTO:
    """Convert MessageContent value object to DTO"""
    if not message_content:
        return None
    
    # Handle dict input
    if isinstance(message_content, dict):
        return MessageContentDTO(
            subject=message_content.get("subject"),
            body=message_content.get("body", ""),
            html_body=message_content.get("html_body"),
            template_variables=message_content.get("template_variables"),
            attachment_urls=message_content.get("attachment_urls"),
            has_attachments=bool(message_content.get("attachment_urls"))
        )
    
    # Handle value object
    return MessageContentDTO(
        subject=message_content.subject,
        body=message_content.body,
        html_body=message_content.html_body,
        template_variables=dict(message_content.template_variables) if message_content.template_variables else None,
        attachment_urls=list(message_content.attachment_urls) if message_content.attachment_urls else None,
        has_attachments=message_content.has_attachments() if hasattr(message_content, 'has_attachments') else False
    )


def map_recipient_to_dto(recipient) -> RecipientDTO:
    """Convert Recipient value object to DTO"""
    if not recipient:
        return None
    
    # Handle dict input
    if isinstance(recipient, dict):
        return RecipientDTO(
            recipient_id=recipient.get("recipient_id"),
            email=recipient.get("email"),
            phone=recipient.get("phone"),
            device_token=recipient.get("device_token"),
            first_name=recipient.get("first_name"),
            last_name=recipient.get("last_name"),
            full_name=recipient.get("full_name", "Customer"),
            language=recipient.get("language", "en"),
            timezone=recipient.get("timezone", "America/Toronto")
        )
    
    # Handle value object
    return RecipientDTO(
        recipient_id=recipient.recipient_id,
        email=recipient.email,
        phone=recipient.phone,
        device_token=recipient.device_token,
        first_name=recipient.first_name,
        last_name=recipient.last_name,
        full_name=recipient.get_full_name() if hasattr(recipient, 'get_full_name') else "Customer",
        language=recipient.language,
        timezone=recipient.timezone
    )


def map_delivery_settings_to_dto(delivery_settings) -> Optional[DeliverySettingsDTO]:
    """Convert DeliverySettings value object to DTO"""
    if not delivery_settings:
        return None
    
    # Handle dict input
    if isinstance(delivery_settings, dict):
        return DeliverySettingsDTO(
            send_immediately=delivery_settings.get("send_immediately", True),
            scheduled_time=delivery_settings.get("scheduled_time"),
            max_retries=delivery_settings.get("max_retries", 3),
            retry_interval_minutes=delivery_settings.get("retry_interval_minutes", 5),
            max_sends_per_minute=delivery_settings.get("max_sends_per_minute"),
            delivery_window_start_hour=delivery_settings.get("delivery_window_start_hour"),
            delivery_window_end_hour=delivery_settings.get("delivery_window_end_hour"),
            is_in_delivery_window=True
        )
    
    # Handle value object
    from datetime import datetime
    return DeliverySettingsDTO(
        send_immediately=delivery_settings.send_immediately,
        scheduled_time=delivery_settings.scheduled_time,
        max_retries=delivery_settings.max_retries,
        retry_interval_minutes=delivery_settings.retry_interval_minutes,
        max_sends_per_minute=delivery_settings.max_sends_per_minute,
        delivery_window_start_hour=delivery_settings.delivery_window_start_hour,
        delivery_window_end_hour=delivery_settings.delivery_window_end_hour,
        is_in_delivery_window=delivery_settings.is_in_delivery_window(datetime.utcnow()) if hasattr(delivery_settings, 'is_in_delivery_window') else True
    )


def map_broadcast_filter_to_dto(broadcast_filter) -> Optional[BroadcastFilterDTO]:
    """Convert BroadcastFilter value object to DTO"""
    if not broadcast_filter:
        return None
    
    # Handle dict input
    if isinstance(broadcast_filter, dict):
        return BroadcastFilterDTO(
            audience_segment=broadcast_filter.get("audience_segment", "all_customers"),
            min_order_count=broadcast_filter.get("min_order_count"),
            max_order_count=broadcast_filter.get("max_order_count"),
            min_total_spent=broadcast_filter.get("min_total_spent"),
            last_order_days_ago_min=broadcast_filter.get("last_order_days_ago_min"),
            last_order_days_ago_max=broadcast_filter.get("last_order_days_ago_max"),
            cities=broadcast_filter.get("cities"),
            provinces=broadcast_filter.get("provinces"),
            postal_code_prefixes=broadcast_filter.get("postal_code_prefixes"),
            opted_in_only=broadcast_filter.get("opted_in_only", True),
            exclude_unsubscribed=broadcast_filter.get("exclude_unsubscribed", True)
        )
    
    # Handle value object
    return BroadcastFilterDTO(
        audience_segment=broadcast_filter.audience_segment.value if hasattr(broadcast_filter.audience_segment, 'value') else broadcast_filter.audience_segment,
        min_order_count=broadcast_filter.min_order_count,
        max_order_count=broadcast_filter.max_order_count,
        min_total_spent=broadcast_filter.min_total_spent,
        last_order_days_ago_min=broadcast_filter.last_order_days_ago_min,
        last_order_days_ago_max=broadcast_filter.last_order_days_ago_max,
        cities=list(broadcast_filter.cities) if broadcast_filter.cities else None,
        provinces=list(broadcast_filter.provinces) if broadcast_filter.provinces else None,
        postal_code_prefixes=list(broadcast_filter.postal_code_prefixes) if broadcast_filter.postal_code_prefixes else None,
        opted_in_only=broadcast_filter.opted_in_only,
        exclude_unsubscribed=broadcast_filter.exclude_unsubscribed
    )


def map_message_to_dto(message) -> MessageDTO:
    """Convert Message entity to DTO"""
    # Handle dict input
    if isinstance(message, dict):
        return MessageDTO(
            id=str(message.get("id", "")),
            recipient=map_recipient_to_dto(message.get("recipient", {})),
            status=message.get("status", "pending"),
            sent_at=message.get("sent_at"),
            delivered_at=message.get("delivered_at"),
            read_at=message.get("read_at"),
            failed_at=message.get("failed_at"),
            failure_reason=message.get("failure_reason"),
            retry_count=message.get("retry_count", 0),
            provider_message_id=message.get("provider_message_id"),
            can_retry=False
        )
    
    # Handle domain object
    return MessageDTO(
        id=str(message.id),
        recipient=map_recipient_to_dto(message.recipient),
        status=message.status.value if hasattr(message.status, 'value') else message.status,
        sent_at=message.sent_at,
        delivered_at=message.delivered_at,
        read_at=message.read_at,
        failed_at=message.failed_at,
        failure_reason=message.failure_reason,
        retry_count=message.retry_count,
        provider_message_id=message.provider_message_id,
        can_retry=message.can_retry(3) if hasattr(message, 'can_retry') else False
    )


def map_broadcast_to_dto(broadcast) -> BroadcastDTO:
    """Convert Broadcast aggregate to DTO"""
    # Handle dict input
    if isinstance(broadcast, dict):
        return BroadcastDTO(
            id=str(broadcast.get("id", "")),
            store_id=str(broadcast.get("store_id", "")),
            tenant_id=str(broadcast.get("tenant_id", "")),
            broadcast_name=broadcast.get("broadcast_name", ""),
            description=broadcast.get("description"),
            status=broadcast.get("status", "draft"),
            message_type=broadcast.get("message_type", "email"),
            message_category=broadcast.get("message_category", "promotional"),
            message_priority=broadcast.get("message_priority", "normal"),
            message_content=map_message_content_to_dto(broadcast.get("message_content")),
            template_used=broadcast.get("template_used"),
            audience_filter=map_broadcast_filter_to_dto(broadcast.get("audience_filter")),
            total_recipients=broadcast.get("total_recipients", 0),
            messages=[],
            delivery_settings=map_delivery_settings_to_dto(broadcast.get("delivery_settings")),
            total_sent=broadcast.get("total_sent", 0),
            total_delivered=broadcast.get("total_delivered", 0),
            total_failed=broadcast.get("total_failed", 0),
            total_read=broadcast.get("total_read", 0),
            success_rate=0.0,
            delivery_rate=0.0,
            created_at=broadcast.get("created_at", datetime.utcnow()),
            updated_at=broadcast.get("updated_at", datetime.utcnow()),
            scheduled_time=broadcast.get("scheduled_time"),
            started_at=broadcast.get("started_at"),
            completed_at=broadcast.get("completed_at"),
            created_by=str(broadcast.get("created_by")) if broadcast.get("created_by") else None,
            is_ready_to_send=False,
            validation_errors=[],
            events=[]
        )
    
    # Handle domain object
    return BroadcastDTO(
        id=str(broadcast.id),
        store_id=str(broadcast.store_id),
        tenant_id=str(broadcast.tenant_id),
        broadcast_name=broadcast.broadcast_name,
        description=broadcast.description,
        status=broadcast.status.value if hasattr(broadcast.status, 'value') else broadcast.status,
        message_type=broadcast.message_type.value if hasattr(broadcast.message_type, 'value') else broadcast.message_type,
        message_category=broadcast.message_category.value if hasattr(broadcast.message_category, 'value') else broadcast.message_category,
        message_priority=broadcast.message_priority.value if hasattr(broadcast.message_priority, 'value') else broadcast.message_priority,
        message_content=map_message_content_to_dto(broadcast.message_content),
        template_used=broadcast.template_used,
        audience_filter=map_broadcast_filter_to_dto(broadcast.audience_filter),
        total_recipients=broadcast.total_recipients,
        messages=[map_message_to_dto(m) for m in broadcast.messages] if broadcast.messages else [],
        delivery_settings=map_delivery_settings_to_dto(broadcast.delivery_settings),
        total_sent=broadcast.total_sent,
        total_delivered=broadcast.total_delivered,
        total_failed=broadcast.total_failed,
        total_read=broadcast.total_read,
        success_rate=broadcast.get_success_rate() if hasattr(broadcast, 'get_success_rate') else 0.0,
        delivery_rate=broadcast.get_delivery_rate() if hasattr(broadcast, 'get_delivery_rate') else 0.0,
        created_at=broadcast.created_at,
        updated_at=broadcast.updated_at,
        scheduled_time=broadcast.scheduled_time,
        started_at=broadcast.started_at,
        completed_at=broadcast.completed_at,
        created_by=str(broadcast.created_by) if broadcast.created_by else None,
        is_ready_to_send=broadcast.is_ready_to_send() if hasattr(broadcast, 'is_ready_to_send') else False,
        validation_errors=broadcast.validate() if hasattr(broadcast, 'validate') else [],
        events=[type(event).__name__ for event in broadcast.domain_events] if hasattr(broadcast, 'domain_events') else []
    )


def map_broadcast_list_to_dto(broadcasts: List, total: int, page: int = 1, page_size: int = 50) -> BroadcastListDTO:
    """Convert list to paginated DTO with counts"""
    broadcast_dtos = [map_broadcast_to_dto(b) for b in broadcasts]
    
    draft_count = sum(1 for b in broadcast_dtos if b.status == "draft")
    scheduled_count = sum(1 for b in broadcast_dtos if b.status == "scheduled")
    sending_count = sum(1 for b in broadcast_dtos if b.status == "sending")
    completed_count = sum(1 for b in broadcast_dtos if b.status == "completed")
    cancelled_count = sum(1 for b in broadcast_dtos if b.status == "cancelled")
    
    return BroadcastListDTO(
        broadcasts=broadcast_dtos,
        total=total,
        page=page,
        page_size=page_size,
        draft_count=draft_count,
        scheduled_count=scheduled_count,
        sending_count=sending_count,
        completed_count=completed_count,
        cancelled_count=cancelled_count
    )


def map_broadcast_stats_to_dto(broadcast) -> BroadcastStatsDTO:
    """Convert broadcast to statistics DTO"""
    if isinstance(broadcast, dict):
        total_sent = broadcast.get("total_sent", 0)
        total_delivered = broadcast.get("total_delivered", 0)
        total_recipients = broadcast.get("total_recipients", 1)
        
        success_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0.0
        delivery_rate = (total_delivered / total_recipients * 100) if total_recipients > 0 else 0.0
        read_rate = (broadcast.get("total_read", 0) / total_delivered * 100) if total_delivered > 0 else 0.0
        
        return BroadcastStatsDTO(
            broadcast_id=str(broadcast.get("id", "")),
            broadcast_name=broadcast.get("broadcast_name", ""),
            total_recipients=total_recipients,
            total_sent=total_sent,
            total_delivered=total_delivered,
            total_failed=broadcast.get("total_failed", 0),
            total_read=broadcast.get("total_read", 0),
            success_rate=success_rate,
            delivery_rate=delivery_rate,
            read_rate=read_rate,
            failed_messages=[],
            retryable_messages_count=0
        )
    
    # Handle domain object
    failed_messages = broadcast.get_failed_messages() if hasattr(broadcast, 'get_failed_messages') else []
    retryable = broadcast.get_retryable_messages() if hasattr(broadcast, 'get_retryable_messages') else []
    
    total_delivered = broadcast.total_delivered
    total_sent = broadcast.total_sent
    
    read_rate = (broadcast.total_read / total_delivered * 100) if total_delivered > 0 else 0.0
    
    return BroadcastStatsDTO(
        broadcast_id=str(broadcast.id),
        broadcast_name=broadcast.broadcast_name,
        total_recipients=broadcast.total_recipients,
        total_sent=total_sent,
        total_delivered=total_delivered,
        total_failed=broadcast.total_failed,
        total_read=broadcast.total_read,
        success_rate=broadcast.get_success_rate() if hasattr(broadcast, 'get_success_rate') else 0.0,
        delivery_rate=broadcast.get_delivery_rate() if hasattr(broadcast, 'get_delivery_rate') else 0.0,
        read_rate=read_rate,
        failed_messages=[map_message_to_dto(m) for m in failed_messages],
        retryable_messages_count=len(retryable)
    )


# ============================================================================
# Customer Engagement V2 DTOs (DDD - Customer Engagement Context)
# ============================================================================

class StarRatingDTO(BaseModel):
    """Star rating DTO (1-5 stars)"""
    rating: int = Field(..., ge=1, le=5)
    is_positive: bool  # 4-5 stars

    class Config:
        json_schema_extra = {
            "example": {
                "rating": 5,
                "is_positive": True
            }
        }


class ReviewRatingsDTO(BaseModel):
    """Detailed product ratings breakdown DTO"""
    overall: StarRatingDTO
    quality: Optional[StarRatingDTO] = None
    value: Optional[StarRatingDTO] = None
    potency: Optional[StarRatingDTO] = None  # Cannabis specific
    flavor: Optional[StarRatingDTO] = None
    average_rating: float = 0.0


class ReviewerInfoDTO(BaseModel):
    """Reviewer information with badges"""
    customer_id: str
    display_name: str
    is_verified_purchaser: bool = False
    total_reviews: int = 0
    helpful_votes_received: int = 0
    reviewer_badge: Optional[str] = None  # Top Reviewer, Frequent Reviewer, etc.
    member_since: Optional[str] = None


class ReviewModerationDTO(BaseModel):
    """Review moderation details"""
    status: str  # pending, approved, rejected, flagged, hidden
    flag_count: int = 0
    flag_reasons: List[str] = Field(default_factory=list)
    moderated_by: Optional[str] = None
    moderated_at: Optional[str] = None
    moderation_notes: Optional[str] = None
    needs_moderation: bool = False


class HelpfulVoteDTO(BaseModel):
    """Helpful vote DTO"""
    id: str
    voter_id: str
    is_helpful: bool
    voted_at: str


class ReviewResponseDTO(BaseModel):
    """Store response to review"""
    id: str
    response_text: str
    responder_name: str
    responder_role: str
    responded_at: str


class ProductReviewDTO(BaseModel):
    """Product review aggregate DTO"""
    id: str
    store_id: str
    tenant_id: str
    product_sku: str
    product_name: str
    reviewer: ReviewerInfoDTO
    ratings: ReviewRatingsDTO
    title: str
    review_text: str
    review_source: str  # website, mobile_app, email, in_store
    photo_urls: List[str] = Field(default_factory=list)
    video_urls: List[str] = Field(default_factory=list)
    moderation: ReviewModerationDTO
    helpful_votes_count: int = 0
    not_helpful_votes_count: int = 0
    helpful_vote_ratio: float = 0.0
    store_response: Optional[ReviewResponseDTO] = None
    is_published: bool = False
    published_at: Optional[str] = None
    created_at: str
    updated_at: str
    events: List[str] = Field(default_factory=list)


class ReviewListDTO(BaseModel):
    """Paginated review list DTO"""
    reviews: List[ProductReviewDTO]
    total: int
    page: int
    page_size: int
    has_more: bool


class ReviewStatisticsDTO(BaseModel):
    """Aggregate review statistics for product"""
    product_sku: str
    product_name: str
    total_reviews: int
    average_rating: float
    five_star_count: int = 0
    four_star_count: int = 0
    three_star_count: int = 0
    two_star_count: int = 0
    one_star_count: int = 0
    five_star_percentage: float = 0.0
    four_star_percentage: float = 0.0
    three_star_percentage: float = 0.0
    two_star_percentage: float = 0.0
    one_star_percentage: float = 0.0
    positive_percentage: float = 0.0  # 4-5 stars
    negative_percentage: float = 0.0  # 1-2 stars
    verified_purchase_percentage: float = 0.0
    total_helpful_votes: int = 0


# Request DTOs

class CreateReviewRequest(BaseModel):
    """Request to create product review"""
    store_id: str
    product_sku: str
    product_name: str
    customer_id: str
    display_name: str
    overall_rating: int = Field(..., ge=1, le=5)
    quality_rating: Optional[int] = Field(None, ge=1, le=5)
    value_rating: Optional[int] = Field(None, ge=1, le=5)
    potency_rating: Optional[int] = Field(None, ge=1, le=5)
    flavor_rating: Optional[int] = Field(None, ge=1, le=5)
    title: str = Field(..., max_length=200)
    review_text: str = Field(..., max_length=5000)
    review_source: str = "website"
    is_verified_purchaser: bool = False
    photo_urls: Optional[List[str]] = None
    video_urls: Optional[List[str]] = None


class ApproveReviewRequest(BaseModel):
    """Request to approve review"""
    approved_by: str
    notes: Optional[str] = None


class RejectReviewRequest(BaseModel):
    """Request to reject review"""
    rejected_by: str
    reason: str
    notes: Optional[str] = None


class FlagReviewRequest(BaseModel):
    """Request to flag review"""
    flagger_id: str
    flag_reason: str  # inappropriate, spam, fake, offensive, off_topic, duplicate, other
    details: Optional[str] = None


class ModerateReviewRequest(BaseModel):
    """Request to moderate flagged review"""
    moderator_id: str
    action: str  # approve, reject, hide
    notes: Optional[str] = None


class MarkHelpfulRequest(BaseModel):
    """Request to mark review as helpful"""
    voter_id: str


class MarkNotHelpfulRequest(BaseModel):
    """Request to mark review as not helpful"""
    voter_id: str


class AddStoreResponseRequest(BaseModel):
    """Request to add store response"""
    response_text: str = Field(..., max_length=1000)
    responder_name: str
    responder_role: str


class UpdateReviewTextRequest(BaseModel):
    """Request to update review text (within 7 days)"""
    new_title: str = Field(..., max_length=200)
    new_text: str = Field(..., max_length=5000)


# ============================================================================
# Customer Engagement V2 Mappers
# ============================================================================

def map_star_rating_to_dto(star_rating) -> StarRatingDTO:
    """Convert StarRating value object to DTO"""
    if isinstance(star_rating, dict):
        return StarRatingDTO(
            rating=star_rating.get('rating', 1),
            is_positive=star_rating.get('rating', 1) >= 4
        )

    return StarRatingDTO(
        rating=star_rating.rating,
        is_positive=star_rating.is_positive() if hasattr(star_rating, 'is_positive') else star_rating.rating >= 4
    )


def map_review_ratings_to_dto(ratings) -> ReviewRatingsDTO:
    """Convert ReviewRatings value object to DTO"""
    if isinstance(ratings, dict):
        overall = StarRatingDTO(
            rating=ratings.get('overall', {}).get('rating', 1),
            is_positive=ratings.get('overall', {}).get('rating', 1) >= 4
        )

        quality = None
        if ratings.get('quality'):
            quality = StarRatingDTO(
                rating=ratings['quality'].get('rating', 1),
                is_positive=ratings['quality'].get('rating', 1) >= 4
            )

        value = None
        if ratings.get('value'):
            value = StarRatingDTO(
                rating=ratings['value'].get('rating', 1),
                is_positive=ratings['value'].get('rating', 1) >= 4
            )

        potency = None
        if ratings.get('potency'):
            potency = StarRatingDTO(
                rating=ratings['potency'].get('rating', 1),
                is_positive=ratings['potency'].get('rating', 1) >= 4
            )

        flavor = None
        if ratings.get('flavor'):
            flavor = StarRatingDTO(
                rating=ratings['flavor'].get('rating', 1),
                is_positive=ratings['flavor'].get('rating', 1) >= 4
            )

        return ReviewRatingsDTO(
            overall=overall,
            quality=quality,
            value=value,
            potency=potency,
            flavor=flavor,
            average_rating=ratings.get('average_rating', 0.0)
        )

    return ReviewRatingsDTO(
        overall=map_star_rating_to_dto(ratings.overall),
        quality=map_star_rating_to_dto(ratings.quality) if ratings.quality else None,
        value=map_star_rating_to_dto(ratings.value) if ratings.value else None,
        potency=map_star_rating_to_dto(ratings.potency) if ratings.potency else None,
        flavor=map_star_rating_to_dto(ratings.flavor) if ratings.flavor else None,
        average_rating=float(ratings.get_average_rating()) if hasattr(ratings, 'get_average_rating') else 0.0
    )


def map_reviewer_info_to_dto(reviewer) -> ReviewerInfoDTO:
    """Convert ReviewerInfo value object to DTO"""
    if isinstance(reviewer, dict):
        return ReviewerInfoDTO(
            customer_id=reviewer.get('customer_id', ''),
            display_name=reviewer.get('display_name', 'Anonymous'),
            is_verified_purchaser=reviewer.get('is_verified_purchaser', False),
            total_reviews=reviewer.get('total_reviews', 0),
            helpful_votes_received=reviewer.get('helpful_votes_received', 0),
            reviewer_badge=reviewer.get('reviewer_badge'),
            member_since=reviewer.get('member_since')
        )

    return ReviewerInfoDTO(
        customer_id=reviewer.customer_id,
        display_name=reviewer.display_name,
        is_verified_purchaser=reviewer.is_verified_purchaser,
        total_reviews=reviewer.total_reviews,
        helpful_votes_received=reviewer.helpful_votes_received,
        reviewer_badge=reviewer.get_reviewer_badge() if hasattr(reviewer, 'get_reviewer_badge') else None,
        member_since=reviewer.member_since.isoformat() if hasattr(reviewer, 'member_since') and reviewer.member_since else None
    )


def map_review_moderation_to_dto(moderation) -> ReviewModerationDTO:
    """Convert ReviewModeration value object to DTO"""
    if isinstance(moderation, dict):
        status_value = moderation.get('status', 'pending')
        if hasattr(status_value, 'value'):
            status_value = status_value.value

        flag_reasons = []
        if moderation.get('flag_reasons'):
            flag_reasons = [
                fr.value if hasattr(fr, 'value') else str(fr)
                for fr in moderation['flag_reasons']
            ]

        return ReviewModerationDTO(
            status=status_value,
            flag_count=moderation.get('flag_count', 0),
            flag_reasons=flag_reasons,
            moderated_by=moderation.get('moderated_by'),
            moderated_at=moderation.get('moderated_at'),
            moderation_notes=moderation.get('moderation_notes'),
            needs_moderation=moderation.get('needs_moderation', False)
        )

    flag_reasons = []
    if hasattr(moderation, 'flag_reasons') and moderation.flag_reasons:
        flag_reasons = [
            fr.value if hasattr(fr, 'value') else str(fr)
            for fr in moderation.flag_reasons
        ]

    return ReviewModerationDTO(
        status=moderation.status.value if hasattr(moderation.status, 'value') else str(moderation.status),
        flag_count=moderation.flag_count,
        flag_reasons=flag_reasons,
        moderated_by=moderation.moderated_by if hasattr(moderation, 'moderated_by') else None,
        moderated_at=moderation.moderated_at.isoformat() if hasattr(moderation, 'moderated_at') and moderation.moderated_at else None,
        moderation_notes=moderation.moderation_notes if hasattr(moderation, 'moderation_notes') else None,
        needs_moderation=moderation.needs_moderation() if hasattr(moderation, 'needs_moderation') else False
    )


def map_helpful_vote_to_dto(vote) -> HelpfulVoteDTO:
    """Convert HelpfulVote entity to DTO"""
    if isinstance(vote, dict):
        return HelpfulVoteDTO(
            id=str(vote.get('id', '')),
            voter_id=vote.get('voter_id', ''),
            is_helpful=vote.get('is_helpful', True),
            voted_at=vote.get('voted_at', '')
        )

    return HelpfulVoteDTO(
        id=str(vote.id),
        voter_id=vote.voter_id,
        is_helpful=vote.is_helpful,
        voted_at=vote.voted_at.isoformat() if hasattr(vote, 'voted_at') and vote.voted_at else ''
    )


def map_review_response_to_dto(response) -> ReviewResponseDTO:
    """Convert ReviewResponse entity to DTO"""
    if isinstance(response, dict):
        return ReviewResponseDTO(
            id=str(response.get('id', '')),
            response_text=response.get('response_text', ''),
            responder_name=response.get('responder_name', ''),
            responder_role=response.get('responder_role', ''),
            responded_at=response.get('responded_at', '')
        )

    return ReviewResponseDTO(
        id=str(response.id),
        response_text=response.response_text,
        responder_name=response.responder_name,
        responder_role=response.responder_role,
        responded_at=response.responded_at.isoformat() if hasattr(response, 'responded_at') and response.responded_at else ''
    )


def map_product_review_to_dto(review) -> ProductReviewDTO:
    """Convert ProductReview aggregate to DTO with dual input handling"""
    if isinstance(review, dict):
        # Handle dict input (from database)
        moderation_data = review.get('moderation', {})
        reviewer_data = review.get('reviewer', {})
        ratings_data = review.get('ratings', {})

        moderation = ReviewModerationDTO(
            status=moderation_data.get('status', 'pending'),
            flag_count=moderation_data.get('flag_count', 0),
            flag_reasons=moderation_data.get('flag_reasons', []),
            moderated_by=moderation_data.get('moderated_by'),
            moderated_at=moderation_data.get('moderated_at'),
            moderation_notes=moderation_data.get('moderation_notes'),
            needs_moderation=moderation_data.get('needs_moderation', False)
        )

        reviewer = ReviewerInfoDTO(
            customer_id=reviewer_data.get('customer_id', ''),
            display_name=reviewer_data.get('display_name', 'Anonymous'),
            is_verified_purchaser=reviewer_data.get('is_verified_purchaser', False),
            total_reviews=reviewer_data.get('total_reviews', 0),
            helpful_votes_received=reviewer_data.get('helpful_votes_received', 0),
            reviewer_badge=reviewer_data.get('reviewer_badge'),
            member_since=reviewer_data.get('member_since')
        )

        overall_rating = StarRatingDTO(
            rating=ratings_data.get('overall', {}).get('rating', 1),
            is_positive=ratings_data.get('overall', {}).get('rating', 1) >= 4
        )

        ratings = ReviewRatingsDTO(
            overall=overall_rating,
            quality=None,
            value=None,
            potency=None,
            flavor=None,
            average_rating=ratings_data.get('average_rating', 0.0)
        )

        store_response = None
        if review.get('store_response'):
            store_response = map_review_response_to_dto(review['store_response'])

        return ProductReviewDTO(
            id=str(review.get('id', '')),
            store_id=str(review.get('store_id', '')),
            tenant_id=str(review.get('tenant_id', '')),
            product_sku=review.get('product_sku', ''),
            product_name=review.get('product_name', ''),
            reviewer=reviewer,
            ratings=ratings,
            title=review.get('title', ''),
            review_text=review.get('review_text', ''),
            review_source=review.get('review_source', 'website'),
            photo_urls=review.get('photo_urls', []),
            video_urls=review.get('video_urls', []),
            moderation=moderation,
            helpful_votes_count=review.get('helpful_votes_count', 0),
            not_helpful_votes_count=review.get('not_helpful_votes_count', 0),
            helpful_vote_ratio=review.get('helpful_vote_ratio', 0.0),
            store_response=store_response,
            is_published=review.get('is_published', False),
            published_at=review.get('published_at'),
            created_at=review.get('created_at', ''),
            updated_at=review.get('updated_at', ''),
            events=review.get('events', [])
        )

    # Handle domain object
    helpful_count = len([v for v in review.helpful_votes if v.is_helpful])
    not_helpful_count = len([v for v in review.helpful_votes if not v.is_helpful])
    total_votes = len(review.helpful_votes)
    helpful_ratio = (helpful_count / total_votes) if total_votes > 0 else 0.0

    return ProductReviewDTO(
        id=str(review.id),
        store_id=str(review.store_id),
        tenant_id=str(review.tenant_id),
        product_sku=review.product_sku,
        product_name=review.product_name,
        reviewer=map_reviewer_info_to_dto(review.reviewer),
        ratings=map_review_ratings_to_dto(review.ratings),
        title=review.title,
        review_text=review.review_text,
        review_source=review.review_source.value if hasattr(review.review_source, 'value') else str(review.review_source),
        photo_urls=list(review.photo_urls) if review.photo_urls else [],
        video_urls=list(review.video_urls) if review.video_urls else [],
        moderation=map_review_moderation_to_dto(review.moderation),
        helpful_votes_count=helpful_count,
        not_helpful_votes_count=not_helpful_count,
        helpful_vote_ratio=helpful_ratio,
        store_response=map_review_response_to_dto(review.store_response) if review.store_response else None,
        is_published=review.is_published() if hasattr(review, 'is_published') else False,
        published_at=review.published_at.isoformat() if hasattr(review, 'published_at') and review.published_at else None,
        created_at=review.created_at.isoformat() if hasattr(review, 'created_at') else '',
        updated_at=review.updated_at.isoformat() if hasattr(review, 'updated_at') else '',
        events=[type(event).__name__ for event in review.domain_events]
    )


def map_review_statistics_to_dto(stats, product_sku: str, product_name: str) -> ReviewStatisticsDTO:
    """Convert ReviewStatistics value object to DTO"""
    if isinstance(stats, dict):
        total = stats.get('total_reviews', 0)

        five_pct = (stats.get('five_star_count', 0) / total * 100) if total > 0 else 0.0
        four_pct = (stats.get('four_star_count', 0) / total * 100) if total > 0 else 0.0
        three_pct = (stats.get('three_star_count', 0) / total * 100) if total > 0 else 0.0
        two_pct = (stats.get('two_star_count', 0) / total * 100) if total > 0 else 0.0
        one_pct = (stats.get('one_star_count', 0) / total * 100) if total > 0 else 0.0

        return ReviewStatisticsDTO(
            product_sku=product_sku,
            product_name=product_name,
            total_reviews=total,
            average_rating=float(stats.get('average_rating', 0.0)),
            five_star_count=stats.get('five_star_count', 0),
            four_star_count=stats.get('four_star_count', 0),
            three_star_count=stats.get('three_star_count', 0),
            two_star_count=stats.get('two_star_count', 0),
            one_star_count=stats.get('one_star_count', 0),
            five_star_percentage=five_pct,
            four_star_percentage=four_pct,
            three_star_percentage=three_pct,
            two_star_percentage=two_pct,
            one_star_percentage=one_pct,
            positive_percentage=stats.get('positive_percentage', 0.0),
            negative_percentage=stats.get('negative_percentage', 0.0),
            verified_purchase_percentage=stats.get('verified_purchase_percentage', 0.0),
            total_helpful_votes=stats.get('total_helpful_votes', 0)
        )

    total = stats.total_reviews

    five_pct = (stats.five_star_count / total * 100) if total > 0 else 0.0
    four_pct = (stats.four_star_count / total * 100) if total > 0 else 0.0
    three_pct = (stats.three_star_count / total * 100) if total > 0 else 0.0
    two_pct = (stats.two_star_count / total * 100) if total > 0 else 0.0
    one_pct = (stats.one_star_count / total * 100) if total > 0 else 0.0

    return ReviewStatisticsDTO(
        product_sku=product_sku,
        product_name=product_name,
        total_reviews=total,
        average_rating=float(stats.average_rating),
        five_star_count=stats.five_star_count,
        four_star_count=stats.four_star_count,
        three_star_count=stats.three_star_count,
        two_star_count=stats.two_star_count,
        one_star_count=stats.one_star_count,
        five_star_percentage=five_pct,
        four_star_percentage=four_pct,
        three_star_percentage=three_pct,
        two_star_percentage=two_pct,
        one_star_percentage=one_pct,
        positive_percentage=float(stats.get_positive_percentage()) if hasattr(stats, 'get_positive_percentage') else 0.0,
        negative_percentage=float(stats.get_negative_percentage()) if hasattr(stats, 'get_negative_percentage') else 0.0,
        verified_purchase_percentage=float(stats.get_verified_purchase_percentage()) if hasattr(stats, 'get_verified_purchase_percentage') else 0.0,
        total_helpful_votes=stats.total_helpful_votes if hasattr(stats, 'total_helpful_votes') else 0
    )


# ============================================================================
# AI & Conversation V2 DTOs (DDD - AI Conversation Context - BASIC CHAT ONLY)
# ============================================================================

class QuickReplyDTO(BaseModel):
    """Quick reply option DTO"""
    reply_id: str
    reply_text: str
    reply_value: str


class MessageContentDTO(BaseModel):
    """Message content DTO"""
    text: str
    message_type: str = "text"  # text, image, file, quick_reply
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    has_media: bool = False


class ParticipantInfoDTO(BaseModel):
    """Participant information DTO"""
    participant_id: str
    participant_role: str  # customer, agent, system
    display_name: str
    email: Optional[str] = None
    department: Optional[str] = None
    is_customer: bool = False
    is_agent: bool = False


class ChatMessageDTO(BaseModel):
    """Individual chat message DTO"""
    id: str
    content: MessageContentDTO
    sender: ParticipantInfoDTO
    sent_at: str
    delivered_at: Optional[str] = None
    read_at: Optional[str] = None
    quick_replies: List[QuickReplyDTO] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_from_customer: bool = False
    is_from_agent: bool = False


class ConversationSummaryDTO(BaseModel):
    """Conversation summary DTO"""
    total_messages: int
    customer_messages: int
    agent_messages: int
    duration_minutes: int
    satisfaction_rating: Optional[str] = None
    satisfaction_comment: Optional[str] = None
    was_resolved: bool = False
    resolution_time_minutes: Optional[int] = None
    average_response_time: Optional[float] = None


class ChatConversationDTO(BaseModel):
    """Chat conversation aggregate DTO"""
    id: str
    customer_id: str
    store_id: str
    tenant_id: str
    status: str  # active, waiting, resolved, closed, abandoned
    customer: ParticipantInfoDTO
    assigned_agent: Optional[ParticipantInfoDTO] = None
    messages: List[ChatMessageDTO] = Field(default_factory=list)
    subject: Optional[str] = None
    category: Optional[str] = None
    satisfaction_rating: Optional[str] = None
    satisfaction_comment: Optional[str] = None
    created_at: str
    updated_at: str
    first_response_at: Optional[str] = None
    resolved_at: Optional[str] = None
    closed_at: Optional[str] = None
    duration_minutes: int = 0
    response_time_minutes: Optional[int] = None
    summary: Optional[ConversationSummaryDTO] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    events: List[str] = Field(default_factory=list)


class ConversationListDTO(BaseModel):
    """Paginated conversation list DTO"""
    conversations: List[ChatConversationDTO]
    total: int
    page: int
    page_size: int
    has_more: bool


# Request DTOs

class StartConversationRequest(BaseModel):
    """Request to start conversation"""
    store_id: str
    customer_id: str
    customer_name: str
    initial_message: str = Field(..., max_length=5000)
    subject: Optional[str] = None
    category: Optional[str] = None


class AddMessageRequest(BaseModel):
    """Request to add message"""
    message_text: str = Field(..., max_length=5000)
    sender_id: str
    sender_name: str
    sender_role: str = "customer"  # customer, agent, system
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    quick_replies: Optional[List[Dict[str, str]]] = None


class AssignAgentRequest(BaseModel):
    """Request to assign agent"""
    agent_id: str
    agent_name: str
    agent_email: Optional[str] = None
    department: Optional[str] = None


class ResolveConversationRequest(BaseModel):
    """Request to resolve conversation"""
    resolved_by: str


class SatisfactionRatingRequest(BaseModel):
    """Request to add satisfaction rating"""
    rating: str  # very_satisfied, satisfied, neutral, dissatisfied, very_dissatisfied
    comment: Optional[str] = Field(None, max_length=1000)


# ============================================================================
# AI & Conversation V2 Mappers
# ============================================================================

def map_quick_reply_to_dto(quick_reply) -> QuickReplyDTO:
    """Convert QuickReply value object to DTO"""
    if isinstance(quick_reply, dict):
        return QuickReplyDTO(
            reply_id=quick_reply.get('reply_id', ''),
            reply_text=quick_reply.get('reply_text', ''),
            reply_value=quick_reply.get('reply_value', '')
        )

    return QuickReplyDTO(
        reply_id=quick_reply.reply_id,
        reply_text=quick_reply.reply_text,
        reply_value=quick_reply.reply_value
    )


def map_message_content_to_dto(content) -> MessageContentDTO:
    """Convert MessageContent value object to DTO"""
    if isinstance(content, dict):
        return MessageContentDTO(
            text=content.get('text', ''),
            message_type=content.get('message_type', 'text'),
            media_url=content.get('media_url'),
            media_type=content.get('media_type'),
            has_media=bool(content.get('media_url'))
        )

    return MessageContentDTO(
        text=content.text,
        message_type=content.message_type.value if hasattr(content.message_type, 'value') else str(content.message_type),
        media_url=content.media_url,
        media_type=content.media_type,
        has_media=content.has_media() if hasattr(content, 'has_media') else bool(content.media_url)
    )


def map_participant_info_to_dto(participant) -> ParticipantInfoDTO:
    """Convert ParticipantInfo value object to DTO"""
    if isinstance(participant, dict):
        role = participant.get('participant_role', 'customer')
        return ParticipantInfoDTO(
            participant_id=participant.get('participant_id', ''),
            participant_role=role,
            display_name=participant.get('display_name', 'Anonymous'),
            email=participant.get('email'),
            department=participant.get('department'),
            is_customer=(role == 'customer'),
            is_agent=(role == 'agent')
        )

    role_value = participant.participant_role.value if hasattr(participant.participant_role, 'value') else str(participant.participant_role)

    return ParticipantInfoDTO(
        participant_id=participant.participant_id,
        participant_role=role_value,
        display_name=participant.display_name,
        email=participant.email,
        department=participant.department,
        is_customer=participant.is_customer() if hasattr(participant, 'is_customer') else (role_value == 'customer'),
        is_agent=participant.is_agent() if hasattr(participant, 'is_agent') else (role_value == 'agent')
    )


def map_chat_message_to_dto(message) -> ChatMessageDTO:
    """Convert ChatMessage entity to DTO"""
    if isinstance(message, dict):
        content_data = message.get('content', {})
        sender_data = message.get('sender', {})

        content = MessageContentDTO(
            text=content_data.get('text', ''),
            message_type=content_data.get('message_type', 'text'),
            media_url=content_data.get('media_url'),
            media_type=content_data.get('media_type'),
            has_media=bool(content_data.get('media_url'))
        )

        sender = ParticipantInfoDTO(
            participant_id=sender_data.get('participant_id', ''),
            participant_role=sender_data.get('participant_role', 'customer'),
            display_name=sender_data.get('display_name', 'Anonymous'),
            email=sender_data.get('email'),
            department=sender_data.get('department'),
            is_customer=(sender_data.get('participant_role') == 'customer'),
            is_agent=(sender_data.get('participant_role') == 'agent')
        )

        quick_replies = []
        if message.get('quick_replies'):
            quick_replies = [
                QuickReplyDTO(**qr) if isinstance(qr, dict) else map_quick_reply_to_dto(qr)
                for qr in message['quick_replies']
            ]

        return ChatMessageDTO(
            id=str(message.get('id', '')),
            content=content,
            sender=sender,
            sent_at=message.get('sent_at', ''),
            delivered_at=message.get('delivered_at'),
            read_at=message.get('read_at'),
            quick_replies=quick_replies,
            metadata=message.get('metadata', {}),
            is_from_customer=(sender_data.get('participant_role') == 'customer'),
            is_from_agent=(sender_data.get('participant_role') == 'agent')
        )

    return ChatMessageDTO(
        id=str(message.id),
        content=map_message_content_to_dto(message.content),
        sender=map_participant_info_to_dto(message.sender),
        sent_at=message.sent_at.isoformat() if hasattr(message, 'sent_at') and message.sent_at else '',
        delivered_at=message.delivered_at.isoformat() if hasattr(message, 'delivered_at') and message.delivered_at else None,
        read_at=message.read_at.isoformat() if hasattr(message, 'read_at') and message.read_at else None,
        quick_replies=[map_quick_reply_to_dto(qr) for qr in message.quick_replies],
        metadata=message.metadata,
        is_from_customer=message.is_from_customer() if hasattr(message, 'is_from_customer') else False,
        is_from_agent=message.is_from_agent() if hasattr(message, 'is_from_agent') else False
    )


def map_conversation_summary_to_dto(summary) -> ConversationSummaryDTO:
    """Convert ConversationSummary value object to DTO"""
    if isinstance(summary, dict):
        return ConversationSummaryDTO(
            total_messages=summary.get('total_messages', 0),
            customer_messages=summary.get('customer_messages', 0),
            agent_messages=summary.get('agent_messages', 0),
            duration_minutes=summary.get('duration_minutes', 0),
            satisfaction_rating=summary.get('satisfaction_rating'),
            satisfaction_comment=summary.get('satisfaction_comment'),
            was_resolved=summary.get('was_resolved', False),
            resolution_time_minutes=summary.get('resolution_time_minutes'),
            average_response_time=summary.get('average_response_time')
        )

    return ConversationSummaryDTO(
        total_messages=summary.total_messages,
        customer_messages=summary.customer_messages,
        agent_messages=summary.agent_messages,
        duration_minutes=summary.duration_minutes,
        satisfaction_rating=summary.satisfaction_rating.value if hasattr(summary.satisfaction_rating, 'value') else summary.satisfaction_rating,
        satisfaction_comment=summary.satisfaction_comment,
        was_resolved=summary.was_resolved,
        resolution_time_minutes=summary.resolution_time_minutes,
        average_response_time=summary.get_average_response_time() if hasattr(summary, 'get_average_response_time') else None
    )


def map_chat_conversation_to_dto(conversation) -> ChatConversationDTO:
    """Convert ChatConversation aggregate to DTO with dual input handling"""
    if isinstance(conversation, dict):
        # Handle dict input (from database)
        customer_data = conversation.get('customer', {})
        agent_data = conversation.get('assigned_agent')

        customer = ParticipantInfoDTO(
            participant_id=customer_data.get('participant_id', ''),
            participant_role=customer_data.get('participant_role', 'customer'),
            display_name=customer_data.get('display_name', 'Anonymous'),
            email=customer_data.get('email'),
            department=customer_data.get('department'),
            is_customer=True,
            is_agent=False
        )

        assigned_agent = None
        if agent_data:
            assigned_agent = ParticipantInfoDTO(
                participant_id=agent_data.get('participant_id', ''),
                participant_role=agent_data.get('participant_role', 'agent'),
                display_name=agent_data.get('display_name', 'Agent'),
                email=agent_data.get('email'),
                department=agent_data.get('department'),
                is_customer=False,
                is_agent=True
            )

        messages = []
        if conversation.get('messages'):
            messages = [map_chat_message_to_dto(m) for m in conversation['messages']]

        summary = None
        if conversation.get('summary'):
            summary = map_conversation_summary_to_dto(conversation['summary'])

        return ChatConversationDTO(
            id=str(conversation.get('id', '')),
            customer_id=conversation.get('customer_id', ''),
            store_id=str(conversation.get('store_id', '')),
            tenant_id=str(conversation.get('tenant_id', '')),
            status=conversation.get('status', 'active'),
            customer=customer,
            assigned_agent=assigned_agent,
            messages=messages,
            subject=conversation.get('subject'),
            category=conversation.get('category'),
            satisfaction_rating=conversation.get('satisfaction_rating'),
            satisfaction_comment=conversation.get('satisfaction_comment'),
            created_at=conversation.get('created_at', ''),
            updated_at=conversation.get('updated_at', ''),
            first_response_at=conversation.get('first_response_at'),
            resolved_at=conversation.get('resolved_at'),
            closed_at=conversation.get('closed_at'),
            duration_minutes=conversation.get('duration_minutes', 0),
            response_time_minutes=conversation.get('response_time_minutes'),
            summary=summary,
            metadata=conversation.get('metadata', {}),
            events=conversation.get('events', [])
        )

    # Handle domain object
    return ChatConversationDTO(
        id=str(conversation.id),
        customer_id=conversation.customer_id,
        store_id=str(conversation.store_id),
        tenant_id=str(conversation.tenant_id),
        status=conversation.status.value if hasattr(conversation.status, 'value') else str(conversation.status),
        customer=map_participant_info_to_dto(conversation.customer),
        assigned_agent=map_participant_info_to_dto(conversation.assigned_agent) if conversation.assigned_agent else None,
        messages=[map_chat_message_to_dto(m) for m in conversation.messages],
        subject=conversation.subject,
        category=conversation.category,
        satisfaction_rating=conversation.satisfaction_rating.value if hasattr(conversation.satisfaction_rating, 'value') else conversation.satisfaction_rating,
        satisfaction_comment=conversation.satisfaction_comment,
        created_at=conversation.created_at.isoformat() if hasattr(conversation, 'created_at') else '',
        updated_at=conversation.updated_at.isoformat() if hasattr(conversation, 'updated_at') else '',
        first_response_at=conversation.first_response_at.isoformat() if hasattr(conversation, 'first_response_at') and conversation.first_response_at else None,
        resolved_at=conversation.resolved_at.isoformat() if hasattr(conversation, 'resolved_at') and conversation.resolved_at else None,
        closed_at=conversation.closed_at.isoformat() if hasattr(conversation, 'closed_at') and conversation.closed_at else None,
        duration_minutes=conversation.get_duration_minutes() if hasattr(conversation, 'get_duration_minutes') else 0,
        response_time_minutes=conversation.get_response_time_minutes() if hasattr(conversation, 'get_response_time_minutes') else None,
        summary=map_conversation_summary_to_dto(conversation.get_summary()) if hasattr(conversation, 'get_summary') else None,
        metadata=conversation.metadata,
        events=[type(event).__name__ for event in conversation.domain_events]
    )


# ============================================================================
# Localization V2 DTOs and Mappers (Phase 11)
# ============================================================================

# Response DTOs
class TranslationKeyDTO(BaseModel):
    """Translation key value object DTO"""
    namespace: str = Field(..., description="Namespace (e.g., 'product', 'ui', 'email')")
    key: str = Field(..., description="Key within namespace")
    full_key: str = Field(..., description="Full key in dot notation (namespace.key)")

    class Config:
        json_schema_extra = {
            "example": {
                "namespace": "product",
                "key": "add_to_cart",
                "full_key": "product.add_to_cart"
            }
        }


class LocalizedTextDTO(BaseModel):
    """Localized text value object DTO"""
    language_code: str = Field(..., description="Language code (en, fr, es, pt, zh)")
    text: str = Field(..., description="Translated text")
    text_plural: Optional[str] = Field(None, description="Plural form (optional)")

    class Config:
        json_schema_extra = {
            "example": {
                "language_code": "en",
                "text": "Add to Cart",
                "text_plural": None
            }
        }


class TranslationDTO(BaseModel):
    """Translation aggregate DTO"""
    id: str
    translation_key: TranslationKeyDTO
    source_language: str = Field(..., description="Source language code")
    source_text: str = Field(..., description="Original text")
    translations: Dict[str, LocalizedTextDTO] = Field(
        default_factory=dict,
        description="Translations by language code"
    )
    status: str = Field(..., description="Translation status (draft, pending_review, approved, published, deprecated)")
    description: Optional[str] = Field(None, description="What this translation is for")
    context: Optional[str] = Field(None, description="Usage context")
    max_length: Optional[int] = Field(None, description="Character limit for UI strings")
    completion_percentage: float = Field(..., description="Completion percentage (0-100)")
    is_complete: bool = Field(..., description="All languages translated")
    supported_languages: List[str] = Field(default_factory=list, description="Languages with translations")
    created_at: str
    updated_at: str
    published_at: Optional[str] = None
    created_by: Optional[str] = None
    last_translated_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    events: List[str] = Field(default_factory=list, description="Domain events")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "translation_key": {
                    "namespace": "product",
                    "key": "add_to_cart",
                    "full_key": "product.add_to_cart"
                },
                "source_language": "en",
                "source_text": "Add to Cart",
                "translations": {
                    "en": {"language_code": "en", "text": "Add to Cart", "text_plural": None},
                    "fr": {"language_code": "fr", "text": "Ajouter au panier", "text_plural": None}
                },
                "status": "published",
                "completion_percentage": 40.0,
                "is_complete": False,
                "supported_languages": ["en", "fr"]
            }
        }


class TranslationStatsDTO(BaseModel):
    """Translation statistics DTO"""
    total_translations: int
    completed_translations: int
    draft_translations: int
    published_translations: int
    average_completion: float = Field(..., description="Average completion percentage")
    languages_coverage: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of translations per language"
    )


class TranslationListDTO(BaseModel):
    """Paginated translation list DTO"""
    translations: List[TranslationDTO]
    total: int
    page: int
    page_size: int
    has_more: bool


# Request DTOs
class CreateTranslationRequest(BaseModel):
    """Request to create new translation"""
    namespace: str = Field(..., description="Namespace (e.g., 'product', 'ui')")
    key: str = Field(..., description="Key within namespace")
    source_text: str = Field(..., max_length=10000, description="Source text")
    source_language: str = Field(default="en", description="Source language code")
    description: Optional[str] = Field(None, description="What this translation is for")
    context: Optional[str] = Field(None, description="Usage context")
    max_length: Optional[int] = Field(None, description="Character limit")

    class Config:
        json_schema_extra = {
            "example": {
                "namespace": "product",
                "key": "add_to_cart",
                "source_text": "Add to Cart",
                "source_language": "en",
                "description": "Product page add to cart button",
                "max_length": 50
            }
        }


class AddTranslationRequest(BaseModel):
    """Request to add language translation"""
    language_code: str = Field(..., description="Language code (en, fr, es, pt, zh)")
    text: str = Field(..., max_length=10000, description="Translated text")
    text_plural: Optional[str] = Field(None, max_length=10000, description="Plural form")
    translated_by: Optional[str] = Field(None, description="Translator user ID")

    class Config:
        json_schema_extra = {
            "example": {
                "language_code": "fr",
                "text": "Ajouter au panier",
                "text_plural": None
            }
        }


class UpdateTranslationRequest(BaseModel):
    """Request to update translation"""
    source_text: Optional[str] = Field(None, max_length=10000)
    description: Optional[str] = None
    context: Optional[str] = None
    max_length: Optional[int] = None


class BulkTranslationRequest(BaseModel):
    """Request for bulk translation operations"""
    translation_ids: List[str] = Field(..., description="Translation IDs to operate on")
    action: str = Field(..., description="Action: publish, deprecate, delete")


# Mapper functions
def map_translation_key_to_dto(translation_key) -> TranslationKeyDTO:
    """Convert TranslationKey value object to DTO"""
    if isinstance(translation_key, dict):
        return TranslationKeyDTO(
            namespace=translation_key.get('namespace', ''),
            key=translation_key.get('key', ''),
            full_key=translation_key.get('full_key', f"{translation_key.get('namespace', '')}.{translation_key.get('key', '')}")
        )

    # Handle domain object
    return TranslationKeyDTO(
        namespace=translation_key.namespace,
        key=translation_key.key,
        full_key=translation_key.get_full_key() if hasattr(translation_key, 'get_full_key') else f"{translation_key.namespace}.{translation_key.key}"
    )


def map_localized_text_to_dto(localized_text) -> LocalizedTextDTO:
    """Convert LocalizedText value object to DTO"""
    if isinstance(localized_text, dict):
        return LocalizedTextDTO(
            language_code=localized_text.get('language_code', ''),
            text=localized_text.get('text', ''),
            text_plural=localized_text.get('text_plural')
        )

    # Handle domain object
    language_code = localized_text.language_code
    if hasattr(language_code, 'value'):
        language_code = language_code.value

    return LocalizedTextDTO(
        language_code=str(language_code),
        text=localized_text.text,
        text_plural=localized_text.text_plural
    )


def map_translation_to_dto(translation) -> TranslationDTO:
    """Convert Translation aggregate to DTO - handles both domain objects and dicts"""
    if isinstance(translation, dict):
        # Handle dict input from database
        translation_key = map_translation_key_to_dto(translation.get('translation_key', {}))

        translations_dict = {}
        for lang_code, localized in translation.get('translations', {}).items():
            translations_dict[lang_code] = map_localized_text_to_dto(localized)

        supported_languages = list(translation.get('translations', {}).keys())
        total_languages = 5  # EN, FR, ES, PT, ZH
        completion = (len(supported_languages) / total_languages) * 100 if supported_languages else 0

        return TranslationDTO(
            id=str(translation.get('id', '')),
            translation_key=translation_key,
            source_language=translation.get('source_language', 'en'),
            source_text=translation.get('source_text', ''),
            translations=translations_dict,
            status=translation.get('status', 'draft'),
            description=translation.get('description'),
            context=translation.get('context'),
            max_length=translation.get('max_length'),
            completion_percentage=completion,
            is_complete=len(supported_languages) == total_languages,
            supported_languages=supported_languages,
            created_at=translation.get('created_at', ''),
            updated_at=translation.get('updated_at', ''),
            published_at=translation.get('published_at'),
            created_by=str(translation['created_by']) if translation.get('created_by') else None,
            last_translated_by=str(translation['last_translated_by']) if translation.get('last_translated_by') else None,
            metadata=translation.get('metadata', {}),
            events=translation.get('events', [])
        )

    # Handle domain object
    translation_key = map_translation_key_to_dto(translation.translation_key)

    # Convert translations dict
    translations_dict = {}
    for lang_code, localized in translation.translations.items():
        lang_code_str = lang_code.value if hasattr(lang_code, 'value') else str(lang_code)
        translations_dict[lang_code_str] = map_localized_text_to_dto(localized)

    source_language = translation.source_language
    if hasattr(source_language, 'value'):
        source_language = source_language.value

    status = translation.status
    if hasattr(status, 'value'):
        status = status.value

    supported_languages = [
        lang.value if hasattr(lang, 'value') else str(lang)
        for lang in translation.get_supported_languages()
    ] if hasattr(translation, 'get_supported_languages') else list(translations_dict.keys())

    return TranslationDTO(
        id=str(translation.id),
        translation_key=translation_key,
        source_language=str(source_language),
        source_text=translation.source_text,
        translations=translations_dict,
        status=str(status),
        description=translation.description,
        context=translation.context,
        max_length=translation.max_length,
        completion_percentage=translation.get_completion_percentage() if hasattr(translation, 'get_completion_percentage') else 0,
        is_complete=translation.is_complete() if hasattr(translation, 'is_complete') else False,
        supported_languages=supported_languages,
        created_at=translation.created_at.isoformat() if hasattr(translation.created_at, 'isoformat') else str(translation.created_at),
        updated_at=translation.updated_at.isoformat() if hasattr(translation.updated_at, 'isoformat') else str(translation.updated_at),
        published_at=translation.published_at.isoformat() if translation.published_at and hasattr(translation.published_at, 'isoformat') else (str(translation.published_at) if translation.published_at else None),
        created_by=str(translation.created_by) if translation.created_by else None,
        last_translated_by=str(translation.last_translated_by) if translation.last_translated_by else None,
        metadata=translation.metadata,
        events=[type(event).__name__ for event in translation.domain_events]
    )


# ============================================================================
# Metadata Management V2 DTOs and Mappers (Phase 12)
# ============================================================================

# Response DTOs
class FieldDefinitionDTO(BaseModel):
    """Field definition value object DTO"""
    field_name: str = Field(..., description="Field name (alphanumeric with underscores)")
    field_label: str = Field(..., description="Human-readable label")
    data_type: str = Field(..., description="Data type (string, integer, decimal, boolean, date, datetime, json, list)")
    is_required: bool = Field(default=False, description="Is field required")
    default_value: Optional[Any] = Field(None, description="Default value")
    min_length: Optional[int] = Field(None, description="Minimum length (for strings)")
    max_length: Optional[int] = Field(None, description="Maximum length (for strings)")
    min_value: Optional[float] = Field(None, description="Minimum value (for numbers)")
    max_value: Optional[float] = Field(None, description="Maximum value (for numbers)")
    allowed_values: Optional[List[str]] = Field(None, description="Allowed values (for enum fields)")
    help_text: Optional[str] = Field(None, description="Help text for UI")
    placeholder: Optional[str] = Field(None, description="Placeholder text for UI")

    class Config:
        json_schema_extra = {
            "example": {
                "field_name": "customer_tier",
                "field_label": "Customer Tier",
                "data_type": "string",
                "is_required": False,
                "allowed_values": ["bronze", "silver", "gold", "platinum"],
                "help_text": "Customer loyalty tier"
            }
        }


class MetadataSchemaDTO(BaseModel):
    """Metadata schema aggregate DTO"""
    id: str
    schema_name: str = Field(..., description="Schema name")
    entity_type: str = Field(..., description="Entity type (product, customer, order, etc.)")
    description: Optional[str] = Field(None, description="Schema description")
    fields: List[FieldDefinitionDTO] = Field(default_factory=list, description="Field definitions")
    is_active: bool = Field(..., description="Schema is active")
    is_published: bool = Field(..., description="Schema is published")
    version: int = Field(..., description="Schema version")
    created_at: str
    updated_at: str
    published_at: Optional[str] = None
    created_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    events: List[str] = Field(default_factory=list, description="Domain events")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "schema_name": "customer_metadata",
                "entity_type": "customer",
                "description": "Custom fields for customers",
                "fields": [
                    {
                        "field_name": "loyalty_points",
                        "field_label": "Loyalty Points",
                        "data_type": "integer",
                        "is_required": False,
                        "min_value": 0
                    }
                ],
                "is_active": True,
                "is_published": True,
                "version": 1
            }
        }


class ValidationResultDTO(BaseModel):
    """Validation result DTO"""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    validated_values: Optional[Dict[str, Any]] = None


class SchemaListDTO(BaseModel):
    """Paginated schema list DTO"""
    schemas: List[MetadataSchemaDTO]
    total: int
    page: int
    page_size: int
    has_more: bool


# Request DTOs
class CreateSchemaRequest(BaseModel):
    """Request to create new schema"""
    schema_name: str = Field(..., description="Schema name")
    entity_type: str = Field(..., description="Entity type (product, customer, order, etc.)")
    description: Optional[str] = Field(None, description="Schema description")

    class Config:
        json_schema_extra = {
            "example": {
                "schema_name": "product_metadata",
                "entity_type": "product",
                "description": "Custom fields for products"
            }
        }


class AddFieldRequest(BaseModel):
    """Request to add field to schema"""
    field_name: str = Field(..., description="Field name")
    field_label: str = Field(..., description="Field label")
    data_type: str = Field(..., description="Data type")
    is_required: bool = Field(default=False)
    default_value: Optional[Any] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[str]] = None
    help_text: Optional[str] = None
    placeholder: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "field_name": "organic_certified",
                "field_label": "Organic Certified",
                "data_type": "boolean",
                "is_required": False,
                "help_text": "Is this product organic certified?"
            }
        }


class UpdateSchemaRequest(BaseModel):
    """Request to update schema metadata"""
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ValidateValuesRequest(BaseModel):
    """Request to validate values against schema"""
    values: Dict[str, Any] = Field(..., description="Values to validate")

    class Config:
        json_schema_extra = {
            "example": {
                "values": {
                    "loyalty_points": 1000,
                    "customer_tier": "gold"
                }
            }
        }


# Mapper functions
def map_field_definition_to_dto(field_def) -> FieldDefinitionDTO:
    """Convert FieldDefinition value object to DTO"""
    if isinstance(field_def, dict):
        return FieldDefinitionDTO(
            field_name=field_def.get('field_name', ''),
            field_label=field_def.get('field_label', ''),
            data_type=field_def.get('data_type', 'string'),
            is_required=field_def.get('is_required', False),
            default_value=field_def.get('default_value'),
            min_length=field_def.get('min_length'),
            max_length=field_def.get('max_length'),
            min_value=field_def.get('min_value'),
            max_value=field_def.get('max_value'),
            allowed_values=list(field_def.get('allowed_values', [])) if field_def.get('allowed_values') else None,
            help_text=field_def.get('help_text'),
            placeholder=field_def.get('placeholder')
        )

    # Handle domain object
    data_type = field_def.data_type
    if hasattr(data_type, 'value'):
        data_type = data_type.value

    allowed_values = None
    if field_def.allowed_values:
        allowed_values = list(field_def.allowed_values)

    return FieldDefinitionDTO(
        field_name=field_def.field_name,
        field_label=field_def.field_label,
        data_type=str(data_type),
        is_required=field_def.is_required,
        default_value=field_def.default_value,
        min_length=field_def.min_length,
        max_length=field_def.max_length,
        min_value=field_def.min_value,
        max_value=field_def.max_value,
        allowed_values=allowed_values,
        help_text=field_def.help_text,
        placeholder=field_def.placeholder
    )


def map_metadata_schema_to_dto(schema) -> MetadataSchemaDTO:
    """Convert MetadataSchema aggregate to DTO - handles both domain objects and dicts"""
    if isinstance(schema, dict):
        # Handle dict input from database
        fields = [map_field_definition_to_dto(f) for f in schema.get('fields', [])]

        return MetadataSchemaDTO(
            id=str(schema.get('id', '')),
            schema_name=schema.get('schema_name', ''),
            entity_type=schema.get('entity_type', ''),
            description=schema.get('description'),
            fields=fields,
            is_active=schema.get('is_active', True),
            is_published=schema.get('is_published', False),
            version=schema.get('version', 1),
            created_at=schema.get('created_at', ''),
            updated_at=schema.get('updated_at', ''),
            published_at=schema.get('published_at'),
            created_by=str(schema['created_by']) if schema.get('created_by') else None,
            metadata=schema.get('metadata', {}),
            events=schema.get('events', [])
        )

    # Handle domain object
    fields = [map_field_definition_to_dto(f) for f in schema.fields]

    return MetadataSchemaDTO(
        id=str(schema.id),
        schema_name=schema.schema_name,
        entity_type=schema.entity_type,
        description=schema.description,
        fields=fields,
        is_active=schema.is_active,
        is_published=schema.is_published,
        version=schema.version,
        created_at=schema.created_at.isoformat() if hasattr(schema.created_at, 'isoformat') else str(schema.created_at),
        updated_at=schema.updated_at.isoformat() if hasattr(schema.updated_at, 'isoformat') else str(schema.updated_at),
        published_at=schema.published_at.isoformat() if schema.published_at and hasattr(schema.published_at, 'isoformat') else (str(schema.published_at) if schema.published_at else None),
        created_by=str(schema.created_by) if schema.created_by else None,
        metadata=schema.metadata,
        events=[type(event).__name__ for event in schema.domain_events]
    )


# ============================================================================
# Purchase Order V2 DTOs and Mappers (Phase 13)
# ============================================================================

# Response DTOs
class OrderStatusTransitionDTO(BaseModel):
    """Status transition value object DTO"""
    from_status: str
    to_status: str
    transitioned_at: str
    transitioned_by: Optional[str] = None
    reason: Optional[str] = None


class ShippingMethodDTO(BaseModel):
    """Shipping method value object DTO"""
    carrier: str
    service_type: str = Field(..., description="ground, express, overnight, etc.")
    tracking_enabled: bool = True
    estimated_days: Optional[int] = None


class DeliveryScheduleDTO(BaseModel):
    """Delivery schedule value object DTO"""
    preferred_delivery_date: Optional[str] = None
    delivery_window_start: Optional[str] = None
    delivery_window_end: Optional[str] = None
    delivery_instructions: Optional[str] = None
    requires_appointment: bool = False


class PurchaseOrderDTO(BaseModel):
    """Purchase order aggregate DTO"""
    id: str
    order_number: str = Field(..., description="PO number (PO-YYYY-MM-XXXXX)")
    store_id: str
    tenant_id: str
    supplier_id: str
    supplier_name: str

    # Status
    status: str = Field(..., description="PO status (draft, submitted, approved, sent_to_supplier, confirmed, partially_received, fully_received, closed, cancelled)")
    approval_status: str = Field(..., description="Approval status (pending, approved, rejected)")

    # Dates
    order_date: str
    expected_delivery_date: Optional[str] = None
    actual_delivery_date: Optional[str] = None
    due_date: Optional[str] = None

    # Financial
    subtotal: str = Field(..., description="Subtotal amount")
    tax_amount: str = Field(..., description="Tax amount")
    shipping_cost: str = Field(..., description="Shipping cost")
    discount_amount: str = Field(..., description="Discount amount")
    total_amount: str = Field(..., description="Total amount")
    currency: str = "CAD"

    # Payment
    payment_terms: str = Field(..., description="Payment terms (net_15, net_30, etc.)")
    payment_method: Optional[str] = None
    prepaid_amount: str = Field(..., description="Prepaid amount")
    amount_due: str = Field(..., description="Amount due")

    # Shipping
    shipping_method: Optional[ShippingMethodDTO] = None
    delivery_schedule: Optional[DeliveryScheduleDTO] = None

    # Supplier contact
    supplier_contact: Optional[str] = None
    supplier_email: Optional[str] = None
    supplier_phone: Optional[str] = None
    supplier_order_number: Optional[str] = None

    # Tracking
    tracking_number: Optional[str] = None
    carrier_name: Optional[str] = None

    # Line items summary
    total_line_items: int = 0
    total_units_ordered: int = 0
    total_units_received: int = 0
    received_percentage: str = "0.00"

    # User tracking
    created_by: Optional[str] = None
    submitted_by: Optional[str] = None
    approved_by: Optional[str] = None
    received_by: Optional[str] = None
    cancelled_by: Optional[str] = None

    # Timestamps
    created_at: str
    updated_at: str
    submitted_at: Optional[str] = None
    approved_at: Optional[str] = None
    sent_at: Optional[str] = None
    confirmed_at: Optional[str] = None
    received_at: Optional[str] = None
    closed_at: Optional[str] = None
    cancelled_at: Optional[str] = None

    # Notes
    internal_notes: Optional[str] = None
    supplier_notes: Optional[str] = None
    receiving_notes: Optional[str] = None
    cancellation_reason: Optional[str] = None

    # Status history
    status_history: List[OrderStatusTransitionDTO] = Field(default_factory=list)

    # Flags
    is_overdue_for_delivery: bool = False
    is_payment_due: bool = False
    can_be_edited: bool = False
    requires_approval: bool = False

    # Metadata and events
    metadata: Dict[str, Any] = Field(default_factory=dict)
    events: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "order_number": "PO-2024-12-A1B2C",
                "store_id": "store-123",
                "supplier_id": "supplier-456",
                "supplier_name": "Premium Cannabis Suppliers Ltd.",
                "status": "approved",
                "approval_status": "approved",
                "total_amount": "5000.00",
                "currency": "CAD"
            }
        }


class PurchaseOrderListDTO(BaseModel):
    """Paginated purchase order list DTO"""
    purchase_orders: List[PurchaseOrderDTO]
    total: int
    page: int
    page_size: int
    has_more: bool


class PurchaseOrderStatsDTO(BaseModel):
    """Purchase order statistics DTO"""
    total_orders: int
    draft_orders: int
    pending_approval: int
    approved_orders: int
    in_transit: int
    partially_received: int
    fully_received: int
    total_value: str = Field(..., description="Total value of all orders")
    avg_order_value: str = Field(..., description="Average order value")
    overdue_deliveries: int


# Request DTOs
class CreatePurchaseOrderRequest(BaseModel):
    """Request to create new purchase order"""
    store_id: str
    supplier_id: str
    supplier_name: str
    payment_terms: str = Field(default="net_30", description="Payment terms")
    expected_delivery_date: Optional[str] = None
    internal_notes: Optional[str] = None
    supplier_notes: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "store_id": "store-123",
                "supplier_id": "supplier-456",
                "supplier_name": "Premium Cannabis Suppliers Ltd.",
                "payment_terms": "net_30",
                "expected_delivery_date": "2024-12-31T00:00:00Z"
            }
        }


class AddLineItemRequest(BaseModel):
    """Request to add line item"""
    quantity: int = Field(..., gt=0, description="Quantity to order")
    unit_price: str = Field(..., description="Unit price")

    class Config:
        json_schema_extra = {
            "example": {
                "quantity": 100,
                "unit_price": "25.50"
            }
        }


class SetFinancialDetailsRequest(BaseModel):
    """Request to set financial details"""
    tax_amount: Optional[str] = None
    shipping_cost: Optional[str] = None
    discount_amount: Optional[str] = None


class SetDeliveryDetailsRequest(BaseModel):
    """Request to set delivery details"""
    expected_delivery_date: Optional[str] = None
    carrier: Optional[str] = None
    service_type: Optional[str] = None
    tracking_enabled: bool = True
    estimated_days: Optional[int] = None
    delivery_instructions: Optional[str] = None
    requires_appointment: bool = False


class SubmitPurchaseOrderRequest(BaseModel):
    """Request to submit purchase order for approval"""
    pass  # No additional data needed, submitted_by from auth


class ApprovePurchaseOrderRequest(BaseModel):
    """Request to approve purchase order"""
    pass  # No additional data needed, approved_by from auth


class RejectPurchaseOrderRequest(BaseModel):
    """Request to reject purchase order"""
    reason: str = Field(..., description="Reason for rejection")


class SendToSupplierRequest(BaseModel):
    """Request to send PO to supplier"""
    pass  # No additional data needed


class ConfirmBySupplierRequest(BaseModel):
    """Request to confirm receipt by supplier"""
    supplier_order_number: Optional[str] = Field(None, description="Supplier's order reference")


# NOTE: V2 receive endpoint DTOs removed - use V1 /api/inventory/purchase-orders/{po_id}/receive
# V1 already uses full DDD implementation, no need for duplicate V2 DTOs

class CancelPurchaseOrderRequest(BaseModel):
    """Request to cancel purchase order"""
    reason: str = Field(..., description="Cancellation reason")


class AddTrackingInfoRequest(BaseModel):
    """Request to add tracking information"""
    tracking_number: str = Field(..., description="Tracking number")
    carrier: Optional[str] = Field(None, description="Carrier name")


# Mapper functions
def map_shipping_method_to_dto(shipping_method) -> Optional[ShippingMethodDTO]:
    """Convert ShippingMethod value object to DTO"""
    if not shipping_method:
        return None

    if isinstance(shipping_method, dict):
        return ShippingMethodDTO(
            carrier=shipping_method.get('carrier', ''),
            service_type=shipping_method.get('service_type', ''),
            tracking_enabled=shipping_method.get('tracking_enabled', True),
            estimated_days=shipping_method.get('estimated_days')
        )

    # Handle domain object
    return ShippingMethodDTO(
        carrier=shipping_method.carrier,
        service_type=shipping_method.service_type,
        tracking_enabled=shipping_method.tracking_enabled,
        estimated_days=shipping_method.estimated_days
    )


def map_delivery_schedule_to_dto(delivery_schedule) -> Optional[DeliveryScheduleDTO]:
    """Convert DeliverySchedule value object to DTO"""
    if not delivery_schedule:
        return None

    if isinstance(delivery_schedule, dict):
        return DeliveryScheduleDTO(
            preferred_delivery_date=delivery_schedule.get('preferred_delivery_date'),
            delivery_window_start=delivery_schedule.get('delivery_window_start'),
            delivery_window_end=delivery_schedule.get('delivery_window_end'),
            delivery_instructions=delivery_schedule.get('delivery_instructions'),
            requires_appointment=delivery_schedule.get('requires_appointment', False)
        )

    # Handle domain object
    return DeliveryScheduleDTO(
        preferred_delivery_date=delivery_schedule.preferred_delivery_date.isoformat() if delivery_schedule.preferred_delivery_date else None,
        delivery_window_start=delivery_schedule.delivery_window_start.isoformat() if delivery_schedule.delivery_window_start else None,
        delivery_window_end=delivery_schedule.delivery_window_end.isoformat() if delivery_schedule.delivery_window_end else None,
        delivery_instructions=delivery_schedule.delivery_instructions,
        requires_appointment=delivery_schedule.requires_appointment
    )


def map_status_transition_to_dto(transition) -> OrderStatusTransitionDTO:
    """Convert OrderStatusTransition value object to DTO"""
    if isinstance(transition, dict):
        return OrderStatusTransitionDTO(
            from_status=transition.get('from_status', ''),
            to_status=transition.get('to_status', ''),
            transitioned_at=transition.get('transitioned_at', ''),
            transitioned_by=transition.get('transitioned_by'),
            reason=transition.get('reason')
        )

    # Handle domain object
    from_status = transition.from_status.value if hasattr(transition.from_status, 'value') else str(transition.from_status)
    to_status = transition.to_status.value if hasattr(transition.to_status, 'value') else str(transition.to_status)

    return OrderStatusTransitionDTO(
        from_status=from_status,
        to_status=to_status,
        transitioned_at=transition.transitioned_at.isoformat() if hasattr(transition.transitioned_at, 'isoformat') else str(transition.transitioned_at),
        transitioned_by=transition.transitioned_by,
        reason=transition.reason
    )


def map_purchase_order_to_dto(po) -> PurchaseOrderDTO:
    """Convert PurchaseOrder aggregate to DTO - handles both domain objects and dicts"""
    if isinstance(po, dict):
        # Handle dict input from database
        status_history = [map_status_transition_to_dto(t) for t in po.get('status_history', [])]

        return PurchaseOrderDTO(
            id=str(po.get('id', '')),
            order_number=po.get('order_number', ''),
            store_id=str(po.get('store_id', '')),
            tenant_id=str(po.get('tenant_id', '')),
            supplier_id=str(po.get('supplier_id', '')),
            supplier_name=po.get('supplier_name', ''),
            status=po.get('status', 'draft'),
            approval_status=po.get('approval_status', 'pending'),
            order_date=po.get('order_date', ''),
            expected_delivery_date=po.get('expected_delivery_date'),
            actual_delivery_date=po.get('actual_delivery_date'),
            due_date=po.get('due_date'),
            subtotal=str(po.get('subtotal', '0')),
            tax_amount=str(po.get('tax_amount', '0')),
            shipping_cost=str(po.get('shipping_cost', '0')),
            discount_amount=str(po.get('discount_amount', '0')),
            total_amount=str(po.get('total_amount', '0')),
            currency=po.get('currency', 'CAD'),
            payment_terms=po.get('payment_terms', 'net_30'),
            payment_method=po.get('payment_method'),
            prepaid_amount=str(po.get('prepaid_amount', '0')),
            amount_due=str(po.get('amount_due', '0')),
            shipping_method=map_shipping_method_to_dto(po.get('shipping_method')),
            delivery_schedule=map_delivery_schedule_to_dto(po.get('delivery_schedule')),
            supplier_contact=po.get('supplier_contact'),
            supplier_email=po.get('supplier_email'),
            supplier_phone=po.get('supplier_phone'),
            supplier_order_number=po.get('supplier_order_number'),
            tracking_number=po.get('tracking_number'),
            carrier_name=po.get('carrier_name'),
            total_line_items=po.get('total_line_items', 0),
            total_units_ordered=po.get('total_units_ordered', 0),
            total_units_received=po.get('total_units_received', 0),
            received_percentage=str(po.get('received_percentage', '0.00')),
            created_by=str(po['created_by']) if po.get('created_by') else None,
            submitted_by=str(po['submitted_by']) if po.get('submitted_by') else None,
            approved_by=str(po['approved_by']) if po.get('approved_by') else None,
            received_by=str(po['received_by']) if po.get('received_by') else None,
            cancelled_by=str(po['cancelled_by']) if po.get('cancelled_by') else None,
            created_at=po.get('created_at', ''),
            updated_at=po.get('updated_at', ''),
            submitted_at=po.get('submitted_at'),
            approved_at=po.get('approved_at'),
            sent_at=po.get('sent_at'),
            confirmed_at=po.get('confirmed_at'),
            received_at=po.get('received_at'),
            closed_at=po.get('closed_at'),
            cancelled_at=po.get('cancelled_at'),
            internal_notes=po.get('internal_notes'),
            supplier_notes=po.get('supplier_notes'),
            receiving_notes=po.get('receiving_notes'),
            cancellation_reason=po.get('cancellation_reason'),
            status_history=status_history,
            is_overdue_for_delivery=po.get('is_overdue_for_delivery', False),
            is_payment_due=po.get('is_payment_due', False),
            can_be_edited=po.get('can_be_edited', False),
            requires_approval=po.get('requires_approval', False),
            metadata=po.get('metadata', {}),
            events=po.get('events', [])
        )

    # Handle domain object
    status = po.status.value if hasattr(po.status, 'value') else str(po.status)
    approval_status = po.approval_status.value if hasattr(po.approval_status, 'value') else str(po.approval_status)
    payment_terms = po.payment_terms.value if hasattr(po.payment_terms, 'value') else str(po.payment_terms)

    status_history = [map_status_transition_to_dto(t) for t in po.status_history]

    return PurchaseOrderDTO(
        id=str(po.id),
        order_number=po.order_number,
        store_id=str(po.store_id),
        tenant_id=str(po.tenant_id),
        supplier_id=str(po.supplier_id),
        supplier_name=po.supplier_name,
        status=status,
        approval_status=approval_status,
        order_date=po.order_date.isoformat() if hasattr(po.order_date, 'isoformat') else str(po.order_date),
        expected_delivery_date=po.expected_delivery_date.isoformat() if po.expected_delivery_date and hasattr(po.expected_delivery_date, 'isoformat') else (str(po.expected_delivery_date) if po.expected_delivery_date else None),
        actual_delivery_date=po.actual_delivery_date.isoformat() if po.actual_delivery_date and hasattr(po.actual_delivery_date, 'isoformat') else (str(po.actual_delivery_date) if po.actual_delivery_date else None),
        due_date=po.due_date.isoformat() if po.due_date and hasattr(po.due_date, 'isoformat') else (str(po.due_date) if po.due_date else None),
        subtotal=str(po.subtotal),
        tax_amount=str(po.tax_amount),
        shipping_cost=str(po.shipping_cost),
        discount_amount=str(po.discount_amount),
        total_amount=str(po.total_amount),
        currency=po.currency,
        payment_terms=payment_terms,
        payment_method=po.payment_method,
        prepaid_amount=str(po.prepaid_amount),
        amount_due=str(po.amount_due),
        shipping_method=map_shipping_method_to_dto(po.shipping_method),
        delivery_schedule=map_delivery_schedule_to_dto(po.delivery_schedule),
        supplier_contact=po.supplier_contact,
        supplier_email=po.supplier_email,
        supplier_phone=po.supplier_phone,
        supplier_order_number=po.supplier_order_number,
        tracking_number=po.tracking_number,
        carrier_name=po.carrier_name,
        total_line_items=po.total_line_items,
        total_units_ordered=po.total_units_ordered,
        total_units_received=po.total_units_received,
        received_percentage=str(po.get_received_percentage()) if hasattr(po, 'get_received_percentage') else "0.00",
        created_by=str(po.created_by) if po.created_by else None,
        submitted_by=str(po.submitted_by) if po.submitted_by else None,
        approved_by=str(po.approved_by) if po.approved_by else None,
        received_by=str(po.received_by) if po.received_by else None,
        cancelled_by=str(po.cancelled_by) if po.cancelled_by else None,
        created_at=po.created_at.isoformat() if hasattr(po.created_at, 'isoformat') else str(po.created_at),
        updated_at=po.updated_at.isoformat() if hasattr(po.updated_at, 'isoformat') else str(po.updated_at),
        submitted_at=po.submitted_at.isoformat() if po.submitted_at and hasattr(po.submitted_at, 'isoformat') else (str(po.submitted_at) if po.submitted_at else None),
        approved_at=po.approved_at.isoformat() if po.approved_at and hasattr(po.approved_at, 'isoformat') else (str(po.approved_at) if po.approved_at else None),
        sent_at=po.sent_at.isoformat() if po.sent_at and hasattr(po.sent_at, 'isoformat') else (str(po.sent_at) if po.sent_at else None),
        confirmed_at=po.confirmed_at.isoformat() if po.confirmed_at and hasattr(po.confirmed_at, 'isoformat') else (str(po.confirmed_at) if po.confirmed_at else None),
        received_at=po.received_at.isoformat() if po.received_at and hasattr(po.received_at, 'isoformat') else (str(po.received_at) if po.received_at else None),
        closed_at=po.closed_at.isoformat() if po.closed_at and hasattr(po.closed_at, 'isoformat') else (str(po.closed_at) if po.closed_at else None),
        cancelled_at=po.cancelled_at.isoformat() if po.cancelled_at and hasattr(po.cancelled_at, 'isoformat') else (str(po.cancelled_at) if po.cancelled_at else None),
        internal_notes=po.internal_notes,
        supplier_notes=po.supplier_notes,
        receiving_notes=po.receiving_notes,
        cancellation_reason=po.cancellation_reason,
        status_history=status_history,
        is_overdue_for_delivery=po.is_overdue_for_delivery() if hasattr(po, 'is_overdue_for_delivery') else False,
        is_payment_due=po.is_payment_due() if hasattr(po, 'is_payment_due') else False,
        can_be_edited=po.can_be_edited() if hasattr(po, 'can_be_edited') else False,
        requires_approval=po.requires_approval() if hasattr(po, 'requires_approval') else False,
        metadata=po.metadata,
        events=[type(event).__name__ for event in po.domain_events]
    )


# ============================================================================
# Phase 14: Identity & Access V2 DTOs
# ============================================================================

# Response DTOs
class VerificationStatusDTO(BaseModel):
    """Verification status for user account"""
    email_verified: bool
    email_verified_at: Optional[str] = None
    phone_verified: bool
    phone_verified_at: Optional[str] = None
    age_verified: bool
    age_verified_at: Optional[str] = None
    is_fully_verified: bool


class AccountSecurityDTO(BaseModel):
    """Account security information"""
    two_factor_enabled: bool
    failed_login_attempts: int
    last_failed_login: Optional[str] = None
    account_locked_until: Optional[str] = None
    is_account_locked: bool
    last_login_at: Optional[str] = None
    last_login_ip: Optional[str] = None
    login_count: int


class PasswordPolicyDTO(BaseModel):
    """Password policy configuration"""
    min_length: int
    require_uppercase: bool
    require_lowercase: bool
    require_digit: bool
    require_special: bool
    allowed_special_chars: str


class UserDTO(BaseModel):
    """Complete user details"""
    id: str
    email: str
    phone: Optional[str] = None
    username: Optional[str] = None
    user_type: str
    status: str
    auth_provider: str
    provider_user_id: Optional[str] = None

    # Personal Information
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: str
    display_name: str
    date_of_birth: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None

    # Verification
    verification: VerificationStatusDTO

    # Security
    security: AccountSecurityDTO

    # Permissions
    permissions: List[str]
    roles: List[str]

    # Activity
    last_activity_at: Optional[str] = None

    # Preferences
    language: str
    timezone: str
    currency: str
    notifications_enabled: bool
    marketing_emails_enabled: bool

    # Metadata
    metadata: Dict[str, Any]
    tags: List[str]

    # Flags
    can_make_purchase: bool
    is_active: bool

    # Timestamps
    created_at: str
    updated_at: str

    # Domain Events
    events: List[str]


class UserSummaryDTO(BaseModel):
    """Summary user information for lists"""
    id: str
    email: str
    phone: Optional[str] = None
    full_name: str
    display_name: str
    user_type: str
    status: str
    roles: List[str]
    email_verified: bool
    phone_verified: bool
    age_verified: bool
    last_login_at: Optional[str] = None
    created_at: str


class UserListDTO(BaseModel):
    """Paginated list of users"""
    users: List[UserSummaryDTO]
    total: int
    page: int
    page_size: int
    has_more: bool


class UserStatsDTO(BaseModel):
    """User statistics"""
    total_users: int
    active_users: int
    inactive_users: int
    suspended_users: int
    pending_users: int
    deleted_users: int
    users_with_2fa: int
    verified_users: int
    users_by_type: Dict[str, int]
    users_by_role: Dict[str, int]
    new_users_today: int
    new_users_this_week: int
    new_users_this_month: int


# Request DTOs
class RegisterUserRequest(BaseModel):
    """Register new user"""
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    user_type: str = "customer"
    date_of_birth: Optional[str] = None
    language: str = "en"
    timezone: str = "America/Toronto"
    marketing_emails_enabled: bool = False


class LoginRequest(BaseModel):
    """User login"""
    email: str
    password: str
    ip_address: Optional[str] = None
    two_factor_code: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    """Change user password"""
    current_password: str
    new_password: str


class UpdateProfileRequest(BaseModel):
    """Update user profile"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None


class UpdatePreferencesRequest(BaseModel):
    """Update user preferences"""
    language: Optional[str] = None
    timezone: Optional[str] = None
    currency: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    marketing_emails_enabled: Optional[bool] = None


class VerifyEmailRequest(BaseModel):
    """Verify email address"""
    verification_code: str


class VerifyPhoneRequest(BaseModel):
    """Verify phone number"""
    verification_code: str


class VerifyAgeRequest(BaseModel):
    """Verify user age (19+ for cannabis)"""
    date_of_birth: str


class Enable2FARequest(BaseModel):
    """Enable two-factor authentication"""
    password: str  # Verify password before enabling 2FA


class AssignRoleRequest(BaseModel):
    """Assign role to user"""
    role: str


class AssignPermissionRequest(BaseModel):
    """Assign permission to user"""
    permission: str


class SuspendUserRequest(BaseModel):
    """Suspend user account"""
    reason: str


class UpdateUserRequest(BaseModel):
    """Update user (admin endpoint)"""
    email: Optional[str] = None
    phone: Optional[str] = None
    username: Optional[str] = None
    status: Optional[str] = None
    roles: Optional[List[str]] = None
    permissions: Optional[List[str]] = None
    tags: Optional[List[str]] = None


# Mapper Functions
def map_verification_status_to_dto(user) -> VerificationStatusDTO:
    """Convert user verification status to DTO (dual input handling)"""
    if isinstance(user, dict):
        # Handle dict input from database
        email_verified = user.get('email_verified', False)
        phone_verified = user.get('phone_verified', False)
        age_verified = user.get('age_verified', False)

        return VerificationStatusDTO(
            email_verified=email_verified,
            email_verified_at=user.get('email_verified_at'),
            phone_verified=phone_verified,
            phone_verified_at=user.get('phone_verified_at'),
            age_verified=age_verified,
            age_verified_at=user.get('age_verified_at'),
            is_fully_verified=email_verified and (phone_verified if user.get('phone') else True)
        )

    # Handle domain object
    return VerificationStatusDTO(
        email_verified=user.email_verified,
        email_verified_at=user.email_verified_at.isoformat() if user.email_verified_at else None,
        phone_verified=user.phone_verified,
        phone_verified_at=user.phone_verified_at.isoformat() if user.phone_verified_at else None,
        age_verified=user.age_verified,
        age_verified_at=user.age_verified_at.isoformat() if user.age_verified_at else None,
        is_fully_verified=user.is_verified() if hasattr(user, 'is_verified') else False
    )


def map_account_security_to_dto(user) -> AccountSecurityDTO:
    """Convert user security info to DTO (dual input handling)"""
    if isinstance(user, dict):
        # Handle dict input from database
        account_locked_until = user.get('account_locked_until')
        is_locked = False
        if account_locked_until:
            from datetime import datetime
            if isinstance(account_locked_until, str):
                account_locked_until = datetime.fromisoformat(account_locked_until)
            is_locked = datetime.utcnow() < account_locked_until

        return AccountSecurityDTO(
            two_factor_enabled=user.get('two_factor_enabled', False),
            failed_login_attempts=user.get('failed_login_attempts', 0),
            last_failed_login=user.get('last_failed_login'),
            account_locked_until=account_locked_until.isoformat() if account_locked_until else None,
            is_account_locked=is_locked,
            last_login_at=user.get('last_login_at'),
            last_login_ip=user.get('last_login_ip'),
            login_count=user.get('login_count', 0)
        )

    # Handle domain object
    return AccountSecurityDTO(
        two_factor_enabled=user.two_factor_enabled,
        failed_login_attempts=user.failed_login_attempts,
        last_failed_login=user.last_failed_login.isoformat() if user.last_failed_login else None,
        account_locked_until=user.account_locked_until.isoformat() if user.account_locked_until else None,
        is_account_locked=user.is_account_locked() if hasattr(user, 'is_account_locked') else False,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        last_login_ip=user.last_login_ip,
        login_count=user.login_count
    )


def map_password_policy_to_dto(policy) -> PasswordPolicyDTO:
    """Convert PasswordPolicy value object to DTO (dual input handling)"""
    if isinstance(policy, dict):
        # Handle dict input from database
        return PasswordPolicyDTO(
            min_length=policy.get('min_length', 8),
            require_uppercase=policy.get('require_uppercase', True),
            require_lowercase=policy.get('require_lowercase', True),
            require_digit=policy.get('require_digit', True),
            require_special=policy.get('require_special', False),
            allowed_special_chars=policy.get('allowed_special_chars', '!@#$%^&*()_+-=[]{}|;:,.<>?')
        )

    # Handle domain object
    return PasswordPolicyDTO(
        min_length=policy.min_length,
        require_uppercase=policy.require_uppercase,
        require_lowercase=policy.require_lowercase,
        require_digit=policy.require_digit,
        require_special=policy.require_special,
        allowed_special_chars=policy.allowed_special_chars if hasattr(policy, 'allowed_special_chars') else '!@#$%^&*()_+-=[]{}|;:,.<>?'
    )


def map_user_to_dto(user) -> UserDTO:
    """Convert User aggregate to DTO (dual input handling)"""
    if isinstance(user, dict):
        # Handle dict input from database
        user_type = user.get('user_type', 'customer')
        if hasattr(user_type, 'value'):
            user_type = user_type.value

        status = user.get('status', 'pending')
        if hasattr(status, 'value'):
            status = status.value

        auth_provider = user.get('auth_provider', 'local')
        if hasattr(auth_provider, 'value'):
            auth_provider = auth_provider.value

        # Calculate full_name
        first_name = user.get('first_name')
        last_name = user.get('last_name')
        email = user.get('email', '')
        if first_name and last_name:
            full_name = f"{first_name} {last_name}"
        elif first_name:
            full_name = first_name
        elif last_name:
            full_name = last_name
        else:
            full_name = email.split('@')[0] if '@' in email else email

        display_name = user.get('username') or full_name

        # Calculate age
        age = None
        dob = user.get('date_of_birth')
        if dob:
            from datetime import date
            if isinstance(dob, str):
                from datetime import datetime
                dob = datetime.fromisoformat(dob).date()
            today = date.today()
            age = today.year - dob.year
            if today.month < dob.month or (today.month == dob.month and today.day < dob.day):
                age -= 1

        verification = map_verification_status_to_dto(user)
        security = map_account_security_to_dto(user)

        # Check if can make purchase
        can_make_purchase = (
            status == 'active' and
            not security.is_account_locked and
            verification.is_fully_verified and
            verification.age_verified
        )

        is_active = status == 'active' and not security.is_account_locked

        return UserDTO(
            id=str(user.get('id')),
            email=email,
            phone=user.get('phone'),
            username=user.get('username'),
            user_type=user_type,
            status=status,
            auth_provider=auth_provider,
            provider_user_id=user.get('provider_user_id'),
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            display_name=display_name,
            date_of_birth=dob.isoformat() if dob and hasattr(dob, 'isoformat') else (str(dob) if dob else None),
            age=age,
            gender=user.get('gender'),
            verification=verification,
            security=security,
            permissions=user.get('permissions', []),
            roles=user.get('roles', []),
            last_activity_at=user.get('last_activity_at'),
            language=user.get('language', 'en'),
            timezone=user.get('timezone', 'America/Toronto'),
            currency=user.get('currency', 'CAD'),
            notifications_enabled=user.get('notifications_enabled', True),
            marketing_emails_enabled=user.get('marketing_emails_enabled', False),
            metadata=user.get('metadata', {}),
            tags=user.get('tags', []),
            can_make_purchase=can_make_purchase,
            is_active=is_active,
            created_at=user.get('created_at').isoformat() if user.get('created_at') and hasattr(user.get('created_at'), 'isoformat') else str(user.get('created_at')) if user.get('created_at') else datetime.utcnow().isoformat(),
            updated_at=user.get('updated_at').isoformat() if user.get('updated_at') and hasattr(user.get('updated_at'), 'isoformat') else str(user.get('updated_at')) if user.get('updated_at') else datetime.utcnow().isoformat(),
            events=[]
        )

    # Handle domain object
    return UserDTO(
        id=str(user.id),
        email=user.email,
        phone=user.phone,
        username=user.username,
        user_type=user.user_type.value if hasattr(user.user_type, 'value') else str(user.user_type),
        status=user.status.value if hasattr(user.status, 'value') else str(user.status),
        auth_provider=user.auth_provider.value if hasattr(user.auth_provider, 'value') else str(user.auth_provider),
        provider_user_id=user.provider_user_id,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=user.get_full_name() if hasattr(user, 'get_full_name') else (user.email.split('@')[0] if user.email else ''),
        display_name=user.get_display_name() if hasattr(user, 'get_display_name') else (user.username or user.email.split('@')[0] if user.email else ''),
        date_of_birth=user.date_of_birth.isoformat() if user.date_of_birth else None,
        age=user.calculate_age() if hasattr(user, 'calculate_age') else None,
        gender=user.gender,
        verification=map_verification_status_to_dto(user),
        security=map_account_security_to_dto(user),
        permissions=user.permissions,
        roles=user.roles,
        last_activity_at=user.last_activity_at.isoformat() if user.last_activity_at else None,
        language=user.language,
        timezone=user.timezone,
        currency=user.currency,
        notifications_enabled=user.notifications_enabled,
        marketing_emails_enabled=user.marketing_emails_enabled,
        metadata=user.metadata,
        tags=user.tags,
        can_make_purchase=user.can_make_purchase() if hasattr(user, 'can_make_purchase') else False,
        is_active=user.is_active() if hasattr(user, 'is_active') else False,
        created_at=user.created_at.isoformat() if user.created_at and hasattr(user.created_at, 'isoformat') else str(user.created_at) if user.created_at else datetime.utcnow().isoformat(),
        updated_at=user.updated_at.isoformat() if user.updated_at and hasattr(user.updated_at, 'isoformat') else str(user.updated_at) if user.updated_at else datetime.utcnow().isoformat(),
        events=[type(event).__name__ for event in user.domain_events]
    )


def map_user_summary_to_dto(user) -> UserSummaryDTO:
    """Convert User to summary DTO (dual input handling)"""
    if isinstance(user, dict):
        # Handle dict input from database
        first_name = user.get('first_name')
        last_name = user.get('last_name')
        email = user.get('email', '')
        if first_name and last_name:
            full_name = f"{first_name} {last_name}"
        elif first_name:
            full_name = first_name
        elif last_name:
            full_name = last_name
        else:
            full_name = email.split('@')[0] if '@' in email else email

        display_name = user.get('username') or full_name

        user_type = user.get('user_type', 'customer')
        if hasattr(user_type, 'value'):
            user_type = user_type.value

        status = user.get('status', 'pending')
        if hasattr(status, 'value'):
            status = status.value

        return UserSummaryDTO(
            id=str(user.get('id')),
            email=email,
            phone=user.get('phone'),
            full_name=full_name,
            display_name=display_name,
            user_type=user_type,
            status=status,
            roles=user.get('roles', []),
            email_verified=user.get('email_verified', False),
            phone_verified=user.get('phone_verified', False),
            age_verified=user.get('age_verified', False),
            last_login_at=user.get('last_login_at'),
            created_at=user.get('created_at').isoformat() if user.get('created_at') and hasattr(user.get('created_at'), 'isoformat') else str(user.get('created_at')) if user.get('created_at') else datetime.utcnow().isoformat()
        )

    # Handle domain object
    return UserSummaryDTO(
        id=str(user.id),
        email=user.email,
        phone=user.phone,
        full_name=user.get_full_name() if hasattr(user, 'get_full_name') else (user.email.split('@')[0] if user.email else ''),
        display_name=user.get_display_name() if hasattr(user, 'get_display_name') else (user.username or user.email.split('@')[0] if user.email else ''),
        user_type=user.user_type.value if hasattr(user.user_type, 'value') else str(user.user_type),
        status=user.status.value if hasattr(user.status, 'value') else str(user.status),
        roles=user.roles,
        email_verified=user.email_verified,
        phone_verified=user.phone_verified,
        age_verified=user.age_verified,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        created_at=user.created_at.isoformat() if user.created_at and hasattr(user.created_at, 'isoformat') else str(user.created_at) if user.created_at else datetime.utcnow().isoformat()
    )
