import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import * as SecureStore from 'expo-secure-store';
import Constants from 'expo-constants';
import { ApiError } from '@/types/api.types';

// Environment variables - Using EXPO_PUBLIC_ prefix for Expo environment variables
const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://10.0.0.169:5024';
const TENANT_ID = process.env.EXPO_PUBLIC_TENANT_ID || 'ce2d57bc-b3ba-4801-b229-889a9fe9626d'; // Pot Palace tenant
const API_TIMEOUT = Number(process.env.EXPO_PUBLIC_API_TIMEOUT) || 30000;

// Secure storage keys
const TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

class ApiClient {
  private client: AxiosInstance;
  private isRefreshing = false;
  private refreshSubscribers: ((token: string) => void)[] = [];

  constructor() {
    console.log('ApiClient initialized with:', { API_URL, TENANT_ID });
    this.client = axios.create({
      baseURL: API_URL,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
        'X-Tenant-ID': TENANT_ID,
        'X-App-Version': Constants.expoConfig?.version || '1.0.0',
        'X-Platform': Constants.platform?.ios ? 'ios' : 'android',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor - add auth token and store ID
    this.client.interceptors.request.use(
      async (config: InternalAxiosRequestConfig) => {
        // Skip auth header for auth endpoints
        const isAuthEndpoint = config.url?.includes('/auth/') &&
                              !config.url?.includes('/auth/refresh');

        if (!isAuthEndpoint) {
          const token = await SecureStore.getItemAsync(TOKEN_KEY);
          if (token) {
            config.headers.Authorization = `Bearer ${token}`;
          }
        }

        // Add current store ID from secure storage if available
        try {
          const storeData = await SecureStore.getItemAsync('weedgo-store-storage');
          if (storeData) {
            const parsed = JSON.parse(storeData);
            const currentStore = parsed?.state?.currentStore;
            if (currentStore?.id) {
              config.headers['X-Store-ID'] = currentStore.id;
            }
          }
        } catch (error) {
          // Store not available yet, skip adding header
        }

        // Add cart session ID if available
        try {
          const cartSessionId = await SecureStore.getItemAsync('cart_session_id');
          if (cartSessionId) {
            config.headers['X-Session-ID'] = cartSessionId;
          }
        } catch (error) {
          // Cart session not available yet, skip adding header
        }

        // Log request in development
        if (__DEV__) {
          console.log('API Request:', {
            method: config.method,
            url: config.url,
            params: config.params,
            data: config.data,
          });
        }

        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor - handle errors and token refresh
    this.client.interceptors.response.use(
      (response) => {
        // Log response in development
        if (__DEV__) {
          console.log('API Response:', {
            status: response.status,
            url: response.config.url,
            data: response.data,
          });
        }
        return response;
      },
      async (error: AxiosError<ApiError>) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
        const status = error.response?.status;
        const url = originalRequest?.url || '';

        // Determine if this is an expected error that shouldn't be logged as an error
        const isExpectedError = (
          // Authentication failures are expected when not logged in
          (status === 401 && !originalRequest._retry) ||
          // 404s for known fallback endpoints are expected
          (status === 404 && (
            url.includes('/api/v1/auth/me') ||
            url.includes('/api/v1/auth/customer/profile') ||
            url.includes('/api/v1/auth/customer/profile/image') ||
            url.includes('/api/v1/auth/customer/addresses') ||
            url.includes('/api/v1/auth/customer/verify-email') ||
            url.includes('/api/v1/auth/customer/verify-email/confirm')
          ))
        );

        // Log error in development (but not for expected cases)
        if (__DEV__ && !isExpectedError) {
          console.error('API Error:', {
            status: error.response?.status,
            url: originalRequest?.url,
            message: error.response?.data?.message || error.message,
            data: error.response?.data,
            detail: error.response?.data?.detail,
            params: originalRequest?.params,
          });

          // Log validation errors more clearly
          if (error.response?.data?.detail && Array.isArray(error.response.data.detail)) {
            console.error('Validation errors:', error.response.data.detail.map((d: any) =>
              `${d.loc?.join('.')} - ${d.msg}`
            ).join(', '));
          }
        }

        // Handle 401 - Token expired
        if (error.response?.status === 401 && !originalRequest._retry) {
          if (!this.isRefreshing) {
            this.isRefreshing = true;
            originalRequest._retry = true;

            try {
              const refreshToken = await SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
              if (!refreshToken) {
                // Silently handle missing refresh token - user just needs to login
                await this.clearTokens();
                this.redirectToLogin();
                return Promise.reject(error);
              }

              const response = await this.refreshAccessToken(refreshToken);
              // Handle both field name formats from backend
              const accessToken = response.data.access_token || response.data.access;
              const newRefreshToken = response.data.refresh_token || response.data.refresh;

              // Save new tokens
              await SecureStore.setItemAsync(TOKEN_KEY, accessToken);
              await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, newRefreshToken);

              // Notify all subscribers
              this.onRefreshed(accessToken);
              this.refreshSubscribers = [];

              // Retry original request
              originalRequest.headers.Authorization = `Bearer ${accessToken}`;
              return this.client(originalRequest);
            } catch (refreshError) {
              // Refresh failed - clear tokens and redirect to login
              await this.clearTokens();
              this.redirectToLogin();
              return Promise.reject(refreshError);
            } finally {
              this.isRefreshing = false;
            }
          }

          // Wait for token refresh to complete
          return new Promise((resolve) => {
            this.subscribeTokenRefresh((token: string) => {
              originalRequest.headers.Authorization = `Bearer ${token}`;
              resolve(this.client(originalRequest));
            });
          });
        }

        // Transform error for consistent handling
        const apiError: ApiError = {
          error: error.response?.data?.error || 'Unknown error',
          message: error.response?.data?.message || error.message,
          statusCode: error.response?.status || 0,
          details: error.response?.data?.details,
        };

        return Promise.reject(apiError);
      }
    );
  }

  private async refreshAccessToken(refreshToken: string) {
    return axios.post(`${API_URL}/api/v1/auth/refresh`, null, {
      headers: {
        Authorization: `Bearer ${refreshToken}`,
        'X-Tenant-ID': TENANT_ID,
      },
    });
  }

  private onRefreshed(token: string) {
    this.refreshSubscribers.forEach((callback) => callback(token));
  }

  private subscribeTokenRefresh(callback: (token: string) => void) {
    this.refreshSubscribers.push(callback);
  }

  private async clearTokens() {
    await SecureStore.deleteItemAsync(TOKEN_KEY);
    await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
  }

  private redirectToLogin() {
    // This will be handled by navigation/auth context
    // Emit event or call navigation method
    if (__DEV__) {
      console.log('Redirecting to login...');
    }
  }

  // Public methods for making requests
  public get<T>(url: string, config?: any) {
    return this.client.get<T>(url, config);
  }

  public post<T>(url: string, data?: any, config?: any) {
    return this.client.post<T>(url, data, config);
  }

  public put<T>(url: string, data?: any, config?: any) {
    return this.client.put<T>(url, data, config);
  }

  public patch<T>(url: string, data?: any, config?: any) {
    return this.client.patch<T>(url, data, config);
  }

  public delete<T>(url: string, config?: any) {
    return this.client.delete<T>(url, config);
  }

  // Helper methods
  public async saveTokens(accessToken: string, refreshToken: string) {
    await SecureStore.setItemAsync(TOKEN_KEY, accessToken);
    await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, refreshToken);
  }

  public async getTokens() {
    const accessToken = await SecureStore.getItemAsync(TOKEN_KEY);
    const refreshToken = await SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
    return { accessToken, refreshToken };
  }

  public async logout() {
    await this.clearTokens();
  }

  public async isAuthenticated(): Promise<boolean> {
    const token = await SecureStore.getItemAsync(TOKEN_KEY);
    return !!token;
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export types for convenience
export type { ApiError } from '@/types/api.types';
export type ApiResponse<T = any> = {
  data: T;
  message?: string;
  error?: string;
};