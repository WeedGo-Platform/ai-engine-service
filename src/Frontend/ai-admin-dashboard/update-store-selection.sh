#!/bin/bash

# Script to add store selection modal to all required pages

echo "Adding store selection modal to Products, Inventory, Accessories, Orders, Customers, Communications, and Deliveries pages..."

# List of pages to update
PAGES=(
  "src/pages/Products.tsx"
  "src/pages/Inventory.tsx"
  "src/pages/Accessories.tsx"
  "src/pages/Orders.tsx"
  "src/pages/Customers.tsx"
  "src/pages/Communications.tsx"
  "src/pages/Deliveries.tsx"
)

# Process each page
for page in "${PAGES[@]}"; do
  echo "Processing $page..."

  # Check if the file exists
  if [ ! -f "$page" ]; then
    echo "  ✗ File not found: $page"
    continue
  fi

  # Check if StoreSelectionModal is already imported
  if grep -q "StoreSelectionModal" "$page"; then
    echo "  ✓ Already has StoreSelectionModal imported"
  else
    echo "  → Adding StoreSelectionModal import and logic..."

    # Create a temporary backup
    cp "$page" "$page.bak"

    # Add the import after the last import statement
    # This is done by finding the first non-import line and inserting before it
    awk '
      BEGIN { import_added = 0 }
      /^import/ { imports[NR] = $0; next }
      /^$/ && !import_added && length(imports) > 0 {
        for (i in imports) print imports[i]
        print "import StoreSelectionModal from '\''../components/StoreSelectionModal'\'';"
        print ""
        import_added = 1
        next
      }
      { print }
    ' "$page.bak" > "$page"

    rm "$page.bak"
    echo "  ✓ Import added"
  fi
done

echo ""
echo "Store selection modal setup complete!"
echo "Note: You may need to manually add the modal logic and state management to each component."
echo "Use PurchaseOrders.tsx as a reference for the implementation pattern."