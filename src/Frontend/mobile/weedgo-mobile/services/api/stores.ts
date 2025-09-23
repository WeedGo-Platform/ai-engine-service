import { apiClient } from './client';
import { Store, StoreHours } from '@/types/api.types';

class StoreService {
  /**
   * Get all available stores for tenant
   */
  async getStores(): Promise<Store[]> {
    const tenantId = process.env.EXPO_PUBLIC_TENANT_ID;
    if (!tenantId) {
      console.warn('No tenant ID configured');
      return [];
    }
    const response = await apiClient.get<Store[]>(`/api/stores/tenant/${tenantId}`);
    return response.data;
  }

  /**
   * Get specific store details
   */
  async getStoreDetails(storeId: string): Promise<Store> {
    const response = await apiClient.get<Store>(`/api/stores/${storeId}`);
    return response.data;
  }

  /**
   * Get store hours
   */
  async getStoreHours(storeId: string): Promise<StoreHours> {
    const response = await apiClient.get<StoreHours>(`/api/stores/${storeId}/hours`);
    return response.data;
  }

  /**
   * Check store availability
   */
  async checkAvailability(
    storeId: string,
    params: { date?: string; time?: string } = {}
  ): Promise<{
    is_open: boolean;
    next_open_time: string;
    delivery_available: boolean;
    pickup_available: boolean;
  }> {
    const response = await apiClient.get<{
      is_open: boolean;
      next_open_time: string;
      delivery_available: boolean;
      pickup_available: boolean;
    }>(`/api/stores/${storeId}/availability`, { params });

    return response.data;
  }

  /**
   * Get nearest store based on location
   */
  async getNearbyStores(latitude?: number, longitude?: number): Promise<Store[]> {
    try {
      const params: any = {};
      if (latitude && longitude) {
        params.latitude = latitude;
        params.longitude = longitude;
      }
      const response = await apiClient.get<Store[]>('/api/stores/nearby', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to get nearby stores:', error);
      return [];
    }
  }

  async getNearestStore(lat: number, lng: number): Promise<Store> {
    const response = await apiClient.get<Store>('/api/stores/nearest', {
      params: { lat, lng },
    });
    return response.data;
  }

  /**
   * Get stores by postal code
   */
  async getStoresByPostalCode(postalCode: string): Promise<Store[]> {
    const response = await apiClient.get<Store[]>('/api/stores/by-postal', {
      params: { postal_code: postalCode },
    });
    return response.data;
  }

  /**
   * Check delivery availability for address
   */
  async checkDeliveryAvailability(
    storeId: string,
    postalCode: string
  ): Promise<{
    available: boolean;
    fee: number;
    minimum_order: number;
    estimated_time: string;
  }> {
    const response = await apiClient.get<{
      available: boolean;
      fee: number;
      minimum_order: number;
      estimated_time: string;
    }>(`/api/stores/${storeId}/delivery-check`, {
      params: { postal_code: postalCode },
    });

    return response.data;
  }

  /**
   * Get store delivery zones
   */
  async getDeliveryZones(storeId: string): Promise<any[]> {
    const response = await apiClient.get<any[]>(`/api/stores/${storeId}/delivery-zones`);
    return response.data;
  }

  /**
   * Get store promotions
   */
  async getStorePromotions(storeId: string): Promise<any[]> {
    const response = await apiClient.get<any[]>(`/api/stores/${storeId}/promotions`);
    return response.data;
  }

  /**
   * Get store reviews
   */
  async getStoreReviews(
    storeId: string,
    params: { limit?: number; offset?: number } = {}
  ): Promise<{ reviews: any[]; total: number; rating: number }> {
    const response = await apiClient.get<{
      reviews: any[];
      total: number;
      rating: number;
    }>(`/api/stores/${storeId}/reviews`, { params });

    return response.data;
  }

  /**
   * Submit store review
   */
  async submitReview(
    storeId: string,
    data: {
      rating: number;
      comment: string;
      order_id?: string;
    }
  ): Promise<void> {
    await apiClient.post(`/api/stores/${storeId}/reviews`, data);
  }
}

// Export singleton instance
export const storeService = new StoreService();