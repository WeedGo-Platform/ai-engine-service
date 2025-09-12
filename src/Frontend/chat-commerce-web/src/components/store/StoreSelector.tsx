/**
 * Store Selector Component with Location Features
 * Allows users to select stores based on location or manual address entry
 * Follows Component Composition pattern with proper separation of concerns
 */

import React, { useState, useEffect, useCallback } from 'react';
import { MapPinIcon, ClockIcon, PhoneIcon, TruckIcon, ShoppingBagIcon } from '@heroicons/react/24/outline';
import { CheckCircleIcon, ExclamationCircleIcon } from '@heroicons/react/24/solid';
import { useTenant } from '../../contexts/TenantContext';

/**
 * Store selector props
 */
interface StoreSelectorProps {
  onStoreSelected?: (storeId: string) => void;
  className?: string;
  showMap?: boolean;
  autoSelectNearest?: boolean;
}

/**
 * Location input modal props
 */
interface LocationInputModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAddressSubmit: (address: string) => void;
  onLocationRequest: () => void;
  locationPermission: 'granted' | 'denied' | 'prompt' | null;
}

/**
 * Store card props
 */
interface StoreCardProps {
  store: any;
  isSelected: boolean;
  onSelect: () => void;
  showDetails?: boolean;
}

/**
 * Location Input Modal Component
 */
