/**
 * Biometric authentication utilities using Expo LocalAuthentication
 */

import * as LocalAuthentication from 'expo-local-authentication';
import { Platform } from 'react-native';

export type BiometricType = 'faceid' | 'touchid' | 'fingerprint' | 'iris' | 'none';

export interface BiometricAuthResult {
  success: boolean;
  error?: string;
  biometricType?: BiometricType;
}

// Check if biometric authentication is available on the device
export async function isBiometricAvailable(): Promise<boolean> {
  try {
    const hasHardware = await LocalAuthentication.hasHardwareAsync();
    if (!hasHardware) return false;

    const isEnrolled = await LocalAuthentication.isEnrolledAsync();
    return isEnrolled;
  } catch (error) {
    console.error('Error checking biometric availability:', error);
    return false;
  }
}

// Get the type of biometric authentication available
export async function getBiometricType(): Promise<BiometricType> {
  try {
    const supportedTypes = await LocalAuthentication.supportedAuthenticationTypesAsync();

    if (supportedTypes.includes(LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION)) {
      return 'faceid';
    }
    if (supportedTypes.includes(LocalAuthentication.AuthenticationType.FINGERPRINT)) {
      if (Platform.OS === 'ios') {
        return 'touchid';
      }
      return 'fingerprint';
    }
    if (supportedTypes.includes(LocalAuthentication.AuthenticationType.IRIS)) {
      return 'iris';
    }

    return 'none';
  } catch (error) {
    console.error('Error getting biometric type:', error);
    return 'none';
  }
}

// Perform biometric authentication
async function authenticate(
  promptMessage: string = 'Authenticate to continue',
  fallbackLabel: string = 'Use Passcode',
  cancelLabel: string = 'Cancel'
): Promise<BiometricAuthResult> {
  try {
    // Check if biometric is available
    const isAvailable = await isBiometricAvailable();
    if (!isAvailable) {
      return {
        success: false,
        error: 'Biometric authentication is not available on this device',
      };
    }

    // Get biometric type
    const biometricType = await getBiometricType();

    // Perform authentication
    const result = await LocalAuthentication.authenticateAsync({
      promptMessage,
      cancelLabel,
      fallbackLabel,
      disableDeviceFallback: false, // Allow passcode as fallback
      requireConfirmation: Platform.OS === 'android', // Android only
    });

    if (result.success) {
      return {
        success: true,
        biometricType,
      };
    } else {
      let errorMessage = 'Authentication failed';

      switch (result.error) {
        case LocalAuthentication.LocalAuthenticationError.UserCancel:
          errorMessage = 'Authentication was cancelled';
          break;
        case LocalAuthentication.LocalAuthenticationError.UserFallback:
          errorMessage = 'User chose to use fallback authentication';
          break;
        case LocalAuthentication.LocalAuthenticationError.SystemCancel:
          errorMessage = 'Authentication was cancelled by the system';
          break;
        case LocalAuthentication.LocalAuthenticationError.PasscodeNotSet:
          errorMessage = 'Device passcode is not set';
          break;
        case LocalAuthentication.LocalAuthenticationError.BiometryNotAvailable:
          errorMessage = 'Biometric authentication is not available';
          break;
        case LocalAuthentication.LocalAuthenticationError.BiometryNotEnrolled:
          errorMessage = 'No biometric authentication methods are enrolled';
          break;
        case LocalAuthentication.LocalAuthenticationError.BiometryLockout:
          errorMessage = 'Too many failed attempts. Biometric authentication is locked';
          break;
        case LocalAuthentication.LocalAuthenticationError.AppCancel:
          errorMessage = 'Authentication was cancelled by the app';
          break;
        case LocalAuthentication.LocalAuthenticationError.InvalidContext:
          errorMessage = 'Authentication context is invalid';
          break;
        case LocalAuthentication.LocalAuthenticationError.NotInteractive:
          errorMessage = 'Authentication failed because the app is not in the foreground';
          break;
        case LocalAuthentication.LocalAuthenticationError.Timeout:
          errorMessage = 'Authentication timed out';
          break;
        default:
          errorMessage = 'Unknown authentication error';
      }

      return {
        success: false,
        error: errorMessage,
        biometricType,
      };
    }
  } catch (error: any) {
    console.error('Biometric authentication error:', error);
    return {
      success: false,
      error: error.message || 'An unexpected error occurred',
    };
  }
}

// Quick authenticate for stored credentials
async function quickAuthenticate(): Promise<BiometricAuthResult> {
  return authenticate('Authenticate to access your account', 'Use Passcode', 'Cancel');
}

// Get a user-friendly name for the biometric type
export function getBiometricDisplayName(type: BiometricType): string {
  switch (type) {
    case 'faceid':
      return 'Face ID';
    case 'touchid':
      return 'Touch ID';
    case 'fingerprint':
      return 'Fingerprint';
    case 'iris':
      return 'Iris Scanner';
    case 'none':
    default:
      return 'Biometric Authentication';
  }
}

// Export as a single object for better compatibility
export const biometricAuth = {
  authenticate,
  quickAuthenticate,
  isAvailable: isBiometricAvailable,
  getType: getBiometricType,
  getDisplayName: getBiometricDisplayName,
};