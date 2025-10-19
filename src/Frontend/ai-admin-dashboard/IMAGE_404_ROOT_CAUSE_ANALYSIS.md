# Product Image 404 Errors - Root Cause Analysis

**Date:** October 18, 2025
**Issue:** Multiple 404 errors for product images from Azure Blob Storage
**Domain:** `storagecdnpublicprod.blob.core.windows.net`

---

## 🔍 Problem Statement

The application is experiencing **~68+ failed image loads** with HTTP 404 errors from Azure Blob Storage CDN. All errors follow this pattern:

```
storagecdnpublicprod.blob.core.windows.net/img/{id}/{gtin}_a1cd_compressed_{id}.jpg
Failed to load resource: the server responded with a status of 404 (The specified blob does not exist.)
```

**Example URLs:**
- `storagecdnpublicprod.blob.core.windows.net/img/302419/00841432013554_a1cd_compressed_302419.jpg`
- `storagecdnpublicprod.blob.core.windows.net/img/111037/00990015301172_a1cc_compressed_111037.jpg`

---

## 🎯 Root Cause Analysis

### 1. **Data Source: OCS Provincial Catalog**

The image URLs are stored in the **`image_url`** field of the Provincial Catalog products:

**Location:** `src/types/index.ts:21` (Product interface)
```typescript
export interface Product {
  // ...
  image_url?: string;  // Optional field containing Azure Blob URL
  // ...
}
```

**Location:** `src/pages/ProvincialCatalogVirtual.tsx:42`
```typescript
interface CatalogProduct {
  // ...
  image_url: string | null;  // OCS Standard field from Excel
  // ...
}
```

### 2. **Image URL Pattern**

The URLs follow this structure:
```
https://storagecdnpublicprod.blob.core.windows.net/img/{PRODUCT_ID}/{GTIN}_{VARIANT}_compressed_{PRODUCT_ID}.jpg
```

Where:
- `{PRODUCT_ID}` = OCS product ID (e.g., 302419, 111037)
- `{GTIN}` = Global Trade Item Number (UPC/barcode, e.g., 00841432013554)
- `{VARIANT}` = Image variant code (e.g., a1cd, a1cc, a1c1, a1cg)

### 3. **Why Images Are Missing**

Several possible reasons:

#### A. **External Data Source** ⭐ **MOST LIKELY**
- These URLs come from the **OCS (Ontario Cannabis Store)** provincial catalog
- The images are hosted on **OCS's Azure CDN**, not WeedGo's infrastructure
- **WeedGo does not control** this Azure Blob Storage account
- Products may have been:
  - Discontinued by OCS
  - Had their images removed/relocated
  - Been imported with stale/incorrect URLs

#### B. **Data Import Issues**
- Provincial catalog Excel file contains outdated image URLs
- URLs were valid at time of catalog creation but images have since been removed
- Bulk import didn't validate URL accessibility

#### C. **CDN Configuration**
- URLs may require authentication/tokens
- CORS restrictions on Azure Blob Storage
- CDN cache expiration issues

#### D. **Image Naming Changes**
- OCS may have changed their image naming convention
- Variant codes (a1cd, a1cc) may have been updated
- Product IDs may have been reassigned

---

## 📊 Impact Analysis

### Affected Components

1. **`Inventory.tsx:411`** - Inventory list view
2. **`ProvincialCatalogImproved.tsx:467`** - Provincial catalog browser
3. **`POS.tsx:1190`** - Point of Sale product cards
4. **`Promotions.tsx:1612, 1737`** - Promotion product selection
5. **`Accessories.tsx:362`** - Accessories inventory

### User Experience Impact

- ❌ Broken product images throughout the application
- ❌ Difficulty identifying products visually
- ❌ Poor UX in POS and catalog browsing
- ✅ Application still **functional** (images are optional)
- ✅ Error handling prevents crashes (onError callbacks present)

### Console Noise

- **68+ console errors** per page load (when viewing inventory/catalog)
- Makes debugging other issues difficult
- Performance impact from failed network requests

---

## ✅ Current Error Handling

The application **already has error handling** for missing images:

**Example from `Inventory.tsx:414`:**
```typescript
<img
  src={item.image_url}
  alt={item.product_name || item.name}
  className="h-10 w-10 rounded-lg object-cover mr-3"
  onError={(e) => {
    const target = e.target as HTMLImageElement;
    target.style.display = 'none';
    // Gracefully hides broken images
  }}
/>
```

**Example from `POS.tsx:1193`:**
```typescript
onError={(e) => {
  const target = e.target as HTMLImageElement;
  target.src = '/placeholder-product.png';  // Fallback image
}}
```

