import React, { useState, useRef } from 'react';
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
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { Colors, BorderRadius, Shadows, Gradients } from '@/constants/Colors';
import { formatPhoneOnType, validatePhoneNumber, toE164 } from '@/utils/phoneFormat';
import { authService } from '@/services/api/auth';

const isDark = true;
const theme = isDark ? Colors.dark : Colors.light;

export default function ResetPasswordScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();

  const [step, setStep] = useState<'request' | 'verify' | 'reset'>('request');
  const [identifier, setIdentifier] = useState((params.email as string) || (params.phone as string) || '');
  const [isEmail, setIsEmail] = useState(!!(params.email));
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const otpInputRef = useRef<TextInput>(null);
  const passwordInputRef = useRef<TextInput>(null);
  const confirmPasswordInputRef = useRef<TextInput>(null);

  const handlePhoneChange = (text: string) => {
    if (!isEmail) {
      const formatted = formatPhoneOnType(text);
      setIdentifier(formatted);
    }
  };

  const handleRequestReset = async () => {
    // Validate input
    if (isEmail && !identifier.includes('@')) {
      Alert.alert('Invalid Email', 'Please enter a valid email address');
      return;
    }

    if (!isEmail && !validatePhoneNumber(identifier)) {
      Alert.alert('Invalid Phone', 'Please enter a valid 10-digit phone number');
      return;
    }

    setLoading(true);
    Keyboard.dismiss();

    try {
      const response = await authService.requestPasswordReset({
        identifier: isEmail ? identifier : toE164(identifier),
      });

      if (response.session_id) {
        setSessionId(response.session_id);
        setStep('verify');
        setTimeout(() => otpInputRef.current?.focus(), 500);
      }
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to send reset code');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async () => {
    if (!otp || otp.length < 4) {
      Alert.alert('Invalid Code', 'Please enter the verification code');
      return;
    }

    setLoading(true);
    Keyboard.dismiss();

    try {
      const response = await authService.verifyResetOTP({
        session_id: sessionId,
        code: otp,
      });

      if (response.success) {
        setStep('reset');
        setTimeout(() => passwordInputRef.current?.focus(), 500);
      }
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Invalid verification code');
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async () => {
    // Validate passwords
    if (!newPassword || newPassword.length < 8) {
      Alert.alert('Invalid Password', 'Password must be at least 8 characters');
      return;
    }

    if (newPassword !== confirmPassword) {
      Alert.alert('Password Mismatch', 'Passwords do not match');
      return;
    }

    setLoading(true);
    Keyboard.dismiss();

    try {
      await authService.resetPassword({
        session_id: sessionId,
        new_password: newPassword,
      });

      Alert.alert(
        'Success',
        'Your password has been reset successfully',
        [
          {
            text: 'Sign In',
            onPress: () => router.replace('/(auth)/login'),
          },
        ]
      );
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to reset password');
    } finally {
      setLoading(false);
    }
  };

  const handleResendCode = async () => {
    setLoading(true);
    try {
      await authService.resendOTP(
        isEmail ? identifier : toE164(identifier),
        sessionId
      );
      Alert.alert('Success', 'A new code has been sent');
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to resend code');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={Gradients.darkBackground}
        style={styles.gradient}
      >
        <SafeAreaView style={styles.safeArea}>
          <KeyboardAvoidingView
            style={styles.keyboardView}
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          >
            <ScrollView
              contentContainerStyle={styles.scrollContent}
              keyboardShouldPersistTaps="handled"
              showsVerticalScrollIndicator={false}
            >
              {/* Back Button */}
              <TouchableOpacity
                style={styles.backButton}
                onPress={() => router.back()}
              >
                <Ionicons name="arrow-back" size={24} color={theme.text} />
              </TouchableOpacity>

              {/* Header */}
              <View style={styles.header}>
                <LinearGradient
                  colors={Gradients.primary}
                  style={styles.iconContainer}
                >
                  <Ionicons name="lock-closed" size={32} color="white" />
                </LinearGradient>
                <Text style={styles.title}>
                  {step === 'request' && 'Reset Password'}
                  {step === 'verify' && 'Verify Code'}
                  {step === 'reset' && 'New Password'}
                </Text>
                <Text style={styles.subtitle}>
                  {step === 'request' && 'Enter your email or phone to receive a reset code'}
                  {step === 'verify' && 'Enter the code we sent you'}
                  {step === 'reset' && 'Create a new password for your account'}
                </Text>
              </View>

              {/* Step 1: Request Reset */}
              {step === 'request' && (
                <>
                  {/* Toggle Email/Phone */}
                  <View style={styles.toggleContainer}>
                    <TouchableOpacity
                      style={[
                        styles.toggleButton,
                        !isEmail && styles.toggleButtonActive,
                      ]}
                      onPress={() => {
                        setIsEmail(false);
                        setIdentifier('');
                      }}
                    >
                      <Text style={[
                        styles.toggleText,
                        !isEmail && styles.toggleTextActive,
                      ]}>
                        Phone
                      </Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[
                        styles.toggleButton,
                        isEmail && styles.toggleButtonActive,
                      ]}
                      onPress={() => {
                        setIsEmail(true);
                        setIdentifier('');
                      }}
                    >
                      <Text style={[
                        styles.toggleText,
                        isEmail && styles.toggleTextActive,
                      ]}>
                        Email
                      </Text>
                    </TouchableOpacity>
                  </View>

                  {/* Input */}
                  <View style={styles.inputWrapper}>
                    <Ionicons
                      name={isEmail ? 'mail-outline' : 'call-outline'}
                      size={20}
                      color={theme.textSecondary}
                    />
                    {!isEmail && <Text style={styles.countryCode}>+1</Text>}
                    <TextInput
                      style={styles.input}
                      placeholder={isEmail ? 'your@email.com' : '(555) 123-4567'}
                      placeholderTextColor={theme.textSecondary}
                      value={identifier}
                      onChangeText={isEmail ? setIdentifier : handlePhoneChange}
                      keyboardType={isEmail ? 'email-address' : 'phone-pad'}
                      autoCapitalize={isEmail ? 'none' : 'none'}
                      autoComplete={isEmail ? 'email' : 'tel'}
                      editable={!loading}
                      returnKeyType="done"
                      onSubmitEditing={handleRequestReset}
                    />
                  </View>

                  <TouchableOpacity
                    onPress={handleRequestReset}
                    disabled={loading}
                    activeOpacity={0.9}
                  >
                    <LinearGradient
                      colors={loading ? ['#666', '#444'] : Gradients.primary}
                      style={styles.button}
                      start={{ x: 0, y: 0 }}
                      end={{ x: 1, y: 1 }}
                    >
                      {loading ? (
                        <ActivityIndicator color="white" />
                      ) : (
                        <>
                          <Text style={styles.buttonText}>Send Reset Code</Text>
                          <Ionicons name="arrow-forward" size={20} color="white" />
                        </>
                      )}
                    </LinearGradient>
                  </TouchableOpacity>
                </>
              )}

              {/* Step 2: Verify OTP */}
              {step === 'verify' && (
                <>
                  <View style={styles.inputWrapper}>
                    <Ionicons name="key-outline" size={20} color={theme.textSecondary} />
                    <TextInput
                      ref={otpInputRef}
                      style={styles.input}
                      placeholder="Enter verification code"
                      placeholderTextColor={theme.textSecondary}
                      value={otp}
                      onChangeText={setOtp}
                      keyboardType="number-pad"
                      maxLength={6}
                      autoComplete="sms-otp"
                      textContentType="oneTimeCode"
                      editable={!loading}
                      returnKeyType="done"
                      onSubmitEditing={handleVerifyOTP}
                    />
                  </View>

                  <TouchableOpacity
                    onPress={handleVerifyOTP}
                    disabled={loading}
                    activeOpacity={0.9}
                  >
                    <LinearGradient
                      colors={loading ? ['#666', '#444'] : Gradients.primary}
                      style={styles.button}
                      start={{ x: 0, y: 0 }}
                      end={{ x: 1, y: 1 }}
                    >
                      {loading ? (
                        <ActivityIndicator color="white" />
                      ) : (
                        <>
                          <Text style={styles.buttonText}>Verify Code</Text>
                          <Ionicons name="checkmark" size={20} color="white" />
                        </>
                      )}
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={styles.linkButton}
                    onPress={handleResendCode}
                    disabled={loading}
                  >
                    <Text style={styles.linkText}>Resend Code</Text>
                  </TouchableOpacity>
                </>
              )}

              {/* Step 3: Reset Password */}
              {step === 'reset' && (
                <>
                  <View style={styles.inputWrapper}>
                    <Ionicons name="lock-closed-outline" size={20} color={theme.textSecondary} />
                    <TextInput
                      ref={passwordInputRef}
                      style={[styles.input, styles.passwordInput]}
                      placeholder="New password"
                      placeholderTextColor={theme.textSecondary}
                      value={newPassword}
                      onChangeText={setNewPassword}
                      secureTextEntry={!showPassword}
                      autoComplete="password-new"
                      textContentType="newPassword"
                      editable={!loading}
                      returnKeyType="next"
                      onSubmitEditing={() => confirmPasswordInputRef.current?.focus()}
                    />
                    <TouchableOpacity
                      onPress={() => setShowPassword(!showPassword)}
                      style={styles.eyeButton}
                    >
                      <Ionicons
                        name={showPassword ? 'eye-off-outline' : 'eye-outline'}
                        size={24}
                        color={theme.textSecondary}
                      />
                    </TouchableOpacity>
                  </View>

                  <View style={styles.inputWrapper}>
                    <Ionicons name="lock-closed-outline" size={20} color={theme.textSecondary} />
                    <TextInput
                      ref={confirmPasswordInputRef}
                      style={[styles.input, styles.passwordInput]}
                      placeholder="Confirm password"
                      placeholderTextColor={theme.textSecondary}
                      value={confirmPassword}
                      onChangeText={setConfirmPassword}
                      secureTextEntry={!showConfirmPassword}
                      autoComplete="password-new"
                      textContentType="newPassword"
                      editable={!loading}
                      returnKeyType="done"
                      onSubmitEditing={handleResetPassword}
                    />
                    <TouchableOpacity
                      onPress={() => setShowConfirmPassword(!showConfirmPassword)}
                      style={styles.eyeButton}
                    >
                      <Ionicons
                        name={showConfirmPassword ? 'eye-off-outline' : 'eye-outline'}
                        size={24}
                        color={theme.textSecondary}
                      />
                    </TouchableOpacity>
                  </View>

                  <TouchableOpacity
                    onPress={handleResetPassword}
                    disabled={loading}
                    activeOpacity={0.9}
                  >
                    <LinearGradient
                      colors={loading ? ['#666', '#444'] : Gradients.success}
                      style={styles.button}
                      start={{ x: 0, y: 0 }}
                      end={{ x: 1, y: 1 }}
                    >
                      {loading ? (
                        <ActivityIndicator color="white" />
                      ) : (
                        <>
                          <Text style={styles.buttonText}>Reset Password</Text>
                          <Ionicons name="checkmark-circle" size={20} color="white" />
                        </>
                      )}
                    </LinearGradient>
                  </TouchableOpacity>
                </>
              )}

              {/* Back to Login */}
              <TouchableOpacity
                style={styles.backToLogin}
                onPress={() => router.back()}
              >
                <Text style={styles.backToLoginText}>
                  Remember your password? <Text style={styles.link}>Sign In</Text>
                </Text>
              </TouchableOpacity>
            </ScrollView>
          </KeyboardAvoidingView>
        </SafeAreaView>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradient: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
  },
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    padding: 24,
    paddingBottom: 50,
  },
  backButton: {
    width: 48,
    height: 48,
    borderRadius: BorderRadius.full,
    backgroundColor: theme.glass,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
    ...Shadows.small,
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  iconContainer: {
    width: 80,
    height: 80,
    borderRadius: BorderRadius.full,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
    ...Shadows.colorful,
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    color: theme.text,
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 16,
    color: theme.textSecondary,
    textAlign: 'center',
    paddingHorizontal: 20,
    lineHeight: 22,
  },
  toggleContainer: {
    flexDirection: 'row',
    backgroundColor: theme.glass,
    borderRadius: BorderRadius.xl,
    padding: 4,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: theme.glassBorder,
  },
  toggleButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: BorderRadius.lg,
    alignItems: 'center',
  },
  toggleButtonActive: {
    backgroundColor: theme.surface,
    ...Shadows.small,
  },
  toggleText: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.textSecondary,
  },
  toggleTextActive: {
    color: theme.primary,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.glass,
    borderWidth: 1,
    borderColor: theme.glassBorder,
    borderRadius: BorderRadius.xl,
    paddingHorizontal: 16,
    height: 56,
    gap: 8,
    marginBottom: 16,
    ...Shadows.small,
  },
  countryCode: {
    fontSize: 16,
    color: theme.text,
    fontWeight: '600',
  },
  input: {
    flex: 1,
    fontSize: 16,
    color: theme.text,
  },
  passwordInput: {
    paddingRight: 40,
  },
  eyeButton: {
    position: 'absolute',
    right: 16,
    padding: 4,
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 56,
    borderRadius: BorderRadius.xxl,
    gap: 8,
    marginBottom: 16,
    ...Shadows.colorful,
  },
  buttonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: '700',
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 3,
  },
  linkButton: {
    alignSelf: 'center',
    marginTop: 8,
  },
  linkText: {
    color: theme.primary,
    fontSize: 14,
    fontWeight: '600',
  },
  backToLogin: {
    marginTop: 32,
    alignSelf: 'center',
  },
  backToLoginText: {
    color: theme.textSecondary,
    fontSize: 14,
  },
  link: {
    color: theme.primary,
    fontWeight: '600',
  },
});