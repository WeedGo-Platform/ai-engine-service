import React, { useState } from 'react';
import { MapPinIcon, ChevronDownIcon } from '@heroicons/react/24/outline';
import { useStore } from '@contexts/StoreContext';

const StoreSelector: React.FC = () => {
  const { stores, selectedStore, isLoadingStores, selectStore } = useStore();
  const [isOpen, setIsOpen] = useState(false);

  if (isLoadingStores) {
    return (
      <div className="flex items-center space-x-2 px-4 py-2 bg-gray-100 rounded-lg animate-pulse">
        <div className="w-5 h-5 bg-gray-300 rounded"></div>
        <div className="w-32 h-4 bg-gray-300 rounded"></div>
      </div>
    );
  }

  if (!stores.length) {
    return (
      <div className="flex items-center space-x-2 px-4 py-2 text-gray-500">
        <MapPinIcon className="w-5 h-5" />
        <span className="text-sm">No stores available</span>
      </div>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-3 py-1 bg-white/10 backdrop-blur-sm border border-white/20 rounded-lg hover:bg-white/20 transition-colors"
      >
        <MapPinIcon className="w-5 h-5 text-white" />
        <div className="text-left">
          <div className="text-xs text-white/80">Shopping at</div>
          <div className="text-sm font-medium text-white truncate max-w-[200px]">
            {selectedStore?.name || 'Select a store'}
          </div>
        </div>
        <ChevronDownIcon className={`w-4 h-4 text-white/80 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
          <div className="absolute top-full mt-2 w-96 bg-white border border-gray-200 rounded-lg shadow-lg z-20">
            <div className="p-4 border-b border-gray-200">
              <h3 className="font-semibold text-gray-900">Select Your Store</h3>
              <p className="text-sm text-gray-500 mt-1">Choose a location for pickup or delivery</p>
            </div>

            <div className="max-h-96 overflow-y-auto">
              {stores.map((store) => (
                <button
                  key={store.id}
                  onClick={() => {
                    selectStore(store.id);
                    setIsOpen(false);
                  }}
                  className={`w-full px-4 py-3 hover:bg-gray-50 transition-colors text-left border-b border-gray-100 last:border-b-0 ${
                    selectedStore?.id === store.id ? 'bg-green-50' : ''
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center">
                        <h4 className="font-medium text-gray-900">{store.name}</h4>
                        {selectedStore?.id === store.id && (
                          <span className="ml-2 px-2 py-0.5 text-xs font-medium text-green-700 bg-green-100 rounded-full">
                            Current
                          </span>
                        )}
                      </div>
                      {(store.address || store.city || store.province) && (
                        <p className="text-sm text-gray-500 mt-1">
                          {typeof store.address === 'object' && store.address !== null ?
                            `${(store.address as any).street || ''}${(store.address as any).city ? `, ${(store.address as any).city}` : ''}${(store.address as any).province ? `, ${(store.address as any).province}` : ''}` :
                            `${store.address || ''}${store.city ? `, ${store.city}` : ''}${store.province ? `, ${store.province}` : ''}`
                          }
                        </p>
                      )}
                      <div className="flex items-center space-x-4 mt-2">
                        {store.delivery_available && (
                          <span className="inline-flex items-center text-xs text-gray-600">
                            <svg className="w-4 h-4 mr-1 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                            Delivery
                          </span>
                        )}
                        {store.pickup_available && (
                          <span className="inline-flex items-center text-xs text-gray-600">
                            <svg className="w-4 h-4 mr-1 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                            Pickup
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default StoreSelector;