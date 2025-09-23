import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { IProduct, ICartItem } from '@templates/types';

interface CartState {
  items: ICartItem[];
  total: number;
  subtotal: number;
  tax: number;
  delivery: number;
  discount: number;
  couponCode: string | null;
  isLoading: boolean;
}

const initialState: CartState = {
  items: [],
  total: 0,
  subtotal: 0,
  tax: 0,
  delivery: 0,
  discount: 0,
  couponCode: null,
  isLoading: false,
};

// Helper functions
const calculateTotals = (state: CartState) => {
  state.subtotal = state.items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  state.tax = state.subtotal * 0.13; // Ontario HST
  state.total = state.subtotal + state.tax + state.delivery - state.discount;
};

const saveCartToLocalStorage = (items: ICartItem[]) => {
  localStorage.setItem('cart', JSON.stringify(items));
};

const loadCartFromLocalStorage = (): ICartItem[] => {
  const cartStr = localStorage.getItem('cart');
  if (cartStr) {
    try {
      return JSON.parse(cartStr);
    } catch {
      return [];
    }
  }
  return [];
};

const cartSlice = createSlice({
  name: 'cart',
  initialState,
  reducers: {
    addToCart: (state, action: PayloadAction<{ product: IProduct; quantity: number }>) => {
      const { product, quantity } = action.payload;
      const existingItem = state.items.find((item) => item.product.id === product.id);

      if (existingItem) {
        existingItem.quantity += quantity;
      } else {
        state.items.push({
          id: `${product.id}-${Date.now()}`,
          product,
          quantity,
          price: product.price,
        });
      }

      calculateTotals(state);
      saveCartToLocalStorage(state.items);
    },

    updateQuantity: (
      state,
      action: PayloadAction<{ itemId: string; quantity: number }>
    ) => {
      const { itemId, quantity } = action.payload;
      const item = state.items.find((item) => item.id === itemId);

      if (item) {
        if (quantity <= 0) {
          state.items = state.items.filter((item) => item.id !== itemId);
        } else {
          item.quantity = quantity;
        }
        calculateTotals(state);
        saveCartToLocalStorage(state.items);
      }
    },

    removeFromCart: (state, action: PayloadAction<string>) => {
      state.items = state.items.filter((item) => item.id !== action.payload);
      calculateTotals(state);
      saveCartToLocalStorage(state.items);
    },

    clearCart: (state) => {
      state.items = [];
      state.total = 0;
      state.subtotal = 0;
      state.tax = 0;
      state.delivery = 0;
      state.discount = 0;
      state.couponCode = null;
      localStorage.removeItem('cart');
    },

    setDeliveryFee: (state, action: PayloadAction<number>) => {
      state.delivery = action.payload;
      calculateTotals(state);
    },

    applyCoupon: (
      state,
      action: PayloadAction<{ code: string; discount: number }>
    ) => {
      state.couponCode = action.payload.code;
      state.discount = action.payload.discount;
      calculateTotals(state);
    },

    removeCoupon: (state) => {
      state.couponCode = null;
      state.discount = 0;
      calculateTotals(state);
    },

    restoreCart: (state) => {
      state.items = loadCartFromLocalStorage();
      calculateTotals(state);
    },

    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
  },
});

export const {
  addToCart,
  updateQuantity,
  removeFromCart,
  clearCart,
  setDeliveryFee,
  applyCoupon,
  removeCoupon,
  restoreCart,
  setLoading,
} = cartSlice.actions;

// Alias for compatibility
export const addItem = (item: {
  id: string;
  sku: string;
  name: string;
  price: number;
  quantity: number;
  image?: string;
  max_quantity?: number;
  thc?: number;
  cbd?: number;
  brand?: string;
  category?: string;
  maxQuantity?: number;
  size?: string;
  weight?: number;
  unit?: string;
  strain?: string;
}) => {
  return addToCart({
    product: {
      id: item.id,
      sku: item.sku,
      name: item.name,
      description: '',
      category: item.category || '',
      brand: item.brand || '',
      price: item.price,
      thc_content: item.thc || 0,
      cbd_content: item.cbd || 0,
      image_url: item.image || '',
      in_stock: true,
      quantity_available: item.maxQuantity || item.max_quantity || 100,
      unit_weight: item.size || (item.weight ? `${item.weight}${item.unit || 'g'}` : ''),
    },
    quantity: item.quantity
  });
};

// Alias for removeFromCart
export const removeItem = removeFromCart;

export default cartSlice.reducer;

// Selectors
export const selectCartItemsCount = (state: { cart: CartState }) =>
  state.cart.items.reduce((count, item) => count + item.quantity, 0);

export const selectCartTotal = (state: { cart: CartState }) => state.cart.total;

export const selectIsCartEmpty = (state: { cart: CartState }) =>
  state.cart.items.length === 0;