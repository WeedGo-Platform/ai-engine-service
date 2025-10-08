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
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Colors, BorderRadius, Shadows, Gradients } from '@/constants/Colors';
import { LinearGradient } from 'expo-linear-gradient';
import { ordersService } from '@/services/api/orders';
import { Order } from '@/types/api.types';

export default function OrdersScreen() {
  const router = useRouter();
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const isDark = false;
  const theme = isDark ? Colors.dark : Colors.light;

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    try {
      const response = await ordersService.getOrders();
      // Backend returns {data: {count, orders, data}}
      // We need to access response.data.orders
      setOrders(response.data?.orders || []);
    } catch (error) {
      console.error('Failed to load orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadOrders();
    setRefreshing(false);
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'delivered':
        return theme.success;
      case 'pending':
        return theme.warning;
      case 'processing':
      case 'confirmed':
        return theme.info;
      case 'cancelled':
        return theme.error;
      default:
        return theme.textSecondary;
    }
  };

  const getStatusGradient = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'delivered':
        return Gradients.hybrid;
      case 'pending':
        return Gradients.warm;
      case 'processing':
      case 'confirmed':
        return Gradients.ocean;
      case 'cancelled':
        return ['#FF7675', '#D63031'];
      default:
        return ['#B2BEC3', '#95A5A6'];
    }
  };

  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <LinearGradient
        colors={[theme.gradientStart, theme.gradientMid, theme.gradientEnd]}
        style={styles.gradientContainer}
        start={{ x: 0, y: 0 }}
        end={{ x: 0.5, y: 1 }}
      >
        <SafeAreaView style={styles.container}>
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={theme.primary} />
            <Text style={styles.loadingText}>Loading orders...</Text>
          </View>
        </SafeAreaView>
      </LinearGradient>
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
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
            <Ionicons name="arrow-back" size={24} color={theme.text} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Order History</Text>
          <View style={{ width: 40 }} />
        </View>

        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={handleRefresh}
              tintColor={theme.primary}
            />
          }
          showsVerticalScrollIndicator={false}
        >
          {orders.length === 0 ? (
            <View style={styles.emptyContainer}>
              <Ionicons name="receipt-outline" size={64} color={theme.textSecondary} />
              <Text style={styles.emptyTitle}>No orders yet</Text>
              <Text style={styles.emptyText}>
                Your order history will appear here once you make your first purchase
              </Text>
              <TouchableOpacity
                style={styles.shopButton}
                onPress={() => router.push('/(tabs)/')}
                activeOpacity={0.8}
              >
                <LinearGradient
                  colors={Gradients.primary}
                  style={styles.shopButtonGradient}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                >
                  <Text style={styles.shopButtonText}>Start Shopping</Text>
                </LinearGradient>
              </TouchableOpacity>
            </View>
          ) : (
            <View style={styles.ordersList}>
              {orders.map((order) => (
                <TouchableOpacity
                  key={order.id}
                  style={styles.orderCard}
                  onPress={() => router.push(`/orders/track/${order.id}`)}
                  activeOpacity={0.9}
                >
                  <LinearGradient
                    colors={['rgba(255, 255, 255, 0.95)', 'rgba(250, 250, 255, 0.9)']}
                    style={styles.orderGradient}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 1 }}
                  >
                    <View style={styles.orderHeader}>
                      <View>
                        <Text style={styles.orderNumber}>Order #{order.order_number}</Text>
                        <Text style={styles.orderDate}>{formatDate(order.created_at)}</Text>
                      </View>
                      <LinearGradient
                        colors={getStatusGradient(order.status)}
                        style={styles.statusBadge}
                        start={{ x: 0, y: 0 }}
                        end={{ x: 1, y: 1 }}
                      >
                        <Text style={styles.statusText}>{order.status?.toUpperCase()}</Text>
                      </LinearGradient>
                    </View>

                    <View style={styles.orderDetails}>
                      <View style={styles.detailRow}>
                        <Ionicons name="basket-outline" size={16} color={theme.textSecondary} />
                        <Text style={styles.detailText}>
                          {order.items?.length || 0} items
                        </Text>
                      </View>
                      <View style={styles.detailRow}>
                        <Ionicons name="location-outline" size={16} color={theme.textSecondary} />
                        <Text style={styles.detailText} numberOfLines={1}>
                          {order.delivery_address?.street || order.delivery_address?.address_line1 || 'Pickup'}
                        </Text>
                      </View>
                    </View>

                    <View style={styles.orderFooter}>
                      <View>
                        <Text style={styles.totalLabel}>Total</Text>
                        <Text style={styles.totalAmount}>${order.total?.toFixed(2) || '0.00'}</Text>
                      </View>
                      {order.status?.toLowerCase() === 'processing' || order.status?.toLowerCase() === 'confirmed' ? (
                        <TouchableOpacity
                          style={styles.trackButton}
                          onPress={(e) => {
                            e.stopPropagation();
                            router.push(`/orders/track/${order.id}`);
                          }}
                        >
                          <LinearGradient
                            colors={Gradients.primary}
                            style={styles.trackButtonGradient}
                            start={{ x: 0, y: 0 }}
                            end={{ x: 1, y: 1 }}
                          >
                            <Ionicons name="navigate-outline" size={16} color="white" />
                            <Text style={styles.trackButtonText}>Track</Text>
                          </LinearGradient>
                        </TouchableOpacity>
                      ) : (
                        <TouchableOpacity
                          style={styles.viewButton}
                          onPress={(e) => {
                            e.stopPropagation();
                            router.push(`/orders/track/${order.id}`);
                          }}
                        >
                          <Text style={styles.viewButtonText}>View Details</Text>
                          <Ionicons name="chevron-forward" size={16} color={theme.primary} />
                        </TouchableOpacity>
                      )}
                    </View>
                  </LinearGradient>
                </TouchableOpacity>
              ))}
            </View>
          )}
        </ScrollView>
      </SafeAreaView>
    </LinearGradient>
  );
}

