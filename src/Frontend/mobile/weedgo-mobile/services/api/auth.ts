import { apiClient } from './client';
import {
  CheckPhoneRequest,
  CheckPhoneResponse,
  RegisterRequest,
  RegisterResponse,
  LoginRequest,
  LoginResponse,
  VerifyOTPRequest,
  VerifyOTPResponse,
  RefreshTokenResponse,
} from '@/types/api.types';

class AuthService {
  /**
   * Check if a phone number exists in the system
   * Used to determine whether to show registration or login flow
   */
  async checkPhone(phone: string): Promise<CheckPhoneResponse> {
    const response = await apiClient.post<CheckPhoneResponse>(
      '/api/v1/auth/customer/check-phone',
      { phone } as CheckPhoneRequest
    );
    return response.data;
  }

  /**
   * Register a new customer
   */
  async register(data: RegisterRequest): Promise<RegisterResponse> {
    const response = await apiClient.post<RegisterResponse>(
      '/api/v1/auth/customer/register',
      data
    );
    return response.data;
  }

  /**
   * Login an existing customer
   */
  async login(phone: string): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>(
      '/api/v1/auth/customer/login',
      { phone } as LoginRequest
    );
    return response.data;
  }

  /**
   * Verify OTP code
   */
  async verifyOTP(data: VerifyOTPRequest): Promise<VerifyOTPResponse> {
    const response = await apiClient.post<VerifyOTPResponse>(
      '/api/v1/auth/otp/verify',
      data
    );

    // Save tokens after successful verification
    if (response.data.access_token && response.data.refresh_token) {
      await apiClient.saveTokens(
        response.data.access_token,
        response.data.refresh_token
      );
    }

    return response.data;
  }

  /**
   * Resend OTP code
   */
  async resendOTP(phone: string, sessionId: string): Promise<{ success: boolean }> {
    const response = await apiClient.post<{ success: boolean }>(
      '/api/v1/auth/otp/resend',
      { phone, session_id: sessionId }
    );
    return response.data;
  }

  /**
   * Refresh access token
   * Note: This is usually called automatically by the API client interceptor
   */
  async refreshToken(): Promise<RefreshTokenResponse> {
    const { refreshToken } = await apiClient.getTokens();

    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await apiClient.post<RefreshTokenResponse>(
      '/api/v1/auth/refresh',
      null,
      {
        headers: {
          Authorization: `Bearer ${refreshToken}`,
        },
      }
    );

    // Save new tokens
    if (response.data.access_token && response.data.refresh_token) {
      await apiClient.saveTokens(
        response.data.access_token,
        response.data.refresh_token
      );
    }

    return response.data;
  }

  /**
   * Logout the user
   */
  async logout(): Promise<void> {
    try {
      // Call logout endpoint
      await apiClient.post('/api/v1/auth/logout');
    } catch (error) {
      // Log error but don't throw - we still want to clear local tokens
      console.error('Logout API call failed:', error);
    } finally {
      // Clear local tokens regardless
      await apiClient.logout();
    }
  }

  /**
   * Check if user is authenticated
   */
  async isAuthenticated(): Promise<boolean> {
    return apiClient.isAuthenticated();
  }

  /**
   * Validate token with backend
   */
  async validateToken(): Promise<boolean> {
    try {
      const response = await apiClient.get('/api/v1/auth/validate');
      return response.data.valid === true;
    } catch (error) {
      return false;
    }
  }
}

// Export singleton instance
export const authService = new AuthService();