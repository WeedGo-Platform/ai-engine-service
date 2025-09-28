#!/bin/bash

# Auto-detect and update IP address for Expo app

echo "🔍 Detecting current IP address..."

# Get current IP address (macOS/Linux compatible)
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CURRENT_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
else
    # Linux
    CURRENT_IP=$(hostname -I | awk '{print $1}')
fi

if [ -z "$CURRENT_IP" ]; then
    echo "❌ Could not detect IP address"
    exit 1
fi

echo "✅ Detected IP: $CURRENT_IP"

# Update config/api.ts
echo "📝 Updating config/api.ts..."
sed -i '' "s/const LOCAL_IP = '[0-9.]*'/const LOCAL_IP = '$CURRENT_IP'/g" config/api.ts

# Update .env.example if it exists
if [ -f ".env.example" ]; then
    echo "📝 Updating .env.example..."
    sed -i '' "s|http://[0-9.]*:5024|http://$CURRENT_IP:5024|g" .env.example
    sed -i '' "s|ws://[0-9.]*:5024|ws://$CURRENT_IP:5024|g" .env.example
fi

# Update .env.local if it exists
if [ -f ".env.local" ]; then
    echo "📝 Updating .env.local..."
    sed -i '' "s|http://[0-9.]*:5024|http://$CURRENT_IP:5024|g" .env.local
    sed -i '' "s|ws://[0-9.]*:5024|ws://$CURRENT_IP:5024|g" .env.local
fi

# Find and update any remaining hardcoded IPs in the codebase
echo "🔍 Checking for any remaining hardcoded IPs..."
OLD_IPS=$(grep -r "10\.0\.0\.[0-9]*" . --include="*.ts" --include="*.tsx" --include="*.js" --exclude-dir=node_modules --exclude-dir=.git | grep -v "// *" | cut -d: -f1 | sort -u)

if [ ! -z "$OLD_IPS" ]; then
    echo "📝 Updating remaining files..."
    for file in $OLD_IPS; do
        echo "  - $file"
        sed -i '' "s/10\.0\.0\.[0-9]*/$CURRENT_IP/g" "$file"
    done
fi

echo ""
echo "✨ Done! IP address updated to $CURRENT_IP"
echo ""
echo "📱 To start the app, run:"
echo "   npm start"
echo ""
echo "🔧 Make sure the backend is running on port 5024"
echo ""