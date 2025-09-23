import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Store, storesApi } from '@api/stores';

interface StoreContextType {
  stores: Store[];
  selectedStore: Store | null;
  isLoadingStores: boolean;
  selectStore: (storeId: string) => Promise<void>;
  refreshStores: () => Promise<void>;
}

const StoreContext = createContext<StoreContextType | undefined>(undefined);

export const useStore = () => {
  const context = useContext(StoreContext);
  if (!context) {
    throw new Error('useStore must be used within a StoreProvider');
  }
  return context;
};

interface StoreProviderProps {
  children: ReactNode;
}

export const StoreProvider: React.FC<StoreProviderProps> = ({ children }) => {
  const [stores, setStores] = useState<Store[]>([]);
  const [selectedStore, setSelectedStore] = useState<Store | null>(null);
  const [isLoadingStores, setIsLoadingStores] = useState(true);

  const tenantId = import.meta.env.VITE_TENANT_ID;

  const refreshStores = async () => {
    if (!tenantId) {
      console.error('No tenant ID configured');
      setIsLoadingStores(false);
      return;
    }

    setIsLoadingStores(true);
    try {
      const fetchedStores = await storesApi.getTenantStores(tenantId);
      setStores(fetchedStores);

      // If we have stores, select one
      if (fetchedStores.length > 0) {
        // Check for previously selected store
        const savedStoreId = localStorage.getItem('selected_store_id');
        const savedStore = fetchedStores.find(s => s.id === savedStoreId);

        if (savedStore) {
          setSelectedStore(savedStore);
        } else {
          // Select first store by default
          setSelectedStore(fetchedStores[0]);
          localStorage.setItem('selected_store_id', fetchedStores[0].id);
        }
      }
    } catch (error) {
      console.error('Failed to fetch stores:', error);
    } finally {
      setIsLoadingStores(false);
    }
  };

  const selectStore = async (storeId: string) => {
    const store = stores.find(s => s.id === storeId);
    if (store) {
      setSelectedStore(store);
      localStorage.setItem('selected_store_id', storeId);
      // Notify backend of store selection
      await storesApi.selectStore(storeId);
      // Reload the page to refresh all data with new store
      window.location.reload();
    }
  };

  useEffect(() => {
    refreshStores();
  }, [tenantId]);

  return (
    <StoreContext.Provider
      value={{
        stores,
        selectedStore,
        isLoadingStores,
        selectStore,
        refreshStores
      }}
    >
      {children}
    </StoreContext.Provider>
  );
};