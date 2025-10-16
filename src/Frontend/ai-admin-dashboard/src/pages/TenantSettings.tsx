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
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!tenant) {
    return (
      <div className="p-6">
        <div className="bg-danger-50 border border-red-200 rounded-lg p-6">
          <p className="text-red-700">{t('settings:messages.tenantNotFound')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/dashboard/tenants')}
          className="mb-4 flex items-center gap-2 text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="w-4 h-4" />
          {t('settings:actions.backToTenants')}
        </button>
        
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-4">
              <Building2 className="w-8 h-8" />
              {tenant.name} {t('settings:titles.tenantSettings')}
            </h1>
            <p className="text-gray-600 mt-1">{t('settings:descriptions.tenantManagement')}</p>
          </div>
        </div>
      </div>

      {/* Alerts */}
      {success && (
        <div className="mb-4 p-6 bg-primary-50 border border-green-200 rounded-lg flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-primary-500" />
          <span className="text-primary-700">{success}</span>
        </div>
      )}

      {error && (
        <div className="mb-4 p-6 bg-danger-50 border border-red-200 rounded-lg flex items-center gap-2">
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
                ? 'border-blue-500 text-accent-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-200'
            }`}
          >
            {t('settings:tabs.general')}
          </button>
          <button
            onClick={() => setActiveTab('payment')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'payment'
                ? 'border-blue-500 text-accent-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-200'
            }`}
          >
            {t('settings:tabs.payment')}
          </button>
          <button
            onClick={() => setActiveTab('communication')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'communication'
                ? 'border-blue-500 text-accent-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-200'
            }`}
          >
            {t('settings:tabs.communication')}
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'general' && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-4">{t('settings:titles.generalInformation')}</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('settings:fields.tenantName')}
              </label>
              <p className="text-lg">{tenant.name}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('settings:fields.tenantCode')}
              </label>
              <p className="text-lg font-mono">{tenant.code}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('settings:fields.companyName')}
              </label>
              <p className="text-lg">{tenant.company_name || t('settings:messages.notSpecified')}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('settings:fields.businessNumber')}
              </label>
              <p className="text-lg">{tenant.business_number || t('settings:messages.notSpecified')}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('settings:fields.contactEmail')}
              </label>
              <p className="text-lg">{tenant.contact_email || t('settings:messages.notSpecified')}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('settings:fields.contactPhone')}
              </label>
              <p className="text-lg">{tenant.contact_phone || t('settings:messages.notSpecified')}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('settings:fields.status')}
              </label>
              <span className={`inline-flex px-2 py-1 rounded-full text-sm font-medium ${
                tenant.status === 'active'
                  ? 'bg-primary-100 text-primary-700'
                  : 'bg-gray-50 text-gray-700'
              }`}>
                {tenant.status}
              </span>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('settings:fields.subscriptionTier')}
              </label>
              <span className="inline-flex px-2 py-1 rounded-full text-sm font-medium bg-blue-100 text-accent-700">
                {tenant.subscription_tier}
              </span>
            </div>
          </div>
          
          {tenant.address && (
            <div className="mt-6">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('settings:fields.address')}
              </label>
              <p className="text-lg">
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