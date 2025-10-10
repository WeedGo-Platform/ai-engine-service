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
  User,
  Profile,
} from '@/types/api.types';

class AuthService {
  /**
   * Check if a phone number exists in the system
   * Used to determine whether to show registration or login flow
   */
  async checkPhone(phone: string): Promise<CheckPhoneResponse> {
    const response = await apiClient.post<CheckPhoneResponse>(
      '/api/v2/identity-access/auth/check-phone',
      { phone } as CheckPhoneRequest
    );
    return response.data;
  }

  /**
   * Register a new customer
   */
  async register(data: RegisterRequest): Promise<RegisterResponse> {
    const response = await apiClient.post<RegisterResponse>(
      '/api/v2/identity-access/users',
      data
    );
    return response.data;
  }

  /**
   * Login an existing customer
   */
  async login(data: { email: string; password: string }): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>(
      '/api/v2/identity-access/auth/login',
      data
    );
    return response.data;
  }

  /**
   * Verify OTP code
   */
  async verifyOTP(data: VerifyOTPRequest): Promise<VerifyOTPResponse> {
    const response = await apiClient.post<VerifyOTPResponse>(
      '/api/v2/identity-access/auth/verify-otp',
      data
    );

    // Save tokens after successful verification (handle both field name formats)
    const accessToken = response.data.access_token || response.data.access;
    const refreshToken = response.data.refresh_token || response.data.refresh;

    if (accessToken && refreshToken) {
      await apiClient.saveTokens(accessToken, refreshToken);
    }

    return response.data;
  }

  /**
   * Resend OTP code
   */
  async resendOTP(phone: string, sessionId: string): Promise<{ success: boolean }> {
    const response = await apiClient.post<{ success: boolean }>(
      '/api/v2/identity-access/auth/resend-otp',
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
      '/api/v2/identity-access/auth/refresh',
      null,
      {
        headers: {
          Authorization: `Bearer ${refreshToken}`,
        },
      }
    );

    // Save new tokens (handle both field name formats)
    const accessToken = response.data.access_token || response.data.access;
    const newRefreshToken = response.data.refresh_token || response.data.refresh;

    if (accessToken && newRefreshToken) {
      await apiClient.saveTokens(accessToken, newRefreshToken);
    }

    return response.data;
  }

  /**
   * Logout the user
   */
  async logout(): Promise<void> {
    try {
      await apiClient.post('/api/v2/identity-access/auth/logout');
    } catch (error) {
      console.error('Logout API call failed:', error);
    }

    // Clear local tokens
    await apiClient.logout();
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
      const response = await apiClient.get('/api/v2/identity-access/auth/validate');
      return response.data.valid === true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get user profile
   * Note: Currently the user data comes from login/register response
   * This method is kept for future use when a dedicated profile endpoint is available
   */
  async getProfile(): Promise<User> {
    // For now, return empty user as profile comes from login
    // This prevents 404 errors until the backend implements the profile endpoint
    throw new Error('Profile endpoint not implemented. User data comes from login response.');
  }

  /**
   * Request password reset
   */
  async requestPasswordReset(data: {
    identifier: string; // email or phone
  }): Promise<{
    success: boolean;
    message: string;
    session_id: string;
  }> {
    const response = await apiClient.post<{
      success: boolean;
      message: string;
      session_id: string;
    }>('/api/v2/identity-access/auth/password-reset', data);
    return response.data;
  }

  /**
   * Verify reset OTP
   */
  async verifyResetOTP(data: {
    session_id: string;
    code: string;
  }): Promise<{
    success: boolean;
    message: string;
  }> {
    const response = await apiClient.post<{
      success: boolean;
      message: string;
    }>('/api/v2/identity-access/auth/verify-reset', data);
    return response.data;
  }

  /**
   * Reset password with new password
   */
  async resetPassword(data: {
    session_id: string;
    new_password: string;
  }): Promise<{
    success: boolean;
    message: string;
  }> {
    const response = await apiClient.post<{
      success: boolean;
      message: string;
    }>('/api/v2/identity-access/auth/reset-password', data);
    return response.data;
  }
}

// Export singleton instance
export const authService = new AuthService();