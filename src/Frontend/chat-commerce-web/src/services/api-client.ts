/**
 * Centralized API Client with Tenant Header Propagation
 * Implements interceptor pattern for automatic header injection
 * Follows Singleton pattern for consistent API access
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';

/**
 * Tenant information interface
 */
interface TenantInfo {
  tenantId: string;
  tenantCode: string;
  templateId: string;
  storeId?: string;
}

/**
 * API Error response structure
 */
interface ApiError {
  message: string;
  code?: string;
  details?: any;
  timestamp?: string;
}

/**
 * Request retry configuration
 */
interface RetryConfig {
  retries: number;
  retryDelay: number;
  retryCondition?: (error: AxiosError) => boolean;
}

/**
 * API Client Configuration
 */
interface ApiClientConfig {
  baseURL?: string;
  timeout?: number;
  retryConfig?: RetryConfig;
  enableLogging?: boolean;
  enableMetrics?: boolean;
}

/**
 * API Client Class
 * Manages all API communications with automatic tenant context
 */
class ApiClient {
  private static instance: ApiClient;
  private axiosInstance: AxiosInstance;
  private tenantInfo: TenantInfo | null = null;
  private requestInterceptorId: number | null = null;
  private responseInterceptorId: number | null = null;
  private metricsEnabled: boolean = false;
  private loggingEnabled: boolean = false;
  
  /**
   * Private constructor for singleton pattern
   */
  private constructor(config: ApiClientConfig = {}) {
    const defaultConfig: AxiosRequestConfig = {
      baseURL: config.baseURL || this.determineBaseURL(),
      timeout: config.timeout || 30000,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      withCredentials: true // Enable cookies for session management
    };
    
    this.axiosInstance = axios.create(defaultConfig);
    this.metricsEnabled = config.enableMetrics || false;
    this.loggingEnabled = config.enableLogging || import.meta.env.MODE === 'development';
    
    this.setupInterceptors();
    this.resolveTenantFromEnvironment();
    
    // Setup retry logic if configured
    if (config.retryConfig) {
      this.setupRetryLogic(config.retryConfig);
    }
  }
  
  /**
   * Get singleton instance
   */
  public static getInstance(config?: ApiClientConfig): ApiClient {
    if (!ApiClient.instance) {
      ApiClient.instance = new ApiClient(config);
    }
    return ApiClient.instance;
  }
  
  /**
   * Determine base URL based on environment
   */
  private determineBaseURL(): string {
    // Check for environment variable
    if (import.meta.env.VITE_API_URL) {
      return import.meta.env.VITE_API_URL;
    }
    
    // Use empty string for proxy in development (api.ts already adds /api prefix)
    if (import.meta.env.MODE === 'development') {
      return '';
    }
    
    // Production URL
    return 'https://api.weedgo.com';
  }
  
  /**
   * Resolve tenant from environment or build configuration
   */
  private resolveTenantFromEnvironment(): void {
    // Check for Vite environment variables
    if (import.meta.env.VITE_TENANT_ID) {
      this.tenantInfo = {
        tenantId: import.meta.env.VITE_TENANT_ID,
        tenantCode: import.meta.env.VITE_TENANT_CODE || 'default',
        templateId: import.meta.env.VITE_TEMPLATE_ID || 'modern-minimal'
      };
      return;
    }
    
    // Check for build-time configuration
    if (typeof __TENANT_CONFIG__ !== 'undefined') {
      const config = __TENANT_CONFIG__ as any;
      this.tenantInfo = {
        tenantId: config.tenantId,
        tenantCode: config.tenantCode,
        templateId: config.templateId
      };
      return;
    }
    
    // Fallback to port-based detection for development
    const port = window.location.port;
    this.tenantInfo = this.getTenantByPort(parseInt(port) || 5173);
  }
  
