import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import useCartStore from '@/stores/cartStore';
import { Colors, BorderRadius, Shadows } from '@/constants/Colors';

const isDark = true;
const theme = isDark ? Colors.dark : Colors.light;

interface SummaryRowProps {
  label: string;
  value: string;
  icon?: string;
  iconColor?: string;
  highlight?: boolean;
  bold?: boolean;
}

function SummaryRow({ label, value, icon, iconColor, highlight, bold }: SummaryRowProps) {
  return (
    <View style={styles.row}>
      <View style={styles.labelContainer}>
        {icon && (
          <Ionicons name={icon as any} size={16} color={iconColor || theme.textSecondary} />
        )}
        <Text style={[styles.label, bold && styles.boldText]}>{label}</Text>
      </View>
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
    <LinearGradient
      colors={['rgba(138, 43, 226, 0.05)', 'rgba(30, 144, 255, 0.05)']}
      style={styles.container}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
    >
      <View style={styles.content}>
        <SummaryRow
          label="Subtotal"
          value={`$${subtotal.toFixed(2)}`}
          icon="basket"
          iconColor={theme.primary}
        />

        {discount > 0 && (
          <SummaryRow
            label="Discount"
            value={`-$${discount.toFixed(2)}`}
            icon="pricetag"
            iconColor={theme.success}
            highlight
          />
        )}

        <SummaryRow
          label="Tax (HST 13%)"
          value={`$${tax.toFixed(2)}`}
          icon="receipt"
          iconColor={theme.strainCBD}
        />

        {!!deliveryFee && deliveryFee > 0 && (
          <SummaryRow
            label="Delivery Fee"
            value={`$${deliveryFee.toFixed(2)}`}
            icon="car"
            iconColor={theme.strainHybrid}
          />
        )}

        <LinearGradient
          colors={['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)']}
          style={styles.divider}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
        />

        <View style={styles.totalRow}>
          <View style={styles.totalLabelContainer}>
            <Ionicons name="wallet" size={20} color={theme.primary} />
            <Text style={styles.totalLabel}>Total</Text>
          </View>
          <LinearGradient
            colors={[theme.primary, theme.strainSativa]}
            style={styles.totalValueContainer}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
          >
            <Text style={styles.totalValue}>${total.toFixed(2)}</Text>
          </LinearGradient>
        </View>

        {/* Savings indicator */}
        {discount > 0 && (
          <View style={styles.savingsContainer}>
            <Ionicons name="checkmark-circle" size={16} color={theme.success} />
            <Text style={styles.savingsText}>
              You're saving ${discount.toFixed(2)}!
            </Text>
          </View>
        )}
      </View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    marginHorizontal: 20,
    borderRadius: BorderRadius.xl,
    borderWidth: 1,
    borderColor: theme.glassBorder,
    overflow: 'hidden',
    ...Shadows.medium,
  },
  content: {
    backgroundColor: theme.glass,
    padding: 20,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginVertical: 10,
  },
  labelContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  label: {
    fontSize: 15,
    color: theme.textSecondary,
    fontWeight: '500',
  },
  value: {
    fontSize: 15,
    color: theme.text,
    fontWeight: '600',
  },
  highlightText: {
    color: theme.success,
    fontWeight: '700',
  },
  boldText: {
    fontWeight: 'bold',
    fontSize: 17,
    color: theme.text,
  },
  divider: {
    height: 2,
    marginVertical: 16,
    borderRadius: 1,
  },
  totalRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
  },
  totalLabelContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  totalLabel: {
    fontSize: 18,
    fontWeight: '700',
    color: theme.text,
  },
  totalValueContainer: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: BorderRadius.full,
    ...Shadows.small,
  },
  totalValue: {
    fontSize: 20,
    fontWeight: '800',
    color: 'white',
    textShadowColor: 'rgba(0, 0, 0, 0.2)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  savingsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: theme.glassBorder,
  },
  savingsText: {
    fontSize: 14,
    color: theme.success,
    fontWeight: '600',
  },
});