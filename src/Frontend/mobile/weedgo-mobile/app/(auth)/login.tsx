import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Keyboard,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuthStore } from '@/stores/authStore';
import { formatPhoneOnType, validatePhoneNumber, toE164 } from '@/utils/phoneFormat';
import { Colors } from '@/constants/Colors';
import { biometricAuth } from '@/utils/biometric';

export default function LoginScreen() {
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [requiresPassword, setRequiresPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [checkingBiometric, setCheckingBiometric] = useState(false);

  const phoneInputRef = useRef<TextInput>(null);
  const passwordInputRef = useRef<TextInput>(null);
  const router = useRouter();

  const { checkPhone, login, error, clearError, loadStoredAuth, biometricEnabled } = useAuthStore();

  // Check for stored auth and biometric on mount
  useEffect(() => {
    checkForStoredAuth();
  }, []);

  const checkForStoredAuth = async () => {
    setCheckingBiometric(true);
    try {
      // First check if user has stored auth
      await loadStoredAuth();

      // If biometric is enabled, offer quick login
      if (biometricEnabled) {
        const biometricAvailable = await biometricAuth.isAvailable();
        if (biometricAvailable) {
          setTimeout(() => {
            offerBiometricLogin();
          }, 500);
        }
      }
    } catch (error) {
      console.log('No stored auth found');
    } finally {
      setCheckingBiometric(false);
    }
  };

  const offerBiometricLogin = async () => {
    Alert.alert(
      'Quick Login',
      'Would you like to sign in with biometrics?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Sign In',
          onPress: async () => {
            const result = await biometricAuth.authenticate('Sign in with biometrics');
            if (result.success) {
              router.replace('/(tabs)');
            } else if (result.error) {
              Alert.alert('Authentication Failed', result.error);
            }
          },
        },
      ]
    );
  };

  const handlePhoneChange = (text: string) => {
    const formatted = formatPhoneOnType(text);
    setPhone(formatted);

    // Clear error when user starts typing
    if (error) clearError();
  };

  const handleContinue = async () => {
    // Validate phone number
    if (!validatePhoneNumber(phone)) {
      Alert.alert('Invalid Phone Number', 'Please enter a valid 10-digit phone number');
      return;
    }

    setLoading(true);
    Keyboard.dismiss();

    try {
      // Check if phone exists
      const phoneCheck = await checkPhone(toE164(phone));

      if (!phoneCheck.exists) {
        // Navigate to registration
        router.push({
          pathname: '/(auth)/register',
          params: { phone: toE164(phone) },
        });
      } else if (phoneCheck.requiresPassword) {
        // Show password field
        setRequiresPassword(true);
        setTimeout(() => passwordInputRef.current?.focus(), 100);
      } else {
        // Send OTP
        const response = await login(toE164(phone));
        if (response.sessionId) {
          router.push({
            pathname: '/(auth)/otp-verify',
            params: {
              phone: toE164(phone),
              sessionId: response.sessionId,
            },
          });
        }
      }
    } catch (err) {
      Alert.alert('Error', error || 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordLogin = async () => {
    if (!password) {
      Alert.alert('Password Required', 'Please enter your password');
      return;
    }

    setLoading(true);
    Keyboard.dismiss();

    try {
      const response = await login(toE164(phone), password);

      if (response.requiresOtp && response.sessionId) {
        router.push({
          pathname: '/(auth)/otp-verify',
          params: {
            phone: toE164(phone),
            sessionId: response.sessionId,
          },
        });
      } else {
        // Direct login successful
        router.replace('/(tabs)');
      }
    } catch (err) {
      Alert.alert('Login Failed', error || 'Invalid phone number or password');
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = () => {
    Alert.alert(
      'Reset Password',
      'We\'ll send you a verification code to reset your password.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Send Code',
          onPress: async () => {
            setLoading(true);
            try {
              const response = await login(toE164(phone));
              if (response.sessionId) {
                router.push({
                  pathname: '/(auth)/otp-verify',
                  params: {
                    phone: toE164(phone),
                    sessionId: response.sessionId,
                    resetPassword: 'true',
                  },
                });
              }
            } catch (err) {
              Alert.alert('Error', 'Failed to send verification code');
            } finally {
              setLoading(false);
            }
          },
        },
      ]
    );
  };

  if (checkingBiometric) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.light.primary} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        style={styles.keyboardView}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {/* Logo/Header */}
          <View style={styles.header}>
            <View style={styles.logoContainer}>
              <Ionicons name="leaf" size={60} color={Colors.light.primary} />
            </View>
            <Text style={styles.title}>Welcome to WeedGo</Text>
            <Text style={styles.subtitle}>
              {requiresPassword ? 'Enter your password to continue' : 'Sign in or create an account to continue'}
            </Text>
          </View>

          {/* Phone Input */}
          <View style={styles.inputContainer}>
            <Text style={styles.inputLabel}>Phone Number</Text>
            <View style={[styles.inputWrapper, requiresPassword && styles.inputDisabled]}>
              <Text style={styles.countryCode}>+1</Text>
              <TextInput
                ref={phoneInputRef}
                style={styles.input}
                placeholder="(555) 123-4567"
                placeholderTextColor={Colors.light.gray}
                value={phone}
                onChangeText={handlePhoneChange}
                keyboardType="phone-pad"
                autoComplete="tel"
                textContentType="telephoneNumber"
                maxLength={14}
                editable={!requiresPassword && !loading}
                returnKeyType={requiresPassword ? 'next' : 'done'}
                onSubmitEditing={requiresPassword ? () => passwordInputRef.current?.focus() : handleContinue}
              />
              {requiresPassword && (
                <TouchableOpacity
                  onPress={() => {
                    setRequiresPassword(false);
                    setPassword('');
                    setPhone('');
                    setTimeout(() => phoneInputRef.current?.focus(), 100);
                  }}
                  style={styles.changeButton}
                >
                  <Text style={styles.changeButtonText}>Change</Text>
                </TouchableOpacity>
              )}
            </View>
          </View>

          {/* Password Input (conditional) */}
          {requiresPassword && (
            <View style={styles.inputContainer}>
              <Text style={styles.inputLabel}>Password</Text>
              <View style={styles.inputWrapper}>
                <TextInput
                  ref={passwordInputRef}
                  style={[styles.input, styles.passwordInput]}
                  placeholder="Enter your password"
                  placeholderTextColor={Colors.light.gray}
                  value={password}
                  onChangeText={setPassword}
                  secureTextEntry={!showPassword}
                  autoComplete="password"
                  textContentType="password"
                  editable={!loading}
                  returnKeyType="done"
                  onSubmitEditing={handlePasswordLogin}
                />
                <TouchableOpacity
                  onPress={() => setShowPassword(!showPassword)}
                  style={styles.eyeButton}
                >
                  <Ionicons
                    name={showPassword ? 'eye-off-outline' : 'eye-outline'}
                    size={24}
                    color={Colors.light.gray}
                  />
                </TouchableOpacity>
              </View>
              <TouchableOpacity onPress={handleForgotPassword} style={styles.forgotButton}>
                <Text style={styles.forgotText}>Forgot password?</Text>
              </TouchableOpacity>
            </View>
          )}

          {/* Continue Button */}
          <TouchableOpacity
            style={[styles.continueButton, loading && styles.buttonDisabled]}
            onPress={requiresPassword ? handlePasswordLogin : handleContinue}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="white" />
            ) : (
              <Text style={styles.continueButtonText}>
                {requiresPassword ? 'Sign In' : 'Continue'}
              </Text>
            )}
          </TouchableOpacity>

          {/* Alternative Options */}
          <View style={styles.dividerContainer}>
            <View style={styles.divider} />
            <Text style={styles.dividerText}>or</Text>
            <View style={styles.divider} />
          </View>

          {/* Skip Login (Guest Mode) */}
          <TouchableOpacity
            style={styles.skipButton}
            onPress={() => router.replace('/(tabs)')}
            disabled={loading}
          >
            <Text style={styles.skipButtonText}>Continue as Guest</Text>
          </TouchableOpacity>

          {/* Terms */}
          <Text style={styles.terms}>
            By continuing, you agree to WeedGo's{' '}
            <Text style={styles.link}>Terms of Service</Text> and{' '}
            <Text style={styles.link}>Privacy Policy</Text>
          </Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.light.background,
  },
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    padding: 24,
    justifyContent: 'center',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  logoContainer: {
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
    paddingHorizontal: 20,
  },
  inputContainer: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.light.text,
    marginBottom: 8,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.light.border,
    borderRadius: 12,
    paddingHorizontal: 16,
    backgroundColor: 'white',
    height: 56,
  },
  inputDisabled: {
    backgroundColor: Colors.light.backgroundSecondary,
  },
  countryCode: {
    fontSize: 16,
    color: Colors.light.text,
    marginRight: 8,
  },
  input: {
    flex: 1,
    fontSize: 16,
    color: Colors.light.text,
  },
  passwordInput: {
    paddingRight: 40,
  },
  eyeButton: {
    position: 'absolute',
    right: 16,
    padding: 4,
  },
  changeButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  changeButtonText: {
    color: Colors.light.primary,
    fontSize: 14,
    fontWeight: '600',
  },
  forgotButton: {
    marginTop: 8,
    alignSelf: 'flex-end',
  },
  forgotText: {
    color: Colors.light.primary,
    fontSize: 14,
  },
  continueButton: {
    backgroundColor: Colors.light.primary,
    borderRadius: 12,
    height: 56,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 12,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  continueButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  dividerContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 24,
  },
  divider: {
    flex: 1,
    height: 1,
    backgroundColor: Colors.light.border,
  },
  dividerText: {
    color: Colors.light.gray,
    paddingHorizontal: 16,
    fontSize: 14,
  },
  skipButton: {
    borderWidth: 1,
    borderColor: Colors.light.border,
    borderRadius: 12,
    height: 56,
    justifyContent: 'center',
    alignItems: 'center',
  },
  skipButtonText: {
    color: Colors.light.text,
    fontSize: 16,
    fontWeight: '500',
  },
  terms: {
    marginTop: 24,
    fontSize: 12,
    color: Colors.light.gray,
    textAlign: 'center',
    lineHeight: 18,
  },
  link: {
    color: Colors.light.primary,
    textDecorationLine: 'underline',
  },
});