  /**
   * Get tenant configuration by port
   */
  private getTenantByPort(port: number): TenantInfo {
    const portMapping: Record<number, TenantInfo> = {
      5173: { tenantId: '00000000-0000-0000-0000-000000000001', tenantCode: 'default', templateId: 'modern-minimal' },
      5174: { tenantId: '00000000-0000-0000-0000-000000000002', tenantCode: 'pot-palace', templateId: 'pot-palace' },
      5175: { tenantId: '00000000-0000-0000-0000-000000000003', tenantCode: 'dark-tech', templateId: 'dark-tech' },
      5176: { tenantId: '00000000-0000-0000-0000-000000000004', tenantCode: 'rasta-vibes', templateId: 'rasta-vibes' },
      5177: { tenantId: '00000000-0000-0000-0000-000000000005', tenantCode: 'weedgo', templateId: 'weedgo' },
      5178: { tenantId: '00000000-0000-0000-0000-000000000006', tenantCode: 'vintage', templateId: 'vintage' },
      5179: { tenantId: '00000000-0000-0000-0000-000000000007', tenantCode: 'dirty', templateId: 'dirty' },
      5180: { tenantId: '00000000-0000-0000-0000-000000000008', tenantCode: 'metal', templateId: 'metal' }
    };
    
    return portMapping[port] || portMapping[5173];
  }
  
  /**
   * Setup request and response interceptors
   */
  private setupInterceptors(): void {
    // Request interceptor
    this.requestInterceptorId = this.axiosInstance.interceptors.request.use(
      (config) => {
        // Add tenant headers
        if (this.tenantInfo) {
          config.headers['X-Tenant-Id'] = this.tenantInfo.tenantId;
          config.headers['X-Tenant-Code'] = this.tenantInfo.tenantCode;
          config.headers['X-Template-Id'] = this.tenantInfo.templateId;
          
          if (this.tenantInfo.storeId) {
            config.headers['X-Store-Id'] = this.tenantInfo.storeId;
          }
        }
        
        // Add request ID for tracing
        config.headers['X-Request-Id'] = this.generateRequestId();
        
        // Add timestamp
        config.headers['X-Request-Timestamp'] = new Date().toISOString();
        
        // Log request if enabled
        if (this.loggingEnabled) {
          console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, {
            headers: config.headers,
            data: config.data,
            params: config.params
          });
        }
        
        // Record metrics if enabled
        if (this.metricsEnabled) {
          config.metadata = { startTime: Date.now() };
        }
        
        return config;
      },
      (error) => {
        if (this.loggingEnabled) {
          console.error('[API Request Error]', error);
        }
        return Promise.reject(error);
      }
    );
    
