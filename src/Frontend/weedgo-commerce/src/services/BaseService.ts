import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import toast from 'react-hot-toast';
import { ApiResponse, PaginatedResponse } from '@/types';

export interface ServiceConfig {
  baseURL?: string;
  timeout?: number;
  headers?: Record<string, string>;
}

export interface RequestOptions extends AxiosRequestConfig {
  showErrorToast?: boolean;
  retryCount?: number;
  retryDelay?: number;
}

/**
 * Base service class for API communication
 * Implements common patterns like error handling, retries, and caching
 */
export abstract class BaseService {
  protected client: AxiosInstance;
  private cache: Map<string, { data: any; timestamp: number }> = new Map();
  private cacheTimeout = 5 * 60 * 1000; // 5 minutes default

  constructor(config?: ServiceConfig) {
    this.client = axios.create({
      baseURL: config?.baseURL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:5024',
      timeout: config?.timeout || 30000,
      headers: {
        'Content-Type': 'application/json',
        ...config?.headers
      }
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token
        const token = this.getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // Add store and tenant IDs
        const storeId = this.getStoreId();
        const tenantId = this.getTenantId();

        if (storeId) {
          config.headers['X-Store-ID'] = storeId;
        }

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
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          await this.handleUnauthorized();
        }

        return Promise.reject(error);
      }
    );
  }

  protected getAuthToken(): string | null {
    return localStorage.getItem('access_token');
  }

  protected getStoreId(): string | null {
    return localStorage.getItem('store_id') || import.meta.env.VITE_STORE_ID;
  }

  protected getTenantId(): string | null {
    return localStorage.getItem('tenant_id') || import.meta.env.VITE_TENANT_ID;
  }

  protected async handleUnauthorized(): Promise<void> {
    // Clear auth data and redirect to login
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    window.location.href = '/login';
  }

  /**
   * GET request with caching support
   */
  protected async get<T>(
    url: string,
    options?: RequestOptions & { useCache?: boolean; cacheKey?: string }
  ): Promise<ApiResponse<T>> {
    try {
      // Check cache
      if (options?.useCache) {
        const cacheKey = options.cacheKey || url;
        const cached = this.getFromCache(cacheKey);
        if (cached) {
          return { data: cached, status: 200 };
        }
      }

      const response = await this.executeWithRetry<T>(
        () => this.client.get<T>(url, options),
        options
      );

      // Store in cache
      if (options?.useCache) {
        const cacheKey = options.cacheKey || url;
        this.setCache(cacheKey, response.data);
      }

      return { data: response.data, status: response.status };
    } catch (error) {
      return this.handleError(error, options);
    }
  }

  /**
   * POST request
   */
  protected async post<T>(
    url: string,
    data?: any,
    options?: RequestOptions
  ): Promise<ApiResponse<T>> {
    try {
      const response = await this.executeWithRetry<T>(
        () => this.client.post<T>(url, data, options),
        options
      );

      return { data: response.data, status: response.status };
    } catch (error) {
      return this.handleError(error, options);
    }
  }

  /**
   * PUT request
   */
  protected async put<T>(
    url: string,
    data?: any,
    options?: RequestOptions
  ): Promise<ApiResponse<T>> {
    try {
      const response = await this.executeWithRetry<T>(
        () => this.client.put<T>(url, data, options),
        options
      );

      return { data: response.data, status: response.status };
    } catch (error) {
      return this.handleError(error, options);
    }
  }

  /**
   * PATCH request
   */
  protected async patch<T>(
    url: string,
    data?: any,
    options?: RequestOptions
  ): Promise<ApiResponse<T>> {
    try {
      const response = await this.executeWithRetry<T>(
        () => this.client.patch<T>(url, data, options),
        options
      );

      return { data: response.data, status: response.status };
    } catch (error) {
      return this.handleError(error, options);
    }
  }

  /**
   * DELETE request
   */
  protected async delete<T>(
    url: string,
    options?: RequestOptions
  ): Promise<ApiResponse<T>> {
    try {
      const response = await this.executeWithRetry<T>(
        () => this.client.delete<T>(url, options),
        options
      );

      return { data: response.data, status: response.status };
    } catch (error) {
      return this.handleError(error, options);
    }
  }

  /**
   * Execute request with retry logic
   */
  private async executeWithRetry<T>(
    request: () => Promise<AxiosResponse<T>>,
    options?: RequestOptions
  ): Promise<AxiosResponse<T>> {
    const maxRetries = options?.retryCount || 0;
    const retryDelay = options?.retryDelay || 1000;

    let lastError: any;

    for (let i = 0; i <= maxRetries; i++) {
      try {
        return await request();
      } catch (error) {
        lastError = error;

        if (i < maxRetries) {
          await this.delay(retryDelay * Math.pow(2, i)); // Exponential backoff
        }
      }
    }

    throw lastError;
  }

  /**
   * Handle errors consistently
   */
  private handleError(error: any, options?: RequestOptions): ApiResponse<any> {
    const message = error.response?.data?.message || error.message || 'An error occurred';

    if (options?.showErrorToast !== false) {
      toast.error(message);
    }

    return {
      error: message,
      status: error.response?.status || 500
    };
  }

  /**
   * Cache management
   */
  private getFromCache(key: string): any | null {
    const cached = this.cache.get(key);

    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.data;
    }

    this.cache.delete(key);
    return null;
  }

  private setCache(key: string, data: any): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }

  protected clearCache(): void {
    this.cache.clear();
  }

  /**
   * Utility methods
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Build query string from params object
   */
  protected buildQueryString(params: Record<string, any>): string {
    const searchParams = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, String(value));
      }
    });

    const queryString = searchParams.toString();
    return queryString ? `?${queryString}` : '';
  }

  /**
   * Helper for paginated requests
   */
  protected async getPaginated<T>(
    url: string,
    params?: {
      page?: number;
      pageSize?: number;
      [key: string]: any;
    },
    options?: RequestOptions
  ): Promise<ApiResponse<PaginatedResponse<T>>> {
    const queryString = params ? this.buildQueryString(params) : '';
    const fullUrl = `${url}${queryString}`;

    const response = await this.get<any>(fullUrl, options);

    if (response.data) {
      // Transform response to standard paginated format
      const paginatedResponse: PaginatedResponse<T> = {
        items: response.data.items || response.data.results || response.data.data || [],
        total: response.data.total || response.data.count || 0,
        page: response.data.page || params?.page || 1,
        pageSize: response.data.pageSize || response.data.page_size || params?.pageSize || 20,
        hasMore: response.data.hasMore || response.data.has_more || false
      };

      return { data: paginatedResponse, status: response.status };
    }

    return response;
  }
}