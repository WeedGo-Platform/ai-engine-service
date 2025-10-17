# Pricing Configuration System

## Overview
The WeedGo pricing system implements a **fail-fast, hierarchical pricing resolution** strategy that requires explicit pricing configuration at store or category level. As of version 2.0, the system **no longer uses hardcoded fallback values** (previously 25%) to ensure pricing accuracy and prevent revenue loss.

## Key Changes (v2.0)

### ⚠️ Breaking Change: No Hardcoded Fallback
Previously, the system would fall back to a hardcoded 25% markup when no pricing configuration was found. This has been **removed** to prevent:
- Incorrect pricing for products that require different margins
- Revenue loss from products that need higher markups
- Compliance issues with products that have regulated pricing requirements

### Fail-Fast Validation
The system now **validates all pricing configuration BEFORE starting database transactions**. If any product in a purchase order is missing pricing configuration, the entire operation fails with detailed error information including remediation steps.

## Hierarchical Pricing Resolution

The system resolves pricing using a hierarchical approach (most specific to most general):

```
1. Sub-Sub-Category Level (e.g., "Indica - Premium Flower - AAA+")
   ↓ (if not found)
2. Sub-Category Level (e.g., "Premium Flower")
   ↓ (if not found)
3. Category Level (e.g., "Indica")
   ↓ (if not found)
4. Store Default Markup
   ↓ (if not found)
5. ❌ FAIL - No pricing configuration available
```

### Example Hierarchy
For a product categorized as:
- **Category**: `Flower`
- **Sub-Category**: `Indica`
- **Sub-Sub-Category**: `Premium`

The system checks in order:
1. `pricing_rules` table: `category='Flower' AND sub_category='Indica' AND sub_sub_category='Premium'`
2. `pricing_rules` table: `category='Flower' AND sub_category='Indica' AND sub_sub_category IS NULL`
3. `pricing_rules` table: `category='Flower' AND sub_category IS NULL AND sub_sub_category IS NULL`
4. `store_settings` table: `store_id` → `settings.markup`
5. **FAIL** with detailed error message

## Database Schema

### 1. **pricing_rules** - Category-Based Pricing
Store-specific pricing rules for product categories.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| store_id | UUID | FK to stores table |
| category | VARCHAR(100) | Product category (nullable) |
| sub_category | VARCHAR(100) | Product sub-category (nullable) |
| sub_sub_category | VARCHAR(100) | Product sub-sub-category (nullable) |
| markup_percentage | DECIMAL(5,2) | Markup percentage (e.g., 25.00 = 25%) |
| effective_from | TIMESTAMP | When this rule becomes active |
| effective_until | TIMESTAMP | When this rule expires (nullable) |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

**Indexes**:
```sql
CREATE INDEX idx_pricing_rules_store_category
ON pricing_rules(store_id, category, sub_category, sub_sub_category);
```

### 2. **store_settings** - Store Default Markup
Store-level default settings stored as JSONB in the `settings` field.

```json
{
  "markup": 30.0,  // Default markup percentage for all products
  "pricing_strategy": "markup",  // or "competitive", "keystone", "cost_plus"
  "min_margin": 15.0,  // Minimum margin percentage
  "max_margin": 50.0,  // Maximum margin percentage
  "round_to": 0.99,  // Round prices to .99 (e.g., 19.99)
  "auto_adjust": false  // Automatically adjust prices based on competition
}
```

## Configuration Examples

### 1. Set Store Default Markup (Required)
Every store **MUST** have a default markup configured:

```python
# Via API
POST /api/stores/{store_id}/settings
{
  "markup": 30.0,  # 30% default markup
  "pricing_strategy": "markup",
  "min_margin": 15.0,
  "max_margin": 50.0
}
```

```sql
-- Via SQL
UPDATE store_settings
SET settings = jsonb_set(settings, '{markup}', '30.0')
WHERE store_id = 'store-uuid';
```

### 2. Configure Category-Level Pricing

```python
# Set markup for all Flower products
POST /api/v2/pricing-promotions/pricing-rules
{
  "store_id": "store-uuid",
  "category": "Flower",
  "sub_category": null,
  "sub_sub_category": null,
  "markup_percentage": 35.0  # 35% for all flower
}
```

