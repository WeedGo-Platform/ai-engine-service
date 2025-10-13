# DDD Integration - Quick Start Guide
## From Analysis to Implementation in 1 Hour

**Goal:** Get your first DDD-powered endpoint running
**Time:** 60 minutes
**Context:** Payment Processing (highest value, isolated)

---

## 📋 Pre-flight Checklist

Before starting, ensure you have:
- [x] Read `DDD_INTEGRATION_STRATEGY.md`
- [x] Reviewed `API_ENDPOINT_ANALYSIS.json`
- [ ] DDD domain models exist in `ddd_refactored/domain/payment_processing/`
- [ ] Test database is running
- [ ] Development environment is set up

---

## 🚀 Step-by-Step Implementation (60 min)

### Step 1: Create V2 Infrastructure (15 min)

#### 1.1 Create Directory Structure
```bash
mkdir -p api/v2/payments
touch api/v2/__init__.py
touch api/v2/payments/__init__.py
touch api/v2/dependencies.py
touch api/v2/dto_mappers.py
```

#### 1.2 Set Up Dependency Injection

Create `api/v2/dependencies.py`:
```python
"""Dependency injection for V2 API"""
from fastapi import Depends
from ddd_refactored.infrastructure.repositories import PaymentTransactionRepository
from ddd_refactored.application.payments import PaymentService

async def get_payment_repository():
    """Get payment repository instance"""
    return PaymentTransactionRepository()

async def get_payment_service(
    repo = Depends(get_payment_repository)
):
    """Get payment application service"""
    return PaymentService(repo)
```

#### 1.3 Create DTO Mappers

Create `api/v2/dto_mappers.py`:
```python
"""DTO mappers for domain → API transformation"""
from typing import Dict, Any
from ddd_refactored.domain.payment_processing import PaymentTransaction
from pydantic import BaseModel

class PaymentTransactionDTO(BaseModel):
    """Payment transaction data transfer object"""
    id: str
    order_id: str
    amount: float
    currency: str
    status: str
    payment_method: str
    transaction_id: str | None = None
    created_at: str
    updated_at: str

def map_payment_to_dto(payment: PaymentTransaction) -> PaymentTransactionDTO:
    """Convert PaymentTransaction domain object to DTO"""
    return PaymentTransactionDTO(
        id=str(payment.id),
        order_id=str(payment.order_id),
        amount=float(payment.amount),
        currency=payment.currency,
        status=payment.status,
        payment_method=payment.payment_method,
        transaction_id=payment.transaction_id,
        created_at=payment.created_at.isoformat(),
        updated_at=payment.updated_at.isoformat()
    )
```

### Step 2: Create First DDD Endpoint (20 min)

Create `api/v2/payments/payment_endpoints.py`:
```python
"""
Payment Processing V2 Endpoints
Powered by DDD Payment Processing Context
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from api.v2.dependencies import get_payment_service
from api.v2.dto_mappers import map_payment_to_dto, PaymentTransactionDTO

router = APIRouter(
    prefix="/v2/payments",
    tags=["Payments V2 (DDD)"]
)

# Request Models
class ProcessPaymentRequest(BaseModel):
    order_id: str
    amount: float
    currency: str = "CAD"
    payment_method: str
    card_token: str | None = None

class RefundPaymentRequest(BaseModel):
    amount: float | None = None  # None = full refund
    reason: str

# Endpoints
@router.post("/process", response_model=PaymentTransactionDTO)
async def process_payment(
    request: ProcessPaymentRequest,
    service = Depends(get_payment_service)
):
    """
    Process a new payment transaction

    This endpoint uses the DDD Payment Processing context:
    - PaymentTransaction aggregate
    - Process payment command
    - Payment events published
    """
    try:
        # Create command from request
        payment = await service.process_payment(
            order_id=request.order_id,
            amount=request.amount,
            currency=request.currency,
            payment_method=request.payment_method,
            card_token=request.card_token
        )

        return map_payment_to_dto(payment)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Payment processing failed")

@router.get("/{transaction_id}", response_model=PaymentTransactionDTO)
async def get_transaction(
    transaction_id: str,
    service = Depends(get_payment_service)
):
    """Get payment transaction by ID"""
    try:
        payment = await service.get_transaction(transaction_id)

        if not payment:
            raise HTTPException(status_code=404, detail="Transaction not found")

        return map_payment_to_dto(payment)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve transaction")

@router.post("/{transaction_id}/refund", response_model=PaymentTransactionDTO)
async def refund_payment(
    transaction_id: str,
    request: RefundPaymentRequest,
    service = Depends(get_payment_service)
):
    """Refund a payment transaction"""
    try:
        payment = await service.refund_payment(
            transaction_id=transaction_id,
            amount=request.amount,
            reason=request.reason
        )

        return map_payment_to_dto(payment)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Refund processing failed")

@router.get("/", response_model=list[PaymentTransactionDTO])
async def list_transactions(
    order_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    service = Depends(get_payment_service)
):
    """List payment transactions with optional filters"""
    try:
        payments = await service.list_transactions(
            order_id=order_id,
            status=status,
            limit=limit
        )

        return [map_payment_to_dto(p) for p in payments]

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to list transactions")
```

### Step 3: Register Endpoint in Server (5 min)

