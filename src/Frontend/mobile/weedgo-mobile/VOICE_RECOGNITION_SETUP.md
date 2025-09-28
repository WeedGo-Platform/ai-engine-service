# Voice Recognition Setup for WeedGo Mobile

## Problem
Native voice recognition on mobile devices requires platform-specific APIs:
- **iOS**: Speech Recognition Framework
- **Android**: SpeechRecognizer API
- **Web Browser**: Web Speech API

These are NOT available in Expo Go, which only includes pre-bundled modules.

## Solution: Development Build with Native Voice

### 1. Prerequisites
```bash
# For iOS development
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer

# For Android development
# Ensure Android Studio is installed
```

### 2. Build Development Client

```bash
# Install dependencies
npm install expo-dev-client @react-native-voice/voice

# Generate native projects
npx expo prebuild --clean

# Run on iOS (requires Xcode)
npx expo run:ios

# Run on Android (requires Android Studio)
npx expo run:android
```

### 3. How It Works

The native voice implementation (`useVoiceTranscription.ts`) provides:
- **On-device transcription** - No audio sent to backend
- **Real-time updates** - Live transcript as you speak
- **Smart chunking** - Auto-sends after natural pauses
- **Auto-stop** - Stops after 2 seconds of silence

## Alternative: Expo Go Compatible Solution

If you need to test in Expo Go immediately, use the fallback implementation that records audio and sends to backend for transcription:

```typescript
// hooks/useVoiceTranscriptionFallback.ts
import { Audio } from 'expo-av';
// Records audio -> Sends to /api/voice/transcribe -> Returns text
```

## Comparison

| Feature | Native Voice (Dev Build) | Fallback (Expo Go) |
|---------|-------------------------|-------------------|
| Transcription Location | On-device | Backend server |
| Real-time Updates | Yes | No |
| Network Required | No | Yes |
| Privacy | High (local) | Lower (server) |
| Expo Go Support | No | Yes |

## Recommended Approach

1. **For Development**: Use fallback with Expo Go for rapid iteration
2. **For Production**: Use native voice with development build for best UX

## Testing Voice Recognition

1. Grant microphone permissions when prompted
2. Tap the microphone button in chat
3. Speak naturally
4. Transcript auto-sends after pause or stop

## Troubleshooting

### "Native module doesn't exist" Error
- You're running in Expo Go
- Solution: Use development build or fallback

### iOS Build Fails
```bash
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
```

### Android Build Fails
- Open Android Studio
- Install required SDKs
- Accept licenses: `sdkmanager --licenses`