---

## 🛠️ Recommended Solutions

### Solution 1: **Implement Robust Fallback Images** ⭐ **RECOMMENDED**

**Pros:**
- Quick implementation
- No dependency on external systems
- Consistent user experience

**Implementation:**
1. Create a utility function for safe image loading
2. Provide default product images by category
3. Update all image components to use the utility

**Priority:** 🔴 **HIGH** - Can be implemented immediately

---

### Solution 2: **Image URL Validation & Cleanup**

**Pros:**
- Removes invalid URLs from database
- Prevents future 404 errors
- Improves data quality

**Implementation:**
1. Create a batch script to validate all image URLs
2. Mark invalid URLs as null in database
3. Optionally download and host images locally

**Priority:** 🟡 **MEDIUM** - Requires backend work

---

### Solution 3: **Local Image Hosting**

**Pros:**
- Full control over images
- No dependency on OCS infrastructure
- Better performance

**Cons:**
- Requires image download and storage
- Potential copyright/licensing issues
- Storage costs

**Implementation:**
1. Download available images from OCS
2. Store in WeedGo's Azure Blob Storage or S3
3. Update database with new URLs

**Priority:** 🟢 **LOW** - Long-term solution

---

### Solution 4: **Graceful Degradation with Placeholder**

**Pros:**
- Immediate fix
- No backend changes needed
- Works with existing data

**Implementation:**
1. Create category-specific placeholder images
2. Update image components with smart fallbacks
3. Add loading states

**Priority:** 🔴 **HIGH** - Quick win

---

## 🚀 Immediate Action Plan

### Phase 1: Quick Fix (< 1 hour)

1. **Create Image Utility Function**
   - Safe image loading with fallbacks
   - Category-specific placeholders
   - Error suppression

2. **Update All Image Components**
   - Replace direct `image_url` usage
   - Use utility function everywhere
   - Consistent fallback experience

3. **Add Placeholder Images**
   - Create `/public/placeholders/` directory
   - Add images for: flower, edibles, concentrates, vapes, accessories

### Phase 2: Data Cleanup (< 1 day)

1. **Validate Existing URLs**
   - Script to test all `image_url` entries
   - Report on success/failure rates
   - Identify patterns in failures

2. **Update Database**
   - Set invalid URLs to null
   - Add `image_validated_at` timestamp
   - Track validation status

### Phase 3: Long-term Solution (< 1 week)

1. **Image Scraping/Download**
   - Attempt to download valid images
   - Store in WeedGo's CDN
   - Update URLs in database

2. **Monitoring**
   - Track image load success rates
   - Alert on high failure rates
   - Periodic URL validation

---

## 📝 Implementation Code

### 1. Image Utility Function

**File:** `src/utils/imageUtils.ts`

```typescript
/**
 * Safe Image Loading Utility
 * Provides fallback images for missing product photos
 */

const PLACEHOLDER_IMAGES = {
  flower: '/placeholders/flower.png',
  edibles: '/placeholders/edibles.png',
  concentrates: '/placeholders/concentrates.png',
  vapes: '/placeholders/vapes.png',
  accessories: '/placeholders/accessories.png',
  default: '/placeholders/product-default.png',
};

export const getProductImageUrl = (
  imageUrl: string | null | undefined,
  category?: string
): string => {
  // If no URL provided, return placeholder
  if (!imageUrl || imageUrl.trim() === '') {
    return getCategoryPlaceholder(category);
  }

  // If URL is from OCS Azure CDN, it may be invalid
  // We'll still try to load it, but have fallback ready
  return imageUrl;
};

export const getCategoryPlaceholder = (category?: string): string => {
  if (!category) return PLACEHOLDER_IMAGES.default;

  const cat = category.toLowerCase();

  if (cat.includes('flower') || cat.includes('dried')) {
    return PLACEHOLDER_IMAGES.flower;
  }
  if (cat.includes('edible') || cat.includes('food')) {
    return PLACEHOLDER_IMAGES.edibles;
  }
  if (cat.includes('concentrate') || cat.includes('extract')) {
    return PLACEHOLDER_IMAGES.concentrates;
  }
  if (cat.includes('vape') || cat.includes('cartridge')) {
    return PLACEHOLDER_IMAGES.vapes;
  }
  if (cat.includes('accessor')) {
    return PLACEHOLDER_IMAGES.accessories;
  }

  return PLACEHOLDER_IMAGES.default;
};

export const handleImageError = (
  e: React.SyntheticEvent<HTMLImageElement>,
  category?: string
) => {
  const target = e.currentTarget;

  // Prevent infinite error loop
  if (target.src.includes('/placeholders/')) {
    target.style.display = 'none';
    return;
  }

  // Set fallback image
  target.src = getCategoryPlaceholder(category);
};
```

