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
import { LinearGradient } from 'expo-linear-gradient';
import { Gradients, Colors } from '@/constants/Colors';
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
            headerTransparent: true,
            headerTintColor: Colors.light.text,
          }}
        />
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.light.primary} />
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
            headerTransparent: true,
            headerTintColor: Colors.light.text,
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
          headerTransparent: true,
          headerTintColor: Colors.light.text,
        }}
      />

      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor={Colors.light.primary}
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
          onPress={handleCheckout}
          disabled={loading}
          activeOpacity={0.9}
        >
          <LinearGradient
            colors={loading ? ['#cccccc', '#aaaaaa'] : Gradients.button}
            style={[styles.checkoutButton, loading && styles.disabledButton]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
          >
            {loading ? (
              <ActivityIndicator color="white" />
            ) : (
              <>
                <Text style={styles.checkoutButtonText}>Checkout</Text>
                <Text style={styles.checkoutTotal}>${total.toFixed(2)}</Text>
              </>
            )}
          </LinearGradient>
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