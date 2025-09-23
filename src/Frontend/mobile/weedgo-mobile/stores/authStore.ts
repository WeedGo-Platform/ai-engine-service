import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { authService } from '@/services/api/auth';

interface User {
  id: string;
  phone: string;
  email?: string;
  firstName?: string;
  lastName?: string;
  profileId: string;
  first_name?: string;  // API compatibility
  last_name?: string;   // API compatibility
  profile_image?: string;
}

interface AuthResponse {
  sessionId?: string;
  requiresOtp?: boolean;
  requiresPassword?: boolean;
  success?: boolean;
  access_token?: string;
  refresh_token?: string;
  user?: User;
}

interface CheckPhoneResponse {
  exists: boolean;
  requiresPassword?: boolean;
}

interface AuthState {
  // State
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  biometricEnabled: boolean;

  // Actions
  setUser: (user: User | null) => void;
  setTokens: (accessToken: string, refreshToken: string) => void;
  checkPhone: (phone: string) => Promise<CheckPhoneResponse>;
  login: (phone: string, password?: string) => Promise<AuthResponse>;
  verifyOTP: (phone: string, otp: string, sessionId: string) => Promise<void>;
  register: (data: { phone: string; email?: string; firstName?: string; lastName?: string; dateOfBirth?: string }) => Promise<AuthResponse>;
  resendOTP: (phone: string, sessionId: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshAccessToken: () => Promise<void>;
  loadStoredAuth: () => Promise<void>;
  clearError: () => void;
  setBiometricEnabled: (enabled: boolean) => void;
  quickAuthenticate: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      biometricEnabled: false,

      // Set user
      setUser: (user) => set({ user, isAuthenticated: !!user }),

      // Set tokens
      setTokens: (accessToken, refreshToken) => {
        set({ accessToken, refreshToken, isAuthenticated: true });
        // Set default auth header
        if (accessToken) {
          // This would be set in your API client
        }
      },

      // Check if phone exists
      checkPhone: async (phone) => {
        try {
          const response = await authService.checkPhone(phone);
          return {
            exists: response.exists,
            requiresPassword: response.requiresOtp === false,
          };
        } catch (error: any) {
          console.error('Check phone error:', error);
          throw error;
        }
      },

      // Login with phone (and optional password)
      login: async (phone, password?) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authService.login({ phone, password });

          // Transform API response to expected format
          const authResponse: AuthResponse = {
            sessionId: response.session_id,
            requiresOtp: response.otp_sent,
            success: response.success,
          };

          set({ isLoading: false });
          return authResponse;
        } catch (error: any) {
          set({
            error: error.message || 'Login failed',
            isLoading: false,
          });
          throw error;
        }
      },

      // Verify OTP
      verifyOTP: async (phone, otp, sessionId) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authService.verifyOTP({
            phone,
            code: otp,
            session_id: sessionId,
          });

          set({
            user: response.user,
            accessToken: response.access_token,
            refreshToken: response.refresh_token,
            isAuthenticated: true,
            isLoading: false,
          });

          // Fetch user profile after successful verification
          if (response.access_token) {
            try {
              const profile = await authService.getProfile();
              set({ user: profile });
            } catch (profileError) {
              console.log('Failed to fetch profile after login:', profileError);
            }
          }
        } catch (error: any) {
          set({
            error: error.message || 'OTP verification failed',
            isLoading: false,
          });
          throw error;
        }
      },

      // Register new user
      register: async (data) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authService.register(data);

          // Transform API response to expected format
          const authResponse: AuthResponse = {
            sessionId: response.session_id || 'temp-session',
            requiresOtp: response.otp_sent,
            success: response.success,
          };

          set({ isLoading: false });
          return authResponse;
        } catch (error: any) {
          set({
            error: error.message || 'Registration failed',
            isLoading: false,
          });
          throw error;
        }
      },

      // Resend OTP
      resendOTP: async (phone, sessionId) => {
        try {
          await authService.resendOTP(phone, sessionId);
        } catch (error: any) {
          set({ error: error.message || 'Failed to resend OTP' });
          throw error;
        }
      },

      // Logout
      logout: async () => {
        try {
          const { accessToken } = get();
          if (accessToken) {
            await authService.logout();
          }
        } catch (error) {
          console.error('Logout error:', error);
        }

        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          error: null,
        });
      },

      // Refresh access token
      refreshAccessToken: async () => {
        const { refreshToken } = get();
        if (!refreshToken) {
          throw new Error('No refresh token');
        }

        try {
          const response = await authService.refreshToken(refreshToken);
          set({
            accessToken: response.access_token,
            refreshToken: response.refresh_token,
          });
        } catch (error: any) {
          // Refresh failed, clear auth
          get().logout();
          throw error;
        }
      },

      // Load stored auth on app start
      loadStoredAuth: async () => {
        set({ isLoading: true });
        try {
          // The persist middleware will automatically load the stored state
          // We just need to validate if the token is still valid
          const { accessToken } = get();
          if (accessToken) {
            // Try to get user profile to validate token
            const user = await authService.getProfile();
            set({ user, isAuthenticated: true });
          }
        } catch (error) {
          // Token invalid, try refresh
          try {
            await get().refreshAccessToken();
            const user = await authService.getProfile();
            set({ user, isAuthenticated: true });
          } catch (refreshError) {
            // Refresh failed, clear auth
            get().logout();
          }
        } finally {
          set({ isLoading: false });
        }
      },

      // Clear error
      clearError: () => set({ error: null }),

      // Set biometric enabled
      setBiometricEnabled: (enabled) => set({ biometricEnabled: enabled }),

      // Quick authenticate with biometrics
      quickAuthenticate: async () => {
        const { user, accessToken } = get();
        if (user && accessToken) {
          set({ isAuthenticated: true });
        } else {
          throw new Error('No stored authentication');
        }
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        biometricEnabled: state.biometricEnabled,
      }),
    }
  )
);