/**
 * HTTP Client Wrapper
 *
 * Centralized HTTP client with:
 * - Automatic retry logic
 * - Request deduplication
 * - Error handling
 * - Request/response interceptors
 * - AbortController support
 *
 * Principles:
 * - SRP: Single responsibility - HTTP communication
 * - DRY: Reusable client configuration
 * - KISS: Simple API, complex logic hidden
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import {
  handleApiError,
  retryWithBackoff,
  requestCache,
  generateCacheKey,
  logError,
  RetryOptions,
} from './api-error-handler';

// ============================================================================
// HTTP Client Configuration
// ============================================================================

/**
 * HTTP client configuration options
 */
export interface HttpClientConfig {
  baseURL: string;
  timeout: number;
  headers?: Record<string, string>;
  retryOptions?: Partial<RetryOptions>;
  enableDeduplication?: boolean;
  onRequest?: (config: AxiosRequestConfig) => AxiosRequestConfig | Promise<AxiosRequestConfig>;
  onResponse?: (response: AxiosResponse) => AxiosResponse | Promise<AxiosResponse>;
  onError?: (error: unknown) => void;
}

/**
 * Default HTTP client configuration
 */
const DEFAULT_CONFIG: Partial<HttpClientConfig> = {
  timeout: 30000, // 30 seconds
  enableDeduplication: true,
  retryOptions: {
    maxRetries: 3,
    initialDelayMs: 1000,
  },
};

// ============================================================================
// HTTP Client Class
// ============================================================================

/**
 * HTTP Client with retry, deduplication, and error handling
 *
 * Following SRP - handles all HTTP communication concerns
 */
export class HttpClient {
  private axiosInstance: AxiosInstance;
  private config: HttpClientConfig;
  private abortControllers: Map<string, AbortController> = new Map();

  constructor(config: HttpClientConfig) {
    this.config = { ...DEFAULT_CONFIG, ...config } as HttpClientConfig;

    // Create axios instance
    this.axiosInstance = axios.create({
      baseURL: this.config.baseURL,
      timeout: this.config.timeout,
      headers: {
        'Content-Type': 'application/json',
        ...this.config.headers,
      },
    });

    // Set up interceptors
    this.setupInterceptors();
  }

  /**
   * Set up request/response interceptors
   */
  private setupInterceptors(): void {
    // Request interceptor
    this.axiosInstance.interceptors.request.use(
      async (config) => {
        // Call custom request handler if provided
        if (this.config.onRequest) {
          config = await this.config.onRequest(config);
        }

        // Log request in development
        if (process.env.NODE_ENV === 'development') {
          console.log(`[HTTP] ${config.method?.toUpperCase()} ${config.url}`, {
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

    // Response interceptor
    this.axiosInstance.interceptors.response.use(
      async (response) => {
        // Call custom response handler if provided
        if (this.config.onResponse) {
          response = await this.config.onResponse(response);
        }

        // Log response in development
        if (process.env.NODE_ENV === 'development') {
          console.log(`[HTTP] ${response.status} ${response.config.url}`, {
            data: response.data,
          });
        }

        return response;
      },
      (error) => {
        // Handle error with our error handler
        const apiError = handleApiError(error);

        // Log error
        logError(apiError, {
          url: error.config?.url,
          method: error.config?.method,
        });

        // Call custom error handler if provided
        if (this.config.onError) {
          this.config.onError(apiError);
        }

        return Promise.reject(apiError);
      }
    );
  }

  /**
   * Set authentication token
   */
  setAuthToken(token: string | null): void {
    if (token) {
      this.axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete this.axiosInstance.defaults.headers.common['Authorization'];
    }
  }

  /**
   * Set custom header
   */
  setHeader(key: string, value: string): void {
    this.axiosInstance.defaults.headers.common[key] = value;
  }

  /**
   * Remove custom header
   */
  removeHeader(key: string): void {
    delete this.axiosInstance.defaults.headers.common[key];
  }

  /**
   * GET request with retry and deduplication
   */
  async get<T = unknown>(
    url: string,
    config?: AxiosRequestConfig & { skipRetry?: boolean; skipDedup?: boolean }
  ): Promise<T> {
    const requestFn = () => this.executeGet<T>(url, config);

    // Apply deduplication if enabled
    if (this.config.enableDeduplication && !config?.skipDedup) {
      const cacheKey = generateCacheKey('GET', url, config?.params);
      return requestCache.getOrExecute(cacheKey, () => this.executeWithRetry(requestFn, config?.skipRetry));
    }

    return this.executeWithRetry(requestFn, config?.skipRetry);
  }

  /**
   * POST request with retry
   */
  async post<T = unknown>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig & { skipRetry?: boolean }
  ): Promise<T> {
    const requestFn = () => this.executePost<T>(url, data, config);
    return this.executeWithRetry(requestFn, config?.skipRetry);
  }

  /**
   * PUT request with retry
   */
  async put<T = unknown>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig & { skipRetry?: boolean }
  ): Promise<T> {
    const requestFn = () => this.executePut<T>(url, data, config);
    return this.executeWithRetry(requestFn, config?.skipRetry);
  }

  /**
   * PATCH request with retry
   */
  async patch<T = unknown>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig & { skipRetry?: boolean }
  ): Promise<T> {
    const requestFn = () => this.executePatch<T>(url, data, config);
    return this.executeWithRetry(requestFn, config?.skipRetry);
  }

  /**
   * DELETE request with retry
   */
  async delete<T = unknown>(
    url: string,
    config?: AxiosRequestConfig & { skipRetry?: boolean }
  ): Promise<T> {
    const requestFn = () => this.executeDelete<T>(url, config);
    return this.executeWithRetry(requestFn, config?.skipRetry);
  }

  /**
   * Execute request with retry logic
   */
  private async executeWithRetry<T>(
    requestFn: () => Promise<T>,
    skipRetry?: boolean
  ): Promise<T> {
    if (skipRetry) {
      return requestFn();
    }

    return retryWithBackoff(requestFn, this.config.retryOptions);
  }

  /**
   * Execute GET request
   */
  private async executeGet<T>(
    url: string,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const abortController = new AbortController();
    const requestKey = `GET:${url}`;
    this.abortControllers.set(requestKey, abortController);

    try {
      const response = await this.axiosInstance.get<T>(url, {
        ...config,
        signal: abortController.signal,
      });
      return response.data;
    } finally {
      this.abortControllers.delete(requestKey);
    }
  }

  /**
   * Execute POST request
   */
  private async executePost<T>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const abortController = new AbortController();
    const requestKey = `POST:${url}`;
    this.abortControllers.set(requestKey, abortController);

    try {
      const response = await this.axiosInstance.post<T>(url, data, {
        ...config,
        signal: abortController.signal,
      });
      return response.data;
    } finally {
      this.abortControllers.delete(requestKey);
    }
  }

  /**
   * Execute PUT request
   */
  private async executePut<T>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const abortController = new AbortController();
    const requestKey = `PUT:${url}`;
    this.abortControllers.set(requestKey, abortController);

    try {
      const response = await this.axiosInstance.put<T>(url, data, {
        ...config,
        signal: abortController.signal,
      });
      return response.data;
    } finally {
      this.abortControllers.delete(requestKey);
    }
  }

