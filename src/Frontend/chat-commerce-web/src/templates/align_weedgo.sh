#!/bin/bash

# Script to align WeedGo template with Modern Minimal template structure
# while preserving WeedGo's color scheme

MODERN_DIR="/Users/charrcy/projects/WeedGo/microservices/ai-engine-service/src/Frontend/chat-commerce-web/src/templates/modern-minimal"
WEEDGO_DIR="/Users/charrcy/projects/WeedGo/microservices/ai-engine-service/src/Frontend/chat-commerce-web/src/templates/weedgo"

echo "Aligning WeedGo template with Modern Minimal template..."

# Copy all components from modern-minimal to weedgo
# We'll then update the colors in a second pass

# Chat components
echo "Copying chat components..."
cp "$MODERN_DIR/components/chat/ChatHeader.tsx" "$WEEDGO_DIR/components/chat/"
cp "$MODERN_DIR/components/chat/ChatMessages.tsx" "$WEEDGO_DIR/components/chat/"
cp "$MODERN_DIR/components/chat/ChatInputArea.tsx" "$WEEDGO_DIR/components/chat/"
cp "$MODERN_DIR/components/chat/AIChatBubble.tsx" "$WEEDGO_DIR/components/chat/"
cp "$MODERN_DIR/components/chat/UserChatBubble.tsx" "$WEEDGO_DIR/components/chat/"
cp "$MODERN_DIR/components/chat/ChatButton.tsx" "$WEEDGO_DIR/components/chat/"
cp "$MODERN_DIR/components/chat/MicrophoneButton.tsx" "$WEEDGO_DIR/components/chat/"
cp "$MODERN_DIR/components/chat/SpeakerButton.tsx" "$WEEDGO_DIR/components/chat/"
cp "$MODERN_DIR/components/chat/TextInputWindow.tsx" "$WEEDGO_DIR/components/chat/"
cp "$MODERN_DIR/components/chat/TranscriptWindow.tsx" "$WEEDGO_DIR/components/chat/"
cp "$MODERN_DIR/components/chat/ChatMetadata.tsx" "$WEEDGO_DIR/components/chat/"

# Layout components
echo "Copying layout components..."
cp "$MODERN_DIR/components/layout/TopMenuBar.tsx" "$WEEDGO_DIR/components/layout/"
cp "$MODERN_DIR/components/layout/HamburgerMenu.tsx" "$WEEDGO_DIR/components/layout/"
cp "$MODERN_DIR/components/layout/TemplateSwitcher.tsx" "$WEEDGO_DIR/components/layout/"
cp "$MODERN_DIR/layouts/Layout.tsx" "$WEEDGO_DIR/layouts/"

# Auth components
echo "Copying auth components..."
cp "$MODERN_DIR/components/auth/Login.tsx" "$WEEDGO_DIR/components/auth/"
cp "$MODERN_DIR/components/auth/Register.tsx" "$WEEDGO_DIR/components/auth/"

# Common components
echo "Copying common components..."
cp "$MODERN_DIR/components/common/ConfigToggleButton.tsx" "$WEEDGO_DIR/components/common/"
cp "$MODERN_DIR/components/common/ErrorBoundary.tsx" "$WEEDGO_DIR/components/common/"
cp "$MODERN_DIR/components/common/LoadingSpinner.tsx" "$WEEDGO_DIR/components/common/"
cp "$MODERN_DIR/components/common/Notification.tsx" "$WEEDGO_DIR/components/common/"

# Legal components
echo "Copying legal components..."
cp "$MODERN_DIR/components/legal/AgeGate.tsx" "$WEEDGO_DIR/components/legal/"
cp "$MODERN_DIR/components/legal/CookieDisclaimer.tsx" "$WEEDGO_DIR/components/legal/"

# Product components
echo "Copying product components..."
cp "$MODERN_DIR/components/product/ProductDetails.tsx" "$WEEDGO_DIR/components/product/"
cp "$MODERN_DIR/components/product/ProductRecommendations.tsx" "$WEEDGO_DIR/components/product/"
cp "$MODERN_DIR/components/product/QuantitySelector.tsx" "$WEEDGO_DIR/components/product/"

# Copy provider and types
echo "Copying provider and types..."
cp "$MODERN_DIR/provider.tsx" "$WEEDGO_DIR/"
cp "$MODERN_DIR/types.ts" "$WEEDGO_DIR/"

# Copy styles
echo "Copying styles..."
cp "$MODERN_DIR/styles/StyleProvider.ts" "$WEEDGO_DIR/styles/"
cp "$MODERN_DIR/styles/scrollbar.css" "$WEEDGO_DIR/styles/"

echo "Initial copy complete. Now updating colors..."

# Update color references in all copied files
# Replace slate colors with gray colors
find "$WEEDGO_DIR" -name "*.tsx" -type f -exec sed -i '' \
  -e 's/slate-900/blue-700/g' \
  -e 's/slate-800/blue-600/g' \
  -e 's/slate-700/gray-700/g' \
  -e 's/slate-600/gray-600/g' \
  -e 's/slate-500/gray-500/g' \
  -e 's/slate-400/gray-400/g' \
  -e 's/slate-300/gray-300/g' \
  -e 's/slate-200/gray-200/g' \
  -e 's/slate-100/gray-100/g' \
  -e 's/slate-50/gray-50/g' \
  -e 's/amber-500/blue-500/g' \
  -e 's/amber-600/blue-600/g' \
  {} \;

# Remove transition classes (no animations)
find "$WEEDGO_DIR" -name "*.tsx" -type f -exec sed -i '' \
  -e 's/transition-[a-z]*//g' \
  -e 's/duration-[0-9]*//g' \
  -e 's/ease-[a-z-]*//g' \
  {} \;

echo "Color updates complete!"
echo "WeedGo template has been aligned with Modern Minimal structure."