### 2. Smart ProductImage Component

**File:** `src/components/ProductImage.tsx`

```typescript
import React from 'react';
import { getProductImageUrl, handleImageError } from '../utils/imageUtils';

interface ProductImageProps {
  src: string | null | undefined;
  alt: string;
  category?: string;
  className?: string;
  fallbackClassName?: string;
}

export const ProductImage: React.FC<ProductImageProps> = ({
  src,
  alt,
  category,
  className = '',
  fallbackClassName = '',
}) => {
  const imageUrl = getProductImageUrl(src, category);

  return (
    <img
      src={imageUrl}
      alt={alt}
      className={className}
      onError={(e) => handleImageError(e, category)}
      loading="lazy"
    />
  );
};
```

### 3. Backend URL Validation Script

**File:** `src/Backend/scripts/validate_image_urls.py`

```python
#!/usr/bin/env python3
"""
Validate Product Image URLs
Checks all image_url entries in provincial_catalog for accessibility
"""

import asyncio
import aiohttp
from sqlalchemy import create_engine, text
from typing import List, Dict

async def check_url(session: aiohttp.ClientSession, url: str, product_id: str) -> Dict:
    """Check if image URL is accessible"""
    try:
        async with session.head(url, timeout=10) as response:
            return {
                'product_id': product_id,
                'url': url,
                'status': response.status,
                'valid': response.status == 200
            }
    except Exception as e:
        return {
            'product_id': product_id,
            'url': url,
            'status': 0,
            'valid': False,
            'error': str(e)
        }

async def validate_all_images():
    """Validate all product images"""
    # Database connection
    engine = create_engine('postgresql://...')

    # Get all products with image URLs
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, image_url
            FROM provincial_catalog
            WHERE image_url IS NOT NULL
            AND image_url != ''
        """))
        products = [(row.id, row.image_url) for row in result]

    print(f"Checking {len(products)} product images...")

    # Check URLs concurrently
    async with aiohttp.ClientSession() as session:
        tasks = [check_url(session, url, pid) for pid, url in products]
        results = await asyncio.gather(*tasks)

    # Analyze results
    valid = sum(1 for r in results if r['valid'])
    invalid = len(results) - valid

    print(f"\nResults:")
    print(f"  ✅ Valid: {valid}")
    print(f"  ❌ Invalid: {invalid}")
    print(f"  Success Rate: {(valid/len(results)*100):.1f}%")

    # Update database - set invalid URLs to null
    invalid_ids = [r['product_id'] for r in results if not r['valid']]

    if invalid_ids:
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE provincial_catalog
                SET image_url = NULL,
                    image_url_validated_at = NOW(),
                    image_url_validation_status = 'invalid'
                WHERE id = ANY(:ids)
            """), {'ids': invalid_ids})
            conn.commit()

        print(f"\n✅ Cleaned up {len(invalid_ids)} invalid image URLs")

if __name__ == "__main__":
    asyncio.run(validate_all_images())
```

---

## 📊 Expected Outcomes

### After Implementing Quick Fix:
- ✅ No more 404 errors in console
- ✅ Consistent placeholder images shown
- ✅ Improved user experience
- ✅ Cleaner debugging environment

### After Data Cleanup:
- ✅ Database reflects reality (null for missing images)
- ✅ No wasted network requests
- ✅ Faster page loads

### After Long-term Solution:
- ✅ All products have valid images
- ✅ Full control over image hosting
- ✅ Better performance
- ✅ No external dependencies

---

## 🎯 Summary

### Root Cause
Product image URLs from OCS provincial catalog point to an **external Azure CDN** (`storagecdnpublicprod.blob.core.windows.net`) that:
1. Is not controlled by WeedGo
2. Contains many outdated/removed images
3. Results in 68+ 404 errors per page load

### Recommended Solution
**Implement robust fallback images** using a utility function that provides category-specific placeholders when images fail to load.

### Priority Actions
1. ✅ Create image utility function (< 30 min)
2. ✅ Add placeholder images (< 30 min)
3. ✅ Update all image components (< 2 hours)
4. ⚠️  Run URL validation script (< 4 hours)
5. ⚠️  Consider local image hosting (future sprint)

---

**Status:** Analysis Complete
**Next Step:** Implement Phase 1 (Quick Fix)
**Estimated Time:** 1-2 hours for complete resolution
