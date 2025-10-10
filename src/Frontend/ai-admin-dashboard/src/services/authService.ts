import axios, { AxiosInstance } from 'axios';
import { authConfig, getAuthStorage, getStorageKey } from '../config/auth.config';

const API_BASE_URL = authConfig.endpoints.baseUrl;

// Create axios instance for auth endpoints (no auth interceptor)
const authApi: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Create axios instance for authenticated requests
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth interceptor for authenticated requests
api.interceptors.request.use(
  (config) => {
    const storage = getAuthStorage();
    const token = storage.getItem(getStorageKey('access_token'));
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Track if we're currently refreshing
let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

const subscribeTokenRefresh = (cb: (token: string) => void) => {
  refreshSubscribers.push(cb);
};

const onTokenRefreshed = (token: string) => {
  refreshSubscribers.forEach(cb => cb(token));
  refreshSubscribers = [];
};

// Add response interceptor to handle token expiry
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      if (!isRefreshing) {
        isRefreshing = true;
        
        try {
          const storage = getAuthStorage();
          const refreshToken = storage.getItem(getStorageKey('refresh_token'));
          if (refreshToken) {
            const response = await authService.refreshToken(refreshToken);
            storage.setItem(getStorageKey('access_token'), response.access_token);
            storage.setItem(getStorageKey('refresh_token'), response.refresh_token);
            
            isRefreshing = false;
            onTokenRefreshed(response.access_token);
            
            // Retry original request with new token
            originalRequest.headers.Authorization = `Bearer ${response.access_token}`;
            return api(originalRequest);
          }
        } catch (refreshError) {
          // Refresh failed, only clear auth-related items
          isRefreshing = false;
          const storage = getAuthStorage();
          storage.removeItem(getStorageKey('access_token'));
          storage.removeItem(getStorageKey('refresh_token'));
          storage.removeItem(getStorageKey('token_expiry'));
          window.location.href = authConfig.redirects.unauthorized;
          return Promise.reject(refreshError);
        }
      } else {
        // Wait for token refresh to complete
        return new Promise((resolve) => {
          subscribeTokenRefresh((token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            resolve(api(originalRequest));
          });
        });
      }
    }
    
    return Promise.reject(error);
  }
);

export interface LoginRequest {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: {
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
  };
  permissions: string[];
}

export interface RefreshTokenResponse extends LoginResponse {}

export interface CurrentUserResponse {
  user: any;
  permissions: string[];
}

export interface TokenVerifyResponse {
  valid: boolean;
  payload?: any;
}

class AuthService {
  /**
   * Login admin user
   */
  async login(email: string, password: string, rememberMe: boolean = false): Promise<LoginResponse> {
    const response = await authApi.post<LoginResponse>(authConfig.endpoints.login, {
      email,
      password,
      remember_me: rememberMe
    });
    return response.data;
  }

  /**
   * Logout current user
   */
  async logout(): Promise<void> {
    try {
      await api.post(authConfig.endpoints.logout);
    } catch (error) {
      console.error('Logout API call failed:', error);
    }
  }

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken: string): Promise<RefreshTokenResponse> {
    const response = await authApi.post<RefreshTokenResponse>(authConfig.endpoints.refresh, {
      refresh_token: refreshToken
    });
    return response.data;
  }

  /**
   * Get current user information
   */
  async getCurrentUser(): Promise<CurrentUserResponse> {
    const response = await api.get<CurrentUserResponse>(authConfig.endpoints.me);
    return response.data;
  }

  /**
   * Verify if token is valid
   */
  async verifyToken(): Promise<TokenVerifyResponse> {
    const response = await api.post<TokenVerifyResponse>(authConfig.endpoints.verify);
    return response.data;
  }

  /**
   * Create new admin user (super admin only)
   */
  async createAdminUser(data: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    role: string;
    tenant_id?: string;
  }): Promise<any> {
    const response = await api.post('/api/v2/identity-access/users', data);
    return response.data;
  }

  /**
   * Check if user has specific permission
   */
  hasPermission(permissions: string[], requiredPermission: string): boolean {
    // Super admin has all permissions
    if (permissions.includes('system:*')) {
      return true;
    }
    
    // Check exact permission
    if (permissions.includes(requiredPermission)) {
      return true;
    }
    
    // Check wildcard permissions
    const parts = requiredPermission.split(':');
    for (let i = parts.length; i > 0; i--) {
      const wildcardPerm = parts.slice(0, i - 1).join(':') + ':*';
      if (permissions.includes(wildcardPerm)) {
        return true;
      }
    }
    
    return false;
  }

  /**
   * Check if user has any of the required permissions
   */
  hasAnyPermission(permissions: string[], requiredPermissions: string[]): boolean {
    return requiredPermissions.some(perm => this.hasPermission(permissions, perm));
  }

  /**
   * Check if user has all required permissions
   */
  hasAllPermissions(permissions: string[], requiredPermissions: string[]): boolean {
    return requiredPermissions.every(perm => this.hasPermission(permissions, perm));
  }

  /**
   * Get authorization header
   */
  getAuthHeader(): { Authorization: string } | {} {
    const storage = getAuthStorage();
    const token = storage.getItem(getStorageKey('access_token'));
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    const storage = getAuthStorage();
    const token = storage.getItem(getStorageKey('access_token'));
    const expiry = storage.getItem(getStorageKey('token_expiry'));

    if (!token || !expiry) {
      return false;
    }

    // Check if token is expired
    const expiryTime = parseInt(expiry, 10);
    if (Date.now() > expiryTime) {
      // Token expired, clear storage
      storage.removeItem(getStorageKey('access_token'));
      storage.removeItem(getStorageKey('refresh_token'));
      storage.removeItem(getStorageKey('token_expiry'));
      return false;
    }

    return true;
  }

  /**
   * Change password for the current user
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<{ message: string }> {
    const response = await api.post('/api/v2/identity-access/users/change-password', {
      current_password: currentPassword,
      new_password: newPassword
    });
    return response.data;
  }
}

const authService = new AuthService();

export default authService;