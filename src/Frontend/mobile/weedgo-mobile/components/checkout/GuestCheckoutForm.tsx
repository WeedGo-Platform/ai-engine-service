import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, BorderRadius, Shadows } from '@/constants/Colors';

const theme = Colors.dark;

interface GuestCheckoutFormProps {
  onSubmit: (data: {
    first_name: string;
    last_name: string;
    email: string;
    phone: string;
  }) => void;
  loading?: boolean;
  onLogin?: () => void;
}

export function GuestCheckoutForm({ onSubmit, loading = false, onLogin }: GuestCheckoutFormProps) {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (!firstName.trim()) {
      newErrors.firstName = 'First name is required';
    }
    if (!lastName.trim()) {
      newErrors.lastName = 'Last name is required';
    }
    if (!email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      newErrors.email = 'Invalid email format';
    }
    if (!phone.trim()) {
      newErrors.phone = 'Phone number is required';
    } else if (!/^\+?[\d\s-()]{10,}$/.test(phone)) {
      newErrors.phone = 'Invalid phone number';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (validate()) {
      onSubmit({
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        email: email.trim().toLowerCase(),
        phone: phone.trim(),
      });
    }
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Ionicons name="person-circle-outline" size={48} color={theme.primary} />
        <Text style={styles.title}>Guest Checkout</Text>
        <Text style={styles.subtitle}>
          Please provide your contact information to complete your order
        </Text>
      </View>

      {/* Form Fields */}
      <View style={styles.form}>
        {/* First Name */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>First Name</Text>
          <View style={[styles.inputWrapper, errors.firstName && styles.inputError]}>
            <Ionicons name="person-outline" size={20} color={theme.textSecondary} />
            <TextInput
              style={styles.input}
              placeholder="John"
              placeholderTextColor={theme.textSecondary}
              value={firstName}
              onChangeText={setFirstName}
              autoCapitalize="words"
              editable={!loading}
            />
          </View>
          {errors.firstName && <Text style={styles.errorText}>{errors.firstName}</Text>}
        </View>

        {/* Last Name */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Last Name</Text>
          <View style={[styles.inputWrapper, errors.lastName && styles.inputError]}>
            <Ionicons name="person-outline" size={20} color={theme.textSecondary} />
            <TextInput
              style={styles.input}
              placeholder="Doe"
              placeholderTextColor={theme.textSecondary}
              value={lastName}
              onChangeText={setLastName}
              autoCapitalize="words"
              editable={!loading}
            />
          </View>
          {errors.lastName && <Text style={styles.errorText}>{errors.lastName}</Text>}
        </View>

        {/* Email */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Email</Text>
          <View style={[styles.inputWrapper, errors.email && styles.inputError]}>
            <Ionicons name="mail-outline" size={20} color={theme.textSecondary} />
            <TextInput
              style={styles.input}
              placeholder="john.doe@example.com"
              placeholderTextColor={theme.textSecondary}
              value={email}
              onChangeText={setEmail}
              autoCapitalize="none"
              keyboardType="email-address"
              autoComplete="email"
              editable={!loading}
            />
          </View>
          {errors.email && <Text style={styles.errorText}>{errors.email}</Text>}
        </View>

        {/* Phone */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Phone Number</Text>
          <View style={[styles.inputWrapper, errors.phone && styles.inputError]}>
            <Ionicons name="call-outline" size={20} color={theme.textSecondary} />
            <TextInput
              style={styles.input}
              placeholder="+1 (555) 123-4567"
              placeholderTextColor={theme.textSecondary}
              value={phone}
              onChangeText={setPhone}
              keyboardType="phone-pad"
              autoComplete="tel"
              editable={!loading}
            />
          </View>
          {errors.phone && <Text style={styles.errorText}>{errors.phone}</Text>}
        </View>
      </View>

      {/* Submit Button */}
      <TouchableOpacity
        style={[styles.submitButton, loading && styles.buttonDisabled]}
        onPress={handleSubmit}
        disabled={loading}
      >
        {loading ? (
          <ActivityIndicator size="small" color={theme.textOnPrimary} />
        ) : (
          <>
            <Text style={styles.submitButtonText}>Continue to Checkout</Text>
            <Ionicons name="arrow-forward" size={20} color={theme.textOnPrimary} />
          </>
        )}
      </TouchableOpacity>

      {/* Login Link */}
      {onLogin && (
        <View style={styles.loginPrompt}>
          <Text style={styles.loginPromptText}>Already have an account?</Text>
          <TouchableOpacity onPress={onLogin} disabled={loading}>
            <Text style={styles.loginLink}>Login</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Privacy Notice */}
      <Text style={styles.privacyText}>
        By continuing, you agree to receive order updates via email and SMS
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: 'rgba(30, 30, 50, 0.85)',
    backdropFilter: 'blur(20px)',
    borderRadius: BorderRadius.xl,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(116, 185, 255, 0.15)',
    ...Shadows.medium,
  },
  header: {
    alignItems: 'center',
    marginBottom: 24,
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: theme.text,
    marginTop: 12,
  },
  subtitle: {
    fontSize: 14,
    color: theme.textSecondary,
    textAlign: 'center',
    marginTop: 8,
    lineHeight: 20,
  },
  form: {
    gap: 16,
  },
  inputGroup: {
    gap: 8,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.text,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.cardBackground,
    borderRadius: BorderRadius.lg,
    borderWidth: 1,
    borderColor: theme.glassBorder,
    paddingHorizontal: 12,
    gap: 8,
  },
  inputError: {
    borderColor: theme.error,
  },
  input: {
    flex: 1,
    color: theme.text,
    fontSize: 15,
    paddingVertical: 12,
  },
  errorText: {
    fontSize: 12,
    color: theme.error,
    marginTop: 4,
  },
  submitButton: {
    backgroundColor: theme.primary,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: BorderRadius.xl,
    marginTop: 24,
    gap: 8,
    shadowColor: theme.primary,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.4,
    shadowRadius: 24,
    elevation: 8,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  submitButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.textOnPrimary,
  },
  loginPrompt: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: 16,
  },
  loginPromptText: {
    fontSize: 14,
    color: theme.textSecondary,
  },
  loginLink: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.primary,
  },
  privacyText: {
    fontSize: 12,
    color: theme.textSecondary,
    textAlign: 'center',
    marginTop: 16,
    lineHeight: 18,
  },
});