### 3. Configure Sub-Category Pricing

```python
# Higher markup for premium flower
POST /api/v2/pricing-promotions/pricing-rules
{
  "store_id": "store-uuid",
  "category": "Flower",
  "sub_category": "Premium",
  "sub_sub_category": null,
  "markup_percentage": 45.0  # 45% for premium flower
}
```

### 4. Configure Specific Sub-Sub-Category Pricing

```python
# Even higher markup for craft cannabis
POST /api/v2/pricing-promotions/pricing-rules
{
  "store_id": "store-uuid",
  "category": "Flower",
  "sub_category": "Premium",
  "sub_sub_category": "Craft",
  "markup_percentage": 55.0  # 55% for craft products
}
```

### 5. Bulk Configuration for New Store

```python
# Configure all common categories at once
pricing_rules = [
    {"category": "Flower", "markup_percentage": 35.0},
    {"category": "Pre-Rolls", "markup_percentage": 40.0},
    {"category": "Edibles", "markup_percentage": 45.0},
    {"category": "Concentrates", "markup_percentage": 50.0},
    {"category": "Vapes", "markup_percentage": 42.0},
    {"category": "Accessories", "markup_percentage": 60.0}
]

for rule in pricing_rules:
    POST /api/v2/pricing-promotions/pricing-rules
    {
        "store_id": store_id,
        "category": rule["category"],
        "markup_percentage": rule["markup_percentage"]
    }
```

## Error Handling

### Pricing Configuration Missing Error

When attempting to receive a purchase order with missing pricing configuration, the system returns:

```json
{
  "error": "pricing_configuration_required",
  "message": "Cannot receive purchase order: 3 item(s) missing pricing configuration",
  "affected_items": [
    {
      "sku": "FLOWER-IND-001",
      "item_name": "Blue Dream 3.5g",
      "category": "Flower",
      "sub_category": "Indica",
      "sub_sub_category": "Premium",
      "unit_cost": 15.50
    },
    {
      "sku": "EDIBLE-GUM-001",
      "item_name": "THC Gummies 10mg",
      "category": "Edibles",
      "sub_category": "Gummies",
      "sub_sub_category": null,
      "unit_cost": 8.75
    }
  ],
  "remediation": {
    "required_action": "Configure pricing before receiving this purchase order",
    "options": [
      {
        "option": "Set store default markup",
        "description": "Applies to ALL products in the store",
        "endpoint": "PUT /api/stores/{store_id}/settings",
        "example_payload": {
          "markup": 30.0
        }
      },
      {
        "option": "Create category-specific pricing rules",
        "description": "Applies to all products in a category",
        "endpoint": "POST /api/v2/pricing-promotions/pricing-rules",
        "example_payload": {
          "category": "Flower",
          "markup_percentage": 35.0
        }
      },
      {
        "option": "Create granular pricing rules",
        "description": "Most specific, applies to sub-category or sub-sub-category",
        "endpoint": "POST /api/v2/pricing-promotions/pricing-rules",
        "example_payload": {
          "category": "Flower",
          "sub_category": "Indica",
          "sub_sub_category": "Premium",
          "markup_percentage": 45.0
        }
      }
    ]
  }
}
```

### Frontend Error Display

The admin dashboard displays a user-friendly error dialog:

```typescript
// Example error handling in React
if (error.error === 'pricing_configuration_required') {
  showPricingConfigurationDialog({
    affectedItems: error.affected_items,
    remediationOptions: error.remediation.options,
    onConfigure: (option) => {
      // Navigate to pricing configuration page
      navigate('/pricing', { state: { option, items: error.affected_items } });
    }
  });
}
```

## Implementation Details

### Service Layer: `InventoryService._get_applicable_markup()`

