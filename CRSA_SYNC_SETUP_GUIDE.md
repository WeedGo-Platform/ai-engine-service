# Ontario CRSA Sync System Setup Guide

## Problem Investigation Summary

### Issue
The CRSA validation system was not pulling data from AGCO because:

1. **Sync service never initialized** - The `initialize_sync_service()` was never called on application startup
2. **No data in database** - The `ontario_crsa_status` table was empty
3. **No CSV files** - No AGCO data had been downloaded or imported
4. **Missing dependencies** - Web scraping libraries not installed

### Root Cause Analysis

**Architecture Discovery:**
```
Frontend (OntarioLicenseValidator.tsx)
  ↓ POST /api/crsa/validate
API Endpoint (ontario_crsa_endpoints.py)
  ↓ validate_license(request)
Service Layer (OntarioCRSAService)
  ↓ await crsa_repo.get_by_license()
Repository (OntarioCRSARepository)
  ↓ SELECT FROM ontario_crsa_status
Database (PostgreSQL - EMPTY!)
```

**Missing Link:**
- Sync service exists but was never started
- No scheduler running to import AGCO data
- No initial data load performed

---

## Solution Implemented

### 1. Application Startup Integration ✅

**File:** `api_server.py`

Added CRSA sync service initialization to the `lifespan` function:

```python
# Initialize CRSA sync service
logger.info("Initializing Ontario CRSA sync service...")
try:
    from services.ontario_crsa_sync_service import initialize_sync_service
    sync_service = await initialize_sync_service(start_scheduler=True)
    app.state.crsa_sync_service = sync_service
    logger.info("✅ CRSA sync service initialized (scheduled daily at 3:00 AM)")
except Exception as e:
    logger.error(f"❌ Failed to initialize CRSA sync service: {e}")
    logger.warning("CRSA sync will need to be run manually")
```

**What this does:**
- Starts sync service on server startup
- Schedules daily sync at 3:00 AM
- Makes service available at `app.state.crsa_sync_service`

### 2. AGCO Data Download Script ✅

**File:** `scripts/download_agco_crsa.py`

Created automated web scraper to download CRSA data from AGCO website:

```bash
# Download latest data
python scripts/download_agco_crsa.py

# Download and import in one step
python scripts/download_agco_crsa.py --import
```

**What it does:**
- Scrapes https://www.agco.ca/status-current-cannabis-retail-store-applications
- Extracts store data from HTML table
- Converts to CSV format
- Saves to `data/crsa/crsa_data_YYYYMMDD_HHMMSS.csv`
- Optionally runs import script

---

## Setup Instructions

### Step 1: Install Dependencies

```bash
cd /Users/charrcy/projects/WeedGo/microservices/ai-engine-service/src/Backend

# Install web scraping dependencies
pip install aiohttp beautifulsoup4 lxml

# Verify requirements.txt has them
grep -E "aiohttp|beautifulsoup4" requirements.txt || echo "Add to requirements.txt"
```

### Step 2: Initial Data Load

```bash
# Option A: Download and import in one step (recommended)
python scripts/download_agco_crsa.py --import

# Option B: Download first, then import manually
python scripts/download_agco_crsa.py
python scripts/import_crsa_data.py data/crsa/crsa_data_*.csv --initial
```

### Step 3: Verify Database

```bash
# Connect to database
psql -h localhost -p 5434 -U weedgo -d ai_engine

# Check records
SELECT 
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE is_active = true) as active,
    COUNT(*) FILTER (WHERE store_application_status = 'Authorized to Open') as authorized,
    COUNT(*) FILTER (WHERE linked_tenant_id IS NOT NULL) as linked
FROM ontario_crsa_status;

# View sample data
SELECT license_number, store_name, municipality, store_application_status 
FROM ontario_crsa_status 
WHERE is_active = true 
LIMIT 5;
```

### Step 4: Test Validation

```bash
# Test API endpoint
curl -X POST http://localhost:5024/api/crsa/validate \
  -H "Content-Type: application/json" \
  -d '{
    "license_number": "CRSA-123456",
    "email": "test@example.com"
  }'
```

Expected response:
```json
{
  "is_valid": true,
  "auto_fill_data": {
    "store_name": "Example Store",
    "address": "123 Main St, Toronto ON",
    "website": "https://example.com"
  },
  "verification_tier": "auto_approved",
  "domain_match": true
}
```

---

## Sync Service Features

### Automated Daily Sync

The sync service runs automatically at **3:00 AM daily**:

1. Downloads latest CSV (if URL configured) or uses latest file
2. Imports new/updated records
3. Marks removed stores as inactive
4. Records sync history
5. Logs statistics

### Manual Sync

Trigger manual sync via API:

```bash
# Manual sync using latest CSV
curl -X POST http://localhost:5024/api/crsa/sync/manual

# Manual sync with specific CSV
curl -X POST http://localhost:5024/api/crsa/sync/manual \
  -H "Content-Type: application/json" \
  -d '{"csv_path": "/path/to/file.csv"}'
```

### Sync Statistics

View sync history:

```bash
curl http://localhost:5024/api/crsa/sync/stats
```

Response:
```json
{
  "total_syncs": 10,
  "successful_syncs": 9,
  "failed_syncs": 1,
  "last_sync_date": "2025-01-15T03:00:00",
  "total_records_processed": 1250
}
```

