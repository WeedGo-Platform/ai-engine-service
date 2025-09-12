/**
 * Store Context Provider
 * Manages store selection and context for multi-tenant inventory management
 * Follows SOLID principles and clean architecture patterns
 */

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from './AuthContext';

// =====================================================
// Type Definitions
// =====================================================

interface StoreAddress {
  street: string;
  city: string;
  province: string;
  postal_code: string;
  country: string;
}

interface Store {
  id: string;
  tenant_id: string;
  store_code: string;
  name: string;
  address: StoreAddress;
  phone?: string;
  email?: string;
  timezone: string;
  license_number?: string;
  license_expiry?: string;
  tax_rate?: number;
  delivery_radius_km?: number;
  delivery_enabled: boolean;
  pickup_enabled: boolean;
  kiosk_enabled: boolean;
  pos_enabled: boolean;
  ecommerce_enabled: boolean;
  status: 'active' | 'inactive' | 'suspended';
  created_at: string;
  updated_at: string;
}

interface StoreInventoryStats {
  total_skus: number;
  total_quantity: number;
  low_stock_items: number;
  out_of_stock_items: number;
  total_value: number;
}

interface StoreContextValue {
  // Current store state
  currentStore: Store | null;
  stores: Store[];
  isLoading: boolean;
  error: Error | null;
  
  // Store operations
  selectStore: (storeId: string) => Promise<void>;
  clearStore: () => void;
  refreshStores: () => Promise<void>;
  
  // Store inventory stats
  inventoryStats: StoreInventoryStats | null;
  loadInventoryStats: (storeId: string) => Promise<void>;
  
  // Utility functions
  getStoreById: (storeId: string) => Store | undefined;
  isStoreActive: (storeId: string) => boolean;
  hasStoreAccess: (storeId: string) => boolean;
}

interface StoreProviderProps {
  children: ReactNode;
  defaultStoreId?: string;
  persistSelection?: boolean;
}

// =====================================================
// Constants
// =====================================================

const STORE_CONTEXT_KEY = 'weedgo_active_store';
const STORE_CACHE_KEY = 'weedgo_stores_cache';
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
const API_BASE_URL = 'http://localhost:5024';

// =====================================================
// Context Creation
// =====================================================

const StoreContext = createContext<StoreContextValue | undefined>(undefined);

// =====================================================
// Custom Hook for Store Context
// =====================================================

export const useStoreContext = (): StoreContextValue => {
  const context = useContext(StoreContext);
  if (!context) {
    throw new Error('useStoreContext must be used within a StoreProvider');
  }
  return context;
};

// =====================================================
// API Service Functions
// =====================================================

