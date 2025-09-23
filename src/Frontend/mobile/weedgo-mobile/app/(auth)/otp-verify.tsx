import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Keyboard,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuthStore } from '@/stores/authStore';
import { Colors } from '@/constants/Colors';
import { biometricAuth, BiometricType } from '@/utils/biometric';
import { maskPhoneNumber } from '@/utils/phoneFormat';

const OTP_LENGTH = 6;
const RESEND_TIMEOUT = 60; // seconds

export default function OTPVerifyScreen() {
  const [otp, setOtp] = useState<string[]>(new Array(OTP_LENGTH).fill(''));
  const [loading, setLoading] = useState(false);
  const [resendTimer, setResendTimer] = useState(RESEND_TIMEOUT);
  const [canResend, setCanResend] = useState(false);

  const inputs = useRef<(TextInput | null)[]>(new Array(OTP_LENGTH).fill(null));
  const timerRef = useRef<NodeJS.Timeout | undefined>(undefined);

  const { phone, sessionId, resetPassword } = useLocalSearchParams<{
    phone: string;
    sessionId: string;
    resetPassword?: string;
  }>();

  const router = useRouter();
  const { verifyOTP, resendOTP, setBiometricEnabled, error, clearError } = useAuthStore();

  // Start countdown timer on mount
  useEffect(() => {
    startResendTimer();
    // Focus first input on mount
    setTimeout(() => inputs.current[0]?.focus(), 300);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const startResendTimer = () => {
    setCanResend(false);
    setResendTimer(RESEND_TIMEOUT);

    timerRef.current = setInterval(() => {
      setResendTimer((prev) => {
        if (prev <= 1) {
          setCanResend(true);
          if (timerRef.current) clearInterval(timerRef.current);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const handleOtpChange = (value: string, index: number) => {
    // Only allow digits
    if (value && !/^\d$/.test(value)) return;

    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);

    // Clear error when user starts typing
    if (error) clearError();

    // Auto-advance to next input
    if (value && index < OTP_LENGTH - 1) {
      inputs.current[index + 1]?.focus();
    }

    // Auto-submit when all digits are entered
    if (value && index === OTP_LENGTH - 1) {
      const otpCode = newOtp.join('');
      if (otpCode.length === OTP_LENGTH) {
        handleVerify(otpCode);
      }
    }
  };

  const handleKeyPress = (key: string, index: number) => {
    // Handle backspace
    if (key === 'Backspace' && !otp[index] && index > 0) {
      inputs.current[index - 1]?.focus();
    }
  };

  const handlePaste = async (event: any, index: number) => {
    const pastedText = event.nativeEvent.text;

    // Check if pasted text is a valid OTP
    if (/^\d{6}$/.test(pastedText)) {
      const otpArray = pastedText.split('');
      setOtp(otpArray);

      // Focus last input
      inputs.current[OTP_LENGTH - 1]?.focus();

      // Auto-submit
      handleVerify(pastedText);
    }
  };

  const handleVerify = async (otpCode: string) => {
    if (otpCode.length !== OTP_LENGTH) {
      Alert.alert('Invalid Code', 'Please enter a 6-digit verification code');
      return;
    }

    setLoading(true);
    Keyboard.dismiss();

    try {
      await verifyOTP(phone, otpCode, sessionId);

      // Check for biometric availability after successful verification
      const biometricAvailable = await biometricAuth.isAvailable();

      if (biometricAvailable && !resetPassword) {
        const biometricType = await biometricAuth.getType();
        const biometricTypeName = biometricAuth.getDisplayName(biometricType);

        Alert.alert(
          'Enable Quick Login',
          `Would you like to enable ${biometricTypeName} for faster sign-in next time?`,
          [
            {
              text: 'Not Now',
              style: 'cancel',
              onPress: () => navigateToHome(),
            },
            {
              text: 'Enable',
              onPress: async () => {
                const result = await biometricAuth.authenticate(
                  `Enable ${biometricTypeName} for WeedGo`
                );

                if (result.success) {
                  await setBiometricEnabled(true);
                  Alert.alert(
                    'Success',
                    `${biometricTypeName} enabled successfully!`,
                    [{ text: 'OK', onPress: () => navigateToHome() }]
                  );
                } else {
                  navigateToHome();
                }
              },
            },
          ]
        );
      } else {
        navigateToHome();
      }
    } catch (err) {
      setLoading(false);

      // Clear OTP inputs on error
      setOtp(new Array(OTP_LENGTH).fill(''));
      inputs.current[0]?.focus();

      Alert.alert(
        'Verification Failed',
        error || 'Invalid verification code. Please try again.'
      );
    }
  };

  const navigateToHome = () => {
    if (resetPassword === 'true') {
      // Navigate to password reset screen
      router.replace({
        pathname: '/(auth)/reset-password',
        params: { phone },
      });
    } else {
      // Navigate to main app
      router.replace('/(tabs)');
    }
  };

  const handleResend = async () => {
    if (!canResend) return;

    setLoading(true);
    try {
      await resendOTP(phone, sessionId);

      // Clear OTP inputs
      setOtp(new Array(OTP_LENGTH).fill(''));
      inputs.current[0]?.focus();

      // Restart timer
      startResendTimer();

      Alert.alert('Code Sent', 'A new verification code has been sent to your phone');
    } catch (err) {
      Alert.alert('Error', 'Failed to resend code. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatTimer = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.iconContainer}>
            <Ionicons name="shield-checkmark" size={60} color={Colors.light.primary} />
          </View>
          <Text style={styles.title}>Verify Your Phone</Text>
          <Text style={styles.subtitle}>
            Enter the 6-digit code sent to{'\n'}
            <Text style={styles.phoneNumber}>{maskPhoneNumber(phone)}</Text>
          </Text>
        </View>

        {/* OTP Input */}
        <View style={styles.otpContainer}>
          {otp.map((digit, index) => (
            <TextInput
              key={index}
              ref={(ref) => { inputs.current[index] = ref; }}
              style={[
                styles.otpInput,
                digit ? styles.otpInputFilled : {},
                error ? styles.otpInputError : {},
              ]}
              value={digit}
              onChangeText={(value) => handleOtpChange(value, index)}
              onKeyPress={({ nativeEvent }) => handleKeyPress(nativeEvent.key, index)}
              onPaste={(e: any) => handlePaste(e, index)}
              keyboardType="number-pad"
              maxLength={1}
              selectTextOnFocus
              editable={!loading}
              autoComplete="one-time-code"
              textContentType="oneTimeCode"
            />
          ))}
        </View>

        {/* Error Message */}
        {error && (
          <View style={styles.errorContainer}>
            <Ionicons name="alert-circle" size={16} color={Colors.light.error} />
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        {/* Verify Button */}
        <TouchableOpacity
          style={[styles.verifyButton, loading && styles.buttonDisabled]}
          onPress={() => handleVerify(otp.join(''))}
          disabled={loading || otp.some((d) => !d)}
        >
          {loading ? (
            <ActivityIndicator color="white" />
          ) : (
            <Text style={styles.verifyButtonText}>Verify Code</Text>
          )}
        </TouchableOpacity>

        {/* Resend Section */}
        <View style={styles.resendContainer}>
          <Text style={styles.resendText}>Didn't receive the code?</Text>
          {canResend ? (
            <TouchableOpacity onPress={handleResend} disabled={loading}>
              <Text style={styles.resendLink}>Resend Code</Text>
            </TouchableOpacity>
          ) : (
            <Text style={styles.resendTimer}>
              Resend in {formatTimer(resendTimer)}
            </Text>
          )}
        </View>

        {/* Alternative Options */}
        <View style={styles.alternativeContainer}>
          <TouchableOpacity
            onPress={() => router.back()}
            style={styles.alternativeButton}
            disabled={loading}
          >
            <Ionicons name="arrow-back" size={20} color={Colors.light.primary} />
            <Text style={styles.alternativeText}>Use different phone number</Text>
          </TouchableOpacity>
        </View>

        {/* Help Text */}
        <Text style={styles.helpText}>
          Make sure you have SMS enabled and check your spam folder if you don't see the message.
        </Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.light.background,
  },
  content: {
    flex: 1,
    padding: 24,
    justifyContent: 'center',
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  iconContainer: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: Colors.light.primaryLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: Colors.light.text,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: Colors.light.gray,
    textAlign: 'center',
    lineHeight: 24,
  },
  phoneNumber: {
    fontWeight: '600',
    color: Colors.light.text,
  },
  otpContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 24,
    paddingHorizontal: 20,
  },
  otpInput: {
    width: 45,
    height: 55,
    borderWidth: 2,
    borderColor: Colors.light.border,
    borderRadius: 12,
    fontSize: 24,
    fontWeight: '600',
    textAlign: 'center',
    color: Colors.light.text,
    backgroundColor: 'white',
  },
  otpInputFilled: {
    borderColor: Colors.light.primary,
    backgroundColor: Colors.light.primaryLight,
  },
  otpInputError: {
    borderColor: Colors.light.error,
    backgroundColor: '#FEE',
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
    paddingHorizontal: 16,
  },
  errorText: {
    color: Colors.light.error,
    fontSize: 14,
    marginLeft: 6,
  },
  verifyButton: {
    backgroundColor: Colors.light.primary,
    borderRadius: 12,
    height: 56,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  verifyButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  resendContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
    gap: 8,
  },
  resendText: {
    fontSize: 14,
    color: Colors.light.gray,
  },
  resendLink: {
    fontSize: 14,
    color: Colors.light.primary,
    fontWeight: '600',
  },
  resendTimer: {
    fontSize: 14,
    color: Colors.light.gray,
    fontWeight: '500',
  },
  alternativeContainer: {
    alignItems: 'center',
    marginBottom: 32,
  },
  alternativeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    gap: 8,
  },
  alternativeText: {
    fontSize: 14,
    color: Colors.light.primary,
    fontWeight: '500',
  },
  helpText: {
    fontSize: 12,
    color: Colors.light.gray,
    textAlign: 'center',
    lineHeight: 18,
    paddingHorizontal: 20,
  },
});