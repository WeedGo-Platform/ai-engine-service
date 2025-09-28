#!/bin/bash

# Script to update all hardcoded IP addresses to use centralized config
# Run this script whenever you need to update IP addresses

echo "Updating IP addresses in mobile app..."

# Update services/chat/websocket.ts
sed -i '' "s|process.env.EXPO_PUBLIC_API_URL || 'http://10.0.0.169:5024'|process.env.EXPO_PUBLIC_API_URL || 'http://10.0.0.29:5024'|g" services/chat/websocket.ts

# Update services/reviews.ts
sed -i '' "s|process.env.EXPO_PUBLIC_API_URL || 'http://10.0.0.169:5024'|process.env.EXPO_PUBLIC_API_URL || 'http://10.0.0.29:5024'|g" services/reviews.ts

# Update services/orderTracking.ts
sed -i '' "s|process.env.EXPO_PUBLIC_WS_URL || 'ws://10.0.0.169:5024'|process.env.EXPO_PUBLIC_WS_URL || 'ws://10.0.0.29:5024'|g" services/orderTracking.ts
sed -i '' "s|process.env.EXPO_PUBLIC_API_URL || 'http://10.0.0.169:5024'|process.env.EXPO_PUBLIC_API_URL || 'http://10.0.0.29:5024'|g" services/orderTracking.ts

# Update services/voice.ts
sed -i '' "s|process.env.EXPO_PUBLIC_API_URL || 'http://10.0.0.169:5024'|process.env.EXPO_PUBLIC_API_URL || 'http://10.0.0.29:5024'|g" services/voice.ts

# Update stores/wishlistStore.ts
sed -i '' "s|process.env.EXPO_PUBLIC_API_URL || 'http://10.0.0.169:5024'|process.env.EXPO_PUBLIC_API_URL || 'http://10.0.0.29:5024'|g" stores/wishlistStore.ts

# Update app/(auth)/login.tsx
sed -i '' "s|process.env.EXPO_PUBLIC_API_URL || 'http://10.0.0.169:5024'|process.env.EXPO_PUBLIC_API_URL || 'http://10.0.0.29:5024'|g" app/\(auth\)/login.tsx

# Update remaining hooks
sed -i '' "s|'ws://10.0.0.169:5024/api/voice/ws/stream'|getVoiceWsUrl()|g" hooks/useVoiceChat.ts
sed -i '' "s|'ws://10.0.0.169:5024/api/voice/ws/stream'|getVoiceWsUrl()|g" hooks/useVoiceWithVAD.ts
sed -i '' "s|'ws://10.0.0.169:5024/api/voice/ws/stream'|getVoiceWsUrl()|g" hooks/useVoiceChatChunked.ts
sed -i '' "s|'ws://10.0.0.169:5024/api/voice/ws/stream'|getVoiceWsUrl()|g" hooks/useRealtimeVoice.ts
sed -i '' "s|'ws://10.0.0.169:5024/api/voice/ws/stream'|getVoiceWsUrl()|g" hooks/useStreamingTranscription.ts
sed -i '' "s|'http://10.0.0.169:5024/api/voice/rtc'|getApiUrl() + '/api/voice/rtc'|g" hooks/useWebRTCTranscription.ts

echo "IP addresses updated to 10.0.0.29"
echo "Remember to update config/api.ts if your IP changes"