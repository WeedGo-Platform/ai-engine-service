/**
 * Add Card Modal
 * Secure card input for Clover payment processing
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Modal,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, BorderRadius, Shadows } from '@/constants/Colors';
import { cloverService, CardDetails } from '@/services/payment/cloverService';
import Toast from 'react-native-toast-message';

interface AddCardModalProps {
  visible: boolean;
  onClose: () => void;
  onCardAdded: (cardInfo: {
    token: string;
    brand: string;
    last4: string;
    expMonth: string;
    expYear: string;
    saveCard: boolean;
  }) => void;
  userId?: string;
}

export function AddCardModal({ visible, onClose, onCardAdded, userId }: AddCardModalProps) {
  const [cardNumber, setCardNumber] = useState('');
  const [expiry, setExpiry] = useState('');
  const [cvv, setCvv] = useState('');
  const [postalCode, setPostalCode] = useState('');
  const [saveCard, setSaveCard] = useState(true);
  const [loading, setLoading] = useState(false);

  const [errors, setErrors] = useState({
    cardNumber: '',
    expiry: '',
    cvv: '',
    postalCode: '',
  });

  const resetForm = () => {
    setCardNumber('');
    setExpiry('');
    setCvv('');
    setPostalCode('');
    setSaveCard(true);
    setErrors({ cardNumber: '', expiry: '', cvv: '', postalCode: '' });
  };

  const handleCardNumberChange = (text: string) => {
    const formatted = cloverService.formatCardNumber(text);
    if (formatted.replace(/\s/g, '').length <= 19) {
      setCardNumber(formatted);
      setErrors({ ...errors, cardNumber: '' });
    }
  };

  const handleExpiryChange = (text: string) => {
    const formatted = cloverService.formatExpiry(text);
    if (formatted.length <= 5) {
      setExpiry(formatted);
      setErrors({ ...errors, expiry: '' });
    }
  };

  const handleCvvChange = (text: string) => {
    const cleaned = text.replace(/\D/g, '');
    if (cleaned.length <= 4) {
      setCvv(cleaned);
      setErrors({ ...errors, cvv: '' });
    }
  };

  const handlePostalCodeChange = (text: string) => {
    const cleaned = text.toUpperCase().replace(/[^A-Z0-9]/g, '');
    if (cleaned.length <= 7) {
      setPostalCode(cleaned);
      setErrors({ ...errors, postalCode: '' });
    }
  };

  const validate = (): boolean => {
    const newErrors = {
      cardNumber: '',
      expiry: '',
      cvv: '',
      postalCode: '',
    };

    // Validate card number
    if (!cloverService.validateCardNumber(cardNumber)) {
      newErrors.cardNumber = 'Invalid card number';
    }

    // Validate expiry
    const [month, year] = expiry.split('/');
    if (!month || !year || !cloverService.validateExpiry(month, year)) {
      newErrors.expiry = 'Invalid or expired card';
    }

    // Validate CVV
    const brand = cloverService.getCardBrand(cardNumber);
    if (!cloverService.validateCVV(cvv, brand)) {
      newErrors.cvv = brand === 'amex' ? 'Enter 4-digit CVV' : 'Enter 3-digit CVV';
    }

    // Validate postal code (Canadian format)
    if (!/^[A-Z]\d[A-Z]\s?\d[A-Z]\d$/.test(postalCode)) {
      newErrors.postalCode = 'Invalid postal code';
    }

    setErrors(newErrors);
    return !Object.values(newErrors).some((error) => error !== '');
  };

  const handleAddCard = async () => {
    if (!validate()) {
      Toast.show({
        type: 'error',
        text1: 'Invalid Card Details',
        text2: 'Please check your card information',
      });
      return;
    }

    setLoading(true);

    try {
      const [month, year] = expiry.split('/');

      const cardDetails: CardDetails = {
        cardNumber: cardNumber.replace(/\s/g, ''),
        expiryMonth: month,
        expiryYear: year,
        cvv,
        postalCode: postalCode.replace(/\s/g, ''),
      };

      // Tokenize card with Clover
      const tokenResult = await cloverService.tokenizeCard(cardDetails);

      console.log('[AddCardModal] Card tokenized successfully:', {
        brand: tokenResult.card.brand,
        last4: tokenResult.card.last4,
        saveToProfile: saveCard,
      });

      // Return card info to parent (PaymentSection will handle saving to backend)
      onCardAdded({
        token: tokenResult.token,
        brand: tokenResult.card.brand,
        last4: tokenResult.card.last4,
        expMonth: tokenResult.card.exp_month,
        expYear: tokenResult.card.exp_year,
        saveCard, // Pass the saveCard preference to parent
      });

      Toast.show({
        type: 'success',
        text1: 'Card Added',
        text2: 'Your payment method is ready',
      });

      resetForm();
      onClose();
    } catch (error: any) {
      console.error('[AddCardModal] Error:', error);
      Toast.show({
        type: 'error',
        text1: 'Card Error',
        text2: error.message || 'Failed to add card',
      });
    } finally {
      setLoading(false);
    }
  };

  const getCardIcon = () => {
    const brand = cloverService.getCardBrand(cardNumber);
    switch (brand) {
      case 'visa':
        return 'card';
      case 'mastercard':
        return 'card';
      case 'amex':
        return 'card';
      default:
        return 'card-outline';
    }
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={onClose} style={styles.headerButton}>
            <Text style={styles.cancelText}>Cancel</Text>
          </TouchableOpacity>
          <Text style={styles.title}>Add Card</Text>
          <View style={styles.headerButton} />
        </View>

        {/* Content */}
        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {/* Security Notice */}
          <View style={styles.securityCard}>
            <Ionicons name="shield-checkmark" size={24} color={theme.success} />
            <View style={styles.securityText}>
              <Text style={styles.securityTitle}>Secure Payment</Text>
              <Text style={styles.securityDescription}>
                Your card details are encrypted and securely processed by Clover
              </Text>
            </View>
          </View>

          {/* Card Number */}
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Card Number</Text>
            <View style={[styles.inputContainer, errors.cardNumber && styles.inputError]}>
              <Ionicons name={getCardIcon()} size={20} color={theme.textSecondary} />
              <TextInput
                style={styles.input}
                value={cardNumber}
                onChangeText={handleCardNumberChange}
                placeholder="1234 5678 9012 3456"
                placeholderTextColor={theme.disabled}
                keyboardType="number-pad"
                maxLength={23}
                autoComplete="cc-number"
              />
            </View>
            {errors.cardNumber ? (
              <Text style={styles.errorText}>{errors.cardNumber}</Text>
            ) : null}
          </View>

          {/* Expiry and CVV */}
          <View style={styles.row}>
            <View style={[styles.inputGroup, styles.inputHalf]}>
              <Text style={styles.label}>Expiry Date</Text>
              <View style={[styles.inputContainer, errors.expiry && styles.inputError]}>
                <Ionicons name="calendar-outline" size={20} color={theme.textSecondary} />
                <TextInput
                  style={styles.input}
                  value={expiry}
                  onChangeText={handleExpiryChange}
                  placeholder="MM/YY"
                  placeholderTextColor={theme.disabled}
                  keyboardType="number-pad"
                  maxLength={5}
                  autoComplete="cc-exp"
                />
              </View>
              {errors.expiry ? <Text style={styles.errorText}>{errors.expiry}</Text> : null}
            </View>

            <View style={[styles.inputGroup, styles.inputHalf]}>
              <Text style={styles.label}>CVV</Text>
              <View style={[styles.inputContainer, errors.cvv && styles.inputError]}>
                <Ionicons name="lock-closed-outline" size={20} color={theme.textSecondary} />
                <TextInput
                  style={styles.input}
                  value={cvv}
                  onChangeText={handleCvvChange}
                  placeholder="123"
                  placeholderTextColor={theme.disabled}
                  keyboardType="number-pad"
                  maxLength={4}
                  secureTextEntry
                  autoComplete="cc-csc"
                />
              </View>
              {errors.cvv ? <Text style={styles.errorText}>{errors.cvv}</Text> : null}
            </View>
          </View>

          {/* Postal Code */}
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Postal Code</Text>
            <View style={[styles.inputContainer, errors.postalCode && styles.inputError]}>
              <Ionicons name="location-outline" size={20} color={theme.textSecondary} />
              <TextInput
                style={styles.input}
                value={postalCode}
                onChangeText={handlePostalCodeChange}
                placeholder="M5V 3A8"
                placeholderTextColor={theme.disabled}
                autoCapitalize="characters"
                maxLength={7}
                autoComplete="postal-code"
              />
            </View>
            {errors.postalCode ? (
              <Text style={styles.errorText}>{errors.postalCode}</Text>
            ) : null}
          </View>

          {/* Save Card Toggle */}
          {userId && (
            <TouchableOpacity
              style={styles.saveCardToggle}
              onPress={() => setSaveCard(!saveCard)}
            >
              <View style={[styles.checkbox, saveCard && styles.checkboxChecked]}>
                {saveCard && <Ionicons name="checkmark" size={16} color={theme.text} />}
              </View>
              <Text style={styles.saveCardText}>Save card for future purchases</Text>
            </TouchableOpacity>
          )}

          {/* Add Card Button */}
          <TouchableOpacity
            style={[styles.addButton, loading && styles.addButtonDisabled]}
            onPress={handleAddCard}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator size="small" color={theme.text} />
            ) : (
              <>
                <Ionicons name="card" size={20} color={theme.text} />
                <Text style={styles.addButtonText}>Add Card</Text>
              </>
            )}
          </TouchableOpacity>

          {/* PCI Compliance Notice */}
          <View style={styles.complianceNotice}>
            <Ionicons name="information-circle-outline" size={16} color={theme.textSecondary} />
            <Text style={styles.complianceText}>
              PCI DSS compliant · AES-256 encryption · Your data is never stored on our servers
            </Text>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </Modal>
  );
}

