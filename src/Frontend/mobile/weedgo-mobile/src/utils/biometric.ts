import * as LocalAuthentication from 'expo-local-authentication';

export enum BiometricType {
  FINGERPRINT = 'fingerprint',
  FACE_ID = 'face',
  IRIS = 'iris',
  NONE = 'none'
}

interface BiometricAuthResult {
  success: boolean;
  error?: string;
  warning?: string;
}

class BiometricAuth {
  /**
   * Check if biometric authentication is available on the device
   */
  async isAvailable(): Promise<boolean> {
    try {
      const compatible = await LocalAuthentication.hasHardwareAsync();
      if (!compatible) return false;

      const enrolled = await LocalAuthentication.isEnrolledAsync();
      return enrolled;
    } catch (error) {
      console.error('Error checking biometric availability:', error);
      return false;
    }
  }

  /**
   * Check if device has biometric hardware
   */
  async hasHardware(): Promise<boolean> {
    try {
      return await LocalAuthentication.hasHardwareAsync();
    } catch (error) {
      console.error('Error checking biometric hardware:', error);
      return false;
    }
  }

  /**
   * Check if user has enrolled biometrics
   */
  async isEnrolled(): Promise<boolean> {
    try {
      return await LocalAuthentication.isEnrolledAsync();
    } catch (error) {
      console.error('Error checking biometric enrollment:', error);
      return false;
    }
  }

  /**
   * Authenticate using biometrics
   */
  async authenticate(reason?: string): Promise<BiometricAuthResult> {
    try {
      const available = await this.isAvailable();
      if (!available) {
        return {
          success: false,
          error: 'Biometric authentication is not available'
        };
      }

      const result = await LocalAuthentication.authenticateAsync({
        promptMessage: reason || 'Authenticate to continue',
        disableDeviceFallback: false,
        cancelLabel: 'Cancel',
        fallbackLabel: 'Use Passcode'
      });

      if (result.success) {
        return { success: true };
      }

      // Handle different error types
      switch (result.error) {
        case LocalAuthentication.AuthenticationError.USER_CANCEL:
          return {
            success: false,
            error: 'Authentication cancelled'
          };
        case LocalAuthentication.AuthenticationError.USER_FALLBACK:
          return {
            success: false,
            warning: 'User chose to use passcode'
          };
        case LocalAuthentication.AuthenticationError.SYSTEM_CANCEL:
          return {
            success: false,
            error: 'System cancelled authentication'
          };
        case LocalAuthentication.AuthenticationError.NOT_ENROLLED:
          return {
            success: false,
            error: 'No biometrics enrolled'
          };
        case LocalAuthentication.AuthenticationError.BIOMETRIC_NOT_AVAILABLE:
          return {
            success: false,
            error: 'Biometric authentication not available'
          };
        case LocalAuthentication.AuthenticationError.LOCKOUT:
          return {
            success: false,
            error: 'Too many failed attempts. Please try again later'
          };
        default:
          return {
            success: false,
            error: 'Authentication failed'
          };
      }
    } catch (error) {
      console.error('Biometric authentication error:', error);
      return {
        success: false,
        error: 'An unexpected error occurred'
      };
    }
  }

  /**
   * Get the type of biometric authentication available
   */
  async getBiometricType(): Promise<BiometricType> {
    try {
      const available = await this.hasHardware();
      if (!available) return BiometricType.NONE;

      const types = await LocalAuthentication.supportedAuthenticationTypesAsync();

      if (types.includes(LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION)) {
        return BiometricType.FACE_ID;
      }
      if (types.includes(LocalAuthentication.AuthenticationType.FINGERPRINT)) {
        return BiometricType.FINGERPRINT;
      }
      if (types.includes(LocalAuthentication.AuthenticationType.IRIS)) {
        return BiometricType.IRIS;
      }

      return BiometricType.NONE;
    } catch (error) {
      console.error('Error getting biometric type:', error);
      return BiometricType.NONE;
    }
  }

  /**
   * Get a user-friendly name for the biometric type
   */
  async getBiometricTypeName(): Promise<string> {
    const type = await this.getBiometricType();
    switch (type) {
      case BiometricType.FACE_ID:
        return 'Face ID';
      case BiometricType.FINGERPRINT:
        return 'Touch ID';
      case BiometricType.IRIS:
        return 'Iris Scanner';
      default:
        return 'Biometric Authentication';
    }
  }

  /**
   * Quick authentication with stored credentials
   */
  async quickAuthenticate(): Promise<BiometricAuthResult> {
    const biometricType = await this.getBiometricTypeName();
    return this.authenticate(`Sign in with ${biometricType}`);
  }
}

export const biometricAuth = new BiometricAuth();