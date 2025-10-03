# Device Management API - Testing Guide

## Prerequisites

1. **Run Database Migration:**
```bash
cd /Users/charrcy/projects/WeedGo/microservices/ai-engine-service/src/Backend
psql -h localhost -p 5434 -U weedgo -d ai_engine -f migrations/009_device_management.sql
```

2. **Start API Server:**
```bash
cd /Users/charrcy/projects/WeedGo/microservices/ai-engine-service/src/Backend
python api_server.py
```

3. **Verify Swagger UI:**
Open: `http://localhost:5024/docs`

Look for new endpoints:
- `🖥️ Device Management` - Device pairing and heartbeat
- `⚙️ Admin - Device Management` - Admin CRUD operations

---

## Testing Sequence

### Step 1: Create a Device (Admin)

**Endpoint:** `POST /api/admin/stores/{store_id}/devices`

First, get a store_id:
```bash
curl -X GET "http://localhost:5024/api/stores" -H "accept: application/json"
```

Copy a `store_id` from the response, then create a device:

```bash
curl -X POST "http://localhost:5024/api/admin/stores/{STORE_ID}/devices" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "KIOSK-TEST-001",
    "device_type": "kiosk",
    "name": "Test Kiosk",
    "location": "Main Floor",
    "passcode": "1234",
    "permissions": {
      "can_process_orders": true,
      "can_access_inventory": true
    },
    "configuration": {
      "idle_timeout": 120,
      "enable_budtender": true
    }
  }'
```

**Expected Response (201 Created):**
```json
{
  "device_id": "KIOSK-TEST-001",
  "device_type": "kiosk",
  "name": "Test Kiosk",
  "location": "Main Floor",
  "status": "pending_pairing",
  "paired_at": null,
  "last_seen": null,
  "created_at": "2025-10-01T...",
  "updated_at": "2025-10-01T...",
  "permissions": {
    "can_process_orders": true,
    "can_access_inventory": true
  },
  "configuration": {
    "idle_timeout": 120,
    "enable_budtender": true
  },
  "metadata": {}
}
```

### Step 2: List Devices (Admin)

```bash
curl -X GET "http://localhost:5024/api/admin/stores/{STORE_ID}/devices" \
  -H "accept: application/json"
```

**Expected Response (200 OK):**
```json
[
  {
    "device_id": "KIOSK-TEST-001",
    "device_type": "kiosk",
    "name": "Test Kiosk",
    "location": "Main Floor",
    "status": "pending_pairing",
    ...
  }
]
```

### Step 3: Pair Device (Kiosk)

**Endpoint:** `POST /api/kiosk/device/pair`

```bash
curl -X POST "http://localhost:5024/api/kiosk/device/pair" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "KIOSK-TEST-001",
    "passcode": "1234",
    "device_info": {
      "hardware_id": "test-expo-session-123",
      "platform": "web",
      "app_version": "1.0.0",
      "model": "Test Browser"
    }
  }'
```

**Expected Response (200 OK):**
```json
{
  "success": true,
  "tenant_id": "uuid-here",
  "store_id": "uuid-here",
  "device_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "device_config": {
    "device_id": "KIOSK-TEST-001",
    "device_type": "kiosk",
    "name": "Test Kiosk",
    "location": "Main Floor",
    "permissions": {
      "can_process_orders": true,
      "can_access_inventory": true
    },
    "configuration": {
      "idle_timeout": 120,
      "enable_budtender": true
    },
    "status": "active",
    "paired_at": "2025-10-01T..."
  },
  "tenant_config": {
    "tenant_id": "uuid",
    "name": "Tenant Name",
    "code": "tenant-code",
    "logo_url": "https://...",
    "settings": {}
  },
  "store_config": {
    "store_id": "uuid",
    "name": "Store Name",
    "address": {},
    "phone": "...",
    "email": "...",
    "hours": {},
    "tax_rate": 0.13,
    "timezone": "America/Toronto"
  }
}
```

**Save the `device_token` for next steps!**

### Step 4: Test Invalid Passcode

```bash
curl -X POST "http://localhost:5024/api/kiosk/device/pair" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "KIOSK-TEST-001",
    "passcode": "9999",
    "device_info": {}
  }'
```

**Expected Response (200 OK with error):**
```json
{
  "success": false,
  "error": "invalid_passcode",
  "message": "Invalid passcode. Please try again.",
  "tenant_id": null,
  "store_id": null,
  "device_token": null
}
```

### Step 5: Send Heartbeat (Device)

```bash
curl -X POST "http://localhost:5024/api/kiosk/device/heartbeat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {DEVICE_TOKEN}" \
  -H "X-Device-Id: KIOSK-TEST-001" \
  -d '{
    "status": "active",
    "metrics": {
      "sessions_today": 10,
      "orders_today": 5,
      "last_activity": "2025-10-01T15:45:00Z"
    }
  }'
```

**Expected Response (200 OK):**
```json
{
  "success": true,
  "message": "Heartbeat received",
  "timestamp": "2025-10-01T..."
}
```

### Step 6: Get Device Info (Device)

```bash
curl -X GET "http://localhost:5024/api/kiosk/device/info" \
  -H "Authorization: Bearer {DEVICE_TOKEN}" \
  -H "X-Device-Id: KIOSK-TEST-001"
```

**Expected Response (200 OK):**
```json
{
  "success": true,
  "device_config": {
    "device_id": "KIOSK-TEST-001",
    "device_type": "kiosk",
    "name": "Test Kiosk",
    "location": "Main Floor",
    "permissions": {...},
    "configuration": {...},
    "status": "active",
    "paired_at": "2025-10-01T...",
    "last_seen": "2025-10-01T..."
  },
  "tenant_id": "uuid",
  "store_id": "uuid"
}
```

