import { apiClient } from './client';

export interface DeliveryAddress {
  id?: string;
  label?: string; // Custom name like "Home", "Work"
  street: string;
  city: string;
  province: string;
  postal_code: string;
  unit?: string;
  instructions?: string;
  is_default?: boolean;
  type?: 'delivery' | 'billing';
  phone?: string;
}

// Backend address format
interface BackendAddress {
  id?: string;
  address_type: 'delivery' | 'billing';
  is_default: boolean;
  label?: string;
  street_address: string;
  unit_number?: string;
  city: string;
  province_state: string;
  postal_code: string;
  country: string;
  phone_number?: string;
  delivery_instructions?: string;
}

class AddressService {
  /**
   * Convert frontend address format to backend format
   */
  private toBackendFormat(address: Partial<DeliveryAddress>): Partial<BackendAddress> {
    return {
      address_type: address.type || 'delivery',
      is_default: address.is_default || false,
      label: address.label,
      street_address: address.street || '',
      unit_number: address.unit,
      city: address.city || '',
      province_state: address.province || 'ON',
      postal_code: address.postal_code || '',
      country: 'Canada',
      phone_number: address.phone,
      delivery_instructions: address.instructions,
    };
  }

  /**
   * Convert backend address format to frontend format
   */
  private toFrontendFormat(address: BackendAddress): DeliveryAddress {
    return {
      id: address.id,
      label: address.label,
      street: address.street_address,
      unit: address.unit_number,
      city: address.city,
      province: address.province_state,
      postal_code: address.postal_code,
      instructions: address.delivery_instructions,
      is_default: address.is_default,
      type: address.address_type,
      phone: address.phone_number,
    };
  }

  /**
   * Get user's saved addresses
   */
  async getAddresses(): Promise<DeliveryAddress[]> {
    try {
      const response = await apiClient.get<BackendAddress[]>('/api/v1/auth/customer/addresses');
      const addresses = response.data || [];
      return addresses.map(addr => this.toFrontendFormat(addr));
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
  async addAddress(address: Partial<DeliveryAddress>): Promise<DeliveryAddress> {
    try {
      const backendAddress = this.toBackendFormat(address);
      const response = await apiClient.post<{ message: string; address_id: string }>(
        '/api/v1/auth/customer/addresses',
        backendAddress
      );

      // Return the created address with the new ID
      return {
        ...address,
        id: response.data.address_id,
      } as DeliveryAddress;
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
      const backendUpdates = this.toBackendFormat(updates);
      const response = await apiClient.put<{ message: string }>(
        `/api/v1/auth/customer/addresses/${addressId}`,
        backendUpdates
      );

      // Return the updated address
      return {
        id: addressId,
        ...updates,
      } as DeliveryAddress;
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
      await apiClient.put(`/api/v1/auth/customer/addresses/${addressId}/set-default`);
    } catch (error) {
      console.error('Failed to set default address:', error);
      throw error;
    }
  }
}

export const addressService = new AddressService();