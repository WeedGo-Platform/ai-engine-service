# CRSA Management UI - Implementation Guide

## Overview

A comprehensive admin interface for managing Ontario Cannabis Retail Store Authorization (CRSA) data, including manual CSV imports, automatic web scraping, and real-time statistics dashboard.

## Features Implemented

### 1. Navigation Integration
- **Location**: Super Admin menu in AI Admin Dashboard
- **Path**: `/dashboard/system/crsa`
- **Icon**: Database icon
- **Permissions**: Super Admin only (`system:super_admin`)
- **Position**: Between "Database" and "System Logs" menu items

### 2. CRSA Management Page

#### **Statistics Tab** (Default View)
Displays comprehensive CRSA database metrics and recent records.

**Features:**
- **Stats Cards:**
  - Total Records (Database icon)
  - Active Stores (Store icon, green)
  - Authorized Stores (CheckCircle icon, blue)
  - Linked Tenants (TrendingUp icon, purple)
  
- **Last Sync Info:**
  - Timestamp of most recent successful sync
  - Clock icon with formatted date/time

- **Recent Records Table:**
  - Shows last 10 CRSA records
  - Columns: License Number, Store Name, Municipality, Status, Last Updated
  - Status badges: Green for authorized, Yellow for pending
  - Sortable and filterable
  - Real-time updates via React Query (30s refresh)

- **Sync History Table:**
  - Last 10 sync operations
  - Columns: Timestamp, Status, Records Processed, Duration
  - Status indicators: Green (success), Red (failed)
  - Shows execution time in seconds

#### **Sync Tab**
Manual control for triggering CRSA web scraper.

**Features:**
- **Manual Sync Button:**
  - Large primary action button with RefreshCw icon
  - Triggers `/api/crsa/sync/manual` endpoint
  - Shows loading state with animated spinner
  - Disabled during sync operation

- **Sync Instructions:**
  - Clear explanation of sync process
  - Bullet points describing each step:
    1. Download latest data from AGCO
    2. Parse and validate CSV
    3. Update database records
    4. Update statistics

- **Last Sync Display:**
  - Gray card showing last sync timestamp
  - Calendar icon with formatted date

- **Info Alert:**
  - Blue alert box with AlertCircle icon
  - Explains automatic sync schedule (daily 3 AM EST)
  - Notes that manual sync is optional

#### **Import Tab**
CSV file upload interface for manual data imports.

**Features:**
- **CSV Format Requirements:**
  - Code block showing required columns
  - Exact format: `License Number, Municipality or First Nation, Store Name, Address, Store Application Status, Website`

- **File Upload Dropzone:**
  - Drag-and-drop file upload area
  - Border highlights on drag hover (blue)
  - Upload icon with clear instructions
  - "Select File" button for browser file picker
  - CSV validation (file extension check)
  - 10MB max file size
  - Responsive hover states

- **File Preview:**
  - Displays after file selection
  - Shows filename and file size
  - Preview table with first 5 rows
  - Styled header row
  - Scrollable overflow for wide tables
  - "Remove" button to clear selection

- **Import Button:**
  - Primary action button with Upload icon
  - Triggers `/api/crsa/upload-csv` POST with FormData
  - Shows loading state during upload
  - Success toast with records count
  - Error handling with detailed messages

- **Warning Alert:**
  - Yellow alert box with AlertCircle icon
  - Warns about irreversible operation
  - Reminds to validate CSV format

## API Endpoints

### New Endpoints Added

#### `GET /api/crsa/sync/stats`
**Purpose:** Get comprehensive sync statistics for dashboard

**Response:**
```json
{
  "total_records": 49,
  "active_stores": 47,
  "authorized_stores": 45,
  "linked_tenants": 3,
  "last_sync": "2024-01-15T03:00:00",
  "sync_history": [
    {
      "timestamp": "2024-01-15T03:00:00",
      "status": "success",
      "records_processed": 49,
      "duration_seconds": 12
    }
  ]
}
```

#### `GET /api/crsa/records?limit=10`
**Purpose:** Get recent CRSA records for preview table

**Query Parameters:**
- `limit` (default: 10) - Maximum records to return
- `offset` (default: 0) - Pagination offset

**Response:**
```json
[
  {
    "license_number": "123456",
    "municipality": "Toronto",
    "store_name": "Example Cannabis",
    "address": "123 Main St",
    "status": "Authorized to Open",
    "website": "https://example.com",
    "last_updated": "2024-01-15T03:00:00"
  }
]
```

#### `POST /api/crsa/upload-csv`
**Purpose:** Upload and import CSV file

**Request:**
- Content-Type: `multipart/form-data`
- Body: CSV file as `file` field

