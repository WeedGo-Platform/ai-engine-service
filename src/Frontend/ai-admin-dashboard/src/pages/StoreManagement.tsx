import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Store as StoreIcon,
  Plus,
  Edit,
  MapPin,
  Clock,
  Phone,
  Mail,
  Calendar,
  CheckCircle,
  XCircle,
  AlertCircle,
  Package,
  Truck,
  ShoppingBag,
  Monitor,
  Globe,
  Shield,
  Pause,
  Play,
  Lock,
  ArrowLeft,
  Settings
} from 'lucide-react';
import tenantService, { Store, Tenant, CreateStoreRequest } from '../services/tenantService';

const PROVINCES = [
  { code: 'ON', name: 'Ontario' },
  { code: 'BC', name: 'British Columbia' },
  { code: 'AB', name: 'Alberta' },
  { code: 'QC', name: 'Quebec' },
  { code: 'SK', name: 'Saskatchewan' },
  { code: 'MB', name: 'Manitoba' },
  { code: 'NS', name: 'Nova Scotia' },
  { code: 'NB', name: 'New Brunswick' },
  { code: 'NL', name: 'Newfoundland and Labrador' },
  { code: 'PE', name: 'Prince Edward Island' },
  { code: 'NT', name: 'Northwest Territories' },
  { code: 'YT', name: 'Yukon' },
  { code: 'NU', name: 'Nunavut' },
];

