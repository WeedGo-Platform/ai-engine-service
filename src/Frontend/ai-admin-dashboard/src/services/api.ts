import axios, { AxiosInstance } from 'axios';
import { appConfig, getApiEndpoint } from '../config/app.config';

/**
 * Enhanced error interface for better error handling
 * Extends standard axios errors with additional context
 */
export interface ApiError extends Error {
  code?: string;
  statusCode?: number;
  details?: any;
  isNetworkError?: boolean;
  isAuthError?: boolean;
  isValidationError?: boolean;
  originalError?: any;
}

// Create axios instance with default config
const axiosInstance: AxiosInstance = axios.create({
  baseURL: appConfig.api.baseUrl, // Use base URL directly without /api prefix
  timeout: appConfig.api.timeout,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
axiosInstance.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add store ID header if available
    const storeId = localStorage.getItem('X-Store-ID');
    if (storeId) {
      config.headers['X-Store-ID'] = storeId;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor with enhanced error handling
axiosInstance.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Create enhanced error object
    const apiError: ApiError = new Error(error.message || 'An error occurred') as ApiError;
    apiError.originalError = error;

    if (error.response) {
      // Server responded with error status
      apiError.statusCode = error.response.status;
      apiError.code = error.response.data?.code || error.response.data?.error;
      apiError.details = error.response.data?.details;
      apiError.message = error.response.data?.message || error.message || 'An error occurred';

      // Flag specific error types for easier handling
      apiError.isAuthError = error.response.status === 401 || error.response.status === 403;
      apiError.isValidationError = error.response.status === 422 || error.response.status === 400;
      apiError.isNetworkError = false;

      // Handle unauthorized access - clear auth and redirect to login
      if (error.response.status === 401) {
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');

        // Only redirect if not already on login page
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }
    } else if (error.request) {
      // Request made but no response (network error)
      apiError.code = 'NETWORK_ERROR';
      apiError.isNetworkError = true;
      apiError.isAuthError = false;
      apiError.isValidationError = false;
      apiError.statusCode = 0;
      apiError.message = 'Network error occurred';
    } else {
      // Something else happened (programming error, etc.)
      apiError.code = 'UNKNOWN_ERROR';
      apiError.isNetworkError = false;
      apiError.isAuthError = false;
      apiError.isValidationError = false;
    }

    return Promise.reject(apiError);
  }
);

// API service object
export const api = {
  // Products
  products: {
    search: (query: string) => axiosInstance.get('/api/v2/products/search', { params: { q: query } }),
    getAll: (params?: any) => axiosInstance.get('/api/v2/products/search', { params }),
    getById: (id: string) => axiosInstance.get(`/api/v2/products/${id}`),
    create: (data: any) => axiosInstance.post('/api/v2/products', data),
    update: (id: string, data: any) => axiosInstance.put(`/api/v2/products/${id}`, data),
    delete: (id: string) => axiosInstance.delete(`/api/v2/products/${id}`),
  },

  // Inventory
  inventory: {
    getAll: (params?: any) => axiosInstance.get('/api/v2/inventory/search', { params }),
    getStatus: (sku: string) => axiosInstance.get(`/api/v2/inventory/sku/${sku}`),
    update: (data: any) => axiosInstance.post('/api/v2/inventory/adjust', data),
    delete: (id: string) => axiosInstance.delete(`/api/v2/inventory/${id}`),
    getLowStock: () => axiosInstance.get('/api/v2/inventory/low-stock'),
    getValueReport: () => axiosInstance.get('/api/v2/inventory/value-report'),
    search: (params?: any) => axiosInstance.get('/api/v2/inventory/search', { params }),
    getSuppliers: () => axiosInstance.get('/api/suppliers'), // V1 - preserved until V2 implementation
    checkExists: (sku: string, batchLot?: string) =>
      axiosInstance.get('/api/v2/inventory/check', { params: { sku, batch_lot: batchLot } }),
  },

  // Orders
  orders: {
    getAll: (params?: any) => axiosInstance.get('/api/v2/orders', { params }),
    getById: (id: string) => axiosInstance.get(`/api/v2/orders/${id}`),
    getByNumber: (orderNumber: string) => axiosInstance.get(`/api/v2/orders/by-number/${orderNumber}`),
    create: (data: any) => axiosInstance.post('/api/v2/orders', data),
    updateStatus: (id: string, data: { payment_status?: string; delivery_status?: string; notes?: string }) =>
      axiosInstance.put(`/api/v2/orders/${id}/status`, data),
    cancel: (id: string, reason: string) => axiosInstance.post(`/api/v2/orders/${id}/cancel`, { reason }),
    getHistory: (id: string) => axiosInstance.get(`/api/v2/orders/${id}/history`),
    getSummary: () => axiosInstance.get('/api/v2/orders/analytics/summary'),
  },

  // Customers
  customers: {
    getAll: (params?: any) => {
      // Use search endpoint with empty query to get all customers
      const searchQuery = params?.search || '';
      return axiosInstance.get('/api/v2/identity-access/customers/search', {
        params: {
          q: searchQuery,
          ...(params?.customer_type && { customer_type: params.customer_type })
        }
      });
    },
    getById: (id: string) => axiosInstance.get(`/api/v2/identity-access/customers/${id}`),
    create: (data: any) => axiosInstance.post('/api/v2/identity-access/customers', data),
    update: (id: string, data: any) => axiosInstance.put(`/api/v2/identity-access/customers/${id}`, data),
    delete: (id: string) => axiosInstance.delete(`/api/v2/identity-access/customers/${id}`),
    getOrders: (id: string) => axiosInstance.get(`/api/v2/orders/customer/${id}`),
    updateLoyaltyPoints: (id: string, points: number) =>
      axiosInstance.patch(`/api/v2/identity-access/customers/${id}/loyalty`, { points }),
  },

  // Suppliers (V1 - preserved until V2 implementation)
  suppliers: {
    getAll: (params?: any) => axiosInstance.get('/api/suppliers', { params }),
    getById: (id: string) => axiosInstance.get(`/api/suppliers/${id}`),
    create: (data: any) => axiosInstance.post('/api/suppliers', data),
    update: (id: string, data: any) => axiosInstance.put(`/api/suppliers/${id}`, data),
    delete: (id: string) => axiosInstance.delete(`/api/suppliers/${id}`),
  },

  // Purchase Orders
  purchaseOrders: {
    getAll: (params?: any) => axiosInstance.get('/api/v2/purchase-orders', { params }),
    getById: (id: string) => axiosInstance.get(`/api/v2/purchase-orders/${id}`),
    create: (data: any) => axiosInstance.post('/api/v2/purchase-orders', data),
    update: (id: string, data: any) => axiosInstance.put(`/api/v2/purchase-orders/${id}`, data),
    receive: (id: string, items: any[]) =>
      axiosInstance.post(`/api/v2/purchase-orders/${id}/receive`, { items }),
  },

  // Cart
  cart: {
    get: () => axiosInstance.get('/api/v2/orders/cart'),
    addItem: (productId: string, quantity: number) =>
      axiosInstance.post('/api/v2/orders/cart/items', { product_id: productId, quantity }),
    updateItem: (itemId: string, quantity: number) =>
      axiosInstance.put(`/api/v2/orders/cart/items/${itemId}`, { quantity }),
    removeItem: (itemId: string) =>
      axiosInstance.delete(`/api/v2/orders/cart/items/${itemId}`),
    clear: () => axiosInstance.delete('/api/v2/orders/cart'),
    applyDiscount: (code: string) => axiosInstance.post('/api/v2/pricing-promotions/apply', { code }),
    setDeliveryAddress: (address: any) => axiosInstance.post('/api/v2/orders/cart/delivery-address', address),
    validate: () => axiosInstance.post('/api/v2/orders/cart/validate'),
    merge: (sessionId: string) => axiosInstance.post('/api/v2/orders/cart/merge', { session_id: sessionId }),
  },

  // Analytics
  analytics: {
    getDashboardStats: () => axiosInstance.get('/admin/dashboard/stats'), // Preserved - no v2 yet
    getStats: () => axiosInstance.get('/admin/stats'), // Preserved - no v2 yet
    getMetrics: () => axiosInstance.get('/admin/metrics'), // Preserved - no v2 yet
    getApiAnalytics: () => axiosInstance.get('/admin/api/analytics'), // Preserved - no v2 yet
    getOrderSummary: () => axiosInstance.get('/api/v2/orders/analytics/summary'),
    getInventoryReport: () => axiosInstance.get('/api/v2/inventory/value-report'),
    getSessions: () => axiosInstance.get('/admin/sessions'), // Preserved - no v2 yet
  },

  // Admin
  admin: {
    login: (credentials: { email: string; password: string }) =>
      axiosInstance.post('/api/v2/identity-access/auth/login', credentials),
    logout: () => axiosInstance.post('/api/v2/identity-access/auth/logout'),
    getProfile: () => axiosInstance.get('/api/v2/identity-access/users/me'),
    register: (data: any) => axiosInstance.post('/api/v2/identity-access/users', data),
    verify: () => axiosInstance.get('/api/v2/identity-access/auth/validate'),
    getSystemHealth: () => axiosInstance.get('/admin/system/health'), // Preserved - no v2 yet
    getModels: () => axiosInstance.get('/admin/models'), // Preserved - no v2 yet
    getAgents: () => axiosInstance.get('/admin/agents'), // Preserved - no v2 yet
    getTools: () => axiosInstance.get('/admin/tools'), // Preserved - no v2 yet
    testTool: (data: any) => axiosInstance.post('/admin/tools/test', data), // Preserved - no v2 yet
  },

  // Voice/AI
  voice: {
    startSession: () => axiosInstance.post('/voice/session'),
    endSession: (sessionId: string) => axiosInstance.post(`/voice/session/${sessionId}/end`),
    processAudio: (sessionId: string, audioData: Blob) => {
      const formData = new FormData();
      formData.append('audio', audioData);
      return axiosInstance.post(`/voice/session/${sessionId}/process`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    getMessage: (sessionId: string, messageId: string) =>
      axiosInstance.get(`/voice/session/${sessionId}/message/${messageId}`),

    // Voice synthesis (personality-aware)
    synthesize: (data: {
      text: string;
      personality_id: string;
      language?: string;
      speed?: number;
      pitch?: number;
      quality?: string;
    }) => axiosInstance.post('/api/voice-synthesis/synthesize', data, {
      responseType: 'blob', // Expect audio file
    }),

    loadPersonalityVoice: (personalityId: string) =>
      axiosInstance.post(`/api/voice-synthesis/personalities/${personalityId}/voice/load`),

    unloadPersonalityVoice: (personalityId: string) =>
      axiosInstance.delete(`/api/voice-synthesis/personalities/${personalityId}/voice/unload`),

    getProviderStatus: () =>
      axiosInstance.get('/api/voice-synthesis/providers/status'),

    getCacheStats: () =>
      axiosInstance.get('/api/voice-synthesis/cache/stats'),

    clearCache: () =>
      axiosInstance.delete('/api/voice-synthesis/cache/clear'),

    invalidatePersonalityCache: (personalityId: string) =>
      axiosInstance.delete(`/api/voice-synthesis/personalities/${personalityId}/cache`),
  },

  // Store Devices
  devices: {
    getAll: (storeId: string) => axiosInstance.get(`/admin/stores/${storeId}/devices`),
    create: (storeId: string, data: any) => axiosInstance.post(`/admin/stores/${storeId}/devices`, data),
    update: (storeId: string, deviceId: string, data: any) =>
      axiosInstance.put(`/admin/stores/${storeId}/devices/${deviceId}`, data),
    delete: (storeId: string, deviceId: string) =>
      axiosInstance.delete(`/admin/stores/${storeId}/devices/${deviceId}`),
    getPairCode: (storeId: string, deviceId: string) =>
      axiosInstance.get(`/admin/stores/${storeId}/devices/${deviceId}/pair-code`),
  },
};

export default axiosInstance;