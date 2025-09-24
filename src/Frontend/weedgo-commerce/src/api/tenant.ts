import apiClient from './client';

export interface TenantSettings {
  id: string;
  name: string;
  display_name?: string;
  store_code?: string;
  logo_url?: string;
  business_name?: string;
  business_address?: string;
  business_phone?: string;
  business_email?: string;
  theme?: {
    primaryColor?: string;
    secondaryColor?: string;
  };
  settings?: Record<string, any>;
}

export const tenantApi = {
  // Get tenant settings by ID
  getTenantSettings: async (tenantId: string): Promise<TenantSettings | null> => {
    try {
      const response = await apiClient.get<TenantSettings>(`/api/tenants/${tenantId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch tenant settings:', error);
      return null;
    }
  },

  // Get tenant by store code (alternative method)
  getTenantByStoreCode: async (storeCode: string): Promise<TenantSettings | null> => {
    try {
      const response = await apiClient.get<TenantSettings>(`/api/tenants/by-store-code/${storeCode}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch tenant by store code:', error);
      return null;
    }
  }
};