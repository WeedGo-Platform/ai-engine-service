import React, { useState, useRef } from 'react';
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
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuthStore } from '@/stores/authStore';
import { Colors } from '@/constants/Colors';
import { getDisplayPhone } from '@/utils/phoneFormat';

export default function RegisterScreen() {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);

  const lastNameRef = useRef<TextInput>(null);
  const emailRef = useRef<TextInput>(null);

  const { phone } = useLocalSearchParams<{ phone: string }>();
  const router = useRouter();
  const { register, error, clearError } = useAuthStore();

  const handleRegister = async () => {
    // Validate inputs
    if (!firstName.trim() || !lastName.trim()) {
      Alert.alert('Required Fields', 'Please enter your first and last name');
      return;
    }

    if (email && !validateEmail(email)) {
      Alert.alert('Invalid Email', 'Please enter a valid email address');
      return;
    }

    setLoading(true);

    try {
      const response = await register({
        phone,
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        email: email.trim() || undefined,
      });

      if (response.sessionId) {
        // Navigate to OTP verification
        router.replace({
          pathname: '/(auth)/otp-verify',
          params: {
            phone,
            sessionId: response.sessionId,
          },
        });
      }
    } catch (err) {
      Alert.alert(
        'Registration Failed',
        error || 'Unable to create account. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleInputChange = (setter: (value: string) => void) => (text: string) => {
    if (error) clearError();
    setter(text);
  };

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
          {/* Header */}
          <View style={styles.header}>
            <View style={styles.iconContainer}>
              <Ionicons name="person-add" size={60} color={Colors.light.primary} />
            </View>
            <Text style={styles.title}>Create Your Account</Text>
            <Text style={styles.subtitle}>
              Set up your WeedGo profile to get started
            </Text>
          </View>

          {/* Phone Display */}
          <View style={styles.phoneDisplay}>
            <Ionicons name="call" size={20} color={Colors.light.gray} />
            <Text style={styles.phoneText}>{getDisplayPhone(phone, true)}</Text>
            <Ionicons name="checkmark-circle" size={20} color={Colors.light.success} />
          </View>

          {/* Form */}
          <View style={styles.form}>
            {/* First Name */}
            <View style={styles.inputContainer}>
              <Text style={styles.inputLabel}>
                First Name <Text style={styles.required}>*</Text>
              </Text>
              <TextInput
                style={styles.input}
                placeholder="Enter your first name"
                placeholderTextColor={Colors.light.gray}
                value={firstName}
                onChangeText={handleInputChange(setFirstName)}
                autoComplete="given-name"
                textContentType="givenName"
                autoCapitalize="words"
                returnKeyType="next"
                onSubmitEditing={() => lastNameRef.current?.focus()}
                editable={!loading}
              />
            </View>

            {/* Last Name */}
            <View style={styles.inputContainer}>
              <Text style={styles.inputLabel}>
                Last Name <Text style={styles.required}>*</Text>
              </Text>
              <TextInput
                ref={lastNameRef}
                style={styles.input}
                placeholder="Enter your last name"
                placeholderTextColor={Colors.light.gray}
                value={lastName}
                onChangeText={handleInputChange(setLastName)}
                autoComplete="family-name"
                textContentType="familyName"
                autoCapitalize="words"
                returnKeyType="next"
                onSubmitEditing={() => emailRef.current?.focus()}
                editable={!loading}
              />
            </View>

            {/* Email (Optional) */}
            <View style={styles.inputContainer}>
              <Text style={styles.inputLabel}>
                Email <Text style={styles.optional}>(Optional)</Text>
              </Text>
              <TextInput
                ref={emailRef}
                style={styles.input}
                placeholder="your@email.com"
                placeholderTextColor={Colors.light.gray}
                value={email}
                onChangeText={handleInputChange(setEmail)}
                autoComplete="email"
                textContentType="emailAddress"
                keyboardType="email-address"
                autoCapitalize="none"
                returnKeyType="done"
                onSubmitEditing={handleRegister}
                editable={!loading}
              />
              <Text style={styles.helpText}>
                We'll use this for order confirmations and account recovery
              </Text>
            </View>
          </View>

          {/* Error Message */}
          {error && (
            <View style={styles.errorContainer}>
              <Ionicons name="alert-circle" size={16} color={Colors.light.error} />
              <Text style={styles.errorText}>{error}</Text>
            </View>
          )}

          {/* Create Account Button */}
          <TouchableOpacity
            style={[styles.createButton, loading && styles.buttonDisabled]}
            onPress={handleRegister}
            disabled={loading || !firstName.trim() || !lastName.trim()}
          >
            {loading ? (
              <ActivityIndicator color="white" />
            ) : (
              <Text style={styles.createButtonText}>Create Account</Text>
            )}
          </TouchableOpacity>

          {/* Privacy Notice */}
          <View style={styles.privacyContainer}>
            <Ionicons name="lock-closed" size={16} color={Colors.light.gray} />
            <Text style={styles.privacyText}>
              Your information is secure and will never be shared
            </Text>
          </View>

          {/* Terms */}
          <Text style={styles.terms}>
            By creating an account, you agree to WeedGo's{'\n'}
            <Text style={styles.link}>Terms of Service</Text> and{' '}
            <Text style={styles.link}>Privacy Policy</Text>
          </Text>

          {/* Back to Login */}
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => router.back()}
            disabled={loading}
          >
            <Ionicons name="arrow-back" size={20} color={Colors.light.primary} />
            <Text style={styles.backButtonText}>Back to Sign In</Text>
          </TouchableOpacity>
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
  },
  header: {
    alignItems: 'center',
    marginBottom: 32,
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
  },
  phoneDisplay: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.light.backgroundSecondary,
    padding: 12,
    borderRadius: 12,
    marginBottom: 24,
    gap: 8,
  },
  phoneText: {
    fontSize: 16,
    fontWeight: '500',
    color: Colors.light.text,
  },
  form: {
    marginBottom: 24,
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
  required: {
    color: Colors.light.error,
  },
  optional: {
    color: Colors.light.gray,
    fontWeight: '400',
  },
  input: {
    borderWidth: 1,
    borderColor: Colors.light.border,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    color: Colors.light.text,
    backgroundColor: 'white',
  },
  helpText: {
    fontSize: 12,
    color: Colors.light.gray,
    marginTop: 6,
    paddingHorizontal: 4,
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
  createButton: {
    backgroundColor: Colors.light.primary,
    borderRadius: 12,
    height: 56,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  createButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  privacyContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
    gap: 8,
  },
  privacyText: {
    fontSize: 12,
    color: Colors.light.gray,
  },
  terms: {
    fontSize: 12,
    color: Colors.light.gray,
    textAlign: 'center',
    lineHeight: 18,
    marginBottom: 24,
  },
  link: {
    color: Colors.light.primary,
    textDecorationLine: 'underline',
  },
  backButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 12,
    gap: 8,
  },
  backButtonText: {
    fontSize: 14,
    color: Colors.light.primary,
    fontWeight: '500',
  },
});