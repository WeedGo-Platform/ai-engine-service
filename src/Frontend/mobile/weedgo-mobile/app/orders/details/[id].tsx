import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Stack, useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { Colors, Gradients, BorderRadius, Shadows } from '@/constants/Colors';
import { ordersService } from '@/services/api/orders';
import { Order } from '@/stores/orderStore';

export default function OrderDetailsScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const theme = Colors.dark;

  useEffect(() => {
    loadOrderDetails();
  }, [id]);

  const loadOrderDetails = async () => {
    if (!id) return;

    try {
      setLoading(true);
      const response = await ordersService.getOrder(id);
      setOrder(response.data);
    } catch (error) {
      console.error('Failed to load order details:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadOrderDetails();
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  };

  if (loading && !order) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.primary} />
        </View>
      </SafeAreaView>
    );
  }

  if (!order) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Ionicons name="alert-circle-outline" size={64} color={theme.textSecondary} />
          <Text style={[styles.errorText, { color: theme.textSecondary }]}>
            Order not found
          </Text>
          <TouchableOpacity
            style={[styles.button, { backgroundColor: theme.primary }]}
            onPress={() => router.back()}
          >
            <Text style={styles.buttonText}>Go Back</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <LinearGradient
      colors={[theme.gradientStart, theme.gradientMid, theme.gradientEnd]}
      style={styles.gradientContainer}
      start={{ x: 0, y: 0 }}
      end={{ x: 0.5, y: 1 }}
    >
      <SafeAreaView style={styles.container}>
        <Stack.Screen
          options={{
            headerShown: true,
            title: `Order #${order.order_number}`,
            headerStyle: {
              backgroundColor: 'transparent',
            },
            headerTintColor: theme.text,
            headerTransparent: true,
          }}
        />

        <ScrollView
          style={styles.scrollView}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={handleRefresh}
              tintColor={theme.primary}
            />
          }
        >
          {/* Order Status Card */}
          <View style={[styles.card, { backgroundColor: theme.cardBackground }]}>
            <View style={styles.statusHeader}>
              <View>
                <Text style={[styles.statusLabel, { color: theme.textSecondary }]}>
                  Status
                </Text>
                <Text style={[styles.statusValue, { color: theme.primary }]}>
                  {order.status?.replace('_', ' ').toUpperCase()}
                </Text>
              </View>
              {(order.status === 'confirmed' || order.status === 'preparing' || order.status === 'out_for_delivery') && (
                <TouchableOpacity
                  style={[styles.trackButton, { backgroundColor: theme.primary }]}
                  onPress={() => router.push(`/orders/track/${order.id}`)}
                >
                  <Ionicons name="navigate" size={16} color="white" />
                  <Text style={styles.trackButtonText}>Track Order</Text>
                </TouchableOpacity>
              )}
            </View>
            <Text style={[styles.orderDate, { color: theme.textSecondary }]}>
              {formatDate(order.created_at)}
            </Text>
          </View>

          {/* Delivery/Pickup Info */}
          {order.delivery_type === 'delivery' && order.delivery_address ? (
            <View style={[styles.card, { backgroundColor: theme.cardBackground }]}>
              <View style={styles.cardHeader}>
                <Ionicons name="location" size={20} color={theme.primary} />
                <Text style={[styles.cardTitle, { color: theme.text }]}>
                  Delivery Address
                </Text>
              </View>
              <Text style={[styles.addressText, { color: theme.text }]}>
                {order.delivery_address.street}
              </Text>
              <Text style={[styles.addressText, { color: theme.text }]}>
                {order.delivery_address.city}, {order.delivery_address.province} {order.delivery_address.postal_code}
              </Text>
              {order.delivery_address.instructions && (
                <Text style={[styles.instructions, { color: theme.textSecondary }]}>
                  Note: {order.delivery_address.instructions}
                </Text>
              )}
            </View>
          ) : (
            <View style={[styles.card, { backgroundColor: theme.cardBackground }]}>
              <View style={styles.cardHeader}>
                <Ionicons name="bag-check" size={20} color={theme.primary} />
                <Text style={[styles.cardTitle, { color: theme.text }]}>
                  Pickup Order
                </Text>
              </View>
              {order.pickup_time && (
                <Text style={[styles.addressText, { color: theme.text }]}>
                  Pickup Time: {order.pickup_time}
                </Text>
              )}
            </View>
          )}

          {/* Order Items */}
          <View style={[styles.card, { backgroundColor: theme.cardBackground }]}>
            <View style={styles.cardHeader}>
              <Ionicons name="cart" size={20} color={theme.primary} />
              <Text style={[styles.cardTitle, { color: theme.text }]}>
                Order Items ({order.items?.length || 0})
              </Text>
            </View>
            {order.items?.map((item, index) => (
              <View key={index} style={styles.itemRow}>
                <View style={styles.itemInfo}>
                  <Text style={[styles.itemName, { color: theme.text }]}>
                    {item.product_name}
                  </Text>
                  {item.size && (
                    <Text style={[styles.itemSize, { color: theme.textSecondary }]}>
                      Size: {item.size}
                    </Text>
                  )}
                </View>
                <View style={styles.itemPricing}>
                  <Text style={[styles.itemQuantity, { color: theme.textSecondary }]}>
                    x{item.quantity}
                  </Text>
                  <Text style={[styles.itemPrice, { color: theme.text }]}>
                    ${item.subtotal?.toFixed(2)}
                  </Text>
                </View>
              </View>
            ))}
          </View>

          {/* Order Summary */}
          <View style={[styles.card, { backgroundColor: theme.cardBackground }]}>
            <View style={styles.cardHeader}>
              <Ionicons name="receipt" size={20} color={theme.primary} />
              <Text style={[styles.cardTitle, { color: theme.text }]}>
                Order Summary
              </Text>
            </View>
            <View style={styles.summaryRow}>
              <Text style={[styles.summaryLabel, { color: theme.textSecondary }]}>
                Subtotal
              </Text>
              <Text style={[styles.summaryValue, { color: theme.text }]}>
                ${order.subtotal?.toFixed(2)}
              </Text>
            </View>
            {order.discount > 0 && (
              <View style={styles.summaryRow}>
                <Text style={[styles.summaryLabel, { color: theme.success }]}>
                  Discount
                </Text>
                <Text style={[styles.summaryValue, { color: theme.success }]}>
                  -${order.discount?.toFixed(2)}
                </Text>
              </View>
            )}
            <View style={styles.summaryRow}>
              <Text style={[styles.summaryLabel, { color: theme.textSecondary }]}>
                Tax
              </Text>
              <Text style={[styles.summaryValue, { color: theme.text }]}>
                ${order.tax?.toFixed(2)}
              </Text>
            </View>
            {order.delivery_type === 'delivery' && (
              <View style={styles.summaryRow}>
                <Text style={[styles.summaryLabel, { color: theme.textSecondary }]}>
                  Delivery Fee
                </Text>
                <Text style={[styles.summaryValue, { color: theme.text }]}>
                  ${order.delivery_fee?.toFixed(2)}
                </Text>
              </View>
            )}
            {order.tip_amount > 0 && (
              <View style={styles.summaryRow}>
                <Text style={[styles.summaryLabel, { color: theme.textSecondary }]}>
                  Tip
                </Text>
                <Text style={[styles.summaryValue, { color: theme.text }]}>
                  ${order.tip_amount?.toFixed(2)}
                </Text>
              </View>
            )}
            <View style={[styles.summaryRow, styles.totalRow]}>
              <Text style={[styles.totalLabel, { color: theme.text }]}>
                Total
              </Text>
              <Text style={[styles.totalValue, { color: theme.primary }]}>
                ${order.total?.toFixed(2)}
              </Text>
            </View>
          </View>

          {/* Payment Method */}
          <View style={[styles.card, { backgroundColor: theme.cardBackground }]}>
            <View style={styles.cardHeader}>
              <Ionicons name="card" size={20} color={theme.primary} />
              <Text style={[styles.cardTitle, { color: theme.text }]}>
                Payment Method
              </Text>
            </View>
            <Text style={[styles.paymentText, { color: theme.text }]}>
              {order.payment_method?.type?.toUpperCase() || 'Cash'}
              {order.payment_method?.last4 && ` ****${order.payment_method.last4}`}
            </Text>
          </View>

          {/* Special Instructions */}
          {order.special_instructions && (
            <View style={[styles.card, { backgroundColor: theme.cardBackground }]}>
              <View style={styles.cardHeader}>
                <Ionicons name="document-text" size={20} color={theme.primary} />
                <Text style={[styles.cardTitle, { color: theme.text }]}>
                  Special Instructions
                </Text>
              </View>
              <Text style={[styles.instructionsText, { color: theme.text }]}>
                {order.special_instructions}
              </Text>
            </View>
          )}

          <View style={{ height: 40 }} />
        </ScrollView>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  gradientContainer: {
    flex: 1,
  },
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  errorContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  errorText: {
    fontSize: 18,
    fontWeight: '600',
    marginTop: 16,
    marginBottom: 24,
  },
  button: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: BorderRadius.md,
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
    paddingTop: 100,
  },
  card: {
    marginHorizontal: 16,
    marginBottom: 16,
    padding: 16,
    borderRadius: BorderRadius.lg,
    ...Shadows.medium,
  },
  statusHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  statusLabel: {
    fontSize: 13,
    fontWeight: '500',
    marginBottom: 4,
  },
  statusValue: {
    fontSize: 18,
    fontWeight: '700',
  },
  trackButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: BorderRadius.md,
  },
  trackButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  orderDate: {
    fontSize: 13,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  addressText: {
    fontSize: 14,
    lineHeight: 20,
  },
  instructions: {
    fontSize: 13,
    marginTop: 8,
    fontStyle: 'italic',
  },
  itemRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.1)',
  },
  itemInfo: {
    flex: 1,
  },
  itemName: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 4,
  },
  itemSize: {
    fontSize: 12,
  },
  itemPricing: {
    alignItems: 'flex-end',
  },
  itemQuantity: {
    fontSize: 12,
    marginBottom: 4,
  },
  itemPrice: {
    fontSize: 14,
    fontWeight: '600',
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  summaryLabel: {
    fontSize: 14,
  },
  summaryValue: {
    fontSize: 14,
    fontWeight: '500',
  },
  totalRow: {
    borderTopWidth: 2,
    borderTopColor: 'rgba(255,255,255,0.2)',
    marginTop: 8,
    paddingTop: 16,
  },
  totalLabel: {
    fontSize: 16,
    fontWeight: '700',
  },
  totalValue: {
    fontSize: 18,
    fontWeight: '700',
  },
  paymentText: {
    fontSize: 14,
  },
  instructionsText: {
    fontSize: 14,
    lineHeight: 20,
  },
});
