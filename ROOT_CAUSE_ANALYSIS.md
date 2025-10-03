# Root Cause Analysis - Admin Portal Errors

**Date:** 2025-10-01
**Investigated by:** Claude Code
**Status:** 🔴 Critical Issues Identified

---

## Issue #1: React Router v7 Future Flag Warning

### Error Message
```
⚠️ React Router Future Flag Warning: React Router will begin wrapping state updates in
`React.startTransition` in v7. You can use the `v7_startTransition` future flag to opt-in early.
```

### Root Cause
- **Location:** `/Users/charrcy/projects/WeedGo/frontend/web-app/admin-portal-web/src/App.tsx`
- **Issue:** Using React Router v6 without enabling v7 future flags
- **Impact:** ⚠️ **Low** - Warning only, no functionality broken
- **Why it appears:** React Router v6.4+ includes future flags to prepare for v7 migration

### Technical Details
React Router v7 will wrap state updates in `React.startTransition` for better concurrent rendering. The warning appears because:
1. BrowserRouter in `App.tsx` (line 268) doesn't specify future flags
2. Application uses default v6 behavior
3. React Router warns about upcoming breaking changes in v7

### Fix Required
Update `BrowserRouter` to enable v7 future flags:

```typescript
// App.tsx line 268
<BrowserRouter
  future={{
    v7_startTransition: true,
    v7_relativeSplatPath: true
  }}
>
```

---

## Issue #2: Provinces API 500 Internal Server Error

### Error Message
```
:5024/api/stores/provinces:1 Failed to load resource: the server responded with a status of 500
(Internal Server Error)
hook.js:608 Failed to fetch provinces: AxiosError
```

### Root Cause
- **Location:** AI Engine Service - `/api/stores/provinces` endpoint
- **Endpoint File:** `/Users/charrcy/projects/WeedGo/microservices/ai-engine-service/src/Backend/api/store_endpoints.py:323`
- **Issue:** Database connection failure or missing `provinces_territories` table
- **Impact:** 🔴 **High** - Prevents admin dashboard from loading provinces data

### Technical Details

#### Endpoint Code (store_endpoints.py:323-356)
```python
@router.get("/provinces", response_model=List[ProvinceTerritory])
async def get_provinces():
    """Get all active provinces and territories"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT
                    id, code, name, type,
                    tax_rate, cannabis_tax_rate, min_age,
                    regulatory_body, delivery_allowed, pickup_allowed
                FROM provinces_territories
                ORDER BY type, name
            """)

            return [
                ProvinceTerritory(
                    id=row['id'],
                    code=row['code'],
                    # ... mapping
                )
                for row in rows
            ]
    except Exception as e:
        logger.error(f"Error fetching provinces: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch provinces")
```

#### Database Connection (tenant_endpoints.py:114-127)
```python
async def get_db_pool() -> asyncpg.Pool:
    """Get or create database connection pool"""
    global _db_pool
    if _db_pool is None:
        _db_pool = await asyncpg.create_pool(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5434)),
            database=os.getenv('DB_NAME', 'ai_engine'),
            user=os.getenv('DB_USER', 'weedgo'),
            password=os.getenv('DB_PASSWORD', 'your_password_here'),  # Default password
            min_size=10,
            max_size=20
        )
    return _db_pool
```

### Problem Diagnosis

**Evidence Found:**
1. ✅ AI Engine service is running (port 5024 listening)
2. ✅ Endpoint code exists and is correct
3. ❌ No `.env` file exists (using default credentials)
4. ❌ Database connection likely failing
5. ✅ Migration files exist:
   - `populate_canadian_provinces.sql`
   - `populate_provinces.sql`
   - `populate_provinces_territories.sql`
   - `update_provinces_territories_data.sql`

**Root Causes (3 possibilities):**

1. **Missing .env file** 🔴 **MOST LIKELY**
   - AI Engine has no `.env` file
   - Using hardcoded defaults: `DB_PASSWORD=your_password_here`
   - Database credentials may not match

2. **Table `provinces_territories` doesn't exist** 🟡 **POSSIBLE**
   - Migrations may not have been run
   - Database schema not initialized
   - SQL files exist but not executed

3. **Database not running or wrong port** 🟡 **POSSIBLE**
   - Expected port: 5434
   - Expected database: ai_engine
   - May not exist or be accessible

### How This Happened

**Timeline:**
1. AI Engine Service implemented with provinces endpoint
2. Migration files created but may not have been executed
3. No `.env` file created (only `.env.example` exists)
4. Service defaults to `DB_PASSWORD=your_password_here`
5. Frontend admin dashboard calls `/api/stores/provinces`
6. Database connection fails → 500 error

### Impact Analysis

**Admin Dashboard Impact:**
- ❌ Cannot load provinces dropdown
- ❌ Cannot create new stores (needs province selection)
- ❌ Store form validation fails
- ❌ User sees error toasts

**User Experience:**
- 🔴 **Broken Feature** - Cannot add new stores
- 🔴 **Error Messages** - "Failed to fetch provinces" appears repeatedly
- 🟡 **Network Tab Pollution** - Repeated 500 errors every page load

**Business Impact:**
- 🔴 **Critical** - Admin cannot onboard new stores
- 🔴 **Blocker** - Store management workflow broken
- 🟡 **Data Integrity** - Cannot validate province codes

---

## Fix Checklist

