/**
 * WebSocket URL Utilities
 * Centralized helper functions for building WebSocket URLs from environment variables
 */

/**
 * Get the base WebSocket URL from environment variables
 * Converts HTTP(S) to WS(S) protocol
 */
export function getWebSocketBaseUrl(): string {
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5024';
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
