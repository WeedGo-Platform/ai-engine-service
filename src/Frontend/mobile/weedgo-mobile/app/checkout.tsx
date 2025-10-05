import React, { useState, useEffect } from 'react';
import {
  View,
  ScrollView,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Stack, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuthStore } from '@/stores/authStore';
import { useCartStore } from '@/stores/cartStore';
import { useOrderStore } from '@/stores/orderStore';
import { useProfileStore } from '@/stores/profileStore';
import { useStoreStore } from '@/stores/storeStore';
import { formatShortAddress } from '@/utils/formatters';
import { DeliveryMethodToggle } from '@/components/checkout/DeliveryMethodToggle';
import { AddressSection } from '@/components/checkout/AddressSection';
import { PaymentSection } from '@/components/checkout/PaymentSection';
import { OrderSummary } from '@/components/checkout/OrderSummary';
import { useDeliveryFee } from '@/hooks/useDeliveryFee';
import Toast from 'react-native-toast-message';
import { Ionicons } from '@expo/vector-icons';

export default function CheckoutScreen() {
  const router = useRouter();
  const { user } = useAuthStore();
  const { items, subtotal, tax, total, sessionId, clearCart, discount, promoCode } = useCartStore();
  const { createOrder } = useOrderStore();
  const { getCheckoutDefaults, defaultAddress, defaultPayment } = useProfileStore();
  const { currentStore: selectedStore } = useStoreStore();

  // Pre-select defaults for 3-tap checkout
  const defaults = getCheckoutDefaults();
  const [deliveryMethod, setDeliveryMethod] = useState<'delivery' | 'pickup'>(defaults.deliveryMethod);
  const [selectedAddress, setSelectedAddress] = useState(defaults.address);
  const [selectedPayment, setSelectedPayment] = useState(defaults.paymentMethod);
  const [tipPercentage, setTipPercentage] = useState(defaults.tipPercentage);
  const [specialInstructions, setSpecialInstructions] = useState('');
  const [pickupTime, setPickupTime] = useState<string | null>(null);
  const [ageVerified, setAgeVerified] = useState(true); // Should be verified during registration
  const [loading, setLoading] = useState(false);

  // Calculate delivery fee based on address
  const { fee: deliveryFee, estimatedTime, available: deliveryAvailable } = useDeliveryFee(
    selectedAddress,
    selectedStore?.id || ''
  );

  // Calculate order totals - FIXED: Include discount in calculation
  const tipAmount = subtotal * tipPercentage;
  const orderTotal = subtotal - discount + tax + (deliveryMethod === 'delivery' ? deliveryFee : 0) + tipAmount;

  // Check if ready to order
  const canPlaceOrder = () => {
    if (!user) return false;
    if (items.length === 0) return false;
    if (!selectedPayment) return false;
    if (deliveryMethod === 'delivery' && !selectedAddress) return false;
    if (deliveryMethod === 'delivery' && !deliveryAvailable) return false;
    if (deliveryMethod === 'pickup' && !pickupTime) return false;
    if (!ageVerified) return false;
    return true;
  };

  // Handle place order - This is the 3rd and final tap!
  const handlePlaceOrder = async () => {
    if (!canPlaceOrder()) {
      Toast.show({
        type: 'error',
        text1: 'Missing Information',
        text2: 'Please complete all required fields',
      });
      return;
    }

    try {
      setLoading(true);

      const orderData = {
        cart_session_id: sessionId!,
        user_id: user!.id,
        store_id: selectedStore!.id,
        delivery_type: deliveryMethod,
        delivery_address: deliveryMethod === 'delivery' ? selectedAddress! : undefined,
        pickup_time: deliveryMethod === 'pickup' ? pickupTime! : undefined,
        payment_method_id: selectedPayment!.id,
        tip_amount: tipAmount,
        special_instructions: specialInstructions || undefined,
      };

      const order = await createOrder(orderData);

      // Navigate to confirmation screen
      router.replace(`/checkout/confirmation?orderId=${order.id}`);
    } catch (error: any) {
      console.error('Order creation failed:', error);
      Alert.alert(
        'Order Failed',
        error.message || 'Unable to place your order. Please try again.',
        [{ text: 'OK' }]
      );
    } finally {
      setLoading(false);
    }
  };

  // Handle back navigation
  const handleBack = () => {
    router.back();
  };

  // Validate minimum order amount
  const meetsMinimum = subtotal >= 50; // $50 minimum

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <Stack.Screen
        options={{
          headerShown: true,
          headerTitle: 'Checkout',
          headerLeft: () => (
            <TouchableOpacity onPress={handleBack} style={styles.headerButton}>
              <Ionicons name="arrow-back" size={24} color="#333" />
            </TouchableOpacity>
          ),
        }}
      />

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Delivery Method Toggle */}
          <DeliveryMethodToggle
            value={deliveryMethod}
            onChange={setDeliveryMethod}
            deliveryAvailable={deliveryAvailable}
          />

          {/* Delivery/Pickup Details */}
          {deliveryMethod === 'delivery' ? (
            <AddressSection
              selectedAddress={selectedAddress}
              onSelectAddress={setSelectedAddress}
              estimatedTime={estimatedTime}
            />
          ) : (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Pickup Details</Text>
              <View style={styles.pickupInfo}>
                <Text style={styles.storeName}>{selectedStore?.name}</Text>
                <Text style={styles.storeAddress}>
                  {formatShortAddress(selectedStore?.address)}
                </Text>
                <TouchableOpacity
                  style={styles.timeSelector}
                  onPress={() => {
                    // TODO: Show time picker modal
                    setPickupTime('ASAP (15-20 mins)');
                  }}
                >
                  <Ionicons name="time-outline" size={20} color="#666" />
                  <Text style={styles.timeSelectorText}>
                    {pickupTime || 'Select pickup time'}
                  </Text>
                  <Ionicons name="chevron-down" size={20} color="#666" />
                </TouchableOpacity>
              </View>
            </View>
          )}

          {/* Payment Method */}
          <PaymentSection
            selectedPayment={selectedPayment}
            onSelectPayment={setSelectedPayment}
          />

          {/* Special Instructions */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Special Instructions (Optional)</Text>
            <TouchableOpacity
              style={styles.instructionsInput}
              onPress={() => {
                // TODO: Show text input modal
                Alert.prompt(
                  'Special Instructions',
                  'Add any special delivery or preparation instructions',
                  [
                    { text: 'Cancel', style: 'cancel' },
                    {
                      text: 'Save',
                      onPress: (text) => setSpecialInstructions(text || ''),
                    },
                  ],
                  'plain-text',
                  specialInstructions
                );
              }}
            >
              <Text
                style={[
                  styles.instructionsText,
                  !specialInstructions && styles.placeholderText,
                ]}
                numberOfLines={2}
              >
                {specialInstructions || 'Add delivery or preparation instructions...'}
              </Text>
              <Ionicons name="pencil" size={20} color="#666" />
            </TouchableOpacity>
          </View>

          {/* Order Summary with Tip Selector */}
          <OrderSummary
            subtotal={subtotal}
            tax={tax}
            deliveryFee={deliveryMethod === 'delivery' ? deliveryFee : 0}
            tipPercentage={tipPercentage}
            tipAmount={tipAmount}
            total={orderTotal}
            discount={discount}
            promoCode={promoCode}
            onTipChange={setTipPercentage}
          />

          {/* Minimum Order Warning */}
          {!meetsMinimum && (
            <View style={styles.warningBanner}>
              <Ionicons name="warning" size={20} color="#FF6B6B" />
              <Text style={styles.warningText}>
                Minimum order amount is $50. Add ${(50 - subtotal).toFixed(2)} more to checkout.
              </Text>
            </View>
          )}

          {/* Age Verification */}
          <TouchableOpacity
            style={styles.ageVerification}
            onPress={() => setAgeVerified(!ageVerified)}
          >
            <View style={[styles.checkbox, ageVerified && styles.checkboxChecked]}>
              {ageVerified && <Ionicons name="checkmark" size={16} color="#FFF" />}
            </View>
            <Text style={styles.ageText}>
              I confirm that I am 19 years of age or older
            </Text>
          </TouchableOpacity>
        </ScrollView>

        {/* Fixed Bottom: Place Order Button */}
        <View style={styles.bottomContainer}>
          <TouchableOpacity
            style={[
              styles.placeOrderButton,
              (!canPlaceOrder() || !meetsMinimum || loading) && styles.buttonDisabled,
            ]}
            onPress={handlePlaceOrder}
            disabled={!canPlaceOrder() || !meetsMinimum || loading}
          >
            {loading ? (
              <ActivityIndicator size="small" color="#FFF" />
            ) : (
              <>
                <Text style={styles.placeOrderText}>Place Order</Text>
                <Text style={styles.placeOrderAmount}>${orderTotal.toFixed(2)}</Text>
              </>
            )}
          </TouchableOpacity>

          {/* Safe area for home indicator */}
          <View style={styles.safeBottom} />
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  headerButton: {
    padding: 8,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 20,
  },
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
  pickupInfo: {
    gap: 8,
  },
  storeName: {
    fontSize: 15,
    fontWeight: '500',
    color: '#333',
  },
  storeAddress: {
    fontSize: 14,
    color: '#666',
  },
  timeSelector: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F8F9FA',
    padding: 12,
    borderRadius: 8,
    marginTop: 8,
    gap: 8,
  },
  timeSelectorText: {
    flex: 1,
    fontSize: 14,
    color: '#333',
  },
  instructionsInput: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F8F9FA',
    padding: 12,
    borderRadius: 8,
    minHeight: 60,
  },
  instructionsText: {
    flex: 1,
    fontSize: 14,
    color: '#333',
    lineHeight: 20,
  },
  placeholderText: {
    color: '#999',
  },
  warningBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF5F5',
    margin: 16,
    padding: 12,
    borderRadius: 8,
    gap: 8,
  },
  warningText: {
    flex: 1,
    fontSize: 13,
    color: '#FF6B6B',
  },
  ageVerification: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    gap: 12,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderWidth: 2,
    borderColor: '#DDD',
    borderRadius: 4,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkboxChecked: {
    backgroundColor: '#27AE60',
    borderColor: '#27AE60',
  },
  ageText: {
    fontSize: 14,
    color: '#333',
    flex: 1,
  },
  bottomContainer: {
    backgroundColor: '#FFF',
    paddingHorizontal: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#EEE',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 5,
  },
  placeOrderButton: {
    backgroundColor: '#27AE60',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 12,
    gap: 8,
  },
  buttonDisabled: {
    backgroundColor: '#CCC',
  },
  placeOrderText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFF',
  },
  placeOrderAmount: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFF',
  },
  safeBottom: {
    height: Platform.OS === 'ios' ? 20 : 16,
  },
});