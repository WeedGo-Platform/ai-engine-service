#!/bin/bash

echo "Updating table and card styles to modern minimal design..."

# Update shadow styles - from heavy shadows to minimal borders
find src -type f \( -name "*.tsx" -o -name "*.jsx" \) -exec sed -i '' \
  -e 's/shadow-lg/border border-gray-200/g' \
  -e 's/shadow-xl/border border-gray-200/g' \
  -e 's/shadow-md/border border-gray-200/g' \
  -e 's/shadow-sm//g' \
  -e 's/shadow//g' \
  {} \;

# Update rounded corners - more consistent rounded styles
find src -type f \( -name "*.tsx" -o -name "*.jsx" \) -exec sed -i '' \
  -e 's/rounded-md/rounded-lg/g' \
  -e 's/rounded-sm/rounded-md/g' \
  -e 's/rounded-xl/rounded-xl/g' \
  {} \;

# Update table header styles
find src -type f \( -name "*.tsx" -o -name "*.jsx" \) -exec sed -i '' \
  -e 's/bg-gray-100/bg-gray-50/g' \
  -e 's/bg-gray-200/bg-gray-100/g' \
  -e 's/text-gray-900 font-semibold/text-gray-700 font-medium text-sm/g' \
  -e 's/text-gray-800 font-semibold/text-gray-700 font-medium text-sm/g' \
  {} \;

# Update table row hover states
find src -type f \( -name "*.tsx" -o -name "*.jsx" \) -exec sed -i '' \
  -e 's/hover:bg-gray-100/hover:bg-gray-50/g' \
  -e 's/hover:bg-gray-200/hover:bg-gray-100/g' \
  {} \;

# Update card padding and spacing
find src -type f \( -name "*.tsx" -o -name "*.jsx" \) -exec sed -i '' \
  -e 's/p-4/p-6/g' \
  -e 's/p-3/p-4/g' \
  -e 's/py-2 px-4/py-2.5 px-4/g' \
  -e 's/py-1 px-2/py-1.5 px-3/g' \
  {} \;

# Update divider styles
find src -type f \( -name "*.tsx" -o -name "*.jsx" \) -exec sed -i '' \
  -e 's/border-gray-300/border-gray-200/g' \
  -e 's/border-gray-400/border-gray-300/g' \
  -e 's/divide-gray-300/divide-gray-200/g' \
  {} \;

echo "Table and card style updates complete!"