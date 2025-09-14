#!/bin/bash

# Script to update all hardcoded values to use configuration
echo "Updating hardcoded values in AI Admin Dashboard..."

# Update all service files to use appConfig
FILES=(
  "src/services/storeService.ts"
  "src/services/catalogService.ts"
  "src/services/paymentService.ts"
  "src/services/tenantService.ts"
  "src/services/posService.ts"
  "src/services/storeHoursService.ts"
)

for file in "${FILES[@]}"; do
  if [ -f "$file" ]; then
    echo "Updating $file..."
    
    # Add import if not present
    if ! grep -q "import.*appConfig" "$file"; then
      sed -i '' '1s/^/import { appConfig } from '\''..\/config\/app.config'\'';\n/' "$file"
    fi
    
    # Replace hardcoded URLs
    sed -i '' "s|import.meta.env.VITE_API_URL || 'http://localhost:5024'|appConfig.api.baseUrl|g" "$file"
    sed -i '' "s|'http://localhost:5024'|appConfig.api.baseUrl|g" "$file"
    sed -i '' "s|'http://localhost:5024/api'|appConfig.api.baseUrl + '/api'|g" "$file"
  fi
done

# Update timeout values in authService.ts
echo "Updating authService.ts..."
if [ -f "src/services/authService.ts" ]; then
  sed -i '' "s|timeout: 30000|timeout: appConfig.api.timeout|g" "src/services/authService.ts"
  
  # Add import if not present
  if ! grep -q "import.*appConfig" "src/services/authService.ts"; then
    sed -i '' '1a\
import { appConfig } from '\''../config/app.config'\'';' "src/services/authService.ts"
  fi
fi

echo "Update completed!"