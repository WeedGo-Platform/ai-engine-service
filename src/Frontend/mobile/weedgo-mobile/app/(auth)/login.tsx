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
  Dimensions,
  Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { BlurView } from 'expo-blur';
import { useAuthStore } from '@/stores/authStore';
import useStoreStore from '@/stores/storeStore';
import { useTenantStore } from '@/stores/tenantStore';
import { formatPhoneOnType, validatePhoneNumber, toE164 } from '@/utils/phoneFormat';
import { useTheme } from '@/contexts/ThemeContext';
import { Colors, BorderRadius, Shadows, Gradients } from '@/constants/Colors';

const { width } = Dimensions.get('window');

export default function LoginScreen() {
  const { theme, isDark } = useTheme();
  const [loginMethod, setLoginMethod] = useState<'phone' | 'email'>('email');
  const [authType, setAuthType] = useState<'otp' | 'password'>('password');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [checkingBiometric, setCheckingBiometric] = useState(true);
  const [savedBiometricEmail, setSavedBiometricEmail] = useState<string | null>(null);

  const phoneInputRef = useRef<TextInput>(null);
  const emailInputRef = useRef<TextInput>(null);
  const passwordInputRef = useRef<TextInput>(null);
  const router = useRouter();

  const {
    checkPhone,
    login,
    error,
    clearError,
    checkBiometricAvailability,
    biometricEnabled,
    biometricAvailable,
    biometricType,
    loginWithBiometric,
    enableBiometric,
    getSavedBiometricEmail,
  } = useAuthStore();
  const { currentStore, loadStores } = useStoreStore();
  const { tenant, loadTenant } = useTenantStore();

  const styles = React.useMemo(() => createStyles(theme, isDark), [theme, isDark]);

  // Load store and tenant info on mount
  useEffect(() => {
    if (!currentStore) {
      loadStores();
    }
    if (!tenant) {
      loadTenant();
    }
    checkForBiometric();
  }, []);

  const checkForBiometric = async () => {
    setCheckingBiometric(true);
    try {
      // Check biometric availability and if enabled
      await checkBiometricAvailability();

      // Get saved email if biometric is enabled
      const savedEmail = await getSavedBiometricEmail();
      if (savedEmail) {
        setSavedBiometricEmail(savedEmail);
        // Pre-fill email field if saved
        setEmail(savedEmail);
        // Keep email as default login method
        setLoginMethod('email');
      }
    } catch (error) {
      console.log('Error checking biometric:', error);
    } finally {
      setCheckingBiometric(false);
    }
  };

  const handleBiometricLogin = async () => {
    setLoading(true);
    try {
      const response = await loginWithBiometric();
      if (response && response.success) {
        console.log('Biometric login successful');
        router.replace('/(tabs)/');
      } else {
        Alert.alert(
          'Authentication Failed',
          'Unable to authenticate with biometrics. Please try with email/phone.'
        );
      }
    } catch (error: any) {
      Alert.alert(
        'Error',
        error.message || 'Biometric authentication failed'
      );
    } finally {
      setLoading(false);
    }
  };

  const handlePhoneChange = (text: string) => {
    const formatted = formatPhoneOnType(text);
    setPhone(formatted);
    if (error) clearError();
  };

  const handleContinue = async () => {
    // Validate input based on login method
    if (loginMethod === 'phone' && !validatePhoneNumber(phone)) {
      Alert.alert('Invalid Phone Number', 'Please enter a valid 10-digit phone number');
      return;
    }

    if (loginMethod === 'email' && !email) {
      Alert.alert('Email Required', 'Please enter your email address');
      return;
    }

    if (authType === 'password' && !password) {
      Alert.alert('Password Required', 'Please enter your password');
      return;
    }

    setLoading(true);
    Keyboard.dismiss();

    try {
      if (authType === 'otp') {
        // Send OTP
        const identifier = loginMethod === 'phone' ? toE164(phone) : email;
        const response = await login(identifier);
        if (response.sessionId) {
          router.push({
            pathname: '/(auth)/otp-verify',
            params: {
              phone: loginMethod === 'phone' ? toE164(phone) : '',
              email: loginMethod === 'email' ? email : '',
              sessionId: response.sessionId,
            },
          });
        }
      } else {
        // Password login
        const identifier = loginMethod === 'phone' ? toE164(phone) : email;
        const response = await login(identifier, password);

        if (response.requiresOtp && response.sessionId) {
          router.push({
            pathname: '/(auth)/otp-verify',
            params: {
              phone: loginMethod === 'phone' ? toE164(phone) : '',
              email: loginMethod === 'email' ? email : '',
              sessionId: response.sessionId,
            },
          });
        } else {
          // Direct login successful
          console.log('Login successful, navigating to home tabs');

          // Offer to enable biometric if available and not yet enabled
          if (biometricAvailable && !biometricEnabled && authType === 'password') {
            const identifier = loginMethod === 'phone' ? toE164(phone) : email;
            Alert.alert(
              `Enable ${biometricType}`,
              `Would you like to use ${biometricType} for faster login next time?`,
              [
                {
                  text: 'Not Now',
                  style: 'cancel',
                  onPress: () => router.replace('/(tabs)/')
                },
                {
                  text: 'Enable',
                  onPress: async () => {
                    const success = await enableBiometric(identifier, password);
                    if (success) {
                      Alert.alert(
                        'Success',
                        `${biometricType} enabled for quick login`,
                        [{ text: 'OK', onPress: () => router.replace('/(tabs)/') }]
                      );
                    } else {
                      router.replace('/(tabs)/');
                    }
                  },
                },
              ]
            );
          } else {
            router.replace('/(tabs)/');
          }
        }
      }
    } catch (err: any) {
      console.error('Login error:', err);
      const errorMessage = err?.response?.data?.detail || err?.message || error || 'Something went wrong. Please try again.';
      Alert.alert('Login Failed', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = () => {
    router.push({
      pathname: '/(auth)/register',
      params: {
        phone: phone ? toE164(phone) : '',
        email: email || '',
      },
    });
  };

  const handleForgotPassword = () => {
    router.push({
      pathname: '/(auth)/reset-password',
      params: {
        phone: phone ? toE164(phone) : '',
        email: email || '',
      },
    });
  };

  if (checkingBiometric) {
    return (
      <View style={styles.container}>
        <LinearGradient
          colors={Gradients.darkBackground}
          style={styles.gradient}
        >
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={theme.primary} />
          </View>
        </LinearGradient>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={Gradients.darkBackground}
        style={styles.gradient}
      >
        <SafeAreaView style={styles.safeArea}>
          {/* Logo Header - Full Width */}
          <View style={styles.logoHeader}>
            {(() => {
              if (tenant?.logo_url) {
                // Construct full URL - API returns relative path
                const baseUrl = process.env.EXPO_PUBLIC_API_URL || 'http://10.0.0.169:5024';
                const fullLogoUrl = tenant.logo_url.startsWith('http')
                  ? tenant.logo_url
                  : `${baseUrl}${tenant.logo_url}`;

                console.log('Tenant logo URL:', fullLogoUrl);

                return (
                  <Image
                    source={{ uri: fullLogoUrl }}
                    style={styles.headerLogo}
                    resizeMode="contain"
                    onError={(e) => {
                      console.log('Tenant logo load error:', e.nativeEvent.error);
                      console.log('Failed URL:', fullLogoUrl);
                    }}
                  />
                );
              }

              return (
                <LinearGradient
                  colors={Gradients.primary}
                  style={styles.defaultLogoGradient}
                >
                  <Ionicons name="leaf" size={60} color="white" />
                </LinearGradient>
              );
            })()}
          </View>

          <KeyboardAvoidingView
            style={styles.keyboardView}
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          >
            <ScrollView
              contentContainerStyle={styles.scrollContent}
              keyboardShouldPersistTaps="handled"
              showsVerticalScrollIndicator={false}
            >
              {/* Decorative gradient circles */}
              <View style={styles.backgroundDecoration}>
                <LinearGradient
                  colors={['rgba(116, 185, 255, 0.1)', 'rgba(139, 233, 253, 0.1)']}
                  style={styles.circleOne}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                />
                <LinearGradient
                  colors={['rgba(255, 107, 157, 0.1)', 'rgba(255, 121, 198, 0.1)']}
                  style={styles.circleTwo}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                />
              </View>

              {/* Welcome Text */}
              <View style={styles.welcomeSection}>
                <Text style={styles.title}>
                  Welcome to {tenant?.display_name || tenant?.name || currentStore?.name || 'WeedGo'}
                </Text>
                <Text style={styles.subtitle}>
                  Sign in to access exclusive deals and track your orders
                </Text>
              </View>

              {/* Login Method Selector */}
              <View style={styles.methodSelector}>
                <TouchableOpacity
                  onPress={() => setLoginMethod('phone')}
                  activeOpacity={0.8}
                  style={styles.methodButtonWrapper}
                >
                  <LinearGradient
                    colors={loginMethod === 'phone' ? Gradients.primary : ['transparent', 'transparent']}
                    style={[
                      styles.methodButton,
                      loginMethod !== 'phone' && styles.methodButtonInactive,
                    ]}
                  >
                    <Ionicons
                      name="call-outline"
                      size={20}
                      color={loginMethod === 'phone' ? 'white' : theme.textSecondary}
                    />
                    <Text style={[
                      styles.methodButtonText,
                      loginMethod === 'phone' && styles.methodButtonTextActive,
                    ]}>
                      Phone
                    </Text>
                  </LinearGradient>
                </TouchableOpacity>

                <TouchableOpacity
                  onPress={() => setLoginMethod('email')}
                  activeOpacity={0.8}
                  style={styles.methodButtonWrapper}
                >
                  <LinearGradient
                    colors={loginMethod === 'email' ? Gradients.secondary : ['transparent', 'transparent']}
                    style={[
                      styles.methodButton,
                      loginMethod !== 'email' && styles.methodButtonInactive,
                    ]}
                  >
                    <Ionicons
                      name="mail-outline"
                      size={20}
                      color={loginMethod === 'email' ? 'white' : theme.textSecondary}
                    />
                    <Text style={[
                      styles.methodButtonText,
                      loginMethod === 'email' && styles.methodButtonTextActive,
                    ]}>
                      Email
                    </Text>
                  </LinearGradient>
                </TouchableOpacity>
              </View>

              {/* Auth Type Selector */}
              <View style={styles.authTypeContainer}>
                <TouchableOpacity
                  style={[
                    styles.authTypeButton,
                    authType === 'otp' && styles.authTypeButtonActive,
                  ]}
                  onPress={() => setAuthType('otp')}
                >
                  <Text style={[
                    styles.authTypeText,
                    authType === 'otp' && styles.authTypeTextActive,
                  ]}>
                    Send OTP Code
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[
                    styles.authTypeButton,
                    authType === 'password' && styles.authTypeButtonActive,
                  ]}
                  onPress={() => setAuthType('password')}
                >
                  <Text style={[
                    styles.authTypeText,
                    authType === 'password' && styles.authTypeTextActive,
                  ]}>
                    Use Password
                  </Text>
                </TouchableOpacity>
              </View>

              {/* Input Fields */}
              <View style={styles.inputContainer}>
                {loginMethod === 'phone' ? (
                  <View style={styles.inputWrapper}>
                    <Ionicons name="call-outline" size={20} color={theme.textSecondary} />
                    <Text style={styles.countryCode}>+1</Text>
                    <TextInput
                      ref={phoneInputRef}
                      style={styles.input}
                      placeholder="(555) 123-4567"
                      placeholderTextColor={theme.textSecondary}
                      value={phone}
                      onChangeText={handlePhoneChange}
                      keyboardType="phone-pad"
                      autoComplete="tel"
                      textContentType="telephoneNumber"
                      maxLength={14}
                      editable={!loading}
                      returnKeyType={authType === 'password' ? 'next' : 'done'}
                      onSubmitEditing={authType === 'password' ?
                        () => passwordInputRef.current?.focus() : handleContinue}
                    />
                  </View>
                ) : (
                  <View style={styles.inputWrapper}>
                    <Ionicons name="mail-outline" size={20} color={theme.textSecondary} />
                    <TextInput
                      ref={emailInputRef}
                      style={styles.input}
                      placeholder="your@email.com"
                      placeholderTextColor={theme.textSecondary}
                      value={email}
                      onChangeText={setEmail}
                      keyboardType="email-address"
                      autoComplete="email"
                      textContentType="emailAddress"
                      autoCapitalize="none"
                      editable={!loading}
                      returnKeyType={authType === 'password' ? 'next' : 'done'}
                      onSubmitEditing={authType === 'password' ?
                        () => passwordInputRef.current?.focus() : handleContinue}
                    />
                  </View>
                )}

                {authType === 'password' && (
                  <View style={styles.inputWrapper}>
                    <Ionicons name="lock-closed-outline" size={20} color={theme.textSecondary} />
                    <TextInput
                      ref={passwordInputRef}
                      style={[styles.input, styles.passwordInput]}
                      placeholder="Enter your password"
                      placeholderTextColor={theme.textSecondary}
                      value={password}
                      onChangeText={setPassword}
                      secureTextEntry={!showPassword}
                      autoComplete="password"
                      textContentType="password"
                      editable={!loading}
                      returnKeyType="done"
                      onSubmitEditing={handleContinue}
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
                )}
              </View>

              {/* Continue Button */}
              <TouchableOpacity
                onPress={handleContinue}
                disabled={loading}
                activeOpacity={0.9}
                style={styles.continueButtonWrapper}
              >
                <LinearGradient
                  colors={loading ? ['#666', '#444'] : Gradients.primary}
                  style={styles.continueButton}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                >
                  {loading ? (
                    <ActivityIndicator color="white" />
                  ) : (
                    <>
                      <Text style={styles.continueButtonText}>
                        {authType === 'otp' ? 'Send Code' : 'Sign In'}
                      </Text>
                      <Ionicons name="arrow-forward" size={20} color="white" />
                    </>
                  )}
                </LinearGradient>
              </TouchableOpacity>

              {/* Forgot Password */}
              {authType === 'password' && (
                <TouchableOpacity
                  style={styles.forgotButton}
                  onPress={handleForgotPassword}
                >
                  <Text style={styles.forgotText}>Forgot password?</Text>
                </TouchableOpacity>
              )}

              {/* Biometric Login Button - Show if enabled */}
              {biometricEnabled && biometricAvailable && savedBiometricEmail && (
                <>
                  <View style={styles.dividerContainer}>
                    <View style={styles.divider} />
                    <Text style={styles.dividerText}>or</Text>
                    <View style={styles.divider} />
                  </View>

                  <TouchableOpacity
                    onPress={handleBiometricLogin}
                    disabled={loading}
                    activeOpacity={0.9}
                    style={styles.biometricButtonWrapper}
                  >
                    <LinearGradient
                      colors={loading ? ['#666', '#444'] : Gradients.purple}
                      style={styles.biometricButton}
                      start={{ x: 0, y: 0 }}
                      end={{ x: 1, y: 1 }}
                    >
                      {loading ? (
                        <ActivityIndicator color="white" />
                      ) : (
                        <>
                          <Ionicons
                            name={biometricType.includes('Face') ? 'scan' : 'finger-print'}
                            size={24}
                            color="white"
                          />
                          <Text style={styles.biometricButtonText}>
                            Sign in with {biometricType}
                          </Text>
                        </>
                      )}
                    </LinearGradient>
                  </TouchableOpacity>

                  <Text style={styles.biometricEmail}>
                    {savedBiometricEmail}
                  </Text>
                </>
              )}

              {/* Alternative Options */}
              <View style={styles.dividerContainer}>
                <View style={styles.divider} />
                <Text style={styles.dividerText}>or</Text>
                <View style={styles.divider} />
              </View>

              {/* Register Button */}
              <TouchableOpacity
                style={styles.registerButton}
                onPress={handleRegister}
                disabled={loading}
              >
                <LinearGradient
                  colors={['rgba(255, 107, 157, 0.1)', 'rgba(255, 121, 198, 0.1)']}
                  style={styles.registerGradient}
                >
                  <Ionicons name="person-add-outline" size={20} color={theme.secondary} />
                  <Text style={styles.registerButtonText}>Create New Account</Text>
                </LinearGradient>
              </TouchableOpacity>

              {/* Skip Login (Guest Mode) */}
              <TouchableOpacity
                style={styles.skipButton}
                onPress={() => router.replace('/(tabs)')}
                disabled={loading}
              >
                <Text style={styles.skipButtonText}>Continue as Guest</Text>
                <Ionicons name="arrow-forward-outline" size={18} color={theme.textSecondary} />
              </TouchableOpacity>

              {/* Terms */}
              <Text style={styles.terms}>
                By continuing, you agree to {tenant?.display_name || tenant?.name || 'our'}{' '}
                <Text style={styles.link}>Terms of Service</Text> and{' '}
                <Text style={styles.link}>Privacy Policy</Text>
              </Text>
            </ScrollView>
          </KeyboardAvoidingView>
        </SafeAreaView>
      </LinearGradient>
    </View>
  );
}

const createStyles = (theme: any, isDark: boolean) => StyleSheet.create({
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
    paddingTop: 0,
    paddingBottom: 50,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  backgroundDecoration: {
    position: 'absolute',
    width: '120%',
    height: '100%',
    left: '-10%',
  },
  circleOne: {
    position: 'absolute',
    width: 300,
    height: 300,
    borderRadius: 150,
    top: -150,
    right: -100,
  },
  circleTwo: {
    position: 'absolute',
    width: 250,
    height: 250,
    borderRadius: 125,
    bottom: -100,
    left: -80,
  },
  logoHeader: {
    width: '100%',
    height: 120,
    backgroundColor: 'transparent',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingTop: 10,
    paddingBottom: 20,
  },
  headerLogo: {
    width: '100%',
    height: '100%',
    maxHeight: 80,
  },
  defaultLogoGradient: {
    width: 100,
    height: 100,
    borderRadius: 50,
    justifyContent: 'center',
    alignItems: 'center',
    ...Shadows.colorful,
  },
  welcomeSection: {
    alignItems: 'center',
    marginBottom: 40,
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    color: theme.text,
    marginBottom: 12,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: theme.textSecondary,
    textAlign: 'center',
    paddingHorizontal: 20,
    lineHeight: 22,
  },
  methodSelector: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 12,
    marginBottom: 20,
  },
  methodButtonWrapper: {
    flex: 1,
    maxWidth: 150,
  },
  methodButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: BorderRadius.xl,
    gap: 8,
    ...Shadows.small,
  },
  methodButtonInactive: {
    backgroundColor: theme.glass,
    borderWidth: 1,
    borderColor: theme.glassBorder,
  },
  methodButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.textSecondary,
  },
  methodButtonTextActive: {
    color: 'white',
  },
  authTypeContainer: {
    flexDirection: 'row',
    backgroundColor: theme.glass,
    borderRadius: BorderRadius.xl,
    padding: 4,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: theme.glassBorder,
  },
  authTypeButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: BorderRadius.lg,
    alignItems: 'center',
  },
  authTypeButtonActive: {
    backgroundColor: theme.surface,
    ...Shadows.small,
  },
  authTypeText: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.textSecondary,
  },
  authTypeTextActive: {
    color: theme.primary,
  },
  inputContainer: {
    gap: 16,
    marginBottom: 24,
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
  continueButtonWrapper: {
    width: '100%',
    marginBottom: 16,
  },
  continueButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 56,
    borderRadius: BorderRadius.xxl,
    gap: 8,
    ...Shadows.colorful,
  },
  continueButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: '700',
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 3,
  },
  forgotButton: {
    alignSelf: 'center',
    marginBottom: 20,
  },
  forgotText: {
    color: theme.primary,
    fontSize: 14,
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
    backgroundColor: theme.glassBorder,
  },
  dividerText: {
    color: theme.textSecondary,
    paddingHorizontal: 16,
    fontSize: 14,
  },
  registerButton: {
    width: '100%',
    marginBottom: 16,
  },
  registerGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: BorderRadius.xxl,
    gap: 8,
    borderWidth: 1,
    borderColor: theme.glassBorder,
  },
  registerButtonText: {
    color: theme.secondary,
    fontSize: 16,
    fontWeight: '600',
  },
  skipButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    gap: 8,
  },
  skipButtonText: {
    color: theme.textSecondary,
    fontSize: 14,
    fontWeight: '500',
  },
  terms: {
    marginTop: 24,
    fontSize: 12,
    color: theme.textSecondary,
    textAlign: 'center',
    lineHeight: 18,
  },
  link: {
    color: theme.primary,
    textDecorationLine: 'underline',
  },
  biometricButtonWrapper: {
    width: '100%',
    marginBottom: 8,
  },
  biometricButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 56,
    borderRadius: BorderRadius.xxl,
    gap: 12,
    ...Shadows.colorful,
  },
  biometricButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: '700',
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 3,
  },
  biometricEmail: {
    fontSize: 14,
    color: theme.textSecondary,
    textAlign: 'center',
    marginBottom: 16,
  },
});