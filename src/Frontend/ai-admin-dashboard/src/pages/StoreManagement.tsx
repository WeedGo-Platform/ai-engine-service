import React, { useState, useEffect } from 'react';
import axios from 'axios';
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
import { getApiEndpoint } from '../config/app.config';
import { useAuth } from '../contexts/AuthContext';
import { useStoreContext } from '../contexts/StoreContext';
import AddressAutocomplete, { AddressComponents } from '../components/AddressAutocomplete';
import DeliveryZoneMapEditor, { DeliveryZoneGeoJSON, ZoneStatistics } from '../components/DeliveryZoneMapEditor';

// Province interface
interface Province {
  id?: string;
  code: string;
  name: string;
  type?: string;
  tax_rate?: number;
  cannabis_tax_rate?: number;
  min_age?: number;
  regulatory_body?: string;
  delivery_allowed?: boolean;
  pickup_allowed?: boolean;
}

const StoreManagement: React.FC = () => {
  const { tenantCode } = useParams<{ tenantCode: string }>();
  const navigate = useNavigate();
  const { user, isSuperAdmin, isTenantAdmin, isStoreManager } = useAuth();
  const { currentStore } = useStoreContext();
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [stores, setStores] = useState<Store[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingStore, setEditingStore] = useState<Store | null>(null);
  const [canAddStore, setCanAddStore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [modalError, setModalError] = useState<string | null>(null);
  const [isStoreManagerView, setIsStoreManagerView] = useState(false);

  useEffect(() => {
    // Check if user is store manager only (not tenant admin or super admin)
    const isStoreManagerOnly = !isSuperAdmin() && !isTenantAdmin() && isStoreManager();
    setIsStoreManagerView(isStoreManagerOnly);
  }, [isSuperAdmin, isTenantAdmin, isStoreManager]);

  useEffect(() => {
    if (tenantCode) {
      loadTenantAndStores();
    }
  }, [tenantCode]);

  // Helper function to check if user can edit a specific store
  const canEditStore = (storeId: string) => {
    // Super admins and tenant admins can edit all stores
    if (isSuperAdmin() || isTenantAdmin()) {
      return true;
    }
    // Store managers can only edit their own store
    if (isStoreManager() && currentStore?.id === storeId) {
      return true;
    }
    return false;
  };

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
      // Store managers cannot add new stores
      setCanAddStore(isStoreManagerView ? false : canAdd.can_add_store);
    } catch (err) {
      setError('Failed to load tenant and stores');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateStore = async (data: CreateStoreRequest) => {
    try {
      setModalError(null);
      await tenantService.createStore(data);
      setShowCreateModal(false);
      loadTenantAndStores();
    } catch (err: any) {
      // Extract error details from the server response
      let errorMessage = 'Failed to create store';

      if (err.response?.data) {
        // Handle validation errors (422)
        if (err.response.data.detail) {
          if (typeof err.response.data.detail === 'string') {
            errorMessage = err.response.data.detail;
          } else if (Array.isArray(err.response.data.detail)) {
            // Handle validation error array with better formatting
            errorMessage = err.response.data.detail
              .map((e: any) => {
                // Extract field name from location path
                const field = e.loc?.length > 1 ? e.loc[e.loc.length - 1] : 'field';
                const fieldName = field.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase());

                // Build user-friendly message
                if (e.type === 'string_too_long' && e.ctx?.max_length) {
                  return `${fieldName}: Must be ${e.ctx.max_length} characters or less (you entered ${e.input?.length || 0} characters)`;
                } else if (e.type === 'string_too_short' && e.ctx?.min_length) {
                  return `${fieldName}: Must be at least ${e.ctx.min_length} characters`;
                } else if (e.type === 'missing') {
                  return `${fieldName}: This field is required`;
                } else if (e.type === 'value_error') {
                  return `${fieldName}: ${e.msg}`;
                } else {
                  // Fallback to original message but include field name
                  return `${fieldName}: ${e.msg || e.message || 'Invalid value'}`;
                }
              })
              .join('\n');
          }
        } else if (err.response.data.message) {
          errorMessage = err.response.data.message;
        } else if (err.response.data.error) {
          errorMessage = err.response.data.error;
        }
      } else if (err.message) {
        errorMessage = err.message;
      }

      setModalError(errorMessage);
      console.error('Store creation error:', err);
    }
  };

  const handleUpdateStore = async (id: string, data: Partial<CreateStoreRequest>) => {
    try {
      setModalError(null);
      await tenantService.updateStore(id, data);
      setEditingStore(null);
      loadTenantAndStores();
    } catch (err: any) {
      // Extract error details from the server response
      let errorMessage = 'Failed to update store';

      if (err.response?.data) {
        if (err.response.data.detail) {
          if (typeof err.response.data.detail === 'string') {
            errorMessage = err.response.data.detail;
          } else if (Array.isArray(err.response.data.detail)) {
            // Handle validation error array with better formatting
            errorMessage = err.response.data.detail
              .map((e: any) => {
                // Extract field name from location path
                const field = e.loc?.length > 1 ? e.loc[e.loc.length - 1] : 'field';
                const fieldName = field.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase());

                // Build user-friendly message
                if (e.type === 'string_too_long' && e.ctx?.max_length) {
                  return `${fieldName}: Must be ${e.ctx.max_length} characters or less (you entered ${e.input?.length || 0} characters)`;
                } else if (e.type === 'string_too_short' && e.ctx?.min_length) {
                  return `${fieldName}: Must be at least ${e.ctx.min_length} characters`;
                } else if (e.type === 'missing') {
                  return `${fieldName}: This field is required`;
                } else if (e.type === 'value_error') {
                  return `${fieldName}: ${e.msg}`;
                } else {
                  // Fallback to original message but include field name
                  return `${fieldName}: ${e.msg || e.message || 'Invalid value'}`;
                }
              })
              .join('\n');
          }
        } else if (err.response.data.message) {
          errorMessage = err.response.data.message;
        } else if (err.response.data.error) {
          errorMessage = err.response.data.error;
        }
      } else if (err.message) {
        errorMessage = err.message;
      }

      setModalError(errorMessage);
      console.error('Store update error:', err);
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
        return <CheckCircle className="w-5 h-5 text-primary-500" />;
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
      <CheckCircle className="w-4 h-4 text-primary-500" />
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
            className="flex items-center gap-2 px-4 py-2 bg-accent-600 text-white rounded-lg hover:bg-accent-700 transition-colors"
          >
            <Plus className="w-5 h-5" />
            New Store
          </button>
        )}
      </div>

      {/* Tenant Info Card */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg ">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
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
        <div className="bg-danger-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-danger-600 dark:text-red-400" />
          <span className="text-red-700 dark:text-red-300">{error}</span>
        </div>
      )}

      {/* Stores Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {stores.length === 0 ? (
          <div className="col-span-2 bg-white dark:bg-gray-800 p-12 rounded-lg  text-center">
            <StoreIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500 dark:text-gray-400">No stores created yet</p>
            {canAddStore && (
              <button
                onClick={() => setShowCreateModal(true)}
                className="mt-4 px-4 py-2 bg-accent-600 text-white rounded-lg hover:bg-accent-700"
              >
                Create First Store
              </button>
            )}
          </div>
        ) : (
          stores.map((store) => (
            <div key={store.id} className="bg-white dark:bg-gray-800 rounded-lg  overflow-hidden">
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
                  {canEditStore(store.id) && (
                    <>
                      <button
                        onClick={() => navigate(`/dashboard/stores/${store.store_code}/settings`)}
                        className="px-3 py-1.5 text-sm text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded-lg flex items-center gap-1"
                      >
                        <Settings className="w-4 h-4" />
                        Settings
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
                        className="px-3 py-1.5 text-sm text-accent-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg"
                      >
                        Edit
                      </button>
                    </>
                  )}
                  {/* Only admins can suspend/reactivate/close stores */}
                  {!isStoreManagerView && (
                    <>
                      {store.status === 'active' ? (
                        <button
                          onClick={() => handleSuspendStore(store.id)}
                          className="px-3 py-1.5 text-sm text-warning-600 dark:text-yellow-400 hover:bg-warning-50 dark:hover:bg-yellow-900/20 rounded-lg"
                        >
                          Suspend
                        </button>
                      ) : store.status === 'suspended' ? (
                        <button
                          onClick={() => handleReactivateStore(store.id)}
                          className="px-3 py-1.5 text-sm text-primary-600 dark:text-green-400 hover:bg-primary-50 dark:hover:bg-green-900/20 rounded-lg"
                        >
                          Reactivate
                        </button>
                      ) : null}
                      {store.status !== 'inactive' && (
                        <button
                          onClick={() => handleCloseStore(store.id)}
                          className="px-3 py-1.5 text-sm text-danger-600 dark:text-red-400 hover:bg-danger-50 dark:hover:bg-red-900/20 rounded-lg"
                        >
                          Close
                        </button>
                      )}
                    </>
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
          error={modalError}
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
            setModalError(null);
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
  error?: string | null;
  onSave: (data: Partial<CreateStoreRequest>) => void;
  onClose: () => void;
}> = ({ tenantId, store, error, onSave, onClose }) => {
  const [provinces, setProvinces] = useState<Province[]>([]);
  const [loadingProvinces, setLoadingProvinces] = useState(true);

  const [formData, setFormData] = useState<Partial<CreateStoreRequest>>({
    tenant_id: tenantId,
    province_code: store?.address?.province || 'ON',
    // store_code is now auto-generated on the backend
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

  // State for coordinates from address autocomplete
  const [coordinates, setCoordinates] = useState<{
    latitude: number | null;
    longitude: number | null;
  }>({
    latitude: store?.location?.latitude || null,
    longitude: store?.location?.longitude || null,
  });

  // State for delivery zone (GeoJSON polygon)
  const [deliveryZone, setDeliveryZone] = useState<DeliveryZoneGeoJSON | null>(
    (store as any)?.delivery_zone || null
  );
  const [zoneStats, setZoneStats] = useState<ZoneStatistics | null>(null);

  // Fetch provinces from API
  useEffect(() => {
    const fetchProvinces = async () => {
      try {
        const response = await axios.get(getApiEndpoint('/stores/provinces'));
        setProvinces(response.data);
      } catch (error) {
        console.error('Failed to fetch provinces:', error);
        // Fallback to a minimal set if API fails
        setProvinces([
          { code: 'ON', name: 'Ontario' },
          { code: 'BC', name: 'British Columbia' },
          { code: 'AB', name: 'Alberta' },
          { code: 'QC', name: 'Quebec' },
        ]);
      } finally {
        setLoadingProvinces(false);
      }
    };

    fetchProvinces();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Validate province_code format
    if (!formData.province_code || !/^[A-Z]{2}$/.test(formData.province_code)) {
      alert('Please select a valid province');
      return;
    }

    // Ensure all required fields are present
    if (!formData.name || !formData.address?.street || !formData.address?.city || !formData.address?.postal_code) {
      alert('Please fill in all required fields');
      return;
    }

    // Include coordinates and delivery zone in submission if available
    const submitData = {
      ...formData,
      location: coordinates.latitude && coordinates.longitude ? {
        latitude: coordinates.latitude,
        longitude: coordinates.longitude
      } : undefined,
      delivery_zone: deliveryZone,
      delivery_zone_stats: zoneStats
    };

    onSave(submitData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">
          {store ? 'Edit Store' : 'Create New Store'}
        </h2>

        {/* Error message display */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <div className="flex items-start">
              <svg className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <div>
                <p className="text-sm font-medium text-red-800 dark:text-red-200">
                  {store ? 'Failed to update store' : 'Failed to create store'}
                </p>
                <div className="text-sm text-red-600 dark:text-red-400 mt-1">
                  {error.split('\n').map((line, index) => (
                    <p key={index} className={index > 0 ? 'mt-1' : ''}>
                      {line}
                    </p>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Store Name *
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder="Enter store name (e.g., London Haze East York)"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              A unique store code will be automatically generated based on the store name and location
            </p>
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
              className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              disabled={loadingProvinces}
            >
              {loadingProvinces ? (
                <option value="">Loading provinces...</option>
              ) : (
                provinces.map(p => (
                  <option key={p.code} value={p.code}>{p.name}</option>
                ))
              )}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Street Address *
            </label>
            <AddressAutocomplete
              value={formData.address?.street || ''}
              onChange={(addressComponents: AddressComponents) => {
                // Update all address fields at once from autocomplete
                setFormData({
                  ...formData,
                  address: {
                    street: addressComponents.street,
                    city: addressComponents.city,
                    province: addressComponents.province,
                    postal_code: addressComponents.postal_code,
                    country: 'Canada'
                  },
                  // Also update province_code to match
                  province_code: addressComponents.province
                });
              }}
              onCoordinatesChange={(coords) => {
                setCoordinates(coords);
              }}
              placeholder="Start typing an address (e.g., 123 Main St, Toronto)"
              required
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              💡 Start typing to see address suggestions - city and postal code will auto-fill
            </p>
          </div>

          <div className="grid grid-cols-3 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                City *
              </label>
              <input
                type="text"
                required
                readOnly
                value={formData.address?.city}
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-700 dark:text-white cursor-not-allowed"
                placeholder="Auto-filled from address"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Auto-filled
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Postal Code *
              </label>
              <input
                type="text"
                required
                readOnly
                value={formData.address?.postal_code}
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-700 dark:text-white cursor-not-allowed"
                placeholder="Auto-filled from address"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Auto-filled
              </p>
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
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Phone
              </label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
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
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                License Number
              </label>
              <input
                type="text"
                value={formData.license_number}
                onChange={(e) => setFormData({ ...formData, license_number: e.target.value })}
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
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
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Store Features
            </label>
            <div className="grid grid-cols-2 gap-4">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.delivery_enabled}
                  onChange={(e) => setFormData({ ...formData, delivery_enabled: e.target.checked })}
                  className="rounded text-accent-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">Delivery Enabled</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.pickup_enabled}
                  onChange={(e) => setFormData({ ...formData, pickup_enabled: e.target.checked })}
                  className="rounded text-accent-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">Pickup Enabled</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.pos_enabled}
                  onChange={(e) => setFormData({ ...formData, pos_enabled: e.target.checked })}
                  className="rounded text-accent-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">POS System</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.ecommerce_enabled}
                  onChange={(e) => setFormData({ ...formData, ecommerce_enabled: e.target.checked })}
                  className="rounded text-accent-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">E-commerce</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.kiosk_enabled}
                  onChange={(e) => setFormData({ ...formData, kiosk_enabled: e.target.checked })}
                  className="rounded text-accent-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">In-Store Kiosk</span>
              </label>
            </div>
          </div>

          {/* Delivery Zone Configuration - Only show if coordinates are available */}
          {coordinates.latitude && coordinates.longitude && (
            <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Delivery Zone (Optional)
                </label>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
                  🗺️ Draw a custom delivery zone polygon on the map. The zone must contain the store location.
                  This provides more precise delivery boundaries than a simple radius.
                </p>
              </div>
              <DeliveryZoneMapEditor
                storeCoordinates={{
                  latitude: coordinates.latitude,
                  longitude: coordinates.longitude
                }}
                initialZone={deliveryZone}
                onChange={(zone) => setDeliveryZone(zone)}
                onStatsChange={(stats) => setZoneStats(stats)}
                className="h-72"
              />
              {zoneStats && (
                <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <p className="text-sm text-blue-800 dark:text-blue-200 font-medium mb-1">
                    Zone Statistics:
                  </p>
                  <div className="grid grid-cols-3 gap-4 text-xs text-blue-700 dark:text-blue-300">
                    <div>
                      <span className="font-semibold">Area:</span> {zoneStats.area_km2.toFixed(2)} km²
                    </div>
                    <div>
                      <span className="font-semibold">Perimeter:</span> {zoneStats.perimeter_km.toFixed(2)} km
                    </div>
                    <div>
                      <span className="font-semibold">Approx. Radius:</span> {zoneStats.approximate_radius_km.toFixed(2)} km
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="flex justify-end gap-4 mt-8 pt-4 border-t border-gray-200 dark:border-gray-700 sticky bottom-0 bg-white dark:bg-gray-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-accent-600 text-white rounded-lg hover:bg-accent-700"
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