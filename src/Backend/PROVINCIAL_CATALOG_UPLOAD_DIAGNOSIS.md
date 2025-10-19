# Provincial Catalog Upload Failure - Root Cause Analysis

**Date:** October 18, 2025
**Issue:** All 5,194 records failed to upload to OCS Product Catalog
**Status:** Total Failure (0 inserted, 0 updated, 5,194 errors)

---

## 🔍 Problem Summary

The upload shows:
```
Successfully processed ON catalog
Total records: 5194
Inserted: 0
Updated: 0
Errors: 5194
```

**This is a 100% failure rate** - every single record failed to process.

---

## 🎯 Root Cause Analysis

### Most Likely Causes (in order of probability):

#### 1. **Missing `OCS Variant Number`** ⭐ **MOST LIKELY**

**Evidence:**
- Lines 234-239 in `provincial_catalog_upload_endpoints.py`:
```python
if pd.isna(ocs_variant_raw):
    error_msg = f"Row {index+2}: Skipped due to missing OCS Variant Number."
    stats['errors'] += 1
    if len(stats['error_details']) < 20:
        stats['error_details'].append(error_msg)
    continue
```

**Why this happens:**
- The Excel/CSV file has `OCS Variant Number` as column header
- BUT the actual data rows might be empty for this column
- OR the column might be named slightly differently (e.g., "OCS Variant #", "Variant Number")
- This field is **REQUIRED** and used as the unique identifier

