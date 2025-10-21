import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Building2,
  Settings,
  ArrowLeft,
  Save,
  AlertCircle
} from 'lucide-react';
import tenantService, { Tenant } from '../services/tenantService';
import paymentService, { PaymentProviderSettings } from '../services/paymentService';
import PaymentProviderSettingsComponent from '../components/PaymentProviderSettings';
import CommunicationSettingsComponent, { CommunicationSettings } from '../components/CommunicationSettings';
import communicationService from '../services/communicationService';
import { usePersistentTab } from '../hooks/usePersistentState';

const TenantSettings: React.FC = () => {
  const { t } = useTranslation(['settings', 'common', 'errors']);
  const { tenantCode } = useParams<{ tenantCode: string }>();
  const navigate = useNavigate();
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [paymentSettings, setPaymentSettings] = useState<PaymentProviderSettings | null>(null);
  const [communicationSettings, setCommunicationSettings] = useState<CommunicationSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [activeTab, setActiveTab] = usePersistentTab<'general' | 'payment' | 'communication'>('tenant_settings', 'general');

  useEffect(() => {
    if (tenantCode) {
      loadTenantData();
    }
  }, [tenantCode]);

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

  const loadTenantData = async () => {
    try {
      setLoading(true);
      const tenantData = await tenantService.getTenantByCode(tenantCode!);
      const paymentData = await paymentService.getTenantPaymentSettings(tenantData.id);
      const communicationData = await communicationService.getTenantCommunicationSettings(tenantData.id);
      setTenant(tenantData);
      setPaymentSettings(paymentData);
      setCommunicationSettings(communicationData);
    } catch (err) {
      setError(t('settings:messages.error.loadSettings'));
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSavePaymentSettings = async (settings: PaymentProviderSettings) => {
    try {
      await paymentService.updateTenantPaymentSettings(tenant!.id, settings);
      setPaymentSettings(settings);
      setSuccess(t('settings:messages.success.paymentSettingsUpdated'));
    } catch (err) {
      setError(t('settings:messages.error.updatePaymentSettings'));
      throw err;
    }
  };

  const handleValidateProvider = async (provider: string) => {
    try {
      const result = await paymentService.validatePaymentProvider(tenant!.id, provider);
      if (result.valid) {
        setSuccess(`${provider} ${t('settings:messages.success.configurationValid')}`);
      } else {
        setError(result.message);
      }
    } catch (err) {
      throw err;
    }
  };

  const handleSaveCommunicationSettings = async (settings: CommunicationSettings) => {
    try {
      await communicationService.updateTenantCommunicationSettings(tenant!.id, settings);
      setCommunicationSettings(settings);
      setSuccess(t('settings:messages.success.communicationSettingsUpdated'));
    } catch (err) {
      setError(t('settings:messages.error.updateCommunicationSettings'));
      throw err;
    }
  };

  const handleValidateCommunicationChannel = async (channel: 'sms' | 'email') => {
    try {
      const result = await communicationService.validateCommunicationChannel(tenant!.id, channel);
      if (result.valid) {
        setSuccess(`${channel.toUpperCase()} ${t('settings:messages.success.configurationValid')}`);
      } else {
        setError(result.message);
      }
    } catch (err) {
      throw err;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50 dark:bg-gray-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 dark:border-primary-400"></div>
      </div>
    );
  }

  if (!tenant) {
    return (
      <div className="p-6 bg-gray-50 dark:bg-gray-900 min-h-screen">
        <div className="bg-danger-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg p-6">
          <p className="text-red-700 dark:text-red-300">{t('settings:messages.tenantNotFound')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 bg-gray-50 dark:bg-gray-900 min-h-screen">
      {/* Header */}
      <div className="mb-4 sm:mb-6">
        <button
          onClick={() => navigate('/dashboard/tenants')}
          className="mb-3 sm:mb-4 flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white active:scale-95 transition-all touch-manipulation"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>{t('settings:actions.backToTenants')}</span>
        </button>

        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-0">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold flex items-center gap-3 sm:gap-4 text-gray-900 dark:text-white">
              <Building2 className="w-6 h-6 sm:w-8 sm:h-8" />
              <span className="line-clamp-1">{tenant.name} {t('settings:titles.tenantSettings')}</span>
            </h1>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{t('settings:descriptions.tenantManagement')}</p>
          </div>
        </div>
      </div>

      {/* Alerts */}
      {success && (
        <div className="mb-4 p-4 sm:p-6 bg-primary-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 rounded-lg flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-primary-500 dark:text-green-400" />
          <span className="text-sm sm:text-base text-primary-700 dark:text-green-300">{success}</span>
        </div>
      )}

      {error && (
        <div className="mb-4 p-4 sm:p-6 bg-danger-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-red-500 dark:text-red-400" />
          <span className="text-sm sm:text-base text-red-700 dark:text-red-300">{error}</span>
        </div>
      )}

      {/* Tabs */}
      <div className="mb-4 sm:mb-6 border-b border-gray-200 dark:border-gray-700 overflow-x-auto -mx-4 sm:mx-0 px-4 sm:px-0">
        <nav className="-mb-px flex space-x-4 sm:space-x-8 min-w-max sm:min-w-0">
          <button
            onClick={() => setActiveTab('general')}
            className={`py-2 px-1 border-b-2 font-medium text-xs sm:text-sm whitespace-nowrap transition-colors ${
              activeTab === 'general'
                ? 'border-blue-500 dark:border-primary-400 text-accent-600 dark:text-primary-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-200 dark:hover:border-gray-600'
            }`}
          >
            {t('settings:tabs.general')}
          </button>
          <button
            onClick={() => setActiveTab('payment')}
            className={`py-2 px-1 border-b-2 font-medium text-xs sm:text-sm whitespace-nowrap transition-colors ${
              activeTab === 'payment'
                ? 'border-blue-500 dark:border-primary-400 text-accent-600 dark:text-primary-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-200 dark:hover:border-gray-600'
            }`}
          >
            {t('settings:tabs.payment')}
          </button>
          <button
            onClick={() => setActiveTab('communication')}
            className={`py-2 px-1 border-b-2 font-medium text-xs sm:text-sm whitespace-nowrap transition-colors ${
              activeTab === 'communication'
                ? 'border-blue-500 dark:border-primary-400 text-accent-600 dark:text-primary-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-200 dark:hover:border-gray-600'
            }`}
          >
            {t('settings:tabs.communication')}
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'general' && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 sm:p-6 transition-colors">
          <h2 className="text-lg sm:text-xl font-semibold mb-3 sm:mb-4 text-gray-900 dark:text-white">{t('settings:titles.generalInformation')}</h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t('settings:fields.tenantName')}
              </label>
              <p className="text-lg text-gray-900 dark:text-white">{tenant.name}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t('settings:fields.tenantCode')}
              </label>
              <p className="text-lg font-mono text-gray-900 dark:text-white">{tenant.code}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t('settings:fields.companyName')}
              </label>
              <p className="text-lg text-gray-900 dark:text-white">{tenant.company_name || t('settings:messages.notSpecified')}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t('settings:fields.businessNumber')}
              </label>
              <p className="text-lg text-gray-900 dark:text-white">{tenant.business_number || t('settings:messages.notSpecified')}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t('settings:fields.contactEmail')}
              </label>
              <p className="text-lg text-gray-900 dark:text-white">{tenant.contact_email || t('settings:messages.notSpecified')}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t('settings:fields.contactPhone')}
              </label>
              <p className="text-lg text-gray-900 dark:text-white">{tenant.contact_phone || t('settings:messages.notSpecified')}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t('settings:fields.status')}
              </label>
              <span className={`inline-flex px-2 py-1 rounded-full text-sm font-medium ${
                tenant.status === 'active'
                  ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                  : 'bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
              }`}>
                {tenant.status}
              </span>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t('settings:fields.subscriptionTier')}
              </label>
              <span className="inline-flex px-2 py-1 rounded-full text-sm font-medium bg-blue-100 dark:bg-blue-900/30 text-accent-700 dark:text-blue-300">
                {tenant.subscription_tier}
              </span>
            </div>
          </div>

          {tenant.address && (
            <div className="mt-4 sm:mt-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t('settings:fields.address')}
              </label>
              <p className="text-base sm:text-lg text-gray-900 dark:text-white">
                {tenant.address.street}<br />
                {tenant.address.city}, {tenant.address.province} {tenant.address.postal_code}<br />
                {tenant.address.country}
              </p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'payment' && paymentSettings && (
        <PaymentProviderSettingsComponent
          tenantId={tenant?.id || ''}
          settings={paymentSettings}
          onSave={handleSavePaymentSettings}
          onValidate={handleValidateProvider}
        />
      )}

      {activeTab === 'communication' && communicationSettings && (
        <CommunicationSettingsComponent
          tenantId={tenant?.id || ''}
          settings={communicationSettings}
          onSave={handleSaveCommunicationSettings}
          onValidate={handleValidateCommunicationChannel}
        />
      )}
    </div>
  );
};

export default TenantSettings;