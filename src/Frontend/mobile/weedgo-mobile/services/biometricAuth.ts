import * as LocalAuthentication from 'expo-local-authentication';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

const SECURE_STORE_KEYS = {
  BIOMETRIC_ENABLED: 'biometric_auth_enabled',
  USER_CREDENTIALS: 'biometric_user_credentials',
  USER_EMAIL: 'biometric_user_email',
};

export interface BiometricCredentials {
  email: string;
  password: string;
}

class BiometricAuthService {
  /**
   * Check if device has biometric hardware available
   */
  async isAvailable(): Promise<boolean> {
    try {
      const hasHardware = await LocalAuthentication.hasHardwareAsync();
      const isEnrolled = await LocalAuthentication.isEnrolledAsync();
      return hasHardware && isEnrolled;
    } catch (error) {
      console.error('Error checking biometric availability:', error);
      return false;
    }
  }

  /**
   * Get supported biometric types (Face ID, Touch ID, etc.)
   */
  async getSupportedTypes(): Promise<LocalAuthentication.AuthenticationType[]> {
    try {
      return await LocalAuthentication.supportedAuthenticationTypesAsync();
    } catch (error) {
      console.error('Error getting supported biometric types:', error);
      return [];
    }
  }

  /**
   * Get the biometric type name for display
   */
  async getBiometricTypeName(): Promise<string> {
    const types = await this.getSupportedTypes();

    if (types.includes(LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION)) {
      return Platform.OS === 'ios' ? 'Face ID' : 'Face Recognition';
    }

    if (types.includes(LocalAuthentication.AuthenticationType.FINGERPRINT)) {
      return Platform.OS === 'ios' ? 'Touch ID' : 'Fingerprint';
    }

    if (types.includes(LocalAuthentication.AuthenticationType.IRIS)) {
      return 'Iris Recognition';
    }

    return 'Biometric Authentication';
  }

  /**
   * Authenticate user with biometrics
   */
  async authenticate(reason?: string): Promise<boolean> {
    try {
      const biometricType = await this.getBiometricTypeName();
      const result = await LocalAuthentication.authenticateAsync({
        promptMessage: reason || `Authenticate with ${biometricType}`,
        fallbackLabel: 'Use Passcode',
        cancelLabel: 'Cancel',
        disableDeviceFallback: false,
      });

      return result.success;
    } catch (error) {
      console.error('Biometric authentication error:', error);
      return false;
    }
  }

  /**
   * Save user credentials securely (encrypted)
   */
  async saveCredentials(credentials: BiometricCredentials): Promise<boolean> {
    try {
      // First authenticate to ensure it's the right user
      const authenticated = await this.authenticate('Confirm your identity to enable biometric login');
      if (!authenticated) {
        return false;
      }

      // Save encrypted credentials
      await SecureStore.setItemAsync(
        SECURE_STORE_KEYS.USER_CREDENTIALS,
        JSON.stringify(credentials)
      );

      // Save email separately for display purposes
      await SecureStore.setItemAsync(
        SECURE_STORE_KEYS.USER_EMAIL,
        credentials.email
      );

      // Mark biometric as enabled
      await SecureStore.setItemAsync(
        SECURE_STORE_KEYS.BIOMETRIC_ENABLED,
        'true'
      );

      return true;
    } catch (error) {
      console.error('Error saving credentials:', error);
      return false;
    }
  }

  /**
   * Retrieve saved credentials after biometric authentication
   */
  async getCredentials(): Promise<BiometricCredentials | null> {
    try {
      // First check if biometric is enabled
      const isEnabled = await this.isBiometricEnabled();
      if (!isEnabled) {
        return null;
      }

      // Authenticate user
      const authenticated = await this.authenticate('Authenticate to sign in');
      if (!authenticated) {
        return null;
      }

      // Retrieve encrypted credentials
      const credentialsJson = await SecureStore.getItemAsync(
        SECURE_STORE_KEYS.USER_CREDENTIALS
      );

      if (!credentialsJson) {
        return null;
      }

      return JSON.parse(credentialsJson) as BiometricCredentials;
    } catch (error) {
      console.error('Error retrieving credentials:', error);
      return null;
    }
  }

  /**
   * Get saved email (for display purposes, doesn't require authentication)
   */
  async getSavedEmail(): Promise<string | null> {
    try {
      return await SecureStore.getItemAsync(SECURE_STORE_KEYS.USER_EMAIL);
    } catch (error) {
      console.error('Error getting saved email:', error);
      return null;
    }
  }

  /**
   * Check if biometric login is enabled
   */
  async isBiometricEnabled(): Promise<boolean> {
    try {
      const enabled = await SecureStore.getItemAsync(
        SECURE_STORE_KEYS.BIOMETRIC_ENABLED
      );
      return enabled === 'true';
    } catch (error) {
      console.error('Error checking biometric status:', error);
      return false;
    }
  }

  /**
   * Enable biometric authentication for current user
   */
  async enableBiometric(credentials: BiometricCredentials): Promise<boolean> {
    try {
      // Check if biometric is available
      const isAvailable = await this.isAvailable();
      if (!isAvailable) {
        throw new Error('Biometric authentication is not available on this device');
      }

      // Save credentials securely
      return await this.saveCredentials(credentials);
    } catch (error) {
      console.error('Error enabling biometric:', error);
      throw error;
    }
  }

  /**
   * Disable biometric authentication
   */
  async disableBiometric(): Promise<boolean> {
    try {
      // First authenticate to ensure it's the right user
      const authenticated = await this.authenticate('Confirm your identity to disable biometric login');
      if (!authenticated) {
        return false;
      }

      // Clear all stored data
      await SecureStore.deleteItemAsync(SECURE_STORE_KEYS.USER_CREDENTIALS);
      await SecureStore.deleteItemAsync(SECURE_STORE_KEYS.USER_EMAIL);
      await SecureStore.deleteItemAsync(SECURE_STORE_KEYS.BIOMETRIC_ENABLED);

      return true;
    } catch (error) {
      console.error('Error disabling biometric:', error);
      return false;
    }
  }

  /**
   * Clear all biometric data (used on logout)
   */
  async clearBiometricData(): Promise<void> {
    try {
      await SecureStore.deleteItemAsync(SECURE_STORE_KEYS.USER_CREDENTIALS);
      await SecureStore.deleteItemAsync(SECURE_STORE_KEYS.USER_EMAIL);
      await SecureStore.deleteItemAsync(SECURE_STORE_KEYS.BIOMETRIC_ENABLED);
    } catch (error) {
      console.error('Error clearing biometric data:', error);
    }
  }
}

export const biometricAuthService = new BiometricAuthService();