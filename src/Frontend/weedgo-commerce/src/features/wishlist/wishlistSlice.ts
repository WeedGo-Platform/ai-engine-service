/**
 * Redux slice for wishlist management
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import apiClient from '@api/client';
import toast from 'react-hot-toast';

// Types
export interface WishlistItem {
  id: string;
  productId: string;
  userId: string;
  product: {
    id: string;
    sku: string;
    name: string;
    price: number;
    images: string[];
    category: string;
    brand: string;
    strain?: string;
    thc?: number;
    cbd?: number;
    inStock: boolean;
    rating?: number;
    reviewCount?: number;
  };
  addedAt: string;
}

interface WishlistState {
  items: WishlistItem[];
  itemIds: Set<string>; // For quick lookup
  isLoading: boolean;
  isAdding: boolean;
  isRemoving: boolean;
  error: string | null;
  total: number;
}

const initialState: WishlistState = {
  items: [],
  itemIds: new Set(),
  isLoading: false,
  isAdding: false,
  isRemoving: false,
  error: null,
  total: 0,
};

// Async thunks
export const fetchWishlist = createAsyncThunk(
  'wishlist/fetchWishlist',
  async () => {
    const response = await apiClient.get('/api/wishlist');
    return response.data.items;
  }
);

export const addToWishlist = createAsyncThunk(
  'wishlist/addToWishlist',
  async (productId: string) => {
    const response = await apiClient.post('/api/wishlist', { product_id: productId });
    return response.data;
  }
);

export const removeFromWishlist = createAsyncThunk(
  'wishlist/removeFromWishlist',
  async (productId: string) => {
    await apiClient.delete(`/api/wishlist/${productId}`);
    return productId;
  }
);

export const clearWishlist = createAsyncThunk(
  'wishlist/clearWishlist',
  async () => {
    await apiClient.delete('/api/wishlist');
    return;
  }
);

export const moveToCart = createAsyncThunk(
  'wishlist/moveToCart',
  async (productId: string, { dispatch }) => {
    // First add to cart
    const response = await apiClient.post('/api/cart', {
      product_id: productId,
      quantity: 1,
    });

    // Then remove from wishlist
    await dispatch(removeFromWishlist(productId));

    return response.data;
  }
);

export const checkWishlistItem = createAsyncThunk(
  'wishlist/checkItem',
  async (productId: string) => {
    const response = await apiClient.get(`/api/wishlist/check/${productId}`);
    return {
      productId,
      isInWishlist: response.data.is_in_wishlist,
    };
  }
);

// Slice
const wishlistSlice = createSlice({
  name: 'wishlist',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    syncWishlistFromStorage: (state) => {
      // Sync from localStorage (for offline support)
      const savedWishlist = localStorage.getItem('wishlist');
      if (savedWishlist) {
        try {
          const items = JSON.parse(savedWishlist);
          state.items = items;
          state.itemIds = new Set(items.map((item: WishlistItem) => item.productId));
          state.total = items.length;
        } catch (error) {
          // Invalid data in localStorage
        }
      }
    },
  },
  extraReducers: (builder) => {
    // Fetch wishlist
    builder
      .addCase(fetchWishlist.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchWishlist.fulfilled, (state, action) => {
        state.items = action.payload;
        state.itemIds = new Set(action.payload.map((item: WishlistItem) => item.productId));
        state.total = action.payload.length;
        state.isLoading = false;

        // Save to localStorage for offline support
        localStorage.setItem('wishlist', JSON.stringify(action.payload));
      })
      .addCase(fetchWishlist.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch wishlist';
      });

    // Add to wishlist
    builder
      .addCase(addToWishlist.pending, (state) => {
        state.isAdding = true;
        state.error = null;
      })
      .addCase(addToWishlist.fulfilled, (state, action) => {
        const newItem = action.payload;

        // Check if item already exists
        if (!state.itemIds.has(newItem.productId)) {
          state.items.unshift(newItem);
          state.itemIds.add(newItem.productId);
          state.total += 1;

          // Update localStorage
          localStorage.setItem('wishlist', JSON.stringify(state.items));

          toast.success('Added to wishlist');
        }

        state.isAdding = false;
      })
      .addCase(addToWishlist.rejected, (state, action) => {
        state.isAdding = false;
        state.error = action.error.message || 'Failed to add to wishlist';
        toast.error('Failed to add to wishlist');
      });

    // Remove from wishlist
    builder
      .addCase(removeFromWishlist.pending, (state) => {
        state.isRemoving = true;
        state.error = null;
      })
      .addCase(removeFromWishlist.fulfilled, (state, action) => {
        const productId = action.payload;

        state.items = state.items.filter(item => item.productId !== productId);
        state.itemIds.delete(productId);
        state.total = state.items.length;

        // Update localStorage
        localStorage.setItem('wishlist', JSON.stringify(state.items));

        toast.success('Removed from wishlist');
        state.isRemoving = false;
      })
      .addCase(removeFromWishlist.rejected, (state, action) => {
        state.isRemoving = false;
        state.error = action.error.message || 'Failed to remove from wishlist';
        toast.error('Failed to remove from wishlist');
      });

    // Clear wishlist
    builder
      .addCase(clearWishlist.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(clearWishlist.fulfilled, (state) => {
        state.items = [];
        state.itemIds = new Set();
        state.total = 0;
        state.isLoading = false;

        // Clear localStorage
        localStorage.removeItem('wishlist');

        toast.success('Wishlist cleared');
      })
      .addCase(clearWishlist.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to clear wishlist';
        toast.error('Failed to clear wishlist');
      });

    // Move to cart
    builder
      .addCase(moveToCart.pending, (state) => {
        state.isRemoving = true;
        state.error = null;
      })
      .addCase(moveToCart.fulfilled, (state) => {
        toast.success('Moved to cart');
        state.isRemoving = false;
      })
      .addCase(moveToCart.rejected, (state, action) => {
        state.isRemoving = false;
        state.error = action.error.message || 'Failed to move to cart';
        toast.error('Failed to move to cart');
      });

    // Check wishlist item
    builder
      .addCase(checkWishlistItem.fulfilled, (state, action) => {
        const { productId, isInWishlist } = action.payload;

        if (isInWishlist && !state.itemIds.has(productId)) {
          // Item is in wishlist on server but not locally - need to sync
          // This typically happens after login
        } else if (!isInWishlist && state.itemIds.has(productId)) {
          // Item is not in wishlist on server but is locally - remove locally
          state.items = state.items.filter(item => item.productId !== productId);
          state.itemIds.delete(productId);
          state.total = state.items.length;
        }
      });
  },
});

// Actions
export const { clearError, syncWishlistFromStorage } = wishlistSlice.actions;

// Selectors
export const selectWishlistItems = (state: { wishlist: WishlistState }) => state.wishlist.items;

export const selectWishlistTotal = (state: { wishlist: WishlistState }) => state.wishlist.total;

export const selectIsInWishlist = (productId: string) => (state: { wishlist: WishlistState }) =>
  state.wishlist.itemIds.has(productId);

export const selectWishlistLoading = (state: { wishlist: WishlistState }) => ({
  isLoading: state.wishlist.isLoading,
  isAdding: state.wishlist.isAdding,
  isRemoving: state.wishlist.isRemoving,
});

export const selectWishlistError = (state: { wishlist: WishlistState }) => state.wishlist.error;

// Helper function to toggle wishlist item
export const toggleWishlistItem = (productId: string) => (dispatch: any, getState: any) => {
  const state = getState();
  const isInWishlist = selectIsInWishlist(productId)(state);

  if (isInWishlist) {
    return dispatch(removeFromWishlist(productId));
  } else {
    return dispatch(addToWishlist(productId));
  }
};

// Export reducer
export default wishlistSlice.reducer;