const StoreManagement: React.FC = () => {
  const { tenantCode } = useParams<{ tenantCode: string }>();
  const navigate = useNavigate();
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [stores, setStores] = useState<Store[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingStore, setEditingStore] = useState<Store | null>(null);
  const [canAddStore, setCanAddStore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (tenantCode) {
      loadTenantAndStores();
    }
  }, [tenantCode]);

  const loadTenantAndStores = async () => {
    if (!tenantCode) return;
    
    try {
      setLoading(true);
      const tenantData = await tenantService.getTenantByCode(tenantCode);
      const [storesData, canAdd] = await Promise.all([
        tenantService.getStores(tenantData.id),
        tenantService.canAddStore(tenantData.id)
      ]);
      
      setTenant(tenantData);
      setStores(storesData);
      setCanAddStore(canAdd.can_add_store);
    } catch (err) {
      setError('Failed to load tenant and stores');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateStore = async (data: CreateStoreRequest) => {
    try {
      await tenantService.createStore(data);
      setShowCreateModal(false);
      loadTenantAndStores();
    } catch (err) {
      setError('Failed to create store');
      console.error(err);
    }
  };

  const handleUpdateStore = async (id: string, data: Partial<CreateStoreRequest>) => {
    try {
      await tenantService.updateStore(id, data);
      setEditingStore(null);
      loadTenantAndStores();
    } catch (err) {
      setError('Failed to update store');
      console.error(err);
    }
  };

  const handleSuspendStore = async (id: string) => {
    if (window.confirm('Are you sure you want to suspend this store?')) {
      try {
        await tenantService.suspendStore(id, 'Admin action');
        loadTenantAndStores();
      } catch (err) {
        setError('Failed to suspend store');
        console.error(err);
      }
    }
  };

  const handleReactivateStore = async (id: string) => {
    try {
      await tenantService.reactivateStore(id);
      loadTenantAndStores();
    } catch (err) {
      setError('Failed to reactivate store');
      console.error(err);
    }
  };

  const handleCloseStore = async (id: string) => {
    if (window.confirm('Are you sure you want to permanently close this store?')) {
      try {
        await tenantService.closeStore(id);
        loadTenantAndStores();
      } catch (err) {
        setError('Failed to close store');
        console.error(err);
      }
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'suspended':
        return <Pause className="w-5 h-5 text-yellow-500" />;
      case 'inactive':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <AlertCircle className="w-5 h-5 text-gray-500" />;
    }
  };

  const getFeatureIcon = (enabled: boolean) => {
    return enabled ? (
      <CheckCircle className="w-4 h-4 text-green-500" />
    ) : (
      <XCircle className="w-4 h-4 text-gray-400" />
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500 dark:text-gray-400">Loading...</div>
      </div>
    );
  }

  if (!tenant) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500 dark:text-gray-400">Tenant not found</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <button
            onClick={() => navigate('/dashboard/tenants')}
            className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white mb-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Tenants
          </button>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Store Management
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            {tenant.name} - {tenant.code}
          </p>
        </div>
        {canAddStore && (
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-5 h-5" />
            New Store
          </button>
        )}
      </div>

      {/* Tenant Info Card */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Subscription</p>
            <p className="text-lg font-semibold text-gray-900 dark:text-white capitalize">
              {tenant.subscription_tier.replace('_', ' ')}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Store Limit</p>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">
              {stores.length} / {tenant.max_stores}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Status</p>
            <p className="text-lg font-semibold text-gray-900 dark:text-white capitalize">
              {tenant.status}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Contact</p>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">
              {tenant.contact_email}
            </p>
          </div>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
          <span className="text-red-700 dark:text-red-300">{error}</span>
        </div>
      )}

      {/* Stores Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {stores.length === 0 ? (
          <div className="col-span-2 bg-white dark:bg-gray-800 p-12 rounded-lg shadow-sm text-center">
            <StoreIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500 dark:text-gray-400">No stores created yet</p>
            {canAddStore && (
              <button
                onClick={() => setShowCreateModal(true)}
                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Create First Store
              </button>
            )}
          </div>
        ) : (
          stores.map((store) => (
            <div key={store.id} className="bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden">
              <div className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                      {store.name}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Code: {store.store_code}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(store.status)}
                    <span className="text-sm capitalize">{store.status}</span>
                  </div>
                </div>

                {/* Store Details */}
                <div className="space-y-3 mb-4">
                  {store.address && (
                    <div className="flex items-start gap-2">
                      <MapPin className="w-4 h-4 text-gray-400 mt-0.5" />
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        <div>{store.address.street}</div>
                        <div>{store.address.city}, {store.address.province} {store.address.postal_code}</div>
                      </div>
                    </div>
                  )}

                  {store.phone && (
                    <div className="flex items-center gap-2">
                      <Phone className="w-4 h-4 text-gray-400" />
                      <span className="text-sm text-gray-600 dark:text-gray-400">{store.phone}</span>
                    </div>
                  )}

                  {store.email && (
                    <div className="flex items-center gap-2">
                      <Mail className="w-4 h-4 text-gray-400" />
                      <span className="text-sm text-gray-600 dark:text-gray-400">{store.email}</span>
                    </div>
                  )}

                  {store.license_number && (
                    <div className="flex items-center gap-2">
                      <Shield className="w-4 h-4 text-gray-400" />
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        License: {store.license_number}
                        {store.license_expiry && ` (Expires: ${store.license_expiry})`}
                      </span>
                    </div>
                  )}
                </div>

                {/* Features */}
                <div className="grid grid-cols-2 gap-2 mb-4 pb-4 border-b border-gray-200 dark:border-gray-700">
                  <div className="flex items-center gap-2">
                    {getFeatureIcon(store.delivery_enabled)}
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      Delivery ({store.delivery_radius_km}km)
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    {getFeatureIcon(store.pickup_enabled)}
                    <span className="text-sm text-gray-600 dark:text-gray-400">Pickup</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {getFeatureIcon(store.pos_enabled)}
                    <span className="text-sm text-gray-600 dark:text-gray-400">POS</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {getFeatureIcon(store.ecommerce_enabled)}
                    <span className="text-sm text-gray-600 dark:text-gray-400">E-commerce</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {getFeatureIcon(store.kiosk_enabled)}
                    <span className="text-sm text-gray-600 dark:text-gray-400">Kiosk</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      Tax: {store.tax_rate}%
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex justify-end gap-2">
                  <button
                    onClick={() => navigate(`/dashboard/stores/${store.store_code}/settings`)}
                    className="px-3 py-1.5 text-sm text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded-lg flex items-center gap-1"
                  >
                    <Settings className="w-4 h-4" />
                    POS Settings
                  </button>
                  <button
                    onClick={() => navigate(`/dashboard/stores/${store.store_code}/hours`)}
                    className="px-3 py-1.5 text-sm text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded-lg flex items-center gap-1"
                  >
                    <Clock className="w-4 h-4" />
                    Hours
                  </button>
                  <button
                    onClick={() => setEditingStore(store)}
                    className="px-3 py-1.5 text-sm text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg"
                  >
                    Edit
                  </button>
                  {store.status === 'active' ? (
                    <button
                      onClick={() => handleSuspendStore(store.id)}
                      className="px-3 py-1.5 text-sm text-yellow-600 dark:text-yellow-400 hover:bg-yellow-50 dark:hover:bg-yellow-900/20 rounded-lg"
                    >
                      Suspend
                    </button>
                  ) : store.status === 'suspended' ? (
                    <button
                      onClick={() => handleReactivateStore(store.id)}
                      className="px-3 py-1.5 text-sm text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg"
                    >
                      Reactivate
                    </button>
                  ) : null}
                  {store.status !== 'inactive' && (
                    <button
                      onClick={() => handleCloseStore(store.id)}
                      className="px-3 py-1.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"
                    >
                      Close
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Create/Edit Modal */}
      {(showCreateModal || editingStore) && tenant && (
        <StoreFormModal
          tenantId={tenant.id}
          store={editingStore}
          onSave={(data) => {
            if (editingStore) {
              handleUpdateStore(editingStore.id, data);
            } else {
              handleCreateStore(data as CreateStoreRequest);
            }
          }}
          onClose={() => {
            setShowCreateModal(false);
            setEditingStore(null);
          }}
        />
      )}
    </div>
  );
};

