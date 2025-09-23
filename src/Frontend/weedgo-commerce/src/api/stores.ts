import apiClient from './client';

export interface Store {
  id: string;
  name: string;
  store_code: string;
  address?: string;
  city?: string;
  province?: string;
  postal_code?: string;
  phone?: string;
  email?: string;
  hours?: {
    [key: string]: {
      open: string;
      close: string;
    };
  };
  delivery_available?: boolean;
  pickup_available?: boolean;
  image_url?: string;
}

export const storesApi = {
  // Get all stores for a tenant
  getTenantStores: async (tenantId: string): Promise<Store[]> => {
    try {
      const response = await apiClient.get<Store[]>(`/api/stores/tenant/${tenantId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch stores:', error);
      // Return empty array if API fails
      return [];
    }
  },

  // Get single store details
  getStore: async (storeId: string): Promise<Store | null> => {
    try {
      const response = await apiClient.get<Store>(`/api/stores/${storeId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch store:', error);
      return null;
    }
  },

  // Select a store (sets it as active)
  selectStore: async (storeId: string): Promise<boolean> => {
    try {
      await apiClient.post(`/api/stores/${storeId}/select`);
      localStorage.setItem('selected_store_id', storeId);
      return true;
    } catch (error) {
      console.error('Failed to select store:', error);
      return false;
    }
  }
};