const isDark = false;
const theme = isDark ? Colors.dark : Colors.light;

const styles = StyleSheet.create({
  gradientContainer: {
    flex: 1,
  },
  container: {
    flex: 1,
    backgroundColor: 'transparent',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  backButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: theme.text,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 100,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: theme.textSecondary,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
    paddingTop: 100,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: theme.text,
    marginTop: 16,
  },
  emptyText: {
    fontSize: 14,
    color: theme.textSecondary,
    textAlign: 'center',
    marginTop: 8,
    marginBottom: 24,
  },
  shopButton: {
    borderRadius: BorderRadius.xl,
    overflow: 'hidden',
    ...Shadows.medium,
  },
  shopButtonGradient: {
    paddingHorizontal: 24,
    paddingVertical: 12,
  },
  shopButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  ordersList: {
    paddingHorizontal: 16,
  },
  orderCard: {
    marginBottom: 16,
    borderRadius: BorderRadius.xl,
    overflow: 'hidden',
    ...Shadows.colorful,
  },
  orderGradient: {
    padding: 16,
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.5)',
    borderRadius: BorderRadius.xl,
  },
  orderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  orderNumber: {
    fontSize: 16,
    fontWeight: '700',
    color: theme.text,
  },
  orderDate: {
    fontSize: 12,
    color: theme.textSecondary,
    marginTop: 2,
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: BorderRadius.full,
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.5)',
  },
  statusText: {
    fontSize: 11,
    fontWeight: '700',
    color: 'white',
    letterSpacing: 0.5,
  },
  orderDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: theme.border,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    flex: 1,
  },
  detailText: {
    fontSize: 13,
    color: theme.textSecondary,
    flex: 1,
  },
  orderFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  totalLabel: {
    fontSize: 12,
    color: theme.textSecondary,
  },
  totalAmount: {
    fontSize: 20,
    fontWeight: '800',
    color: theme.primary,
  },
  trackButton: {
    borderRadius: BorderRadius.full,
    overflow: 'hidden',
    ...Shadows.small,
  },
  trackButtonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  trackButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  viewButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  viewButtonText: {
    color: theme.primary,
    fontSize: 14,
    fontWeight: '600',
  },
});