const LocationInputModal: React.FC<LocationInputModalProps> = ({
  isOpen,
  onClose,
  onAddressSubmit,
  onLocationRequest,
  locationPermission
}) => {
  const [address, setAddress] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (address.trim()) {
      setIsSubmitting(true);
      await onAddressSubmit(address);
      setIsSubmitting(false);
      onClose();
    }
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h2 className="text-xl font-bold mb-4">Find Stores Near You</h2>
        
        {locationPermission !== 'denied' && (
          <div className="mb-4">
            <button
              onClick={onLocationRequest}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <MapPinIcon className="h-5 w-5" />
              Use My Current Location
            </button>
          </div>
        )}
        
        <div className="relative my-4">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-300" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-white text-gray-500">Or enter your address</span>
          </div>
        </div>
        
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="Enter your delivery address"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isSubmitting}
          />
          
          <div className="mt-4 flex gap-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
              disabled={isSubmitting || !address.trim()}
            >
              {isSubmitting ? 'Finding Stores...' : 'Find Stores'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

/**
 * Store Card Component
 */
const StoreCard: React.FC<StoreCardProps> = ({
  store,
  isSelected,
  onSelect,
  showDetails = true
}) => {
  const formatDistance = (distance: number, unit: string) => {
    if (distance < 1 && unit === 'km') {
      return `${Math.round(distance * 1000)} m`;
    }
    return `${distance.toFixed(1)} ${unit}`;
  };
  
  const getOperatingStatus = () => {
    const now = new Date();
    const currentDay = now.toLocaleDateString('en-US', { weekday: 'long' });
    const currentTime = now.toTimeString().slice(0, 5);
    
    const todayHours = store.hours?.find((h: any) => h.dayOfWeek === currentDay);
    
    if (!todayHours || todayHours.isClosed) {
      return { isOpen: false, text: 'Closed' };
    }
    
    if (currentTime >= todayHours.openTime && currentTime <= todayHours.closeTime) {
      return { isOpen: true, text: `Open until ${todayHours.closeTime}` };
    }
    
    return { isOpen: false, text: `Opens at ${todayHours.openTime}` };
  };
  
  const status = getOperatingStatus();
  
  return (
    <div
      className={`border rounded-lg p-4 cursor-pointer transition-all ${
        isSelected
          ? 'border-green-500 bg-green-50 ring-2 ring-green-500'
          : 'border-gray-200 hover:border-gray-300 hover:shadow-md'
      }`}
      onClick={onSelect}
    >
      <div className="flex justify-between items-start mb-2">
        <div className="flex-1">
          <h3 className="font-semibold text-lg">{store.name}</h3>
          {store.location.distance && (
            <p className="text-sm text-gray-600">
              {formatDistance(store.location.distance, store.location.distanceUnit || 'km')} away
            </p>
          )}
        </div>
        {isSelected && (
          <CheckCircleIcon className="h-6 w-6 text-green-500 flex-shrink-0" />
        )}
      </div>
      
      {showDetails && (
        <>
          <div className="text-sm text-gray-600 space-y-1 mb-3">
            <p className="flex items-start gap-1">
              <MapPinIcon className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <span>
                {store.location.address}, {store.location.city}, {store.location.state} {store.location.zipCode}
              </span>
            </p>
            
            {store.phoneNumber && (
              <p className="flex items-center gap-1">
                <PhoneIcon className="h-4 w-4" />
                <span>{store.phoneNumber}</span>
              </p>
            )}
            
            <p className="flex items-center gap-1">
              <ClockIcon className="h-4 w-4" />
              <span className={status.isOpen ? 'text-green-600' : 'text-red-600'}>
                {status.text}
              </span>
            </p>
          </div>
          
          <div className="flex gap-2">
            {store.pickupAvailable && (
              <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                <ShoppingBagIcon className="h-3 w-3" />
                Pickup
              </span>
            )}
            {store.deliveryAvailable && (
              <span className="inline-flex items-center gap-1 px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full">
                <TruckIcon className="h-3 w-3" />
                Delivery
              </span>
            )}
          </div>
          
          {store.minimumOrderAmount && (
            <p className="text-xs text-gray-500 mt-2">
              Minimum order: ${store.minimumOrderAmount}
            </p>
          )}
        </>
      )}
    </div>
  );
};

/**
 * Main Store Selector Component
 */
const StoreSelector: React.FC<StoreSelectorProps> = ({
  onStoreSelected,
  className = '',
  showMap = false,
  autoSelectNearest = true
}) => {
  const {
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
    setUserAddress
  } = useTenant();
  
  const [showLocationModal, setShowLocationModal] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  
  // Initialize location on mount
  useEffect(() => {
    if (!isInitialized && !userLocation && !isLocationLoading) {
      setShowLocationModal(true);
      setIsInitialized(true);
    }
  }, [isInitialized, userLocation, isLocationLoading]);
  
  // Handle store selection
  const handleStoreSelect = useCallback(async (storeId: string) => {
    await selectStore(storeId);
    if (onStoreSelected) {
      onStoreSelected(storeId);
    }
  }, [selectStore, onStoreSelected]);
  
  // Handle location request
  const handleLocationRequest = useCallback(async () => {
    const location = await requestUserLocation();
    if (location) {
      setShowLocationModal(false);
      await findNearestStores(location);
    }
  }, [requestUserLocation, findNearestStores]);
  
  // Handle address submission
  const handleAddressSubmit = useCallback(async (address: string) => {
    const location = await setUserAddress(address);
    if (location) {
      await findNearestStores(location);
    }
  }, [setUserAddress, findNearestStores]);
  
  // Handle change location
  const handleChangeLocation = () => {
    setShowLocationModal(true);
  };
  
  // Loading state
  if (isStoresLoading || isLocationLoading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-gray-600">
            {isLocationLoading ? 'Getting your location...' : 'Finding nearby stores...'}
          </p>
        </div>
      </div>
    );
  }
  
  // Error state
  if (storesError || locationError) {
    return (
      <div className={`p-4 ${className}`}>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start gap-2">
            <ExclamationCircleIcon className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-red-700 font-medium">Error finding stores</p>
              <p className="text-red-600 text-sm mt-1">
                {storesError || locationError || 'Unable to find stores near you'}
              </p>
              <button
                onClick={handleChangeLocation}
                className="mt-2 text-sm text-red-700 underline hover:text-red-800"
              >
                Try a different location
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className={className}>
      {/* Location header */}
      {userLocation && (
        <div className="mb-4 p-3 bg-gray-50 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MapPinIcon className="h-5 w-5 text-gray-600" />
            <div>
              <p className="text-sm font-medium">Delivery Location</p>
              <p className="text-xs text-gray-600">
                {userLocation.address || `${userLocation.latitude.toFixed(4)}, ${userLocation.longitude.toFixed(4)}`}
              </p>
            </div>
          </div>
          <button
            onClick={handleChangeLocation}
            className="text-sm text-blue-600 hover:text-blue-700 underline"
          >
            Change
          </button>
        </div>
      )}
      
      {/* Store list */}
      {nearbyStores.length > 0 ? (
        <div className="space-y-3">
          <h3 className="font-semibold text-lg mb-2">
            {selectedStore ? 'Select a Different Store' : 'Select a Store'}
          </h3>
          {nearbyStores.map((store) => (
            <StoreCard
              key={store.id}
              store={store}
              isSelected={selectedStore?.id === store.id}
              onSelect={() => handleStoreSelect(store.id)}
              showDetails={true}
            />
          ))}
        </div>
      ) : (
        <div className="text-center p-8">
          <MapPinIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 mb-4">No stores found near your location</p>
          <button
            onClick={handleChangeLocation}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Try a Different Location
          </button>
        </div>
      )}
      
      {/* Location input modal */}
      <LocationInputModal
        isOpen={showLocationModal}
        onClose={() => setShowLocationModal(false)}
        onAddressSubmit={handleAddressSubmit}
        onLocationRequest={handleLocationRequest}
        locationPermission={locationPermission}
      />
    </div>
  );
};

export default StoreSelector;