### Step 7: Update Device (Admin)

```bash
curl -X PUT "http://localhost:5024/api/admin/stores/{STORE_ID}/devices/KIOSK-TEST-001" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Kiosk Name",
    "status": "active",
    "configuration": {
      "idle_timeout": 180
    }
  }'
```

**Expected Response (200 OK):**
```json
{
  "device_id": "KIOSK-TEST-001",
  "name": "Updated Kiosk Name",
  "status": "active",
  ...
}
```

### Step 8: Delete Device (Admin)

```bash
curl -X DELETE "http://localhost:5024/api/admin/stores/{STORE_ID}/devices/KIOSK-TEST-001"
```

**Expected Response (200 OK):**
```json
{
  "success": true,
  "message": "Device 'KIOSK-TEST-001' deleted successfully"
}
```

---

## Error Scenarios

### 1. Device Not Found
```bash
curl -X POST "http://localhost:5024/api/kiosk/device/pair" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "NONEXISTENT",
    "passcode": "1234",
    "device_info": {}
  }'
```

**Response:**
```json
{
  "success": false,
  "error": "device_not_found",
  "message": "Device 'NONEXISTENT' not found in any store. Please contact admin."
}
```

### 2. Device Already Exists (Admin Create)
Try creating the same device_id twice:

**Response (409 Conflict):**
```json
{
  "detail": "Device 'KIOSK-TEST-001' already exists in this store"
}
```

### 3. Inactive Device
Update device status to inactive, then try to pair:

```bash
# First, set device to inactive
curl -X PUT "http://localhost:5024/api/admin/stores/{STORE_ID}/devices/KIOSK-TEST-001" \
  -H "Content-Type: application/json" \
  -d '{"status": "inactive"}'

# Then try to pair
curl -X POST "http://localhost:5024/api/kiosk/device/pair" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "KIOSK-TEST-001",
    "passcode": "1234",
    "device_info": {}
  }'
```

**Response:**
```json
{
  "success": false,
  "error": "device_inactive",
  "message": "This device has been deactivated. Please contact admin."
}
```

---

## Database Verification

### Check Devices in Store
```sql
SELECT
    id,
    name,
    jsonb_pretty(settings->'devices') as devices
FROM stores
WHERE settings->'devices' IS NOT NULL
LIMIT 1;
```

### Find Device by ID
```sql
SELECT * FROM find_device_by_id('KIOSK-TEST-001');
```

### List All Devices Across Stores
```sql
SELECT
    s.id as store_id,
    s.name as store_name,
    elem->>'device_id' as device_id,
    elem->>'device_type' as device_type,
    elem->>'name' as device_name,
    elem->>'location' as location,
    elem->>'status' as status,
    elem->>'paired_at' as paired_at
FROM stores s
CROSS JOIN LATERAL jsonb_array_elements(s.settings->'devices') elem
WHERE s.settings->'devices' IS NOT NULL;
```

---

## Postman Collection

Import this into Postman for easy testing:

### Environment Variables
```
base_url: http://localhost:5024
store_id: <paste-your-store-id>
device_token: <set-after-pairing>
```

### Collection
```json
{
  "info": {
    "name": "Device Management API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Admin - Create Device",
      "request": {
        "method": "POST",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "url": "{{base_url}}/api/admin/stores/{{store_id}}/devices",
        "body": {
          "mode": "raw",
          "raw": "{\n  \"device_id\": \"KIOSK-TEST-001\",\n  \"device_type\": \"kiosk\",\n  \"name\": \"Test Kiosk\",\n  \"location\": \"Main Floor\",\n  \"passcode\": \"1234\",\n  \"permissions\": {\"can_process_orders\": true},\n  \"configuration\": {\"idle_timeout\": 120}\n}"
        }
      }
    },
    {
      "name": "Admin - List Devices",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/api/admin/stores/{{store_id}}/devices"
      }
    },
    {
      "name": "Device - Pair",
      "request": {
        "method": "POST",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "url": "{{base_url}}/api/kiosk/device/pair",
        "body": {
          "mode": "raw",
          "raw": "{\n  \"device_id\": \"KIOSK-TEST-001\",\n  \"passcode\": \"1234\",\n  \"device_info\": {\"hardware_id\": \"test-123\", \"platform\": \"web\"}\n}"
        }
      }
    },
    {
      "name": "Device - Heartbeat",
      "request": {
        "method": "POST",
        "header": [
          {"key": "Content-Type", "value": "application/json"},
          {"key": "Authorization", "value": "Bearer {{device_token}}"},
          {"key": "X-Device-Id", "value": "KIOSK-TEST-001"}
        ],
        "url": "{{base_url}}/api/kiosk/device/heartbeat",
        "body": {
          "mode": "raw",
          "raw": "{\n  \"status\": \"active\",\n  \"metrics\": {\"sessions_today\": 10}\n}"
        }
      }
    }
  ]
}
```

---

## Success Criteria

✅ **Phase 1 Complete When:**
1. Migration runs successfully
2. Can create device via admin API
3. Can list devices
4. Device pairing works with correct passcode
5. Device pairing fails with wrong passcode (but allows retry)
6. Heartbeat updates last_seen
7. Device info returns full config
8. Can update device
9. Can delete device

---

## Next Steps

After backend testing is successful:
1. **Frontend Kiosk Integration** (Phase 2)
2. **Admin Dashboard UI** (Phase 3)
3. **Production Deployment** (Phase 4)