```python
async def _get_applicable_markup(
    self,
    store_id: UUID,
    category: Optional[str],
    sub_category: Optional[str],
    sub_sub_category: Optional[str]
) -> Optional[float]:
    """
    Get applicable markup percentage for a product.
    Returns None if no pricing configuration is found (fail-fast approach).

    Resolution order:
    1. Most specific pricing rule (all 3 levels match)
    2. Sub-category level (2 levels match)
    3. Category level (1 level matches)
    4. Store default markup from settings
    5. None (triggers error)
    """

    # Try to find specific pricing rule
    query = """
        SELECT markup_percentage
        FROM pricing_rules
        WHERE store_id = $1
          AND (category = $2 OR (category IS NULL AND $2 IS NULL))
          AND (sub_category = $3 OR (sub_category IS NULL AND $3 IS NULL))
          AND (sub_sub_category = $4 OR (sub_sub_category IS NULL AND $4 IS NULL))
          AND (effective_from IS NULL OR effective_from <= NOW())
          AND (effective_until IS NULL OR effective_until > NOW())
        ORDER BY
          CASE WHEN sub_sub_category IS NOT NULL THEN 1
               WHEN sub_category IS NOT NULL THEN 2
               WHEN category IS NOT NULL THEN 3
               ELSE 4 END
        LIMIT 1
    """

    result = await self.db.fetchrow(query, store_id, category, sub_category, sub_sub_category)

    if result:
        return float(result['markup_percentage'])

    # Fall back to store default markup
    settings_query = """
        SELECT settings->'markup' as markup
        FROM store_settings
        WHERE store_id = $1
    """
    settings = await self.db.fetchrow(settings_query, store_id)
    if settings and settings['markup']:
        return float(settings['markup'])

    # No pricing configuration found - return None to trigger fail-fast
    return None
```

### Pre-Transaction Validation

```python
async def receive_purchase_order(self, po_id: UUID, received_items: List[Dict[str, Any]]) -> bool:
    """
    Process receipt of purchase order items with fail-fast validation.

    Validates ALL items have pricing configuration BEFORE starting transaction.
    """

    # Get store_id from purchase order
    store_query = "SELECT store_id FROM purchase_orders WHERE id = $1"
    store_id = await self.db.fetchval(store_query, po_id)

    # PRE-VALIDATE: Check pricing configuration for all items
    items_missing_pricing = []

    for item in received_items:
        # Get product category information
        product_query = """
            SELECT category, sub_category, sub_sub_category
            FROM provincial_catalog
            WHERE sku = $1
        """
        product_cat = await self.db.fetchrow(product_query, item['sku'])

        # Check if markup is available
        markup_percentage = await self._get_applicable_markup(
            store_id,
            product_cat.get('category') if product_cat else None,
            product_cat.get('sub_category') if product_cat else None,
            product_cat.get('sub_sub_category') if product_cat else None
        )

        if markup_percentage is None:
            items_missing_pricing.append({
                'sku': item['sku'],
                'item_name': item.get('item_name', 'Unknown'),
                'category': product_cat.get('category') if product_cat else None,
                'sub_category': product_cat.get('sub_category') if product_cat else None,
                'sub_sub_category': product_cat.get('sub_sub_category') if product_cat else None,
                'unit_cost': item.get('unit_cost')
            })

    # If any items are missing pricing configuration, fail fast
    if items_missing_pricing:
        error_details = {
            'error': 'pricing_configuration_required',
            'message': f'Cannot receive purchase order: {len(items_missing_pricing)} item(s) missing pricing configuration',
            'affected_items': items_missing_pricing,
            'remediation': { /* ... remediation steps ... */ }
        }
        raise ValueError(str(error_details))

    # All items have pricing - proceed with transaction
    async with self.db.transaction():
        # ... process items ...
```

## Best Practices

### 1. Configure Defaults First
Always set store default markup before receiving inventory:

```python
# Step 1: Create store
store = create_store(...)

# Step 2: IMMEDIATELY set default pricing
update_store_settings(store.id, {"markup": 30.0})

# Step 3: Now you can receive inventory
receive_purchase_order(...)
```

### 2. Use Category-Level Rules for Bulk Products
For large product catalogs, configure at category level instead of per-product:

```python
# ✅ Good: Configure once for all flower
create_pricing_rule(category="Flower", markup=35.0)

# ❌ Bad: Configure for each individual flower product
# (too many rules to maintain)
```

### 3. Reserve Granular Rules for Exceptions
Use sub-category and sub-sub-category rules only when needed:

