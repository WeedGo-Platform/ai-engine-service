import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from './AuthContext';
import { getApiUrl } from '../config/app.config';

// =====================================================
// Type Definitions
// =====================================================

interface Tenant {
  id: string;
  name: string;
  code: string;
  status?: string;
}

interface TenantContextValue {
  currentTenant: Tenant | null;
  tenants: Tenant[];
  isLoading: boolean;
  error: Error | null;
  selectTenant: (tenantId: string) => Promise<void>;
  clearTenant: () => void;
  refreshTenants: () => Promise<void>;
}

interface TenantProviderProps {
  children: ReactNode;
}

// =====================================================
// Constants
// =====================================================

const TENANT_CONTEXT_KEY = 'weedgo_active_tenant';

// =====================================================
// Context Creation
// =====================================================

const TenantContext = createContext<TenantContextValue | undefined>(undefined);

// =====================================================
// Custom Hook
// =====================================================

export const useTenantContext = (): TenantContextValue => {
  const context = useContext(TenantContext);
  if (!context) {
    throw new Error('useTenantContext must be used within a TenantProvider');
  }
  return context;
};

// =====================================================
// API Service Functions
// =====================================================

const tenantService = {
  fetchTenants: async (): Promise<Tenant[]> => {
    const token = localStorage.getItem('weedgo_auth_access_token') ||
                  sessionStorage.getItem('weedgo_auth_access_token');

    const response = await fetch(`${API_BASE_URL}/api/tenants`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch tenants');
    }

    return response.json();
  },
};

// =====================================================
// Storage Utilities
// =====================================================

const storageUtils = {
  getStoredTenantId: (): string | null => {
    try {
      return localStorage.getItem(TENANT_CONTEXT_KEY);
    } catch (error) {
      console.error('Failed to read from localStorage:', error);
      return null;
    }
  },

  saveTenantId: (tenantId: string): void => {
    try {
      localStorage.setItem(TENANT_CONTEXT_KEY, tenantId);
    } catch (error) {
      console.error('Failed to save to localStorage:', error);
    }
  },

  clearTenantId: (): void => {
    try {
      localStorage.removeItem(TENANT_CONTEXT_KEY);
    } catch (error) {
      console.error('Failed to clear localStorage:', error);
    }
  },
};

// =====================================================
// Tenant Provider Component
// =====================================================

export const TenantProvider: React.FC<TenantProviderProps> = ({ children }) => {
  const queryClient = useQueryClient();
  const { user, isSuperAdmin, isTenantAdmin, isAuthenticated } = useAuth();
  const [currentTenant, setCurrentTenant] = useState<Tenant | null>(null);

  // Fetch tenants query
  const {
    data: allTenants = [],
    isLoading,
    error,
    refetch: refreshTenants,
  } = useQuery<Tenant[], Error>({
    queryKey: ['tenants', user?.user_id],
    queryFn: tenantService.fetchTenants,
    enabled: isAuthenticated && (isSuperAdmin() || isTenantAdmin()),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Filter tenants based on user permissions
  const tenants = React.useMemo(() => {
    if (isSuperAdmin()) {
      return allTenants;
    }

    if (isTenantAdmin() && user?.tenant_id) {
      return allTenants.filter(t => t.id === user.tenant_id);
    }

    return [];
  }, [allTenants, isSuperAdmin, isTenantAdmin, user]);

  // Select tenant
  const selectTenant = useCallback(async (tenantId: string) => {
    const tenant = tenants.find(t => t.id === tenantId);
    if (!tenant) {
      throw new Error(`Tenant with ID ${tenantId} not found or not accessible`);
    }

    setCurrentTenant(tenant);
    storageUtils.saveTenantId(tenantId);

    // Set tenant ID in request headers for subsequent API calls
    window.localStorage.setItem('X-Tenant-ID', tenantId);
  }, [tenants]);

  // Clear tenant selection
  const clearTenant = useCallback(() => {
    setCurrentTenant(null);
    storageUtils.clearTenantId();
    window.localStorage.removeItem('X-Tenant-ID');
  }, []);

  // Auto-select tenant on mount
  useEffect(() => {
    if (!isLoading && tenants.length > 0 && !currentTenant) {
      // For tenant admins with only one tenant, auto-select it
      if (isTenantAdmin() && !isSuperAdmin() && tenants.length === 1) {
        selectTenant(tenants[0].id).catch(console.error);
      } else {
        // Try to restore previous selection
        const storedId = storageUtils.getStoredTenantId();
        if (storedId && tenants.find(t => t.id === storedId)) {
          selectTenant(storedId).catch(console.error);
        }
      }
    }
  }, [isLoading, tenants, currentTenant, isTenantAdmin, isSuperAdmin, selectTenant]);

  // Set global tenant header for API requests
  useEffect(() => {
    if (currentTenant) {
      const originalFetch = window.fetch;
      window.fetch = function(...args) {
        const [url, config = {}] = args;

        if (typeof url === 'string' && url.includes('/api/')) {
          config.headers = {
            ...config.headers,
            'X-Tenant-ID': currentTenant.id,
          };
        }

        return originalFetch.call(this, url, config);
      };

      return () => {
        window.fetch = originalFetch;
      };
    }
  }, [currentTenant]);

  const contextValue: TenantContextValue = {
    currentTenant,
    tenants,
    isLoading,
    error,
    selectTenant,
    clearTenant,
    refreshTenants,
  };

  return (
    <TenantContext.Provider value={contextValue}>
      {children}
    </TenantContext.Provider>
  );
};

export default TenantContext;