**Response:**
```json
{
  "success": true,
  "message": "CSV imported successfully",
  "filename": "crsa_data.csv",
  "records_imported": 49,
  "output": "Import script output..."
}
```

**Error Cases:**
- 400: Invalid file type (not CSV)
- 500: Import script failed
- 504: Import timeout (>5 minutes)

#### `POST /api/crsa/sync/manual`
**Purpose:** Trigger manual web scraper sync (alias for `/admin/sync/manual`)

**Response:**
```json
{
  "success": true,
  "message": "Sync completed",
  "records_processed": 49,
  "records_inserted": 2,
  "records_updated": 47
}
```

### Existing Endpoints Used
- `POST /api/crsa/admin/sync/manual` - Original manual sync endpoint
- `GET /api/crsa/admin/sync/history` - Sync history (20 records)
- `GET /api/crsa/statistics` - General CRSA statistics

## Technical Implementation

### Frontend Stack
- **Framework:** React 18 + TypeScript
- **State Management:** React Query (@tanstack/react-query)
- **Routing:** React Router v6
- **Styling:** Tailwind CSS with dark mode
- **Icons:** Lucide React
- **Notifications:** react-hot-toast
- **i18n:** react-i18next (prepared, not fully implemented)

### Backend Stack
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL with asyncpg
- **File Handling:** Python tempfile + subprocess
- **Import Script:** `scripts/import_crsa_data.py`
- **Web Scraper:** `scripts/download_agco_crsa.py` (BeautifulSoup)

### File Structure
```
src/
├── Frontend/ai-admin-dashboard/src/
│   ├── pages/
│   │   └── SystemSettings/
│   │       └── CRSAManagement.tsx (NEW - 700+ lines)
│   └── App.tsx (UPDATED - added route & nav item)
└── Backend/api/
    └── ontario_crsa_endpoints.py (UPDATED - added 4 new endpoints)
```

## Data Flow

### Statistics Display
1. Component mounts → React Query fetches `/api/crsa/sync/stats`
2. Auto-refresh every 30 seconds
3. Display stats in cards + tables
4. Handle loading states and errors

### Manual Sync
1. User clicks "Run Manual Sync" button
2. POST to `/api/crsa/sync/manual`
3. Backend calls sync service
4. Sync service runs web scraper
5. Import script updates database
6. Success response invalidates queries
7. UI auto-refreshes with new data

### CSV Upload
1. User drops/selects CSV file
2. Preview first 5 rows in table
3. User clicks "Import Data"
4. Upload file via FormData to `/api/crsa/upload-csv`
5. Backend saves to temp file
6. Import script processes CSV
7. Database updated via upsert
8. Success toast shows records count
9. Queries invalidated → UI refreshes

## Database Schema

### `ontario_crsa_status` Table
Primary CRSA data storage.

**Key Columns:**
- `license_number` (PK) - Ontario retail license
- `store_name` - Store name
- `municipality` - Municipality name
- `first_nation` - First Nation name (alternative to municipality)
- `address` - Full street address
- `store_application_status` - Status (e.g., "Authorized to Open")
- `website` - Store website URL
- `linked_tenant_id` - FK to tenants table
- `is_active` - Boolean flag
- `last_synced_at` - Timestamp of last update

### `crsa_sync_history` Table
Audit log for sync operations.

**Key Columns:**
- `id` (PK) - UUID
- `sync_date` - Timestamp of sync
- `success` - Boolean flag
- `records_processed` - Total records processed
- `records_inserted` - New records added
- `records_updated` - Existing records modified
- `records_skipped` - Invalid/duplicate records
- `error_message` - Error details if failed
- `csv_source` - Path to source CSV
- `duration_seconds` - Execution time

## Error Handling

### Frontend
- **Network Errors:** Toast notification with error message
- **Invalid File:** Pre-validation before upload (CSV extension check)
- **Upload Timeout:** 5-minute timeout on backend prevents hanging
- **Empty States:** "No records found" messages in tables

### Backend
- **File Validation:** 400 error for non-CSV files
- **Import Failures:** 500 error with script stderr output
- **Database Errors:** Proper exception handling with logging
- **Timeout Protection:** subprocess timeout prevents long-running imports

## Security Considerations

1. **Authentication:** Protected by `ProtectedRoute` with `system:super_admin` permission
2. **File Upload Validation:** Only CSV files accepted, extension check
3. **Temporary File Cleanup:** Automatic deletion after import
4. **SQL Injection Prevention:** Parameterized queries with asyncpg
5. **CSRF Protection:** FastAPI default CORS handling
6. **File Size Limits:** 10MB max in UI, additional limits possible in nginx/FastAPI

## Performance Optimizations

