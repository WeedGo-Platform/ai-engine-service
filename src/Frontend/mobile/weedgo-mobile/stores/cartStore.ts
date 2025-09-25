import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Product, Cart, CartItem as ApiCartItem } from '@/types/api.types';
import { cartService } from '@/services/api/cart';
import { Alert } from 'react-native';
import Toast from 'react-native-toast-message';

interface CartItem {
  id?: string;
  product: Product;
  quantity: number;
  size?: string;
  sku: string;
  price: number;
  subtotal: number;
  image?: string;
  name: string;
}

interface CartStore {
  // State
  sessionId: string | null;
  items: CartItem[];
  subtotal: number;
  tax: number;
  deliveryFee: number;
  discount: number;
  total: number;
  promoCode: string | null;
  loading: boolean;
  error: string | null;
  minimumOrder: number;

  // Session management
  createSession: () => Promise<void>;
  loadSession: () => Promise<void>;

  // Item management
  addItem: (product: Product, quantity?: number, size?: string) => Promise<void>;
  updateQuantity: (sku: string, quantity: number) => Promise<void>;
  removeItem: (sku: string) => Promise<void>;
  clearCart: () => Promise<void>;

  // Promotions
  applyPromoCode: (code: string) => Promise<void>;
  removePromoCode: () => Promise<void>;

  // Calculations
  calculateTotals: () => void;
  validateCart: () => Promise<boolean>;

  // Helpers
  syncWithServer: () => Promise<void>;
  getItemCount: () => number;
  getCartItem: (sku: string) => CartItem | undefined;
  setDeliveryFee: (fee: number) => void;
  refreshCart: () => Promise<void>;
}

const TAX_RATE = 0.13; // 13% tax rate (Ontario HST)
const MINIMUM_ORDER_AMOUNT = 50; // Minimum order amount in dollars

