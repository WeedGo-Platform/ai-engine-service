/**
 * Store Selector Component
 * Provides UI for selecting and switching between stores
 * Displays current store info and inventory statistics
 */

import React, { useState, useEffect, useRef } from 'react';
import { ChevronDownIcon, BuildingStorefrontIcon, CheckIcon } from '@heroicons/react/24/outline';
import { useStoreContext } from '../contexts/StoreContext';

interface StoreSelectorProps {
  className?: string;
  showStats?: boolean;
  compact?: boolean;
  position?: 'header' | 'sidebar' | 'modal';
}

export const StoreSelector: React.FC<StoreSelectorProps> = ({
  className = '',
  showStats = false,
  compact = false,
  position = 'header',
}) => {
  const {
    currentStore,
    stores,
    isLoading,
    error,
    selectStore,
    inventoryStats,
    isStoreActive,
  } = useStoreContext();

  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Filter stores based on search term
  const filteredStores = stores.filter(store =>
    store.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    store.store_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
    store.address.city.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleStoreSelect = async (storeId: string) => {
    try {
      await selectStore(storeId);
      setIsOpen(false);
      setSearchTerm('');
    } catch (error) {
      console.error('Failed to select store:', error);
    }
  };

  if (isLoading) {
    return (
      <div className={`animate-pulse ${className}`}>
        <div className="h-10 bg-gray-100 rounded w-48"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`text-red-500 text-sm ${className}`}>
        Failed to load stores
      </div>
    );
  }

  if (stores.length === 0) {
    return (
      <div className={`text-gray-500 text-sm ${className}`}>
        No stores available
      </div>
    );
  }

  // Compact view for sidebar or limited space
  if (compact) {
    return (
      <div className={`relative ${className}`} ref={dropdownRef}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center justify-center w-10 h-10 rounded-lg hover:bg-gray-50 transition-colors"
          title={currentStore?.name || 'Select Store'}
        >
          <BuildingStorefrontIcon className="h-6 w-6 text-gray-600" />
          {currentStore && (
            <span className="absolute -top-1 -right-1 h-3 w-3 bg-primary-500 rounded-full"></span>
          )}
        </button>
        
        {isOpen && (
          <div className="absolute z-50 mt-2 w-72 bg-white rounded-lg border border-gray-200 border border-gray-200">
            {renderDropdownContent()}
          </div>
        )}
      </div>
    );
  }

  // Full view for header
  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`
          flex items-center gap-4 px-4 py-2 bg-white border border-gray-200 
          rounded-lg hover:border-gray-300 transition-colors min-w-[200px]
          ${isOpen ? 'border-blue-500 ring-2 ring-blue-200' : ''}
        `}
      >
        <BuildingStorefrontIcon className="h-5 w-5 text-gray-600" />
        <div className="flex-1 text-left">
          {currentStore ? (
            <div>
              <p className="text-sm font-medium text-gray-900">{currentStore.name}</p>
              <p className="text-xs text-gray-500">{currentStore.store_code}</p>
            </div>
          ) : (
            <p className="text-sm text-gray-500">Select a store</p>
          )}
        </div>
        <ChevronDownIcon 
          className={`h-5 w-5 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} 
        />
      </button>

      {isOpen && (
        <div className={`
          absolute z-50 mt-2 bg-white rounded-lg border border-gray-200 border border-gray-200
          ${position === 'header' ? 'w-96' : 'w-full min-w-[320px]'}
        `}>
          {renderDropdownContent()}
        </div>
      )}

      {showStats && currentStore && inventoryStats && (
        <div className="mt-2 p-4 bg-gray-50 rounded-lg text-xs">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <span className="text-gray-500">Total SKUs:</span>
              <span className="ml-2 font-medium">{inventoryStats.total_skus}</span>
            </div>
            <div>
              <span className="text-gray-500">Total Qty:</span>
              <span className="ml-2 font-medium">{inventoryStats.total_quantity}</span>
            </div>
            <div>
              <span className="text-gray-500">Low Stock:</span>
              <span className="ml-2 font-medium text-orange-600">
                {inventoryStats.low_stock_items}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Out of Stock:</span>
              <span className="ml-2 font-medium text-danger-600">
                {inventoryStats.out_of_stock_items}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  function renderDropdownContent() {
    return (
      <>
        {/* Search input */}
        <div className="p-4 border-b border-gray-200">
          <input
            type="text"
            placeholder="Search stores..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            autoFocus
          />
        </div>

        {/* Store list */}
        <div className="max-h-96 overflow-y-auto">
          {filteredStores.length === 0 ? (
            <div className="p-6 text-center text-gray-500 text-sm">
              No stores found
            </div>
          ) : (
            filteredStores.map((store) => (
              <button
                key={store.id}
                onClick={() => handleStoreSelect(store.id)}
                disabled={!isStoreActive(store.id)}
                className={`
                  w-full p-4 text-left hover:bg-gray-50 transition-colors
                  border-b border-gray-100 last:border-0
                  ${currentStore?.id === store.id ? 'bg-blue-50' : ''}
                  ${!isStoreActive(store.id) ? 'opacity-50 cursor-not-allowed' : ''}
                `}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium text-gray-900">
                        {store.name}
                      </p>
                      {currentStore?.id === store.id && (
                        <CheckIcon className="h-4 w-4 text-accent-600" />
                      )}
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {store.store_code} • {store.address.city}, {store.address.province}
                    </p>
                    {store.phone && (
                      <p className="text-xs text-gray-400 mt-1">{store.phone}</p>
                    )}
                  </div>
                  <div className="ml-3">
                    <span className={`
                      inline-flex items-center px-2 py-1 rounded-full text-xs font-medium
                      ${store.status === 'active' 
                        ? 'bg-primary-100 text-primary-800' 
                        : store.status === 'inactive'
                        ? 'bg-gray-50 text-gray-800'
                        : 'bg-danger-100 text-danger-800'
                      }
                    `}>
                      {store.status}
                    </span>
                  </div>
                </div>
                
                {/* Store features indicators */}
                <div className="flex gap-2 mt-2">
                  {store.delivery_enabled && (
                    <span className="text-xs bg-blue-100 text-accent-700 px-2 py-0.5 rounded">
                      Delivery
                    </span>
                  )}
                  {store.pickup_enabled && (
                    <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                      Pickup
                    </span>
                  )}
                  {store.pos_enabled && (
                    <span className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded">
                      POS
                    </span>
                  )}
                  {store.ecommerce_enabled && (
                    <span className="text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded">
                      E-commerce
                    </span>
                  )}
                </div>
              </button>
            ))
          )}
        </div>

        {/* Quick actions */}
        {currentStore && (
          <div className="p-4 border-t border-gray-200 bg-gray-50">
            <div className="text-xs text-gray-600">
              Current: <span className="font-medium">{currentStore.name}</span>
            </div>
          </div>
        )}
      </>
    );
  }
};

export default StoreSelector;