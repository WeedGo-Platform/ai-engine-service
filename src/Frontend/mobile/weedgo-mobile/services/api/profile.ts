import { apiClient } from './client';
import { Profile, Address } from '@/types/api.types';

class ProfileService {
  /**
   * Get user profile
   */
  async getProfile(): Promise<Profile> {
    const response = await apiClient.get<Profile>('/api/profile');
    return response.data;
  }

  /**
   * Update user profile
   */
  async updateProfile(data: Partial<Profile>): Promise<Profile> {
    const response = await apiClient.put<{ success: boolean; profile: Profile }>(
      '/api/profile/update',
      data
    );
    return response.data.profile;
  }

  /**
   * Get user addresses
   */
  async getAddresses(): Promise<Address[]> {
    const response = await apiClient.get<Address[]>('/api/profile/addresses');
    return response.data;
  }

  /**
   * Add new address
   */
  async addAddress(address: Omit<Address, 'id'>): Promise<string> {
    const response = await apiClient.post<{ success: boolean; address_id: string }>(
      '/api/profile/addresses',
      address
    );
    return response.data.address_id;
  }

  /**
   * Update address
   */
  async updateAddress(addressId: string, data: Partial<Address>): Promise<Address> {
    const response = await apiClient.put<Address>(
      `/api/profile/addresses/${addressId}`,
      data
    );
    return response.data;
  }

  /**
   * Delete address
   */
  async deleteAddress(addressId: string): Promise<void> {
    await apiClient.delete(`/api/profile/addresses/${addressId}`);
  }

  /**
   * Set default address
   */
  async setDefaultAddress(addressId: string, type: 'delivery' | 'billing'): Promise<void> {
    await apiClient.post(`/api/profile/addresses/${addressId}/default`, { type });
  }

  /**
   * Upload medical document
   */
  async uploadMedicalDocument(document: FormData): Promise<{ document_id: string }> {
    const response = await apiClient.post<{ document_id: string }>(
      '/api/profile/medical-documents',
      document,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  }

  /**
   * Get medical documents
   */
  async getMedicalDocuments(): Promise<any[]> {
    const response = await apiClient.get<any[]>('/api/profile/medical-documents');
    return response.data;
  }

  /**
   * Update preferences
   */
  async updatePreferences(preferences: Record<string, any>): Promise<void> {
    await apiClient.put('/api/profile/preferences', { preferences });
  }

  /**
   * Get order history
   */
  async getOrderHistory(params: { limit?: number; offset?: number } = {}): Promise<any[]> {
    const response = await apiClient.get<any[]>('/api/profile/orders', { params });
    return response.data;
  }

  /**
   * Get wishlist
   */
  async getWishlist(): Promise<any[]> {
    const response = await apiClient.get<any[]>('/api/profile/wishlist');
    return response.data;
  }

  /**
   * Add to wishlist
   */
  async addToWishlist(productId: string): Promise<void> {
    await apiClient.post('/api/profile/wishlist', { product_id: productId });
  }

  /**
   * Remove from wishlist
   */
  async removeFromWishlist(productId: string): Promise<void> {
    await apiClient.delete(`/api/profile/wishlist/${productId}`);
  }
}

// Export singleton instance
export const profileService = new ProfileService();