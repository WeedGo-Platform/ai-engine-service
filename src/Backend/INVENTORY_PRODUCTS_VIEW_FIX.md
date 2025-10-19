# Inventory Products View Fix Report

## Problem Summary

The POS system was encountering a **500 Internal Server Error** when attempting to fetch product details:

```
GET http://localhost:5024/api/products/details/105000_28g___?store_id=... 500 (Internal Server Error)
```

### Root Cause

The error was caused by a **missing database view**: `inventory_products_view`

```json
{"detail":"relation \"inventory_products_view\" does not exist"}
```

The view existed in the legacy database (`ai-engine-db` on port 5433) but was **never migrated** to the new PostGIS database (`ai-engine-db-postgis` on port 5434).

## Investigation Approach

Following the recommended approach, we:

1. ✅ Connected to the legacy `ai-engine-db` database
2. ✅ Discovered the `inventory_products_view` definition  
3. ✅ Identified all dependent objects:
   - 2 trigger functions
   - 2 triggers
   - 28 indexes (11 missing in PostGIS DB)
4. ✅ Migrated everything to `ai-engine-db-postgis`

## Discovered Objects from Legacy DB

### Views
- `inventory_products_view` - Main view combining product catalog and inventory data
- `comprehensive_product_inventory_view` - Extended version (not currently needed)

### Functions
```sql
update_inventory_timestamp()
update_product_catalog_updated_at()
```

### Triggers
```sql
update_ocs_inventory_timestamp_trigger
trigger_update_ocs_product_catalog_updated_at
```

### Indexes Migrated
**ocs_product_catalog:**
- `idx_product_catalog_ocs_rating_count`
- `idx_product_catalog_ocs_slug`
- `idx_product_catalog_ocs_strain_type`
- `idx_products_name`
- `idx_products_plant_type`
- `idx_products_price`
- `idx_products_subcategory`

**ocs_inventory:**
- `idx_ocs_inventory_each_gtin`
- `idx_ocs_inventory_quantity`
- `idx_ocs_inventory_store`
- `idx_ocs_inventory_supplier`

## The View Definition

The `inventory_products_view` is a LEFT JOIN between:
- `ocs_product_catalog` (p) - Product catalog data
- `ocs_inventory` (i) - Store inventory data

**Join condition:**
```sql
LEFT JOIN ocs_inventory i 
  ON lower(TRIM(BOTH FROM i.sku)) = lower(TRIM(BOTH FROM p.ocs_variant_number))
```

**Key calculated fields:**
- `in_stock` - Boolean based on quantity_available > 0
- `stock_status` - 'in_stock', 'low_stock', or 'out_of_stock'
- `effective_price` - COALESCE(retail_price, unit_price)
- `thc_range_min/max`, `cbd_range_min/max` - For filtering

**Total fields returned:** 95 columns covering:
- Product details (name, brand, category, descriptions)
- Cannabinoid content (THC/CBD percentages and ranges)
- Physical specifications (dimensions, weight, pack size)
- Inventory data (quantities, pricing, stock levels)
- Production info (grow method, region, drying method)
- Hardware specs (for vapes/accessories)

## Solution Applied

Created migration file: `database/migrations/create_inventory_products_view_complete.sql`

This migration includes:
1. Trigger functions for auto-updating timestamps
2. Triggers on both tables
3. Missing indexes for query performance
4. The complete `inventory_products_view` definition
5. Permissions grant

## Migration Results

```
CREATE FUNCTION (2)
CREATE TRIGGER (2)
CREATE INDEX (11)
CREATE VIEW (1)
GRANT
```

**Verification:**
```
inventory_products_view migration completed successfully | total_products: 5194
```

## Testing & Verification

### Before Fix:
```bash
curl "http://localhost:5024/api/products/details/105000_28g___?store_id=..."
# Response: 500 - relation "inventory_products_view" does not exist
```

### After Fix:
```bash
curl "http://localhost:5024/api/products/details/105000_28g___?store_id=..."
# Response: 200 OK
```

**Sample Response:**
```json
{
  "basic_info": {
    "product_name": "11 Week Pink",
    "ocs_variant_number": "105000_28g___",
    "brand": "Broken Coast Cannabis",
    ...
  },
  "pricing": {
    "unit_price": 69.5,
    "retail_price": 83.4,
    "effective_price": 83.4
  },
  "inventory": {
    "quantity_on_hand": 150,
    "in_stock": true,
    "stock_status": "in_stock"
  },
  ...
}
```

## Files Created

1. `/database/migrations/create_inventory_products_view_complete.sql` - Complete migration script
2. `INVENTORY_PRODUCTS_VIEW_FIX.md` - This documentation

## Technical Details

### Affected Endpoints
- `GET /api/products/details/{product_id}` - Main product details endpoint
- `GET /api/products/by-slug` - SEO-friendly product lookup
- Any other endpoints relying on `inventory_products_view`

### Performance Considerations
- The view uses LEFT JOIN to ensure products without inventory still appear
- Case-insensitive SKU matching with `lower(TRIM())`
- Indexes on both sides of the join for optimal performance
- Pre-calculated fields reduce computation at query time

### Database Compatibility
- Migration is idempotent (uses `IF NOT EXISTS`, `CREATE OR REPLACE`)
- Compatible with PostgreSQL 12+
- Works with both standard PostgreSQL and PostGIS extension

## Impact

✅ **Fixed:** POS system can now load product details  
✅ **Fixed:** Inventory queries now work correctly  
✅ **Improved:** Query performance with additional indexes  
✅ **Maintained:** Automatic timestamp updates via triggers  

## Prevention

To prevent similar issues in the future:

1. **Document all custom database objects** (views, triggers, functions)
2. **Include migrations for ALL DB objects** when setting up new instances
3. **Maintain parity** between legacy and new databases during transition period
4. **Test critical endpoints** against new DB before switching
5. **Use migration tracking** to ensure all migrations are applied

## Credits

- **Error discovered:** POS.tsx frontend (line 724)
- **Root cause identified:** Missing `inventory_products_view` in PostGIS DB
- **Investigation approach:** Compare legacy DB vs current DB
- **Resolution:** Complete migration of view + dependencies
- **Fix verified:** Endpoint now returns 200 OK with complete product data

---

**Date:** 2025-10-18  
**Database:** ai-engine (PostGIS)  
**Migration File:** `create_inventory_products_view_complete.sql`  
**Products Affected:** 5,194