  /**
   * Execute PATCH request
   */
  private async executePatch<T>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const abortController = new AbortController();
    const requestKey = `PATCH:${url}`;
    this.abortControllers.set(requestKey, abortController);

    try {
      const response = await this.axiosInstance.patch<T>(url, data, {
        ...config,
        signal: abortController.signal,
      });
      return response.data;
    } finally {
      this.abortControllers.delete(requestKey);
    }
  }

  /**
   * Execute DELETE request
   */
  private async executeDelete<T>(
    url: string,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const abortController = new AbortController();
    const requestKey = `DELETE:${url}`;
    this.abortControllers.set(requestKey, abortController);

    try {
      const response = await this.axiosInstance.delete<T>(url, {
        ...config,
        signal: abortController.signal,
      });
      return response.data;
    } finally {
      this.abortControllers.delete(requestKey);
    }
  }

  /**
   * Cancel specific request
   */
  cancelRequest(method: string, url: string): void {
    const requestKey = `${method}:${url}`;
    const controller = this.abortControllers.get(requestKey);
    if (controller) {
      controller.abort();
      this.abortControllers.delete(requestKey);
    }
  }

  /**
   * Cancel all pending requests
   */
  cancelAllRequests(): void {
    this.abortControllers.forEach(controller => controller.abort());
    this.abortControllers.clear();
  }

  /**
   * Clear request deduplication cache
   */
  clearCache(): void {
    requestCache.clear();
  }
}

// ============================================================================
// Create Default Client Instance
// ============================================================================

/**
 * Get API base URL from environment
 *
 * Cloud-First: Requires VITE_API_URL to be set in production environments
 */
function getApiBaseUrl(): string {
  // Try Vite env var first
  if (import.meta.env?.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }

  // Try process.env (for compatibility)
  if (typeof process !== 'undefined' && process.env?.VITE_API_URL) {
    return process.env.VITE_API_URL;
  }

  // Only fall back to localhost in development mode
  if (import.meta.env.DEV || process.env.NODE_ENV === 'development') {
    console.warn('⚠️ VITE_API_URL not set, using localhost default for development');
    return 'http://localhost:6024';
  }

  // In production, VITE_API_URL must be explicitly set
  throw new Error(
    'VITE_API_URL environment variable is not set. ' +
    'Please configure it in your .env file for your deployment environment. ' +
    'This is required for cloud deployments.'
  );
}

/**
 * Default HTTP client instance
 *
 * Pre-configured with standard settings.
 * Use this for most API calls.
 */
export const httpClient = new HttpClient({
  baseURL: getApiBaseUrl(),
  timeout: 30000,
  retryOptions: {
    maxRetries: 3,
    initialDelayMs: 1000,
    maxDelayMs: 10000,
    backoffMultiplier: 2,
  },
  enableDeduplication: true,
  onRequest: async (config) => {
    // Add auth token from localStorage
    const token = localStorage.getItem('authToken');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
});

/**
 * Create custom HTTP client instance
 *
 * Use this when you need different configuration.
 *
 * @example
 * const customClient = createHttpClient({
 *   baseURL: 'https://api.example.com',
 *   timeout: 60000,
 *   retryOptions: { maxRetries: 5 }
 * });
 */
export function createHttpClient(config: HttpClientConfig): HttpClient {
  return new HttpClient(config);
}
