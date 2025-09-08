import axios, { AxiosInstance } from 'axios';

// Create axios instance with default config
const axiosInstance: AxiosInstance = axios.create({
  baseURL: 'http://localhost:5024/api',
  timeout: 30000,
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
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
axiosInstance.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API service object
export const api = {
  // Products
  products: {
    search: (query: string) => axiosInstance.get('/search/products', { params: { q: query } }),
    getAll: (params?: any) => axiosInstance.get('/search/products', { params }),
    getById: (id: string) => axiosInstance.get(`/search/products`, { params: { id } }),
    create: (data: any) => axiosInstance.post('/search/products', data),
    update: (id: string, data: any) => axiosInstance.put(`/search/products/${id}`, data),
    delete: (id: string) => axiosInstance.delete(`/search/products/${id}`),
  },

  // Inventory
  inventory: {
    getAll: (params?: any) => axiosInstance.get('/inventory/search', { params }),
    getStatus: (sku: string) => axiosInstance.get(`/inventory/status/${sku}`),
    update: (data: any) => axiosInstance.post('/inventory/update', data),
    getLowStock: () => axiosInstance.get('/inventory/low-stock'),
    getValueReport: () => axiosInstance.get('/inventory/value-report'),
    search: (params?: any) => axiosInstance.get('/inventory/search', { params }),
    getSuppliers: () => axiosInstance.get('/inventory/suppliers'),
  },

  // Orders
  orders: {
    getAll: (params?: any) => axiosInstance.get('/orders/', { params }),
    getById: (id: string) => axiosInstance.get(`/orders/${id}`),
    getByNumber: (orderNumber: string) => axiosInstance.get(`/orders/by-number/${orderNumber}`),
    create: (data: any) => axiosInstance.post('/orders/create', data),
    updateStatus: (id: string, status: string) => 
      axiosInstance.put(`/orders/${id}/status`, { status }),
    cancel: (id: string) => axiosInstance.post(`/orders/${id}/cancel`),
    getHistory: (id: string) => axiosInstance.get(`/orders/${id}/history`),
    getSummary: () => axiosInstance.get('/orders/analytics/summary'),
  },

  // Customers
  customers: {
    getAll: (params?: any) => axiosInstance.get('/customers', { params }),
    getById: (id: string) => axiosInstance.get(`/customers/${id}`),
    create: (data: any) => axiosInstance.post('/customers', data),
    update: (id: string, data: any) => axiosInstance.put(`/customers/${id}`, data),
    delete: (id: string) => axiosInstance.delete(`/customers/${id}`),
    getOrders: (id: string) => axiosInstance.get(`/customers/${id}/orders`),
    updateLoyaltyPoints: (id: string, points: number) =>
      axiosInstance.patch(`/customers/${id}/loyalty`, { points }),
  },

  // Suppliers
  suppliers: {
    getAll: (params?: any) => axiosInstance.get('/inventory/suppliers', { params }),
    getById: (id: string) => axiosInstance.get(`/suppliers/${id}`),
    create: (data: any) => axiosInstance.post('/suppliers', data),
    update: (id: string, data: any) => axiosInstance.put(`/suppliers/${id}`, data),
    delete: (id: string) => axiosInstance.delete(`/suppliers/${id}`),
  },

  // Purchase Orders
  purchaseOrders: {
    getAll: (params?: any) => axiosInstance.get('/inventory/purchase-orders', { params }),
    getById: (id: string) => axiosInstance.get(`/inventory/purchase-orders`, { params: { po_id: id } }),
    create: (data: any) => axiosInstance.post('/inventory/purchase-orders', data),
    update: (id: string, data: any) => axiosInstance.put(`/inventory/purchase-orders`, { ...data, po_id: id }),
    receive: (id: string, items: any[]) =>
      axiosInstance.post(`/inventory/purchase-orders/${id}/receive`, { items }),
  },

  // Cart
  cart: {
    get: () => axiosInstance.get('/cart/'),
    addItem: (productId: string, quantity: number) =>
      axiosInstance.post('/cart/items', { product_id: productId, quantity }),
    updateItem: (itemId: string, quantity: number) =>
      axiosInstance.put(`/cart/items/${itemId}`, { quantity }),
    removeItem: (itemId: string) =>
      axiosInstance.delete(`/cart/items/${itemId}`),
    clear: () => axiosInstance.delete('/cart/'),
    applyDiscount: (code: string) => axiosInstance.post('/cart/discount', { code }),
    setDeliveryAddress: (address: any) => axiosInstance.post('/cart/delivery-address', address),
    validate: () => axiosInstance.post('/cart/validate'),
    merge: (sessionId: string) => axiosInstance.post('/cart/merge', { session_id: sessionId }),
  },

  // Analytics
  analytics: {
    getDashboardStats: () => axiosInstance.get('/admin/dashboard/stats'),
    getStats: () => axiosInstance.get('/admin/stats'),
    getMetrics: () => axiosInstance.get('/admin/metrics'),
    getApiAnalytics: () => axiosInstance.get('/admin/api/analytics'),
    getOrderSummary: () => axiosInstance.get('/orders/analytics/summary'),
    getInventoryReport: () => axiosInstance.get('/inventory/value-report'),
    getSessions: () => axiosInstance.get('/admin/sessions'),
  },

  // Admin
  admin: {
    login: (credentials: { email: string; password: string }) =>
      axiosInstance.post('/auth/login', credentials),
    logout: () => axiosInstance.post('/auth/logout'),
    getProfile: () => axiosInstance.get('/auth/me'),
    register: (data: any) => axiosInstance.post('/auth/register', data),
    verify: () => axiosInstance.get('/auth/verify'),
    getSystemHealth: () => axiosInstance.get('/admin/system/health'),
    getModels: () => axiosInstance.get('/admin/models'),
    getAgents: () => axiosInstance.get('/admin/agents'),
    getTools: () => axiosInstance.get('/admin/tools'),
    testTool: (data: any) => axiosInstance.post('/admin/tools/test', data),
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
  },
};

export default axiosInstance;