Edit `api_server.py` or `api_server.py`:
```python
# Add at top
from api.v2.payments import payment_endpoints as payments_v2

# Add in router registration section
app.include_router(
    payments_v2.router,
    prefix="/api",  # Will be /api/v2/payments
    tags=["Payments V2"]
)
```

### Step 4: Test the Endpoint (10 min)

#### 4.1 Start the Server
```bash
python api_server.py
```

#### 4.2 Check OpenAPI Docs
Navigate to: `http://localhost:5024/docs`

Look for "Payments V2 (DDD)" section

#### 4.3 Test Process Payment
```bash
curl -X POST http://localhost:5024/api/v2/payments/process \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "test-order-123",
    "amount": 99.99,
    "currency": "CAD",
    "payment_method": "credit_card",
    "card_token": "tok_test_123"
  }'
```

Expected response:
```json
{
  "id": "uuid-here",
  "order_id": "test-order-123",
  "amount": 99.99,
  "currency": "CAD",
  "status": "pending",
  "payment_method": "credit_card",
  "transaction_id": null,
  "created_at": "2025-10-09T...",
  "updated_at": "2025-10-09T..."
}
```

### Step 5: Add Backward Compatibility (10 min)

Update OLD `api/payment_endpoints.py`:
```python
# At top
from api.v2.payments import payment_endpoints as v2_payments
from fastapi import Depends
from warnings import warn

@router.post("/process")
async def process_payment_v1(
    request: PaymentRequest,
    v2_service = Depends(v2_payments.get_payment_service)
):
    """
    DEPRECATED: Use /v2/payments/process instead

    This endpoint exists for backward compatibility and proxies to V2.
    It will be removed in version 3.0 (6 months from now).
    """
    warn(
        "Payment V1 endpoint is deprecated. Use /v2/payments/process",
        DeprecationWarning,
        stacklevel=2
    )

    # Convert V1 request to V2 request
    v2_request = ProcessPaymentRequest(
        order_id=request.order_id,
        amount=request.amount,
        currency=request.currency or "CAD",
        payment_method=request.payment_method,
        card_token=request.card_token
    )

    # Call V2 endpoint
    return await v2_payments.process_payment(v2_request, v2_service)
```

---

## ✅ Verification Checklist

After completing all steps:

- [ ] Server starts without errors
- [ ] `/docs` shows "Payments V2 (DDD)" section
- [ ] POST /api/v2/payments/process works
- [ ] GET /api/v2/payments/{id} works
- [ ] POST /api/v2/payments/{id}/refund works
- [ ] GET /api/v2/payments/ lists transactions
- [ ] V1 endpoint proxies to V2
- [ ] All tests pass: `pytest tests/api/v2/`

---

## 🎓 What You Just Learned

1. **DDD Integration Pattern**
   - Domain → Application → API layers
   - Dependency injection for clean architecture
   - DTO mapping for API contracts

2. **Backward Compatibility**
   - V1 → V2 proxy pattern
   - Deprecation warnings
   - Zero breaking changes

3. **API Design**
   - RESTful conventions
   - Clear request/response models
   - Proper error handling

---

## 🚀 Next Steps

Now that you have ONE DDD endpoint working:

### This Week
1. Add remaining payment operations (authorize, capture, void)
2. Add event publishing to payment events
3. Write integration tests
4. Monitor V2 endpoint performance

### Next Week
1. Start Order Management context integration
2. Follow same pattern as payments
3. Wire up Order aggregate

### This Month
1. Complete Phase 2 contexts (Order, Inventory, Identity)
2. Deprecate V1 endpoints officially
3. Update frontend to use V2

---

## 📊 Success Metrics

After your first DDD integration:

**Technical:**
- Response time < 100ms
- Error rate < 0.1%
- Test coverage > 80%

**Team:**
- Developers understand DDD pattern
- Can replicate for other contexts
- Positive feedback on code quality

---

## 🆘 Troubleshooting

### Error: "Module 'ddd_refactored' not found"
**Solution:** Ensure DDD code is in correct location and PYTHONPATH is set
```bash
export PYTHONPATH="${PYTHONPATH}:${PWD}"
```

### Error: "Repository not initialized"
**Solution:** Check database connection and ensure tables exist
```bash
python scripts/verify_database.py
```

### Error: "Circular import"
**Solution:** Review dependency injection setup, ensure repositories aren't importing endpoints

---

## 📚 Resources

- **Full Strategy:** `DDD_INTEGRATION_STRATEGY.md`
- **API Analysis:** `API_ENDPOINT_ANALYSIS.json`
- **DDD Architecture:** `DDD_ARCHITECTURE_REFACTORING.md`
- **Code Cleanup:** `CODE_CLEANUP_REPORT.md`

---

## 💡 Pro Tips

1. **Start Small:** Get one endpoint working perfectly before scaling
2. **Test Early:** Write tests as you go, not after
3. **Document As You Build:** Update OpenAPI descriptions
4. **Monitor Performance:** Compare V1 vs V2 response times
5. **Get Feedback:** Show teammates and iterate

---

**Congratulations!** 🎉

You now have a DDD-powered API endpoint. This pattern will be replicated across all 14 bounded contexts. Each integration gets easier as the team learns the pattern.

**Total Time to First DDD Endpoint:** ~60 minutes
**Total Time to Full Integration:** ~5 months
**ROI:** Massive improvement in code quality, maintainability, and feature velocity

---

**Ready to Begin?** Start with Step 1 above! 🚀
