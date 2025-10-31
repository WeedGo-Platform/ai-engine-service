/**
 * API Configuration
 * Centralized configuration for all API endpoints
 *
 * IMPORTANT: For React Native physical devices, set EXPO_PUBLIC_API_URL in .env
 * Example: EXPO_PUBLIC_API_URL=http://YOUR_LOCAL_IP:5024
 *
 * To find your local IP:
 * - macOS: ifconfig | grep "inet " | grep -v 127.0.0.1
 * - Windows: ipconfig
 * - Linux: ip addr show
 */

// API Configuration
export const API_CONFIG = {
  // Use environment variable (recommended for all environments)
  // Falls back to localhost for emulator/simulator
  BASE_URL: process.env.EXPO_PUBLIC_API_URL || 'http://localhost:5024',
  // Build WebSocket URL from API URL with v1 unified chat path
  WS_URL: (process.env.EXPO_PUBLIC_API_URL || 'http://localhost:5024').replace('http://', 'ws://').replace('https://', 'wss://') + '/api/v1/chat/ws',

  // Specific endpoints
  VOICE_WS_URL: process.env.EXPO_PUBLIC_VOICE_WS_URL || 'ws://localhost:5024/api/voice/ws/stream',

  // Timeout settings
  TIMEOUT: 30000,

  // Retry settings
  MAX_RETRIES: 3,
  RETRY_DELAY: 1000,
};

// Helper function to get the appropriate URL based on platform
export function getApiUrl(): string {
  return API_CONFIG.BASE_URL;
}

export function getWsUrl(): string {
  return API_CONFIG.WS_URL;
}

export function getVoiceWsUrl(): string {
  return API_CONFIG.VOICE_WS_URL;
}

// Export individual URLs for backward compatibility
export const API_URL = API_CONFIG.BASE_URL;
export const WS_URL = API_CONFIG.WS_URL;
export const VOICE_WS_URL = API_CONFIG.VOICE_WS_URL;