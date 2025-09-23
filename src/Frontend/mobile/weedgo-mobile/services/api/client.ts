import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import * as SecureStore from 'expo-secure-store';
import Constants from 'expo-constants';
import { ApiError } from '@/types/api.types';

// Environment variables
const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:5024';
const TENANT_ID = process.env.EXPO_PUBLIC_TENANT_ID || '00000000-0000-0000-0000-000000000001';

// Secure storage keys
const TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

class ApiClient {
  private client: AxiosInstance;
  private isRefreshing = false;
  private refreshSubscribers: ((token: string) => void)[] = [];

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      timeout: 30000,
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

        // Log error in development
        if (__DEV__) {
          console.error('API Error:', {
            status: error.response?.status,
            url: originalRequest?.url,
            message: error.response?.data?.message || error.message,
          });
        }

        // Handle 401 - Token expired
        if (error.response?.status === 401 && !originalRequest._retry) {
          if (!this.isRefreshing) {
            this.isRefreshing = true;
            originalRequest._retry = true;

            try {
              const refreshToken = await SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
              if (!refreshToken) {
                throw new Error('No refresh token available');
              }

              const response = await this.refreshAccessToken(refreshToken);
              const { access_token, refresh_token } = response.data;

              // Save new tokens
              await SecureStore.setItemAsync(TOKEN_KEY, access_token);
              await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, refresh_token);

              // Notify all subscribers
              this.onRefreshed(access_token);
              this.refreshSubscribers = [];

              // Retry original request
              originalRequest.headers.Authorization = `Bearer ${access_token}`;
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