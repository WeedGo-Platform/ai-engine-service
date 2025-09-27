import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Platform,
  Dimensions,
  StyleSheet,
} from 'react-native';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { BlurView } from 'expo-blur';
import { Ionicons } from '@expo/vector-icons';
import { Gradients, Colors, BorderRadius, Shadows } from '@/constants/Colors';
import { useTheme } from '@/contexts/ThemeContext';
import useCartStore from '@/stores/cartStore';
import { CartItem } from '@/components/cart/CartItem';
import { OrderSummary } from '@/components/cart/OrderSummary';
import { EmptyCart } from '@/components/cart/EmptyCart';
import { PromoCodeInput } from '@/components/cart/PromoCodeInput';

const { width } = Dimensions.get('window');

export default function CartScreen() {
  const router = useRouter();
  const [refreshing, setRefreshing] = useState(false);
  const { theme, isDark } = useTheme();

  const {
    items,
    subtotal,
    tax,
    deliveryFee,
    discount,
    total,
    loading,
    loadSession,
    validateCart,
    getItemCount,
    refreshCart,
  } = useCartStore();

  const styles = React.useMemo(() => createStyles(theme, isDark), [theme, isDark]);

  // Load cart on mount
  useEffect(() => {
    loadSession();
  }, []);

  // Handle pull to refresh
  const handleRefresh = async () => {
    setRefreshing(true);
    await refreshCart();
    setRefreshing(false);
  };

  // Handle checkout
  const handleCheckout = async () => {
    const isValid = await validateCart();
    if (isValid) {
      router.push('/checkout/');
    }
  };

  // Get total item count
  const itemCount = getItemCount();

  if (loading && items.length === 0) {
    return (
      <View style={styles.container}>
        <LinearGradient
          colors={isDark ? [theme.background, theme.backgroundSecondary, theme.surface] : [theme.gradientStart, theme.gradientMid, theme.gradientEnd]}
          style={styles.gradient}
          start={{ x: 0, y: 0 }}
          end={{ x: 0.5, y: 1 }}
        >
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={theme.primary} />
            <Text style={styles.loadingText}>Loading cart...</Text>
          </View>
        </LinearGradient>
      </View>
    );
  }

  if (items.length === 0) {
    return (
      <View style={styles.container}>
        <LinearGradient
          colors={isDark ? [theme.background, theme.backgroundSecondary, theme.surface] : [theme.gradientStart, theme.gradientMid, theme.gradientEnd]}
          style={styles.gradient}
          start={{ x: 0, y: 0 }}
          end={{ x: 0.5, y: 1 }}
        >
          <EmptyCart />
        </LinearGradient>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={isDark ? [theme.background, theme.backgroundSecondary, theme.surface] : [theme.gradientStart, theme.gradientMid, theme.gradientEnd]}
        style={styles.gradient}
        start={{ x: 0, y: 0 }}
        end={{ x: 0.5, y: 1 }}
      >
        {/* Header Section - Simplified without title */}
        <View style={styles.header}>
          <View style={styles.headerInfo}>
            <Text style={styles.headerSubtitle}>
              {itemCount} {itemCount === 1 ? 'item' : 'items'} in cart
            </Text>
            <TouchableOpacity onPress={handleRefresh} style={styles.refreshButton}>
              <Ionicons name="refresh" size={20} color={theme.primary} />
            </TouchableOpacity>
          </View>
        </View>

        <ScrollView
          style={styles.scrollView}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={handleRefresh}
              tintColor={theme.primary}
            />
          }
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Cart Items Section */}
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Ionicons name="basket" size={20} color={theme.primary} />
              <Text style={styles.sectionTitle}>Your Items</Text>
            </View>
            <View style={styles.itemsList}>
              {items.map((item, index) => (
                <CartItem
                  key={item.sku || `${item.product.id}-${index}`}
                  item={item}
                />
              ))}
            </View>
          </View>

          {/* Promo Code Section */}
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Ionicons name="pricetag" size={20} color={theme.strainHybrid} />
              <Text style={styles.sectionTitle}>Promo Code</Text>
            </View>
            <PromoCodeInput />
          </View>

          {/* Order Summary Section */}
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Ionicons name="receipt" size={20} color={theme.strainCBD} />
              <Text style={styles.sectionTitle}>Order Summary</Text>
            </View>
            <OrderSummary />
          </View>

          {/* Minimum order notice if applicable */}
          {total < 50 && (
            <LinearGradient
              colors={['rgba(255, 193, 7, 0.1)', 'rgba(255, 152, 0, 0.1)']}
              style={styles.minimumNotice}
            >
              <Ionicons name="information-circle" size={24} color="#FFA000" />
              <Text style={styles.minimumNoticeText}>
                Minimum order is $50. Add ${(50 - total).toFixed(2)} more to checkout.
              </Text>
            </LinearGradient>
          )}

          {/* Spacer for bottom button */}
          <View style={{ height: 100 }} />
        </ScrollView>

        {/* Floating Checkout Button */}
        <View style={styles.checkoutContainer}>
          <TouchableOpacity
            onPress={handleCheckout}
            disabled={loading || total < 50}
            activeOpacity={0.9}
            style={styles.checkoutButtonWrapper}
          >
            <LinearGradient
              colors={loading || total < 50 ? ['#666', '#444'] : ['#00D084', '#00F5A0']}
              style={styles.checkoutButton}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
            >
              {loading ? (
                <ActivityIndicator color="white" />
              ) : (
                <>
                  <View style={styles.checkoutContent}>
                    <Ionicons name="card" size={24} color="white" />
                    <Text style={styles.checkoutButtonText}>Checkout</Text>
                  </View>
                  <View style={styles.checkoutTotalContainer}>
                    <Text style={styles.checkoutTotalLabel}>Total</Text>
                    <Text style={styles.checkoutTotal}>${total.toFixed(2)}</Text>
                  </View>
                </>
              )}
            </LinearGradient>
          </TouchableOpacity>
        </View>
      </LinearGradient>
    </View>
  );
}

