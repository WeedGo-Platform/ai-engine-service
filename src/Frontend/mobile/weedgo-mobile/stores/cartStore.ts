import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Product } from '@/types/api.types';
import { cartService } from '@/services/api/cart';

interface CartItem {
  product: Product;
  quantity: number;
  size?: string;
}

interface CartStore {
  // State
  items: CartItem[];
  subtotal: number;
  tax: number;
  deliveryFee: number;
  discount: number;
  total: number;
  promoCode: string | null;
  sessionId: string | null;
  loading: boolean;
  error: string | null;

  // Actions
  addToCart: (product: Product, quantity?: number, size?: string) => void;
  removeFromCart: (productId: string) => void;
  updateQuantity: (productId: string, quantity: number) => void;
  clearCart: () => void;
  applyPromoCode: (code: string) => Promise<void>;
  removePromoCode: () => void;
  calculateTotals: () => void;
  syncWithServer: () => Promise<void>;
  getItemCount: () => number;
  getCartItem: (productId: string) => CartItem | undefined;
  setDeliveryFee: (fee: number) => void;
}

const TAX_RATE = 0.13; // 13% tax rate (Ontario HST)

const useCartStore = create<CartStore>()(
  persist(
    (set, get) => ({
      // Initial state
      items: [],
      subtotal: 0,
      tax: 0,
      deliveryFee: 0,
      discount: 0,
      total: 0,
      promoCode: null,
      sessionId: null,
      loading: false,
      error: null,

      // Add item to cart
      addToCart: (product: Product, quantity = 1, size?: string) => {
        const state = get();
        const existingItem = state.items.find(
          item => item.product.id === product.id && item.size === size
        );

        if (existingItem) {
          // Update quantity if item already in cart
          const updatedItems = state.items.map(item =>
            item.product.id === product.id && item.size === size
              ? { ...item, quantity: item.quantity + quantity }
              : item
          );
          set({ items: updatedItems });
        } else {
          // Add new item to cart
          set({
            items: [...state.items, { product, quantity, size }],
          });
        }

        get().calculateTotals();
        get().syncWithServer();
      },

      // Remove item from cart
      removeFromCart: (productId: string) => {
        const state = get();
        const updatedItems = state.items.filter(
          item => item.product.id !== productId
        );
        set({ items: updatedItems });
        get().calculateTotals();
        get().syncWithServer();
      },

      // Update item quantity
      updateQuantity: (productId: string, quantity: number) => {
        const state = get();

        if (quantity <= 0) {
          get().removeFromCart(productId);
          return;
        }

        const updatedItems = state.items.map(item =>
          item.product.id === productId
            ? { ...item, quantity }
            : item
        );

        set({ items: updatedItems });
        get().calculateTotals();
        get().syncWithServer();
      },

      // Clear entire cart
      clearCart: () => {
        set({
          items: [],
          subtotal: 0,
          tax: 0,
          deliveryFee: 0,
          discount: 0,
          total: 0,
          promoCode: null,
        });
        get().syncWithServer();
      },

      // Apply promo code
      applyPromoCode: async (code: string) => {
        set({ loading: true, error: null });

        try {
          // This would typically call the API to validate and apply the promo
          // For now, we'll simulate a discount
          const discount = 10; // Example: $10 off

          set({
            promoCode: code,
            discount,
            loading: false,
          });

          get().calculateTotals();
        } catch (error: any) {
          set({
            error: error.message || 'Invalid promo code',
            loading: false,
          });
        }
      },

      // Remove promo code
      removePromoCode: () => {
        set({ promoCode: null, discount: 0 });
        get().calculateTotals();
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

      // Sync cart with server
      syncWithServer: async () => {
        const state = get();

        // Skip if no items
        if (state.items.length === 0) return;

        try {
          // This would typically sync with the server
          // For now, we'll just log
          console.log('Syncing cart with server...', state.items);
        } catch (error) {
          console.error('Failed to sync cart:', error);
        }
      },

      // Get total item count
      getItemCount: () => {
        return get().items.reduce((sum, item) => sum + item.quantity, 0);
      },

      // Get specific cart item
      getCartItem: (productId: string) => {
        return get().items.find(item => item.product.id === productId);
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
        items: state.items,
        promoCode: state.promoCode,
        deliveryFee: state.deliveryFee,
      }),
    }
  )
);

export default useCartStore;