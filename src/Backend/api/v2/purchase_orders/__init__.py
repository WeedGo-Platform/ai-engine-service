"""
Purchase Order Management V2 API

DDD-powered supplier ordering and receiving management using the Purchase Order bounded context.

Features:
- Complete PO lifecycle (draft → submitted → approved → sent → received → closed)
- Multi-stage approval workflow
- Line item management
- Financial tracking (subtotal, tax, shipping, discounts)
- Payment terms and due dates (NET_15, NET_30, NET_45, NET_60, NET_90)
- Shipping and delivery scheduling
- Partial and full receiving
- Supplier confirmation tracking
- Tracking numbers and carrier integration
- Status history with transition validation
- Automatic approval threshold ($5000+)
- Overdue delivery detection
- Payment due tracking

Purchase Order Statuses:
- draft: Being created
- submitted: Awaiting approval
- approved: Approved, ready to send
- sent_to_supplier: Sent to supplier
- confirmed: Confirmed by supplier
- partially_received: Some items received
- fully_received: All items received
- closed: Order completed
- cancelled: Order cancelled
"""

from .purchase_order_endpoints import router

__all__ = ["router"]