const createStyles = (theme: any, isDark: boolean) => StyleSheet.create({
  container: {
    flex: 1,
  },
  gradient: {
    flex: 1,
  },
  header: {
    paddingTop: Platform.OS === 'ios' ? 50 : 40,
    paddingHorizontal: 20,
    paddingBottom: 16,
  },
  headerInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerSubtitle: {
    fontSize: 18,
    color: theme.text,
    fontWeight: '600',
  },
  refreshButton: {
    padding: 8,
    borderRadius: BorderRadius.full,
    backgroundColor: theme.glass,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 20,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: theme.textSecondary,
  },
  section: {
    marginTop: 20,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
    marginHorizontal: 20,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: theme.text,
  },
  itemsList: {
    marginBottom: 8,
  },
  minimumNotice: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 20,
    marginTop: 20,
    padding: 16,
    borderRadius: BorderRadius.xl,
    gap: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 193, 7, 0.3)',
  },
  minimumNoticeText: {
    flex: 1,
    fontSize: 14,
    color: theme.text,
    fontWeight: '500',
  },
  checkoutContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: theme.glass,
    borderTopLeftRadius: BorderRadius.xxl,
    borderTopRightRadius: BorderRadius.xxl,
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: Platform.OS === 'ios' ? 100 : 80,
    ...Shadows.large,
  },
  checkoutButtonWrapper: {
    width: '100%',
  },
  checkoutButton: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 18,
    paddingHorizontal: 24,
    borderRadius: BorderRadius.xxl,
    overflow: 'hidden',
    ...Shadows.colorful,
  },
  checkoutContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  checkoutButtonText: {
    fontSize: 18,
    fontWeight: '700',
    color: 'white',
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 3,
  },
  checkoutTotalContainer: {
    alignItems: 'flex-end',
  },
  checkoutTotalLabel: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.8)',
    marginBottom: 2,
  },
  checkoutTotal: {
    fontSize: 22,
    fontWeight: '800',
    color: 'white',
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 3,
  },
});