# OCS Integration Deployment Guide

**Date**: October 22, 2025  
**Status**: Backend Complete - Ready for UI Integration & Testing

## ✅ Completed Components

### 1. Database Schema
- All 6 OCS tables exist in `ai_engine` database
- Existing columns ready: `stores.ocs_key`, `stores.license_number`, `tenants.crol_number`

### 2. Services (Backend)
- ✅ `services/ocs_auth_service.py` - OAuth 2.0 authentication
- ✅ `services/ocs_inventory_position_service.py` - Daily snapshots
- ✅ `services/ocs_inventory_event_service.py` - Real-time events

### 3. Workers (Backend)
- ✅ `workers/ocs_daily_sync_worker.py` - Daily 1 AM sync
- ✅ `workers/ocs_event_worker.py` - Redis event queue
- ✅ `workers/ocs_retry_worker.py` - Retry with backoff

### 4. API Endpoints
- ✅ `api/ocs_endpoints.py` - 8 management endpoints

---

## 📋 Deployment Steps

### Step 1: Install Dependencies

```bash
cd /Users/charrcy/projects/WeedGo/microservices/ai-engine-service/src/Backend

# Install Python packages
pip install apscheduler pytz redis aiohttp

# Verify installations
python3 -c "import apscheduler; import pytz; import redis; import aiohttp; print('✅ All dependencies installed')"
```

### Step 2: Configure Environment Variables

Add to `.env` file:

```bash
# OCS API Configuration
OCS_API_BASE_URL=https://api.ocs.ca

# Database (already configured)
DB_HOST=localhost
DB_PORT=5434
DB_NAME=ai_engine
DB_USER=weedgo
DB_PASSWORD=weedgo123

# Redis (for event queue)
REDIS_HOST=localhost
REDIS_PORT=6379

# Optional: Enable hourly testing mode
OCS_HOURLY_TEST=false
```

### Step 3: Register API Endpoints

Add to your main FastAPI app:

```python
# In main.py or app.py
from api import ocs_endpoints

app.include_router(ocs_endpoints.router)
```

### Step 4: Start Workers

#### Option A: Run in Terminal (Development)

```bash
# Terminal 1: Daily Sync Worker
python3 workers/ocs_daily_sync_worker.py

# Terminal 2: Event Worker
python3 workers/ocs_event_worker.py

# Terminal 3: Retry Worker
python3 workers/ocs_retry_worker.py
```

#### Option B: Systemd Services (Production)

Create `/etc/systemd/system/ocs-daily-sync.service`:

```ini
[Unit]
Description=OCS Daily Sync Worker
After=network.target postgresql.service

[Service]
Type=simple
User=weedgo
WorkingDirectory=/Users/charrcy/projects/WeedGo/microservices/ai-engine-service/src/Backend
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 workers/ocs_daily_sync_worker.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create similar files for:
- `/etc/systemd/system/ocs-event-worker.service`
- `/etc/systemd/system/ocs-retry-worker.service`

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ocs-daily-sync ocs-event-worker ocs-retry-worker
sudo systemctl start ocs-daily-sync ocs-event-worker ocs-retry-worker

# Check status
sudo systemctl status ocs-daily-sync
sudo systemctl status ocs-event-worker
sudo systemctl status ocs-retry-worker
```

---

## 🔌 Integration Points

### POS Transactions

Add after successful sale:

```python
from workers.ocs_event_worker import OCSEventWorker

# After POS transaction saved
event_data = {
    'tenant_id': tenant_id,
    'store_id': store_id,
    'transaction_type': 'sale',
    'transaction_id': transaction_id,
    'items': [
        {
            'ocs_sku': item['ocs_sku'],
            'quantity': item['quantity'],
            'unit_price': item['unit_price']
        }
        for item in sale_items
    ]
}

# Enqueue for async processing
worker = OCSEventWorker()
await worker.enqueue_event(event_data)
```

### Inventory Adjustments

```python
event_data = {
    'tenant_id': tenant_id,
    'store_id': store_id,
    'transaction_type': 'adjustment',
    'transaction_id': adjustment_id,
    'items': adjustment_items
}
await worker.enqueue_event(event_data)
```

### Other Operations

Use same pattern for:
- `'purchase'` - Supplier receiving
- `'transfer'` - Store transfer
- `'return'` - Customer return
- `'damage'` - Damaged goods destruction

---

## 🎨 UI Integration Tasks

### 1. Store Management Page

**File**: `src/Frontend/ai-admin-dashboard/src/pages/StoreManagement.tsx`

Add **"Compliance"** tab with:
- OCS Hash Key input field
- CRSA License Number input field
- Save button calling `PUT /api/ocs/stores/{store_id}/config`

### 2. Tenant Management Page

**File**: `src/Frontend/ai-admin-dashboard/src/pages/TenantManagement.tsx`

Add fields:
- CROL Number (tenant-level)
- OCS Credentials section (Super Admin only):
  - Client ID input
  - Client Secret input (password field)
  - Test & Save button calling `POST /api/ocs/credentials`

### 3. OCS Compliance Dashboard

