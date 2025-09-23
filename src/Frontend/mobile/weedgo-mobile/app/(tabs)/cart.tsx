import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { Stack, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import useCartStore from '@/stores/cartStore';
import { CartItem } from '@/components/cart/CartItem';
import { OrderSummary } from '@/components/cart/OrderSummary';
import { EmptyCart } from '@/components/cart/EmptyCart';
import { PromoCodeInput } from '@/components/cart/PromoCodeInput';
import { styles } from '@/styles/cart.styles';

export default function CartScreen() {
  const router = useRouter();
  const [refreshing, setRefreshing] = useState(false);

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
      <SafeAreaView style={styles.container}>
        <Stack.Screen
          options={{
            title: 'Cart',
            headerShown: true,
            headerStyle: { backgroundColor: '#1a1a1a' },
            headerTintColor: '#fff',
          }}
        />
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#00ff00" />
          <Text style={styles.loadingText}>Loading cart...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (items.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        <Stack.Screen
          options={{
            title: 'Cart',
            headerShown: true,
            headerStyle: { backgroundColor: '#1a1a1a' },
            headerTintColor: '#fff',
          }}
        />
        <EmptyCart />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <Stack.Screen
        options={{
          title: `Cart (${itemCount})`,
          headerShown: true,
          headerStyle: { backgroundColor: '#1a1a1a' },
          headerTintColor: '#fff',
        }}
      />

      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor="#00ff00"
          />
        }
        contentContainerStyle={styles.scrollContent}
      >
        {/* Cart Items Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Your Items</Text>
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
          <Text style={styles.sectionTitle}>Promo Code</Text>
          <PromoCodeInput />
        </View>

        {/* Order Summary Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Order Summary</Text>
          <OrderSummary />
        </View>

        {/* Checkout Button */}
        <TouchableOpacity
          style={[styles.checkoutButton, loading && styles.disabledButton]}
          onPress={handleCheckout}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#000" />
          ) : (
            <>
              <Text style={styles.checkoutButtonText}>Checkout</Text>
              <Text style={styles.checkoutTotal}>${total.toFixed(2)}</Text>
            </>
          )}
        </TouchableOpacity>

        {/* Minimum order notice if applicable */}
        {total < 50 && (
          <View style={styles.minimumNotice}>
            <Text style={styles.minimumNoticeText}>
              Minimum order is $50. Add ${(50 - total).toFixed(2)} more to checkout.
            </Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}