    // Response interceptor
    this.responseInterceptorId = this.axiosInstance.interceptors.response.use(
      (response) => {
        // Log response if enabled
        if (this.loggingEnabled) {
          console.log(`[API Response] ${response.config.method?.toUpperCase()} ${response.config.url}`, {
            status: response.status,
            data: response.data
          });
        }
        
        // Record metrics if enabled
        if (this.metricsEnabled && response.config.metadata) {
          const duration = Date.now() - response.config.metadata.startTime;
          this.recordMetric('api_request_duration', duration, {
            method: response.config.method,
            url: response.config.url,
            status: response.status
          });
        }
        
        return response;
      },
      (error: AxiosError<ApiError>) => {
        // Log error if enabled
        if (this.loggingEnabled) {
          console.error(`[API Error] ${error.config?.method?.toUpperCase()} ${error.config?.url}`, {
            status: error.response?.status,
            error: error.response?.data || error.message
          });
        }
        
        // Record error metrics if enabled
        if (this.metricsEnabled && error.config && error.config.metadata) {
          const duration = Date.now() - error.config.metadata.startTime;
          this.recordMetric('api_request_error', duration, {
            method: error.config.method,
            url: error.config.url,
            status: error.response?.status || 0,
            error: error.code
          });
        }
        
        // Enhanced error handling
        return Promise.reject(this.transformError(error));
      }
    );
  }
  
  /**
   * Setup retry logic
   */
  private setupRetryLogic(retryConfig: RetryConfig): void {
    this.axiosInstance.interceptors.response.use(
      undefined,
      async (error: AxiosError) => {
        const config = error.config as any;
        
        // Guard against undefined config
        if (!config) {
          return Promise.reject(error);
        }
        
        // Initialize retry count
        if (!config.__retryCount) {
          config.__retryCount = 0;
        }
        
        // Check if should retry
        const shouldRetry = retryConfig.retryCondition
          ? retryConfig.retryCondition(error)
          : error.response?.status === 503 || error.code === 'ECONNABORTED';
        
        if (config.__retryCount < retryConfig.retries && shouldRetry) {
          config.__retryCount++;
          
          // Exponential backoff
          const delay = retryConfig.retryDelay * Math.pow(2, config.__retryCount - 1);
          
          if (this.loggingEnabled) {
            console.log(`[API Retry] Attempt ${config.__retryCount} after ${delay}ms`);
          }
          
          await new Promise(resolve => setTimeout(resolve, delay));
          
          return this.axiosInstance(config);
        }
        
        return Promise.reject(error);
      }
    );
  }
  
  /**
   * Transform axios error to application error
   */
  private transformError(error: AxiosError<ApiError>): Error {
    if (error.response) {
      // Server responded with error
      const apiError = new Error(
        error.response.data?.message || `Request failed with status ${error.response.status}`
      );
      (apiError as any).status = error.response.status;
      (apiError as any).code = error.response.data?.code;
      (apiError as any).details = error.response.data?.details;
      return apiError;
    } else if (error.request) {
      // Request made but no response
      const networkError = new Error('Network error: No response from server');
      (networkError as any).code = 'NETWORK_ERROR';
      return networkError;
    } else {
      // Request setup error
      return new Error(error.message || 'Request configuration error');
    }
  }
  
  /**
   * Generate unique request ID
   */
  private generateRequestId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
  
  /**
   * Record metric (placeholder for actual metrics implementation)
   */
  private recordMetric(name: string, value: number, tags: Record<string, any>): void {
    // This would integrate with your metrics service
    if (this.loggingEnabled) {
      console.debug(`[Metric] ${name}: ${value}ms`, tags);
    }
  }
  
  /**
   * Update tenant information
   */
  public setTenantInfo(tenantInfo: TenantInfo): void {
    this.tenantInfo = tenantInfo;
  }
  
  /**
   * Update store ID
   */
  public setStoreId(storeId: string): void {
    if (this.tenantInfo) {
      this.tenantInfo.storeId = storeId;
    }
  }
  
  /**
   * Get current tenant info
   */
  public getTenantInfo(): TenantInfo | null {
    return this.tenantInfo;
  }
  
  /**
   * HTTP Methods
   */
  
  public async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.get<T>(url, config);
    return response.data;
  }
  
  public async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.post<T>(url, data, config);
    return response.data;
  }
  
  public async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.put<T>(url, data, config);
    return response.data;
  }
  
  public async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.patch<T>(url, data, config);
    return response.data;
  }
  
  public async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.delete<T>(url, config);
    return response.data;
  }
  
  /**
   * Get axios instance for advanced usage
   */
  public getAxiosInstance(): AxiosInstance {
    return this.axiosInstance;
  }
  
  /**
   * Clean up interceptors
   */
  public cleanup(): void {
    if (this.requestInterceptorId !== null) {
      this.axiosInstance.interceptors.request.eject(this.requestInterceptorId);
    }
    if (this.responseInterceptorId !== null) {
      this.axiosInstance.interceptors.response.eject(this.responseInterceptorId);
    }
  }
}

// Export singleton instance
export const apiClient = ApiClient.getInstance({
  enableLogging: import.meta.env.MODE === 'development',
  enableMetrics: false,
  retryConfig: {
    retries: 3,
    retryDelay: 1000,
    retryCondition: (error) => {
      // Retry on network errors and 5xx errors
      return !error.response || (error.response.status >= 500 && error.response.status < 600);
    }
  }
});

// Export class for testing
export { ApiClient };

// Export types
export type { TenantInfo, ApiError, ApiClientConfig };