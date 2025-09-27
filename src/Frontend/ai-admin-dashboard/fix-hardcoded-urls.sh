#!/bin/bash

# Script to fix hardcoded URLs in kiosk components

echo "Fixing hardcoded URLs in kiosk components..."

# Add import statement if not present and replace URLs
for file in src/components/kiosk/*.tsx; do
  if [ -f "$file" ]; then
    echo "Processing $file..."

    # Check if import already exists
    if ! grep -q "import { getApiUrl } from '../../config/app.config';" "$file"; then
      # Add import after the first import statement
      sed -i '' "1,/^import /s/^import /import { getApiUrl } from '..\/..\/config\/app.config';\nimport /" "$file"
    fi

    # Replace hardcoded URLs with getApiUrl
    sed -i '' "s|'http://localhost:5024/|getApiUrl('/|g" "$file"
    sed -i '' 's|`http://localhost:5024/|`${getApiUrl("/|g' "$file"
    sed -i '' 's|/api/|api/|g' "$file"  # Fix double /api/
    sed -i '' 's|getApiUrl("//|getApiUrl("/|g' "$file"  # Fix double slashes
  fi
done

# Fix menuDisplay component
file="src/components/menuDisplay/MenuDisplay.tsx"
if [ -f "$file" ]; then
  echo "Processing $file..."
  if ! grep -q "import { getApiUrl } from '../../config/app.config';" "$file"; then
    sed -i '' "1,/^import /s/^import /import { getApiUrl } from '..\/..\/config\/app.config';\nimport /" "$file"
  fi
  sed -i '' 's|`http://localhost:5024/|`${getApiUrl("/|g' "$file"
fi

echo "Done!"