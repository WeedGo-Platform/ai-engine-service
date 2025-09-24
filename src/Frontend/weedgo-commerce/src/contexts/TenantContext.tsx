import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { TenantSettings, tenantApi } from '@api/tenant';

interface TenantContextType {
  tenant: TenantSettings | null;
  isLoadingTenant: boolean;
  refreshTenant: () => Promise<void>;
}

const TenantContext = createContext<TenantContextType | undefined>(undefined);

export const useTenant = () => {
  const context = useContext(TenantContext);
  if (!context) {
    throw new Error('useTenant must be used within a TenantProvider');
  }
  return context;
};

interface TenantProviderProps {
  children: ReactNode;
}

export const TenantProvider: React.FC<TenantProviderProps> = ({ children }) => {
  const [tenant, setTenant] = useState<TenantSettings | null>(null);
  const [isLoadingTenant, setIsLoadingTenant] = useState(true);

  const tenantId = import.meta.env.VITE_TENANT_ID;

  const refreshTenant = async () => {
    if (!tenantId) {
      console.error('No tenant ID configured');
      setIsLoadingTenant(false);
      return;
    }

    setIsLoadingTenant(true);
    try {
      const tenantSettings = await tenantApi.getTenantSettings(tenantId);
      setTenant(tenantSettings);
    } catch (error) {
      console.error('Failed to fetch tenant settings:', error);
    } finally {
      setIsLoadingTenant(false);
    }
  };

  useEffect(() => {
    refreshTenant();
  }, [tenantId]);

  return (
    <TenantContext.Provider
      value={{
        tenant,
        isLoadingTenant,
        refreshTenant
      }}
    >
      {children}
    </TenantContext.Provider>
  );
};