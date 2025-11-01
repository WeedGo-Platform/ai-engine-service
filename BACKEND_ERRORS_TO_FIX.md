# Backend Errors Found - Dashboard Fixes Branch

**Date:** November 1, 2025  
**Branch:** dashboard-fixes  
**Status:** Multiple 500 errors requiring database fixes

---

## 🔴 Critical Errors (500)

### 1. Missing Table: `review_summary_view`
**Error:**
```
asyncpg.exceptions.UndefinedTableError: relation "review_summary_view" does not exist
```

**Location:** `api/review_endpoints.py:226`

**Endpoints Affected:**
- `GET /api/v1/reviews/products/{sku}/ratings` - 500 error
- `GET /api/v1/reviews/products/{sku}/reviews` - 500 error

**Fix Required:** Create the `review_summary_view` materialized view or table

---

### 2. Database Connection Pool Issue
**Error:**
```
asyncpg.exceptions._base.InterfaceError: cannot call Connection.fetch(): 
connection has been released back to the pool
```

**Location:** `api/review_endpoints.py:371`

**Issue:** Database connection being used after it's been released back to pool

**Fix Required:** Properly manage database connections with context managers

---

### 3. Missing Column: `location_code` in batch_tracking
**Error:**
```
column "location_code" does not exist
HINT: Perhaps you meant to reference the column "batch_tracking.location_id"
```

**Location:** `api/product_details_endpoints.py` - batch fetching

**Fix Required:** Update query to use `location_id` instead of `location_code`

---

### 4. Wrong Column Reference: `i.product_name`
**Error:**
```
column i.product_name does not exist
HINT: Perhaps you meant to reference the column "pc.product_name"
```

**Location:** `api/kiosk_endpoints.py:584` - recommendations endpoint

**Endpoints Affected:**
- `POST /api/kiosk/products/recommendations` - 500 error

**Fix Required:** Change `i.product_name` to `pc.product_name` in SQL query

---

## ⚠️ Warnings

### 5. Missing Inventory Records
**Warning:**
```
Transaction validation failed: Inventory record not found for SKU
```

**Location:** `api/pos_transaction_endpoints.py`

**Issue:** SKUs `93247ef8` and `5d2300d4` don't have inventory records

**Fix Required:** Either add inventory records or handle gracefully

---

## ✅ Fixed in This Branch

1. ✅ Missing `Wrench` icon import in `ProductDetailsModal.tsx` - FIXED
2. ✅ Missing `appConfig` import in `TenantManagement.tsx` - FIXED (feature/signup)
3. ✅ Missing auth headers in PO modal supplier lookup - FIXED
4. ✅ Provincial suppliers seeded - FIXED
5. ✅ **Missing `review_summary_view` table** - FIXED (created materialized view)
6. ✅ **Database connection pool management** - FIXED (proper async context)
7. ✅ **Wrong column `i.product_name`** - FIXED (changed to `pc.product_name`)
8. ✅ **Wrong column `location_code`** - FIXED (changed to `location_id`)

---

## ⚠️ Remaining Issues

### 5. Missing Inventory Records - ROOT CAUSE IDENTIFIED
**Status:** Frontend Bug

**Issue:** POS transaction endpoint receives inventory UUIDs instead of SKUs
- Backend expects: `product.sku` (e.g., "105000_28G___")
- Frontend sends: `product.id` (e.g., "93247ef8-2a03-40f6-ad53...")
- Backend uses first 8 chars as SKU, which doesn't match any inventory

**Affected SKUs (actually UUIDs):**
- `93247ef8` → Actually inventory ID `93247ef8-2a03-40f6-ad53-ca9bb02a27aa` (SKU: 105000_28G___)
- `5d2300d4` → Actually inventory ID `5d2300d4-d5e5-43fb-a880-c1eb804cee25` (SKU: 310102_2G___)

**Fix Required:** Update POS frontend to send `product.sku` instead of `product.id`

**Location:** Frontend POS component that creates transactions

---

## 📋 TODO - Priority Order

### High Priority (Blocking Kiosk)
1. **Fix review_summary_view**
   - Create materialized view or table
   - Update review endpoints to handle missing view gracefully

2. **Fix kiosk recommendations**
   - Update query in `kiosk_endpoints.py` line 584
   - Change `i.product_name` to `pc.product_name`

3. **Fix database connection pool**
   - Add proper connection management in review_endpoints.py
   - Use `async with` context managers

### Medium Priority
4. **Fix batch tracking query**
   - Update `product_details_endpoints.py`
   - Change `location_code` to `location_id`

### Low Priority
5. **Handle missing inventory gracefully**
   - Add better error messages
   - Consider auto-creating inventory records

---

## 🔧 Quick Fixes

### Fix #1: Kiosk Recommendations
```python
# In api/kiosk_endpoints.py around line 584
# Change FROM:
SELECT i.product_name, ...

# TO:
SELECT pc.product_name, ...
```

### Fix #2: Batch Tracking
```python
# In api/product_details_endpoints.py
# Change FROM:
... location_code ...

# TO:
... location_id ...
```

### Fix #3: Database Connection
```python
# In api/review_endpoints.py
# Use proper context manager:
async with pool.acquire() as db:
    rows = await db.fetch(query, *params)
```

---

## 📊 Error Summary

| Error Type | Count | Severity | Status |
|------------|-------|----------|--------|
| Missing Table | 1 | HIGH | ✅ FIXED |
| Connection Pool | 1 | HIGH | ✅ FIXED |
| Wrong Column | 2 | HIGH | ✅ FIXED |
| Frontend Bug (UUID vs SKU) | 1 | MEDIUM | ⚠️ Needs Frontend Fix |

---

**Next Steps:**
1. Create review_summary_view migration
2. Fix SQL queries with wrong column references
3. Add proper database connection management
4. Test all affected endpoints

