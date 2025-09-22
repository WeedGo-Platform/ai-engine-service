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
import useCartStore from '@/stores/cartStore';

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
            <Ionicons name="checkmark-circle" size={24} color="#00ff00" />
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
          style={[styles.applyButton, loading && styles.disabledButton]}
          onPress={handleApply}
          disabled={loading || !code.trim()}
        >
          {loading ? (
            <ActivityIndicator size="small" color="#000" />
          ) : (
            <Text style={styles.applyButtonText}>Apply</Text>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginHorizontal: 16,
  },
  inputContainer: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  input: {
    flex: 1,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    color: '#1a1a1a',
  },
  applyButton: {
    backgroundColor: '#00ff00',
    paddingHorizontal: 24,
    justifyContent: 'center',
    borderTopRightRadius: 12,
    borderBottomRightRadius: 12,
  },
  applyButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
  },
  disabledButton: {
    opacity: 0.5,
  },
  appliedContainer: {
    marginHorizontal: 16,
  },
  appliedContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#00ff00',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
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
    fontWeight: '600',
    color: '#1a1a1a',
  },
  appliedDiscount: {
    fontSize: 14,
    color: '#00ff00',
    marginTop: 2,
  },
  removeButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  removeText: {
    fontSize: 14,
    color: '#ff3b30',
    fontWeight: '600',
  },
});