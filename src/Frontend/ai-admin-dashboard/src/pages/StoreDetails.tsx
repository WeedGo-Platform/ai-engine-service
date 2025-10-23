import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  ArrowLeft,
  Store as StoreIcon,
  MapPin,
  Phone,
  Mail,
  Clock,
  Shield,
  Settings,
  BarChart3,
} from 'lucide-react';
import tenantService, { Store } from '../services/tenantService';
import OCSComplianceTab from '../components/OCSComplianceTab';

const StoreDetails: React.FC = () => {
  const { storeId } = useParams<{ storeId: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation(['stores', 'common']);

  const [store, setStore] = useState<Store | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'details' | 'compliance' | 'settings'>('details');

  useEffect(() => {
    if (storeId) {
      loadStore();
    }
  }, [storeId]);

  const loadStore = async () => {
    if (!storeId) return;

    try {
      setLoading(true);
      // Note: You'll need to add a getStoreById method to tenantService
      // For now, we'll use a workaround
      const response = await fetch(`/api/stores/${storeId}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('authToken')}`,
        },
      });
      const data = await response.json();
      setStore(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load store');
      console.error('Failed to load store:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500 dark:text-gray-400">Loading...</div>
      </div>
    );
  }

  if (error || !store) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-500 dark:text-red-400">{error || 'Store not found'}</div>
      </div>
    );
  }

  const tabs = [
    { id: 'details', label: 'Details', icon: StoreIcon },
    { id: 'compliance', label: 'OCS Compliance', icon: Shield },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start gap-3">
        <div>
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white mb-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">
            {store.name}
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Store Code: {store.store_code}
          </p>
        </div>
      </div>

      {/* Store Summary Card */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {store.address && (
            <div className="flex items-start gap-3">
              <MapPin className="w-5 h-5 text-gray-400 mt-1" />
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Address</p>
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {store.address.city}, {store.address.province}
                </p>
              </div>
            </div>
          )}
          {store.phone && (
            <div className="flex items-start gap-3">
              <Phone className="w-5 h-5 text-gray-400 mt-1" />
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Phone</p>
                <p className="text-sm font-medium text-gray-900 dark:text-white">{store.phone}</p>
              </div>
            </div>
          )}
          {store.email && (
            <div className="flex items-start gap-3">
              <Mail className="w-5 h-5 text-gray-400 mt-1" />
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Email</p>
                <p className="text-sm font-medium text-gray-900 dark:text-white">{store.email}</p>
              </div>
            </div>
          )}
          <div className="flex items-start gap-3">
            <Clock className="w-5 h-5 text-gray-400 mt-1" />
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Status</p>
              <p className="text-sm font-medium text-gray-900 dark:text-white capitalize">
                {store.status}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <div className="border-b border-gray-200 dark:border-gray-700">
          <nav className="flex -mb-px">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'details' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Store Information
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Store Name</p>
                  <p className="text-base font-medium text-gray-900 dark:text-white">
                    {store.name}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Store Code</p>
                  <p className="text-base font-medium text-gray-900 dark:text-white">
                    {store.store_code}
                  </p>
                </div>
                {store.license_number && (
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">License Number</p>
                    <p className="text-base font-medium text-gray-900 dark:text-white">
                      {store.license_number}
                    </p>
                  </div>
                )}
                {store.timezone && (
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Timezone</p>
                    <p className="text-base font-medium text-gray-900 dark:text-white">
                      {store.timezone}
                    </p>
                  </div>
                )}
              </div>

              <div className="mt-6">
                <h4 className="text-base font-semibold text-gray-900 dark:text-white mb-3">
                  Enabled Features
                </h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {[
                    { key: 'delivery_enabled', label: 'Delivery' },
                    { key: 'pickup_enabled', label: 'Pickup' },
                    { key: 'pos_enabled', label: 'POS' },
                    { key: 'ecommerce_enabled', label: 'E-commerce' },
                    { key: 'kiosk_enabled', label: 'Kiosk' },
                  ].map((feature) => (
                    <div
                      key={feature.key}
                      className={`px-3 py-2 rounded-lg text-sm ${
                        (store as any)[feature.key]
                          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                          : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                      }`}
                    >
                      {feature.label}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'compliance' && (
            <OCSComplianceTab
              storeId={store.id}
              tenantId={store.tenant_id}
              currentConfig={{
                ocs_key: (store as any).ocs_key,
                license_number: store.license_number,
              }}
              onConfigUpdate={loadStore}
            />
          )}

          {activeTab === 'settings' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Store Settings
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Store settings management coming soon...
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StoreDetails;
