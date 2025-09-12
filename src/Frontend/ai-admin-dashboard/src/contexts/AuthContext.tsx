import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import authService from '../services/authService';

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

  // Check for existing session on mount
  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        setLoading(false);
        return;
      }

      // Verify token and get user info
      const response = await authService.verifyToken();
      
      if (response.valid) {
        setUser(response.payload);
        setIsAuthenticated(true);
        
        // Get fresh user data and permissions
        const userData = await authService.getCurrentUser();
        setUser(userData.user);
        setPermissions(userData.permissions);
      } else {
        // Token invalid, try to refresh
        await refreshToken();
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      // Clear invalid session
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string, rememberMe: boolean = false) => {
    try {
      const response = await authService.login(email, password, rememberMe);
      
      // Store tokens
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);
      
      // Store token expiry for auto-refresh
      const expiryTime = Date.now() + (response.expires_in * 1000);
      localStorage.setItem('token_expiry', expiryTime.toString());
      
      // Set user data
      setUser(response.user);
      setPermissions(response.permissions);
      setIsAuthenticated(true);
      
      // Set up token refresh timer
      setupTokenRefresh(response.expires_in);
      
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
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('token_expiry');
      setUser(null);
      setPermissions([]);
      setIsAuthenticated(false);
    }
  };

  const refreshToken = async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }
      
      const response = await authService.refreshToken(refreshToken);
      
      // Update tokens
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);
      
      // Update expiry
      const expiryTime = Date.now() + (response.expires_in * 1000);
      localStorage.setItem('token_expiry', expiryTime.toString());
      
      // Update user data
      setUser(response.user);
      setPermissions(response.permissions);
      setIsAuthenticated(true);
      
      // Set up new refresh timer
      setupTokenRefresh(response.expires_in);
      
    } catch (error) {
      console.error('Token refresh failed:', error);
      // Redirect to login
      await logout();
      throw error;
    }
  };

  const setupTokenRefresh = (expiresIn: number) => {
    // Refresh token 5 minutes before expiry
    const refreshTime = (expiresIn - 300) * 1000;
    
    if (refreshTime > 0) {
      setTimeout(() => {
        refreshToken().catch(console.error);
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
    
    if (tenantId) {
      return hasPermission(`tenant:${tenantId}:admin`) || 
             hasPermission(`tenant:${tenantId}:*`);
    }
    
    // Check if admin of any tenant
    return user?.tenants?.some(t => t.role === 'admin' || t.role === 'owner') || false;
  };

  const isStoreManager = (storeId?: string): boolean => {
    if (isSuperAdmin()) return true;
    
    if (storeId) {
      return hasPermission(`store:${storeId}:manager`) || 
             hasPermission(`store:${storeId}:*`);
    }
    
    // Check if manager of any store
    return user?.stores?.some(s => s.role === 'manager') || false;
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
    isStoreManager
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;