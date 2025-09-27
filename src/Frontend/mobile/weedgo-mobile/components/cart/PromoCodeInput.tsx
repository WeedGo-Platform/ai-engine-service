import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import useCartStore from '@/stores/cartStore';
import { Colors, BorderRadius, Shadows } from '@/constants/Colors';

const isDark = true;
const theme = isDark ? Colors.dark : Colors.light;

export function PromoCodeInput() {
  const [code, setCode] = useState('');
  const { applyPromoCode, promoCode, removePromoCode, loading, discount } =
    useCartStore();

  const handleApply = async () => {
    if (code.trim()) {
      await applyPromoCode(code.toUpperCase());
      setCode('');
    }
  };

  // If a promo code is already applied
  if (promoCode) {
    return (
      <View style={styles.appliedContainer}>
        <View style={styles.appliedContent}>
          <View style={styles.appliedLeft}>
            <Ionicons name="checkmark-circle" size={24} color={theme.success} />
            <View style={styles.appliedText}>
              <Text style={styles.appliedCode}>{promoCode}</Text>
              <Text style={styles.appliedDiscount}>
                You saved ${discount.toFixed(2)}!
              </Text>
            </View>
          </View>
          <TouchableOpacity
            onPress={removePromoCode}
            disabled={loading}
            style={styles.removeButton}
          >
            <Text style={styles.removeText}>Remove</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  // Promo code input form
  return (
    <View style={styles.container}>
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          value={code}
          onChangeText={setCode}
          placeholder="Enter promo code"
          placeholderTextColor="#999"
          autoCapitalize="characters"
          autoCorrect={false}
          editable={!loading}
        />
        <TouchableOpacity
          onPress={handleApply}
          disabled={loading || !code.trim()}
          activeOpacity={0.8}
        >
          <LinearGradient
            colors={loading || !code.trim() ? ['#666', '#444'] : [theme.primary, theme.primaryLight]}
            style={styles.applyButton}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
          >
            {loading ? (
              <ActivityIndicator size="small" color="white" />
            ) : (
              <Text style={styles.applyButtonText}>Apply</Text>
            )}
          </LinearGradient>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginHorizontal: 20,
  },
  inputContainer: {
    flexDirection: 'row',
    backgroundColor: theme.glass,
    borderRadius: BorderRadius.xl,
    borderWidth: 1,
    borderColor: theme.glassBorder,
    ...Shadows.medium,
  },
  input: {
    flex: 1,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    color: theme.text,
  },
  applyButton: {
    paddingHorizontal: 24,
    paddingVertical: 14,
    justifyContent: 'center',
    borderTopRightRadius: BorderRadius.xl - 1,
    borderBottomRightRadius: BorderRadius.xl - 1,
  },
  applyButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: 'white',
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  disabledButton: {
    opacity: 0.5,
  },
  appliedContainer: {
    marginHorizontal: 20,
  },
  appliedContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: theme.glass,
    padding: 16,
    borderRadius: BorderRadius.xl,
    borderWidth: 2,
    borderColor: theme.success,
    ...Shadows.medium,
  },
  appliedLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  appliedText: {
    marginLeft: 12,
  },
  appliedCode: {
    fontSize: 16,
    fontWeight: '700',
    color: theme.text,
  },
  appliedDiscount: {
    fontSize: 14,
    color: theme.success,
    marginTop: 2,
    fontWeight: '600',
  },
  removeButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  removeText: {
    fontSize: 14,
    color: theme.secondary,
    fontWeight: '600',
  },
});