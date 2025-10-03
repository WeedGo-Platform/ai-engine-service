# AI Admin Dashboard - Device Management Update

**Date:** 2025-10-01
**Status:** ✅ Complete
**Location:** `/src/Frontend/ai-admin-dashboard`

---

## Summary

Updated the AI Admin Dashboard Device Management tab to include passcode field and connect to AI Engine Service API for device registration.

## Changes Made

### 1. Updated Device Interface
**File:** `/src/components/storeSettings/AllSettingsTabbed.tsx`

Added `passcode` field to Device interface:

```typescript
interface Device {
  id: string;
  name: string;
  platform: 'web' | 'tablet';
  appType: 'pos' | 'kiosk' | 'menu';
  deviceId: string;
  passcode?: string; // ✅ NEW: Added for device pairing
  status: 'active' | 'inactive';
  lastActivity?: string;
}
```

### 2. Added Passcode Input Field
**File:** `/src/components/storeSettings/AllSettingsTabbed.tsx` (lines 459-469)

Added passcode input field to the "Add Device" form:

```typescript
<div>
  <label className="block text-sm font-medium mb-1">Passcode</label>
  <input
    type="text"
    placeholder="4-6 digit passcode"
    value={newDevice.passcode}
    onChange={(e) => setNewDevice({
      ...newDevice,
      passcode: e.target.value.replace(/[^0-9]/g, '')
    })}
    maxLength={6}
    className="w-full px-3 py-2 border rounded-lg"
  />
</div>
```

**Features:**
- Numeric-only input (filters out non-digits)
- Max length of 6 digits
- Placeholder text for guidance
- Validation on submit

### 3. Updated Form Grid Layout
Changed from 4-column to 5-column grid to accommodate passcode field:

```typescript
// BEFORE:
<div className="grid grid-cols-1 md:grid-cols-4 gap-4">

// AFTER:
<div className="grid grid-cols-1 md:grid-cols-5 gap-4">
```

### 4. Added Device API Service
**File:** `/src/services/api.ts` (lines 186-196)

Added new `devices` API service:

```typescript
// Store Devices
devices: {
  getAll: (storeId: string) =>
    axiosInstance.get(`/api/admin/stores/${storeId}/devices`),

  create: (storeId: string, data: any) =>
    axiosInstance.post(`/api/admin/stores/${storeId}/devices`, data),

  update: (storeId: string, deviceId: string, data: any) =>
    axiosInstance.put(`/api/admin/stores/${storeId}/devices/${deviceId}`, data),

  delete: (storeId: string, deviceId: string) =>
    axiosInstance.delete(`/api/admin/stores/${storeId}/devices/${deviceId}`),

  getPairCode: (storeId: string, deviceId: string) =>
    axiosInstance.get(`/api/admin/stores/${storeId}/devices/${deviceId}/pair-code`),
},
```

### 5. Updated addDevice Function to Call API
**File:** `/src/components/storeSettings/AllSettingsTabbed.tsx` (lines 363-406)

Replaced local-only device creation with API call:

