import React, { useState, useEffect } from 'react';
import { X, Store, Building2, ChevronRight } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import tenantService from '../services/tenantService';

interface StoreSelectionModalProps {
  isOpen: boolean;
  onSelect: (tenantId: string, storeId: string, storeName: string, tenantName?: string) => void;
  onClose?: () => void;
}

const StoreSelectionModal: React.FC<StoreSelectionModalProps> = ({ 
  isOpen, 
  onSelect,
  onClose 
}) => {
  const { user, isSuperAdmin, isTenantAdminOnly } = useAuth();
  const [selectedTenant, setSelectedTenant] = useState<string>('');
  const [selectedStore, setSelectedStore] = useState<string>('');
  const [step, setStep] = useState<'tenant' | 'store'>('tenant');

  // Fetch all tenants (for super admin)
  const { data: tenants, isLoading: loadingTenants, error: tenantsError } = useQuery({
    queryKey: ['tenants'],
    queryFn: async () => {
      try {
        // Using getTenants method from tenantService
        const response = await tenantService.getTenants();
        console.log('Fetched tenants:', response);
        // Handle both array and wrapped response
        if (Array.isArray(response)) {
          return response;
        } else if (response?.tenants) {
          return response.tenants;
        } else if (response?.data) {
          return Array.isArray(response.data) ? response.data : response.data.tenants || [];
        }
        return [];
      } catch (error) {
        console.error('Error fetching tenants:', error);
        throw error;
      }
    },
    enabled: isSuperAdmin() && isOpen,
  });

  // Fetch stores for selected tenant or for tenant admin without explicit tenant ID
  const { data: stores, isLoading: loadingStores, error: storesError, refetch: refetchStores } = useQuery({
    queryKey: ['stores', selectedTenant, isTenantAdminOnly()],
    queryFn: async () => {
      console.log('Store query function called with tenant:', selectedTenant);
      
      // This shouldn't happen now that backend returns fresh data
      // But keep as fallback just in case
      if (isTenantAdminOnly() && !selectedTenant) {
        console.log('Warning: Tenant admin without tenant ID in state');
        return []
      }
      
      if (!selectedTenant) {
        console.log('No tenant ID, returning empty array');
        return [];
      }
      
      console.log('Fetching stores for tenant:', selectedTenant);
      try {
        const response = await tenantService.getStores(selectedTenant);
        console.log('Stores response:', response);
        // Handle both array and wrapped response
        if (Array.isArray(response)) {
          return response;
        } else if (response?.stores) {
          return response.stores;
        } else if (response?.data) {
          return Array.isArray(response.data) ? response.data : response.data.stores || [];
        }
        return [];
      } catch (error) {
        console.error('Error fetching stores:', error);
        throw error;
      }
    },
    enabled: (!!selectedTenant || isTenantAdminOnly()) && isOpen,
    staleTime: 0, // Always fetch fresh data
    gcTime: 0, // Don't cache the data
  });

  // Refetch stores when tenant changes
  useEffect(() => {
    if (selectedTenant && isOpen) {
      console.log('Tenant changed, refetching stores for:', selectedTenant);
      refetchStores();
    }
  }, [selectedTenant, isOpen, refetchStores]);

  useEffect(() => {
    if (isOpen) {
      console.log('Modal opened - User data:', {
        user,
        tenants: user?.tenants,
        stores: user?.stores,
        isTenantAdminOnly: isTenantAdminOnly(),
        isSuperAdmin: isSuperAdmin()
      });
      
      // Reset state when modal opens
      setSelectedStore('');
      
      if (isTenantAdminOnly()) {
        // For tenant admin, we need to find the tenant ID
        // It could be in user.tenants or we might need to extract it from user.stores
        let tenantId: string | undefined;
        
        if (user?.tenants && user.tenants.length > 0) {
          // The tenant object has 'id' field based on AuthContext interface
          tenantId = user.tenants[0].id;
          console.log('Found tenant ID from user.tenants:', tenantId);
        } else if (user?.stores && user.stores.length > 0) {
          // If no tenants, but we have stores, get tenant_id from the first store
          tenantId = user.stores[0].tenant_id;
          console.log('Found tenant ID from user.stores:', tenantId);
        }
        
        if (tenantId) {
          setSelectedTenant(tenantId);
          setStep('store');
        } else {
          console.error('No tenant ID found for tenant admin user', { user });
          // Still try to show stores if we have them
          setStep('store');
        }
      } else if (isSuperAdmin()) {
        // For super admin, start with tenant selection
        setSelectedTenant('');
        setStep('tenant');
      }
    }
  }, [isOpen, user, isTenantAdminOnly, isSuperAdmin]);

  const handleTenantSelect = (tenantId: string) => {
    setSelectedTenant(tenantId);
    setStep('store');
  };

  const handleStoreSelect = (storeId: string, storeName: string) => {
    setSelectedStore(storeId);
    const selectedTenantData = isTenantAdminOnly()
      ? user?.tenants?.[0]
      : tenants?.find((t: any) => t.id === selectedTenant);
    onSelect(selectedTenant, storeId, storeName, selectedTenantData?.name);
  };

  const handleBack = () => {
    if (step === 'store' && isSuperAdmin()) {
      setStep('tenant');
      setSelectedStore('');
    }
  };

  if (!isOpen) return null;

  const renderTenantSelection = () => {
    if (tenantsError) {
      return (
        <div className="text-center py-8">
          <p className="text-red-600 mb-2">Failed to load tenants</p>
          <p className="text-sm text-gray-500">Please refresh and try again</p>
        </div>
      );
    }

    if (loadingTenants) {
      return (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      );
    }

    return (
      <div className="space-y-3">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Building2 className="w-5 h-5 text-blue-600" />
          Select Tenant
        </h3>
        <div className="max-h-96 overflow-y-auto space-y-2">
          {(!tenants || tenants.length === 0) ? (
            <div className="text-center py-8 text-gray-500">
              No tenants available
            </div>
          ) : (
            tenants.map((tenant: any) => (
            <button
              key={tenant.id}
              onClick={() => handleTenantSelect(tenant.id)}
              className="w-full text-left p-4 rounded-lg border hover:border-blue-500 hover:bg-blue-50 transition-all group"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-semibold text-gray-900">{tenant.name}</p>
                  <p className="text-sm text-gray-500">Code: {tenant.code}</p>
                </div>
                <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-blue-600" />
              </div>
            </button>
          )))}
        </div>
      </div>
    );
  };

  const renderStoreSelection = () => {
    console.log('renderStoreSelection - state:', {
      loadingStores,
      stores,
      storesError,
      selectedTenant,
      step
    });

    if (loadingStores) {
      return (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      );
    }

    if (storesError) {
      return (
        <div className="text-center py-8">
          <p className="text-red-600 mb-2">Failed to load stores</p>
          <p className="text-sm text-gray-500">Please refresh and try again</p>
        </div>
      );
    }

    // For tenant admins, use fetched stores since user.stores might not be populated
    const availableStores = stores || [];
    const selectedTenantData = isTenantAdminOnly() 
      ? user?.tenants?.[0] 
      : tenants?.find((t: any) => t.id === selectedTenant);
    
    // If no stores available, show appropriate message
    if (!availableStores || availableStores.length === 0) {
      return (
        <div className="space-y-3">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Store className="w-5 h-5 text-green-600" />
              Select Store
            </h3>
            {isSuperAdmin() && (
              <button
                onClick={handleBack}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                ← Back to Tenants
              </button>
            )}
          </div>
          
          {selectedTenantData && (
            <div className="bg-gray-50 p-3 rounded-lg mb-4">
              <p className="text-sm text-gray-600">
                Tenant: <span className="font-semibold text-gray-900">{selectedTenantData.name}</span>
              </p>
            </div>
          )}

          <div className="text-center py-8 text-gray-500">
            No stores available for this tenant
          </div>
        </div>
      );
    }

    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Store className="w-5 h-5 text-green-600" />
            Select Store
          </h3>
          {isSuperAdmin() && (
            <button
              onClick={handleBack}
              className="text-sm text-blue-600 hover:text-blue-700"
            >
              ← Back to Tenants
            </button>
          )}
        </div>
        
        {selectedTenantData && (
          <div className="bg-gray-50 p-3 rounded-lg mb-4">
            <p className="text-sm text-gray-600">
              Tenant: <span className="font-semibold text-gray-900">{selectedTenantData.name}</span>
            </p>
          </div>
        )}

        <div className="max-h-96 overflow-y-auto space-y-2">
          {availableStores?.map((store: any) => (
            <button
              key={store.id}
              onClick={() => handleStoreSelect(store.id, store.name)}
              className="w-full text-left p-4 rounded-lg border hover:border-green-500 hover:bg-green-50 transition-all group"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-semibold text-gray-900">{store.name}</p>
                  <p className="text-sm text-gray-500">Code: {store.store_code || store.code}</p>
                  {store.address && (
                    <p className="text-xs text-gray-400 mt-1">
                      {typeof store.address === 'string' 
                        ? store.address 
                        : `${store.address.street}, ${store.address.city}, ${store.address.province} ${store.address.postal_code}`}
                    </p>
                  )}
                </div>
                <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-green-600" />
              </div>
            </button>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-bold text-gray-900">
            Select Store for Purchase Orders
          </h2>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          )}
        </div>

        <div className="p-6">
          {step === 'tenant' && isSuperAdmin() && renderTenantSelection()}
          {step === 'store' && renderStoreSelection()}
        </div>

        <div className="px-6 py-4 bg-gray-50 border-t">
          <p className="text-sm text-gray-600">
            {isSuperAdmin() 
              ? "As a super admin, please select a tenant and store to manage purchase orders."
              : isTenantAdminOnly()
              ? "Select a store from your tenant to manage purchase orders."
              : ""}
          </p>
        </div>
      </div>
    </div>
  );
};

export default StoreSelectionModal;