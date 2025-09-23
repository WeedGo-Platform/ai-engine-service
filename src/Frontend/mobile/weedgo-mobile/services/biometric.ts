import * as LocalAuthentication from 'expo-local-authentication';
import AsyncStorage from '@react-native-async-storage/async-storage';

const BIOMETRIC_ENABLED_KEY = 'biometric_auth_enabled';
const BIOMETRIC_TYPE_KEY = 'biometric_type';

export type BiometricType = 'face' | 'fingerprint' | 'iris' | 'none';

interface BiometricResult {
  success: boolean;
  error?: string;
}

interface BiometricStatus {
  isAvailable: boolean;
  biometricType: BiometricType;
  isEnabled: boolean;
  isEnrolled: boolean;
}

class BiometricService {
  /**
   * Check if biometric authentication is available on device
   */
  async checkBiometricStatus(): Promise<BiometricStatus> {
    try {
      // Check if biometric hardware is available
      const isAvailable = await LocalAuthentication.hasHardwareAsync();

      // Check if biometrics are enrolled
      const isEnrolled = await LocalAuthentication.isEnrolledAsync();

      // Get biometric type
      const supportedTypes = await LocalAuthentication.supportedAuthenticationTypesAsync();
      let biometricType: BiometricType = 'none';

      if (supportedTypes.includes(LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION)) {
        biometricType = 'face';
      } else if (supportedTypes.includes(LocalAuthentication.AuthenticationType.FINGERPRINT)) {
        biometricType = 'fingerprint';
      } else if (supportedTypes.includes(LocalAuthentication.AuthenticationType.IRIS)) {
        biometricType = 'iris';
      }

      // Check if user has enabled biometric authentication
      const isEnabled = await this.isBiometricEnabled();

      return {
        isAvailable,
        biometricType,
        isEnabled,
        isEnrolled,
      };
    } catch (error) {
      console.error('Failed to check biometric status:', error);
      return {
        isAvailable: false,
        biometricType: 'none',
        isEnabled: false,
        isEnrolled: false,
      };
    }
  }

  /**
   * Authenticate using biometrics
   */
  async authenticate(
    promptMessage?: string,
    cancelLabel?: string,
    fallbackLabel?: string
  ): Promise<BiometricResult> {
    try {
      const status = await this.checkBiometricStatus();

      if (!status.isAvailable) {
        return {
          success: false,
          error: 'Biometric authentication is not available on this device',
        };
      }

      if (!status.isEnrolled) {
        return {
          success: false,
          error: 'No biometric credentials are enrolled. Please set up biometrics in your device settings.',
        };
      }

      if (!status.isEnabled) {
        return {
          success: false,
          error: 'Biometric authentication is disabled. Enable it in the app settings.',
        };
      }

      const result = await LocalAuthentication.authenticateAsync({
        promptMessage: promptMessage || 'Authenticate to continue',
        cancelLabel: cancelLabel || 'Cancel',
        fallbackLabel: fallbackLabel || 'Use Passcode',
        disableDeviceFallback: false,
        requireConfirmation: false,
      });

      if (result.success) {
        return { success: true };
      } else {
        return {
          success: false,
          error: this.getErrorMessage(result.error),
        };
      }
    } catch (error) {
      console.error('Biometric authentication failed:', error);
      return {
        success: false,
        error: 'An unexpected error occurred during authentication',
      };
    }
  }

  /**
   * Enable biometric authentication
   */
  async enableBiometric(): Promise<boolean> {
    try {
      const status = await this.checkBiometricStatus();

      if (!status.isAvailable || !status.isEnrolled) {
        return false;
      }

      // Authenticate before enabling
      const authResult = await this.authenticate(
        'Authenticate to enable biometric login',
        'Cancel',
        'Use Passcode'
      );

      if (authResult.success) {
        await AsyncStorage.setItem(BIOMETRIC_ENABLED_KEY, 'true');
        await AsyncStorage.setItem(BIOMETRIC_TYPE_KEY, status.biometricType);
        return true;
      }

      return false;
    } catch (error) {
      console.error('Failed to enable biometric:', error);
      return false;
    }
  }

  /**
   * Disable biometric authentication
   */
  async disableBiometric(): Promise<boolean> {
    try {
      await AsyncStorage.removeItem(BIOMETRIC_ENABLED_KEY);
      await AsyncStorage.removeItem(BIOMETRIC_TYPE_KEY);
      return true;
    } catch (error) {
      console.error('Failed to disable biometric:', error);
      return false;
    }
  }

  /**
   * Check if biometric is enabled by user
   */
  async isBiometricEnabled(): Promise<boolean> {
    try {
      const enabled = await AsyncStorage.getItem(BIOMETRIC_ENABLED_KEY);
      return enabled === 'true';
    } catch (error) {
      console.error('Failed to check biometric enabled status:', error);
      return false;
    }
  }

  /**
   * Get stored biometric type
   */
  async getStoredBiometricType(): Promise<BiometricType> {
    try {
      const type = await AsyncStorage.getItem(BIOMETRIC_TYPE_KEY);
      return (type as BiometricType) || 'none';
    } catch (error) {
      console.error('Failed to get biometric type:', error);
      return 'none';
    }
  }

  /**
   * Quick authentication for app resume
   */
  async quickAuthenticate(): Promise<boolean> {
    const isEnabled = await this.isBiometricEnabled();

    if (!isEnabled) {
      return true; // Skip if not enabled
    }

    const result = await this.authenticate(
      'Authenticate to continue',
      'Cancel',
      'Use Passcode'
    );

    return result.success;
  }

  /**
   * Authenticate for sensitive operations
   */
  async authenticateForSensitiveOperation(
    operationName: string
  ): Promise<BiometricResult> {
    const isEnabled = await this.isBiometricEnabled();

    if (!isEnabled) {
      return { success: true }; // Skip if not enabled
    }

    return this.authenticate(
      `Authenticate to ${operationName}`,
      'Cancel',
      'Use Passcode'
    );
  }

  /**
   * Get error message for biometric error
   */
  private getErrorMessage(error: string): string {
    switch (error) {
      case 'UserCancel':
        return 'Authentication was cancelled';
      case 'UserFallback':
        return 'User chose to use fallback authentication';
      case 'SystemCancel':
        return 'Authentication was cancelled by the system';
      case 'NotEnrolled':
        return 'No biometric credentials are enrolled';
      case 'BiometryNotAvailable':
        return 'Biometric authentication is not available';
      case 'BiometryNotEnrolled':
        return 'No biometric credentials are enrolled';
      case 'BiometryLockout':
        return 'Too many failed attempts. Biometric authentication is locked';
      case 'BiometryPermanentLockout':
        return 'Biometric authentication is permanently locked';
      case 'BiometryDisconnected':
        return 'Biometric sensor is disconnected';
      case 'DeviceLocked':
        return 'Device is locked';
      case 'PasscodeNotSet':
        return 'Device passcode is not set';
      case 'FaceRecognitionNotAvailable':
        return 'Face recognition is not available';
      case 'FingerprintScannerNotAvailable':
        return 'Fingerprint scanner is not available';
      case 'IrisRecognitionNotAvailable':
        return 'Iris recognition is not available';
      default:
        return 'Authentication failed';
    }
  }
}

// Export singleton instance
export const biometricService = new BiometricService();