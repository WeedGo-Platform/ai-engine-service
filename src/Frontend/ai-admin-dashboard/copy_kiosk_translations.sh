#!/bin/bash

# Copy kiosk.json to all language directories
SOURCE_EN="src/i18n/locales/en/kiosk.json"
SOURCE_FR="src/i18n/locales/fr/kiosk.json"

# Array of all language codes
LANGUAGES=(ar bn cr de es fa gu he hi it iu ja ko nl pa pl pt ro ru so ta tl uk ur vi yue zh)

echo "Copying kiosk.json to all language directories..."

for lang in "${LANGUAGES[@]}"; do
    TARGET="src/i18n/locales/$lang/kiosk.json"
    
    # Use French translation for French-related languages
    if [ "$lang" == "fr" ]; then
        continue # Already created
    fi
    
    # For all other languages, copy English as base (to be translated later)
    echo "Creating $TARGET"
    cp "$SOURCE_EN" "$TARGET"
done

echo "Done! Created kiosk.json in ${#LANGUAGES[@]} languages"
echo "Note: All files except fr/ are in English and need translation"