// Store Form Modal Component
const StoreFormModal: React.FC<{
  tenantId: string;
  store?: Store | null;
  onSave: (data: Partial<CreateStoreRequest>) => void;
  onClose: () => void;
}> = ({ tenantId, store, onSave, onClose }) => {
  const [formData, setFormData] = useState<Partial<CreateStoreRequest>>({
    tenant_id: tenantId,
    province_code: store?.address?.province || 'ON',
    store_code: store?.store_code || '',
    name: store?.name || '',
    address: store?.address || {
      street: '',
      city: '',
      province: 'ON',
      postal_code: '',
      country: 'Canada',
    },
    phone: store?.phone || '',
    email: store?.email || '',
    license_number: store?.license_number || '',
    license_expiry: store?.license_expiry || '',
    delivery_radius_km: store?.delivery_radius_km || 10,
    delivery_enabled: store?.delivery_enabled ?? true,
    pickup_enabled: store?.pickup_enabled ?? true,
    kiosk_enabled: store?.kiosk_enabled ?? false,
    pos_enabled: store?.pos_enabled ?? true,
    ecommerce_enabled: store?.ecommerce_enabled ?? true,
    timezone: store?.timezone || 'America/Toronto',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">
          {store ? 'Edit Store' : 'Create New Store'}
        </h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Store Name *
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Store Code *
              </label>
              <input
                type="text"
                required
                disabled={!!store}
                value={formData.store_code}
                onChange={(e) => setFormData({ ...formData, store_code: e.target.value.toUpperCase() })}
                pattern="^[A-Z0-9_\-]+$"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white disabled:opacity-50"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Province/Territory *
            </label>
            <select
              required
              value={formData.province_code}
              onChange={(e) => {
                const province = e.target.value;
                setFormData({
                  ...formData,
                  province_code: province,
                  address: { ...formData.address!, province }
                });
              }}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            >
              {PROVINCES.map(p => (
                <option key={p.code} value={p.code}>{p.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Street Address *
            </label>
            <input
              type="text"
              required
              value={formData.address?.street}
              onChange={(e) => setFormData({
                ...formData,
                address: { ...formData.address!, street: e.target.value }
              })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                City *
              </label>
              <input
                type="text"
                required
                value={formData.address?.city}
                onChange={(e) => setFormData({
                  ...formData,
                  address: { ...formData.address!, city: e.target.value }
                })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Postal Code *
              </label>
              <input
                type="text"
                required
                value={formData.address?.postal_code}
                onChange={(e) => setFormData({
                  ...formData,
                  address: { ...formData.address!, postal_code: e.target.value }
                })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Delivery Radius (km)
              </label>
              <input
                type="number"
                min="0"
                max="100"
                value={formData.delivery_radius_km}
                onChange={(e) => setFormData({ ...formData, delivery_radius_km: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Phone
              </label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Email
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                License Number
              </label>
              <input
                type="text"
                value={formData.license_number}
                onChange={(e) => setFormData({ ...formData, license_number: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                License Expiry
              </label>
              <input
                type="date"
                value={formData.license_expiry}
                onChange={(e) => setFormData({ ...formData, license_expiry: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Store Features
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.delivery_enabled}
                  onChange={(e) => setFormData({ ...formData, delivery_enabled: e.target.checked })}
                  className="rounded text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">Delivery Enabled</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.pickup_enabled}
                  onChange={(e) => setFormData({ ...formData, pickup_enabled: e.target.checked })}
                  className="rounded text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">Pickup Enabled</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.pos_enabled}
                  onChange={(e) => setFormData({ ...formData, pos_enabled: e.target.checked })}
                  className="rounded text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">POS System</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.ecommerce_enabled}
                  onChange={(e) => setFormData({ ...formData, ecommerce_enabled: e.target.checked })}
                  className="rounded text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">E-commerce</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.kiosk_enabled}
                  onChange={(e) => setFormData({ ...formData, kiosk_enabled: e.target.checked })}
                  className="rounded text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">In-Store Kiosk</span>
              </label>
            </div>
          </div>

          <div className="flex justify-end gap-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              {store ? 'Update' : 'Create'} Store
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default StoreManagement;