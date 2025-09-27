import { apiClient } from './client';

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

class TenantService {
  /**
   * Get tenant settings by ID
   */
  async getTenantSettings(tenantId?: string): Promise<TenantSettings | null> {
    const id = tenantId || process.env.EXPO_PUBLIC_TENANT_ID;
    if (!id) {
      console.error('No tenant ID configured');
      return null;
    }

    try {
      const response = await apiClient.get<TenantSettings>(`/api/tenants/${id}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch tenant settings:', error);
      return null;
    }
  }

  /**
   * Get tenant by store code (alternative method)
   */
  async getTenantByStoreCode(storeCode: string): Promise<TenantSettings | null> {
    try {
      const response = await apiClient.get<TenantSettings>(`/api/tenants/by-store-code/${storeCode}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch tenant by store code:', error);
      return null;
    }
  }
}

// Export singleton instance
export const tenantService = new TenantService();