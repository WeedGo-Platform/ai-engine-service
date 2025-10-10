# Environment Configuration Guide

## Overview
This guide explains how to configure the mobile app for different testing and deployment scenarios.

## Environment Files

### Main Configuration Files
- `.env` - Default development configuration (current: physical device setup)
- `.env.local` - Local overrides (not committed to git)
- `.env.example` - Template for new developers

### Scenario-Specific Configurations
- `.env.simulator` - iOS Simulator configuration
- `.env.emulator` - Android Emulator configuration
- `.env.production` - Production deployment

## IP Address Configuration

### Finding Your Machine's IP Address
```bash
# macOS/Linux
ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}'

# Alternative for macOS
ipconfig getifaddr en0  # WiFi
ipconfig getifaddr en1  # Ethernet
```

### Configuration by Testing Environment

| Environment | API URL | Notes |
|------------|---------|-------|
| **iOS Simulator** | `http://localhost:5024` | Simulator can access localhost directly |
| **Android Emulator** | `http://10.0.2.2:5024` | Special alias for host machine |
| **Physical Device (Same Network)** | `http://10.0.0.29:5024` | Use your machine's actual IP |
| **Production** | `https://api.weedgo.ca` | Production server URL |

## Usage Instructions

### 1. iOS Simulator Testing
```bash
# Copy simulator configuration
cp .env.simulator .env

# Or use directly with Expo
EXPO_PUBLIC_API_URL=http://localhost:5024 expo start --ios
```

### 2. Android Emulator Testing
```bash
# Copy emulator configuration
cp .env.emulator .env

# Or use directly with Expo
EXPO_PUBLIC_API_URL=http://10.0.2.2:5024 expo start --android
```

### 3. Physical Device Testing
```bash
# Ensure .env has your machine's IP
# Current configuration: 10.0.0.29

# Start Expo with QR code
expo start

# Scan QR code with Expo Go app on your device
```

### 4. Production Build
```bash
# Use production configuration
cp .env.production .env

# Build for production
eas build --platform ios --profile production
eas build --platform android --profile production
```

## Backend Server Setup

Ensure the backend is running and accessible:

```bash
# Start backend server
cd src/Backend
python3 main_server.py

# Verify it's running
curl http://localhost:5024/health
```

### Allow Network Access (macOS)
If testing on physical devices, ensure your firewall allows incoming connections:
1. System Preferences → Security & Privacy → Firewall
2. Click "Firewall Options"
3. Allow incoming connections for Python

## WebSocket Configuration

WebSocket URLs follow the same pattern as HTTP URLs:
- Replace `http://` with `ws://`
- Replace `https://` with `wss://`

Example:
```
API: http://10.0.0.29:5024
WebSocket: ws://10.0.0.29:5024
Voice WebSocket: ws://10.0.0.29:5024/api/v2/ai-conversation/ws
```

## Troubleshooting

### Connection Refused
- **iOS Simulator**: Ensure backend is running on port 5024
- **Android Emulator**: Use 10.0.2.2, not localhost
- **Physical Device**: Ensure device is on same network as your machine

### Network Request Failed
- Check firewall settings
- Verify IP address is correct
- Ensure backend CORS allows your app's origin

### Invalid API Response
- Check backend logs for errors
- Verify v2 endpoints are properly registered
- Ensure tenant_id is included in requests

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `EXPO_PUBLIC_API_URL` | Backend API base URL | `http://10.0.0.29:5024` |
| `EXPO_PUBLIC_WS_URL` | WebSocket base URL | `ws://10.0.0.29:5024` |
| `EXPO_PUBLIC_VOICE_WS_URL` | Voice WebSocket URL | `ws://10.0.0.29:5024/api/v2/ai-conversation/ws` |
| `EXPO_PUBLIC_TENANT_ID` | Default tenant identifier | `ce2d57bc-b3ba-4801-b229-889a9fe9626d` |
| `EXPO_PUBLIC_API_TIMEOUT` | Request timeout (ms) | `30000` |
| `EXPO_PUBLIC_ENV` | Environment name | `development`, `production` |
| `EXPO_PUBLIC_ENABLE_VOICE` | Enable voice features | `true`, `false` |
| `EXPO_PUBLIC_ENABLE_CHAT` | Enable chat features | `true`, `false` |
| `EXPO_PUBLIC_ENABLE_BIOMETRIC` | Enable biometric auth | `true`, `false` |

## Security Notes

⚠️ **Important**:
- Never commit `.env.local` with sensitive data
- Keep production API keys and secrets secure
- Use environment-specific API keys
- Enable HTTPS/WSS for production

## Quick Commands

```bash
# Check current configuration
grep API_URL .env

# Test API connectivity
curl $(grep API_URL .env | cut -d'=' -f2)/health

# Switch to simulator testing
cp .env.simulator .env && expo start --ios

# Switch to emulator testing
cp .env.emulator .env && expo start --android

# Reset to default (physical device)
git checkout .env
```

---

**Last Updated**: 2025-10-10
**Backend Port**: 5024
**Current Machine IP**: 10.0.0.29