import React, { useState, useEffect } from 'react';
import { ChevronDown, Store, Building } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useStoreContext } from '../contexts/StoreContext';
import { useTenantContext } from '../contexts/TenantContext';

interface Tenant {
  id: string;
  name: string;
  code: string;
}

interface StoreData {
  id: string;
  name: string;
  store_code: string;
  tenant_id: string;
}

const TopBarSelectors: React.FC = () => {
  const { user, isSuperAdmin, isTenantAdmin, isStoreManager } = useAuth();
  const { currentStore, stores, selectStore, refreshStores } = useStoreContext();
  const { currentTenant, tenants, selectTenant, refreshTenants } = useTenantContext();

  const [showTenantDropdown, setShowTenantDropdown] = useState(false);
  const [showStoreDropdown, setShowStoreDropdown] = useState(false);
  const [filteredStores, setFilteredStores] = useState<StoreData[]>([]);

  // Filter stores based on selected tenant
  useEffect(() => {
    if (currentTenant && stores) {
      const tenantStores = stores.filter(s => s.tenant_id === currentTenant.id);
      setFilteredStores(tenantStores);
    } else {
      setFilteredStores(stores || []);
    }
  }, [currentTenant, stores]);

  // Don't show selectors for store managers and staff - they have fixed context
  if (isStoreManager() && !isTenantAdmin() && !isSuperAdmin()) {
    return (
      <div className="flex items-center space-x-4 text-sm">
        {currentStore && (
          <div className="flex items-center space-x-2 px-3 py-1 bg-gray-50 rounded-lg">
            <Store className="h-4 w-4 text-gray-600" />
            <span className="font-medium">{currentStore.name}</span>
          </div>
        )}
      </div>
    );
  }

  const handleTenantSelect = async (tenant: Tenant) => {
    await selectTenant(tenant.id);
    setShowTenantDropdown(false);
    // Clear store selection when tenant changes
    if (currentStore && currentStore.tenant_id !== tenant.id) {
      // Store will be auto-selected from the new tenant's stores
    }
  };

  const handleStoreSelect = async (store: StoreData) => {
    try {
      await selectStore(store.id);
      setShowStoreDropdown(false);
    } catch (error) {
      console.error('Failed to select store:', error);
    }
  };

  return (
    <div className="flex items-center space-x-4">
      {/* Tenant Selector - Only for Super Admins */}
      {isSuperAdmin() && (
        <div className="relative">
          <button
            onClick={() => setShowTenantDropdown(!showTenantDropdown)}
            className="flex items-center space-x-2 px-3 py-1.5 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Building className="h-4 w-4 text-gray-600" />
            <span className="text-sm font-medium">
              {currentTenant ? currentTenant.name : 'Select Tenant'}
            </span>
            <ChevronDown className="h-4 w-4 text-gray-400" />
          </button>

          {showTenantDropdown && (
            <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg border border-gray-200 border border-gray-200 z-50">
              <div className="p-2 border-b border-gray-200">
                <p className="text-xs text-gray-500 font-medium px-2">SELECT TENANT</p>
              </div>
              <div className="max-h-64 overflow-y-auto">
                {tenants.map((tenant) => (
                  <button
                    key={tenant.id}
                    onClick={() => handleTenantSelect(tenant)}
                    className={`w-full text-left px-4 py-2 hover:bg-gray-50 transition-colors ${
                      currentTenant?.id === tenant.id ? 'bg-blue-50 text-accent-600' : ''
                    }`}
                  >
                    <div className="font-medium text-sm">{tenant.name}</div>
                    <div className="text-xs text-gray-500">{tenant.code}</div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Store Selector - For Super Admins and Tenant Admins */}
      {(isSuperAdmin() || isTenantAdmin()) && (
        <div className="relative">
          <button
            onClick={() => setShowStoreDropdown(!showStoreDropdown)}
            className="flex items-center space-x-2 px-3 py-1.5 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Store className="h-4 w-4 text-gray-600" />
            <span className="text-sm font-medium">
              {currentStore ? currentStore.name : 'Select Store'}
            </span>
            <ChevronDown className="h-4 w-4 text-gray-400" />
          </button>

          {showStoreDropdown && (
            <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg border border-gray-200 border border-gray-200 z-50">
              <div className="p-2 border-b border-gray-200">
                <p className="text-xs text-gray-500 font-medium px-2">SELECT STORE</p>
              </div>
              <div className="max-h-64 overflow-y-auto">
                {filteredStores.length > 0 ? (
                  filteredStores.map((store) => (
                    <button
                      key={store.id}
                      onClick={() => handleStoreSelect(store)}
                      className={`w-full text-left px-4 py-2 hover:bg-gray-50 transition-colors ${
                        currentStore?.id === store.id ? 'bg-blue-50 text-accent-600' : ''
                      }`}
                    >
                      <div className="font-medium text-sm">{store.name}</div>
                      <div className="text-xs text-gray-500">{store.store_code}</div>
                    </button>
                  ))
                ) : (
                  <div className="px-4 py-3 text-sm text-gray-500">
                    {currentTenant ? 'No stores available for this tenant' : 'Please select a tenant first'}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Display current context */}
      {currentStore && (
        <div className="text-sm text-gray-600">
          <span className="font-medium">{currentStore.name}</span>
        </div>
      )}
    </div>
  );
};

export default TopBarSelectors;