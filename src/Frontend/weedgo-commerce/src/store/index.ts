import { configureStore } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import authSlice from '@features/auth/authSlice';
import cartSlice from '@features/cart/cartSlice';
import productsSlice from '@features/products/productsSlice';
import chatSlice from '@features/chat/chatSlice';
import deliverySlice from '@features/delivery/deliverySlice';
import reviewsSlice from '@features/reviews/reviewsSlice';
import wishlistSlice from '@features/wishlist/wishlistSlice';
import storeSlice from '@features/store/storeSlice';

export const store = configureStore({
  reducer: {
    auth: authSlice,
    cart: cartSlice,
    products: productsSlice,
    chat: chatSlice,
    delivery: deliverySlice,
    reviews: reviewsSlice,
    wishlist: wishlistSlice,
    store: storeSlice,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore these action types
        ignoredActions: ['chat/messageReceived', 'auth/setUser'],
        // Ignore these field paths in all actions
        ignoredActionPaths: ['payload.timestamp', 'meta.arg'],
        // Ignore these paths in the state
        ignoredPaths: ['chat.messages'],
      },
    }),
  devTools: import.meta.env.DEV,
});

setupListeners(store.dispatch);

// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;