```python
# Category default: 35%
create_pricing_rule(category="Flower", markup=35.0)

# Exception: Premium craft flower needs higher margin
create_pricing_rule(
    category="Flower",
    sub_category="Premium",
    sub_sub_category="Craft",
    markup=55.0
)
```

### 4. Test Pricing Before Bulk Operations
Use the pricing preview endpoint before processing large purchase orders:

```python
# Preview pricing for all items
POST /api/v2/pricing-promotions/preview
{
  "store_id": "store-uuid",
  "items": [
    {"sku": "FLOWER-001", "unit_cost": 15.50},
    {"sku": "EDIBLE-001", "unit_cost": 8.75}
  ]
}

# Response shows calculated prices and any missing configuration
{
  "items": [
    {
      "sku": "FLOWER-001",
      "unit_cost": 15.50,
      "markup_percentage": 35.0,
      "retail_price": 20.93,
      "has_pricing": true
    },
    {
      "sku": "EDIBLE-001",
      "unit_cost": 8.75,
      "markup_percentage": null,
      "retail_price": null,
      "has_pricing": false,
      "error": "No pricing configuration found"
    }
  ]
}
```

## API Endpoints

```
# Pricing Rules
POST   /api/v2/pricing-promotions/pricing-rules           - Create pricing rule
GET    /api/v2/pricing-promotions/pricing-rules           - List pricing rules
GET    /api/v2/pricing-promotions/pricing-rules/{id}      - Get specific rule
PUT    /api/v2/pricing-promotions/pricing-rules/{id}      - Update pricing rule
DELETE /api/v2/pricing-promotions/pricing-rules/{id}      - Delete pricing rule

# Store Settings
PUT    /api/stores/{id}/settings                          - Update store settings (including markup)
GET    /api/stores/{id}/settings                          - Get store settings

# Pricing Preview
POST   /api/v2/pricing-promotions/preview                 - Preview pricing for items

# Bulk Operations
POST   /api/v2/pricing-promotions/bulk-pricing-rules      - Create multiple rules at once
PUT    /api/v2/pricing-promotions/bulk-update-markup      - Update markup for category
```

## Migration Guide

### Upgrading from v1.x (with hardcoded fallback)

**Step 1: Audit Current Stores**
```sql
-- Find stores without default markup
SELECT s.id, s.name, s.store_code
FROM stores s
LEFT JOIN store_settings ss ON s.id = ss.store_id
WHERE ss.settings->>'markup' IS NULL OR ss.settings->>'markup' = '';
```

**Step 2: Set Default Markup for All Stores**
```sql
-- Set 30% default for all stores missing markup
UPDATE store_settings ss
SET settings = jsonb_set(settings, '{markup}', '30.0')
WHERE settings->>'markup' IS NULL OR settings->>'markup' = ''
RETURNING store_id;
```

**Step 3: Configure Category-Level Pricing**
```sql
-- Add category rules for common product types
INSERT INTO pricing_rules (id, store_id, category, markup_percentage, created_at)
SELECT
  gen_random_uuid(),
  s.id,
  unnest(ARRAY['Flower', 'Pre-Rolls', 'Edibles', 'Concentrates', 'Vapes', 'Accessories']),
  unnest(ARRAY[35.0, 40.0, 45.0, 50.0, 42.0, 60.0]),
  NOW()
FROM stores s;
```

**Step 4: Test with Preview Endpoint**
```bash
# Test that all products now have pricing
curl -X POST http://localhost:5024/api/v2/pricing-promotions/preview \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "store-uuid",
    "items": [/* all SKUs */]
  }'
```

**Step 5: Deploy v2.0**
Once all stores have pricing configuration, deploy the new version with fail-fast validation.

## Troubleshooting

### Problem: Purchase Order Reception Fails

**Symptom**: Error message "Cannot receive purchase order: X item(s) missing pricing configuration"

**Solution**: Check the `affected_items` array in the error response and configure pricing for those categories:

```python
# From error response, get the categories
affected_categories = set(item['category'] for item in error['affected_items'])

# Configure pricing for each category
for category in affected_categories:
    create_pricing_rule(
        store_id=store_id,
        category=category,
        markup_percentage=35.0  # adjust as needed
    )
```

### Problem: Wrong Prices Being Calculated

**Symptom**: Retail prices don't match expected values