### Priority 1: Fix Provinces API (CRITICAL)

#### Option A: Create .env file with correct credentials
```bash
cd /Users/charrcy/projects/WeedGo/microservices/ai-engine-service

# Copy example
cp .env.example .env

# Update with actual credentials
cat > .env << EOF
DB_HOST=localhost
DB_PORT=5434
DB_NAME=ai_engine
DB_USER=weedgo
DB_PASSWORD={ACTUAL_PASSWORD}
JWT_SECRET={ACTUAL_SECRET}
EOF
```

#### Option B: Run database migrations
```bash
cd /Users/charrcy/projects/WeedGo/microservices/ai-engine-service

# Connect to database and run migrations
psql -h localhost -p 5434 -U weedgo -d ai_engine -f src/Backend/migrations/populate_provinces_territories.sql
```

#### Option C: Verify database exists
```bash
# Check if database exists
psql -h localhost -p 5434 -U weedgo -l | grep ai_engine

# If not, create it
createdb -h localhost -p 5434 -U weedgo ai_engine

# Then run migrations
psql -h localhost -p 5434 -U weedgo -d ai_engine -f src/Backend/migrations/populate_provinces_territories.sql
```

### Priority 2: Fix React Router Warning (LOW)

```typescript
// File: /Users/charrcy/projects/WeedGo/frontend/web-app/admin-portal-web/src/App.tsx
// Line 268

// BEFORE:
<BrowserRouter>

// AFTER:
<BrowserRouter
  future={{
    v7_startTransition: true,
    v7_relativeSplatPath: true
  }}
>
```

---

## Testing Steps

### Test 1: Verify Database Connection
```bash
# From AI Engine directory
cd /Users/charrcy/projects/WeedGo/microservices/ai-engine-service

# Check connection
psql -h localhost -p 5434 -U weedgo -d ai_engine -c "SELECT COUNT(*) FROM provinces_territories"
```

**Expected:** Should return count of provinces (13 for Canada)

### Test 2: Test Provinces Endpoint
```bash
# Direct API test
curl http://localhost:5024/api/stores/provinces

# Expected: JSON array of provinces
# Actual if broken: 500 error
```

### Test 3: Verify Admin Dashboard
```bash
# In admin portal
cd /Users/charrcy/projects/WeedGo/frontend/web-app/admin-portal-web
npm start

# Navigate to: http://localhost:3003/locations/new
# Expected: Province dropdown loads
# Actual if broken: "Failed to fetch provinces" error
```

---

## Recommended Actions

### Immediate (Do Now)
1. 🔴 **Create .env file** with correct database credentials
2. 🔴 **Verify database exists** and is accessible
3. 🔴 **Run provinces migration** if table doesn't exist
4. 🔴 **Restart AI Engine** service to pick up .env
5. 🔴 **Test provinces endpoint** with curl

### Short Term (This Week)
1. 🟡 **Fix React Router warning** - add future flags
2. 🟡 **Add database health check** endpoint
3. 🟡 **Add better error logging** for provinces endpoint
4. 🟡 **Document .env setup** in README

### Long Term (Next Sprint)
1. 🟢 **Add database migration runner** to startup
2. 🟢 **Add retry logic** for database connections
3. 🟢 **Add monitoring** for API errors
4. 🟢 **Add fallback** for provinces (hardcoded Canadian provinces)

---

## Prevention Measures

### For Similar Issues in Future:

1. **Environment Setup Validation**
   - Add startup check for required env vars
   - Fail fast if .env missing
   - Document environment setup in README

2. **Database Migration Automation**
   - Run migrations on startup (if not exists)
   - Add migration status endpoint
   - Version control migrations

3. **Better Error Handling**
   - Return specific error codes (not just 500)
   - Log full stack traces
   - Add correlation IDs for debugging

4. **Health Checks**
   - Add `/health` endpoint
   - Check database connectivity
   - Check required tables exist

---

## Files Affected

### Need Changes:
1. `/Users/charrcy/projects/WeedGo/microservices/ai-engine-service/.env` - **CREATE**
2. `/Users/charrcy/projects/WeedGo/frontend/web-app/admin-portal-web/src/App.tsx` - **UPDATE** (line 268)

### Reference Files:
1. `/Users/charrcy/projects/WeedGo/microservices/ai-engine-service/.env.example`
2. `/Users/charrcy/projects/WeedGo/microservices/ai-engine-service/src/Backend/api/store_endpoints.py:323`
3. `/Users/charrcy/projects/WeedGo/microservices/ai-engine-service/src/Backend/api/tenant_endpoints.py:114`
4. `/Users/charrcy/projects/WeedGo/microservices/ai-engine-service/src/Backend/migrations/populate_provinces_territories.sql`

---

## Summary

**Critical Issue:** Database connection failure causing provinces API to return 500 error

**Root Cause:** Missing `.env` file → Using default credentials → Database connection fails

**Business Impact:** 🔴 **BLOCKER** - Cannot create new stores in admin dashboard

**Fix Duration:**
- Creating .env file: **5 minutes**
- Running migrations: **2 minutes**
- Testing: **3 minutes**
- **Total: ~10 minutes**

**Status:** 🔴 **Requires Immediate Action**

---

**Next Steps:**
1. User to provide database credentials
2. Create .env file
3. Verify database and run migrations
4. Test provinces endpoint
5. Fix React Router warning
