import { apiClient } from './client';
import { Profile } from '@/types/api.types';

interface UpdateProfileRequest {
  first_name?: string;
  last_name?: string;
  email?: string;
  date_of_birth?: string;
  profile_image?: string;
}

interface UploadProfileImageResponse {
  image_url: string;
  success: boolean;
}

interface VerifyAgeRequest {
  date_of_birth: string;
  verification_method: 'manual' | 'id_scan' | 'government_api';
  document_type?: string;
  document_number?: string;
}

interface VerifyAgeResponse {
  verified: boolean;
  age: number;
  verified_at: string;
  message?: string;
}

class CustomerService {
  /**
   * Get customer profile
   * Gets the current authenticated customer's profile data
   */
  async getProfile(): Promise<Profile> {
    try {
      // First try the customer-specific endpoint
      const response = await apiClient.get<Profile>('/api/v1/auth/customer/profile');
      return response.data;
    } catch (error: any) {
      // If customer profile endpoint doesn't exist, build from user data
      if (error.statusCode === 404 || error.response?.status === 404) {
        // Get user data from auth store as fallback
        const userDataStr = await apiClient.get('/api/v1/auth/me').catch(() => null);
        if (userDataStr && userDataStr.data) {
          const userData = userDataStr.data;
          return {
            id: userData.id || userData.profile_id,
            phone: userData.phone,
            email: userData.email,
            first_name: userData.first_name,
            last_name: userData.last_name,
            date_of_birth: userData.date_of_birth,
            profile_image: userData.profile_image,
            phone_verified: true, // Phone is verified if they logged in
            email_verified: userData.email_verified || false,
            age_verified: userData.age_verified || false,
            preferences: userData.preferences || {},
            medical_info: userData.medical_info || {},
            addresses: [],
            created_at: userData.created_at,
            updated_at: userData.updated_at,
          };
        }
      }
      throw error;
    }
  }

  /**
   * Update customer profile
   */
  async updateProfile(data: UpdateProfileRequest): Promise<Profile> {
    try {
      // Try customer-specific endpoint first
      const response = await apiClient.put<Profile>('/api/v1/auth/customer/profile', data);
      return response.data;
    } catch (error: any) {
      // Fallback to POS endpoint if customer endpoint doesn't exist
      if (error.statusCode === 404 || error.response?.status === 404) {
        // Get current user ID from stored user data
        const { user } = await apiClient.get('/api/v1/auth/me').catch(() => ({ user: null }));
        if (user && user.id) {
          const response = await apiClient.put<Profile>(`/api/v1/pos/customers/${user.id}`, data);
          return response.data;
        }
      }
      throw error;
    }
  }

  /**
   * Upload profile image
   */
  async uploadProfileImage(imageUri: string): Promise<string> {
    try {
      // Create form data
      const formData = new FormData();
      const filename = imageUri.split('/').pop() || 'profile.jpg';
      const match = /\.(\w+)$/.exec(filename);
      const type = match ? `image/${match[1]}` : 'image/jpeg';

      // Append the image
      formData.append('file', {
        uri: imageUri,
        name: filename,
        type,
      } as any);

      // Upload image
      const response = await apiClient.post<UploadProfileImageResponse>(
        '/api/v1/auth/customer/profile/image',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      if (response.data.success && response.data.image_url) {
        // Update profile with new image URL
        await this.updateProfile({ profile_image: response.data.image_url });
        return response.data.image_url;
      }

      throw new Error('Failed to upload image');
    } catch (error: any) {
      // Only log unexpected errors (not 404s for fallback endpoints)
      if (error.statusCode !== 404 && error.response?.status !== 404) {
        console.error('Upload profile image error:', error);
      }

      // Fallback: Save image URL directly if upload endpoint doesn't exist
      if (error.statusCode === 404 || error.response?.status === 404) {
        try {
          // In development, just update with the local URI
          // In production, you'd upload to a cloud service like S3
          await this.updateProfile({ profile_image: imageUri });
          return imageUri;
        } catch (updateError: any) {
          // If update also fails (e.g., not authenticated), just return the URI
          // The UI can still display it locally
          if (updateError.statusCode === 401 || updateError.status === 401) {
            // User not authenticated - store locally only
            return imageUri;
          }
          throw updateError;
        }
      }

      throw error;
    }
  }

  /**
   * Verify customer age
   */
  async verifyAge(data: VerifyAgeRequest): Promise<VerifyAgeResponse> {
    try {
      const response = await apiClient.post<VerifyAgeResponse>(
        '/api/v1/auth/customer/verify-age',
        data
      );
      return response.data;
    } catch (error: any) {
      // Fallback to POS endpoint
      if (error.statusCode === 404 || error.response?.status === 404) {
        const response = await apiClient.post<VerifyAgeResponse>(
          '/api/v1/pos/customers/verify-age',
          data
        );
        return response.data;
      }
      throw error;
    }
  }

  /**
   * Request email verification
   */
  async requestEmailVerification(email: string): Promise<{ success: boolean; message: string }> {
    try {
      const response = await apiClient.post<{ success: boolean; message: string }>(
        '/api/v1/auth/customer/verify-email',
        { email }
      );
      return response.data;
    } catch (error: any) {
      // Only log unexpected errors (not 404s for missing endpoints)
      if (error.statusCode !== 404 && error.response?.status !== 404) {
        console.error('Email verification request failed:', error);
      }
      // For 404, return a fallback response
      if (error.statusCode === 404 || error.response?.status === 404) {
        return {
          success: false,
          message: 'Email verification is not available at this time'
        };
      }
      throw error;
    }
  }

  /**
   * Verify email with code
   */
  async verifyEmailCode(email: string, code: string): Promise<{ verified: boolean }> {
    try {
      const response = await apiClient.post<{ verified: boolean }>(
        '/api/v1/auth/customer/verify-email/confirm',
        { email, code }
      );
      return response.data;
    } catch (error) {
      console.error('Email verification failed:', error);
      throw error;
    }
  }

  /**
   * Update communication preferences
   */
  async updatePreferences(preferences: Record<string, any>): Promise<void> {
    try {
      await apiClient.put('/api/v1/auth/customer/preferences', { preferences });
    } catch (error: any) {
      // Fallback to communication endpoint
      if (error.statusCode === 404 || error.response?.status === 404) {
        const { user } = await apiClient.get('/api/v1/auth/me').catch(() => ({ user: null }));
        if (user && user.id) {
          await apiClient.put(`/api/v1/communication/preferences/${user.id}`, preferences);
        }
      } else {
        throw error;
      }
    }
  }

  /**
   * Delete customer account
   */
  async deleteAccount(reason?: string): Promise<void> {
    try {
      await apiClient.delete('/api/v1/auth/customer/account', {
        data: { reason }
      });
    } catch (error) {
      console.error('Account deletion failed:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const customerService = new CustomerService();