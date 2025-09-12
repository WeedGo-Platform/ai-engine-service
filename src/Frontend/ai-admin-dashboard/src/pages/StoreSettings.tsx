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
import paymentService, { POSTerminalSettings } from '../services/paymentService';
import POSTerminalSettingsComponent from '../components/POSTerminalSettings';

const StoreSettings: React.FC = () => {
  const { storeCode } = useParams<{ storeCode: string }>();
  const navigate = useNavigate();
  const [store, setStore] = useState<Store | null>(null);
  const [posSettings, setPosSettings] = useState<POSTerminalSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'general' | 'pos' | 'hours'>('general');

  useEffect(() => {
    if (storeCode) {
      loadStoreData();
    }
  }, [storeCode]);

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
      const storeData = await storeService.getStoreByCode(storeCode!);
      const posData = await paymentService.getStorePOSSettings(storeData.id);
      setStore(storeData);
      setPosSettings(posData);
    } catch (err) {
      setError('Failed to load store settings');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSavePOSSettings = async (settings: POSTerminalSettings) => {
    try {
      await paymentService.updateStorePOSSettings(store!.id, settings);
      setPosSettings(settings);
      setSuccess('POS settings updated successfully');
    } catch (err) {
      setError('Failed to update POS settings');
      throw err;
    }
  };

  const handlePingTerminal = async (terminalId: string) => {
    try {
      const result = await paymentService.pingPOSTerminal(store!.id, terminalId);
      if (result.status === 'online') {
        setSuccess(`Terminal ${terminalId} is online (${result.response_time_ms}ms)`);
      } else {
        setError(`Terminal ${terminalId} is offline`);
      }
    } catch (err) {
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
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!store) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700">Store not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
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
          className="mb-4 flex items-center gap-2 text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Stores
        </button>
        
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <StoreIcon className="w-8 h-8" />
              {store.name} Settings
            </h1>
            <p className="text-gray-600 mt-1">Manage store configuration and POS settings</p>
          </div>
        </div>
      </div>

      {/* Alerts */}
      {success && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-green-500" />
          <span className="text-green-700">{success}</span>
        </div>
      )}

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <span className="text-red-700">{error}</span>
        </div>
      )}

      {/* Tabs */}
      <div className="mb-6 border-b">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('general')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'general'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            General Settings
          </button>
          <button
            onClick={() => setActiveTab('pos')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'pos'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            POS & Terminals
          </button>
          <button
            onClick={() => setActiveTab('hours')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'hours'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Store Hours
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'general' && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4">General Information</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Store Name
              </label>
              <p className="text-lg">{store.name}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Store Code
              </label>
              <p className="text-lg font-mono">{store.store_code}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <Phone className="inline w-4 h-4 mr-1" />
                Phone
              </label>
              <p className="text-lg">{store.phone || 'Not specified'}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <Mail className="inline w-4 h-4 mr-1" />
                Email
              </label>
              <p className="text-lg">{store.email || 'Not specified'}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                License Number
              </label>
              <p className="text-lg">{store.license_number || 'Not specified'}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                License Expiry
              </label>
              <p className="text-lg">
                {store.license_expiry 
                  ? new Date(store.license_expiry).toLocaleDateString()
                  : 'Not specified'}
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tax Rate
              </label>
              <p className="text-lg">{store.tax_rate}%</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Timezone
              </label>
              <p className="text-lg">{store.timezone}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <span className={`inline-flex px-2 py-1 rounded-full text-sm font-medium ${
                store.status === 'active' 
                  ? 'bg-green-100 text-green-700'
                  : 'bg-gray-100 text-gray-700'
              }`}>
                {store.status}
              </span>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Delivery Radius
              </label>
              <p className="text-lg">{store.delivery_radius_km} km</p>
            </div>
          </div>
          
          {store.address && (
            <div className="mt-6">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <MapPin className="inline w-4 h-4 mr-1" />
                Address
              </label>
              <p className="text-lg">
                {store.address.street}<br />
                {store.address.city}, {store.address.province} {store.address.postal_code}<br />
                {store.address.country}
              </p>
            </div>
          )}
          
          <div className="mt-6">
            <h3 className="text-lg font-semibold mb-3">Service Options</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={store.delivery_enabled}
                  disabled
                  className="w-4 h-4 text-blue-600 rounded"
                />
                <span className="text-sm">Delivery Enabled</span>
              </label>
              
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={store.pickup_enabled}
                  disabled
                  className="w-4 h-4 text-blue-600 rounded"
                />
                <span className="text-sm">Pickup Enabled</span>
              </label>
              
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={store.kiosk_enabled}
                  disabled
                  className="w-4 h-4 text-blue-600 rounded"
                />
                <span className="text-sm">Kiosk Enabled</span>
              </label>
              
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={store.pos_enabled}
                  disabled
                  className="w-4 h-4 text-blue-600 rounded"
                />
                <span className="text-sm">POS Enabled</span>
              </label>
              
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={store.ecommerce_enabled}
                  disabled
                  className="w-4 h-4 text-blue-600 rounded"
                />
                <span className="text-sm">E-commerce Enabled</span>
              </label>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'pos' && posSettings && (
        <POSTerminalSettingsComponent
          storeId={store?.id || ''}
          settings={posSettings}
          onSave={handleSavePOSSettings}
          onPingTerminal={handlePingTerminal}
        />
      )}

      {activeTab === 'hours' && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5" />
            Store Hours
          </h2>
          
          <div className="space-y-3">
            {['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].map(day => {
              const dayHours = store.hours?.[day];
              const dayCapitalized = day.charAt(0).toUpperCase() + day.slice(1);
              
              return (
                <div key={day} className="flex items-center justify-between py-2 border-b">
                  <span className="font-medium">{dayCapitalized}</span>
                  <span className="text-gray-600">
                    {!dayHours || dayHours.closed 
                      ? 'Closed' 
                      : `${dayHours.open} - ${dayHours.close}`}
                  </span>
                </div>
              );
            })}
          </div>
          
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-700">
              To modify store hours, please use the Store Hours Management page or contact support.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default StoreSettings;