#!/bin/bash

# Update color classes from green to primary theme
echo "Updating color scheme from green to primary..."

# Update button colors
find src -type f \( -name "*.tsx" -o -name "*.jsx" \) -exec sed -i '' \
  -e 's/bg-green-600/bg-primary-600/g' \
  -e 's/bg-green-700/bg-primary-700/g' \
  -e 's/bg-green-500/bg-primary-500/g' \
  -e 's/hover:bg-green-700/hover:bg-primary-700/g' \
  -e 's/hover:bg-green-600/hover:bg-primary-600/g' \
  -e 's/hover:bg-green-500/hover:bg-primary-500/g' \
  -e 's/focus:ring-green-500/focus:ring-primary-500/g' \
  -e 's/focus:border-green-500/focus:border-primary-500/g' \
  -e 's/text-green-600/text-primary-600/g' \
  -e 's/text-green-700/text-primary-700/g' \
  -e 's/text-green-500/text-primary-500/g' \
  -e 's/hover:text-green-700/hover:text-primary-700/g' \
  -e 's/hover:text-green-600/hover:text-primary-600/g' \
  -e 's/hover:text-green-500/hover:text-primary-500/g' \
  -e 's/border-green-600/border-primary-600/g' \
  -e 's/border-green-500/border-primary-500/g' \
  -e 's/border-green-300/border-primary-300/g' \
  -e 's/bg-green-50/bg-primary-50/g' \
  -e 's/bg-green-100/bg-primary-100/g' \
  -e 's/text-green-800/text-primary-800/g' \
  -e 's/text-green-900/text-primary-900/g' \
  {} \;

# Update secondary button styles
find src -type f \( -name "*.tsx" -o -name "*.jsx" \) -exec sed -i '' \
  -e 's/bg-blue-600/bg-accent-600/g' \
  -e 's/bg-blue-700/bg-accent-700/g' \
  -e 's/bg-blue-500/bg-accent-500/g' \
  -e 's/hover:bg-blue-700/hover:bg-accent-700/g' \
  -e 's/hover:bg-blue-600/hover:bg-accent-600/g' \
  -e 's/text-blue-600/text-accent-600/g' \
  -e 's/text-blue-700/text-accent-700/g' \
  -e 's/text-blue-500/text-accent-500/g' \
  -e 's/hover:text-blue-700/hover:text-accent-700/g' \
  -e 's/hover:text-blue-600/hover:text-accent-600/g' \
  {} \;

# Update status colors
find src -type f \( -name "*.tsx" -o -name "*.jsx" \) -exec sed -i '' \
  -e 's/bg-red-50/bg-danger-50/g' \
  -e 's/bg-red-100/bg-danger-100/g' \
  -e 's/bg-red-600/bg-danger-600/g' \
  -e 's/text-red-600/text-danger-600/g' \
  -e 's/text-red-800/text-danger-800/g' \
  -e 's/bg-yellow-50/bg-warning-50/g' \
  -e 's/bg-yellow-100/bg-warning-100/g' \
  -e 's/bg-yellow-600/bg-warning-600/g' \
  -e 's/text-yellow-600/text-warning-600/g' \
  -e 's/text-yellow-800/text-warning-800/g' \
  {} \;

echo "Color scheme update complete!"