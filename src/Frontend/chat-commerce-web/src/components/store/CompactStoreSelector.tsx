/**
 * Compact Store Selector Component
 * A minimal version of store selector for headers and inline use
 * Follows Presentation Component pattern
 */

import React, { useState } from 'react';
import { MapPinIcon, ChevronDownIcon } from '@heroicons/react/24/outline';
import { useTenant } from '../../contexts/TenantContext';
import StoreSelector from './StoreSelector';

/**
 * Compact store selector props
 */
interface CompactStoreSelectorProps {
  className?: string;
  showIcon?: boolean;
  onStoreChange?: (storeId: string) => void;
}

/**
 * Compact Store Selector Component
 */
const CompactStoreSelector: React.FC<CompactStoreSelectorProps> = ({
  className = '',
  showIcon = true,
  onStoreChange
}) => {
  const { selectedStore, nearbyStores } = useTenant();
  const [showModal, setShowModal] = useState(false);
  
  const handleStoreSelected = (storeId: string) => {
    setShowModal(false);
    if (onStoreChange) {
      onStoreChange(storeId);
    }
  };
  
  return (
    <>
      {/* Compact selector button */}
      <button
        onClick={() => setShowModal(true)}
        className={`flex items-center gap-2 px-3 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors ${className}`}
      >
        {showIcon && <MapPinIcon className="h-4 w-4 text-gray-500" />}
        <div className="text-left">
          {selectedStore ? (
            <>
              <p className="text-sm font-medium text-gray-900">{selectedStore.name}</p>
              <p className="text-xs text-gray-500">
                {selectedStore.location.city}, {selectedStore.location.state}
              </p>
            </>
          ) : (
            <p className="text-sm text-gray-600">Select Store</p>
          )}
        </div>
        <ChevronDownIcon className="h-4 w-4 text-gray-400 ml-2" />
      </button>
      
      {/* Store selector modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden">
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">Select Store</h2>
                <button
                  onClick={() => setShowModal(false)}
                  className="text-gray-400 hover:text-gray-500"
                >
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            <div className="p-4 overflow-y-auto max-h-[calc(80vh-80px)]">
              <StoreSelector
                onStoreSelected={handleStoreSelected}
                autoSelectNearest={false}
              />
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default CompactStoreSelector;