#!/usr/bin/env python3
"""
Add missing auth/address translation keys to all 28 language files
"""
import json
import os
from pathlib import Path

# New keys to add (in English)
NEW_AUTH_KEYS = {
    "errors": {
        "databaseConnectionFailed": "Database connection failed",
        "invalidAuthCredentials": "Invalid authentication credentials",
        "notAuthenticated": "Not authenticated - no token or X-User-Id header provided",
        "emailAlreadyRegistered": "Email already registered",
        "registrationFailed": "Registration failed. Please try again.",
        "logoutSuccessful": "Logout successful",
        "userNotFound": "User not found",
        "failedRetrieveProvinceInfo": "Failed to retrieve province information",
        "failedRetrieveUserInfo": "Failed to retrieve user information"
    },
    "address": {
        "createdSuccessfully": "Address created successfully",
        "updatedSuccessfully": "Address updated successfully",
        "deletedSuccessfully": "Address deleted successfully",
        "defaultUpdatedSuccessfully": "Default address updated successfully",
        "failedCreate": "Failed to create address",
        "failedUpdate": "Failed to update address",
        "failedDelete": "Failed to delete address",
        "failedSetDefault": "Failed to set default address",
        "notAuthorizedUpdate": "Not authorized to update this address",
        "notFoundOrNotAuthorized": "Address not found or not authorized",
        "failedRetrieve": "Failed to retrieve addresses"
    }
}

# Get locale directories
locales_dir = Path(__file__).parent.parent.parent / 'Frontend' / 'ai-admin-dashboard' / 'src' / 'i18n' / 'locales'

languages = [d.name for d in locales_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]

print(f"Found {len(languages)} languages: {', '.join(sorted(languages))}\n")
print(f"Will add {sum(len(v) for v in NEW_AUTH_KEYS.values())} new translation keys to auth.json for each language\n")

for lang in sorted(languages):
    if lang == 'en':
        print(f"✓ Skipping {lang} (already updated)")
        continue
        
    auth_file = locales_dir / lang / 'auth.json'
    
    if not auth_file.exists():
        print(f"⚠️  Skipping {lang} - auth.json not found")
        continue
    
    # Load existing translations
    with open(auth_file, 'r', encoding='utf-8') as f:
        translations = json.load(f)
    
    # Merge new keys (preserving existing translations)
    for section, keys in NEW_AUTH_KEYS.items():
        if section not in translations:
            translations[section] = {}
        for key, value in keys.items():
            if key not in translations[section]:
                # For non-English, mark as needing translation
                translations[section][key] = value if lang == 'en' else f"[TRANSLATE] {value}"
    
    # Save updated translations
    with open(auth_file, 'w', encoding='utf-8') as f:
        json.dump(translations, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Updated {lang}/auth.json")

print(f"\n✅ Complete! Added keys to {len(languages)-1} language files.")
print("\n⚠️  Keys marked with [TRANSLATE] need professional translation.")
print("   Run the translation service to auto-translate these keys.")
