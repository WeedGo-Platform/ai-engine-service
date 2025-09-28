# IP Configuration Guide for WeedGo Mobile App

## Current Configuration
- **Current IP**: `10.0.0.29`
- **Backend Port**: `5024`
- **API URL**: `http://10.0.0.29:5024`
- **WebSocket URL**: `ws://10.0.0.29:5024`

## Quick Update

### Automatic Update (Recommended)
Run this command to automatically detect and update your IP:
```bash
./auto-update-ip.sh
```

This script will:
1. Detect your current IP address
2. Update all configuration files
3. Update any hardcoded IPs in the codebase

### Manual Update
If you need to manually set a specific IP:

1. **Update the central config** (`config/api.ts`):
   ```typescript
   const LOCAL_IP = 'YOUR_IP_HERE';
   ```

2. **Update environment files** (if using):
   - `.env.local`
   - `.env.development`

## Configuration Files

### 1. Central Configuration
**File**: `config/api.ts`
- Main configuration file for all API endpoints
- All components should import from this file
- Contains `LOCAL_IP` constant that needs updating

### 2. Environment Variables
**File**: `.env.local` (create from `.env.example`)
```
EXPO_PUBLIC_API_URL=http://YOUR_IP:5024
EXPO_PUBLIC_WS_URL=ws://YOUR_IP:5024
EXPO_PUBLIC_VOICE_WS_URL=ws://YOUR_IP:5024/api/voice/ws/stream
```

### 3. Components Using the Config
The following components are configured to use the centralized config:
- `hooks/useVoiceChatSimple.ts`
- `hooks/useVoiceChatWithVAD.ts`
- `hooks/useVoiceWithVAD.ts`
- `services/api/client.ts`
- All other services and hooks

## Troubleshooting

### Finding Your IP Address

**macOS**:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**Linux**:
```bash
hostname -I
```

**Windows**:
```cmd
ipconfig
```

### Common Issues

1. **Connection Refused**
   - Ensure backend is running: `python3 api_server.py`
   - Check firewall settings
   - Verify port 5024 is not blocked

2. **Network Unreachable**
   - Ensure phone and computer are on same network
   - Check IP hasn't changed
   - Disable VPN if active

3. **WebSocket Connection Failed**
   - Backend must be running on port 5024
   - Check CORS settings in backend
   - Verify WebSocket endpoints are correct

## Development Workflow

1. **Start Backend**:
   ```bash
   cd microservices/ai-engine-service/src/Backend
   python3 api_server.py
   ```

2. **Update IP** (if changed):
   ```bash
   cd src/Frontend/mobile/weedgo-mobile
   ./auto-update-ip.sh
   ```

3. **Start Expo**:
   ```bash
   npm start
   # or
   npx expo start
   ```

4. **Connect Device**:
   - Scan QR code with Expo Go app
   - Or use simulator/emulator

## Production Configuration

For production, use environment variables:
```bash
EXPO_PUBLIC_API_URL=https://api.weedgo.com
EXPO_PUBLIC_WS_URL=wss://api.weedgo.com
```

These will override the local development settings.