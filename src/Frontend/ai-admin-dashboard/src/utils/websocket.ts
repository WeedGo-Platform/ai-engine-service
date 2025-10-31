/**
 * WebSocket URL Utilities
 * Centralized helper functions for building WebSocket URLs from environment variables
 */

/**
 * Get the base WebSocket URL from environment variables
 * Converts HTTP(S) to WS(S) protocol
 *
 * Cloud-First: Requires VITE_API_URL to be set in production environments
 */
export function getWebSocketBaseUrl(): string {
  // Get API URL from environment (required in production)
  const apiUrl = import.meta.env.VITE_API_URL;

  // Only fall back to localhost in development mode
  if (!apiUrl) {
    if (import.meta.env.DEV) {
      console.warn('⚠️ VITE_API_URL not set, using localhost default for development');
      return 'ws://localhost:6024';
    }
    throw new Error(
      'VITE_API_URL environment variable is not set. ' +
      'Please configure it in your .env file for your deployment environment.'
    );
  }

  return apiUrl.replace('http://', 'ws://').replace('https://', 'wss://');
}

/**
 * Build a WebSocket URL for a specific endpoint
 * @param endpoint - The WebSocket endpoint path (e.g., '/api/v1/chat/ws')
 */
export function buildWebSocketUrl(endpoint: string): string {
  const baseUrl = getWebSocketBaseUrl();
  // Ensure endpoint starts with /
  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${baseUrl}${normalizedEndpoint}`;
}

/**
 * Commonly used WebSocket endpoints
 */
export const WS_ENDPOINTS = {
  CHAT: '/api/v1/chat/ws',
  NOTIFICATIONS: '/ws/notifications/admin',
  VOICE_STREAM: '/voice/stream',
  SALES_CHAT: '/api/v1/chat/ws',
} as const;

/**
 * Get a specific WebSocket URL by endpoint name
 */
export function getWebSocketUrl(endpoint: keyof typeof WS_ENDPOINTS): string {
  return buildWebSocketUrl(WS_ENDPOINTS[endpoint]);
}
