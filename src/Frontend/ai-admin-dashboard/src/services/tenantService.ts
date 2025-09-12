import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5024';

export interface Address {
  street: string;
  city: string;
  province: string;
  postal_code: string;
  country: string;
}

export interface Tenant {
  id: string;
  name: string;
  code: string;
  company_name?: string;
  business_number?: string;
  gst_hst_number?: string;
  address?: Address;
  contact_email?: string;
  contact_phone?: string;
  website?: string;
  logo_url?: string;
  status: string;
  subscription_tier: string;
  max_stores: number;
  currency: string;
  settings: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Store {
  id: string;
  tenant_id: string;
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

export interface CreateTenantRequest {
  name: string;
  code: string;
  contact_email: string;
  subscription_tier: 'community' | 'basic' | 'small_business' | 'enterprise';
  company_name?: string;
  business_number?: string;
  gst_hst_number?: string;
  address?: Address;
  contact_phone?: string;
  website?: string;
  logo_url?: string;
  settings?: Record<string, any>;
}

export interface CreateStoreRequest {
  tenant_id: string;
  province_code: string;
  store_code: string;
  name: string;
  address: Address;
  phone?: string;
  email?: string;
  hours?: Record<string, any>;
  timezone?: string;
  license_number?: string;
  license_expiry?: string;
  delivery_radius_km?: number;
  delivery_enabled?: boolean;
  pickup_enabled?: boolean;
  kiosk_enabled?: boolean;
  pos_enabled?: boolean;
  ecommerce_enabled?: boolean;
  settings?: Record<string, any>;
  latitude?: number;
  longitude?: number;
}

class TenantService {
  private api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Tenant operations
  async getTenants(params?: {
    status?: string;
    subscription_tier?: string;
    limit?: number;
    offset?: number;
  }): Promise<Tenant[]> {
    const response = await this.api.get('/api/tenants/', { params });
    return response.data;
  }

  async getTenant(id: string): Promise<Tenant> {
    const response = await this.api.get(`/api/tenants/${id}`);
    return response.data;
  }
  
  async getTenantById(id: string): Promise<Tenant> {
    return this.getTenant(id);
  }

  async getTenantByCode(code: string): Promise<Tenant> {
    const response = await this.api.get(`/api/tenants/by-code/${code}`);
    return response.data;
  }

  async createTenant(data: CreateTenantRequest): Promise<Tenant> {
    const response = await this.api.post('/api/tenants/', data);
    return response.data;
  }

  async updateTenant(id: string, data: Partial<CreateTenantRequest>): Promise<Tenant> {
    const response = await this.api.put(`/api/tenants/${id}`, data);
    return response.data;
  }

  async upgradeTenantSubscription(id: string, newTier: string): Promise<Tenant> {
    const response = await this.api.post(`/api/tenants/${id}/upgrade`, {
      new_tier: newTier,
    });
    return response.data;
  }

  async suspendTenant(id: string, reason: string): Promise<Tenant> {
    const response = await this.api.post(`/api/tenants/${id}/suspend`, { reason });
    return response.data;
  }

  async reactivateTenant(id: string): Promise<Tenant> {
    const response = await this.api.post(`/api/tenants/${id}/reactivate`);
    return response.data;
  }

  async canAddStore(tenantId: string): Promise<{ can_add_store: boolean }> {
    const response = await this.api.get(`/api/tenants/${tenantId}/can-add-store`);
    return response.data;
  }

  // Store operations
  async getStores(tenantId: string, params?: {
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<Store[]> {
    const response = await this.api.get(`/api/stores/tenant/${tenantId}`, { params });
    return response.data;
  }

  async getStore(id: string): Promise<Store> {
    const response = await this.api.get(`/api/stores/${id}`);
    return response.data;
  }

  async createStore(data: CreateStoreRequest): Promise<Store> {
    const response = await this.api.post('/api/stores/', data);
    return response.data;
  }

  async updateStore(id: string, data: Partial<CreateStoreRequest>): Promise<Store> {
    const response = await this.api.put(`/api/stores/${id}`, data);
    return response.data;
  }

  async suspendStore(id: string, reason: string): Promise<Store> {
    const response = await this.api.post(`/api/stores/${id}/suspend`, { reason });
    return response.data;
  }

  async reactivateStore(id: string): Promise<Store> {
    const response = await this.api.post(`/api/stores/${id}/reactivate`);
    return response.data;
  }

  async closeStore(id: string): Promise<Store> {
    const response = await this.api.post(`/api/stores/${id}/close`);
    return response.data;
  }

  async validateStoreLicense(id: string): Promise<{ license_valid: boolean }> {
    const response = await this.api.get(`/api/stores/${id}/validate-license`);
    return response.data;
  }
}

export default new TenantService();