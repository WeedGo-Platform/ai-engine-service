import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface DeliveryLocation {
  lat: number;
  lng: number;
}

interface DeliveryDriver {
  id: string;
  name: string;
  phone: string;
  vehicle: string;
  photo?: string;
}

interface DeliveryTracking {
  orderId: string;
  status: 'pending' | 'confirmed' | 'preparing' | 'picked_up' | 'en_route' | 'delivered';
  driver?: DeliveryDriver;
  estimatedTime?: number; // in minutes
  currentLocation?: DeliveryLocation;
  route?: DeliveryLocation[];
  updatedAt: string;
}

interface DeliveryState {
  currentTracking: DeliveryTracking | null;
  isTracking: boolean;
  deliveryAddress: string | null;
  deliveryInstructions: string | null;
  deliveryTime: string | null; // ISO string
  deliveryFee: number;
}

const initialState: DeliveryState = {
  currentTracking: null,
  isTracking: false,
  deliveryAddress: null,
  deliveryInstructions: null,
  deliveryTime: null,
  deliveryFee: 0,
};

const deliverySlice = createSlice({
  name: 'delivery',
  initialState,
  reducers: {
    setTracking: (state, action: PayloadAction<DeliveryTracking>) => {
      state.currentTracking = action.payload;
      state.isTracking = true;
    },
    updateTrackingStatus: (
      state,
      action: PayloadAction<DeliveryTracking['status']>
    ) => {
      if (state.currentTracking) {
        state.currentTracking.status = action.payload;
        state.currentTracking.updatedAt = new Date().toISOString();
      }
    },
    updateDriverLocation: (state, action: PayloadAction<DeliveryLocation>) => {
      if (state.currentTracking) {
        state.currentTracking.currentLocation = action.payload;
        state.currentTracking.updatedAt = new Date().toISOString();
      }
    },
    setDeliveryDetails: (
      state,
      action: PayloadAction<{
        address: string;
        instructions?: string;
        time?: string;
        fee?: number;
      }>
    ) => {
      state.deliveryAddress = action.payload.address;
      state.deliveryInstructions = action.payload.instructions || null;
      state.deliveryTime = action.payload.time || null;
      state.deliveryFee = action.payload.fee || 0;
    },
    clearTracking: (state) => {
      state.currentTracking = null;
      state.isTracking = false;
    },
    clearDeliveryDetails: (state) => {
      state.deliveryAddress = null;
      state.deliveryInstructions = null;
      state.deliveryTime = null;
      state.deliveryFee = 0;
    },
  },
});

export const {
  setTracking,
  updateTrackingStatus,
  updateDriverLocation,
  setDeliveryDetails,
  clearTracking,
  clearDeliveryDetails,
} = deliverySlice.actions;

export default deliverySlice.reducer;