import { apiClient, ApiResponse } from './client';
import { Order, CreateOrderData } from '@/stores/orderStore';

export const ordersService = {
  // Create a new order
  createOrder: (data: CreateOrderData): Promise<ApiResponse<Order>> => {
    return apiClient.post('/api/v2/orders', data);
  },

  // Get user's orders
  getOrders: (params?: {
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<ApiResponse<{ orders: Order[]; total: number }>> => {
    return apiClient.get('/api/v2/orders', { params });
  },

  // Get specific order
  getOrder: (orderId: string): Promise<ApiResponse<Order>> => {
    return apiClient.get(`/api/v2/orders/${orderId}`);
  },

  // Cancel an order
  cancelOrder: (orderId: string, data: { reason?: string }): Promise<ApiResponse<void>> => {
    return apiClient.post(`/api/v2/orders/${orderId}/cancel`, data);
  },

  // Track order status
  trackOrder: (orderId: string): Promise<ApiResponse<{
    status: string;
    location?: { lat: number; lng: number };
    estimated_time?: string;
    driver?: {
      name: string;
      phone: string;
      photo?: string;
    };
  }>> => {
    return apiClient.get(`/api/v2/delivery/track/${orderId}`);
  },

  // Rate an order
  rateOrder: (orderId: string, data: {
    rating: number;
    comment?: string;
    driver_rating?: number;
  }): Promise<ApiResponse<void>> => {
    return apiClient.post(`/api/v2/customer-engagement/reviews`, data);
  },

  // Get product for reorder
  getProductForReorder: (productId: string): Promise<ApiResponse<any>> => {
    return apiClient.get(`/api/v2/products/${productId}`);
  },

  // Validate order before submission
  validateOrder: (data: Partial<CreateOrderData>): Promise<ApiResponse<{
    valid: boolean;
    issues: string[];
  }>> => {
    return apiClient.post('/api/v2/orders/validate', data);
  },

  // Apply promo code to order
  applyPromoCode: (code: string, subtotal: number): Promise<ApiResponse<{
    valid: boolean;
    discount_amount: number;
    discount_percentage?: number;
    message?: string;
  }>> => {
    return apiClient.post('/api/v2/pricing-promotions/validate', { code, subtotal });
  },

  // Get order receipt
  getReceipt: (orderId: string): Promise<ApiResponse<{
    receipt_url: string;
    receipt_html?: string;
  }>> => {
    return apiClient.get(`/api/v2/orders/${orderId}/receipt`);
  },

  // Report issue with order
  reportIssue: (orderId: string, data: {
    issue_type: 'missing_item' | 'wrong_item' | 'quality' | 'delivery' | 'other';
    description: string;
    photos?: string[];
  }): Promise<ApiResponse<{
    ticket_id: string;
    status: string;
  }>> => {
    return apiClient.post(`/api/v2/orders/${orderId}/issues`, data);
  },
};