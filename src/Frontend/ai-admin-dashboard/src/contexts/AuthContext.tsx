import React, { createContext, useContext, useState, useEffect, ReactNode, useRef } from 'react';
import authService from '../services/authService';
import { authConfig, getAuthStorage, getStorageKey } from '../config/auth.config';

interface User {
  user_id: string;
  email: string;
  role: string;
  first_name?: string;
  last_name?: string;
  tenants: Array<{
    id: string;
    name: string;
    code: string;
    role: string;
  }>;
  stores: Array<{
    id: string;
    name: string;
    code: string;
    role: string;
    tenant_id: string;
  }>;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  permissions: string[];
  login: (email: string, password: string, rememberMe?: boolean) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  hasPermission: (permission: string) => boolean;
  hasAnyPermission: (permissions: string[]) => boolean;
  isSuperAdmin: () => boolean;
  isTenantAdmin: (tenantId?: string) => boolean;
  isStoreManager: (storeId?: string) => boolean;
  isTenantAdminOnly: () => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [permissions, setPermissions] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const refreshTimerRef = useRef<NodeJS.Timeout | null>(null);
  const storage = getAuthStorage();

  // Check for existing session on mount
  useEffect(() => {
    checkAuthStatus();
    
    // Set up session check on window focus if enabled
    if (authConfig.session.checkOnFocus) {
      const handleFocus = () => checkAuthStatus();
      window.addEventListener('focus', handleFocus);
      return () => window.removeEventListener('focus', handleFocus);
    }
  }, []);
  
  // Set up periodic session check if enabled
  useEffect(() => {
    if (authConfig.session.checkInterval > 0 && isAuthenticated) {
      const interval = setInterval(() => {
        checkAuthStatus();
      }, authConfig.session.checkInterval * 1000);
      
      return () => clearInterval(interval);
    }
  }, [isAuthenticated]);

  const checkAuthStatus = async () => {
    try {
      const token = storage.getItem(getStorageKey('access_token'));
      
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        // Try to get current user directly first (faster than verify)
        const userData = await authService.getCurrentUser();
        setUser(userData.user);
        setPermissions(userData.permissions);
        setIsAuthenticated(true);
      } catch (error: any) {
        // If 401, token might be expired, try to refresh
        if (error?.response?.status === 401) {
          const refreshTokenValue = storage.getItem(getStorageKey('refresh_token'));
          if (refreshTokenValue) {
            try {
              await refreshToken();
            } catch (refreshError) {
              // Only clear auth tokens
              storage.removeItem(getStorageKey('access_token'));
              storage.removeItem(getStorageKey('refresh_token'));
              storage.removeItem(getStorageKey('token_expiry'));
              setIsAuthenticated(false);
            }
          } else {
            // No refresh token available
            storage.removeItem(getStorageKey('access_token'));
            storage.removeItem(getStorageKey('token_expiry'));
            setIsAuthenticated(false);
          }
        } else {
          // Network error or other issue - don't log out yet
          console.error('Auth check failed with non-401 error:', error);
          // Try to use cached user data if available
          const cachedToken = storage.getItem(getStorageKey('access_token'));
          if (cachedToken) {
            // Keep user logged in but log the error
            setIsAuthenticated(true);
          }
        }
      }
    } catch (error) {
      console.error('Auth check failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string, rememberMe: boolean = false) => {
    try {
      const response = await authService.login(email, password, rememberMe);
      
      // Store tokens
      storage.setItem(getStorageKey('access_token'), response.access_token);
      storage.setItem(getStorageKey('refresh_token'), response.refresh_token);
      
      // Store token expiry for auto-refresh
      const expiryTime = Date.now() + (response.expires_in * 1000);
      storage.setItem(getStorageKey('token_expiry'), expiryTime.toString());
      
      // Set user data
      setUser(response.user);
      setPermissions(response.permissions);
      setIsAuthenticated(true);
      
      // Set up token refresh timer if enabled
      if (authConfig.tokenRefresh.enabled) {
        setupTokenRefresh(response.expires_in);
      }
      
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local state regardless
      storage.removeItem(getStorageKey('access_token'));
      storage.removeItem(getStorageKey('refresh_token'));
      storage.removeItem(getStorageKey('token_expiry'));
      
      // Clear refresh timer
      if (refreshTimerRef.current) {
        clearTimeout(refreshTimerRef.current);
        refreshTimerRef.current = null;
      }
      setUser(null);
      setPermissions([]);
      setIsAuthenticated(false);
    }
  };

  const refreshToken = async () => {
    try {
      const refreshToken = storage.getItem(getStorageKey('refresh_token'));
      
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }
      
      const response = await authService.refreshToken(refreshToken);
      
      // Update tokens
      storage.setItem(getStorageKey('access_token'), response.access_token);
      storage.setItem(getStorageKey('refresh_token'), response.refresh_token);
      
      // Update expiry
      const expiryTime = Date.now() + (response.expires_in * 1000);
      storage.setItem(getStorageKey('token_expiry'), expiryTime.toString());
      
      // Update user data
      setUser(response.user);
      setPermissions(response.permissions);
      setIsAuthenticated(true);
      
      // Set up new refresh timer if enabled
      if (authConfig.tokenRefresh.enabled) {
        setupTokenRefresh(response.expires_in);
      }
      
    } catch (error) {
      console.error('Token refresh failed:', error);
      // Redirect to login
      await logout();
      throw error;
    }
  };

