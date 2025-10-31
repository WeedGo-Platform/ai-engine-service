import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import toast from 'react-hot-toast';
import {
  Building2,
  Plus,
  Edit,
  CheckCircle,
  XCircle,
  AlertCircle,
  Search,
  DollarSign,
  Store,
  Users,
  TrendingUp,
  Pause,
  Play,
  Crown,
  Package,
  CreditCard,
  UserPlus,
  Ban,
  UserX,
  Shield,
  RefreshCw,
  X
} from 'lucide-react';
import tenantService, { Tenant, CreateTenantRequest } from '../services/tenantService';
import ocsService from '../services/ocsService';
import { getApiEndpoint } from '../config/app.config';
import { useAuth } from '../contexts/AuthContext';
import TenantEditModal from '../components/TenantEditModal';
import { useErrorHandler } from '../hooks/useErrorHandler';

const TenantManagement: React.FC = () => {
  const navigate = useNavigate();
  const { user, isSuperAdmin, isTenantAdmin, isStoreManager } = useAuth();
  const { t } = useTranslation(['tenants', 'errors', 'modals', 'common']);
  const { handleOperationError } = useErrorHandler();
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterTier, setFilterTier] = useState<string>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingTenant, setEditingTenant] = useState<Tenant | null>(null);
  const [showTenantModal, setShowTenantModal] = useState(false);
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null);
  const [isTenantAdminView, setIsTenantAdminView] = useState(false);
  const [isStoreManagerView, setIsStoreManagerView] = useState(false);
  const [tenantMetrics, setTenantMetrics] = useState<any>(null);
  const [storeCount, setStoreCount] = useState({ total: 0, active: 0 });
  const [showOCSCredentialsModal, setShowOCSCredentialsModal] = useState(false);

  useEffect(() => {
    // Check if user is tenant admin and not super admin
    const isTenantAdminOnly = !isSuperAdmin() && isTenantAdmin();
    const isStoreManagerOnly = !isSuperAdmin() && !isTenantAdmin() && isStoreManager();
    setIsTenantAdminView(isTenantAdminOnly);
    setIsStoreManagerView(isStoreManagerOnly);
    loadTenants();
    if (isTenantAdminOnly || isStoreManagerOnly) {
      loadTenantMetrics();
      // loadStoreCount will be called after tenant is loaded in loadTenants
    }
  }, [filterStatus, filterTier, isSuperAdmin, isTenantAdmin, isStoreManager]);

  const loadTenantMetrics = async () => {
    try {
      const currentTenantId = user?.tenants?.[0]?.id;
      if (currentTenantId) {
        const response = await fetch(getApiEndpoint(`/tenants/${currentTenantId}/metrics`));
        if (response.ok) {
          const metrics = await response.json();
          setTenantMetrics(metrics);
        }
      }
    } catch (err) {
      handleOperationError(err, 'load', 'tenant');
    }
  };

  const loadStoreCount = async (tenantId?: string) => {
    try {
      // Use provided tenantId or try to get from user context
      const idToUse = tenantId || user?.tenants?.[0]?.id;
      if (idToUse) {
        const stores = await tenantService.getStores(idToUse);
        const totalStores = stores.length;
        const activeStores = stores.filter(store => store.status === 'active').length;
        setStoreCount({ total: totalStores, active: activeStores });
      }
    } catch (err) {
      handleOperationError(err, 'load', 'store');
    }
  };

  const loadTenants = async () => {
    try {
      setLoading(true);

      // If tenant admin or store manager, only load their tenant
      if (isTenantAdminView || isStoreManagerView) {
        const currentTenantCode = user?.tenants?.[0]?.code;
        if (currentTenantCode) {
          try {
            const response = await fetch(getApiEndpoint(`/tenants/by-code/${currentTenantCode}`));
            if (response.ok) {
              const tenantData = await response.json();
              setTenants([tenantData]);
              // Load store count for this tenant
              loadStoreCount(tenantData.id);
            } else {
              toast.error(t('tenants:messages.organizationLoadFailed'));
            }
          } catch (err) {
            handleOperationError(err, 'load', 'tenant');
          }
        } else {
          toast.error(t('tenants:messages.noOrganization'));
        }
      } else {
        // Super admin can see all tenants
        const params: any = {};
        if (filterStatus !== 'all') params.status = filterStatus;
        if (filterTier !== 'all') params.subscription_tier = filterTier;

        const data = await tenantService.getTenants(params);
        setTenants(data);

        // Load store count for the first tenant if available
        if (data && data.length > 0) {
          loadStoreCount(data[0].id);
        }
      }
    } catch (err) {
      handleOperationError(err, 'load', 'tenant');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTenant = async (data: CreateTenantRequest) => {
    try {
      await tenantService.createTenant(data);
      setShowCreateModal(false);
      toast.success(t('tenants:messages.created'));
      loadTenants();
    } catch (err) {
      handleOperationError(err, 'create', 'tenant');
    }
  };

  const handleUpdateTenant = async (id: string, data: Partial<CreateTenantRequest>, logoFile?: File | null) => {
    try {
      // Remove the code field from update data as it cannot be changed
      const { code, ...updateData } = data;

      // Update tenant basic info first
      await tenantService.updateTenant(id, updateData);

      // Upload logo if provided
      if (logoFile) {
        const formData = new FormData();
        formData.append('file', logoFile);

        const response = await fetch(getApiEndpoint('/uploads/tenant/${id}/logo'), {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || t('tenants:messages.logoUploadFailed'));
        }

        toast.success(t('tenants:messages.logoUploaded'));
      }

      setEditingTenant(null);
      toast.success(t('tenants:messages.updated'));
      loadTenants();
    } catch (err) {
      handleOperationError(err, 'update', 'tenant');
    }
  };

  const handleSuspendTenant = async (id: string) => {
    if (window.confirm(t('tenants:confirmations.suspendMessage'))) {
      try {
        await tenantService.suspendTenant(id, 'Admin action');
        toast.success(t('tenants:messages.suspended'));
        loadTenants();
      } catch (err) {
        handleOperationError(err, 'update', 'tenant');
      }
    }
  };

  const handleReactivateTenant = async (id: string) => {
    try {
      await tenantService.reactivateTenant(id);
      toast.success(t('tenants:messages.reactivated'));
      loadTenants();
    } catch (err) {
      handleOperationError(err, 'update', 'tenant');
    }
  };

  // Removed unused handleUpgradeSubscription - can be added back when needed
  // Removed handleDeleteTenant - deleteTenant method doesn't exist on tenantService

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-5 h-5 text-primary-500" />;
      case 'suspended':
        return <Pause className="w-5 h-5 text-yellow-500" />;
      case 'cancelled':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <AlertCircle className="w-5 h-5 text-gray-500" />;
    }
  };

  const getTierIcon = (tier: string) => {
    switch (tier) {
      case 'enterprise':
        return <Crown className="w-5 h-5 text-purple-500" />;
      case 'small_business':
        return <TrendingUp className="w-5 h-5 text-accent-500" />;
      case 'basic':
        return <Package className="w-5 h-5 text-primary-500" />;
      default:
        return <Users className="w-5 h-5 text-gray-500" />;
    }
  };

  const getTierPrice = (tier: string) => {
    switch (tier) {
      case 'enterprise':
        return '$299+';
      case 'small_business':
        return '$149';
      case 'basic':
        return '$99';
      case 'community':
        return 'Free';
      default:
        return '-';
    }
  };

  const filteredTenants = tenants.filter(tenant =>
    tenant.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    tenant.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
    tenant.contact_email?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            {isTenantAdminView || isStoreManagerView ? t('tenants:titles.organizationManagement') : t('tenants:titles.management')}
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            {isStoreManagerView
              ? t('tenants:descriptions.viewOrganization')
              : isTenantAdminView
                ? t('tenants:descriptions.manageOrganization')
                : t('tenants:descriptions.manageMultiTenant')}
          </p>
        </div>
        {!isTenantAdminView && !isStoreManagerView && (
          <div className="flex gap-3">
            <button
              onClick={() => setShowOCSCredentialsModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Shield className="w-5 h-5" />
              OCS Credentials
            </button>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-accent-600 text-white rounded-lg hover:bg-accent-700 transition-colors"
            >
              <Plus className="w-5 h-5" />
              {t('tenants:titles.create')}
            </button>
          </div>
        )}
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg ">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">{isTenantAdminView ? t('tenants:metrics.totalStores') : t('tenants:metrics.totalTenants')}</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {isTenantAdminView ? storeCount.total : tenants.length}
              </p>
            </div>
            <Building2 className="w-8 h-8 text-accent-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg ">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">{isTenantAdminView ? t('tenants:metrics.activeStores') : t('tenants:status.active')}</p>
              <p className="text-2xl font-bold text-primary-600">
                {isTenantAdminView ? storeCount.active : tenants.filter(t => t.status === 'active').length}
              </p>
            </div>
            <CheckCircle className="w-8 h-8 text-primary-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg ">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">{t('tenants:subscription.enterprise')}</p>
              <p className="text-2xl font-bold text-purple-600">
                {tenants.filter(t => t.subscription_tier === 'enterprise').length}
              </p>
            </div>
            <Crown className="w-8 h-8 text-purple-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg ">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">{isTenantAdminView ? t('tenants:metrics.lastMonthRevenue') : t('tenants:metrics.monthlyRevenue')}</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                ${isTenantAdminView ?
                  (tenantMetrics?.last_month_revenue?.toLocaleString() || '0') :
                  tenants.reduce((sum, t) => {
                    const price = { enterprise: 299, professional_and_growing_business: 149, small_business: 99, community_and_new_business: 0 };
                    return sum + (price[t.subscription_tier as keyof typeof price] || 0);
                  }, 0)
                }
              </p>
              {isTenantAdminView && tenantMetrics?.order_count !== undefined && (
                <p className="text-xs text-gray-500 mt-1">
                  {tenantMetrics.order_count} order{tenantMetrics.order_count !== 1 ? 's' : ''}
                </p>
              )}
            </div>
            <DollarSign className="w-8 h-8 text-primary-500" />
          </div>
        </div>
      </div>

      {/* Filters - only show for super admin */}
      {!isTenantAdminView && (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg ">
          <div className="flex flex-wrap gap-6">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder={t('tenants:messages.searchPlaceholder')}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>
            </div>

            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-4 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            >
            <option value="all">{t('tenants:messages.filterByStatus')}</option>
            <option value="active">{t('tenants:status.active')}</option>
            <option value="suspended">{t('tenants:status.suspended')}</option>
            <option value="cancelled">{t('tenants:status.inactive')}</option>
          </select>

          <select
            value={filterTier}
            onChange={(e) => setFilterTier(e.target.value)}
            className="px-4 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          >
            <option value="all">All Tiers</option>
            <option value="community_and_new_business">Community and New Business</option>
            <option value="small_business">Small Business</option>
            <option value="professional_and_growing_business">Professional and Growing Business</option>
            <option value="enterprise">Enterprise</option>
          </select>
        </div>
      </div>
      )}

      {/* Organization Card for Tenant Admin and Store Manager */}
      {(isTenantAdminView || isStoreManagerView) && tenants.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg  p-6">
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
              <p className="mt-4 text-gray-500">Loading organization data...</p>
            </div>
          ) : (
            <div>
              <div className="flex items-start justify-between mb-6">
                <div className="flex items-start gap-6">
                  {tenants[0]?.logo_url && (
                    <img
                      src={tenants[0].logo_url.startsWith('http') ? tenants[0].logo_url : `${appConfig.api.baseUrl}${tenants[0].logo_url}`}
                      alt={`${tenants[0].name} logo`}
                      className="w-16 h-16 object-contain rounded"
                    />
                  )}
                  <div>
                    <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
                      {tenants[0].name}
                    </h2>
                    <p className="text-gray-500 dark:text-gray-400">Code: {tenants[0].code}</p>
                    <div className="mt-2">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                        tenants[0].status === 'active' 
                          ? 'bg-primary-100 text-primary-700 dark:bg-green-900/30 dark:text-green-400' 
                          : 'bg-gray-50 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                      }`}>
                        {tenants[0].status}
                      </span>
                    </div>
                  </div>
                </div>
                {!isStoreManagerView && (
                  <button
                    onClick={() => {
                      setSelectedTenant(tenants[0]);
                      setShowTenantModal(true);
                    }}
                    className="flex items-center gap-2 px-4 py-2 bg-accent-600 text-white rounded-lg hover:bg-accent-700"
                  >
                    <Edit className="w-4 h-4" />
                    Edit Organization
                  </button>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div>
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Contact Email</p>
                  <p className="text-gray-900 dark:text-white">{tenants[0].contact_email || 'Not set'}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Contact Phone</p>
                  <p className="text-gray-900 dark:text-white">{tenants[0].contact_phone || 'Not set'}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Subscription</p>
                  <div className="flex items-center gap-2">
                    {getTierIcon(tenants[0].subscription_tier)}
                    <span className="text-gray-900 dark:text-white capitalize">
                      {tenants[0].subscription_tier.replace('_', ' ')}
                    </span>
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Store Limit</p>
                  <p className="text-gray-900 dark:text-white">{storeCount.total} / {tenants[0].max_stores}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Website</p>
                  <p className="text-gray-900 dark:text-white">{tenants[0].website || 'Not set'}</p>
                </div>
              </div>

              <div className="mt-6 pt-6 border-t dark:border-gray-700">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Quick Actions</h3>
                <div className="flex gap-4">
                  <button
                    onClick={() => navigate(`/dashboard/tenants/${tenants[0].code}/stores`)}
                    className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                  >
                    <Store className="w-4 h-4" />
                    {isStoreManagerView ? t('tenants:actions.viewStores') : t('tenants:actions.manageStores')}
                  </button>
                  {!isStoreManagerView && (
                    <button
                      onClick={() => navigate(`/dashboard/tenants/${tenants[0].code}/payment-settings`)}
                      className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                    >
                      <CreditCard className="w-4 h-4" />
                      {t('tenants:actions.paymentSettings')}
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tenants Table - Only show for super admin */}
      {!isTenantAdminView && (
      <div className="bg-white dark:bg-gray-800 rounded-lg  overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Tenant
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Contact
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Subscription
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Stores
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                    Loading tenants...
                  </td>
                </tr>
              ) : filteredTenants.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                    No tenants found
                  </td>
                </tr>
              ) : (
                filteredTenants.map((tenant) => (
                  <tr key={tenant.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-6 py-4">
                      <div className="flex items-start gap-4">
                        {tenant.logo_url && (
                          <img
                            src={tenant.logo_url.startsWith('http') ? tenant.logo_url : `${appConfig.api.baseUrl}${tenant.logo_url}`}
                            alt={`${tenant.name} logo`}
                            className="w-10 h-10 object-contain rounded"
                            onError={(e) => {
                              (e.target as HTMLImageElement).style.display = 'none';
                            }}
                          />
                        )}
                        <div>
                          <div className="text-sm font-medium text-gray-900 dark:text-white">
                            {tenant.name}
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            Code: {tenant.code}
                          </div>
                          {tenant.company_name && (
                            <div className="text-xs text-gray-400 dark:text-gray-500">
                              {tenant.company_name}
                            </div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm">
                        <div className="text-gray-900 dark:text-white">
                          {tenant.contact_email}
                        </div>
                        {tenant.contact_phone && (
                          <div className="text-gray-500 dark:text-gray-400">
                            {tenant.contact_phone}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        {getTierIcon(tenant.subscription_tier)}
                        <div>
                          <div className="text-sm font-medium text-gray-900 dark:text-white capitalize">
                            {tenant.subscription_tier.replace('_', ' ')}
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400">
                            {getTierPrice(tenant.subscription_tier)}/month
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <Store className="w-4 h-4 text-gray-400" />
                        <span className="text-sm text-gray-900 dark:text-white">
                          0 / {tenant.max_stores}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(tenant.status)}
                        <span className="text-sm capitalize text-gray-900 dark:text-white">
                          {tenant.status}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => navigate(`/dashboard/tenants/${tenant.code}/stores`)}
                          className="p-1 text-gray-600 hover:text-indigo-600 dark:text-gray-400 dark:hover:text-indigo-400"
                          title={t('tenants:actions.manageStores')}
                        >
                          <Store className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => navigate(`/dashboard/tenants/${tenant.code}/payment-settings`)}
                          className="p-1 text-gray-600 hover:text-purple-600 dark:text-gray-400 dark:hover:text-purple-400"
                          title={t('tenants:actions.paymentSettings')}
                        >
                          <CreditCard className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => {
                            if (isTenantAdminView) {
                              setSelectedTenant(tenant);
                              setShowTenantModal(true);
                            } else {
                              setEditingTenant(tenant);
                            }
                          }}
                          className="p-1 text-gray-600 hover:text-accent-600 dark:text-gray-400 dark:hover:text-blue-400"
                          title="Edit"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        {tenant.status === 'active' ? (
                          <button
                            onClick={() => handleSuspendTenant(tenant.id)}
                            className="p-1 text-gray-600 hover:text-warning-600 dark:text-gray-400 dark:hover:text-yellow-400"
                            title="Suspend"
                          >
                            <Pause className="w-4 h-4" />
                          </button>
                        ) : tenant.status === 'suspended' ? (
                          <button
                            onClick={() => handleReactivateTenant(tenant.id)}
                            className="p-1 text-gray-600 hover:text-primary-600 dark:text-gray-400 dark:hover:text-green-400"
                            title="Reactivate"
                          >
                            <Play className="w-4 h-4" />
                          </button>
                        ) : null}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
      )}

      {/* Edit Modal for tenant admins */}
      {isTenantAdminView && selectedTenant && showTenantModal && (
        <TenantEditModal
          tenant={selectedTenant}
          isOpen={showTenantModal}
          onClose={() => {
            setShowTenantModal(false);
            setSelectedTenant(null);
          }}
          onSave={async (updatedTenant, logoFile) => {
            await handleUpdateTenant(selectedTenant.id, updatedTenant, logoFile);
            setShowTenantModal(false);
            setSelectedTenant(null);
            loadTenants(); // Refresh tenants to show updated logo
          }}
          readOnly={false}
          showUsersTab={true}
        />
      )}

      {/* Create/Edit Modal for super admins */}
      {!isTenantAdminView && (showCreateModal || editingTenant) && (
        <TenantFormModal
          tenant={editingTenant}
          onSave={(data, logoFile) => {
            if (editingTenant) {
              handleUpdateTenant(editingTenant.id, data, logoFile);
            } else {
              handleCreateTenant(data as CreateTenantRequest);
            }
          }}
          onClose={() => {
            setShowCreateModal(false);
            setEditingTenant(null);
          }}
        />
      )}

      {/* OCS Credentials Modal */}
      {showOCSCredentialsModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <Shield className="w-6 h-6" />
                OCS OAuth Credentials Configuration
              </h2>
              <button
                onClick={() => setShowOCSCredentialsModal(false)}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
              <p className="text-sm text-blue-900 dark:text-blue-100">
                <strong>Note:</strong> These OAuth credentials will be used to authenticate with the OCS API for the selected tenant. 
                Each tenant requires its own set of OAuth credentials.
              </p>
            </div>

            <form onSubmit={async (e) => {
              e.preventDefault();
              const formData = new FormData(e.currentTarget);
              const tenantId = formData.get('tenant_id') as string;
              const credentials = {
                client_id: formData.get('client_id') as string,
                client_secret: formData.get('client_secret') as string,
              };

              try {
                await ocsService.storeCredentials(tenantId, credentials);
                toast.success('OCS credentials saved successfully');
                setShowOCSCredentialsModal(false);
              } catch (error) {
                console.error('Error saving OCS credentials:', error);
                toast.error('Failed to save OCS credentials');
              }
            }}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Select Tenant
                  </label>
                  <select
                    name="tenant_id"
                    required
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="">-- Select a tenant --</option>
                    {tenants.map(tenant => (
                      <option key={tenant.id} value={tenant.id}>
                        {tenant.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    OAuth Client ID
                  </label>
                  <input
                    type="text"
                    name="client_id"
                    required
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    placeholder="Enter OAuth Client ID"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    OAuth Client Secret
                  </label>
                  <input
                    type="password"
                    name="client_secret"
                    required
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    placeholder="Enter OAuth Client Secret"
                  />
                </div>

                <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-2">Default OAuth Configuration</h3>
                  <div className="space-y-1 text-xs text-gray-600 dark:text-gray-400">
                    <p><strong>Token URL:</strong> https://login.microsoftonline.com/common/oauth2/v2.0/token</p>
                    <p><strong>Scope:</strong> https://ocsapi.ocs.ca/.default</p>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                    These default values are automatically used by the OCS integration.
                  </p>
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowOCSCredentialsModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Save Credentials
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

// Helper function to format phone number
const formatPhoneNumber = (value: string) => {
  // Remove all non-digits
  const digits = value.replace(/\D/g, '');
  
  // Format as (XXX) XXX-XXXX or +X (XXX) XXX-XXXX
  if (digits.length <= 10) {
    const match = digits.match(/^(\d{0,3})(\d{0,3})(\d{0,4})$/);
    if (match) {
      const [, area, prefix, line] = match;
      if (line) return `(${area}) ${prefix}-${line}`;
      if (prefix) return `(${area}) ${prefix}`;
      if (area) return area.length === 3 ? `(${area}) ` : area;
    }
  } else {
    // Handle international format with country code
    const match = digits.match(/^(\d{1,3})(\d{0,3})(\d{0,3})(\d{0,4})$/);
    if (match) {
      const [, country, area, prefix, line] = match;
      if (line) return `+${country} (${area}) ${prefix}-${line}`;
      if (prefix) return `+${country} (${area}) ${prefix}`;
      if (area) return `+${country} (${area})`;
      if (country) return `+${country}`;
    }
  }
  return value;
};

// Helper function to normalize website URL
const normalizeWebsiteUrl = (url: string) => {
  if (!url) return '';
  // If no protocol, add https://
  if (!url.match(/^https?:\/\//)) {
    return `https://${url}`;
  }
  return url;
};

// Tenant Form Modal Component
const TenantFormModal: React.FC<{
  tenant?: Tenant | null;
  onSave: (data: Partial<CreateTenantRequest>, logoFile?: File | null) => void;
  onClose: () => void;
}> = ({ tenant, onSave, onClose }) => {
  const { t } = useTranslation(['tenants', 'common']);
  const [activeTab, setActiveTab] = useState<'general' | 'features' | 'branding' | 'legal' | 'delivery' | 'payment' | 'notifications' | 'seo' | 'analytics' | 'budtender' | 'users'>('general');
  const [logoFile, setLogoFile] = useState<File | null>(null);
  const [logoPreview, setLogoPreview] = useState<string | null>(tenant?.logo_url || null);
  const [tenantUsers, setTenantUsers] = useState<any[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [userError, setUserError] = useState<string | null>(null);
  const [userSuccess, setUserSuccess] = useState<string | null>(null);
  const [showAddUserForm, setShowAddUserForm] = useState(false);
  const [newUser, setNewUser] = useState({ email: '', first_name: '', last_name: '', role: 'staff', password: '' });
  const [formData, setFormData] = useState<Partial<CreateTenantRequest>>({
    name: tenant?.name || '',
    code: tenant?.code || '',
    contact_email: tenant?.contact_email || '',
    subscription_tier: tenant?.subscription_tier as any || 'community_and_new_business',
    company_name: tenant?.company_name || '',
    business_number: tenant?.business_number || '',
    gst_hst_number: tenant?.gst_hst_number || '',
    crol_number: tenant?.crol_number || '',
    contact_phone: tenant?.contact_phone || '',
    website: tenant?.website || '',
    address: tenant?.address || {
      street: '',
      city: '',
      province: '',
      postal_code: '',
      country: 'Canada',
    },
  });
  
  // Initialize settings from tenant or defaults
  const [settings, setSettings] = useState({
    features: {
      reviews: tenant?.settings?.features?.reviews ?? true,
      wishlist: tenant?.settings?.features?.wishlist ?? true,
      loyalty_program: tenant?.settings?.features?.loyalty_program ?? false,
      virtual_budtender: tenant?.settings?.features?.virtual_budtender ?? false,
      recommendations: tenant?.settings?.features?.recommendations ?? true,
    },
    branding: {
      primary_color: tenant?.settings?.branding?.primary_color || '#4F46E5',
      secondary_color: tenant?.settings?.branding?.secondary_color || '#10B981',
      font_family: tenant?.settings?.branding?.font_family || 'Inter',
      custom_css: tenant?.settings?.branding?.custom_css || '',
      favicon_url: tenant?.settings?.branding?.favicon_url || '',
      email_logo_url: tenant?.settings?.branding?.email_logo_url || '',
      invoice_logo_url: tenant?.settings?.branding?.invoice_logo_url || '',
    },
    legal: {
      terms_url: tenant?.settings?.legal?.terms_url || '',
      privacy_url: tenant?.settings?.legal?.privacy_url || '',
      age_verification: tenant?.settings?.legal?.age_verification ?? true,
    },
    delivery: {
      min_order_value: tenant?.settings?.delivery?.min_order_value || 50,
      free_delivery_threshold: tenant?.settings?.delivery?.free_delivery_threshold || 150,
      delivery_zones: tenant?.settings?.delivery?.delivery_zones || [],
      blackout_dates: tenant?.settings?.delivery?.blackout_dates || [],
    },
    analytics: {
      google_analytics_id: tenant?.settings?.analytics?.google_analytics_id || '',
      facebook_pixel_id: tenant?.settings?.analytics?.facebook_pixel_id || '',
      enable_heatmaps: tenant?.settings?.analytics?.enable_heatmaps ?? false,
      enable_session_recording: tenant?.settings?.analytics?.enable_session_recording ?? false,
      segment_write_key: tenant?.settings?.analytics?.segment_write_key || '',
      mixpanel_token: tenant?.settings?.analytics?.mixpanel_token || '',
    },
    virtual_budtender: {
      enabled: tenant?.settings?.virtual_budtender?.enabled ?? false,
      ai_model: tenant?.settings?.virtual_budtender?.ai_model || 'gpt-4',
      personality: tenant?.settings?.virtual_budtender?.personality || 'friendly',
      product_recommendations: tenant?.settings?.virtual_budtender?.product_recommendations ?? true,
      dosage_guidance: tenant?.settings?.virtual_budtender?.dosage_guidance ?? true,
    },
    payment: {
      accepted_methods: tenant?.settings?.payment?.accepted_methods || ['credit_card', 'debit_card'],
      gateway_provider: tenant?.settings?.payment?.gateway_provider || 'stripe',
      hold_duration_days: tenant?.settings?.payment?.hold_duration_days || 7,
      auto_capture: tenant?.settings?.payment?.auto_capture ?? true,
    },
    notifications: {
      email_enabled: tenant?.settings?.notifications?.email_enabled ?? true,
      sms_enabled: tenant?.settings?.notifications?.sms_enabled ?? false,
      push_enabled: tenant?.settings?.notifications?.push_enabled ?? false,
      order_updates: tenant?.settings?.notifications?.order_updates ?? true,
      marketing: tenant?.settings?.notifications?.marketing ?? false,
    },
    seo: {
      meta_title: tenant?.settings?.seo?.meta_title || '',
      meta_description: tenant?.settings?.seo?.meta_description || '',
      sitemap_enabled: tenant?.settings?.seo?.sitemap_enabled ?? true,
      robots_txt: tenant?.settings?.seo?.robots_txt || '',
    },
  });

  // Fetch tenant users when Users tab is active
  useEffect(() => {
    if (activeTab === 'users' && tenant?.id) {
      fetchTenantUsers();
    }
  }, [activeTab, tenant?.id]);

  const fetchTenantUsers = async () => {
    if (!tenant?.id) {
      console.log('fetchTenantUsers: No tenant ID available');
      return;
    }
    
    console.log('fetchTenantUsers: Fetching users for tenant:', tenant.id);
    setLoadingUsers(true);
    setUserError(null);
    try {
      const authToken = localStorage.getItem('authToken');
      const apiUrl = getApiEndpoint(`/tenants/${tenant.id}/users`);
      console.log('fetchTenantUsers: Full API URL:', apiUrl);
      console.log('fetchTenantUsers: Auth token exists:', !!authToken);
      const response = await fetch(apiUrl, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      });
      console.log('fetchTenantUsers: Response status:', response.status);
      if (!response.ok) {
        const errorText = await response.text();
        console.error('fetchTenantUsers: Error response:', errorText);
        throw new Error(`Failed to fetch users: ${response.status}`);
      }
      const data = await response.json();
      console.log('fetchTenantUsers: Received users:', data);
      // Filter out customers - only show admin users (tenant_admin, store_manager, staff)
      const adminUsers = data.filter((user: any) => 
        user.role !== 'customer' && user.role !== 'super_admin'
      );
      console.log('fetchTenantUsers: Filtered admin users:', adminUsers);
      setTenantUsers(adminUsers);
    } catch (err: any) {
      console.error('fetchTenantUsers: Error:', err);
      setUserError(err.message);
    } finally {
      setLoadingUsers(false);
    }
  };

  const handleResetPassword = async (userId: string) => {
    if (!tenant?.id) return;
    
    try {
      const response = await fetch(
        getApiEndpoint(`/tenants/${tenant.id}/users/${userId}/reset-password`),
        { method: 'POST' }
      );
      if (!response.ok) throw new Error('Failed to reset password');
      const data = await response.json();
      setUserSuccess(`Password reset successfully. Temporary password: ${data.temporary_password}`);
      setTimeout(() => setUserSuccess(null), 5000);
    } catch (err: any) {
      setUserError(err.message);
      setTimeout(() => setUserError(null), 3000);
    }
  };

  const handleToggleUserStatus = async (userId: string, currentStatus: boolean) => {
    if (!tenant?.id) return;
    
    try {
      const response = await fetch(
        getApiEndpoint(`/tenants/${tenant.id}/users/${userId}`),
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ active: !currentStatus })
        }
      );
      if (!response.ok) throw new Error('Failed to update user status');
      await fetchTenantUsers();
      setUserSuccess(`User ${!currentStatus ? 'activated' : 'deactivated'} successfully`);
      setTimeout(() => setUserSuccess(null), 3000);
    } catch (err: any) {
      setUserError(err.message);
      setTimeout(() => setUserError(null), 3000);
    }
  };

  const handleDeleteUser = async (userId: string, userEmail: string) => {
    if (!tenant?.id) return;

    if (!window.confirm(t('common:confirmations.deleteUser', { email: userEmail }))) return;

    try {
      const response = await fetch(
        getApiEndpoint(`/tenants/${tenant.id}/users/${userId}`),
        { method: 'DELETE' }
      );
      if (!response.ok) throw new Error(t('tenants:messages.deleteFailed'));
      await fetchTenantUsers();
      setUserSuccess(t('tenants:userManagement.deleted'));
      setTimeout(() => setUserSuccess(null), 3000);
    } catch (err: any) {
      setUserError(err.message);
      setTimeout(() => setUserError(null), 3000);
    }
  };

  const handleEditUserRole = async (userId: string, newRole: string) => {
    if (!tenant?.id) return;

    try {
      const response = await fetch(
        getApiEndpoint(`/tenants/${tenant.id}/users/${userId}`),
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ role: newRole })
        }
      );
      if (!response.ok) throw new Error(t('tenants:messages.updateFailed'));
      await fetchTenantUsers();
      setUserSuccess(t('tenants:userManagement.roleUpdated'));
      setTimeout(() => setUserSuccess(null), 3000);
    } catch (err: any) {
      setUserError(err.message);
      setTimeout(() => setUserError(null), 3000);
    }
  };

  const handleAddUser = async () => {
    if (!tenant?.id) return;

    setUserError(null);
    setUserSuccess(null);

    try {
      const authToken = localStorage.getItem('authToken');
      const response = await fetch(
        getApiEndpoint(`/tenants/${tenant.id}/users`),
        {
          method: 'POST',
          headers: { 
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json' 
          },
          body: JSON.stringify(newUser)
        }
      );
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || t('tenants:messages.createFailed'));
      }
      await fetchTenantUsers();
      setUserSuccess(t('tenants:userManagement.created'));
      setShowAddUserForm(false);
      setNewUser({ email: '', first_name: '', last_name: '', role: 'staff', password: '' });
      setTimeout(() => setUserSuccess(null), 3000);
    } catch (err: any) {
      setUserError(err.message);
      setTimeout(() => setUserError(null), 3000);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Normalize website URL before saving
    const dataToSave = {
      ...formData,
      website: normalizeWebsiteUrl(formData.website || ''),
      settings: settings // Include all settings in the save
    };
    onSave(dataToSave, logoFile);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-6xl max-h-[90vh] overflow-y-auto">
        <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">
          {tenant ? t('tenants:titles.edit') : t('tenants:titles.create')}
        </h2>
        
        {/* Tab Navigation */}
        <div className="mb-6 border-b border-gray-200 dark:border-gray-700">
          <nav className="-mb-px flex space-x-8">
            <button
              type="button"
              onClick={() => setActiveTab('general')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'general'
                  ? 'border-blue-500 text-accent-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              General
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('features')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'features'
                  ? 'border-blue-500 text-accent-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              Features
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('branding')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'branding'
                  ? 'border-blue-500 text-accent-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              Branding
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('legal')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'legal'
                  ? 'border-blue-500 text-accent-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              Legal & Compliance
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('delivery')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'delivery'
                  ? 'border-blue-500 text-accent-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              Delivery
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('payment')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'payment'
                  ? 'border-blue-500 text-accent-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              Payment
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('notifications')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'notifications'
                  ? 'border-blue-500 text-accent-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              Notifications
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('seo')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'seo'
                  ? 'border-blue-500 text-accent-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              SEO
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('analytics')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'analytics'
                  ? 'border-blue-500 text-accent-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              Analytics
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('budtender')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'budtender'
                  ? 'border-blue-500 text-accent-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              Virtual Budtender
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('users')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'users'
                  ? 'border-blue-500 text-accent-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              Admin Users
            </button>
          </nav>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <>
            {/* General Tab */}
            {activeTab === 'general' && (
            <>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Tenant Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Tenant Code *
                  </label>
                  <input
                    type="text"
                    required
                    disabled={!!tenant}
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                    pattern="^[A-Z0-9_\-]+$"
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white disabled:opacity-50"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Contact Email *
                  </label>
                  <input
                    type="email"
                    required
                    value={formData.contact_email}
                    onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Subscription Tier *
                  </label>
                  <select
                    required
                    value={formData.subscription_tier}
                    onChange={(e) => setFormData({ ...formData, subscription_tier: e.target.value as any })}
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="community_and_new_business">Community and New Business (Free)</option>
                    <option value="small_business">Small Business ($99/month)</option>
                    <option value="professional_and_growing_business">Professional and Growing Business ($149/month)</option>
                    <option value="enterprise">Enterprise ($299+/month)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Company Name
                </label>
                <input
                  type="text"
                  value={formData.company_name}
                  onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Business Number
                  </label>
                  <input
                    type="text"
                    value={formData.business_number}
                    onChange={(e) => setFormData({ ...formData, business_number: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    GST/HST Number
                  </label>
                  <input
                    type="text"
                    value={formData.gst_hst_number}
                    onChange={(e) => setFormData({ ...formData, gst_hst_number: e.target.value })}
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
                    value={formData.contact_phone}
                    onChange={(e) => {
                      const formatted = formatPhoneNumber(e.target.value);
                      setFormData({ ...formData, contact_phone: formatted });
                    }}
                    placeholder="(416) 555-0123"
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    CROL Number
                  </label>
                  <input
                    type="text"
                    value={formData.crol_number}
                    onChange={(e) => setFormData({ ...formData, crol_number: e.target.value })}
                    placeholder="Cannabis Retail Operating License"
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    Required for OCS integration (Ontario only)
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Website
                  </label>
                  <input
                    type="text"
                    value={formData.website}
                    onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                    placeholder="www.example.com"
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Logo Upload
                </label>
                <div className="space-y-2">
                  <div className="flex items-center space-x-3">
                    <input
                      type="file"
                      accept="image/png,image/jpeg,image/jpg,image/webp"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                          setLogoFile(file);
                          const reader = new FileReader();
                          reader.onloadend = () => {
                            setLogoPreview(reader.result as string);
                          };
                          reader.readAsDataURL(file);
                        }
                      }}
                      className="flex-1 px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    />
                    {logoPreview && (
                      <img 
                        src={logoPreview} 
                        alt="Logo preview" 
                        className="w-16 h-16 object-contain border border-gray-200 dark:border-gray-600 rounded"
                      />
                    )}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    Max 2MB • PNG, JPG, WebP • Recommended: 500x500px square
                  </div>
                </div>
              </div>
            </>
          )}

          {/* Features Tab */}
          {activeTab === 'features' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Platform Features</h3>
              <div className="grid grid-cols-2 gap-6">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={settings.features.reviews}
                    onChange={(e) => setSettings({ ...settings, features: { ...settings.features, reviews: e.target.checked }})}
                    className="w-4 h-4 text-accent-600 rounded"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Product Reviews</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={settings.features.wishlist}
                    onChange={(e) => setSettings({ ...settings, features: { ...settings.features, wishlist: e.target.checked }})}
                    className="w-4 h-4 text-accent-600 rounded"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Wishlist</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={settings.features.loyalty_program}
                    onChange={(e) => setSettings({ ...settings, features: { ...settings.features, loyalty_program: e.target.checked }})}
                    className="w-4 h-4 text-accent-600 rounded"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Loyalty Program</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={settings.features.virtual_budtender}
                    onChange={(e) => setSettings({ ...settings, features: { ...settings.features, virtual_budtender: e.target.checked }})}
                    className="w-4 h-4 text-accent-600 rounded"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Virtual Budtender</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={settings.features.recommendations}
                    onChange={(e) => setSettings({ ...settings, features: { ...settings.features, recommendations: e.target.checked }})}
                    className="w-4 h-4 text-accent-600 rounded"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Product Recommendations</span>
                </label>
              </div>
              
              {settings.features.virtual_budtender && (
                <>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6">Virtual Budtender Settings</h3>
                  <div className="grid grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        AI Model
                      </label>
                      <select
                        value={settings.virtual_budtender.ai_model}
                        onChange={(e) => setSettings({ ...settings, virtual_budtender: { ...settings.virtual_budtender, ai_model: e.target.value }})}
                        className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                      >
                        <option value="gpt-4">GPT-4</option>
                        <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                        <option value="claude-3">Claude 3</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Personality
                      </label>
                      <select
                        value={settings.virtual_budtender.personality}
                        onChange={(e) => setSettings({ ...settings, virtual_budtender: { ...settings.virtual_budtender, personality: e.target.value }})}
                        className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                      >
                        <option value="friendly">Friendly</option>
                        <option value="professional">Professional</option>
                        <option value="educational">Educational</option>
                        <option value="casual">Casual</option>
                      </select>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-6">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={settings.virtual_budtender.product_recommendations}
                        onChange={(e) => setSettings({ ...settings, virtual_budtender: { ...settings.virtual_budtender, product_recommendations: e.target.checked }})}
                        className="w-4 h-4 text-accent-600 rounded"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">Product Recommendations</span>
                    </label>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={settings.virtual_budtender.dosage_guidance}
                        onChange={(e) => setSettings({ ...settings, virtual_budtender: { ...settings.virtual_budtender, dosage_guidance: e.target.checked }})}
                        className="w-4 h-4 text-accent-600 rounded"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">Dosage Guidance</span>
                    </label>
                  </div>
                </>
              )}
            </div>
          )}

          {/* Branding Tab */}
          {activeTab === 'branding' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Brand Colors</h3>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Primary Color
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="color"
                      value={settings.branding.primary_color}
                      onChange={(e) => setSettings({ ...settings, branding: { ...settings.branding, primary_color: e.target.value }})}
                      className="w-12 h-10 border border-gray-200 dark:border-gray-600 rounded"
                    />
                    <input
                      type="text"
                      value={settings.branding.primary_color}
                      onChange={(e) => setSettings({ ...settings, branding: { ...settings.branding, primary_color: e.target.value }})}
                      className="flex-1 px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Secondary Color
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="color"
                      value={settings.branding.secondary_color}
                      onChange={(e) => setSettings({ ...settings, branding: { ...settings.branding, secondary_color: e.target.value }})}
                      className="w-12 h-10 border border-gray-200 dark:border-gray-600 rounded"
                    />
                    <input
                      type="text"
                      value={settings.branding.secondary_color}
                      onChange={(e) => setSettings({ ...settings, branding: { ...settings.branding, secondary_color: e.target.value }})}
                      className="flex-1 px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    />
                  </div>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Font Family
                </label>
                <select
                  value={settings.branding.font_family}
                  onChange={(e) => setSettings({ ...settings, branding: { ...settings.branding, font_family: e.target.value }})}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                >
                  <option value="Inter">Inter</option>
                  <option value="Roboto">Roboto</option>
                  <option value="Open Sans">Open Sans</option>
                  <option value="Lato">Lato</option>
                  <option value="Montserrat">Montserrat</option>
                  <option value="Poppins">Poppins</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Custom CSS
                </label>
                <textarea
                  value={settings.branding.custom_css}
                  onChange={(e) => setSettings({ ...settings, branding: { ...settings.branding, custom_css: e.target.value }})}
                  rows={4}
                  placeholder="/* Add custom CSS here */"
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white font-mono text-sm"
                />
              </div>
            </div>
          )}

          {/* Legal Tab */}
          {activeTab === 'legal' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Compliance Settings</h3>
              <div className="grid grid-cols-2 gap-6">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={settings.legal.age_verification}
                    onChange={(e) => setSettings({ ...settings, legal: { ...settings.legal, age_verification: e.target.checked }})}
                    className="w-4 h-4 text-accent-600 rounded"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Age Verification Required</span>
                </label>
              </div>
            </div>
          )}

          {/* Delivery Tab */}
          {activeTab === 'delivery' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Delivery Settings</h3>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Minimum Order Value ($)
                  </label>
                  <input
                    type="number"
                    value={settings.delivery.min_order_value}
                    onChange={(e) => setSettings({ ...settings, delivery: { ...settings.delivery, min_order_value: parseFloat(e.target.value) }})}
                    min="0"
                    step="5"
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Free Delivery Threshold ($)
                  </label>
                  <input
                    type="number"
                    value={settings.delivery.free_delivery_threshold}
                    onChange={(e) => setSettings({ ...settings, delivery: { ...settings.delivery, free_delivery_threshold: parseFloat(e.target.value) }})}
                    min="0"
                    step="10"
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Analytics Tab */}
          {activeTab === 'analytics' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Analytics Integrations</h3>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('tenants:seo.googleAnalytics')}
                </label>
                <input
                  type="text"
                  value={settings.analytics.google_analytics_id}
                  onChange={(e) => setSettings({ ...settings, analytics: { ...settings.analytics, google_analytics_id: e.target.value }})}
                  placeholder={t('tenants:seo.googleAnalyticsPlaceholder')}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('tenants:seo.facebookPixel')}
                </label>
                <input
                  type="text"
                  value={settings.analytics.facebook_pixel_id}
                  onChange={(e) => setSettings({ ...settings, analytics: { ...settings.analytics, facebook_pixel_id: e.target.value }})}
                  placeholder={t('tenants:seo.facebookPixelPlaceholder')}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Segment Write Key
                </label>
                <input
                  type="text"
                  value={settings.analytics.segment_write_key}
                  onChange={(e) => setSettings({ ...settings, analytics: { ...settings.analytics, segment_write_key: e.target.value }})}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Mixpanel Token
                </label>
                <input
                  type="text"
                  value={settings.analytics.mixpanel_token}
                  onChange={(e) => setSettings({ ...settings, analytics: { ...settings.analytics, mixpanel_token: e.target.value }})}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>
            </div>
          )}

          {/* Virtual Budtender Tab */}
          {activeTab === 'budtender' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Virtual Budtender Configuration</h3>
              
              <div>
                <label className="flex items-center gap-2 mb-4">
                  <input
                    type="checkbox"
                    checked={settings.virtual_budtender.enabled}
                    onChange={(e) => setSettings({ ...settings, virtual_budtender: { ...settings.virtual_budtender, enabled: e.target.checked }})}
                    className="w-4 h-4 text-accent-600 rounded"
                  />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Enable Virtual Budtender</span>
                </label>
              </div>

              {settings.virtual_budtender.enabled && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      AI Model
                    </label>
                    <select
                      value={settings.virtual_budtender.ai_model}
                      onChange={(e) => setSettings({ ...settings, virtual_budtender: { ...settings.virtual_budtender, ai_model: e.target.value }})}
                      className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    >
                      <option value="gpt-4">GPT-4 (Most Advanced)</option>
                      <option value="gpt-3.5-turbo">GPT-3.5 Turbo (Fast & Efficient)</option>
                      <option value="claude-3">Claude 3 (Balanced)</option>
                      <option value="llama-2">Llama 2 (Open Source)</option>
                    </select>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Choose the AI model that powers your virtual budtender
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Personality Style
                    </label>
                    <select
                      value={settings.virtual_budtender.personality}
                      onChange={(e) => setSettings({ ...settings, virtual_budtender: { ...settings.virtual_budtender, personality: e.target.value }})}
                      className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    >
                      <option value="friendly">Friendly - Warm and welcoming approach</option>
                      <option value="professional">Professional - Formal and informative</option>
                      <option value="educational">Educational - Focus on learning and effects</option>
                      <option value="casual">Casual - Relaxed and conversational</option>
                      <option value="expert">Expert - Deep knowledge and recommendations</option>
                    </select>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Define how your virtual budtender interacts with customers
                    </p>
                  </div>
                </>
              )}
            </div>
          )}

          {/* Users Tab */}
          {activeTab === 'users' && (
            <div className="space-y-4">
              {/* Success/Error Messages */}
              {userSuccess && (
                <div className="p-4 bg-primary-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                  <p className="text-sm text-primary-700 dark:text-green-300">{userSuccess}</p>
                </div>
              )}
              {userError && (
                <div className="p-4 bg-danger-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                  <p className="text-sm text-red-700 dark:text-red-300">{userError}</p>
                </div>
              )}

              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Tenant Admin Users</h3>
                <button
                  type="button"
                  className="flex items-center gap-2 px-4 py-2 bg-accent-500 text-white rounded-lg hover:bg-accent-600 transition-colors"
                  onClick={() => setShowAddUserForm(true)}
                >
                  <UserPlus className="w-4 h-4" />
                  Add User
                </button>
              </div>

              {/* Add User Form */}
              {showAddUserForm && (
                <div className="p-6 bg-gray-50 dark:bg-gray-700 rounded-lg space-y-3 mb-4">
                  <h4 className="font-medium text-gray-900 dark:text-white">Add New User</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <input
                      type="email"
                      placeholder="Email"
                      value={newUser.email}
                      onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                      className="px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-600 text-gray-900 dark:text-white placeholder-gray-400"
                    />
                    <input
                      type="password"
                      placeholder="Password"
                      value={newUser.password}
                      onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                      className="px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-600 text-gray-900 dark:text-white placeholder-gray-400"
                    />
                    <input
                      type="text"
                      placeholder="First Name"
                      value={newUser.first_name}
                      onChange={(e) => setNewUser({ ...newUser, first_name: e.target.value })}
                      className="px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-600 text-gray-900 dark:text-white placeholder-gray-400"
                    />
                    <input
                      type="text"
                      placeholder="Last Name"
                      value={newUser.last_name}
                      onChange={(e) => setNewUser({ ...newUser, last_name: e.target.value })}
                      className="px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-600 text-gray-900 dark:text-white placeholder-gray-400"
                    />
                    <select
                      value={newUser.role}
                      onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                      className="px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-600 text-gray-900 dark:text-white col-span-2"
                    >
                      <option value="tenant_admin">Tenant Admin</option>
                      <option value="store_manager">Store Manager</option>
                      <option value="staff">Staff</option>
                    </select>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={handleAddUser}
                      className="px-4 py-2 bg-primary-600 dark:bg-primary-700 text-white rounded-lg hover:bg-primary-700 dark:hover:bg-primary-600"
                    >
                      Add User
                    </button>
                    <button
                      onClick={() => setShowAddUserForm(false)}
                      className="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-400 dark:hover:bg-gray-500"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              {/* User List */}
              <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6">
                {loadingUsers ? (
                  <div className="flex justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                  </div>
                ) : tenantUsers.length === 0 ? (
                  <div className="text-center py-8 bg-white dark:bg-gray-700/50 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600">
                    <Users className="w-12 h-12 mx-auto text-gray-400 dark:text-gray-500 mb-3" />
                    <p className="text-gray-600 dark:text-gray-400 font-medium mb-1">No admin users yet</p>
                    <p className="text-sm text-gray-500 dark:text-gray-500 mb-4">
                      Click the "Add User" button above to create the first admin user for this tenant
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {tenantUsers.map((user) => (
                      <div key={user.id} className="flex items-center justify-between p-4 bg-white dark:bg-gray-700 rounded-lg">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 bg-gray-100 dark:bg-gray-600 rounded-full flex items-center justify-center">
                            <Users className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                          </div>
                          <div>
                            <div className="font-medium text-gray-900 dark:text-white">
                              {user.first_name || 'N/A'} {user.last_name || ''}
                            </div>
                            <div className="text-sm text-gray-500 dark:text-gray-400">
                              {user.email}
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-6">
                          <div className="flex items-center gap-2">
                            <Shield className="w-4 h-4 text-gray-400" />
                            <select
                              value={user.role}
                              onChange={(e) => handleEditUserRole(user.id, e.target.value)}
                              className="text-sm text-gray-600 dark:text-gray-300 bg-transparent border border-gray-200 dark:border-gray-600 rounded px-2 py-1"
                              title="Change Role"
                            >
                              <option value="tenant_admin">Tenant Admin</option>
                              <option value="store_manager">Store Manager</option>
                              <option value="staff">Staff</option>
                            </select>
                          </div>
                          
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            user.active 
                              ? 'bg-primary-100 text-primary-700 dark:bg-green-900 dark:text-green-300' 
                              : 'bg-danger-100 text-red-700 dark:bg-red-900 dark:text-red-300'
                          }`}>
                            {user.active ? 'Active' : 'Inactive'}
                          </span>
                          
                          <div className="flex items-center gap-1">
                            <button
                              type="button"
                              className="p-1 text-gray-400 hover:text-accent-500 transition-colors"
                              title="Reset Password"
                              onClick={() => handleResetPassword(user.id)}
                            >
                              <RefreshCw className="w-4 h-4" />
                            </button>
                            <button
                              type="button"
                              className="p-1 text-gray-400 hover:text-yellow-500 transition-colors"
                              title={user.active ? 'Block User' : 'Unblock User'}
                              onClick={() => handleToggleUserStatus(user.id, user.active)}
                            >
                              <Ban className="w-4 h-4" />
                            </button>
                            <button
                              type="button"
                              className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                              title="Delete User"
                              onClick={() => handleDeleteUser(user.id, user.email)}
                            >
                              <UserX className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6">
                <p className="text-sm text-accent-700 dark:text-blue-300">
                  Tenant admin users can manage stores, staff, and settings across all stores in this tenant.
                </p>
              </div>
            </div>
          )}

          {/* Payment Tab */}
          {activeTab === 'payment' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Payment Settings</h3>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Accepted Payment Methods
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={settings.payment.accepted_methods.includes('credit_card')}
                      onChange={(e) => {
                        const methods = e.target.checked 
                          ? [...settings.payment.accepted_methods, 'credit_card']
                          : settings.payment.accepted_methods.filter((m: string) => m !== 'credit_card');
                        setSettings({ ...settings, payment: { ...settings.payment, accepted_methods: methods }});
                      }}
                      className="w-4 h-4 text-accent-600 rounded"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">Credit Card</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={settings.payment.accepted_methods.includes('debit_card')}
                      onChange={(e) => {
                        const methods = e.target.checked 
                          ? [...settings.payment.accepted_methods, 'debit_card']
                          : settings.payment.accepted_methods.filter((m: string) => m !== 'debit_card');
                        setSettings({ ...settings, payment: { ...settings.payment, accepted_methods: methods }});
                      }}
                      className="w-4 h-4 text-accent-600 rounded"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">Debit Card</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={settings.payment.accepted_methods.includes('cash')}
                      onChange={(e) => {
                        const methods = e.target.checked 
                          ? [...settings.payment.accepted_methods, 'cash']
                          : settings.payment.accepted_methods.filter((m: string) => m !== 'cash');
                        setSettings({ ...settings, payment: { ...settings.payment, accepted_methods: methods }});
                      }}
                      className="w-4 h-4 text-accent-600 rounded"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">Cash</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={settings.payment.accepted_methods.includes('etransfer')}
                      onChange={(e) => {
                        const methods = e.target.checked 
                          ? [...settings.payment.accepted_methods, 'etransfer']
                          : settings.payment.accepted_methods.filter((m: string) => m !== 'etransfer');
                        setSettings({ ...settings, payment: { ...settings.payment, accepted_methods: methods }});
                      }}
                      className="w-4 h-4 text-accent-600 rounded"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">E-Transfer</span>
                  </label>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Payment Gateway Provider
                  </label>
                  <select
                    value={settings.payment.gateway_provider}
                    onChange={(e) => setSettings({ ...settings, payment: { ...settings.payment, gateway_provider: e.target.value }})}
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="stripe">Stripe</option>
                    <option value="square">Square</option>
                    <option value="moneris">Moneris</option>
                    <option value="paypal">PayPal</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Payment Hold Duration (days)
                  </label>
                  <input
                    type="number"
                    value={settings.payment.hold_duration_days}
                    onChange={(e) => setSettings({ ...settings, payment: { ...settings.payment, hold_duration_days: parseInt(e.target.value) }})}
                    min="0"
                    max="30"
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>
              </div>
              <div>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={settings.payment.auto_capture}
                    onChange={(e) => setSettings({ ...settings, payment: { ...settings.payment, auto_capture: e.target.checked }})}
                    className="w-4 h-4 text-accent-600 rounded"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Auto-capture payments</span>
                </label>
              </div>
            </div>
          )}

          {/* Notifications Tab */}
          {activeTab === 'notifications' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Notification Settings</h3>
              <div className="grid grid-cols-2 gap-6">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={settings.notifications.email_enabled}
                    onChange={(e) => setSettings({ ...settings, notifications: { ...settings.notifications, email_enabled: e.target.checked }})}
                    className="w-4 h-4 text-accent-600 rounded"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Email Notifications</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={settings.notifications.sms_enabled}
                    onChange={(e) => setSettings({ ...settings, notifications: { ...settings.notifications, sms_enabled: e.target.checked }})}
                    className="w-4 h-4 text-accent-600 rounded"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">SMS Notifications</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={settings.notifications.push_enabled}
                    onChange={(e) => setSettings({ ...settings, notifications: { ...settings.notifications, push_enabled: e.target.checked }})}
                    className="w-4 h-4 text-accent-600 rounded"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Push Notifications</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={settings.notifications.order_updates}
                    onChange={(e) => setSettings({ ...settings, notifications: { ...settings.notifications, order_updates: e.target.checked }})}
                    className="w-4 h-4 text-accent-600 rounded"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Order Updates</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={settings.notifications.marketing}
                    onChange={(e) => setSettings({ ...settings, notifications: { ...settings.notifications, marketing: e.target.checked }})}
                    className="w-4 h-4 text-accent-600 rounded"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Marketing Messages</span>
                </label>
              </div>
            </div>
          )}

          {/* SEO Tab */}
          {activeTab === 'seo' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{t('tenants:seo.title')}</h3>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('tenants:seo.metaTitle')}
                </label>
                <input
                  type="text"
                  value={settings.seo.meta_title}
                  onChange={(e) => setSettings({ ...settings, seo: { ...settings.seo, meta_title: e.target.value }})}
                  placeholder={t('tenants:seo.metaTitlePlaceholder')}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('tenants:seo.metaDescription')}
                </label>
                <textarea
                  value={settings.seo.meta_description}
                  onChange={(e) => setSettings({ ...settings, seo: { ...settings.seo, meta_description: e.target.value }})}
                  rows={3}
                  placeholder={t('tenants:seo.metaDescriptionPlaceholder')}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>
              <div>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={settings.seo.sitemap_enabled}
                    onChange={(e) => setSettings({ ...settings, seo: { ...settings.seo, sitemap_enabled: e.target.checked }})}
                    className="w-4 h-4 text-accent-600 rounded"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Generate Sitemap</span>
                </label>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('tenants:seo.robotsTxt')}
                </label>
                <textarea
                  value={settings.seo.robots_txt}
                  onChange={(e) => setSettings({ ...settings, seo: { ...settings.seo, robots_txt: e.target.value }})}
                  rows={4}
                  placeholder={t('tenants:seo.robotsTxtPlaceholder')}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white font-mono text-sm"
                />
              </div>
            </div>
          )}

          <div className="flex justify-end gap-4 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-accent-600 text-white rounded-lg hover:bg-accent-700"
            >
              {tenant ? 'Update' : 'Create'} Tenant
            </button>
          </div>
          </>
        </form>
      </div>
    </div>
  );
};

export default TenantManagement;