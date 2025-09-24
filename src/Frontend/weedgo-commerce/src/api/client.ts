import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios';
import toast from 'react-hot-toast';

// Types
interface AuthTokens {
  access: string;
  refresh: string;
}

interface RefreshResponse {
  access: string;
  refresh: string;
}

// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5024';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token management
const tokenManager = {
  getAccessToken: (): string | null => {
    return localStorage.getItem('access_token');
  },
  getRefreshToken: (): string | null => {
    return localStorage.getItem('refresh_token');
  },
  setTokens: (tokens: AuthTokens): void => {
    localStorage.setItem('access_token', tokens.access);
    localStorage.setItem('refresh_token', tokens.refresh);
  },
  clearTokens: (): void => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  },
};

// Request queue for token refresh
let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

const subscribeTokenRefresh = (cb: (token: string) => void) => {
  refreshSubscribers.push(cb);
};

const onTokenRefreshed = (token: string) => {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
};

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token
    const token = tokenManager.getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add store ID header from selected store (managed by StoreContext)
    const storeId = localStorage.getItem('selected_store_id');
    if (storeId) {
      config.headers['X-Store-ID'] = storeId;
    }

    // Add tenant ID header - single source of truth from environment
    const tenantId = import.meta.env.VITE_TENANT_ID;
    if (tenantId) {
      config.headers['X-Tenant-ID'] = tenantId;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

    // Handle 401 Unauthorized
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (!isRefreshing) {
        isRefreshing = true;
        originalRequest._retry = true;

        const refreshToken = tokenManager.getRefreshToken();
        if (refreshToken) {
          try {
            const { data } = await axios.post<RefreshResponse>(
              `${import.meta.env.VITE_API_BASE_URL}/api/auth/refresh`,
              { refresh: refreshToken }
            );

            tokenManager.setTokens(data);
            isRefreshing = false;
            onTokenRefreshed(data.access);

            // Retry original request with new token
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${data.access}`;
            }
            return apiClient(originalRequest);
          } catch (refreshError) {
            isRefreshing = false;
            tokenManager.clearTokens();

            // Only redirect to login if not already there
            if (window.location.pathname !== '/login') {
              window.location.href = '/login';
            }

            toast.error('Session expired. Please login again.');
            return Promise.reject(refreshError);
          }
        } else {
          // No refresh token available
          tokenManager.clearTokens();
          if (window.location.pathname !== '/login') {
            window.location.href = '/login';
          }
        }
      } else {
        // Token refresh is already in progress
        return new Promise((resolve) => {
          subscribeTokenRefresh((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            resolve(apiClient(originalRequest));
          });
        });
      }
    }

    // Handle other error responses
    if (error.response) {
      const message = (error.response.data as any)?.detail ||
                     (error.response.data as any)?.message ||
                     'An error occurred';

      // Only show toast for non-401 errors
      if (error.response.status !== 401) {
        toast.error(message);
      }
    } else if (error.request) {
      toast.error('Network error. Please check your connection.');
    } else {
      toast.error('An unexpected error occurred.');
    }

    return Promise.reject(error);
  }
);

// Export client and utility functions
export default apiClient;

export const setAuthTokens = (tokens: AuthTokens) => {
  tokenManager.setTokens(tokens);
};

export const clearAuthTokens = () => {
  tokenManager.clearTokens();
};

export const isAuthenticated = (): boolean => {
  return !!tokenManager.getAccessToken();
};

// Utility function for file uploads
export const createFormData = (data: Record<string, any>): FormData => {
  const formData = new FormData();

  Object.keys(data).forEach((key) => {
    if (data[key] !== null && data[key] !== undefined) {
      if (data[key] instanceof File || data[key] instanceof Blob) {
        formData.append(key, data[key]);
      } else if (typeof data[key] === 'object') {
        formData.append(key, JSON.stringify(data[key]));
      } else {
        formData.append(key, String(data[key]));
      }
    }
  });

  return formData;
};