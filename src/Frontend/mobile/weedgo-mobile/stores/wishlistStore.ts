import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Product } from '@/types/api.types';

interface WishlistItem {
  productId: string;
  product: Product;
  addedAt: Date;
}

interface WishlistStore {
  items: WishlistItem[];
  isLoading: boolean;

  // Actions
  addToWishlist: (product: Product) => Promise<boolean>;
  removeFromWishlist: (productId: string) => Promise<boolean>;
  isInWishlist: (productId: string) => boolean;
  clearWishlist: () => void;
  getWishlistCount: () => number;
  syncWithBackend: () => Promise<void>;
}

export const useWishlistStore = create<WishlistStore>()(
  persist(
    (set, get) => ({
      items: [],
      isLoading: false,

      addToWishlist: async (product: Product) => {
        try {
          const state = get();

          // Check if already in wishlist
          if (state.isInWishlist(product.id)) {
            return false;
          }

          const newItem: WishlistItem = {
            productId: product.id,
            product,
            addedAt: new Date(),
          };

          set((state) => ({
            items: [...state.items, newItem],
          }));

          // Sync with backend if user is logged in
          await get().syncWithBackend();

          return true;
        } catch (error) {
          console.error('Failed to add to wishlist:', error);
          return false;
        }
      },

      removeFromWishlist: async (productId: string) => {
        try {
          set((state) => ({
            items: state.items.filter((item) => item.productId !== productId),
          }));

          // Sync with backend if user is logged in
          await get().syncWithBackend();

          return true;
        } catch (error) {
          console.error('Failed to remove from wishlist:', error);
          return false;
        }
      },

      isInWishlist: (productId: string) => {
        const state = get();
        return state.items.some((item) => item.productId === productId);
      },

      clearWishlist: () => {
        set({ items: [] });
      },

      getWishlistCount: () => {
        const state = get();
        return state.items.length;
      },

      syncWithBackend: async () => {
        try {
          // Get auth token from storage
          const authData = await AsyncStorage.getItem('auth_token');
          if (!authData) return;

          const apiUrl = process.env.EXPO_PUBLIC_API_URL || 'http://10.0.0.29:5024';
          const state = get();

          // Send wishlist to backend
          const response = await fetch(`${apiUrl}/api/wishlist/sync`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${authData}`,
            },
            body: JSON.stringify({
              product_ids: state.items.map((item) => item.productId),
            }),
          });

          if (response.ok) {
            const data = await response.json();

            // Update local wishlist with backend data if needed
            if (data.wishlist) {
              // This would update with full product details from backend
              console.log('Wishlist synced with backend');
            }
          }
        } catch (error) {
          console.error('Failed to sync wishlist with backend:', error);
        }
      },
    }),
    {
      name: 'wishlist-storage',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        items: state.items.map((item) => ({
          productId: item.productId,
          product: {
            id: item.product.id,
            name: item.product.name,
            brand: item.product.brand,
            price: item.product.price,
            image_url: item.product.image_url,
            thc_content: item.product.thc_content,
            cbd_content: item.product.cbd_content,
            strain_type: item.product.strain_type,
            category: item.product.category,
            subCategory: item.product.subCategory,
          },
          addedAt: item.addedAt,
        })),
      }),
    }
  )
);