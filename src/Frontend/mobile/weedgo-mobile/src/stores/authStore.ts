import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';
import { authService } from '@/services/api/auth';
import { ApiError } from '@/services/api/client';

interface User {
  id: string;
  phone: string;
  email?: string;
  first_name: string;
  last_name: string;
  profile_image?: string;
  created_at: string;
  is_verified: boolean;
  preferences?: {
    notifications_enabled: boolean;
    biometric_enabled: boolean;
    preferred_store_id?: string;
  };
}

interface RegisterData {
  phone: string;
  email?: string;
  first_name: string;
  last_name: string;
  password?: string;
}

interface AuthStore {
  // State
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  sessionId: string | null;
  biometricEnabled: boolean;

  // Actions
  checkPhone: (phone: string) => Promise<{ exists: boolean; requiresPassword: boolean }>;
  register: (data: RegisterData) => Promise<{ sessionId: string }>;
  login: (phone: string, password?: string) => Promise<{ sessionId: string; requiresOtp: boolean }>;
  verifyOTP: (code: string, sessionId: string) => Promise<void>;
  resendOTP: (sessionId: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshAuth: () => Promise<boolean>;
  loadStoredAuth: () => Promise<void>;
  setBiometricEnabled: (enabled: boolean) => Promise<void>;

  // Utility actions
  setLoading: (loading: boolean) => void;
  clearError: () => void;
  error: string | null;
}

const TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_KEY = 'user_data';
const BIOMETRIC_KEY = 'biometric_enabled';

export const useAuthStore = create<AuthStore>((set, get) => ({
  // Initial state
  user: null,
  token: null,
  refreshToken: null,
  isLoading: false,
  isAuthenticated: false,
  sessionId: null,
  biometricEnabled: false,
  error: null,

  // Check if phone exists
  checkPhone: async (phone: string) => {
    try {
      set({ isLoading: true, error: null });
      const response = await authService.checkPhone(phone);
      return response.data;
    } catch (error) {
      const message = error instanceof ApiError ? error.message : 'Failed to check phone';
      set({ error: message });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  // Register new user
  register: async (data: RegisterData) => {
    try {
      set({ isLoading: true, error: null });
      const response = await authService.register(data);
      set({ sessionId: response.data.sessionId });
      return response.data;
    } catch (error) {
      const message = error instanceof ApiError ? error.message : 'Registration failed';
      set({ error: message });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  // Login existing user
  login: async (phone: string, password?: string) => {
    try {
      set({ isLoading: true, error: null });
      const response = await authService.login({ phone, password });

      if (response.data.requiresOtp) {
        set({ sessionId: response.data.sessionId });
        return response.data;
      }

      // Direct login without OTP (if configured)
      if (response.data.token && response.data.user) {
        await storeTokens(response.data.token, response.data.refreshToken);
        await storeUser(response.data.user);
        set({
          user: response.data.user,
          token: response.data.token,
          refreshToken: response.data.refreshToken,
          isAuthenticated: true,
          sessionId: null
        });
      }

      return response.data;
    } catch (error) {
      const message = error instanceof ApiError ? error.message : 'Login failed';
      set({ error: message });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  // Verify OTP
  verifyOTP: async (code: string, sessionId: string) => {
    try {
      set({ isLoading: true, error: null });
      const response = await authService.verifyOTP({ code, sessionId });

      // Store tokens and user data
      await storeTokens(response.data.token, response.data.refreshToken);
      await storeUser(response.data.user);

      set({
        user: response.data.user,
        token: response.data.token,
        refreshToken: response.data.refreshToken,
        isAuthenticated: true,
        sessionId: null
      });
    } catch (error) {
      const message = error instanceof ApiError ? error.message : 'Invalid verification code';
      set({ error: message });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  // Resend OTP
  resendOTP: async (sessionId: string) => {
    try {
      set({ isLoading: true, error: null });
      await authService.resendOTP(sessionId);
    } catch (error) {
      const message = error instanceof ApiError ? error.message : 'Failed to resend code';
      set({ error: message });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  // Logout
  logout: async () => {
    try {
      set({ isLoading: true });

      // Call logout API if token exists
      const token = get().token;
      if (token) {
        try {
          await authService.logout();
        } catch (error) {
          console.log('Logout API error:', error);
          // Continue with local logout even if API fails
        }
      }

      // Clear secure storage
      await clearTokens();
      await clearUser();

      // Reset state
      set({
        user: null,
        token: null,
        refreshToken: null,
        isAuthenticated: false,
        sessionId: null,
        error: null
      });
    } finally {
      set({ isLoading: false });
    }
  },

  // Refresh authentication
  refreshAuth: async () => {
    try {
      const refreshToken = get().refreshToken;
      if (!refreshToken) return false;

      const response = await authService.refreshToken(refreshToken);

      // Update tokens
      await storeTokens(response.data.token, response.data.refreshToken);

      set({
        token: response.data.token,
        refreshToken: response.data.refreshToken
      });

      return true;
    } catch (error) {
      // If refresh fails, logout
      await get().logout();
      return false;
    }
  },

  // Load stored authentication
  loadStoredAuth: async () => {
    try {
      set({ isLoading: true });

      // Load tokens
      const tokens = await getTokens();
      if (!tokens.access || !tokens.refresh) {
        set({ isLoading: false });
        return;
      }

      // Load user data
      const userData = await getUser();
      if (!userData) {
        set({ isLoading: false });
        return;
      }

      // Load biometric preference
      const biometricEnabled = await SecureStore.getItemAsync(BIOMETRIC_KEY);

      // Validate token with API
      try {
        const response = await authService.validateToken(tokens.access);
        if (response.data.valid) {
          set({
            user: userData,
            token: tokens.access,
            refreshToken: tokens.refresh,
            isAuthenticated: true,
            biometricEnabled: biometricEnabled === 'true'
          });
        } else {
          // Try to refresh
          const refreshed = await get().refreshAuth();
          if (!refreshed) {
            await get().logout();
          }
        }
      } catch (error) {
        // Try to refresh on validation error
        const refreshed = await get().refreshAuth();
        if (!refreshed) {
          await get().logout();
        }
      }
    } catch (error) {
      console.error('Error loading stored auth:', error);
    } finally {
      set({ isLoading: false });
    }
  },

  // Set biometric preference
  setBiometricEnabled: async (enabled: boolean) => {
    try {
      await SecureStore.setItemAsync(BIOMETRIC_KEY, enabled ? 'true' : 'false');

      // Update user preferences on server
      const user = get().user;
      if (user) {
        await authService.updatePreferences({
          biometric_enabled: enabled
        });
      }

      set({ biometricEnabled: enabled });
    } catch (error) {
      console.error('Error setting biometric preference:', error);
    }
  },

  // Utility actions
  setLoading: (loading: boolean) => set({ isLoading: loading }),
  clearError: () => set({ error: null })
}));

// Helper functions for secure storage
async function storeTokens(access: string, refresh: string) {
  await SecureStore.setItemAsync(TOKEN_KEY, access);
  await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, refresh);
}

async function getTokens() {
  const access = await SecureStore.getItemAsync(TOKEN_KEY);
  const refresh = await SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
  return { access, refresh };
}

async function clearTokens() {
  await SecureStore.deleteItemAsync(TOKEN_KEY);
  await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
}

async function storeUser(user: User) {
  await SecureStore.setItemAsync(USER_KEY, JSON.stringify(user));
}

async function getUser(): Promise<User | null> {
  try {
    const userData = await SecureStore.getItemAsync(USER_KEY);
    return userData ? JSON.parse(userData) : null;
  } catch (error) {
    console.error('Error parsing user data:', error);
    return null;
  }
}

async function clearUser() {
  await SecureStore.deleteItemAsync(USER_KEY);
}