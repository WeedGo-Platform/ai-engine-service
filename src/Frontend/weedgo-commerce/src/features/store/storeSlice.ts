import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface Store {
  id: string;
  name: string;
  address: string;
  city: string;
  province: string;
  postal_code: string;
  phone: string;
  hours?: {
    [key: string]: { open: string; close: string };
  };
}

interface StoreState {
  selectedStore: Store | null;
  stores: Store[];
  loading: boolean;
  error: string | null;
}

const initialState: StoreState = {
  selectedStore: null,
  stores: [],
  loading: false,
  error: null,
};

const storeSlice = createSlice({
  name: 'store',
  initialState,
  reducers: {
    setSelectedStore: (state, action: PayloadAction<Store>) => {
      state.selectedStore = action.payload;
      // Save to localStorage for persistence
      localStorage.setItem('selectedStore', JSON.stringify(action.payload));
    },
    clearSelectedStore: (state) => {
      state.selectedStore = null;
      localStorage.removeItem('selectedStore');
    },
    setStores: (state, action: PayloadAction<Store[]>) => {
      state.stores = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    // Initialize from localStorage
    initializeStore: (state) => {
      const saved = localStorage.getItem('selectedStore');
      if (saved) {
        try {
          state.selectedStore = JSON.parse(saved);
        } catch (error) {
          console.error('Failed to parse saved store:', error);
        }
      }
    },
  },
});

export const {
  setSelectedStore,
  clearSelectedStore,
  setStores,
  setLoading,
  setError,
  initializeStore,
} = storeSlice.actions;

export default storeSlice.reducer;