```typescript
const addDevice = async () => {
  if (newDevice.name && newDevice.deviceId && newDevice.passcode) {
    try {
      // Call AI Engine API to create device
      const response = await api.devices.create(storeId, {
        device_id: newDevice.deviceId,
        device_name: newDevice.name,
        passcode: newDevice.passcode,
        device_type: newDevice.appType, // pos, kiosk, menu
        settings: {
          platform: newDevice.platform, // ✅ Includes platform type
          application_type: newDevice.appType
        }
      });

      // Add device to local state
      const device: Device = {
        id: response.data.id || `device_${Date.now()}`,
        name: newDevice.name,
        platform: newDevice.platform,
        appType: newDevice.appType,
        deviceId: newDevice.deviceId,
        passcode: response.data.passcode,
        status: 'active',
        lastActivity: new Date().toISOString()
      };

      setLocalSettings({
        ...localSettings,
        devices: [...localSettings.devices, device]
      });

      setNewDevice({ name: '', platform: 'web', appType: 'pos', deviceId: '', passcode: '' });
      setShowAddDevice(false);

      // Show success with passcode
      alert(`Device created successfully!\n\nDevice ID: ${newDevice.deviceId}\nPasscode: ${response.data.passcode}\n\n⚠️ Save this passcode - it won't be shown again!`);
    } catch (error: any) {
      console.error('Failed to create device:', error);
      alert(`Failed to create device: ${error.response?.data?.detail || error.message}`);
    }
  } else {
    alert('Please fill in all required fields (Device Name, Device ID, and Passcode)');
  }
};
```

**Key Features:**
- ✅ Async API call to AI Engine Service
- ✅ Platform type included in `settings.platform` payload
- ✅ Application type included in `settings.application_type`
- ✅ Proper error handling with user-friendly messages
- ✅ Success alert displays passcode (one-time display)
- ✅ Validation for all required fields

### 6. Added API Import
**File:** `/src/components/storeSettings/AllSettingsTabbed.tsx` (line 7)

```typescript
import { api } from '../../services/api';
```

---

## API Payload Structure

When creating a device, the following payload is sent to AI Engine:

```json
{
  "device_id": "KIOSK-001",
  "device_name": "Front Counter Kiosk",
  "passcode": "123456",
  "device_type": "kiosk",
  "settings": {
    "platform": "tablet",
    "application_type": "kiosk"
  }
}
```

**Field Mapping:**
- `device_id` → newDevice.deviceId
- `device_name` → newDevice.name
- `passcode` → newDevice.passcode
- `device_type` → newDevice.appType (pos, kiosk, menu)
- `settings.platform` → newDevice.platform (web, tablet)
- `settings.application_type` → newDevice.appType

---

## Backend Endpoint

**Endpoint:** `POST /api/admin/stores/{storeId}/devices`

**Expected Response:**
```json
{
  "success": true,
  "id": "uuid-123",
  "device_id": "KIOSK-001",
  "passcode": "123456",
  "device_token": "jwt-token-here",
  "message": "Device created successfully"
}
```

---

## User Flow

1. **Admin navigates to Store Settings → Devices tab**
2. **Clicks "Add Device" button**
3. **Fills in form:**
   - Device Name: "Front Counter Kiosk"
   - Platform: "Tablet Application"
   - Application Type: "Kiosk (Self-Service)"
   - Device ID: "KIOSK-001"
   - Passcode: "123456" ✅ NEW FIELD
4. **Clicks "Add Device"**
5. **API request sent to AI Engine Service**
6. **Success alert shows:**
   ```
   Device created successfully!

   Device ID: KIOSK-001
   Passcode: 123456

   ⚠️ Save this passcode - it won't be shown again!
   ```
7. **Device appears in list**

---

## Kiosk Pairing Flow

Now that the device is created with a passcode:

1. **Admin shares Device ID + Passcode** with kiosk operator
2. **Kiosk app opens DeviceRegistrationScreen**
3. **Enters Device ID** (KIOSK-001)
4. **Enters Passcode** (123456)
5. **Clicks "Pair Device"**
6. **Kiosk calls** `POST /api/kiosk/devices/pair`
7. **Backend validates passcode** (bcrypt compare)
8. **Returns JWT token + credentials**
9. **Kiosk stores in AsyncStorage**
10. **Device is now authenticated**

---

## Files Modified

1. ✅ `/src/components/storeSettings/AllSettingsTabbed.tsx`
   - Added passcode field to Device interface
   - Added passcode input to form
   - Updated addDevice function to call API
   - Added validation and error handling

2. ✅ `/src/services/api.ts`
   - Added devices API service
   - Implemented create, getAll, update, delete, getPairCode

---

## Testing Checklist

### Manual Testing
- [ ] Navigate to Store Settings → Devices tab
- [ ] Click "Add Device" button
- [ ] Verify all 5 fields are visible (Name, Platform, App Type, Device ID, Passcode)
- [ ] Try to submit without passcode → Should show validation error
- [ ] Enter valid data and submit
- [ ] Verify API request is sent to `/api/admin/stores/{storeId}/devices`
- [ ] Verify success alert shows with passcode
- [ ] Verify device appears in list
- [ ] Test kiosk pairing with Device ID + Passcode

### API Testing
```bash
# Test device creation
curl -X POST http://localhost:5024/api/admin/stores/{store_id}/devices \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {admin_token}" \
  -d '{
    "device_id": "TEST-001",
    "device_name": "Test Device",
    "passcode": "123456",
    "device_type": "kiosk",
    "settings": {
      "platform": "tablet",
      "application_type": "kiosk"
    }
  }'
```

---

## Known Issues / Future Enhancements

### Current Limitations
1. **No passcode strength validation** - Accepts any 4-6 digit number
2. **Plain text passcode in alert** - Consider using modal with copy button
3. **No passcode regeneration** - Once set, cannot change via UI
4. **No device list refresh** - Uses local state only, doesn't fetch from API

### Recommended Enhancements
1. **Add passcode strength indicator**
   - Minimum 6 digits required
   - Show strength meter

2. **Improve passcode display**
   - Use modal instead of alert
   - Add "Copy to Clipboard" button
   - Add QR code generation for easy scanning

3. **Load devices from API on mount**
   ```typescript
   useEffect(() => {
     const loadDevices = async () => {
       const response = await api.devices.getAll(storeId);
       setLocalSettings({ devices: response.data });
     };
     loadDevices();
   }, [storeId]);
   ```

4. **Add device deletion**
   ```typescript
   const deleteDevice = async (deviceId: string) => {
     await api.devices.delete(storeId, deviceId);
     // Refresh list
   };
   ```

5. **Add "View Passcode" button**
   - Call `/api/admin/stores/{storeId}/devices/{deviceId}/pair-code`
   - Show in secure modal
   - Require admin re-authentication

---

## Security Considerations

### Implemented
✅ Numeric-only passcode input
✅ API authentication via JWT
✅ Backend bcrypt hashing (12 salt rounds)
✅ One-time passcode display
✅ Store-scoped device creation

### Recommendations
⚠️ Add passcode complexity requirements (min 6 digits)
⚠️ Add rate limiting on device creation
⚠️ Add audit logging for device creation/pairing
⚠️ Consider passcode expiration (e.g., 24 hours to pair)
⚠️ Add device revocation endpoint

---

## Dependencies

- **React**: UI framework
- **Axios**: HTTP client
- **Lucide React**: Icons
- **AI Engine Service**: Backend API (port 5024)

---

## Related Documentation

- **Kiosk Pairing Flow:** `/frontend/tablet-app/kiosk-tablet-app/DEVICE_PAIRING_INTEGRATION.md`
- **API Endpoints:** `/microservices/ai-engine-service/src/Backend/api/admin_device_endpoints.py`
- **Kiosk API Migration:** `/frontend/tablet-app/kiosk-tablet-app/IMPLEMENTATION_COMPLETE.md`

---

## Status Summary

✅ **Complete** - All requested features implemented:
1. ✅ Passcode field added to form
2. ✅ Device interface updated
3. ✅ API service created
4. ✅ addDevice function connects to AI Engine API
5. ✅ Platform type sent in API payload
6. ✅ Validation and error handling

**Ready for testing!**
