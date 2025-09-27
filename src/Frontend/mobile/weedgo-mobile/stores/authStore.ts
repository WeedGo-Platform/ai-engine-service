import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { authService } from '@/services/api/auth';
import { apiClient } from '@/services/api/client';
import { biometricAuthService } from '@/services/biometricAuth';

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
  biometricAvailable: boolean;
  biometricType: string;

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

  // Biometric methods
  checkBiometricAvailability: () => Promise<void>;
  loginWithBiometric: () => Promise<AuthResponse | null>;
  enableBiometric: (email: string, password: string) => Promise<boolean>;
  disableBiometric: () => Promise<boolean>;
  getSavedBiometricEmail: () => Promise<string | null>;
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
      biometricAvailable: false,
      biometricType: 'Biometric',

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

      // Login with email/phone (and optional password)
      login: async (identifier, password?) => {
        set({ isLoading: true, error: null });
        try {
          console.log('Login attempt with identifier:', identifier);
          // Determine if identifier is email or phone
          const isEmail = identifier.includes('@');
          const loginData = isEmail
            ? { email: identifier, password: password || '' }
            : { email: identifier, password: password || '' }; // API expects email field

          console.log('Login data being sent:', loginData);
          const response = await authService.login(loginData);
          console.log('Login API response:', response);

          // Save tokens and user data (handle both field name formats)
          const accessToken = response.access_token || response.access;
          const refreshToken = response.refresh_token || response.refresh || '';

          if (response && accessToken) {
            console.log('Setting user data and tokens');
            set({
              user: response.user,
              accessToken: accessToken,
              refreshToken: refreshToken,
              isAuthenticated: true,
              isLoading: false,
            });

            // Save tokens to API client
            await apiClient.saveTokens(accessToken, refreshToken);
          } else {
            throw new Error('Invalid response from login API');
          }

          // Return success response
          const authResponse: AuthResponse = {
            sessionId: '',
            requiresOtp: false,
            success: true,
          };

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

          // Save tokens and user data
          set({
            user: response.user,
            accessToken: response.access_token,
            isAuthenticated: true,
            isLoading: false,
          });

          // Save tokens to API client
          if (response.access_token) {
            await apiClient.saveTokens(response.access_token, '');
          }

          // Return success response
          const authResponse: AuthResponse = {
            sessionId: '',
            requiresOtp: false,
            success: true,
          };

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

        // Clear biometric data on logout
        await biometricAuthService.clearBiometricData();

        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          error: null,
          biometricEnabled: false,
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

      // Check biometric availability
      checkBiometricAvailability: async () => {
        try {
          const isAvailable = await biometricAuthService.isAvailable();
          const biometricType = await biometricAuthService.getBiometricTypeName();
          const isEnabled = await biometricAuthService.isBiometricEnabled();

          set({
            biometricAvailable: isAvailable,
            biometricType,
            biometricEnabled: isEnabled,
          });
        } catch (error) {
          console.error('Error checking biometric availability:', error);
          set({
            biometricAvailable: false,
            biometricEnabled: false,
          });
        }
      },

      // Login with biometric
      loginWithBiometric: async () => {
        set({ isLoading: true, error: null });
        try {
          // Get stored credentials using biometric authentication
          const credentials = await biometricAuthService.getCredentials();

          if (!credentials) {
            set({ isLoading: false });
            return null;
          }

          // Use the credentials to login
          const response = await authService.login({
            email: credentials.email,
            password: credentials.password,
          });

          // Save tokens and user data
          if (response && response.access_token) {
            set({
              user: response.user,
              accessToken: response.access_token,
              refreshToken: response.refresh_token || '',
              isAuthenticated: true,
              isLoading: false,
            });

            // Save tokens to API client
            await apiClient.saveTokens(response.access_token, response.refresh_token || '');

            return {
              sessionId: '',
              requiresOtp: false,
              success: true,
            };
          }

          throw new Error('Invalid response from login API');
        } catch (error: any) {
          set({
            error: error.message || 'Biometric login failed',
            isLoading: false,
          });
          return null;
        }
      },

      // Enable biometric authentication
      enableBiometric: async (email: string, password: string) => {
        try {
          const success = await biometricAuthService.enableBiometric({ email, password });
          if (success) {
            set({ biometricEnabled: true });
          }
          return success;
        } catch (error: any) {
          set({ error: error.message || 'Failed to enable biometric' });
          return false;
        }
      },

      // Disable biometric authentication
      disableBiometric: async () => {
        try {
          const success = await biometricAuthService.disableBiometric();
          if (success) {
            set({ biometricEnabled: false });
          }
          return success;
        } catch (error: any) {
          set({ error: error.message || 'Failed to disable biometric' });
          return false;
        }
      },

      // Get saved biometric email
      getSavedBiometricEmail: async () => {
        return await biometricAuthService.getSavedEmail();
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
        // Don't persist isAuthenticated - it should be derived from tokens
      }),
      onRehydrateStorage: () => (state) => {
        // After rehydration, set isAuthenticated based on token presence
        if (state) {
          state.isAuthenticated = !!(state.accessToken && state.user);
        }
      },
    }
  )
);