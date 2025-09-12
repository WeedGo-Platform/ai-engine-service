/**
 * Tenant Context Provider
 * Manages tenant and store resolution for multi-tenant architecture
 * Follows Context API pattern with comprehensive state management
 */

import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import axios, { AxiosInstance } from 'axios';

/**
 * Interfaces for type safety
 */
interface TenantInfo {
  tenantId: string;
  tenantCode: string;
  tenantName: string;
  templateId: string;
  subdomain?: string;
  settings?: Record<string, any>;
}

interface StoreLocation {
  storeId: string;
  storeName: string;
  address: string;
  city: string;
  state: string;
  zipCode: string;
  latitude: number;
  longitude: number;
  distance?: number;
  distanceUnit?: 'km' | 'miles';
}

interface StoreHours {
  dayOfWeek: string;
  openTime: string;
  closeTime: string;
  isClosed: boolean;
}

interface Store {
  id: string;
  name: string;
  code: string;
  location: StoreLocation;
  hours: StoreHours[];
  phoneNumber?: string;
  email?: string;
  isActive: boolean;
  deliveryAvailable: boolean;
  pickupAvailable: boolean;
  deliveryRadius?: number;
  minimumOrderAmount?: number;
}

interface UserLocation {
  latitude: number;
  longitude: number;
  accuracy?: number;
  timestamp?: number;
  address?: string;
}

interface TenantContextState {
  // Tenant information
  tenant: TenantInfo | null;
  isTenantLoading: boolean;
  tenantError: string | null;
  
  // Store information
  selectedStore: Store | null;
  nearbyStores: Store[];
  isStoresLoading: boolean;
  storesError: string | null;
  
  // User location
  userLocation: UserLocation | null;
  isLocationLoading: boolean;
  locationError: string | null;
  locationPermission: 'granted' | 'denied' | 'prompt' | null;
  
  // Actions
  selectStore: (storeId: string) => Promise<void>;
  findNearestStores: (location?: UserLocation) => Promise<Store[]>;
  requestUserLocation: () => Promise<UserLocation | null>;
  setUserAddress: (address: string) => Promise<UserLocation | null>;
  refreshTenant: () => Promise<void>;
  clearStoreSelection: () => void;
}

/**
 * Default context value
 */
const defaultContextValue: TenantContextState = {
  tenant: null,
  isTenantLoading: true,
  tenantError: null,
  selectedStore: null,
  nearbyStores: [],
  isStoresLoading: false,
  storesError: null,
  userLocation: null,
  isLocationLoading: false,
  locationError: null,
  locationPermission: null,
  selectStore: async () => {},
  findNearestStores: async () => [],
  requestUserLocation: async () => null,
  setUserAddress: async () => null,
  refreshTenant: async () => {},
  clearStoreSelection: () => {}
};

/**
 * Create context
 */
const TenantContext = createContext<TenantContextState>(defaultContextValue);

/**
 * Custom hook to use tenant context
 */
export const useTenant = () => {
  const context = useContext(TenantContext);
  if (!context) {
    throw new Error('useTenant must be used within TenantProvider');
  }
  return context;
};

/**
 * Tenant Provider Props
 */
interface TenantProviderProps {
  children: React.ReactNode;
  apiClient?: AxiosInstance;
  autoDetectLocation?: boolean;
  persistStoreSelection?: boolean;
}

/**
 * Tenant Provider Component
 */
