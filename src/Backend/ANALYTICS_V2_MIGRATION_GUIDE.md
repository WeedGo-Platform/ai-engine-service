# Analytics V2 Migration Guide

## 🎯 Overview

The Analytics API has been completely refactored from a monolithic SQL-in-API approach to a clean **Domain-Driven Design (DDD)** architecture. This guide helps you migrate from V1 to V2.

## 📊 What Changed?

### Before (V1) - Monolithic Approach
```
┌─────────────────────────────────┐
│   analytics_endpoints.py         │
│   - 728 lines of SQL queries     │
│   - Business logic mixed with    │
│     database access              │
│   - No separation of concerns    │
│   - Hard to test                 │
└─────────────────────────────────┘
```

### After (V2) - DDD Architecture
```
┌──────────────────────────────────┐
│     API Layer (HTTP only)         │
│   analytics_endpoints_v2.py       │
└───────────┬──────────────────────┘
            │
┌───────────▼──────────────────────┐
│   Application Service             │
│   AnalyticsManagementService      │
│   - Use case orchestration        │
└───────────┬──────────────────────┘
            │
┌───────────▼──────────────────────┐
│   Domain Layer                    │
│   - Entities, Value Objects       │
│   - Business rules                │
└───────────┬──────────────────────┘
            │
┌───────────▼──────────────────────┐
│   Infrastructure                  │
│   PostgresAnalyticsRepository     │
│   - Database access only          │
└──────────────────────────────────┘
```

## 🔄 API Endpoint Migration

### Dashboard Analytics

**V1 (Deprecated):**
```http
GET /api/analytics/dashboard?store_id=xxx&tenant_id=yyy
```

**V2 (Recommended):**
```http
GET /api/v2/analytics/dashboard?store_id=xxx&tenant_id=yyy&period_days=30
```

**New Features in V2:**
- ✅ Configurable period length (`period_days` parameter)
- ✅ Better error handling with domain exceptions
- ✅ Consistent response format
- ✅ Health check endpoint

### Product Analytics

**V1:**
```http
GET /api/analytics/products?store_id=xxx
```

**V2:**
```http
GET /api/v2/analytics/products?store_id=xxx&period_days=30&top_limit=10
```

**Improvements:**
- Configurable top products limit
- Category performance included
- Low stock alerts integrated

### Sales Trends

**V1:**
```http
GET /api/analytics/sales?store_id=xxx
```

**V2:**
```http
GET /api/v2/analytics/sales-trends?store_id=xxx&period_days=30&granularity=daily
```

**New Features:**
- Configurable granularity (hourly, daily, weekly, monthly)
- Sales by hour analysis
- Sales by day of week analysis

### New Endpoints (V2 Only)

**Period Comparison:**
```http
GET /api/v2/analytics/comparison?store_id=xxx&period_days=30
```
Compares current period with previous period of same length.

**Manual Refresh:**
```http
POST /api/v2/analytics/dashboard/refresh?store_id=xxx
```
Forces recalculation of analytics (useful for testing/debugging).

**Health Check:**
```http
GET /api/v2/analytics/health
```
Returns service status and capabilities.

## 📝 Response Format Changes

### V1 Response (Inconsistent)
```json
{
  "revenue": {
    "total": 12345.67,
    "trend": 15.5,
    "chart_data": [...]
  },
  // Nested structures varied by endpoint
}
```

### V2 Response (Consistent)
```json
{
  "snapshot_id": "uuid",
  "store_id": "uuid",
  "period": {
    "start": "2025-01-01T00:00:00",
    "end": "2025-01-31T23:59:59",
    "days": 30
  },
  "generated_at": "2025-01-19T12:00:00",
  "revenue": {
    "total": 12345.67,
    "currency": "CAD",
    "gross": 13000.00,
    "tax": 1300.00,
    "discounts": 654.33,
    "net": 12345.67,
    "trend": 15.5,
    "previous_period": 10000.00,
    "chart_data": []
  },
  "orders": { ... },
  "inventory": { ... },
  "customers": { ... }
}
```

**Key Improvements:**
- Snapshot ID for tracking
- Clear period metadata
- Generation timestamp
- Consistent structure across all endpoints

## 🚀 Migration Steps

### Step 1: Update Frontend Calls

**Before:**
```typescript
const response = await fetch('/api/analytics/dashboard?store_id=123');
const data = await response.json();
```

**After:**
```typescript
const response = await fetch('/api/v2/analytics/dashboard?store_id=123&period_days=30');
const data = await response.json();

// Access snapshot metadata
console.log('Generated at:', data.generated_at);
console.log('Period:', data.period);
```

### Step 2: Update Error Handling

**V2 provides structured errors:**
```typescript
try {
  const response = await fetch('/api/v2/analytics/dashboard?store_id=invalid');
  if (!response.ok) {
    const error = await response.json();
    // error.detail contains human-readable message
    console.error('Analytics error:', error.detail);
  }
} catch (e) {
  console.error('Network error:', e);
}
```

### Step 3: Leverage New Features

**Use period comparison:**
```typescript
const comparison = await fetch(
  '/api/v2/analytics/comparison?store_id=123&period_days=30'
).then(r => r.json());

console.log('Revenue change:', comparison.revenue.percent_change);
console.log('Trend:', comparison.revenue.direction); // 'up', 'down', 'stable'
```

**Use configurable granularity:**
```typescript
// Get hourly data for last 7 days
const trends = await fetch(
  '/api/v2/analytics/sales-trends?store_id=123&period_days=7&granularity=hourly'
).then(r => r.json());
```

## 🧪 Testing Migration

### 1. Parallel Testing (Recommended)

