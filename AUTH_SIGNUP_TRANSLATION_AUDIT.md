# Auth/Signup Translation Audit - Summary

## What Was Done

### 1. Identified Hardcoded Strings
- **Total hardcoded strings found:** 35
  - `customer_auth.py`: 29 strings  
  - `auth_otp.py`: 6 strings

### 2. Updated English Base File
- ✅ Added 20 new translation keys to `src/Frontend/ai-admin-dashboard/src/i18n/locales/en/auth.json`
- New sections added:
  - `errors`: 9 new keys (database errors, authentication, registration)
  - `address`: 11 new keys (address management CRUD operations)

### 3. Propagated Keys to All 28 Languages
- ✅ Updated auth.json for all 28 supported languages:
  - ar, bn, cr, de, es, fa, fr, gu, he, hi, it, iu, ja, ko, nl, pa, pl, pt, ro, ru, so, ta, tl, uk, ur, vi, yue, zh
- Keys marked with `[TRANSLATE]` prefix for easy identification

## What Needs Translation

Each of the 28 languages needs these 20 strings translated:

### Error Messages (9)
1. "Database connection failed"
2. "Invalid authentication credentials"
3. "Not authenticated - no token or X-User-Id header provided"
4. "Email already registered"
5. "Registration failed. Please try again."
6. "Logout successful"
7. "User not found"
8. "Failed to retrieve province information"
9. "Failed to retrieve user information"

### Address Management (11)
1. "Address created successfully"
2. "Address updated successfully"
3. "Address deleted successfully"
4. "Default address updated successfully"
5. "Failed to create address"
6. "Failed to update address"
7. "Failed to delete address"
8. "Failed to set default address"
9. "Not authorized to update this address"
10. "Address not found or not authorized"
11. "Failed to retrieve addresses"

## Translation Statistics
- **Total keys per language:** 20
- **Total languages:** 28
- **Total translations needed:** 560 (20 × 28)

## Files Modified
- ✅ `src/Frontend/ai-admin-dashboard/src/i18n/locales/en/auth.json` - Updated with new keys
- ✅ All 28 language `auth.json` files - Keys added with `[TRANSLATE]` markers

## Next Steps

### Option 1: Manual Professional Translation
- Hire translators to replace `[TRANSLATE]` markers with proper translations
- Ensures highest quality, especially for legal/compliance text

### Option 2: AI Translation Service
- Use backend translation service (needs fixing - has dependencies issues)
- Batch translate all `[TRANSLATE]` marked strings
- Review and approve AI translations

### Option 3: Hybrid Approach
- Use AI for initial translation
- Professional review for critical messages (errors, legal text)

## Translation Service Issues Found
The backend translation service has configuration issues:
- Missing `httpx` module
- Database schema constraint issues (`target_language` null constraint)
- Missing TaskType.TRANSLATION attribute

## Files Created
1. `src/Backend/data/translations/auth_signup_keys.json` - Source translation keys
2. `scripts/add_auth_translation_keys.py` - Script to add keys to all languages
3. `scripts/translate_auth_files.py` - Auto-translation script (needs fixing)

## Recommendation
Since the translation service needs fixes, **manually translate the 20 strings** or use a simple OpenAI/Claude API call to batch translate. The structure is ready - just need to replace `[TRANSLATE]` prefixes with actual translations.

## Quick Validation
```bash
# Count remaining [TRANSLATE] markers per language
for lang in ar bn cr de es fa fr gu he hi it iu ja ko nl pa pl pt ro ru so ta tl uk ur vi yue zh; do
  count=$(grep -c "\[TRANSLATE\]" src/Frontend/ai-admin-dashboard/src/i18n/locales/$lang/auth.json 2>/dev/null || echo "0")
  echo "$lang: $count"
done
```

Expected: Each language should show "20" until translated.
