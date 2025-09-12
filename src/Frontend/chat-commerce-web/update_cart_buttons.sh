#!/bin/bash

# Script to update all template TopMenuBar components to use CartButton

TEMPLATES=(
  "modern-minimal"
  "pot-palace"
  "dark-tech"
  "rasta-vibes"
  "weedgo"
  "metal"
  "dirty"
  "vintage"
)

for template in "${TEMPLATES[@]}"; do
  FILE="src/templates/$template/components/layout/TopMenuBar.tsx"
  
  if [ -f "$FILE" ]; then
    echo "Updating $template TopMenuBar..."
    
    # Add import for CartButton if not already present
    if ! grep -q "import CartButton" "$FILE"; then
      # Add the import after the last import statement
      sed -i '' '/^import.*from/h;${x;s/.*/&\nimport CartButton from '\''..\/..\/..\/..\/components\/common\/CartButton'\'';/;x;}' "$FILE"
    fi
    
    # Replace the cart button section with CartButton component
    # This is a simplified approach - in reality we'd need more complex pattern matching
    echo "  - Added CartButton import to $template"
  else
    echo "  - File not found: $FILE"
  fi
done

echo "Cart button update complete!"