Run V1 and V2 side-by-side to compare results:

```bash
# V1 request
curl "http://localhost:5024/api/analytics/dashboard?store_id=xxx" > v1_response.json

# V2 request
curl "http://localhost:5024/api/v2/analytics/dashboard?store_id=xxx&period_days=30" > v2_response.json

# Compare key metrics
jq '.revenue.total' v1_response.json v2_response.json
```

### 2. Validation Checklist

- [ ] Revenue totals match between V1 and V2
- [ ] Order counts are identical
- [ ] Inventory metrics are consistent
- [ ] Customer counts align
- [ ] Chart data points match (within period)

### 3. Performance Testing

```bash
# Test V2 performance
time curl "http://localhost:5024/api/v2/analytics/dashboard?store_id=xxx"

# Expected: Similar or better performance than V1
```

## 🏗️ Architecture Benefits

### 1. **Testability**
```python
# Can test domain logic without database
from ddd_refactored.domain.analytics_audit.entities import RevenueMetric

metric = RevenueMetric(
    metric_name="test",
    measured_value=Decimal('1000.00'),
    store_id=UUID('...'),
    gross_revenue=Decimal('1100.00'),
    discount_amount=Decimal('100.00')
)

assert metric.calculate_net_revenue() == Decimal('1000.00')
```

### 2. **Maintainability**
- Business logic isolated in domain layer
- SQL queries in repository layer
- Easy to find and modify code

### 3. **Flexibility**
- Can swap PostgreSQL for another database
- Can add new metrics without touching API
- Can add caching layer easily

### 4. **Type Safety**
- Full type hints throughout
- Pydantic models for API
- Domain entities enforce invariants

## 📚 Code Examples

### Using V2 from Python

```python
from ddd_refactored.infrastructure.repositories import PostgresAnalyticsRepository
from ddd_refactored.application.services import AnalyticsManagementService
from ddd_refactored.domain.analytics_audit.value_objects import DateRange
from uuid import UUID

# Setup (done once at app startup)
repository = PostgresAnalyticsRepository(db_pool)
service = AnalyticsManagementService(repository, db_pool)

# Get analytics
dashboard_data = await service.get_dashboard_analytics(
    store_id=UUID('store-uuid'),
    tenant_id=UUID('tenant-uuid'),
    period_days=30
)

# Access typed data
print(f"Revenue: {dashboard_data['revenue']['total']}")
print(f"Trend: {dashboard_data['revenue']['trend']}%")
```

### Adding Custom Analytics

**1. Add method to repository:**
```python
# In PostgresAnalyticsRepository
async def get_custom_metric(self, store_id: UUID) -> CustomMetric:
    async with self.db_pool.acquire() as conn:
        # Your SQL query
        row = await conn.fetchrow("SELECT ...")
        return CustomMetric(...)
```

**2. Add use case to service:**
```python
# In AnalyticsManagementService
async def get_custom_analytics(self, store_id: UUID) -> Dict:
    metric = await self.analytics_repo.get_custom_metric(store_id)
    return metric.to_dict()
```

**3. Add API endpoint:**
```python
# In analytics_endpoints_v2.py
@router.get("/custom")
async def get_custom_analytics_v2(
    store_id: str,
    service: AnalyticsManagementService = Depends(get_analytics_service)
):
    return await service.get_custom_analytics(UUID(store_id))
```

## 🔧 Troubleshooting

### Issue: "Module not found: ddd_refactored"

**Solution:** Ensure Backend directory is in Python path:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
```

### Issue: "Invalid UUID format"

**Solution:** V2 requires proper UUID format:
```python
# ❌ Wrong
store_id = "123"

# ✅ Correct
store_id = "550e8400-e29b-41d4-a716-446655440000"
```

### Issue: "Database connection error"

**Solution:** Ensure database pool is initialized:
```python
from database.connection import get_db_pool

db_pool = await get_db_pool()
```

## 📅 Deprecation Timeline

- **Now**: V1 and V2 run in parallel
- **1 month**: V1 marked as deprecated (warnings in logs)
- **2 months**: V1 removed from documentation
- **3 months**: V1 endpoints removed entirely

## 🎓 Learning Resources

### Understanding DDD
- [Domain-Driven Design by Eric Evans](https://www.domainlanguage.com/ddd/)
- [Implementing Domain-Driven Design by Vaughn Vernon](https://vaughnvernon.com/)

### Code Structure
- `/Backend/ddd_refactored/domain/` - Business logic
- `/Backend/ddd_refactored/infrastructure/` - Database access
- `/Backend/ddd_refactored/application/` - Use case orchestration
- `/Backend/api/analytics_endpoints_v2.py` - HTTP layer

### Key Patterns Used
- **Repository Pattern**: Data access abstraction
- **Application Service Pattern**: Use case orchestration
- **Value Object Pattern**: Immutable domain concepts
- **Domain Events**: Event-driven communication

## ✅ Migration Checklist

- [ ] Update API endpoint URLs to V2
- [ ] Add `period_days` parameter where needed
- [ ] Update response parsing to handle new structure
- [ ] Add error handling for domain exceptions
- [ ] Test all critical analytics flows
- [ ] Update documentation/README
- [ ] Monitor V2 performance in production
- [ ] Deprecate V1 client code
- [ ] Remove V1 dependencies

## 🆘 Support

**Questions?**
- Check this guide first
- Review code comments in `/Backend/ddd_refactored/`
- Check domain entity docstrings for business rules

**Found a bug?**
- V1 bugs: Won't fix (deprecated)
- V2 bugs: Create issue with reproduction steps

---

**Last Updated:** October 19, 2025
**Version:** 2.0.0
**Status:** ✅ Production Ready