const theme = Colors.dark;

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 60,
    paddingBottom: 15,
    paddingHorizontal: 16,
    backgroundColor: theme.glass,
    borderBottomWidth: 1,
    borderBottomColor: theme.glassBorder,
  },
  headerButton: {
    padding: 8,
    minWidth: 60,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: theme.text,
  },
  cancelText: {
    fontSize: 16,
    color: theme.textSecondary,
  },
  content: {
    flex: 1,
    padding: 16,
  },
  securityCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(34, 197, 94, 0.1)',
    padding: 16,
    borderRadius: BorderRadius.xl,
    marginBottom: 24,
    gap: 12,
    borderLeftWidth: 3,
    borderLeftColor: theme.success,
  },
  securityText: {
    flex: 1,
  },
  securityTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: theme.text,
    marginBottom: 4,
  },
  securityDescription: {
    fontSize: 13,
    color: theme.textSecondary,
    lineHeight: 18,
  },
  inputGroup: {
    marginBottom: 20,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.text,
    marginBottom: 8,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.cardBackground,
    borderRadius: BorderRadius.lg,
    paddingHorizontal: 12,
    paddingVertical: 14,
    gap: 12,
    borderWidth: 1,
    borderColor: theme.glassBorder,
  },
  inputError: {
    borderColor: theme.error,
    borderWidth: 2,
  },
  input: {
    flex: 1,
    fontSize: 16,
    color: theme.text,
  },
  errorText: {
    fontSize: 12,
    color: theme.error,
    marginTop: 4,
    marginLeft: 4,
  },
  row: {
    flexDirection: 'row',
    gap: 12,
  },
  inputHalf: {
    flex: 1,
  },
  saveCardToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 24,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderWidth: 2,
    borderColor: theme.glassBorder,
    borderRadius: BorderRadius.sm,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkboxChecked: {
    backgroundColor: theme.primary,
    borderColor: theme.primary,
  },
  saveCardText: {
    fontSize: 14,
    color: theme.text,
  },
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.primary,
    padding: 18,
    borderRadius: BorderRadius.xl,
    gap: 8,
    ...Shadows.large,
  },
  addButtonDisabled: {
    opacity: 0.6,
  },
  addButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: theme.text,
  },
  complianceNotice: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 20,
    paddingHorizontal: 16,
  },
  complianceText: {
    flex: 1,
    fontSize: 11,
    color: theme.textSecondary,
    textAlign: 'center',
    lineHeight: 16,
  },
});
