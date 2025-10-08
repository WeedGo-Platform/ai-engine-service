/**
 * JWT Token Utilities
 *
 * Utilities for parsing and validating JWT tokens
 * Follows RFC 7519 (JSON Web Token standard)
 */

export interface JWTPayload {
  exp?: number;  // Expiration time (seconds since Unix epoch)
  iat?: number;  // Issued at (seconds since Unix epoch)
  sub?: string;  // Subject (user ID)
  [key: string]: any;
}

/**
 * Decode JWT token without verification
 * Note: This only decodes the payload, does NOT verify signature
 * Server-side verification is still required for security
 */
export function decodeJWT(token: string): JWTPayload | null {
  try {
    // JWT format: header.payload.signature
    const parts = token.split('.');
    if (parts.length !== 3) {
      console.error('Invalid JWT format: token must have 3 parts');
      return null;
    }

    // Decode base64url payload (second part)
    const payload = parts[1];

    // Base64url decoding: replace URL-safe chars and pad if needed
    const base64 = payload
      .replace(/-/g, '+')
      .replace(/_/g, '/')
      .padEnd(payload.length + (4 - (payload.length % 4)) % 4, '=');

    // Decode base64 and parse JSON
    const decoded = atob(base64);
    const parsed = JSON.parse(decoded);

    return parsed;
  } catch (error) {
    console.error('Failed to decode JWT:', error);
    return null;
  }
}

/**
 * Get token expiration time in milliseconds
 * Returns null if token is invalid or has no expiration
 */
export function getTokenExpiry(token: string): number | null {
  const payload = decodeJWT(token);
  if (!payload || !payload.exp) {
    return null;
  }

  // Convert from seconds to milliseconds
  return payload.exp * 1000;
}

/**
 * Check if token is expired
 * Adds a buffer time (default 60 seconds) to consider tokens "expired" slightly early
 */
export function isTokenExpired(token: string, bufferSeconds: number = 60): boolean {
  const expiry = getTokenExpiry(token);
  if (!expiry) {
    // If we can't determine expiry, consider it expired to be safe
    return true;
  }

  const now = Date.now();
  const bufferMs = bufferSeconds * 1000;

  return now >= (expiry - bufferMs);
}

/**
 * Get remaining time until token expires (in milliseconds)
 * Returns 0 if already expired, null if invalid token
 */
export function getTimeUntilExpiry(token: string): number | null {
  const expiry = getTokenExpiry(token);
  if (!expiry) {
    return null;
  }

  const remaining = expiry - Date.now();
  return Math.max(0, remaining);
}

/**
 * Check if token should be refreshed
 * Returns true if token expires within the threshold
 *
 * @param token - JWT access token
 * @param thresholdMinutes - Minutes before expiry to refresh (default: 5)
 */
export function shouldRefreshToken(token: string, thresholdMinutes: number = 5): boolean {
  const remaining = getTimeUntilExpiry(token);
  if (remaining === null) {
    return true; // Invalid token should be refreshed
  }

  const thresholdMs = thresholdMinutes * 60 * 1000;
  return remaining <= thresholdMs;
}

/**
 * Get token issued at time in milliseconds
 */
export function getTokenIssuedAt(token: string): number | null {
  const payload = decodeJWT(token);
  if (!payload || !payload.iat) {
    return null;
  }

  return payload.iat * 1000;
}

/**
 * Get token age in milliseconds
 */
export function getTokenAge(token: string): number | null {
  const issuedAt = getTokenIssuedAt(token);
  if (!issuedAt) {
    return null;
  }

  return Date.now() - issuedAt;
}

/**
 * Format time duration in human-readable format
 *
 * @param milliseconds - Duration in milliseconds
 * @returns Formatted string like "5m 30s" or "2h 15m"
 */
export function formatDuration(milliseconds: number): string {
  const seconds = Math.floor(milliseconds / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) {
    return `${days}d ${hours % 24}h`;
  } else if (hours > 0) {
    return `${hours}h ${minutes % 60}m`;
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  } else {
    return `${seconds}s`;
  }
}

/**
 * Get user ID from token
 */
export function getUserIdFromToken(token: string): string | null {
  const payload = decodeJWT(token);
  return payload?.sub || payload?.user_id || null;
}

/**
 * Validate token structure (does not verify signature)
 */
export function isValidTokenStructure(token: string): boolean {
  if (!token || typeof token !== 'string') {
    return false;
  }

  const parts = token.split('.');
  if (parts.length !== 3) {
    return false;
  }

  // Try to decode payload
  const payload = decodeJWT(token);
  return payload !== null;
}