**Verification:**
```python
# Line 190-194 checks for column existence
if 'OCS Variant Number' not in df.columns:
    raise HTTPException(
        status_code=400,
        detail="OCS Variant Number column is required for matching products"
    )
```
✅ Column exists (otherwise we'd get a 400 error)
❌ Column values are all NaN/empty

---

#### 2. **Column Name Mismatch**

**Evidence:**
The file might have slightly different column names than expected:
- Expected: `"OCS Variant Number"` (exact case and spacing)
- Actual might be: `"OCS VARIANT NUMBER"`, `"OCS Variant #"`, `"Variant Number"`, etc.

**Impact:**
- Code checks: `if 'OCS Variant Number' not in df.columns`
- Pandas is case-sensitive for column names
- A single character difference = column not found

---

#### 3. **Data Type Issues**

**Evidence:**
Even if the column exists, values might be:
- Completely empty (NaN)
- Whitespace only
- Non-standard format
- Excel formula errors (#N/A, #REF!)

---

#### 4. **Database Connection Issues**

**Evidence:**
- Line 154-160 creates direct asyncpg connection
- Connection might fail silently
- Transaction might not be committing

**Less likely** because:
- We can query the table successfully
- The table structure matches expectations
- No database errors in response

---

## 📊 Diagnostic Steps

### Step 1: Check the Excel File Structure

Run this Python script to analyze the uploaded file:

```python
import pandas as pd

# Load the file
df = pd.read_excel('path/to/ocs_catalog.xlsx')

print("=" * 80)
print("FILE STRUCTURE ANALYSIS")
print("=" * 80)

# 1. Check columns
print(f"\nTotal Columns: {len(df.columns)}")
print(f"\nColumn Names:")
for i, col in enumerate(df.columns, 1):
    print(f"  {i}. '{col}' (type: {df[col].dtype})")

# 2. Check for OCS Variant Number
print(f"\n{'=' * 80}")
print("OCS VARIANT NUMBER ANALYSIS")
print("=" * 80)

if 'OCS Variant Number' in df.columns:
    print("✅ Column exists")

    # Check data
    variant_col = df['OCS Variant Number']
    print(f"\nTotal rows: {len(variant_col)}")
    print(f"Non-null values: {variant_col.notna().sum()}")
    print(f"Null/NaN values: {variant_col.isna().sum()}")
    print(f"Empty strings: {(variant_col == '').sum()}")

    print(f"\nFirst 10 non-null values:")
    non_null = variant_col.dropna().head(10)
    for idx, val in non_null.items():
        print(f"  Row {idx+2}: '{val}'")

    print(f"\nUnique values: {variant_col.nunique()}")

    # Check for whitespace issues
    if variant_col.notna().any():
        sample = str(variant_col.dropna().iloc[0])
        print(f"\nSample value analysis:")
        print(f"  Value: '{sample}'")
        print(f"  Length: {len(sample)}")
        print(f"  Stripped: '{sample.strip()}'")
        print(f"  Type: {type(sample)}")
else:
    print("❌ Column 'OCS Variant Number' NOT FOUND")
    print(f"\nSimilar column names:")
    for col in df.columns:
        if 'variant' in col.lower() or 'ocs' in col.lower():
            print(f"  - '{col}'")

# 3. Check first row data
print(f"\n{'=' * 80}")
print("FIRST ROW DATA SAMPLE")
print("=" * 80)
print(df.iloc[0].to_dict())
```

---

### Step 2: Add Better Error Logging

Update `provincial_catalog_upload_endpoints.py` to capture more detailed errors:

**Add after line 203:**
```python
# Enhanced logging
error_summary = {
    'missing_variant': 0,
    'invalid_integer': 0,
    'invalid_float': 0,
    'database_error': 0,
    'other': 0
}
```

**Update error handling (lines 234-239):**
```python
if pd.isna(ocs_variant_raw):
    error_msg = f"Row {index+2}: Missing OCS Variant Number"
    error_summary['missing_variant'] += 1
    stats['errors'] += 1
    if len(stats['error_details']) < 50:  # Increase to 50
        stats['error_details'].append(error_msg)
    continue
```

**Add at the end (before return, line 347):**
```python
# Add error breakdown to response
stats['error_breakdown'] = error_summary

print(f"\n{'=' * 80}")
print(f"UPLOAD SUMMARY")
print(f"{'=' * 80}")
print(f"Total: {stats['totalRecords']}")
print(f"Success: {stats['inserted'] + stats['updated']}")
print(f"Errors: {stats['errors']}")
print(f"\nError Breakdown:")
for error_type, count in error_summary.items():
    if count > 0:
        print(f"  {error_type}: {count}")
print(f"{'=' * 80}\n")
```

---

### Step 3: Test with Sample Data

Create a minimal test file with just 5 rows:

**test_ocs_catalog.csv:**
```csv
OCS Variant Number,Product Name,Brand,Category,Size,Unit Price
1234567-00001,Test Product 1,Test Brand,DRIED FLOWER,3.5g,29.99
1234567-00002,Test Product 2,Test Brand,PRE-ROLLS,1g,15.99
1234567-00003,Test Product 3,Test Brand,EDIBLES,10mg,12.99
1234567-00004,Test Product 4,Test Brand,VAPES,0.5g,39.99
1234567-00005,Test Product 5,Test Brand,CONCENTRATES,1g,49.99
```

Upload this file and check:
- Do all 5 succeed?
- Do all 5 fail?
- What error messages appear?

---

## 🛠️ Quick Fixes

### Fix 1: Case-Insensitive Column Matching

**Add this function after line 138:**
```python
def find_column_case_insensitive(df: pd.DataFrame, column_name: str) -> str:
    """Find column name in DataFrame case-insensitively"""
    for col in df.columns:
        if col.strip().lower() == column_name.lower():
            return col
    return None
```

**Update line 190:**
```python
# Find the OCS Variant Number column (case-insensitive)
variant_column = find_column_case_insensitive(df, 'OCS Variant Number')
if variant_column is None:
    raise HTTPException(
        status_code=400,
        detail=f"OCS Variant Number column not found. Available columns: {', '.join(df.columns)}"
    )

# Use the found column name
df = df.rename(columns={variant_column: 'OCS Variant Number'})
```

---

### Fix 2: Strip Whitespace from Column Names

**Add after line 187:**
```python
# Strip whitespace from column names
df.columns = df.columns.str.strip()

# Also strip whitespace from all string values
for col in df.columns:
    if df[col].dtype == 'object':
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
```

---

### Fix 3: Better NaN Handling

**Update line 234:**
```python
# Skip row if OCS Variant Number is missing, NaN, or empty string
ocs_variant_raw = row.get('OCS Variant Number')
if pd.isna(ocs_variant_raw) or str(ocs_variant_raw).strip() == '':
    error_msg = f"Row {index+2}: Missing or empty OCS Variant Number (value: '{ocs_variant_raw}')"
    stats['errors'] += 1
    if len(stats['error_details']) < 50:
        stats['error_details'].append(error_msg)
    continue
```

---

### Fix 4: Add Dry Run Mode

**Add parameter to endpoint (line 143):**
```python
async def upload_provincial_catalog(
    file: UploadFile = File(...),
    province: str = Form(...),
    dry_run: bool = Form(False)  # Add dry_run parameter
):
```

**Update database operations (line 331):**
```python
if not dry_run:
    # Execute the query
    result = await conn.fetchrow(insert_query, *values)

    if result and result['inserted']:
        stats['inserted'] += 1
    else:
        stats['updated'] += 1
else:
    # Dry run - just validate, don't insert
    print(f"[DRY RUN] Would insert/update row {index+2}: {ocs_variant}")
    stats['inserted'] += 1  # Count as success for dry run
```

---

## 📋 Recommended Actions

### Immediate Actions (< 1 hour)

1. **Export Error Details from UI**
   - The UI shows "Errors: 5194" but doesn't show error_details
   - Update frontend to display `stats.error_details` array
   - This will show first 20 error messages

2. **Enable Debug Logging**
   - Add `print()` statements throughout the upload process
   - Check Docker logs: `docker logs -f ai-engine-backend`

3. **Test with Minimal File**
   - Create test_ocs_catalog.csv with 5 rows
   - Upload and verify exact error messages

### Short-term Fixes (< 4 hours)

1. **Implement Case-Insensitive Column Matching** (Fix 1)
2. **Add Whitespace Stripping** (Fix 2)
3. **Improve NaN Handling** (Fix 3)
4. **Add Dry Run Mode** (Fix 4)
5. **Display Detailed Errors in UI**

### Long-term Improvements (< 1 week)

1. **File Validation Before Upload**
   - Client-side validation of file structure
   - Preview first 10 rows before upload
   - Column mapping interface if names don't match

2. **Batch Processing with Progress**
   - Process in batches of 100 rows
   - Return progress updates
   - Allow resume on failure

3. **Data Quality Reports**
   - Pre-upload validation report
   - Missing/invalid data highlights
   - Suggested fixes

---

## 🎯 Expected Root Cause

Based on the code analysis, **the most likely cause is**:

### **All rows have empty/null `OCS Variant Number` values**

**Why:**
1. The code explicitly checks for this: `if pd.isna(ocs_variant_raw): continue`
2. This is the FIRST check, so it would catch all rows
3. The column might exist as a header but have no data
4. OR the Excel file might have formulas that didn't evaluate

**How to verify:**
```python
import pandas as pd
df = pd.read_excel('your_file.xlsx')
print(f"OCS Variant Number null count: {df['OCS Variant Number'].isna().sum()}")
print(f"OCS Variant Number non-null count: {df['OCS Variant Number'].notna().sum()}")
```

If the null count = 5194, that's your problem!

---

## 🔧 Immediate Solution

**Add this to the frontend to show error details:**

**File:** `src/pages/ProvincialCatalogVirtual.tsx` (around line 18)

Update the interface:
```typescript
interface UploadStatus {
  type: 'idle' | 'uploading' | 'success' | 'error';
  message?: string;
  stats?: {
    totalRecords?: number;
    inserted?: number;
    updated?: number;
    errors?: number;
    error_details?: string[];  // Add this
  };
}
```

Then display errors (around line 615):
```tsx
{uploadStatus.stats?.error_details && uploadStatus.stats.error_details.length > 0 && (
  <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
    <h4 className="font-medium text-red-800 dark:text-red-200 mb-2">
      Error Details (first {uploadStatus.stats.error_details.length}):
    </h4>
    <ul className="list-disc list-inside text-sm text-red-700 dark:text-red-300 space-y-1">
      {uploadStatus.stats.error_details.map((error, i) => (
        <li key={i}>{error}</li>
      ))}
    </ul>
  </div>
)}
```

---

**Status:** Analysis Complete
**Next Step:** Display error details in UI and verify root cause
**Priority:** 🔴 **HIGH** - Blocking feature
