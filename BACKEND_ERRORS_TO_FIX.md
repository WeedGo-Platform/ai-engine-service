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
| Missing Table | 1 | HIGH | ❌ Not Fixed |
| Connection Pool | 1 | HIGH | ❌ Not Fixed |
| Wrong Column | 2 | HIGH | ❌ Not Fixed |
| Missing Data | 2 | MEDIUM | ⚠️ Data Issue |

---

**Next Steps:**
1. Create review_summary_view migration
2. Fix SQL queries with wrong column references
3. Add proper database connection management
4. Test all affected endpoints

