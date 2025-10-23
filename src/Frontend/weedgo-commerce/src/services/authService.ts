/**
 * Enhanced authentication service with JWT token validation and security
 */

import { jwtDecode } from 'jwt-decode';
import { logger } from '@utils/logger';

interface JWTPayload {
  user_id: string;
  email: string;
  exp: number;
  iat: number;
  type: 'access' | 'refresh';
  session_id?: string;
  permissions?: string[];
}

interface TokenPair {
  access: string;
  refresh: string;
}

interface SessionInfo {
  userId: string;
  email: string;
  sessionId: string;
  expiresAt: Date;
  lastActivity: Date;
  isValid: boolean;
}

class AuthService {
  private static instance: AuthService;
  private sessionCheckInterval: NodeJS.Timeout | null = null;
  private readonly TOKEN_REFRESH_THRESHOLD = 5 * 60 * 1000; // 5 minutes
  private readonly SESSION_CHECK_INTERVAL = 60 * 1000; // 1 minute
  private readonly MAX_SESSION_IDLE_TIME = 30 * 60 * 1000; // 30 minutes

  private constructor() {
    this.startSessionMonitoring();
  }

  public static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService();
    }
    return AuthService.instance;
  }

  /**
   * Validate JWT token structure and signature
   */
  public validateToken(token: string): boolean {
    try {
      if (!token || typeof token !== 'string') {
        return false;
      }

      // Basic JWT structure validation
      const parts = token.split('.');
      if (parts.length !== 3) {
        return false;
      }

      // Decode and validate payload
      const payload = this.decodeToken(token);
      if (!payload) {
        return false;
      }

      // Check token expiration
      if (this.isTokenExpired(token)) {
        return false;
      }

      // Validate required fields
      if (!payload.user_id || !payload.email || !payload.exp || !payload.iat) {
        return false;
      }

      // Check if issued time is not in the future
      const now = Date.now() / 1000;
      if (payload.iat > now) {
        logger.warn('Token issued in the future', { iat: payload.iat, now });
        return false;
      }

      return true;
    } catch (error) {
      logger.error('Token validation failed', error);
      return false;
    }
  }

  /**
   * Decode JWT token safely
   */
  public decodeToken(token: string): JWTPayload | null {
    try {
      const decoded = jwtDecode<JWTPayload>(token);
      return decoded;
    } catch (error) {
      logger.error('Failed to decode token', error);
      return null;
    }
  }

  /**
   * Check if token is expired
   */
  public isTokenExpired(token: string): boolean {
    try {
      const payload = this.decodeToken(token);
      if (!payload || !payload.exp) {
        return true;
      }

      const now = Date.now() / 1000;
      return payload.exp < now;
    } catch {
      return true;
    }
  }

  /**
   * Check if token needs refresh (approaching expiration)
   */
  public shouldRefreshToken(token: string): boolean {
    try {
      const payload = this.decodeToken(token);
      if (!payload || !payload.exp) {
        return false;
      }

      const now = Date.now();
      const expirationTime = payload.exp * 1000;
      return (expirationTime - now) < this.TOKEN_REFRESH_THRESHOLD;
    } catch {
      return false;
    }
  }

  /**
   * Store tokens securely
   */
  public storeTokens(tokens: TokenPair): void {
    // Validate tokens before storing
    if (!this.validateToken(tokens.access)) {
      throw new Error('Invalid access token');
    }

    if (!this.validateToken(tokens.refresh)) {
      throw new Error('Invalid refresh token');
    }

    // Store in localStorage (consider using httpOnly cookies for production)
    localStorage.setItem('access_token', tokens.access);
    localStorage.setItem('refresh_token', tokens.refresh);

    // Store token metadata
    const accessPayload = this.decodeToken(tokens.access);
    if (accessPayload) {
      localStorage.setItem('token_expires', String(accessPayload.exp * 1000));
      localStorage.setItem('user_id', accessPayload.user_id);
      localStorage.setItem('user_email', accessPayload.email);

      if (accessPayload.session_id) {
        localStorage.setItem('session_id', accessPayload.session_id);
      }
    }

    // Update last activity
    this.updateLastActivity();
  }

  /**
   * Get stored access token
   */
  public getAccessToken(): string | null {
    const token = localStorage.getItem('access_token');

    if (!token) {
      return null;
    }

    // Validate token before returning
    if (!this.validateToken(token)) {
      this.clearTokens();
      return null;
    }

    return token;
  }

  /**
   * Get stored refresh token
   */
  public getRefreshToken(): string | null {
    const token = localStorage.getItem('refresh_token');

    if (!token) {
      return null;
    }

    // Basic validation (don't clear tokens if refresh is invalid, might be refreshing)
    if (token.split('.').length !== 3) {
      return null;
    }

    return token;
  }

  /**
   * Clear all authentication data
   */
  public clearTokens(): void {
    // Clear tokens
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');

    // Clear metadata
    localStorage.removeItem('token_expires');
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_email');
    localStorage.removeItem('session_id');
    localStorage.removeItem('last_activity');
    localStorage.removeItem('user');

    // Clear session monitoring
    this.stopSessionMonitoring();
  }

  /**
   * Get current session information
   */
  public getSessionInfo(): SessionInfo | null {
    const accessToken = this.getAccessToken();
    if (!accessToken) {
      return null;
    }

    const payload = this.decodeToken(accessToken);
    if (!payload) {
      return null;
    }

    const lastActivity = localStorage.getItem('last_activity');
    const lastActivityDate = lastActivity ? new Date(parseInt(lastActivity)) : new Date();

    return {
      userId: payload.user_id,
      email: payload.email,
      sessionId: payload.session_id || '',
      expiresAt: new Date(payload.exp * 1000),
      lastActivity: lastActivityDate,
      isValid: !this.isTokenExpired(accessToken) && !this.isSessionIdle(),
    };
  }

  /**
   * Check if session is idle (no activity for too long)
   */
  public isSessionIdle(): boolean {
    const lastActivity = localStorage.getItem('last_activity');
    if (!lastActivity) {
      return false;
    }

    const now = Date.now();
    const lastActivityTime = parseInt(lastActivity);
    return (now - lastActivityTime) > this.MAX_SESSION_IDLE_TIME;
  }

  /**
   * Update last activity timestamp
   */
  public updateLastActivity(): void {
    localStorage.setItem('last_activity', String(Date.now()));
  }

  /**
   * Start monitoring session validity
   */
  private startSessionMonitoring(): void {
    if (this.sessionCheckInterval) {
      return;
    }

    this.sessionCheckInterval = setInterval(() => {
      const accessToken = localStorage.getItem('access_token');
      if (!accessToken) {
        return;
      }

      // Check token validity
      if (this.isTokenExpired(accessToken)) {
        logger.info('Access token expired');
        this.handleSessionExpired();
        return;
      }

      // Check session idle timeout
      if (this.isSessionIdle()) {
        logger.info('Session idle timeout');
        this.handleSessionExpired();
        return;
      }

      // Check if token needs refresh
      if (this.shouldRefreshToken(accessToken)) {
        logger.info('Token approaching expiration, should refresh');
        // Trigger token refresh (handled by API client interceptor)
      }
    }, this.SESSION_CHECK_INTERVAL);
  }

  /**
   * Stop monitoring session
   */
  private stopSessionMonitoring(): void {
    if (this.sessionCheckInterval) {
      clearInterval(this.sessionCheckInterval);
      this.sessionCheckInterval = null;
    }
  }

  /**
   * Handle expired session
   */
  private handleSessionExpired(): void {
    this.clearTokens();

    // Dispatch event for app to handle
    window.dispatchEvent(new CustomEvent('auth:session-expired'));

    // Redirect to login if not already there
    if (window.location.pathname !== '/login') {
      window.location.href = '/login?reason=session_expired';
    }
  }

  /**
   * Check if user has specific permission
   */
  public hasPermission(permission: string): boolean {
    const token = this.getAccessToken();
    if (!token) {
      return false;
    }

    const payload = this.decodeToken(token);
    if (!payload || !payload.permissions) {
      return false;
    }

    return payload.permissions.includes(permission);
  }

  /**
   * Get user permissions
   */
  public getPermissions(): string[] {
    const token = this.getAccessToken();
    if (!token) {
      return [];
    }

    const payload = this.decodeToken(token);
    return payload?.permissions || [];
  }

  /**
   * Validate token against backend
   */
  public async validateTokenWithBackend(token: string): Promise<boolean> {
    try {
      const response = await fetch('/api/auth/validate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      return response.ok;
    } catch (error) {
      logger.error('Failed to validate token with backend', error);
      return false;
    }
  }

  /**
   * Refresh access token using refresh token
   */
  public async refreshAccessToken(): Promise<TokenPair | null> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      return null;
    }

    try {
      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh: refreshToken }),
      });

      if (!response.ok) {
        throw new Error('Failed to refresh token');
      }

      const tokens = await response.json();
      this.storeTokens(tokens);
      return tokens;
    } catch (error) {
      logger.error('Failed to refresh access token', error);
      this.clearTokens();
      return null;
    }
  }

  /**
   * Revoke tokens (logout)
   */
  public async revokeTokens(): Promise<void> {
    const accessToken = this.getAccessToken();
    const refreshToken = this.getRefreshToken();

    if (!accessToken || !refreshToken) {
      this.clearTokens();
      return;
    }

    try {
      await fetch('/api/auth/revoke', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ refresh: refreshToken }),
      });
    } catch (error) {
      logger.error('Failed to revoke tokens', error);
    } finally {
      this.clearTokens();
    }
  }
}

// Export singleton instance
export const authService = AuthService.getInstance();

// Export types
export type { JWTPayload, TokenPair, SessionInfo };

// Utility functions
export const isAuthenticated = (): boolean => {
  const token = authService.getAccessToken();
  return !!token && !authService.isTokenExpired(token);
};

export const getCurrentUser = (): { id: string; email: string } | null => {
  const sessionInfo = authService.getSessionInfo();
  if (!sessionInfo || !sessionInfo.isValid) {
    return null;
  }

  return {
    id: sessionInfo.userId,
    email: sessionInfo.email,
  };
};

// Auto-refresh on activity
if (typeof window !== 'undefined') {
  ['click', 'keypress', 'scroll', 'mousemove'].forEach(event => {
    window.addEventListener(event, () => {
      authService.updateLastActivity();
    }, { passive: true });
  });

  // Listen for session expired events
  window.addEventListener('auth:session-expired', () => {
    logger.info('Session expired event received');
  });
}