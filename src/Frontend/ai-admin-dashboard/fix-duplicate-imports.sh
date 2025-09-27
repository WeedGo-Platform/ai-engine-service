#!/bin/bash

# Script to remove duplicate getApiUrl imports from kiosk components

echo "Fixing duplicate imports..."

# Function to remove duplicate import from a file
fix_file() {
    local file=$1
    echo "Processing $file..."

    # Remove the first line if it's the duplicate import
    if head -n 1 "$file" | grep -q "import { getApiUrl }"; then
        # Check if line 3 also has the same import
        if sed -n '3p' "$file" | grep -q "import { getApiUrl }"; then
            # Remove the first line (duplicate import)
            sed -i '' '1d' "$file"
            echo "  Fixed duplicate import in $file"
        fi
    fi
}

# Fix all kiosk components
for file in src/components/kiosk/*.tsx; do
    if [ -f "$file" ]; then
        fix_file "$file"
    fi
done

# Also check other components that might have been affected
for file in src/components/menuDisplay/*.tsx src/components/accessories/*.tsx; do
    if [ -f "$file" ]; then
        fix_file "$file"
    fi
done

echo "Done! All duplicate imports have been fixed."