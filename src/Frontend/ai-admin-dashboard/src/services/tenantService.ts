import { getAuthStorage, getStorageKey } from '../config/auth.config';
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
  crol_number?: string; // Cannabis Retail Operating License number for OCS
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
  province_code?: string;
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
  crol_number?: string; // Cannabis Retail Operating License number for OCS
  address?: Address;
  contact_phone?: string;
  website?: string;
  logo_url?: string;
  settings?: Record<string, any>;
}

export interface CreateStoreRequest {
  tenant_id: string;
  province_code: string;
  store_code?: string;  // Now optional - will be auto-generated if not provided
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

  constructor() {
    // Add request interceptor to include auth token
    this.api.interceptors.request.use(
      (config) => {
        const storage = getAuthStorage();
        const token = storage.getItem(getStorageKey('access_token'));
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );
  }

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

  async checkTenantExists(code?: string, website?: string): Promise<{
    exists: boolean;
    conflicts: Array<{
      type: string;
      value: string;
      existing_tenant: {
        id: string;
        name: string;
        code: string;
        website?: string;
        contact_email?: string;
      }
    }>;
  }> {
    const response = await this.api.post('/api/tenants/check-exists', {
      code,
      website
    });
    return response.data;
  }

  async createTenantWithAdmin(data: CreateTenantRequest): Promise<Tenant> {
    const response = await this.api.post('/api/tenants/signup', data);
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

  // Tenant user management
  async getTenantUsers(tenantId: string): Promise<any[]> {
    const response = await this.api.get(`/api/tenants/${tenantId}/users`);
    return response.data;
  }

  async createTenantUser(tenantId: string, userData: {
    email: string;
    first_name: string;
    last_name: string;
    role: string;
    password?: string;
  }): Promise<any> {
    const response = await this.api.post(`/api/tenants/${tenantId}/users`, userData);
    return response.data;
  }

  async updateTenantUser(tenantId: string, userId: string, userData: any): Promise<any> {
    const response = await this.api.put(`/api/tenants/${tenantId}/users/${userId}`, userData);
    return response.data;
  }

  async deleteTenantUser(tenantId: string, userId: string): Promise<void> {
    await this.api.delete(`/api/tenants/${tenantId}/users/${userId}`);
  }

  // OTP Verification operations
  async sendOTP(identifier: string, identifierType: 'email' | 'phone'): Promise<{
    success: boolean;
    message?: string;
    expiresIn?: number;
  }> {
    try {
      const response = await this.api.post('/api/v1/auth/otp/send', {
        identifier,
        identifier_type: identifierType,
        purpose: 'verification'
      });
      return {
        success: true,
        message: response.data.message,
        expiresIn: response.data.expires_in
      };
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.detail || error.message || 'Failed to send OTP'
      };
    }
  }

  async verifyOTP(identifier: string, identifierType: 'email' | 'phone', code: string): Promise<{
    success: boolean;
    message?: string;
    accessToken?: string;
    user?: any;
  }> {
    try {
      const response = await this.api.post('/api/v1/auth/otp/verify', {
        identifier,
        identifier_type: identifierType,
        code,
        purpose: 'verification'
      });
      return {
        success: true,
        message: response.data.message,
        accessToken: response.data.access_token,
        user: response.data.user
      };
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.detail || error.message || 'Failed to verify OTP'
      };
    }
  }

  async resendOTP(identifier: string, identifierType: 'email' | 'phone'): Promise<{
    success: boolean;
    message?: string;
    expiresIn?: number;
  }> {
    try {
      const response = await this.api.post('/api/v1/auth/otp/resend', {
        identifier,
        identifier_type: identifierType,
        purpose: 'verification'
      });
      return {
        success: true,
        message: response.data.message,
        expiresIn: response.data.expires_in
      };
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.detail || error.message || 'Failed to resend OTP'
      };
    }
  }
}

export default new TenantService();