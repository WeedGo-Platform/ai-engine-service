import { apiClient } from './client';

export interface DeliveryAddress {
  id?: string;
  name?: string; // Custom name like "Home", "Work"
  street: string;
  city: string;
  province: string;
  postal_code: string;
  unit?: string;
  instructions?: string;
  is_default?: boolean;
  type?: 'home' | 'work' | 'other';
}

class AddressService {
  /**
   * Get user's saved addresses
   */
  async getAddresses(): Promise<DeliveryAddress[]> {
    try {
      const response = await apiClient.get('/api/v1/auth/customer/addresses');
      return response.data || [];
    } catch (error: any) {
      // If 404 or 401, return empty array (no addresses yet or not authenticated)
      if (error.statusCode === 404 || error.response?.status === 404 ||
          error.statusCode === 401 || error.status === 401) {
        return [];
      }
      console.error('Failed to fetch addresses:', error);
      throw error;
    }
  }

  /**
   * Add a new delivery address
   */
  async addAddress(address: DeliveryAddress): Promise<DeliveryAddress> {
    try {
      const response = await apiClient.post('/api/v1/auth/customer/addresses', address);
      return response.data;
    } catch (error) {
      console.error('Failed to add address:', error);
      throw error;
    }
  }

  /**
   * Update an existing delivery address
   */
  async updateAddress(addressId: string, updates: Partial<DeliveryAddress>): Promise<DeliveryAddress> {
    try {
      const response = await apiClient.put(`/api/v1/auth/customer/addresses/${addressId}`, updates);
      return response.data;
    } catch (error) {
      console.error('Failed to update address:', error);
      throw error;
    }
  }

  /**
   * Delete a delivery address
   */
  async deleteAddress(addressId: string): Promise<void> {
    try {
      await apiClient.delete(`/api/v1/auth/customer/addresses/${addressId}`);
    } catch (error) {
      console.error('Failed to delete address:', error);
      throw error;
    }
  }

  /**
   * Set an address as default
   */
  async setDefaultAddress(addressId: string): Promise<void> {
    try {
      await apiClient.put(`/api/v1/auth/customer/addresses/${addressId}/default`);
    } catch (error) {
      console.error('Failed to set default address:', error);
      throw error;
    }
  }
}

export const addressService = new AddressService();