**Solution**: Check pricing rule hierarchy - more specific rules override general ones:

```sql
-- Show all pricing rules for a store, ordered by specificity
SELECT
  category,
  sub_category,
  sub_sub_category,
  markup_percentage,
  CASE
    WHEN sub_sub_category IS NOT NULL THEN 'Sub-Sub-Category (Most Specific)'
    WHEN sub_category IS NOT NULL THEN 'Sub-Category'
    WHEN category IS NOT NULL THEN 'Category'
    ELSE 'Should use store default'
  END as specificity_level
FROM pricing_rules
WHERE store_id = $1
ORDER BY
  CASE WHEN sub_sub_category IS NOT NULL THEN 1
       WHEN sub_category IS NOT NULL THEN 2
       WHEN category IS NOT NULL THEN 3
       ELSE 4 END;
```

### Problem: Store Default Markup Not Working

**Symptom**: System reports no pricing configuration even though store has default markup

**Solution**: Verify the markup is stored correctly in JSONB:

```sql
-- Check store settings
SELECT
  store_id,
  settings->>'markup' as markup,
  pg_typeof(settings->'markup') as markup_type
FROM store_settings
WHERE store_id = $1;

-- Should return a numeric value, not null
-- If null, update it:
UPDATE store_settings
SET settings = jsonb_set(settings, '{markup}', '30.0')
WHERE store_id = $1;
```

## Performance Considerations

### Indexing Strategy
```sql
-- Essential indexes for pricing queries
CREATE INDEX idx_pricing_rules_store_category
ON pricing_rules(store_id, category, sub_category, sub_sub_category);

CREATE INDEX idx_pricing_rules_effective_dates
ON pricing_rules(effective_from, effective_until)
WHERE effective_from IS NOT NULL OR effective_until IS NOT NULL;

-- For store settings lookup
CREATE INDEX idx_store_settings_store_id
ON store_settings(store_id);
```

### Caching
Consider caching pricing rules at the application level:

```python
from functools import lru_cache
from datetime import datetime, timedelta

class PricingCache:
    def __init__(self, ttl_seconds=300):  # 5 minute cache
        self.cache = {}
        self.ttl = timedelta(seconds=ttl_seconds)

    def get_markup(self, store_id, category, sub_cat, sub_sub_cat):
        key = (store_id, category, sub_cat, sub_sub_cat)
        if key in self.cache:
            value, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.ttl:
                return value
        return None

    def set_markup(self, store_id, category, sub_cat, sub_sub_cat, markup):
        key = (store_id, category, sub_cat, sub_sub_cat)
        self.cache[key] = (markup, datetime.now())
```

## Security Considerations

1. **Role-Based Access Control**: Only users with `pricing:write` permission can modify pricing rules
2. **Audit Trail**: All pricing changes are logged with user ID and timestamp
3. **Validation**: Markup percentages are validated (typically 0-200%)
4. **Rate Limiting**: Pricing configuration endpoints are rate-limited to prevent abuse

## Compliance & Regulations

### Canadian Cannabis Pricing Regulations
- Minimum pricing floors (varies by province)
- Maximum markup caps (in some provinces)
- Tax calculation requirements (excise + provincial + federal)

Store default markup should be set considering all regulatory requirements:

```python
# Example: Ontario with regulatory constraints
default_markup = calculate_compliant_markup(
    min_floor=provincial_min_floor,  # From province regulations
    max_cap=provincial_max_cap,      # From province regulations
    target_margin=30.0,              # Store's target
    tax_rate=13.0                    # HST in Ontario
)
```

---

## Summary

The v2.0 pricing system requires **explicit configuration** at either:
1. **Store level** (default markup in settings), OR
2. **Category level** (pricing rules for specific product categories)

The system uses **fail-fast validation** to ensure all products have pricing configuration before processing inventory operations. This prevents revenue loss and ensures pricing accuracy across your entire product catalog.

**Key Takeaways**:
- ✅ Always configure store default markup first
- ✅ Use category-level rules for product groups
- ✅ Reserve granular rules for exceptions
- ✅ Test with preview endpoint before bulk operations
- ❌ Never assume default pricing exists
- ❌ Don't rely on hardcoded fallbacks (they're gone!)
