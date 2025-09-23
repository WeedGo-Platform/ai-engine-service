import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Location from 'expo-location';
import { Store, DayHours } from '@/types/api.types';
import { storeService } from '@/services/api/stores';

interface StoreState {
  // State
  currentStore: Store | null;
  stores: Store[];
  loading: boolean;
  error: string | null;
  isStoreOpen: boolean;
  nextOpenTime: string | null;

  // Actions
  loadStores: () => Promise<void>;
  setCurrentStore: (store: Store) => void;
  selectStoreById: (storeId: string) => Promise<void>;
  getNearestStore: (lat: number, lng: number) => Promise<void>;
  checkStoreAvailability: () => Promise<void>;
  isCurrentlyOpen: () => boolean;
  getStoreHours: () => string;
  getDeliveryInfo: (postalCode: string) => Promise<any>;
  findNearestStore: (stores: Store[], lat: number, lng: number) => Store;
  calculateDistance: (lat1: number, lon1: number, lat2: number, lon2: number) => number;
}

const useStoreStore = create<StoreState>()(
  persist(
    (set, get) => ({
      // Initial state
      currentStore: null,
      stores: [],
      loading: false,
      error: null,
      isStoreOpen: true,
      nextOpenTime: null,

      // Load all available stores
      loadStores: async () => {
        set({ loading: true, error: null });

        try {
          const stores = await storeService.getStores();
          set({ stores, loading: false });

          // If no current store selected, try to select based on location
          if (!get().currentStore && stores.length > 0) {
            // Try to get user location and select nearest store
            try {
              // Request location permission
              const { status } = await Location.requestForegroundPermissionsAsync();
              if (status === 'granted') {
                const location = await Location.getCurrentPositionAsync({});
                const nearestStore = get().findNearestStore(stores, location.coords.latitude, location.coords.longitude);
                set({ currentStore: nearestStore });
              } else {
                // If location not available, select the first store
                set({ currentStore: stores[0] });
              }
            } catch (locationError) {
              // Fallback to first store if location fails
              console.log('Location not available, using first store');
              set({ currentStore: stores[0] });
            }
            await get().checkStoreAvailability();
          }
        } catch (error: any) {
          set({
            error: error.message || 'Failed to load stores',
            loading: false,
          });
        }
      },

      // Set current store
      setCurrentStore: (store: Store) => {
        set({ currentStore: store });
        get().checkStoreAvailability();
      },

      // Select store by ID
      selectStoreById: async (storeId: string) => {
        set({ loading: true, error: null });

        try {
          const store = await storeService.getStoreDetails(storeId);
          set({ currentStore: store, loading: false });
          await get().checkStoreAvailability();
        } catch (error: any) {
          set({
            error: error.message || 'Failed to load store details',
            loading: false,
          });
        }
      },

      // Get nearest store based on location
      getNearestStore: async (lat: number, lng: number) => {
        set({ loading: true, error: null });

        try {
          const store = await storeService.getNearestStore(lat, lng);
          set({ currentStore: store, loading: false });
          await get().checkStoreAvailability();
        } catch (error: any) {
          set({
            error: error.message || 'Failed to find nearest store',
            loading: false,
          });
        }
      },

      // Check if store is currently available
      checkStoreAvailability: async () => {
        const { currentStore } = get();
        if (!currentStore) return;

        try {
          const availability = await storeService.checkAvailability(currentStore.id);
          set({
            isStoreOpen: availability.is_open,
            nextOpenTime: availability.next_open_time,
          });
        } catch (error) {
          // If the availability endpoint doesn't exist, fall back to checking hours
          console.warn('Store availability endpoint not found, checking hours locally');
          const isOpen = get().isCurrentlyOpen();
          set({ isStoreOpen: isOpen });
        }
      },

      // Check if store is currently open based on hours
      isCurrentlyOpen: () => {
        const { currentStore } = get();
        if (!currentStore || !currentStore.hours) return false;

        const now = new Date();
        const dayOfWeek = now.toLocaleDateString('en-US', { weekday: 'long' }).toLowerCase() as keyof typeof currentStore.hours;
        const currentTime = now.toTimeString().slice(0, 5); // HH:MM format

        const todayHours = currentStore.hours[dayOfWeek] as DayHours | undefined;

        if (!todayHours || todayHours.is_closed) {
          return false;
        }

        return currentTime >= todayHours.open && currentTime <= todayHours.close;
      },

      // Get formatted store hours string
      getStoreHours: () => {
        const { currentStore, isStoreOpen } = get();
        if (!currentStore) return 'Store hours unavailable';

        if (!isStoreOpen) {
          const { nextOpenTime } = get();
          return nextOpenTime ? `Opens at ${nextOpenTime}` : 'Closed';
        }

        const now = new Date();
        const dayOfWeek = now.toLocaleDateString('en-US', { weekday: 'long' }).toLowerCase() as keyof typeof currentStore.hours;
        const todayHours = currentStore.hours[dayOfWeek] as DayHours | undefined;

        if (!todayHours || todayHours.is_closed) {
          return 'Closed today';
        }

        return `Open until ${todayHours.close}`;
      },

      // Get delivery info for postal code
      getDeliveryInfo: async (postalCode: string) => {
        const { currentStore } = get();
        if (!currentStore) {
          throw new Error('No store selected');
        }

        try {
          return await storeService.checkDeliveryAvailability(
            currentStore.id,
            postalCode
          );
        } catch (error: any) {
          throw new Error(error.message || 'Failed to check delivery availability');
        }
      },

      // Calculate distance between two coordinates (Haversine formula)
      calculateDistance: (lat1: number, lon1: number, lat2: number, lon2: number) => {
        const R = 6371; // Radius of the earth in km
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a =
          Math.sin(dLat/2) * Math.sin(dLat/2) +
          Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
          Math.sin(dLon/2) * Math.sin(dLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        const d = R * c; // Distance in km
        return d;
      },

      // Find nearest store to given coordinates
      findNearestStore: (stores: Store[], lat: number, lng: number) => {
        if (stores.length === 0) return stores[0];

        let nearestStore = stores[0];
        let minDistance = Infinity;

        stores.forEach(store => {
          if (store.latitude && store.longitude) {
            const distance = get().calculateDistance(lat, lng, store.latitude, store.longitude);
            if (distance < minDistance) {
              minDistance = distance;
              nearestStore = store;
            }
          }
        });

        return nearestStore;
      },
    }),
    {
      name: 'weedgo-store-storage',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        currentStore: state.currentStore,
      }),
    }
  )
);

export default useStoreStore;
export { useStoreStore };