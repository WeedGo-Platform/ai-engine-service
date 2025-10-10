/**
 * API Configuration
 * Centralized configuration for all API endpoints
 */

// Get the local machine's IP address
// Update this when your IP changes or when switching between environments
const LOCAL_IP = '10.0.0.29';  // Update this with your current IP

// API Configuration
export const API_CONFIG = {
  // Use environment variable if available, otherwise use local IP
  BASE_URL: process.env.EXPO_PUBLIC_API_URL || `http://${LOCAL_IP}:5024`,
  // Build WebSocket URL from API URL with v1 unified chat path
  WS_URL: (process.env.EXPO_PUBLIC_API_URL || `http://${LOCAL_IP}:5024`).replace('http://', 'ws://').replace('https://', 'wss://') + '/api/v1/chat/ws',

  // Specific endpoints
  VOICE_WS_URL: process.env.EXPO_PUBLIC_VOICE_WS_URL || `ws://${LOCAL_IP}:5024/api/voice/ws/stream`,

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