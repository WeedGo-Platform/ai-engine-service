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
  template?: string;
}

export const storesApi = {
  // Get all stores for a tenant
  getTenantStores: async (tenantId: string): Promise<Store[]> => {
    try {
      const response = await apiClient.get<Store[]>(`/api/stores/tenant/${tenantId}`);
      const stores = response.data;

      // Temporarily assign templates based on store name for testing
      // TODO: Remove this when backend provides template data
      stores.forEach(store => {
        if (store.name?.toLowerCase().includes('pot palace') ||
            store.store_code?.toLowerCase().includes('pot-palace')) {
          store.template = 'pot-palace';
        } else if (store.name?.toLowerCase().includes('london') ||
                   store.store_code?.toLowerCase().includes('london')) {
          store.template = 'modern';
        } else {
          // Default template
          store.template = 'modern';
        }
      });

      return stores;
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