import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Store as StoreIcon,
  Settings,
  ArrowLeft,
  Save,
  AlertCircle,
  Clock,
  MapPin,
  Phone,
  Mail
} from 'lucide-react';
import storeService, { Store } from '../services/storeService';
import AllSettingsTabbed from '../components/storeSettings/AllSettingsTabbed';
import { useStoreContext } from '../contexts/StoreContext';
import { useAuth } from '../contexts/AuthContext';

const StoreSettings: React.FC = () => {
  const { storeCode } = useParams<{ storeCode: string }>();
  const navigate = useNavigate();
  const { currentStore, stores, selectStore } = useStoreContext();
  const { user } = useAuth();
  const [store, setStore] = useState<Store | null>(null);
  const [storeSettings, setStoreSettings] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'general' | 'settings'>('general');

  useEffect(() => {
    loadStoreData();
  }, [storeCode, currentStore]);

  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [success]);

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  const loadStoreData = async () => {
    try {
      setLoading(true);
      let storeData: Store | null = null;

      // Guard: Don't attempt to fetch if storeCode is undefined/empty
      if (!storeCode || storeCode === 'undefined') {
        console.warn('StoreSettings: Invalid or missing storeCode in URL:', storeCode);

        // Try to use currentStore from context as fallback
        if (currentStore?.store_code) {
          console.log('StoreSettings: Using store_code from context:', currentStore.store_code);
          // Redirect to proper URL with store code
          navigate(`/dashboard/stores/${currentStore.store_code}/settings`, { replace: true });
          return;
        }

        setError('No store selected. Please select a store first.');
        setLoading(false);
        return;
      }

      // Use store code from URL to fetch directly from API
      // This is simpler and more reliable than depending on context being populated
      try {
        storeData = await storeService.getStoreByCode(storeCode);

        // Update context with the found store for consistency
        if (storeData && storeData.id !== currentStore?.id) {
          await selectStore(storeData.id);
        }
      } catch (err: any) {
        console.error('Error fetching store by code:', err);
        // Check if it's a 404 or other error
        if (err.response?.status === 404) {
          setError(`Store with code "${storeCode}" not found`);
        } else {
          setError('Failed to load store data. Please try again.');
        }
      }

      if (storeData) {
        setStore(storeData);
        setStoreSettings(storeData.settings || {});
        setError(null);
      }
    } catch (err) {
      setError('Failed to load store settings');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSettings = async (category: string, settings: any) => {
    try {
      // Update the store's settings field with the new settings
      const updatedSettings = {
        ...storeSettings,
        [category]: settings
      };
      
      await storeService.updateStore(store!.id, {
        settings: updatedSettings
      });
      
      setStoreSettings(updatedSettings);
      setSuccess(`${category.charAt(0).toUpperCase() + category.slice(1)} settings updated successfully`);
    } catch (err) {
      setError(`Failed to update ${category} settings`);
      throw err;
    }
  };

  const formatHours = (hours: any) => {
    if (!hours) return 'Not set';
    
    const daysOfWeek = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
    return daysOfWeek.map(day => {
      const dayHours = hours[day];
      if (!dayHours || dayHours.closed) {
        return `${day.charAt(0).toUpperCase() + day.slice(1)}: Closed`;
      }
      return `${day.charAt(0).toUpperCase() + day.slice(1)}: ${dayHours.open} - ${dayHours.close}`;
    }).join(', ');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50 dark:bg-gray-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 dark:border-primary-400"></div>
      </div>
    );
  }

  if (!store) {
    return (
      <div className="p-6 bg-gray-50 dark:bg-gray-900 min-h-screen">
        <div className="bg-danger-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg p-6">
          <p className="text-red-700 dark:text-red-300">Store not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-gray-50 dark:bg-gray-900 min-h-screen">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => {
            // Navigate back to the tenant's stores page
            if (store?.tenant_code) {
              navigate(`/tenants/${store.tenant_code}/stores`);
            } else if (store?.tenant_id) {
              // Fallback to navigate back if we don't have tenant_code
              navigate(-1);
            } else {
              navigate(-1); // Go back if we don't have tenant info
            }
          }}
          className="mb-4 flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Stores
        </button>

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-4 text-gray-900 dark:text-white">
              <StoreIcon className="w-8 h-8" />
              {store.name} Settings
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">Manage store configuration and POS settings</p>
          </div>
        </div>
      </div>

      {/* Alerts */}
      {success && (
        <div className="mb-4 p-6 bg-primary-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 rounded-lg flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-primary-500 dark:text-green-400" />
          <span className="text-primary-700 dark:text-green-300">{success}</span>
        </div>
      )}

      {error && (
        <div className="mb-4 p-6 bg-danger-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-red-500 dark:text-red-400" />
          <span className="text-red-700 dark:text-red-300">{error}</span>
        </div>
      )}

      {/* Tabs */}
      <div className="mb-6 border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('general')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'general'
                ? 'border-blue-500 dark:border-primary-400 text-accent-600 dark:text-primary-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-200 dark:hover:border-gray-600'
            }`}
          >
            General Information
          </button>
          <button
            onClick={() => setActiveTab('settings')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'settings'
                ? 'border-blue-500 dark:border-primary-400 text-accent-600 dark:text-primary-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-200 dark:hover:border-gray-600'
            }`}
          >
            Store Configuration
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'general' && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">General Information</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Store Name
              </label>
              <p className="text-lg text-gray-900 dark:text-white">{store.name}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Store Code
              </label>
              <p className="text-lg font-mono text-gray-900 dark:text-white">{store.store_code}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                <Phone className="inline w-4 h-4 mr-1" />
                Phone
              </label>
              <p className="text-lg text-gray-900 dark:text-white">{store.phone || 'Not specified'}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                <Mail className="inline w-4 h-4 mr-1" />
                Email
              </label>
              <p className="text-lg text-gray-900 dark:text-white">{store.email || 'Not specified'}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                License Number
              </label>
              <p className="text-lg text-gray-900 dark:text-white">{store.license_number || 'Not specified'}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                License Expiry
              </label>
              <p className="text-lg text-gray-900 dark:text-white">
                {store.license_expiry
                  ? new Date(store.license_expiry).toLocaleDateString()
                  : 'Not specified'}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Tax Rate
              </label>
              <p className="text-lg text-gray-900 dark:text-white">{store.tax_rate}%</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Timezone
              </label>
              <p className="text-lg text-gray-900 dark:text-white">{store.timezone}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Status
              </label>
              <span className={`inline-flex px-2 py-1 rounded-full text-sm font-medium ${
                store.status === 'active'
                  ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                  : 'bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
              }`}>
                {store.status}
              </span>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Delivery Radius
              </label>
              <p className="text-lg text-gray-900 dark:text-white">{store.delivery_radius_km} km</p>
            </div>
          </div>
          
          {store.address && (
            <div className="mt-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                <MapPin className="inline w-4 h-4 mr-1" />
                Address
              </label>
              <p className="text-lg text-gray-900 dark:text-white">
                {store.address.street}<br />
                {store.address.city}, {store.address.province} {store.address.postal_code}<br />
                {store.address.country}
              </p>
            </div>
          )}

          <div className="mt-6">
            <h3 className="text-lg font-semibold mb-3 text-gray-900 dark:text-white">Service Options</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={store.delivery_enabled}
                  disabled
                  className="w-4 h-4 text-accent-600 dark:text-accent-400 rounded"
                />
                <span className="text-sm text-gray-900 dark:text-white">Delivery Enabled</span>
              </label>

              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={store.pickup_enabled}
                  disabled
                  className="w-4 h-4 text-accent-600 dark:text-accent-400 rounded"
                />
                <span className="text-sm text-gray-900 dark:text-white">Pickup Enabled</span>
              </label>

              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={store.kiosk_enabled}
                  disabled
                  className="w-4 h-4 text-accent-600 dark:text-accent-400 rounded"
                />
                <span className="text-sm text-gray-900 dark:text-white">Kiosk Enabled</span>
              </label>

              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={store.pos_enabled}
                  disabled
                  className="w-4 h-4 text-accent-600 dark:text-accent-400 rounded"
                />
                <span className="text-sm text-gray-900 dark:text-white">POS Enabled</span>
              </label>

              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={store.ecommerce_enabled}
                  disabled
                  className="w-4 h-4 text-accent-600 dark:text-accent-400 rounded"
                />
                <span className="text-sm text-gray-900 dark:text-white">E-commerce Enabled</span>
              </label>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'settings' && (
        <AllSettingsTabbed
          storeId={store?.id || ''}
          initialSettings={storeSettings}
          store={store}
          onSave={handleSaveSettings}
        />
      )}

    </div>
  );
};

export default StoreSettings;