import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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

const TenantSettings: React.FC = () => {
  const { tenantCode } = useParams<{ tenantCode: string }>();
  const navigate = useNavigate();
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [paymentSettings, setPaymentSettings] = useState<PaymentProviderSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'general' | 'payment'>('general');

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
      setTenant(tenantData);
      setPaymentSettings(paymentData);
    } catch (err) {
      setError('Failed to load tenant settings');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSavePaymentSettings = async (settings: PaymentProviderSettings) => {
    try {
      await paymentService.updateTenantPaymentSettings(tenant!.id, settings);
      setPaymentSettings(settings);
      setSuccess('Payment settings updated successfully');
    } catch (err) {
      setError('Failed to update payment settings');
      throw err;
    }
  };

  const handleValidateProvider = async (provider: string) => {
    try {
      const result = await paymentService.validatePaymentProvider(tenant!.id, provider);
      if (result.valid) {
        setSuccess(`${provider} configuration is valid`);
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
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700">Tenant not found</p>
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
          Back to Tenants
        </button>
        
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <Building2 className="w-8 h-8" />
              {tenant.name} Settings
            </h1>
            <p className="text-gray-600 mt-1">Manage tenant configuration and payment settings</p>
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
            onClick={() => setActiveTab('payment')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'payment'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Payment Settings
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
                Tenant Name
              </label>
              <p className="text-lg">{tenant.name}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tenant Code
              </label>
              <p className="text-lg font-mono">{tenant.code}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Company Name
              </label>
              <p className="text-lg">{tenant.company_name || 'Not specified'}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Business Number
              </label>
              <p className="text-lg">{tenant.business_number || 'Not specified'}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Contact Email
              </label>
              <p className="text-lg">{tenant.contact_email || 'Not specified'}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Contact Phone
              </label>
              <p className="text-lg">{tenant.contact_phone || 'Not specified'}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <span className={`inline-flex px-2 py-1 rounded-full text-sm font-medium ${
                tenant.status === 'active' 
                  ? 'bg-green-100 text-green-700'
                  : 'bg-gray-100 text-gray-700'
              }`}>
                {tenant.status}
              </span>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Subscription Tier
              </label>
              <span className="inline-flex px-2 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-700">
                {tenant.subscription_tier}
              </span>
            </div>
          </div>
          
          {tenant.address && (
            <div className="mt-6">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Address
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
    </div>
  );
};

export default TenantSettings;