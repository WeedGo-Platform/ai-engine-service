import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { tenantService, TenantSettings } from '@/services/api/tenant';

interface TenantState {
  // State
  tenant: TenantSettings | null;
  loading: boolean;
  error: string | null;

  // Actions
  loadTenant: () => Promise<void>;
  refreshTenant: () => Promise<void>;
  clearError: () => void;
}

export const useTenantStore = create<TenantState>()(
  persist(
    (set, get) => ({
      // Initial state
      tenant: null,
      loading: false,
      error: null,

      // Load tenant settings
      loadTenant: async () => {
        const { tenant } = get();
        // If already loaded, skip
        if (tenant) return;

        set({ loading: true, error: null });
        try {
          const tenantSettings = await tenantService.getTenantSettings();
          if (tenantSettings) {
            console.log('Tenant settings loaded:', tenantSettings);
            console.log('Tenant logo URL:', tenantSettings.logo_url);
            set({ tenant: tenantSettings, loading: false });
          } else {
            set({
              error: 'Failed to load tenant settings',
              loading: false
            });
          }
        } catch (error: any) {
          set({
            error: error.message || 'Failed to load tenant',
            loading: false,
          });
        }
      },

      // Force refresh tenant settings
      refreshTenant: async () => {
        set({ loading: true, error: null });
        try {
          const tenantSettings = await tenantService.getTenantSettings();
          if (tenantSettings) {
            console.log('Tenant settings refreshed:', tenantSettings);
            console.log('Tenant logo URL:', tenantSettings.logo_url);
            set({ tenant: tenantSettings, loading: false });
          } else {
            set({
              error: 'Failed to load tenant settings',
              loading: false
            });
          }
        } catch (error: any) {
          set({
            error: error.message || 'Failed to load tenant',
            loading: false,
          });
        }
      },

      // Clear error
      clearError: () => set({ error: null }),
    }),
    {
      name: 'tenant-storage',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        tenant: state.tenant,
      }),
    }
  )
);

export default useTenantStore;