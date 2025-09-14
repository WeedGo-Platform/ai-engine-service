import axios from 'axios';
import { appConfig } from '../config/app.config';
import { getAuthStorage, getStorageKey } from '../config/auth.config';

const API_BASE_URL = appConfig.api.baseUrl;

export interface Address {
  street: string;
  city: string;
  province: string;
  postal_code: string;
  country: string;
}

export interface Store {
  id: string;
  tenant_id: string;
  tenant_code?: string;
  province_territory_id: string;
  store_code: string;
  name: string;
  address?: Address;
  phone?: string;
  email?: string;
  hours: Record<string, any>;
  timezone: string;
  license_number?: string;
  license_expiry?: string;
  tax_rate: number;
  delivery_radius_km: number;
  delivery_enabled: boolean;
  pickup_enabled: boolean;
  kiosk_enabled: boolean;
  pos_enabled: boolean;
  ecommerce_enabled: boolean;
  status: string;
  settings: Record<string, any>;
  pos_integration: Record<string, any>;
  seo_config: Record<string, any>;
  location?: { latitude: number; longitude: number };
  created_at: string;
  updated_at: string;
}

class StoreService {
  private getAuthHeaders() {
    const storage = getAuthStorage();
    const token = storage.getItem(getStorageKey('access_token'));
    return {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    };
  }

  async getStoreById(id: string): Promise<Store> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/stores/${id}`,
        this.getAuthHeaders()
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching store:', error);
      throw error;
    }
  }

  async getStoreByCode(code: string): Promise<Store> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/stores/by-code/${code}`,
        this.getAuthHeaders()
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching store by code:', error);
      throw error;
    }
  }

  async getStoresByTenant(tenantId: string): Promise<Store[]> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/stores/tenant/${tenantId}`,
        this.getAuthHeaders()
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching stores:', error);
      throw error;
    }
  }

  async updateStore(id: string, data: Partial<Store>): Promise<Store> {
    try {
      const response = await axios.put(
        `${API_BASE_URL}/api/stores/${id}`,
        data,
        this.getAuthHeaders()
      );
      return response.data;
    } catch (error) {
      console.error('Error updating store:', error);
      throw error;
    }
  }
}

export default new StoreService();