import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Switch,
  Modal,
  Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import DateTimePicker from '@react-native-community/datetimepicker';
import { useAuthStore } from '@/stores/authStore';
import { useTenantStore } from '@/stores/tenantStore';
import useStoreStore from '@/stores/storeStore';
import { Colors, Gradients, BorderRadius } from '@/constants/Colors';
import { TERMS_OF_SERVICE, PRIVACY_POLICY } from '@/constants/LegalContent';

interface RegistrationData {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  confirmPassword: string;
  dateOfBirth: Date | null;
  acceptTerms: boolean;
  acceptPrivacy: boolean;
  acceptMarketing: boolean;
  referralCode: string;
  enableVoiceAuth: boolean;
}

export default function RegisterScreen() {
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [showTermsModal, setShowTermsModal] = useState(false);
  const [showPrivacyModal, setShowPrivacyModal] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState({ score: 0, text: '', color: '' });

  const [formData, setFormData] = useState<RegistrationData>({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: '',
    dateOfBirth: null,
    acceptTerms: false,
    acceptPrivacy: false,
    acceptMarketing: false,
    referralCode: '',
    enableVoiceAuth: false,
  });

  const phoneRef = useRef<TextInput>(null);
  const firstNameRef = useRef<TextInput>(null);
  const lastNameRef = useRef<TextInput>(null);
  const emailRef = useRef<TextInput>(null);
  const passwordRef = useRef<TextInput>(null);
  const confirmPasswordRef = useRef<TextInput>(null);
  const referralRef = useRef<TextInput>(null);

  const { phone } = useLocalSearchParams<{ phone: string }>();
  const router = useRouter();
  const { register, error, clearError } = useAuthStore();
  const { tenant, loadTenant } = useTenantStore();
  const { currentStore, loadStores } = useStoreStore();

  const totalSteps = 4;

  // Load store and tenant info on mount
  useEffect(() => {
    if (!currentStore) {
      loadStores();
    }
    if (!tenant) {
      loadTenant();
    }
  }, []);

  // Calculate minimum age (19 years ago from today)
  const getMinimumDate = () => {
    const today = new Date();
    const minDate = new Date(today.getFullYear() - 19, today.getMonth(), today.getDate());
    return minDate;
  };

  // Calculate maximum date for date picker (120 years ago)
  const getMaximumDate = () => {
    const today = new Date();
    return new Date(today.getFullYear() - 120, 0, 1);
  };

  const updateFormData = (field: keyof RegistrationData, value: any) => {
    if (error) clearError();
    setFormData(prev => ({ ...prev, [field]: value }));

    // Real-time password strength check
    if (field === 'password') {
      checkPasswordStrength(value as string);
    }
  };

  const checkPasswordStrength = (password: string) => {
    let score = 0;
    let text = '';
    let color = Colors.dark.error;

    if (password.length >= 8) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[a-z]/.test(password)) score++;
    if (/\d/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;

    if (score === 0 || password.length === 0) {
      text = '';
      color = Colors.dark.textSecondary;
    } else if (score < 3) {
      text = 'Weak';
      color = Colors.dark.error;
    } else if (score === 3) {
      text = 'Fair';
      color = '#FF9500';
    } else if (score === 4) {
      text = 'Good';
      color = '#FFD93D';
    } else {
      text = 'Strong';
      color = Colors.dark.primary;
    }

    setPasswordStrength({ score, text, color });
  };

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validatePassword = (password: string): { valid: boolean; message?: string } => {
    if (password.length < 8) {
      return { valid: false, message: 'Password must be at least 8 characters' };
    }
    const hasUpper = /[A-Z]/.test(password);
    const hasLower = /[a-z]/.test(password);
    const hasNumber = /\d/.test(password);

    if (!hasUpper || !hasLower || !hasNumber) {
      return { valid: false, message: 'Password must contain uppercase, lowercase, and number' };
    }
    return { valid: true };
  };

  const validateAge = (dob: Date): { valid: boolean; message?: string } => {
    const today = new Date();
    const age = today.getFullYear() - dob.getFullYear();
    const monthDiff = today.getMonth() - dob.getMonth();

    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < dob.getDate())) {
      if (age - 1 < 19) {
        return { valid: false, message: 'You must be 19 or older to register' };
      }
    } else if (age < 19) {
      return { valid: false, message: 'You must be 19 or older to register' };
    }
    return { valid: true };
  };

  const validateStep = (step: number): boolean => {
    switch (step) {
      case 1:
        if (!formData.firstName.trim() || !formData.lastName.trim()) {
          Alert.alert('Required Fields', 'Please enter your first and last name');
          return false;
        }
        if (formData.email && !validateEmail(formData.email)) {
          Alert.alert('Invalid Email', 'Please enter a valid email address');
          return false;
        }
        return true;

      case 2:
        const passwordCheck = validatePassword(formData.password);
        if (!passwordCheck.valid) {
          Alert.alert('Invalid Password', passwordCheck.message);
          return false;
        }
        if (formData.password !== formData.confirmPassword) {
          Alert.alert('Password Mismatch', 'Passwords do not match');
          return false;
        }
        if (!formData.dateOfBirth) {
          Alert.alert('Required Field', 'Please select your date of birth');
          return false;
        }
        const ageCheck = validateAge(formData.dateOfBirth);
        if (!ageCheck.valid) {
          Alert.alert('Age Verification', ageCheck.message);
          return false;
        }
        return true;

      case 3:
        if (!formData.acceptTerms || !formData.acceptPrivacy) {
          Alert.alert('Required', 'You must accept Terms of Service and Privacy Policy to continue');
          return false;
        }
        return true;

      default:
        return true;
    }
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      if (currentStep < totalSteps) {
        setCurrentStep(currentStep + 1);
      } else {
        handleRegister();
      }
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    } else {
      router.back();
    }
  };

  const handleRegister = async () => {
    if (!phone) {
      Alert.alert('Error', 'Phone number is required. Please go back and enter your phone number.');
      return;
    }

    setLoading(true);

    try {
      const response = await register({
        phone,
        firstName: formData.firstName.trim(),
        lastName: formData.lastName.trim(),
        email: formData.email.trim() || undefined,
        password: formData.password,
        dateOfBirth: formData.dateOfBirth?.toISOString().split('T')[0],
        acceptTerms: formData.acceptTerms,
        acceptPrivacy: formData.acceptPrivacy,
        acceptMarketing: formData.acceptMarketing,
        referralCode: formData.referralCode.trim() || undefined,
        enableVoiceAuth: formData.enableVoiceAuth,
      });

      if (response.success) {
        // Navigate to main app or OTP verification if needed
        router.replace('/(tabs)');
      }
    } catch (err: any) {
      const friendlyMessage = err.message?.includes('phone')
        ? 'There was an issue with your phone number. Please try again.'
        : err.message?.includes('email')
        ? 'This email is already registered. Please use a different email or sign in.'
        : err.message || 'Unable to create account. Please check your information and try again.';

      Alert.alert('Registration Failed', friendlyMessage);
    } finally {
      setLoading(false);
    }
  };

  const onDateChange = (event: any, selectedDate?: Date) => {
    // Close the picker on Android immediately, on iOS keep it open until user confirms
    if (Platform.OS === 'android') {
      setShowDatePicker(false);
    }
    if (selectedDate) {
      updateFormData('dateOfBirth', selectedDate);
      // Close picker after selection on iOS
      if (Platform.OS === 'ios') {
        setShowDatePicker(false);
      }
    }
  };

  const formatDate = (date: Date | null): string => {
    if (!date) return '';
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  };

  const renderProgressStepper = () => (
    <View style={styles.stepperContainer}>
      {[1, 2, 3, 4].map((step) => (
        <View key={step} style={styles.stepItem}>
          <View style={[
            styles.stepCircle,
            step <= currentStep && styles.stepCircleActive,
          ]}>
            {step < currentStep ? (
              <Ionicons name="checkmark" size={16} color="#fff" />
            ) : (
              <Text style={[
                styles.stepNumber,
                step <= currentStep && styles.stepNumberActive,
              ]}>{step}</Text>
            )}
          </View>
          {step < 4 && (
            <View style={[
              styles.stepLine,
              step < currentStep && styles.stepLineActive,
            ]} />
          )}
        </View>
      ))}
    </View>
  );

  const renderStep1 = () => (
    <View style={styles.stepContent}>
      <Text style={styles.stepTitle}>Personal Information</Text>
      <Text style={styles.stepSubtitle}>Let's start with your basic details</Text>

      {/* Phone Number */}
      <View style={styles.inputContainer}>
        <Text style={styles.inputLabel}>
          Phone Number <Text style={styles.required}>*</Text>
        </Text>
        <View style={styles.inputWrapper}>
          <TextInput
            ref={phoneRef}
            style={styles.input}
            placeholder="Enter your phone number"
            placeholderTextColor={Colors.dark.textSecondary}
            value={phone || ''}
            onChangeText={(text) => {
              // Update phone state in parent navigation params
              // Note: This updates the local phone value
              router.setParams({ phone: text });
            }}
            keyboardType="phone-pad"
            textContentType="telephoneNumber"
            autoComplete="tel"
            returnKeyType="next"
            onSubmitEditing={() => firstNameRef.current?.focus()}
            editable={!loading}
          />
        </View>
      </View>

      {/* First Name */}
      <View style={styles.inputContainer}>
        <Text style={styles.inputLabel}>
          First Name <Text style={styles.required}>*</Text>
        </Text>
        <View style={styles.inputWrapper}>
          <TextInput
            ref={firstNameRef}
            style={styles.input}
            placeholder="Enter your first name"
            placeholderTextColor={Colors.dark.textSecondary}
            value={formData.firstName}
            onChangeText={(text) => updateFormData('firstName', text)}
            autoComplete="given-name"
            textContentType="givenName"
            autoCapitalize="words"
            returnKeyType="next"
            onSubmitEditing={() => lastNameRef.current?.focus()}
            editable={!loading}
          />
        </View>
      </View>

      {/* Last Name */}
      <View style={styles.inputContainer}>
        <Text style={styles.inputLabel}>
          Last Name <Text style={styles.required}>*</Text>
        </Text>
        <View style={styles.inputWrapper}>
          <TextInput
            ref={lastNameRef}
            style={styles.input}
            placeholder="Enter your last name"
            placeholderTextColor={Colors.dark.textSecondary}
            value={formData.lastName}
            onChangeText={(text) => updateFormData('lastName', text)}
            autoComplete="family-name"
            textContentType="familyName"
            autoCapitalize="words"
            returnKeyType="next"
            onSubmitEditing={() => emailRef.current?.focus()}
            editable={!loading}
          />
        </View>
      </View>

      {/* Email */}
      <View style={styles.inputContainer}>
        <Text style={styles.inputLabel}>
          Email <Text style={styles.optional}>(Optional)</Text>
        </Text>
        <View style={styles.inputWrapper}>
          <TextInput
            ref={emailRef}
            style={styles.input}
            placeholder="your@email.com"
            placeholderTextColor={Colors.dark.textSecondary}
            value={formData.email}
            onChangeText={(text) => updateFormData('email', text)}
            autoComplete="email"
            textContentType="emailAddress"
            keyboardType="email-address"
            autoCapitalize="none"
            returnKeyType="done"
            editable={!loading}
          />
        </View>
        <Text style={styles.helpText}>
          For order confirmations and account recovery
        </Text>
      </View>
    </View>
  );

  const renderStep2 = () => (
    <View style={styles.stepContent}>
      <Text style={styles.stepTitle}>Security & Verification</Text>
      <Text style={styles.stepSubtitle}>Create a secure password and verify your age</Text>

      {/* Password */}
      <View style={styles.inputContainer}>
        <Text style={styles.inputLabel}>
          Password <Text style={styles.required}>*</Text>
        </Text>
        <View style={styles.inputWrapper}>
          <TextInput
            ref={passwordRef}
            style={styles.inputWithIcon}
            placeholder="Create a strong password"
            placeholderTextColor={Colors.dark.textSecondary}
            value={formData.password}
            onChangeText={(text) => updateFormData('password', text)}
            secureTextEntry={!showPassword}
            autoComplete="password-new"
            textContentType="newPassword"
            returnKeyType="next"
            onSubmitEditing={() => confirmPasswordRef.current?.focus()}
            editable={!loading}
          />
          <TouchableOpacity
            style={styles.eyeIcon}
            onPress={() => setShowPassword(!showPassword)}
          >
            <Ionicons
              name={showPassword ? 'eye-off' : 'eye'}
              size={20}
              color={Colors.dark.textSecondary}
            />
          </TouchableOpacity>
        </View>
        {formData.password.length > 0 && (
          <View style={styles.passwordStrengthContainer}>
            <View style={styles.passwordStrengthBar}>
              <View
                style={[
                  styles.passwordStrengthFill,
                  { width: `${(passwordStrength.score / 5) * 100}%`, backgroundColor: passwordStrength.color }
                ]}
              />
            </View>
            <Text style={[styles.passwordStrengthText, { color: passwordStrength.color }]}>
              {passwordStrength.text}
            </Text>
          </View>
        )}
        <Text style={styles.helpText}>
          Minimum 8 characters with uppercase, lowercase, and number
        </Text>
      </View>

      {/* Confirm Password */}
      <View style={styles.inputContainer}>
        <Text style={styles.inputLabel}>
          Confirm Password <Text style={styles.required}>*</Text>
        </Text>
        <View style={styles.inputWrapper}>
          <TextInput
            ref={confirmPasswordRef}
            style={styles.inputWithIcon}
            placeholder="Confirm your password"
            placeholderTextColor={Colors.dark.textSecondary}
            value={formData.confirmPassword}
            onChangeText={(text) => updateFormData('confirmPassword', text)}
            secureTextEntry={!showConfirmPassword}
            autoComplete="password-new"
            textContentType="newPassword"
            returnKeyType="done"
            editable={!loading}
          />
          <TouchableOpacity
            style={styles.eyeIcon}
            onPress={() => setShowConfirmPassword(!showConfirmPassword)}
          >
            <Ionicons
              name={showConfirmPassword ? 'eye-off' : 'eye'}
              size={20}
              color={Colors.dark.textSecondary}
            />
          </TouchableOpacity>
        </View>
        {formData.confirmPassword.length > 0 && formData.password !== formData.confirmPassword && (
          <Text style={styles.errorHelpText}>Passwords do not match</Text>
        )}
        {formData.confirmPassword.length > 0 && formData.password === formData.confirmPassword && (
          <Text style={styles.successHelpText}>Passwords match</Text>
        )}
      </View>

      {/* Date of Birth */}
      <View style={styles.inputContainer}>
        <Text style={styles.inputLabel}>
          Date of Birth <Text style={styles.required}>*</Text>
        </Text>
        <TouchableOpacity
          style={styles.inputWrapper}
          onPress={() => setShowDatePicker(true)}
          disabled={loading}
        >
          <View style={styles.dateInputContent}>
            <Text style={[styles.dateText, !formData.dateOfBirth && styles.datePlaceholder]}>
              {formData.dateOfBirth ? formatDate(formData.dateOfBirth) : 'Select your date of birth'}
            </Text>
            <Ionicons name="calendar-outline" size={20} color={Colors.dark.textSecondary} />
          </View>
        </TouchableOpacity>
        <Text style={styles.helpText}>
          You must be 19 or older to register
        </Text>
      </View>

      {showDatePicker && (
        <DateTimePicker
          value={formData.dateOfBirth || getMinimumDate()}
          mode="date"
          display={Platform.OS === 'ios' ? 'spinner' : 'default'}
          onChange={onDateChange}
          maximumDate={getMinimumDate()}
          minimumDate={getMaximumDate()}
        />
      )}
    </View>
  );

  const renderStep3 = () => (
    <View style={styles.stepContent}>
      <Text style={styles.stepTitle}>Legal & Preferences</Text>
      <Text style={styles.stepSubtitle}>Review and accept our terms</Text>

      {/* Terms & Privacy */}
      <View style={styles.checkboxContainer}>
        <TouchableOpacity
          style={styles.checkboxRow}
          onPress={() => updateFormData('acceptTerms', !formData.acceptTerms)}
        >
          <View style={[styles.checkbox, formData.acceptTerms && styles.checkboxActive]}>
            {formData.acceptTerms && (
              <Ionicons name="checkmark" size={16} color="#fff" />
            )}
          </View>
          <Text style={styles.checkboxLabel}>
            I accept the{' '}
            <Text
              style={styles.link}
              onPress={(e) => {
                e.stopPropagation();
                setShowTermsModal(true);
              }}
            >
              Terms of Service
            </Text>
            <Text style={styles.required}> *</Text>
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.checkboxRow}
          onPress={() => updateFormData('acceptPrivacy', !formData.acceptPrivacy)}
        >
          <View style={[styles.checkbox, formData.acceptPrivacy && styles.checkboxActive]}>
            {formData.acceptPrivacy && (
              <Ionicons name="checkmark" size={16} color="#fff" />
            )}
          </View>
          <Text style={styles.checkboxLabel}>
            I accept the{' '}
            <Text
              style={styles.link}
              onPress={(e) => {
                e.stopPropagation();
                setShowPrivacyModal(true);
              }}
            >
              Privacy Policy
            </Text>
            <Text style={styles.required}> *</Text>
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.checkboxRow}
          onPress={() => updateFormData('acceptMarketing', !formData.acceptMarketing)}
        >
          <View style={[styles.checkbox, formData.acceptMarketing && styles.checkboxActive]}>
            {formData.acceptMarketing && (
              <Ionicons name="checkmark" size={16} color="#fff" />
            )}
          </View>
          <Text style={styles.checkboxLabel}>
            I want to receive marketing emails and special offers
          </Text>
        </TouchableOpacity>
      </View>

      {/* Referral Code */}
      <View style={styles.inputContainer}>
        <Text style={styles.inputLabel}>
          Referral Code <Text style={styles.optional}>(Optional)</Text>
        </Text>
        <View style={styles.inputWrapper}>
          <TextInput
            ref={referralRef}
            style={styles.input}
            placeholder="Enter referral code"
            placeholderTextColor={Colors.dark.textSecondary}
            value={formData.referralCode}
            onChangeText={(text) => updateFormData('referralCode', text.toUpperCase())}
            autoCapitalize="characters"
            returnKeyType="done"
            editable={!loading}
          />
        </View>
        <Text style={styles.helpText}>
          Have a referral code? Enter it for special rewards!
        </Text>
      </View>
    </View>
  );

  const renderStep4 = () => (
    <View style={styles.stepContent}>
      <Text style={styles.stepTitle}>Voice Authentication</Text>
      <Text style={styles.stepSubtitle}>Optional: Set up voice login for faster access</Text>

      <View style={styles.voiceContainer}>
        <LinearGradient
          colors={Gradients.purple}
          style={styles.voiceCard}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        >
          <Ionicons name="mic" size={48} color="#fff" />
          <Text style={styles.voiceTitle}>Voice Authentication</Text>
          <Text style={styles.voiceDescription}>
            Use your voice to log in quickly and securely
          </Text>

          <View style={styles.voiceToggle}>
            <Text style={styles.voiceToggleLabel}>Enable Voice Auth</Text>
            <Switch
              value={formData.enableVoiceAuth}
              onValueChange={(value) => updateFormData('enableVoiceAuth', value)}
              trackColor={{ false: Colors.dark.border, true: Colors.dark.primary }}
              thumbColor="#fff"
            />
          </View>
        </LinearGradient>

        <Text style={styles.voiceNote}>
          You can skip this step and set it up later in settings
        </Text>
      </View>
    </View>
  );

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 1:
        return renderStep1();
      case 2:
        return renderStep2();
      case 3:
        return renderStep3();
      case 4:
        return renderStep4();
      default:
        return null;
    }
  };

  // Determine logo URL
  const fullLogoUrl = (() => {
    if (tenant?.logo_url) {
      // Construct full URL - API returns relative path
      const baseUrl = process.env.EXPO_PUBLIC_API_URL || 'http://192.168.1.140:5024';
      const logoUrl = tenant.logo_url.startsWith('http')
        ? tenant.logo_url
        : `${baseUrl}${tenant.logo_url}`;

      console.log('Tenant logo URL:', logoUrl);
      return logoUrl;
    }
    return null;
  })();

  return (
    <LinearGradient
      colors={Gradients.darkBackground}
      style={styles.gradient}
    >
      <SafeAreaView style={styles.container}>
        {/* Header with Logo */}
        <View style={styles.headerContainer}>
          {(() => {
            if (fullLogoUrl) {
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
                <Ionicons name="leaf" size={40} color="white" />
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
            {/* Welcome Section */}
            <View style={styles.welcomeSection}>
              <Text style={styles.title}>Create Account</Text>
              <Text style={styles.subtitle}>
                Join {tenant?.display_name || tenant?.name || currentStore?.name || 'WeedGo'} and start shopping
              </Text>
            </View>

            {/* Step Info */}
            <View style={styles.stepInfo}>
              <Text style={styles.stepInfoText}>Step {currentStep} of {totalSteps}</Text>
            </View>

            {/* Progress Stepper */}
            {renderProgressStepper()}

            {/* Current Step Content */}
            {renderCurrentStep()}

            {/* Navigation Buttons */}
            <View style={styles.buttonContainer}>
              <TouchableOpacity
                style={styles.backNavButton}
                onPress={handleBack}
                disabled={loading}
              >
                <Ionicons name="arrow-back" size={20} color={Colors.dark.primary} />
                <Text style={styles.backNavButtonText}>Back</Text>
              </TouchableOpacity>

              <LinearGradient
                colors={Gradients.primary}
                style={styles.nextButton}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
              >
                <TouchableOpacity
                  style={styles.nextButtonInner}
                  onPress={handleNext}
                  disabled={loading}
                >
                  {loading ? (
                    <ActivityIndicator color="white" />
                  ) : (
                    <>
                      <Text style={styles.nextButtonText}>
                        {currentStep === totalSteps ? 'Create Account' : 'Continue'}
                      </Text>
                      <Ionicons name="arrow-forward" size={20} color="#fff" />
                    </>
                  )}
                </TouchableOpacity>
              </LinearGradient>
            </View>
          </ScrollView>
        </KeyboardAvoidingView>

        {/* Terms Modal */}
        <Modal
          visible={showTermsModal}
          animationType="slide"
          presentationStyle="pageSheet"
          onRequestClose={() => setShowTermsModal(false)}
        >
          <SafeAreaView style={styles.modalContainer}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Terms of Service</Text>
              <TouchableOpacity onPress={() => setShowTermsModal(false)}>
                <Ionicons name="close" size={28} color={Colors.dark.text} />
              </TouchableOpacity>
            </View>
            <ScrollView style={styles.modalContent}>
              <Text style={styles.modalText}>
                {TERMS_OF_SERVICE}
              </Text>
            </ScrollView>
            <TouchableOpacity
              style={styles.modalAcceptButton}
              onPress={() => {
                updateFormData('acceptTerms', true);
                setShowTermsModal(false);
              }}
            >
              <Text style={styles.modalAcceptButtonText}>Accept Terms</Text>
            </TouchableOpacity>
          </SafeAreaView>
        </Modal>

        {/* Privacy Modal */}
        <Modal
          visible={showPrivacyModal}
          animationType="slide"
          presentationStyle="pageSheet"
          onRequestClose={() => setShowPrivacyModal(false)}
        >
          <SafeAreaView style={styles.modalContainer}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Privacy Policy</Text>
              <TouchableOpacity onPress={() => setShowPrivacyModal(false)}>
                <Ionicons name="close" size={28} color={Colors.dark.text} />
              </TouchableOpacity>
            </View>
            <ScrollView style={styles.modalContent}>
              <Text style={styles.modalText}>
                {PRIVACY_POLICY}
              </Text>
            </ScrollView>
            <TouchableOpacity
              style={styles.modalAcceptButton}
              onPress={() => {
                updateFormData('acceptPrivacy', true);
                setShowPrivacyModal(false);
              }}
            >
              <Text style={styles.modalAcceptButtonText}>Accept Privacy Policy</Text>
            </TouchableOpacity>
          </SafeAreaView>
        </Modal>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  gradient: {
    flex: 1,
  },
  container: {
    flex: 1,
  },
  headerContainer: {
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
  },
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    padding: 24,
  },
  stepInfo: {
    alignItems: 'center',
    marginBottom: 16,
  },
  stepInfoText: {
    fontSize: 14,
    color: Colors.dark.textSecondary,
    fontWeight: '500',
  },

  // Progress Stepper
  stepperContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 32,
    paddingHorizontal: 20,
  },
  stepItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  stepCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.dark.glass,
    borderWidth: 2,
    borderColor: Colors.dark.glassBorder,
    justifyContent: 'center',
    alignItems: 'center',
  },
  stepCircleActive: {
    backgroundColor: Colors.dark.primary,
    borderColor: Colors.dark.primary,
  },
  stepNumber: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.dark.textSecondary,
  },
  stepNumberActive: {
    color: '#fff',
  },
  stepLine: {
    width: 40,
    height: 2,
    backgroundColor: Colors.dark.glassBorder,
    marginHorizontal: 4,
  },
  stepLineActive: {
    backgroundColor: Colors.dark.primary,
  },

  // Step Content
  stepContent: {
    marginBottom: 24,
  },
  stepTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: Colors.dark.text,
    marginBottom: 8,
  },
  stepSubtitle: {
    fontSize: 14,
    color: Colors.dark.textSecondary,
    marginBottom: 24,
  },


  // Input Styles
  inputContainer: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.dark.text,
    marginBottom: 8,
  },
  required: {
    color: Colors.dark.error,
  },
  optional: {
    color: Colors.dark.textSecondary,
    fontWeight: '400',
  },
  inputWrapper: {
    backgroundColor: Colors.dark.glass,
    borderWidth: 1,
    borderColor: Colors.dark.glassBorder,
    borderRadius: BorderRadius.lg,
    position: 'relative',
  },
  input: {
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    color: Colors.dark.text,
  },
  inputWithIcon: {
    paddingHorizontal: 16,
    paddingVertical: 14,
    paddingRight: 48,
    fontSize: 16,
    color: Colors.dark.text,
  },
  eyeIcon: {
    position: 'absolute',
    right: 16,
    top: 0,
    bottom: 0,
    justifyContent: 'center',
  },
  helpText: {
    fontSize: 12,
    color: Colors.dark.textSecondary,
    marginTop: 6,
    paddingHorizontal: 4,
  },
  errorHelpText: {
    fontSize: 12,
    color: Colors.dark.error,
    marginTop: 6,
    paddingHorizontal: 4,
  },
  successHelpText: {
    fontSize: 12,
    color: Colors.dark.primary,
    marginTop: 6,
    paddingHorizontal: 4,
  },

  // Password Strength
  passwordStrengthContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
    paddingHorizontal: 4,
  },
  passwordStrengthBar: {
    flex: 1,
    height: 4,
    backgroundColor: Colors.dark.glassBorder,
    borderRadius: 2,
    marginRight: 12,
    overflow: 'hidden',
  },
  passwordStrengthFill: {
    height: '100%',
    borderRadius: 2,
  },
  passwordStrengthText: {
    fontSize: 12,
    fontWeight: '600',
  },

  // Date Picker
  dateInputContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  dateText: {
    fontSize: 16,
    color: Colors.dark.text,
  },
  datePlaceholder: {
    color: Colors.dark.textSecondary,
  },

  // Checkbox Styles
  checkboxContainer: {
    marginBottom: 24,
  },
  checkboxRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: Colors.dark.glassBorder,
    backgroundColor: Colors.dark.glass,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  checkboxActive: {
    backgroundColor: Colors.dark.primary,
    borderColor: Colors.dark.primary,
  },
  checkboxLabel: {
    fontSize: 14,
    color: Colors.dark.text,
    flex: 1,
  },
  link: {
    color: Colors.dark.primary,
    textDecorationLine: 'underline',
  },

  // Voice Auth
  voiceContainer: {
    alignItems: 'center',
  },
  voiceCard: {
    width: '100%',
    padding: 32,
    borderRadius: BorderRadius.xl,
    alignItems: 'center',
    marginBottom: 16,
  },
  voiceTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#fff',
    marginTop: 16,
    marginBottom: 8,
  },
  voiceDescription: {
    fontSize: 14,
    color: '#fff',
    textAlign: 'center',
    opacity: 0.9,
    marginBottom: 24,
  },
  voiceToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    width: '100%',
    paddingHorizontal: 20,
  },
  voiceToggleLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  voiceNote: {
    fontSize: 12,
    color: Colors.dark.textSecondary,
    textAlign: 'center',
  },

  // Navigation Buttons
  buttonContainer: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
  },
  backNavButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: BorderRadius.lg,
    backgroundColor: Colors.dark.glass,
    borderWidth: 1,
    borderColor: Colors.dark.glassBorder,
    gap: 8,
    flex: 1,
  },
  backNavButtonText: {
    fontSize: 16,
    color: Colors.dark.primary,
    fontWeight: '600',
  },
  nextButton: {
    flex: 2,
    borderRadius: BorderRadius.lg,
    overflow: 'hidden',
  },
  nextButtonInner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    gap: 8,
  },
  nextButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },

  // Modal Styles
  modalContainer: {
    flex: 1,
    backgroundColor: Colors.dark.background,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: Colors.dark.border,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: Colors.dark.text,
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },
  modalText: {
    fontSize: 14,
    lineHeight: 22,
    color: Colors.dark.text,
  },
  modalAcceptButton: {
    margin: 20,
    padding: 16,
    backgroundColor: Colors.dark.primary,
    borderRadius: BorderRadius.lg,
    alignItems: 'center',
  },
  modalAcceptButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },

  // Welcome Section Styles
  welcomeSection: {
    alignItems: 'center',
    marginBottom: 40,
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    color: Colors.dark.text,
    marginBottom: 12,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: Colors.dark.textSecondary,
    textAlign: 'center',
    paddingHorizontal: 20,
    lineHeight: 22,
  },
});