---

## Data Flow

### How CRSA Validation Works

1. **User enters license number** in frontend (TenantSignup.tsx → OntarioLicenseValidator.tsx)
2. **Frontend validates** → POST to `/api/crsa/validate`
3. **API endpoint** → Calls `OntarioCRSAService.validate_license()`
4. **Service validates:**
   - License exists in database
   - Store is active (`is_active = true`)
   - Store is authorized (`store_application_status = 'Authorized to Open'`)
   - Not linked to another tenant (`linked_tenant_id IS NULL`)
   - Email domain matches store website (optional)
5. **Returns validation result** with auto-fill data

### Validation Tiers

| Tier | Criteria | Action |
|------|----------|--------|
| `auto_approved` | All checks pass + domain match | Auto-approve signup |
| `manual_review` | All checks pass, no domain match | Require admin review |
| `rejected` | Failed validation checks | Show error to user |

---

## Troubleshooting

### Problem: "No CSV files found"

**Solution:**
```bash
# Download fresh data
python scripts/download_agco_crsa.py --import

# Or manually place CSV in data/crsa/
mkdir -p data/crsa
cp /path/to/agco_data.csv data/crsa/
```

### Problem: "License number not found"

**Possible causes:**
1. Database empty → Run initial import
2. License doesn't exist in AGCO data
3. License format mismatch

**Check:**
```sql
-- Search for similar license numbers
SELECT license_number, store_name 
FROM ontario_crsa_status 
WHERE license_number LIKE '%123%' 
LIMIT 10;
```

### Problem: "Validation fails for authorized store"

**Check all validation criteria:**
```sql
SELECT 
    license_number,
    store_name,
    is_active,
    store_application_status,
    linked_tenant_id,
    website
FROM ontario_crsa_status 
WHERE license_number = 'CRSA-123456';
```

**Validation requirements:**
- `is_active = true`
- `store_application_status = 'Authorized to Open'`
- `linked_tenant_id IS NULL`

### Problem: "Sync service not running"

**Check server logs:**
```bash
# Look for startup message
grep "CRSA sync service" server.log

# Should see:
# ✅ CRSA sync service initialized (scheduled daily at 3:00 AM)
```

**Verify scheduler:**
```python
# In Python console
from services.ontario_crsa_sync_service import get_sync_service
sync = get_sync_service()
print(f"Running: {sync.is_running}")
print(f"Last sync: {sync.last_sync_time}")
```

---

## API Endpoints

### Validation
```
POST /api/crsa/validate
Body: {"license_number": "CRSA-123456", "email": "user@example.com"}
```

### Search
```
GET /api/crsa/search?q=store+name
```

### Sync Management
```
POST /api/crsa/sync/manual
GET /api/crsa/sync/stats
```

### Link Store to Tenant
```
POST /api/crsa/link
Body: {"license_number": "CRSA-123456", "tenant_id": "uuid"}
```

---

## Database Schema

```sql
CREATE TABLE ontario_crsa_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    license_number VARCHAR(50) UNIQUE NOT NULL,
    municipality VARCHAR(255),
    first_nation VARCHAR(255),
    store_name VARCHAR(500) NOT NULL,
    address TEXT NOT NULL,
    store_application_status VARCHAR(100) NOT NULL,
    website VARCHAR(500),
    linked_tenant_id UUID REFERENCES tenants(id),
    is_active BOOLEAN DEFAULT TRUE,
    first_seen_at TIMESTAMP DEFAULT NOW(),
    last_synced_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE crsa_sync_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sync_date TIMESTAMP NOT NULL,
    success BOOLEAN NOT NULL,
    records_processed INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Maintenance

### Weekly Tasks
- Review sync history for failures
- Check for stores marked inactive
- Verify authorized count matches AGCO website

### Monthly Tasks
- Audit linked tenants
- Review manual sync triggers
- Update web scraping logic if AGCO site changes

### As Needed
- Run manual sync after known AGCO updates
- Investigate validation failures
- Update domain matching logic

---

## Next Steps

1. **Add to requirements.txt:**
   ```
   aiohttp>=3.9.0
   beautifulsoup4>=4.12.0
   lxml>=4.9.0
   ```

2. **Run initial data load:**
   ```bash
   python scripts/download_agco_crsa.py --import
   ```

3. **Test validation:**
   - Use real AGCO license number
   - Verify auto-fill works
   - Check domain matching

4. **Monitor sync service:**
   - Check daily sync runs at 3 AM
   - Review sync history in database
   - Set up alerts for sync failures

---

## Related Files

- `api_server.py` - Application startup, sync service initialization
- `services/ontario_crsa_sync_service.py` - Sync service implementation
- `scripts/download_agco_crsa.py` - AGCO data download script (NEW)
- `scripts/import_crsa_data.py` - CSV import script
- `api/ontario_crsa_endpoints.py` - API endpoints
- `core/services/ontario_crsa_service.py` - Business logic
- `core/repositories/ontario_crsa_repository.py` - Database queries
- `components/OntarioLicenseValidator.tsx` - Frontend validation

---

## Support

If validation still doesn't work after setup:

1. Check database has records
2. Verify sync service is running
3. Review API logs for errors
4. Test with known valid license number from AGCO website
5. Check network connectivity to AGCO site