const useCartStore = create<CartStore>()(
  persist(
    (set, get) => ({
      // Initial state
      sessionId: null,
      items: [],
      subtotal: 0,
      tax: 0,
      deliveryFee: 0,
      discount: 0,
      total: 0,
      promoCode: null,
      loading: false,
      error: null,
      minimumOrder: MINIMUM_ORDER_AMOUNT,

      // Session management
      createSession: async () => {
        try {
          const sessionId = await cartService.createSession();
          set({ sessionId });
        } catch (error: any) {
          console.error('Failed to create cart session:', error);
          set({ error: error.message });
        }
      },

      loadSession: async () => {
        try {
          set({ loading: true, error: null });
          await cartService.initialize();
          const cart = await cartService.getCart();

          // Convert API cart items to local cart items, filtering out invalid items
          const items: CartItem[] = cart.items
            .filter(item => item && (item.product || item.product_id))
            .map(item => ({
              id: item.id,
              product: item.product || {} as Product,
              quantity: item.quantity || 1,
              sku: item.product?.sku || item.sku || item.product_id || '',
              price: item.price || 0,
              subtotal: item.subtotal || 0,
              image: item.product?.image_url || item.product?.image || (item.product?.images && item.product.images[0]) || item.image_url || '',
              name: item.product?.name || item.name || 'Unknown Product',
              size: item.product?.size || item.size,
            }));

          set({
            sessionId: cart.session_id,
            items,
            subtotal: cart.subtotal,
            tax: cart.tax,
            deliveryFee: cart.delivery_fee || 0,
            discount: cart.discount || 0,
            total: cart.total,
            promoCode: cart.promo_code || null,
            loading: false,
          });
        } catch (error: any) {
          console.error('Failed to load cart session:', error);
          set({ loading: false, error: error.message });
        }
      },

      // Add item to cart
      addItem: async (product: Product, quantity = 1, size?: string) => {
        const state = get();

        // Ensure we have a session
        if (!state.sessionId) {
          await get().createSession();
        }

        set({ loading: true, error: null });

        try {
          const response = await cartService.addItem({
            product_id: product.id,
            quantity,
            size: size || product.size,
            // Include required fields for API
            sku: product.sku,
            name: product.name,
            category: product.category,
            price: product.price
          });

          // Refresh cart from server
          await get().refreshCart();

          // Show success toast
          Toast.show({
            type: 'success',
            text1: 'Added to Cart',
            text2: `${product.name} added to your cart`,
            position: 'bottom',
          });
        } catch (error: any) {
          console.error('Failed to add item to cart:', error);
          const errorMessage = error.response?.data?.message || error.message || 'Could not add item to cart';
          set({ loading: false, error: errorMessage });

          Toast.show({
            type: 'error',
            text1: 'Error',
            text2: errorMessage,
            position: 'bottom',
          });
        }
      },

      // Remove item from cart
      removeItem: async (sku: string) => {
        const state = get();
        const item = state.items.find(i => i.sku === sku);

        if (!item || !item.id) return;

        set({ loading: true, error: null });

        try {
          await cartService.removeItem(item.id);
          await get().refreshCart();

          Toast.show({
            type: 'success',
            text1: 'Removed from Cart',
            text2: `${item.name} removed`,
            position: 'bottom',
          });
        } catch (error: any) {
          console.error('Failed to remove item from cart:', error);
          set({ loading: false, error: error.message });

          Toast.show({
            type: 'error',
            text1: 'Error',
            text2: 'Could not remove item',
            position: 'bottom',
          });
        }
      },

      // Update item quantity
      updateQuantity: async (sku: string, quantity: number) => {
        const state = get();
        const item = state.items.find(i => i.sku === sku);

        if (!item || !item.id) return;

        if (quantity <= 0) {
          await get().removeItem(sku);
          return;
        }

        set({ loading: true, error: null });

        try {
          await cartService.updateItem(item.id, quantity);
          await get().refreshCart();
        } catch (error: any) {
          console.error('Failed to update item quantity:', error);
          set({ loading: false, error: error.message });

          Toast.show({
            type: 'error',
            text1: 'Error',
            text2: 'Could not update quantity',
            position: 'bottom',
          });
        }
      },

      // Clear entire cart
      clearCart: async () => {
        set({ loading: true, error: null });

        try {
          await cartService.clearCart();

          set({
            sessionId: null,
            items: [],
            subtotal: 0,
            tax: 0,
            deliveryFee: 0,
            discount: 0,
            total: 0,
            promoCode: null,
            loading: false,
          });

          Toast.show({
            type: 'success',
            text1: 'Cart Cleared',
            text2: 'Your cart has been emptied',
            position: 'bottom',
          });
        } catch (error: any) {
          console.error('Failed to clear cart:', error);
          set({ loading: false, error: error.message });
        }
      },

      // Apply promo code
      applyPromoCode: async (code: string) => {
        if (!code.trim()) {
          Toast.show({
            type: 'error',
            text1: 'Error',
            text2: 'Please enter a promo code',
            position: 'bottom',
          });
          return;
        }

        set({ loading: true, error: null });

        try {
          const response = await cartService.applyPromoCode(code);

          if (response.success) {
            await get().refreshCart();

            Toast.show({
              type: 'success',
              text1: 'Promo Code Applied',
              text2: `You saved $${response.discount.toFixed(2)}!`,
              position: 'bottom',
            });
          } else {
            throw new Error('Invalid promo code');
          }
        } catch (error: any) {
          console.error('Failed to apply promo code:', error);
          set({ loading: false, error: error.message });

          Toast.show({
            type: 'error',
            text1: 'Invalid Code',
            text2: 'The promo code you entered is not valid',
            position: 'bottom',
          });
        }
      },

      // Remove promo code
      removePromoCode: async () => {
        set({ loading: true, error: null });

        try {
          await cartService.removePromoCode();
          await get().refreshCart();

          Toast.show({
            type: 'info',
            text1: 'Promo Code Removed',
            text2: 'Your promo code has been removed',
            position: 'bottom',
          });
        } catch (error: any) {
          console.error('Failed to remove promo code:', error);
          set({ loading: false, error: error.message });
        }
      },

      // Calculate cart totals
      calculateTotals: () => {
        const state = get();
        const subtotal = state.items.reduce(
          (sum, item) => sum + item.product.price * item.quantity,
          0
        );

        const taxableAmount = subtotal - state.discount;
        const tax = taxableAmount * TAX_RATE;
        const total = taxableAmount + tax + state.deliveryFee;

        set({
          subtotal: parseFloat(subtotal.toFixed(2)),
          tax: parseFloat(tax.toFixed(2)),
          total: parseFloat(total.toFixed(2)),
        });
      },

      // Validate cart before checkout
      validateCart: async (): Promise<boolean> => {
        const state = get();

        if (state.items.length === 0) {
          Alert.alert(
            'Empty Cart',
            'Your cart is empty. Add some items to continue.',
            [{ text: 'OK' }]
          );
          return false;
        }

        set({ loading: true, error: null });

        try {
          const validation = await cartService.validateCart();

          if (!validation.valid) {
            Alert.alert(
              'Cart Issues',
              validation.issues.join('\n'),
              [
                {
                  text: 'Update Cart',
                  onPress: () => get().refreshCart()
                },
                {
                  text: 'Cancel',
                  style: 'cancel'
                }
              ]
            );
            set({ loading: false });
            return false;
          }

          // Check minimum order amount
          if (state.total < state.minimumOrder) {
            const remaining = state.minimumOrder - state.total;
            Alert.alert(
              'Minimum Order',
              `Minimum order is $${state.minimumOrder}. Add $${remaining.toFixed(2)} more to continue.`,
              [{ text: 'OK' }]
            );
            set({ loading: false });
            return false;
          }

          set({ loading: false });
          return true;
        } catch (error: any) {
          console.error('Failed to validate cart:', error);
          set({ loading: false, error: error.message });
          return false;
        }
      },

      // Refresh cart from server
      refreshCart: async () => {
        const state = get();

        if (!state.sessionId) return;

        try {
          const cart = await cartService.getCart();

          // Convert API cart items to local cart items, filtering out invalid items
          const items: CartItem[] = cart.items
            .filter(item => item && (item.product || item.product_id))
            .map(item => ({
              id: item.id,
              product: item.product || {} as Product,
              quantity: item.quantity || 1,
              sku: item.product?.sku || item.sku || item.product_id || '',
              price: item.price || 0,
              subtotal: item.subtotal || 0,
              image: item.product?.image_url || item.product?.image || (item.product?.images && item.product.images[0]) || item.image_url || '',
              name: item.product?.name || item.name || 'Unknown Product',
              size: item.product?.size || item.size,
            }));

          set({
            items,
            subtotal: cart.subtotal,
            tax: cart.tax,
            deliveryFee: cart.delivery_fee || 0,
            discount: cart.discount || 0,
            total: cart.total,
            promoCode: cart.promo_code || null,
            loading: false,
          });
        } catch (error: any) {
          console.error('Failed to refresh cart:', error);
          set({ loading: false });
        }
      },

      // Sync cart with server (legacy compatibility)
      syncWithServer: async () => {
        await get().refreshCart();
      },

      // Get total item count
      getItemCount: () => {
        return get().items.reduce((sum, item) => sum + item.quantity, 0);
      },

      // Get specific cart item
      getCartItem: (sku: string) => {
        return get().items.find(item => item.sku === sku);
      },

      // Set delivery fee
      setDeliveryFee: (fee: number) => {
        set({ deliveryFee: fee });
        get().calculateTotals();
      },
    }),
    {
      name: 'weedgo-cart-storage',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        sessionId: state.sessionId,
        items: state.items,
        promoCode: state.promoCode,
        deliveryFee: state.deliveryFee,
      }),
    }
  )
);

export default useCartStore;
export { useCartStore };