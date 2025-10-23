import apiClient from './client';

// Types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone?: string;
  date_of_birth: string; // Required for age verification
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  email_verified: boolean;
  age_verified: boolean;
  created_at: string;
  preferences?: UserPreferences;
}

export interface UserPreferences {
  language: string;
  notifications_enabled: boolean;
  marketing_enabled: boolean;
  favorite_categories?: string[];
  delivery_address?: DeliveryAddress;
}

export interface DeliveryAddress {
  street: string;
  city: string;
  province: string;
  postal_code: string;
  unit?: string;
  instructions?: string;
}

export interface ResetPasswordRequest {
  email: string;
}

export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}

export interface VerifyEmailRequest {
  token: string;
}

// API Functions
export const authApi = {
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    try {
      const response = await apiClient.post<LoginResponse>('/api/v1/auth/customer/login', data);
      // Store tokens
      if (response.data.access) {
        localStorage.setItem('access_token', response.data.access);
        localStorage.setItem('refresh_token', response.data.refresh);
        // Set auth header for future requests
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${response.data.access}`;
      }
      return response.data;
    } catch (error: any) {
      console.error('Login failed:', error);
      throw new Error(error.response?.data?.detail || error.response?.data?.message || 'Invalid email or password');
    }
  },

  register: async (data: RegisterRequest): Promise<LoginResponse> => {
    try {
      const response = await apiClient.post<LoginResponse>('/api/v1/auth/customer/register', data);
      // Store tokens
      if (response.data.access) {
        localStorage.setItem('access_token', response.data.access);
        localStorage.setItem('refresh_token', response.data.refresh);
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${response.data.access}`;
      }
      return response.data;
    } catch (error: any) {
      console.error('Registration failed:', error);
      throw new Error(error.response?.data?.detail || error.response?.data?.message || 'Registration failed. Please try again.');
    }
  },

  logout: async (): Promise<void> => {
    try {
      await apiClient.post('/api/v1/auth/customer/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear tokens regardless
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      delete apiClient.defaults.headers.common['Authorization'];
    }
  },

  refresh: async (refreshToken: string): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>('/api/auth/refresh', {
      refresh: refreshToken,
    });
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/api/v1/auth/customer/me');
    return response.data;
  },

  updateProfile: async (data: Partial<User>): Promise<User> => {
    const response = await apiClient.put<User>('/api/auth/profile', data);
    return response.data;
  },

  verifyEmail: async (data: VerifyEmailRequest): Promise<void> => {
    await apiClient.post('/api/auth/verify-email', data);
  },

  resetPassword: async (data: ResetPasswordRequest): Promise<void> => {
    await apiClient.post('/api/auth/reset-password', data);
  },

  changePassword: async (data: ChangePasswordRequest): Promise<void> => {
    await apiClient.post('/api/auth/change-password', data);
  },

  verifyAge: async (dateOfBirth: string): Promise<{ verified: boolean }> => {
    const response = await apiClient.post<{ verified: boolean }>('/api/auth/verify-age', {
      date_of_birth: dateOfBirth,
    });
    return response.data;
  },

  checkEmail: async (email: string): Promise<{ available: boolean; message?: string }> => {
    try {
      // Use the existing guest checkout endpoint to check if user exists
      const response = await apiClient.get<{ exists: boolean; requires_login: boolean }>(
        `/api/checkout/check-user/${encodeURIComponent(email)}`
      );

      // Convert the response: if email exists, it's NOT available
      return {
        available: !response.data.exists,
        message: response.data.exists
          ? 'An account with this email already exists. Please sign in instead.'
          : undefined
      };
    } catch (error: any) {
      console.error('Email check failed:', error);
      // Return available: true on error to allow registration to proceed
      // The actual validation will happen server-side during registration
      return { available: true };
    }
  },
};