  const setupTokenRefresh = (expiresIn: number) => {
    // Clear any existing timer
    if (refreshTimerRef.current) {
      clearTimeout(refreshTimerRef.current);
    }
    
    // Refresh token before expiry based on config
    const refreshTime = (expiresIn - authConfig.tokenRefresh.bufferTime) * 1000;
    
    if (refreshTime > 0) {
      refreshTimerRef.current = setTimeout(() => {
        refreshToken().catch((error) => {
          console.error('Auto-refresh failed:', error);
          // Optionally retry based on config
          // Could implement retry logic here if needed
        });
      }, refreshTime);
    }
  };

  // Permission helper functions
  const hasPermission = (permission: string): boolean => {
    // Super admin has all permissions
    if (permissions.includes('system:*')) {
      return true;
    }
    
    // Check exact permission
    if (permissions.includes(permission)) {
      return true;
    }
    
    // Check wildcard permissions
    const parts = permission.split(':');
    for (let i = parts.length; i > 0; i--) {
      const wildcardPerm = parts.slice(0, i - 1).join(':') + ':*';
      if (permissions.includes(wildcardPerm)) {
        return true;
      }
    }
    
    return false;
  };

  const hasAnyPermission = (requiredPermissions: string[]): boolean => {
    return requiredPermissions.some(perm => hasPermission(perm));
  };

  const isSuperAdmin = (): boolean => {
    return user?.role === 'super_admin' || hasPermission('system:*');
  };

  const isTenantAdmin = (tenantId?: string): boolean => {
    if (isSuperAdmin()) return true;
    
    // Check if user has tenant_admin role
    if (user?.role === 'tenant_admin') return true;
    
    if (tenantId) {
      return hasPermission(`tenant:${tenantId}:admin`) || 
             hasPermission(`tenant:${tenantId}:*`);
    }
    
    // Check if admin of any tenant
    return user?.tenants?.some(t => t.role === 'admin' || t.role === 'owner' || t.role === 'tenant_admin') || false;
  };

  const isStoreManager = (storeId?: string): boolean => {
    if (isSuperAdmin()) return true;
    
    if (storeId) {
      return hasPermission(`store:${storeId}:manager`) || 
             hasPermission(`store:${storeId}:*`);
    }
    
    // Debug logging for store manager check
    console.log('isStoreManager check:', {
      stores: user?.stores,
      store_role: user?.store_role,
      role: user?.role,
      storeCheck: user?.stores?.some(s => s.role === 'manager' || s.role === 'store_manager'),
      directRoleCheck: user?.store_role === 'manager' || user?.store_role === 'store_manager',
      mainRoleCheck: user?.role === 'store_manager'
    });
    
    // Check if manager of any store - check for both 'manager' and 'store_manager' roles
    return user?.stores?.some(s => s.role === 'manager' || s.role === 'store_manager') || 
           user?.store_role === 'manager' || 
           user?.store_role === 'store_manager' ||
           user?.role === 'store_manager' ||
           false;
  };

  const isTenantAdminOnly = (): boolean => {
    // Returns true ONLY if user is a tenant admin, not a super admin
    if (isSuperAdmin()) return false;
    
    // Check if user has tenant_admin role
    if (user?.role === 'tenant_admin') return true;
    
    // Check if admin of any tenant
    return user?.tenants?.some(t => t.role === 'admin' || t.role === 'owner' || t.role === 'tenant_admin') || false;
  };

  const value: AuthContextType = {
    user,
    loading,
    isAuthenticated,
    permissions,
    login,
    logout,
    refreshToken,
    hasPermission,
    hasAnyPermission,
    isSuperAdmin,
    isTenantAdmin,
    isStoreManager,
    isTenantAdminOnly
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;