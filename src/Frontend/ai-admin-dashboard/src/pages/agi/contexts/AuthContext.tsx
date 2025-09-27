/**
 * Authentication Context and Provider
 * Manages user authentication state and provides authentication methods
 * Following SOLID principles with clear separation of concerns
 */

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { agiApi } from '../services/agiApi';
import { wsService } from '../services/websocket';
import { IUser, ILoginRequest, ILoginResponse } from '../types';

/**
 * Authentication state interface
 */
export interface IAuthState {
  user: IUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

/**
 * Authentication context value interface
 */
export interface IAuthContextValue extends IAuthState {
  login: (credentials: ILoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  clearError: () => void;
}

/**
 * Initial authentication state
 */
const initialAuthState: IAuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null
};

/**
 * Authentication Context
 */
const AuthContext = createContext<IAuthContextValue | undefined>(undefined);

/**
 * Authentication Provider Component
 */
export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [authState, setAuthState] = useState<IAuthState>(initialAuthState);

  /**
   * Initialize authentication on mount
   */
  useEffect(() => {
    initializeAuth();
  }, []);

  /**
   * Update WebSocket authentication when user changes
   */
  useEffect(() => {
    if (authState.isAuthenticated) {
      const token = localStorage.getItem('agi_auth_token');
      if (token) {
        wsService.updateAuthToken(token);
        wsService.connect().catch(console.error);
      }
    } else {
      wsService.disconnect();
    }
  }, [authState.isAuthenticated]);

  /**
   * Initialize authentication from stored token
   */
  const initializeAuth = async () => {
    setAuthState(prev => ({ ...prev, isLoading: true }));

    try {
      const token = localStorage.getItem('agi_auth_token');

      if (!token) {
        setAuthState(prev => ({
          ...prev,
          isLoading: false,
          isAuthenticated: false
        }));
        return;
      }

      // Set token in API service
      agiApi.setAuthToken(token);

      // Fetch current user
      const user = await agiApi.getCurrentUser();

      setAuthState({
        user,
        isAuthenticated: true,
        isLoading: false,
        error: null
      });
    } catch (error: any) {
      console.error('Auth initialization failed:', error);

      // Token might be expired, try to refresh
      if (error.status === 401) {
        try {
          await refreshToken();
        } catch (refreshError) {
          // Refresh failed, clear auth
          clearAuth();
        }
      } else {
        setAuthState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: error.message || 'Authentication failed'
        });
      }
    }
  };

  /**
   * Login user
   */
  const login = useCallback(async (credentials: ILoginRequest) => {
    setAuthState(prev => ({
      ...prev,
      isLoading: true,
      error: null
    }));

    try {
      const response = await agiApi.login(credentials);

      // Fetch user data
      const user = await agiApi.getCurrentUser();

      setAuthState({
        user,
        isAuthenticated: true,
        isLoading: false,
        error: null
      });
    } catch (error: any) {
      console.error('Login failed:', error);
      setAuthState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: error.message || 'Login failed'
      });
      throw error;
    }
  }, []);

  /**
   * Logout user
   */
  const logout = useCallback(async () => {
    setAuthState(prev => ({
      ...prev,
      isLoading: true
    }));

    try {
      await agiApi.logout();
    } catch (error) {
      console.error('Logout error:', error);
      // Continue with local logout even if API call fails
    } finally {
      clearAuth();
    }
  }, []);

  /**
   * Refresh authentication token
   */
  const refreshToken = useCallback(async () => {
    try {
      const response = await agiApi.refreshToken();

      // Fetch updated user data
      const user = await agiApi.getCurrentUser();

      setAuthState({
        user,
        isAuthenticated: true,
        isLoading: false,
        error: null
      });
    } catch (error: any) {
      console.error('Token refresh failed:', error);
      clearAuth();
      throw error;
    }
  }, []);

  /**
   * Clear authentication state
   */
  const clearAuth = () => {
    agiApi.clearAuthToken();
    wsService.disconnect();

    setAuthState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null
    });
  };

  /**
   * Clear error message
   */
  const clearError = useCallback(() => {
    setAuthState(prev => ({ ...prev, error: null }));
  }, []);

  /**
   * Setup automatic token refresh
   */
  useEffect(() => {
    if (!authState.isAuthenticated) return;

    // Refresh token every 45 minutes (assuming 1 hour expiry)
    const refreshInterval = setInterval(() => {
      refreshToken().catch(error => {
        console.error('Auto refresh failed:', error);
      });
    }, 45 * 60 * 1000);

    return () => clearInterval(refreshInterval);
  }, [authState.isAuthenticated, refreshToken]);

  /**
   * Handle auth-related WebSocket events
   */
  useEffect(() => {
    const handleUnauthorized = () => {
      clearAuth();
      setAuthState(prev => ({
        ...prev,
        error: 'Session expired. Please login again.'
      }));
    };

    const unsubscribe = wsService.subscribe('unauthorized', handleUnauthorized);
    return unsubscribe;
  }, []);

  const contextValue: IAuthContextValue = {
    ...authState,
    login,
    logout,
    refreshToken,
    clearError
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

/**
 * Custom hook to use authentication context
 */
export const useAuth = (): IAuthContextValue => {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
};

/**
 * HOC for protected routes
 */
export const withAuth = <P extends object>(
  Component: React.ComponentType<P>,
  requiredRoles?: string[]
): React.FC<P> => {
  return (props: P) => {
    const { user, isAuthenticated, isLoading } = useAuth();

    if (isLoading) {
      return (
        <div className="flex items-center justify-center h-screen">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      );
    }

    if (!isAuthenticated) {
      return (
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">
              Authentication Required
            </h2>
            <p className="text-gray-600">Please login to access this page.</p>
          </div>
        </div>
      );
    }

    if (requiredRoles && user) {
      const hasRequiredRole = requiredRoles.some(role =>
        user.roles.includes(role)
      );

      if (!hasRequiredRole) {
        return (
          <div className="flex items-center justify-center h-screen">
            <div className="text-center">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">
                Access Denied
              </h2>
              <p className="text-gray-600">
                You don't have permission to access this page.
              </p>
            </div>
          </div>
        );
      }
    }

    return <Component {...props} />;
  };
};

export default AuthContext;