import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import useCartStore from '@/stores/cartStore';

interface SummaryRowProps {
  label: string;
  value: string;
  highlight?: boolean;
  bold?: boolean;
}

function SummaryRow({ label, value, highlight, bold }: SummaryRowProps) {
  return (
    <View style={styles.row}>
      <Text style={[styles.label, bold && styles.boldText]}>{label}</Text>
      <Text
        style={[
          styles.value,
          highlight && styles.highlightText,
          bold && styles.boldText,
        ]}
      >
        {value}
      </Text>
    </View>
  );
}

export function OrderSummary() {
  const { subtotal, tax, deliveryFee, discount, total } = useCartStore();

  return (
    <View style={styles.container}>
      <SummaryRow label="Subtotal" value={`$${subtotal.toFixed(2)}`} />

      {discount > 0 && (
        <SummaryRow
          label="Discount"
          value={`-$${discount.toFixed(2)}`}
          highlight
        />
      )}

      <SummaryRow label="Tax (HST 13%)" value={`$${tax.toFixed(2)}`} />

      {deliveryFee > 0 && (
        <SummaryRow label="Delivery Fee" value={`$${deliveryFee.toFixed(2)}`} />
      )}

      <View style={styles.divider} />

      <SummaryRow label="Total" value={`$${total.toFixed(2)}`} bold />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    marginHorizontal: 16,
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginVertical: 8,
  },
  label: {
    fontSize: 16,
    color: '#666',
  },
  value: {
    fontSize: 16,
    color: '#1a1a1a',
  },
  highlightText: {
    color: '#00ff00',
    fontWeight: '600',
  },
  boldText: {
    fontWeight: 'bold',
    fontSize: 18,
    color: '#1a1a1a',
  },
  divider: {
    height: 1,
    backgroundColor: '#e0e0e0',
    marginVertical: 12,
  },
});