/**
 * Order Confirmation Screen
 * Shows confirmation after successful order placement
 */

import React, { useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Image,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Colors, BorderRadius, Shadows } from '@/constants/Colors';
import Animated, { FadeIn, SlideInDown } from 'react-native-reanimated';

export default function OrderConfirmationScreen() {
  const router = useRouter();
  const { orderId, orderNumber } = useLocalSearchParams();

  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
      <ScrollView contentContainerStyle={styles.content}>
        {/* Success Icon */}
        <Animated.View entering={FadeIn.delay(200)} style={styles.iconContainer}>
          <View style={styles.iconCircle}>
            <Ionicons name="checkmark" size={80} color={Colors.light.success} />
          </View>
        </Animated.View>

        {/* Success Message */}
        <Animated.View entering={SlideInDown.delay(400)} style={styles.messageContainer}>
          <Text style={styles.title}>Order Placed Successfully!</Text>
          <Text style={styles.subtitle}>Thank you for your order</Text>

          {orderNumber && (
            <View style={styles.orderNumberContainer}>
              <Text style={styles.orderNumberLabel}>Order Number</Text>
              <Text style={styles.orderNumber}>{orderNumber}</Text>
            </View>
          )}
        </Animated.View>

        {/* Information Cards */}
        <Animated.View entering={SlideInDown.delay(600)} style={styles.infoCards}>
          <View style={styles.infoCard}>
            <Ionicons name="mail-outline" size={24} color={Colors.light.primary} />
            <Text style={styles.infoTitle}>Confirmation Sent</Text>
            <Text style={styles.infoText}>
              Check your email for order details
            </Text>
          </View>

          <View style={styles.infoCard}>
            <Ionicons name="time-outline" size={24} color={Colors.light.primary} />
            <Text style={styles.infoTitle}>Estimated Time</Text>
            <Text style={styles.infoText}>
              43-58 minutes
            </Text>
          </View>
        </Animated.View>

        {/* Action Buttons */}
        <Animated.View entering={SlideInDown.delay(800)} style={styles.buttonContainer}>
          <TouchableOpacity
            style={styles.primaryButton}
            onPress={() => router.push('/orders')}
          >
            <Text style={styles.primaryButtonText}>View Order Details</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.secondaryButton}
            onPress={() => router.push('/(tabs)/')}
          >
            <Text style={styles.secondaryButtonText}>Continue Shopping</Text>
          </TouchableOpacity>
        </Animated.View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.light.background,
  },
  content: {
    padding: 24,
    alignItems: 'center',
  },
  iconContainer: {
    marginTop: 40,
    marginBottom: 24,
  },
  iconCircle: {
    width: 160,
    height: 160,
    borderRadius: 80,
    backgroundColor: `${Colors.light.success}15`,
    alignItems: 'center',
    justifyContent: 'center',
    ...Shadows.medium,
  },
  messageContainer: {
    alignItems: 'center',
    marginBottom: 32,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: Colors.light.text,
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: Colors.light.textSecondary,
    marginBottom: 24,
    textAlign: 'center',
  },
  orderNumberContainer: {
    backgroundColor: Colors.light.card,
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: BorderRadius.medium,
    alignItems: 'center',
    ...Shadows.small,
  },
  orderNumberLabel: {
    fontSize: 12,
    color: Colors.light.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 4,
  },
  orderNumber: {
    fontSize: 20,
    fontWeight: '600',
    color: Colors.light.primary,
    fontFamily: 'monospace',
  },
  infoCards: {
    width: '100%',
    gap: 16,
    marginBottom: 32,
  },
  infoCard: {
    backgroundColor: Colors.light.card,
    padding: 20,
    borderRadius: BorderRadius.medium,
    alignItems: 'center',
    ...Shadows.small,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.text,
    marginTop: 8,
    marginBottom: 4,
  },
  infoText: {
    fontSize: 14,
    color: Colors.light.textSecondary,
    textAlign: 'center',
  },
  buttonContainer: {
    width: '100%',
    gap: 12,
  },
  primaryButton: {
    backgroundColor: Colors.light.primary,
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: BorderRadius.medium,
    alignItems: 'center',
    ...Shadows.small,
  },
  primaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  secondaryButton: {
    backgroundColor: 'transparent',
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: BorderRadius.medium,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.light.border,
  },
  secondaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.primary,
  },
});