1. **React Query Caching:** 5-minute stale time on statistics
2. **Auto-refresh Strategy:** 30s interval only on Statistics tab
3. **Lazy Loading:** Tables paginated (10 records per page)
4. **Database Indexing:** License number indexed as primary key
5. **CSV Preview:** Only parse first 6 lines for preview
6. **Async Processing:** Import runs in subprocess, non-blocking

## Testing Checklist

### Frontend
- [ ] Navigate to CRSA Management from menu
- [ ] Statistics tab loads with data
- [ ] Cards display correct counts
- [ ] Recent records table shows data
- [ ] Sync history table shows operations
- [ ] Switch to Sync tab
- [ ] Manual sync button works
- [ ] Loading states display correctly
- [ ] Switch to Import tab
- [ ] Drag-and-drop file works
- [ ] File picker works
- [ ] Preview table displays correctly
- [ ] Import button uploads file
- [ ] Success notification appears
- [ ] Data refreshes after import

### Backend
- [ ] GET /api/crsa/sync/stats returns data
- [ ] GET /api/crsa/records returns records
- [ ] POST /api/crsa/sync/manual triggers scraper
- [ ] POST /api/crsa/upload-csv accepts CSV
- [ ] CSV import script runs successfully
- [ ] Database updated with new records
- [ ] Sync history logged correctly
- [ ] Error handling works (invalid files, timeouts)

### Integration
- [ ] Upload CSV → Database updated → UI refreshes
- [ ] Manual sync → Records updated → Stats change
- [ ] Dark mode styles work correctly
- [ ] Mobile responsive layout
- [ ] Permissions enforce super admin only

## Future Enhancements

### Short Term
1. **Search & Filter:** Add search bar for records table
2. **Export:** Download current CRSA data as CSV
3. **Bulk Actions:** Select multiple records for operations
4. **Chart Visualization:** Add bar/line charts for statistics
5. **Real-time Sync Status:** WebSocket updates during long syncs

### Medium Term
1. **Sync Scheduling:** UI to configure sync frequency
2. **Email Notifications:** Alert on sync failures
3. **Audit Trail:** Detailed change history per record
4. **Data Validation Rules:** Configurable validation in UI
5. **Multi-file Upload:** Batch import multiple CSVs

### Long Term
1. **Automated Conflict Resolution:** Smart merging of duplicates
2. **Machine Learning:** Predict store authorization likelihood
3. **API Integration:** Direct AGCO API instead of scraping
4. **Multi-province Support:** Extend to other provinces
5. **Mobile App:** Native iOS/Android admin app

## Troubleshooting

### Issue: "No records found" in tables
**Cause:** Database empty or sync never run  
**Solution:** Click "Run Manual Sync" or upload CSV file

### Issue: CSV upload fails with timeout
**Cause:** Large file (>10MB) or slow import script  
**Solution:** Reduce file size, check import script performance, increase timeout

### Issue: Statistics not updating after import
**Cause:** React Query cache not invalidated  
**Solution:** Manually refresh page or check invalidateQueries calls

### Issue: Manual sync button does nothing
**Cause:** Backend sync service not initialized  
**Solution:** Check API server startup logs, verify sync service initialization

### Issue: Navigation item not visible
**Cause:** User lacks super admin permissions  
**Solution:** Verify user role in database, check permission checks in Layout

## Maintenance

### Daily
- Monitor sync history for failures
- Check sync_history table for errors

### Weekly
- Review import logs for patterns
- Verify AGCO website structure hasn't changed

### Monthly
- Archive old sync history (>90 days)
- Optimize database indexes if needed
- Review and update CSV validation rules

### Quarterly
- Update web scraper if AGCO website changes
- Review and update documentation
- Performance testing with large datasets

## Related Documentation

- [CRSA_SYNC_SETUP_GUIDE.md](CRSA_SYNC_SETUP_GUIDE.md) - Initial setup instructions
- [CRSA_NOT_PULLING_INVESTIGATION.md](CRSA_NOT_PULLING_INVESTIGATION.md) - Root cause analysis
- [MULTI_TENANT_ARCHITECTURE.md](MULTI_TENANT_ARCHITECTURE.md) - Overall system architecture
- API Documentation: `/docs` endpoint (FastAPI Swagger UI)

## Support

For issues or questions:
1. Check logs: `docker-compose logs api-server`
2. Review sync history in UI
3. Verify database connection
4. Check AGCO website availability
5. Review import script output

## Version History

### v1.0.0 (2024-01-15)
- Initial CRSA Management UI implementation
- Statistics, Sync, and Import tabs
- Real-time dashboard with auto-refresh
- CSV upload with preview
- Manual sync trigger
- Integration with existing CRSA endpoints
