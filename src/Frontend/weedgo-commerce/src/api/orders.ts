import apiClient from './client';

// Types based on actual API
export interface OrderItem {
  product_id: string;
  sku: string;
  name: string;
  price: number;
  quantity: number;
  subtotal: number;
  image_url?: string;
  thc_content?: number;
  cbd_content?: number;
}

export interface DeliveryInfo {
  type: 'delivery' | 'pickup';
  address?: string;
  city?: string;
  province?: string;
  postal_code?: string;
  delivery_instructions?: string;
  scheduled_time?: string;
}

export interface Order {
  id: string;
  order_number: string;
  user_id?: string;
  store_id: string;
  status: 'pending' | 'confirmed' | 'preparing' | 'ready' | 'out_for_delivery' | 'delivered' | 'cancelled';
  items: OrderItem[];
  subtotal: number;
  tax: number;
  delivery_fee: number;
  total: number;
  delivery_info: DeliveryInfo;
  payment_status: 'pending' | 'paid' | 'failed' | 'refunded';
  payment_method?: string;
  created_at: string;
  updated_at: string;
  estimated_delivery?: string;
  tracking_number?: string;
  driver_name?: string;
  driver_phone?: string;
}

export interface CreateOrderRequest {
  store_id: string;
  items: Array<{
    product_id: string;
    quantity: number;
  }>;
  delivery_info: DeliveryInfo;
  payment_method?: string;
  customer_info?: {
    name: string;
    email: string;
    phone: string;
  };
}

export interface OrderHistoryResponse {
  orders: Order[];
  total: number;
  page: number;
  limit: number;
}

// API Functions
export const ordersApi = {
  // Create a new order
  create: async (request: CreateOrderRequest): Promise<Order> => {
    try {
      const response = await apiClient.post<Order>('/api/orders/create', request);
      return response.data;
    } catch (error) {
      console.error('Failed to create order:', error);
      throw error;
    }
  },

  // Get order by ID
  getOrder: async (orderId: string): Promise<Order> => {
    try {
      const response = await apiClient.get<Order>(`/api/orders/${orderId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch order:', error);
      throw error;
    }
  },

  // Get order by order number
  getOrderByNumber: async (orderNumber: string): Promise<Order> => {
    try {
      const response = await apiClient.get<Order>(`/api/orders/by-number/${orderNumber}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch order by number:', error);
      throw error;
    }
  },

  // Get user's order history
  getOrderHistory: async (
    userId?: string,
    limit = 20,
    offset = 0
  ): Promise<OrderHistoryResponse> => {
    try {
      const params = new URLSearchParams({
        limit: String(limit),
        offset: String(offset),
      });

      if (userId) {
        params.append('user_id', userId);
      }

      const response = await apiClient.get<OrderHistoryResponse>(`/api/orders/?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch order history:', error);
      return {
        orders: [],
        total: 0,
        page: 1,
        limit
      };
    }
  },

  // Update order status
  updateOrderStatus: async (
    orderId: string,
    status: Order['status']
  ): Promise<Order> => {
    try {
      const response = await apiClient.put<Order>(`/api/orders/${orderId}/status`, { status });
      return response.data;
    } catch (error) {
      console.error('Failed to update order status:', error);
      throw error;
    }
  },

  // Cancel order
  cancelOrder: async (orderId: string, reason?: string): Promise<Order> => {
    try {
      const response = await apiClient.post<Order>(`/api/orders/${orderId}/cancel`, { reason });
      return response.data;
    } catch (error) {
      console.error('Failed to cancel order:', error);
      throw error;
    }
  },

  // Track order - real-time updates
  trackOrder: async (orderNumber: string): Promise<Order> => {
    try {
      const response = await apiClient.get<Order>(`/api/orders/track/${orderNumber}`);
      return response.data;
    } catch (error) {
      // Fallback to get by number
      return ordersApi.getOrderByNumber(orderNumber);
    }
  },
};