export const TenantProvider: React.FC<TenantProviderProps> = ({
  children,
  apiClient,
  autoDetectLocation = true,
  persistStoreSelection = true
}) => {
  // State management
  const [tenant, setTenant] = useState<TenantInfo | null>(null);
  const [isTenantLoading, setIsTenantLoading] = useState(true);
  const [tenantError, setTenantError] = useState<string | null>(null);
  
  const [selectedStore, setSelectedStore] = useState<Store | null>(null);
  const [nearbyStores, setNearbyStores] = useState<Store[]>([]);
  const [isStoresLoading, setIsStoresLoading] = useState(false);
  const [storesError, setStoresError] = useState<string | null>(null);
  
  const [userLocation, setUserLocation] = useState<UserLocation | null>(null);
  const [isLocationLoading, setIsLocationLoading] = useState(false);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [locationPermission, setLocationPermission] = useState<'granted' | 'denied' | 'prompt' | null>(null);
  
  // API client setup
  const api = useMemo(() => {
    if (apiClient) return apiClient;
    
    const instance = axios.create({
      baseURL: '/api',
      timeout: 10000
    });
    
    // Add tenant headers interceptor
    instance.interceptors.request.use((config) => {
      if (tenant) {
        config.headers['X-Tenant-Id'] = tenant.tenantId;
        config.headers['X-Tenant-Code'] = tenant.tenantCode;
        config.headers['X-Template-Id'] = tenant.templateId;
      }
      
      // Add store header if selected
      if (selectedStore) {
        config.headers['X-Store-Id'] = selectedStore.id;
      }
      
      return config;
    });
    
    return instance;
  }, [apiClient, tenant, selectedStore]);
  
  /**
   * Resolve tenant from environment or port
   */
  const resolveTenant = useCallback(async () => {
    try {
      setIsTenantLoading(true);
      setTenantError(null);
      
      // Check if tenant config is embedded in build
      if (typeof __TENANT_CONFIG__ !== 'undefined') {
        const config = __TENANT_CONFIG__ as any;
        setTenant({
          tenantId: config.tenantId,
          tenantCode: config.tenantCode,
          tenantName: config.tenantCode.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
          templateId: config.templateId,
          subdomain: config.subdomain
        });
        setIsTenantLoading(false);
        return;
      }
      
      // Fallback: resolve from API endpoint
      const response = await api.get('/tenants/resolve');
      if (response.data) {
        setTenant(response.data);
      } else {
        // Use default tenant for development
        const port = window.location.port || '5173';
        const defaultTenant = getDefaultTenantByPort(parseInt(port));
        setTenant(defaultTenant);
      }
    } catch (error) {
      console.error('Failed to resolve tenant:', error);
      setTenantError('Failed to determine tenant context');
      
      // Fallback to default tenant
      const port = window.location.port || '5173';
      const defaultTenant = getDefaultTenantByPort(parseInt(port));
      setTenant(defaultTenant);
    } finally {
      setIsTenantLoading(false);
    }
  }, [api]);
  
  /**
   * Get default tenant configuration by port
   */
  const getDefaultTenantByPort = (port: number): TenantInfo => {
    const portMappings: Record<number, TenantInfo> = {
      5173: {
        tenantId: '00000000-0000-0000-0000-000000000001',
        tenantCode: 'default',
        tenantName: 'Default Store',
        templateId: 'modern-minimal'
      },
      5174: {
        tenantId: '00000000-0000-0000-0000-000000000002',
        tenantCode: 'pot-palace',
        tenantName: 'Pot Palace',
        templateId: 'pot-palace'
      },
      5175: {
        tenantId: '00000000-0000-0000-0000-000000000003',
        tenantCode: 'dark-tech',
        tenantName: 'Dark Tech',
        templateId: 'dark-tech'
      },
      5176: {
        tenantId: '00000000-0000-0000-0000-000000000004',
        tenantCode: 'rasta-vibes',
        tenantName: 'Rasta Vibes',
        templateId: 'rasta-vibes'
      }
    };
    
    return portMappings[port] || portMappings[5173];
  };
  
  /**
   * Request user location using browser API
   */
  const requestUserLocation = useCallback(async (): Promise<UserLocation | null> => {
    if (!navigator.geolocation) {
      setLocationError('Geolocation is not supported by your browser');
      return null;
    }
    
    setIsLocationLoading(true);
    setLocationError(null);
    
    return new Promise((resolve) => {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const location: UserLocation = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            timestamp: position.timestamp
          };
          
          // Try to get address via reverse geocoding
          try {
            const response = await api.post('/stores/reverse-geocode', {
              latitude: location.latitude,
              longitude: location.longitude
            });
            location.address = response.data.address;
          } catch (error) {
            console.warn('Reverse geocoding failed:', error);
          }
          
          setUserLocation(location);
          setLocationPermission('granted');
          setIsLocationLoading(false);
          
          // Store in session storage
          sessionStorage.setItem('userLocation', JSON.stringify(location));
          
          resolve(location);
        },
        (error) => {
          console.error('Location error:', error);
          setLocationError(error.message);
          setLocationPermission(error.code === 1 ? 'denied' : 'prompt');
          setIsLocationLoading(false);
          resolve(null);
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 300000 // 5 minutes
        }
      );
    });
  }, [api]);
  
  /**
   * Set user address and geocode it
   */
  const setUserAddress = useCallback(async (address: string): Promise<UserLocation | null> => {
    try {
      setIsLocationLoading(true);
      setLocationError(null);
      
      const response = await api.post('/stores/geocode', { address });
      const location: UserLocation = {
        latitude: response.data.latitude,
        longitude: response.data.longitude,
        address: address
      };
      
      setUserLocation(location);
      sessionStorage.setItem('userLocation', JSON.stringify(location));
      
      return location;
    } catch (error) {
      console.error('Geocoding failed:', error);
      setLocationError('Failed to geocode address');
      return null;
    } finally {
      setIsLocationLoading(false);
    }
  }, [api]);
  
  /**
   * Find nearest stores
   */
  const findNearestStores = useCallback(async (location?: UserLocation): Promise<Store[]> => {
    try {
      setIsStoresLoading(true);
      setStoresError(null);
      
      const targetLocation = location || userLocation;
      if (!targetLocation) {
        throw new Error('No location available');
      }
      
      const response = await api.post('/stores/nearest', {
        latitude: targetLocation.latitude,
        longitude: targetLocation.longitude,
        limit: 10,
        maxDistance: 50
      });
      
      const stores = response.data.map((store: any) => ({
        id: store.store_id,
        name: store.name,
        code: store.code,
        location: {
          storeId: store.store_id,
          storeName: store.name,
          address: store.address,
          city: store.city,
          state: store.state,
          zipCode: store.zip_code,
          latitude: store.latitude,
          longitude: store.longitude,
          distance: store.distance,
          distanceUnit: store.distance_unit
        },
        hours: store.hours || [],
        phoneNumber: store.phone_number,
        email: store.email,
        isActive: store.is_active,
        deliveryAvailable: store.delivery_available,
        pickupAvailable: store.pickup_available,
        deliveryRadius: store.delivery_radius,
        minimumOrderAmount: store.minimum_order_amount
      }));
      
      setNearbyStores(stores);
      
      // Auto-select nearest store if none selected
      if (!selectedStore && stores.length > 0) {
        await selectStore(stores[0].id);
      }
      
      return stores;
    } catch (error) {
      console.error('Failed to find stores:', error);
      setStoresError('Failed to find nearby stores');
      return [];
    } finally {
      setIsStoresLoading(false);
    }
  }, [api, userLocation, selectedStore]);
  
  /**
   * Select a store
   */
  const selectStore = useCallback(async (storeId: string) => {
    try {
      // Find store in nearby stores or fetch it
      let store = nearbyStores.find(s => s.id === storeId);
      
      if (!store) {
        const response = await api.get(`/stores/${storeId}`);
        store = response.data;
      }
      
      setSelectedStore(store);
      
      // Persist selection
      if (persistStoreSelection) {
        localStorage.setItem(`selectedStore_${tenant?.tenantId}`, storeId);
      }
      
      // Notify backend of store selection
      await api.post(`/stores/${storeId}/select`);
    } catch (error) {
      console.error('Failed to select store:', error);
      setStoresError('Failed to select store');
    }
  }, [api, nearbyStores, persistStoreSelection, tenant]);
  
  /**
   * Clear store selection
   */
  const clearStoreSelection = useCallback(() => {
    setSelectedStore(null);
    if (persistStoreSelection && tenant) {
      localStorage.removeItem(`selectedStore_${tenant.tenantId}`);
    }
  }, [persistStoreSelection, tenant]);
  
  /**
   * Refresh tenant information
   */
  const refreshTenant = useCallback(async () => {
    await resolveTenant();
  }, [resolveTenant]);
  
  /**
   * Initialize tenant on mount
   */
  useEffect(() => {
    resolveTenant();
  }, []);
  
  /**
   * Load saved location on mount
   */
  useEffect(() => {
    const savedLocation = sessionStorage.getItem('userLocation');
    if (savedLocation) {
      try {
        setUserLocation(JSON.parse(savedLocation));
      } catch (error) {
        console.error('Failed to parse saved location:', error);
      }
    } else if (autoDetectLocation) {
      // Request location after a short delay
      setTimeout(() => {
        requestUserLocation();
      }, 1000);
    }
  }, [autoDetectLocation]);
  
  /**
   * Load saved store selection when tenant changes
   */
  useEffect(() => {
    if (tenant && persistStoreSelection) {
      const savedStoreId = localStorage.getItem(`selectedStore_${tenant.tenantId}`);
      if (savedStoreId) {
        selectStore(savedStoreId);
      }
    }
  }, [tenant, persistStoreSelection]);
  
  /**
   * Find stores when location changes
   */
  useEffect(() => {
    if (userLocation && tenant) {
      findNearestStores();
    }
  }, [userLocation, tenant]);
  
  // Context value
  const contextValue: TenantContextState = {
    tenant,
    isTenantLoading,
    tenantError,
    selectedStore,
    nearbyStores,
    isStoresLoading,
    storesError,
    userLocation,
    isLocationLoading,
    locationError,
    locationPermission,
    selectStore,
    findNearestStores,
    requestUserLocation,
    setUserAddress,
    refreshTenant,
    clearStoreSelection
  };
  
  return (
    <TenantContext.Provider value={contextValue}>
      {children}
    </TenantContext.Provider>
  );
};

export default TenantContext;