#!/bin/bash

# Fix AIAssistant.tsx
sed -i '' "s|fetch(getApiUrl('api/chat', {|fetch(getApiUrl('/api/chat'), {|g" src/components/kiosk/AIAssistant.tsx

# Fix Checkout.tsx
sed -i '' "s|fetch(getApiUrl('api/kiosk/order/create', {|fetch(getApiUrl('/api/kiosk/order/create'), {|g" src/components/kiosk/Checkout.tsx

# Fix CustomerAuthModal.tsx
sed -i '' "s|fetch(getApiUrl('api/kiosk/auth/customer/login', {|fetch(getApiUrl('/api/kiosk/auth/customer/login'), {|g" src/components/kiosk/CustomerAuthModal.tsx
sed -i '' "s|fetch(getApiUrl('api/kiosk/auth/customer/register', {|fetch(getApiUrl('/api/kiosk/auth/customer/register'), {|g" src/components/kiosk/CustomerAuthModal.tsx

# Fix ProductBrowsing.tsx
sed -i '' 's|`${getApiUrl("api/kiosk/products/browse?${params}"|getApiUrl(`/api/kiosk/products/browse?${params}`)|g' src/components/kiosk/ProductBrowsing.tsx
sed -i '' "s|fetch(getApiUrl('api/kiosk/products/recommendations', {|fetch(getApiUrl('/api/kiosk/products/recommendations'), {|g" src/components/kiosk/ProductBrowsing.tsx

# Fix ProductRecommendations.tsx
sed -i '' "s|fetch(getApiUrl('api/kiosk/products/recommendations', {|fetch(getApiUrl('/api/kiosk/products/recommendations'), {|g" src/components/kiosk/ProductRecommendations.tsx

# Fix QRLoginModal.tsx
sed -i '' "s|fetch(getApiUrl('api/kiosk/auth/qr-generate', {|fetch(getApiUrl('/api/kiosk/auth/qr-generate'), {|g" src/components/kiosk/QRLoginModal.tsx
sed -i '' 's|`${getApiUrl("api/kiosk/auth/check-qr/${code}"|getApiUrl(`/api/kiosk/auth/check-qr/${code}`)|g' src/components/kiosk/QRLoginModal.tsx
sed -i '' "s|fetch(getApiUrl('api/kiosk/auth/manual-code', {|fetch(getApiUrl('/api/kiosk/auth/manual-code'), {|g" src/components/kiosk/QRLoginModal.tsx

# Fix MenuDisplay.tsx
sed -i '' 's|`${getApiUrl("/api/kiosk/products/browse?store_id=${currentStore.id}&limit=500"|getApiUrl(`/api/kiosk/products/browse?store_id=${currentStore.id}&limit=500`)|g' src/components/menuDisplay/MenuDisplay.tsx

echo "Syntax errors fixed!"