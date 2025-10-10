import { apiClient, ApiResponse } from './client';
import { DeliveryAddress } from '@/stores/orderStore';

interface DeliveryFeeRequest {
  store_id: string;
  delivery_address: DeliveryAddress;
  order_subtotal?: number;
}

interface DeliveryFeeResponse {
  delivery_fee: number;
  estimated_time: string;
  available: boolean;
  distance?: number;
  minimum_order?: number;
  free_delivery_threshold?: number;
  message?: string;
}

interface DeliveryZone {
  id: string;
  name: string;
  postal_codes: string[];
  fee: number;
  minimum_order: number;
  estimated_time: string;
  available: boolean;
}

interface DeliveryDriver {
  id: string;
  name: string;
  phone: string;
  photo?: string;
  vehicle: {
    make: string;
    model: string;
    color: string;
    license_plate: string;
  };
  rating: number;
  location?: {
    lat: number;
    lng: number;
  };
}

export const deliveryService = {
  // Calculate delivery fee
  calculateFee: (data: DeliveryFeeRequest): Promise<ApiResponse<DeliveryFeeResponse>> => {
    return apiClient.post('/api/v2/delivery/calculate-fee', data);
  },

  // Get delivery zones
  getDeliveryZones: (storeId: string): Promise<ApiResponse<DeliveryZone[]>> => {
    return apiClient.get(`/api/v2/delivery/zones/store/${storeId}`);
  },

  // Check if address is in delivery zone
  checkDeliveryAvailability: (data: {
    store_id: string;
    postal_code: string;
  }): Promise<ApiResponse<{
    available: boolean;
    zone?: string;
    message?: string;
  }>> => {
    return apiClient.post('/api/v2/delivery/zones/check', data);
  },

  // Get estimated delivery time
  getEstimatedTime: (data: {
    store_id: string;
    delivery_address: DeliveryAddress;
    order_size?: 'small' | 'medium' | 'large';
  }): Promise<ApiResponse<{
    estimated_time: string;
    rush_hour: boolean;
    weather_delay: boolean;
  }>> => {
    return apiClient.post('/api/v2/delivery/estimate', data);
  },

  // Track delivery
  trackDelivery: (orderId: string): Promise<ApiResponse<{
    status: 'preparing' | 'ready' | 'picked_up' | 'on_the_way' | 'delivered';
    driver?: DeliveryDriver;
    location?: {
      lat: number;
      lng: number;
    };
    estimated_arrival: string;
    updates: Array<{
      timestamp: string;
      status: string;
      message: string;
    }>;
  }>> => {
    return apiClient.get(`/api/v2/delivery/track/${orderId}`);
  },

  // Get delivery instructions templates
  getInstructionTemplates: (): Promise<ApiResponse<string[]>> => {
    return apiClient.get('/api/v2/delivery/instructions/templates');
  },

  // Report delivery issue
  reportIssue: (orderId: string, data: {
    issue_type: 'not_delivered' | 'wrong_address' | 'damaged' | 'late' | 'other';
    description: string;
    photos?: string[];
  }): Promise<ApiResponse<{
    ticket_id: string;
    status: string;
  }>> => {
    // Note: Need delivery_id, using orderId as placeholder
    return apiClient.post(`/api/v2/delivery/${orderId}/issues`, data);
  },

  // Rate delivery experience
  rateDelivery: (orderId: string, data: {
    rating: number;
    driver_rating?: number;
    comment?: string;
    tips?: {
      on_time: boolean;
      professional: boolean;
      order_condition: boolean;
    };
  }): Promise<ApiResponse<void>> => {
    return apiClient.post(`/api/v2/customer-engagement/reviews`, { ...data, order_id: orderId });
  },

  // Get delivery history
  getDeliveryHistory: (params?: {
    limit?: number;
    offset?: number;
    status?: string;
  }): Promise<ApiResponse<{
    deliveries: Array<{
      order_id: string;
      delivered_at: string;
      driver: string;
      rating?: number;
      delivery_fee: number;
    }>;
    total: number;
  }>> => {
    return apiClient.get('/api/v2/delivery/history', { params });
  },

  // Schedule delivery
  scheduleDelivery: (data: {
    order_id: string;
    scheduled_time: string;
    notes?: string;
  }): Promise<ApiResponse<{
    confirmation_id: string;
    scheduled_time: string;
  }>> => {
    return apiClient.post('/api/v2/delivery/schedule', data);
  },

  // Cancel scheduled delivery
  cancelScheduledDelivery: (confirmationId: string): Promise<ApiResponse<void>> => {
    return apiClient.delete(`/api/v2/delivery/schedule/${confirmationId}`);
  },
};