const storeService = {
  /**
   * Fetch all accessible stores for the current user
   */
  fetchStores: async (): Promise<Store[]> => {
    const response = await fetch(`${API_BASE_URL}/api/stores/tenant/active`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        // Add auth headers if needed
      },
    });
    
    if (!response.ok) {
      // Fallback to fetch all stores if tenant endpoint doesn't exist
      const fallbackResponse = await fetch(`${API_BASE_URL}/api/stores`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!fallbackResponse.ok) {
        throw new Error('Failed to fetch stores');
      }
      
      return fallbackResponse.json();
    }
    
    return response.json();
  },
  
  /**
   * Set active store for the session
   */
  setActiveStore: async (storeId: string): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/api/stores/${storeId}/select`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Store-ID': storeId,
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to set active store');
    }
  },
  
  /**
   * Fetch inventory statistics for a store
   */
  fetchInventoryStats: async (storeId: string): Promise<StoreInventoryStats> => {
    const response = await fetch(`${API_BASE_URL}/api/stores/${storeId}/inventory/stats`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-Store-ID': storeId,
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch inventory statistics');
    }
    
    return response.json();
  },
};

// =====================================================
// Local Storage Utilities
// =====================================================

const storageUtils = {
  /**
   * Get stored store ID from localStorage
   */
  getStoredStoreId: (): string | null => {
    try {
      return localStorage.getItem(STORE_CONTEXT_KEY);
    } catch (error) {
      console.error('Failed to read from localStorage:', error);
      return null;
    }
  },
  
  /**
   * Save store ID to localStorage
   */
  saveStoreId: (storeId: string): void => {
    try {
      localStorage.setItem(STORE_CONTEXT_KEY, storeId);
    } catch (error) {
      console.error('Failed to save to localStorage:', error);
    }
  },
  
  /**
   * Clear stored store ID
   */
  clearStoreId: (): void => {
    try {
      localStorage.removeItem(STORE_CONTEXT_KEY);
    } catch (error) {
      console.error('Failed to clear localStorage:', error);
    }
  },
  
  /**
   * Get cached stores from localStorage
   */
  getCachedStores: (): { stores: Store[]; timestamp: number } | null => {
    try {
      const cached = localStorage.getItem(STORE_CACHE_KEY);
      return cached ? JSON.parse(cached) : null;
    } catch (error) {
      console.error('Failed to read cache:', error);
      return null;
    }
  },
  
  /**
   * Cache stores in localStorage
   */
  cacheStores: (stores: Store[]): void => {
    try {
      localStorage.setItem(
        STORE_CACHE_KEY,
        JSON.stringify({ stores, timestamp: Date.now() })
      );
    } catch (error) {
      console.error('Failed to cache stores:', error);
    }
  },
};

// =====================================================
// Store Provider Component
// =====================================================

export const StoreProvider: React.FC<StoreProviderProps> = ({
  children,
  defaultStoreId,
  persistSelection = true,
}) => {
  const queryClient = useQueryClient();
  const { user, isSuperAdmin, isAuthenticated } = useAuth();
  const [currentStore, setCurrentStore] = useState<Store | null>(null);
  const [inventoryStats, setInventoryStats] = useState<StoreInventoryStats | null>(null);
  const [filteredStores, setFilteredStores] = useState<Store[]>([]);
  
  // Fetch stores query
  const {
    data: allStores = [],
    isLoading,
    error,
    refetch: refreshStores,
  } = useQuery<Store[], Error>({
    queryKey: ['stores', user?.user_id],
    queryFn: storeService.fetchStores,
    enabled: isAuthenticated,
    staleTime: CACHE_DURATION,
    cacheTime: CACHE_DURATION * 2,
    onSuccess: (data) => {
      // Filter stores based on user permissions
      let accessibleStores = data;
      
      if (!isSuperAdmin()) {
        // Filter stores based on user's store permissions
        const userStoreIds = user?.stores?.map(s => s.id) || [];
        accessibleStores = data.filter(store => 
          userStoreIds.includes(store.id)
        );
      }
      
      setFilteredStores(accessibleStores);
      
      // Cache stores for offline access
      storageUtils.cacheStores(accessibleStores);
      
      // Auto-select store if needed
      if (!currentStore && accessibleStores.length > 0) {
        const storedId = persistSelection ? storageUtils.getStoredStoreId() : null;
        const storeToSelect = 
          (storedId && accessibleStores.find(s => s.id === storedId)) ||
          (defaultStoreId && accessibleStores.find(s => s.id === defaultStoreId)) ||
          accessibleStores.find(s => s.status === 'active');
        
        if (storeToSelect) {
          selectStore(storeToSelect.id);
        }
      }
    },
    onError: () => {
      // Try to use cached data on error
      const cached = storageUtils.getCachedStores();
      if (cached && Date.now() - cached.timestamp < CACHE_DURATION * 2) {
        queryClient.setQueryData(['stores'], cached.stores);
      }
    },
  });
  
  // Select store mutation
  const selectStoreMutation = useMutation({
    mutationFn: storeService.setActiveStore,
    onSuccess: (_, storeId) => {
      const store = stores.find(s => s.id === storeId);
      if (store) {
        setCurrentStore(store);
        if (persistSelection) {
          storageUtils.saveStoreId(storeId);
        }
        // Set store ID in request headers for subsequent API calls
        window.localStorage.setItem('X-Store-ID', storeId);
      }
    },
  });
  
  // Load inventory stats mutation
  const loadInventoryStatsMutation = useMutation({
    mutationFn: storeService.fetchInventoryStats,
    onSuccess: (data) => {
      setInventoryStats(data);
    },
  });
  
  // =====================================================
  // Context Methods
  // =====================================================
  
  const selectStore = useCallback(async (storeId: string) => {
    const store = filteredStores.find(s => s.id === storeId);
    if (!store) {
      throw new Error(`Store with ID ${storeId} not found or not accessible`);
    }
    
    if (store.status !== 'active') {
      throw new Error(`Store ${store.name} is not active`);
    }
    
    // Check user has permission to access this store
    if (!isSuperAdmin() && user?.stores && !user.stores.find(s => s.id === storeId)) {
      throw new Error(`You don't have permission to access store ${store.name}`);
    }
    
    await selectStoreMutation.mutateAsync(storeId);
    // Load inventory stats for the selected store
    await loadInventoryStatsMutation.mutateAsync(storeId);
  }, [filteredStores, selectStoreMutation, loadInventoryStatsMutation, isSuperAdmin, user]);
  
  const clearStore = useCallback(() => {
    setCurrentStore(null);
    setInventoryStats(null);
    if (persistSelection) {
      storageUtils.clearStoreId();
    }
    window.localStorage.removeItem('X-Store-ID');
  }, [persistSelection]);
  
  const loadInventoryStats = useCallback(async (storeId: string) => {
    await loadInventoryStatsMutation.mutateAsync(storeId);
  }, [loadInventoryStatsMutation]);
  
  const getStoreById = useCallback((storeId: string) => {
    return filteredStores.find(s => s.id === storeId);
  }, [filteredStores]);
  
  const isStoreActive = useCallback((storeId: string) => {
    const store = getStoreById(storeId);
    return store?.status === 'active';
  }, [getStoreById]);
  
  const hasStoreAccess = useCallback((storeId: string) => {
    if (isSuperAdmin()) return true;
    
    const store = getStoreById(storeId);
    if (!store) return false;
    
    // Check if user has permission for this store
    return user?.stores?.some(s => s.id === storeId) || false;
  }, [getStoreById, isSuperAdmin, user]);
  
  // =====================================================
  // Effects
  // =====================================================
  
  // Initialize store selection on mount
  useEffect(() => {
    if (!isLoading && filteredStores.length > 0 && !currentStore) {
      const storedId = persistSelection ? storageUtils.getStoredStoreId() : null;
      if (storedId && filteredStores.find(s => s.id === storedId)) {
        selectStore(storedId).catch(console.error);
      } else if (defaultStoreId && filteredStores.find(s => s.id === defaultStoreId)) {
        selectStore(defaultStoreId).catch(console.error);
      }
    }
  }, [isLoading, filteredStores, currentStore, persistSelection, defaultStoreId, selectStore]);
  
  // Set global store header for API requests
  useEffect(() => {
    if (currentStore) {
      // Set default header for all fetch requests
      const originalFetch = window.fetch;
      window.fetch = function(...args) {
        const [url, config = {}] = args;
        
        // Add store header if it's an API call
        if (typeof url === 'string' && url.includes('/api/')) {
          config.headers = {
            ...config.headers,
            'X-Store-ID': currentStore.id,
          };
        }
        
        return originalFetch.call(this, url, config);
      };
      
      return () => {
        window.fetch = originalFetch;
      };
    }
  }, [currentStore]);
  
  // =====================================================
  // Context Value
  // =====================================================
  
  const contextValue: StoreContextValue = {
    currentStore,
    stores: filteredStores,
    isLoading,
    error,
    selectStore,
    clearStore,
    refreshStores,
    inventoryStats,
    loadInventoryStats,
    getStoreById,
    isStoreActive,
    hasStoreAccess,
  };
  
  return (
    <StoreContext.Provider value={contextValue}>
      {children}
    </StoreContext.Provider>
  );
};

// =====================================================
// Export Additional Utilities
// =====================================================

export const withStoreContext = <P extends object>(
  Component: React.ComponentType<P>
): React.FC<P> => {
  return (props: P) => (
    <StoreProvider>
      <Component {...props} />
    </StoreProvider>
  );
};

export default StoreContext;