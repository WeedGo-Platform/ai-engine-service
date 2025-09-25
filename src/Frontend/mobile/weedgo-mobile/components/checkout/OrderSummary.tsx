import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Modal,
  ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface OrderSummaryProps {
  subtotal: number;
  tax: number;
  deliveryFee: number;
  tipPercentage: number;
  tipAmount: number;
  total: number;
  onTipChange: (percentage: number) => void;
}

export function OrderSummary({
  subtotal,
  tax,
  deliveryFee,
  tipPercentage,
  tipAmount,
  total,
  onTipChange,
}: OrderSummaryProps) {
  const [showTipModal, setShowTipModal] = useState(false);

  const tipOptions = [
    { label: 'No Tip', value: 0 },
    { label: '10%', value: 0.1 },
    { label: '15%', value: 0.15 },
    { label: '20%', value: 0.2 },
    { label: '25%', value: 0.25 },
    { label: 'Custom', value: -1 },
  ];

  const formatTipLabel = () => {
    if (tipPercentage === 0) return 'No Tip';
    return `${(tipPercentage * 100).toFixed(0)}%`;
  };

  const handleTipSelect = (value: number) => {
    if (value === -1) {
      // Handle custom tip
      setShowTipModal(false);
      // TODO: Show custom tip input
      return;
    }
    onTipChange(value);
    setShowTipModal(false);
  };

  return (
    <>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Order Summary</Text>

        <View style={styles.summaryRow}>
          <Text style={styles.summaryLabel}>Subtotal</Text>
          <Text style={styles.summaryValue}>${subtotal.toFixed(2)}</Text>
        </View>

        {!!deliveryFee && deliveryFee > 0 && (
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Delivery Fee</Text>
            <Text style={styles.summaryValue}>
              {deliveryFee === 0 ? 'FREE' : `$${deliveryFee.toFixed(2)}`}
            </Text>
          </View>
        )}

        <View style={styles.summaryRow}>
          <Text style={styles.summaryLabel}>Tax (HST)</Text>
          <Text style={styles.summaryValue}>${tax.toFixed(2)}</Text>
        </View>

        {/* Tip Selector */}
        <TouchableOpacity
          style={[styles.summaryRow, styles.tipRow]}
          onPress={() => setShowTipModal(true)}
        >
          <View style={styles.tipLabelContainer}>
            <Text style={styles.summaryLabel}>Tip</Text>
            <View style={styles.tipBadge}>
              <Text style={styles.tipBadgeText}>{formatTipLabel()}</Text>
              <Ionicons name="chevron-down" size={14} color="#27AE60" />
            </View>
          </View>
          <Text style={styles.summaryValue}>${tipAmount.toFixed(2)}</Text>
        </TouchableOpacity>

        <View style={styles.divider} />

        <View style={[styles.summaryRow, styles.totalRow]}>
          <Text style={styles.totalLabel}>Total</Text>
          <Text style={styles.totalValue}>${total.toFixed(2)}</Text>
        </View>

        {/* Savings Message */}
        {deliveryFee === 0 && subtotal >= 100 && (
          <View style={styles.savingsMessage}>
            <Ionicons name="checkmark-circle" size={16} color="#27AE60" />
            <Text style={styles.savingsText}>
              You saved ${10} on delivery with this order!
            </Text>
          </View>
        )}
      </View>

      {/* Tip Selection Modal */}
      <Modal
        visible={showTipModal}
        animationType="slide"
        transparent
        onRequestClose={() => setShowTipModal(false)}
      >
        <TouchableOpacity
          style={styles.modalOverlay}
          activeOpacity={1}
          onPress={() => setShowTipModal(false)}
        >
          <View style={styles.tipModal}>
            <View style={styles.tipModalHeader}>
              <Text style={styles.tipModalTitle}>Add a Tip</Text>
              <Text style={styles.tipModalSubtitle}>
                Tips go directly to your delivery driver
              </Text>
            </View>

            <View style={styles.tipOptions}>
              {tipOptions.map((option) => (
                <TouchableOpacity
                  key={option.label}
                  style={[
                    styles.tipOption,
                    option.value === tipPercentage && styles.tipOptionSelected,
                    option.value === -1 && styles.tipOptionCustom,
                  ]}
                  onPress={() => handleTipSelect(option.value)}
                >
                  <Text
                    style={[
                      styles.tipOptionLabel,
                      option.value === tipPercentage && styles.tipOptionLabelSelected,
                    ]}
                  >
                    {option.label}
                  </Text>
                  {option.value > 0 && (
                    <Text
                      style={[
                        styles.tipOptionAmount,
                        option.value === tipPercentage && styles.tipOptionAmountSelected,
                      ]}
                    >
                      ${(subtotal * option.value).toFixed(2)}
                    </Text>
                  )}
                  {option.value === tipPercentage && option.value !== -1 && (
                    <Ionicons
                      name="checkmark-circle"
                      size={20}
                      color="#27AE60"
                      style={styles.tipOptionCheck}
                    />
                  )}
                </TouchableOpacity>
              ))}
            </View>

            <TouchableOpacity
              style={styles.tipModalClose}
              onPress={() => setShowTipModal(false)}
            >
              <Text style={styles.tipModalCloseText}>Done</Text>
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  section: {
    backgroundColor: '#FFF',
    marginTop: 12,
    padding: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginVertical: 6,
  },
  summaryLabel: {
    fontSize: 14,
    color: '#666',
  },
  summaryValue: {
    fontSize: 14,
    color: '#333',
    fontWeight: '500',
  },
  tipRow: {
    backgroundColor: '#F8F9FA',
    padding: 8,
    borderRadius: 8,
    marginVertical: 8,
  },
  tipLabelContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  tipBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0FFF4',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 4,
  },
  tipBadgeText: {
    fontSize: 12,
    color: '#27AE60',
    fontWeight: '500',
  },
  divider: {
    height: 1,
    backgroundColor: '#EEE',
    marginVertical: 12,
  },
  totalRow: {
    marginVertical: 0,
  },
  totalLabel: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  totalValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#27AE60',
  },
  savingsMessage: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0FFF4',
    padding: 12,
    borderRadius: 8,
    marginTop: 12,
    gap: 8,
  },
  savingsText: {
    fontSize: 13,
    color: '#27AE60',
    flex: 1,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  tipModal: {
    backgroundColor: '#FFF',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingBottom: 34, // Safe area
  },
  tipModalHeader: {
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#EEE',
  },
  tipModalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  tipModalSubtitle: {
    fontSize: 13,
    color: '#666',
  },
  tipOptions: {
    padding: 16,
  },
  tipOption: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    marginBottom: 8,
  },
  tipOptionSelected: {
    backgroundColor: '#F0FFF4',
    borderWidth: 1,
    borderColor: '#27AE60',
  },
  tipOptionCustom: {
    backgroundColor: '#FFF',
    borderWidth: 1,
    borderColor: '#DDD',
    borderStyle: 'dashed',
  },
  tipOptionLabel: {
    flex: 1,
    fontSize: 15,
    color: '#333',
    fontWeight: '500',
  },
  tipOptionLabelSelected: {
    color: '#27AE60',
  },
  tipOptionAmount: {
    fontSize: 14,
    color: '#666',
    marginRight: 8,
  },
  tipOptionAmountSelected: {
    color: '#27AE60',
    fontWeight: '500',
  },
  tipOptionCheck: {
    marginLeft: 4,
  },
  tipModalClose: {
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#27AE60',
    margin: 16,
    marginTop: 0,
    borderRadius: 12,
  },
  tipModalCloseText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFF',
  },
});