Create new page: `src/Frontend/ai-admin-dashboard/src/pages/OCSCompliance.tsx`

Features:
- **Status Overview**:
  - Credentials configured ✓/✗
  - Active token status
  - Enabled stores count
  
- **Submission History**:
  - Position submissions (last 30 days)
  - Event submissions (last 100)
  - Success/failure rates
  
- **Actions**:
  - Manual position submission button
  - Retry failed events button
  - View audit logs
  
**API Calls**:
```typescript
// Get status
GET /api/ocs/status/{tenant_id}

// Get histories
GET /api/ocs/position/history/{store_id}
GET /api/ocs/events/history/{store_id}

// Manual actions
POST /api/ocs/position/submit
POST /api/ocs/events/retry

// Audit logs (super admin)
GET /api/ocs/audit
```

---

## 🧪 Testing Checklist

### Authentication Service
```bash
# Test in Python console
python3 << EOF
import asyncio
import os
os.environ['DB_NAME'] = 'ai_engine'

from services.ocs_auth_service import OCSAuthService
import asyncpg

async def test():
    pool = await asyncpg.create_pool(
        host='localhost', port=5434,
        database='ai_engine', user='weedgo', password='weedgo123'
    )
    service = OCSAuthService(pool)
    
    # Test credential validation (use test credentials)
    valid = await service.validate_credentials('test_client_id', 'test_secret')
    print(f'Credentials valid: {valid}')
    
    await pool.close()

asyncio.run(test())
EOF
```

### Position Service
```bash
# Test position submission
curl -X POST http://localhost:8000/api/ocs/position/submit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "store_id": "YOUR_STORE_ID",
    "snapshot_date": "2025-10-22"
  }'
```

### Event Worker
```bash
# Check Redis queue
redis-cli LLEN ocs_events

# Monitor worker logs
tail -f /var/log/ocs-event-worker.log
```

---

## 📊 Monitoring

### Check Worker Status

```bash
# Daily Sync Worker
sudo systemctl status ocs-daily-sync

# Event Worker
sudo systemctl status ocs-event-worker

# Retry Worker
sudo systemctl status ocs-retry-worker
```

### Check Database Logs

```sql
-- Recent position submissions
SELECT * FROM ocs_inventory_position_log 
ORDER BY submitted_at DESC LIMIT 10;

-- Recent events
SELECT * FROM ocs_inventory_event_log 
ORDER BY submitted_at DESC LIMIT 20;

-- Failed submissions
SELECT * FROM ocs_inventory_event_log 
WHERE status = 'failed' 
ORDER BY submitted_at DESC;

-- Audit trail
SELECT * FROM ocs_audit_log 
ORDER BY created_at DESC LIMIT 20;
```

### Check Redis Queue

```bash
# Queue size
redis-cli LLEN ocs_events

# Peek at queue
redis-cli LRANGE ocs_events 0 4
```

---

## 🚨 Troubleshooting

### Workers Not Running

```bash
# Check logs
journalctl -u ocs-daily-sync -n 50
journalctl -u ocs-event-worker -n 50
journalctl -u ocs-retry-worker -n 50

# Restart services
sudo systemctl restart ocs-daily-sync
sudo systemctl restart ocs-event-worker
sudo systemctl restart ocs-retry-worker
```

### Failed Submissions

1. Check `ocs_inventory_event_log` for error messages
2. Verify OCS credentials are valid
3. Check token expiration in `ocs_oauth_tokens`
4. Test manual submission via API endpoint
5. Check retry worker is processing failed events

### Token Issues

```sql
-- Check token status
SELECT 
    tenant_id,
    token_expires_at,
    token_expires_at > NOW() as is_valid
FROM ocs_oauth_tokens;

-- Force token refresh
UPDATE ocs_oauth_tokens 
SET access_token_encrypted = NULL, token_expires_at = NULL 
WHERE tenant_id = 'YOUR_TENANT_ID';
```

---

## 📝 Next Steps

1. **UI Integration** (6-8 hours):
   - Store Management Compliance tab
   - Tenant Management CROL field
   - OCS Compliance Dashboard

2. **POS/Inventory Integration** (2-3 hours):
   - Add event hooks to all transaction types
   - Test event queue processing

3. **Testing** (3-4 hours):
   - End-to-end testing of all workflows
   - Load testing with multiple stores
   - Error handling scenarios

4. **Documentation** (1-2 hours):
   - User guide for tenant admins
   - Super admin configuration guide
   - Operations runbook

**Total Estimated Time**: 12-17 hours

---

## 🎯 Success Criteria

- ✅ Daily position syncs run at 1 AM Eastern
- ✅ Real-time events submitted within 1 minute of transaction
- ✅ Failed events retry with exponential backoff
- ✅ All submissions logged to database
- ✅ UI allows tenant admins to configure OCS settings
- ✅ Super admins can view audit logs and trigger manual syncs
- ✅ Error rate < 1% under normal operations
- ✅ Workers auto-restart on failure

---

**Backend Implementation**: ✅ **COMPLETE**  
**Next Phase**: UI Integration & Testing
