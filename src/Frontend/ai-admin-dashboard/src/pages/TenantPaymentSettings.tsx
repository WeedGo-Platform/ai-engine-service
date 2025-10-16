import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  CreditCard,
  Shield,
  Key,
  AlertCircle,
  CheckCircle,
  Settings,
  DollarSign,
  TrendingUp,
  Activity,
  Lock,
  Unlock,
  RefreshCw,
  Plus,
  Edit2,
  Trash2,
  ExternalLink,
  Info,
  ChevronRight,
  Download,
  Eye,
  EyeOff,
  Copy,
  Check,
  XCircle,
  Loader2,
  Zap,
  Server,
  Globe,
  Link,
  Save,
  X
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import paymentService from '../services/paymentService';
import tenantService from '../services/tenantService';

interface PaymentProvider {
  id: string;
  type: 'clover' | 'moneris' | 'stripe' | 'square' | 'interac';
  name: string;
  status: 'active' | 'inactive' | 'pending' | 'error';
  environment: 'sandbox' | 'production';
  merchantId?: string;
  lastSync?: string;
  healthStatus?: 'healthy' | 'degraded' | 'unavailable';
  credentials?: {
    hasApiKey: boolean;
    hasSecret: boolean;
    hasOAuth: boolean;
    oauthExpiry?: string;
  };
  fees?: {
    platformPercentage: number;
    platformFixed: number;
  };
  limits?: {
    dailyLimit?: number;
    transactionLimit?: number;
  };
}

interface PaymentStats {
  totalTransactions: number;
  totalVolume: number;
  successRate: number;
  averageTransaction: number;
  todayVolume: number;
  pendingSettlement: number;
  platformFees: number;
  netRevenue: number;
}

const TenantPaymentSettings: React.FC = () => {
  const { t } = useTranslation(['payments', 'common']);
  const { tenantId } = useParams<{ tenantId: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [tenant, setTenant] = useState<any>(null);
  const [providers, setProviders] = useState<PaymentProvider[]>([]);
  const [stats, setStats] = useState<PaymentStats | null>(null);
  const [activeTab, setActiveTab] = useState<'providers' | 'credentials' | 'fees' | 'webhooks' | 'analytics'>('providers');
  const [selectedProvider, setSelectedProvider] = useState<PaymentProvider | null>(null);
  const [showCredentialModal, setShowCredentialModal] = useState(false);
  const [showOAuthModal, setShowOAuthModal] = useState(false);
  const [isTestingConnection, setIsTestingConnection] = useState(false);
  const [credentialForm, setCredentialForm] = useState({
    apiKey: '',
    secret: '',
    merchantId: '',
    accessToken: '',
    environment: 'sandbox' as 'sandbox' | 'production'
  });
  const [copied, setCopied] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (tenantId) {
      loadTenantData();
      loadPaymentProviders();
      loadPaymentStats();
    }
  }, [tenantId]);

  const loadTenantData = async () => {
    try {
      const data = await tenantService.getTenant(tenantId!);
      setTenant(data);
    } catch (err) {
      setError(t('payments:settings.notifications.tenantLoadFailed'));
    }
  };

  const loadPaymentProviders = async () => {
    try {
      setLoading(true);
      // Mock data - replace with actual API call
      const mockProviders: PaymentProvider[] = [
        {
          id: '1',
          type: 'clover',
          name: 'Clover',
          status: 'active',
          environment: 'sandbox',
          merchantId: 'MERCHANT123',
          lastSync: '2024-01-15T10:30:00Z',
          healthStatus: 'healthy',
          credentials: {
            hasApiKey: true,
            hasSecret: true,
            hasOAuth: true,
            oauthExpiry: '2024-02-15T10:30:00Z'
          },
          fees: {
            platformPercentage: 2.0,
            platformFixed: 0.30
          },
          limits: {
            dailyLimit: 10000,
            transactionLimit: 1000
          }
        },
        {
          id: '2',
          type: 'moneris',
          name: 'Moneris',
          status: 'inactive',
          environment: 'production',
          healthStatus: 'unavailable',
          credentials: {
            hasApiKey: false,
            hasSecret: false,
            hasOAuth: false
          }
        }
      ];
      setProviders(mockProviders);
    } catch (err) {
      setError(t('payments:settings.notifications.providersLoadFailed'));
    } finally {
      setLoading(false);
    }
  };

  const loadPaymentStats = async () => {
    try {
      // Mock data - replace with actual API call
      const mockStats: PaymentStats = {
        totalTransactions: 1234,
        totalVolume: 98765.43,
        successRate: 94.5,
        averageTransaction: 80.07,
        todayVolume: 3456.78,
        pendingSettlement: 1234.56,
        platformFees: 234.56,
        netRevenue: 98530.87
      };
      setStats(mockStats);
    } catch (err) {
      console.error('Failed to load payment stats:', err);
    }
  };

  const handleTestConnection = async (provider: PaymentProvider) => {
    setIsTestingConnection(true);
    try {
      // API call to test connection
      await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate API call
      setSuccess(t('payments:settings.notifications.connectionTestSuccess', { providerName: provider.name }));
    } catch (err) {
      setError(t('payments:settings.notifications.connectionTestFailed', { providerName: provider.name }));
    } finally {
      setIsTestingConnection(false);
    }
  };

  const handleCopyWebhookUrl = (provider: PaymentProvider) => {
    const webhookUrl = `https://api.weedgo.ai/webhooks/${provider.type}/${tenantId}/${provider.id}`;
    navigator.clipboard.writeText(webhookUrl);
    setCopied(provider.id);
    setTimeout(() => setCopied(null), 2000);
  };

  const handleUpdateCredentials = async () => {
    if (!selectedProvider || !tenantId) return;
    
    try {
      setLoading(true);
      setError(null);
      
      // Call the appropriate API based on provider type
      if (selectedProvider.type === 'clover') {
        await paymentService.configureCloverCredentials(tenantId, {
          api_key: credentialForm.apiKey,
          secret: credentialForm.secret,
          merchant_id: credentialForm.merchantId,
          access_token: credentialForm.accessToken,
          environment: credentialForm.environment
        });
      } else {
        // For other providers, use the generic update endpoint
        await paymentService.updateProvider(tenantId, selectedProvider.id, {
          credentials: {
            apiKey: credentialForm.apiKey,
            secret: credentialForm.secret,
            merchantId: credentialForm.merchantId,
            environment: credentialForm.environment
          }
        });
      }
      
      setSuccess(t('payments:settings.notifications.credentialsUpdated', { providerName: selectedProvider.name }));
      setShowCredentialModal(false);
      
      // Reset form
      setCredentialForm({
        apiKey: '',
        secret: '',
        merchantId: '',
        accessToken: '',
        environment: 'sandbox'
      });
      
      // Refresh providers
      await loadPaymentProviders();
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      // Handle error properly - extract message from error object
      let errorMessage = t('payments:settings.notifications.credentialsUpdateFailed');
      if (err.response?.data?.detail) {
        if (typeof err.response.data.detail === 'string') {
          errorMessage = err.response.data.detail;
        } else if (Array.isArray(err.response.data.detail)) {
          // Handle validation errors array
          errorMessage = err.response.data.detail
            .map((e: any) => e.msg || e.message || 'Validation error')
            .join(', ');
        } else if (typeof err.response.data.detail === 'object') {
          errorMessage = err.response.data.detail.message || JSON.stringify(err.response.data.detail);
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      setError(errorMessage);
      setTimeout(() => setError(null), 5000);
    } finally {
      setLoading(false);
    }
  };

  const getProviderIcon = (type: string) => {
    switch (type) {
      case 'clover':
        return '🍀';
      case 'moneris':
        return '💳';
      case 'stripe':
        return '💰';
      case 'square':
        return '⬜';
      case 'interac':
        return '🏦';
      default:
        return '💳';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
      case 'healthy':
        return 'text-primary-500';
      case 'degraded':
      case 'pending':
        return 'text-yellow-500';
      case 'inactive':
      case 'unavailable':
      case 'error':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-6">
          <button
            onClick={() => navigate('/dashboard/tenants')}
            className="p-2 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg"
          >
            <ChevronRight className="w-5 h-5 rotate-180" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              {t('payments:settings.title')}
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              {tenant?.name} - {tenant?.code}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <button className="px-4 py-2 bg-accent-600 text-white rounded-lg hover:bg-accent-700 flex items-center gap-2">
            <Plus className="w-4 h-4" />
            {t('payments:settings.addProvider')}
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">{t('payments:settings.stats.totalVolume')}</span>
              <DollarSign className="w-4 h-4 text-primary-500" />
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              ${stats.totalVolume.toLocaleString()}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {t('payments:settings.stats.transactionsCount', { count: stats.totalTransactions })}
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">{t('payments:settings.stats.successRate')}</span>
              <TrendingUp className="w-4 h-4 text-accent-500" />
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {stats.successRate}%
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {t('payments:settings.stats.avgTransaction', { amount: stats.averageTransaction.toFixed(2) })}
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">{t('payments:settings.stats.todayVolume')}</span>
              <Activity className="w-4 h-4 text-purple-500" />
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              ${stats.todayVolume.toLocaleString()}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {t('payments:settings.stats.pendingSettlement', { amount: stats.pendingSettlement.toFixed(2) })}
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">{t('payments:settings.stats.netRevenue')}</span>
              <Zap className="w-4 h-4 text-yellow-500" />
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              ${stats.netRevenue.toLocaleString()}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {t('payments:settings.stats.platformFees', { amount: stats.platformFees.toFixed(2) })}
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="flex gap-6">
          {[
            { id: 'providers', label: t('payments:settings.tabs.providers'), icon: CreditCard },
            { id: 'credentials', label: t('payments:settings.tabs.credentials'), icon: Key },
            { id: 'fees', label: t('payments:settings.tabs.feesLimits'), icon: DollarSign },
            { id: 'webhooks', label: t('payments:settings.tabs.webhooks'), icon: Link },
            { id: 'analytics', label: t('payments:settings.tabs.analytics'), icon: TrendingUp }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-1 py-3 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-accent-600 dark:text-blue-400'
                  : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6">
        {activeTab === 'providers' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold mb-4">{t('payments:settings.providersTab.title')}</h3>

            {providers.map((provider) => (
              <div
                key={provider.id}
                className="border border-gray-200 dark:border-gray-700 rounded-lg p-6"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-6">
                    <div className="text-3xl">{getProviderIcon(provider.type)}</div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="font-semibold text-gray-900 dark:text-white">
                          {provider.name}
                        </h4>
                        <span className={`text-sm ${getStatusColor(provider.status)}`}>
                          • {provider.status}
                        </span>
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        {provider.environment === 'production' ? (
                          <span className="flex items-center gap-1">
                            <Globe className="w-3 h-3" />
                            {t('payments:settings.providersTab.production')}
                          </span>
                        ) : (
                          <span className="flex items-center gap-1">
                            <Server className="w-3 h-3" />
                            {t('payments:settings.providersTab.sandbox')}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        {t('payments:settings.providersTab.healthStatus')}
                      </div>
                      <div className={`text-sm font-medium ${getStatusColor(provider.healthStatus || 'unknown')}`}>
                        {provider.healthStatus || t('payments:settings.providersTab.unknown')}
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <button
                        onClick={() => handleTestConnection(provider)}
                        disabled={isTestingConnection}
                        className="p-2 text-gray-600 hover:text-accent-600 dark:text-gray-400 dark:hover:text-blue-400"
                        title={t('payments:settings.providersTab.testConnection')}
                      >
                        {isTestingConnection ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Activity className="w-4 h-4" />
                        )}
                      </button>
                      <button
                        onClick={() => {
                          setSelectedProvider(provider);
                          setShowCredentialModal(true);
                        }}
                        className="p-2 text-gray-600 hover:text-purple-600 dark:text-gray-400 dark:hover:text-purple-400"
                        title={t('payments:settings.providersTab.configure')}
                      >
                        <Settings className="w-4 h-4" />
                      </button>
                      <button
                        className="p-2 text-gray-600 hover:text-danger-600 dark:text-gray-400 dark:hover:text-red-400"
                        title={t('payments:settings.providersTab.remove')}
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>

                {provider.merchantId && (
                  <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                    <div className="grid grid-cols-3 gap-6 text-sm">
                      <div>
                        <span className="text-gray-600 dark:text-gray-400">{t('payments:settings.providersTab.merchantId')}</span>
                        <span className="ml-2 font-mono text-gray-900 dark:text-white">
                          {provider.merchantId}
                        </span>
                      </div>
                      {provider.lastSync && (
                        <div>
                          <span className="text-gray-600 dark:text-gray-400">{t('payments:settings.providersTab.lastSync')}</span>
                          <span className="ml-2 text-gray-900 dark:text-white">
                            {new Date(provider.lastSync).toLocaleDateString()}
                          </span>
                        </div>
                      )}
                      {provider.credentials?.oauthExpiry && (
                        <div>
                          <span className="text-gray-600 dark:text-gray-400">{t('payments:settings.providersTab.oauthExpires')}</span>
                          <span className="ml-2 text-gray-900 dark:text-white">
                            {new Date(provider.credentials.oauthExpiry).toLocaleDateString()}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}

            {providers.length === 0 && (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                {t('payments:settings.providersTab.noProviders')}
              </div>
            )}
          </div>
        )}

        {activeTab === 'credentials' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold mb-4">{t('payments:settings.credentialsTab.title')}</h3>

            <div className="bg-warning-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-6">
              <div className="flex gap-2">
                <Shield className="w-5 h-5 text-warning-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-yellow-700 dark:text-yellow-300">
                  <strong>{t('payments:settings.credentialsTab.securityNotice')}</strong> {t('payments:settings.credentialsTab.securityMessage')}
                </div>
              </div>
            </div>

            {providers.map((provider) => (
              <div key={provider.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                    {getProviderIcon(provider.type)} {provider.name}
                  </h4>
                  <button
                    onClick={() => {
                      setSelectedProvider(provider);
                      setShowCredentialModal(true);
                    }}
                    className="text-sm text-accent-600 hover:text-accent-700 dark:text-blue-400"
                  >
                    {t('payments:settings.credentialsTab.updateCredentials')}
                  </button>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between py-2">
                    <span className="text-sm text-gray-600 dark:text-gray-400">{t('payments:settings.credentialsTab.apiKey')}</span>
                    <span className="flex items-center gap-2">
                      {provider.credentials?.hasApiKey ? (
                        <CheckCircle className="w-4 h-4 text-primary-500" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-500" />
                      )}
                      <span className="text-sm">
                        {provider.credentials?.hasApiKey ? t('payments:settings.credentialsTab.configured') : t('payments:settings.credentialsTab.notConfigured')}
                      </span>
                    </span>
                  </div>

                  <div className="flex items-center justify-between py-2">
                    <span className="text-sm text-gray-600 dark:text-gray-400">{t('payments:settings.credentialsTab.secretKey')}</span>
                    <span className="flex items-center gap-2">
                      {provider.credentials?.hasSecret ? (
                        <CheckCircle className="w-4 h-4 text-primary-500" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-500" />
                      )}
                      <span className="text-sm">
                        {provider.credentials?.hasSecret ? t('payments:settings.credentialsTab.configured') : t('payments:settings.credentialsTab.notConfigured')}
                      </span>
                    </span>
                  </div>

                  {provider.type === 'clover' && (
                    <div className="flex items-center justify-between py-2">
                      <span className="text-sm text-gray-600 dark:text-gray-400">{t('payments:settings.credentialsTab.oauthToken')}</span>
                      <span className="flex items-center gap-2">
                        {provider.credentials?.hasOAuth ? (
                          <>
                            <CheckCircle className="w-4 h-4 text-primary-500" />
                            <span className="text-sm">
                              {t('payments:settings.credentialsTab.connected')}
                              {provider.credentials.oauthExpiry && (
                                <span className="text-gray-500 ml-1">
                                  ({t('payments:settings.credentialsTab.expires', { date: new Date(provider.credentials.oauthExpiry).toLocaleDateString() })})
                                </span>
                              )}
                            </span>
                          </>
                        ) : (
                          <>
                            <XCircle className="w-4 h-4 text-red-500" />
                            <button
                              onClick={() => {
                                setSelectedProvider(provider);
                                setShowOAuthModal(true);
                              }}
                              className="text-sm text-accent-600 hover:text-accent-700"
                            >
                              {t('payments:settings.credentialsTab.connectOAuth')}
                            </button>
                          </>
                        )}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'fees' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold mb-4">{t('payments:settings.feesTab.title')}</h3>

            {providers.map((provider) => (
              <div key={provider.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                <h4 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  {getProviderIcon(provider.type)} {provider.name}
                </h4>

                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                      {t('payments:settings.feesTab.platformFees')}
                    </h5>
                    <div className="space-y-3">
                      <div>
                        <label className="text-sm text-gray-600 dark:text-gray-400">
                          {t('payments:settings.feesTab.percentageFee')}
                        </label>
                        <div className="flex items-center gap-2 mt-1">
                          <input
                            type="number"
                            value={provider.fees?.platformPercentage || 2.0}
                            step="0.01"
                            min="0"
                            max="10"
                            className="w-24 px-3 py-1 border border-gray-200 dark:border-gray-600 rounded-lg dark:bg-gray-700"
                          />
                          <span className="text-sm text-gray-600 dark:text-gray-400">%</span>
                        </div>
                      </div>
                      <div>
                        <label className="text-sm text-gray-600 dark:text-gray-400">
                          {t('payments:settings.feesTab.fixedFee')}
                        </label>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-sm text-gray-600 dark:text-gray-400">$</span>
                          <input
                            type="number"
                            value={provider.fees?.platformFixed || 0.30}
                            step="0.01"
                            min="0"
                            className="w-24 px-3 py-1 border border-gray-200 dark:border-gray-600 rounded-lg dark:bg-gray-700"
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                      {t('payments:settings.feesTab.transactionLimits')}
                    </h5>
                    <div className="space-y-3">
                      <div>
                        <label className="text-sm text-gray-600 dark:text-gray-400">
                          {t('payments:settings.feesTab.dailyLimit')}
                        </label>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-sm text-gray-600 dark:text-gray-400">$</span>
                          <input
                            type="number"
                            value={provider.limits?.dailyLimit || 10000}
                            step="100"
                            min="0"
                            className="w-32 px-3 py-1 border border-gray-200 dark:border-gray-600 rounded-lg dark:bg-gray-700"
                          />
                        </div>
                      </div>
                      <div>
                        <label className="text-sm text-gray-600 dark:text-gray-400">
                          {t('payments:settings.feesTab.perTransactionLimit')}
                        </label>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-sm text-gray-600 dark:text-gray-400">$</span>
                          <input
                            type="number"
                            value={provider.limits?.transactionLimit || 1000}
                            step="10"
                            min="0"
                            className="w-32 px-3 py-1 border border-gray-200 dark:border-gray-600 rounded-lg dark:bg-gray-700"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <button className="px-4 py-2 bg-accent-600 text-white rounded-lg hover:bg-accent-700 text-sm">
                    {t('payments:settings.feesTab.saveChanges')}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'webhooks' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold mb-4">{t('payments:settings.webhooksTab.title')}</h3>

            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
              <div className="flex gap-2">
                <Info className="w-5 h-5 text-accent-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-accent-700 dark:text-blue-300">
                  {t('payments:settings.webhooksTab.infoMessage')}
                </div>
              </div>
            </div>

            {providers.map((provider) => (
              <div key={provider.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                <h4 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  {getProviderIcon(provider.type)} {provider.name}
                </h4>

                <div className="space-y-3">
                  <div>
                    <label className="text-sm text-gray-600 dark:text-gray-400">
                      {t('payments:settings.webhooksTab.webhookUrl')}
                    </label>
                    <div className="flex gap-2 mt-1">
                      <input
                        type="text"
                        readOnly
                        value={`https://api.weedgo.ai/webhooks/${provider.type}/${tenantId}/${provider.id}`}
                        className="flex-1 px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-600 rounded-lg font-mono text-sm"
                      />
                      <button
                        onClick={() => handleCopyWebhookUrl(provider)}
                        className="px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
                      >
                        {copied === provider.id ? (
                          <Check className="w-4 h-4 text-primary-500" />
                        ) : (
                          <Copy className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="text-sm text-gray-600 dark:text-gray-400">
                      {t('payments:settings.webhooksTab.webhookSecret')}
                    </label>
                    <div className="flex gap-2 mt-1">
                      <input
                        type="password"
                        placeholder={t('payments:settings.webhooksTab.webhookSecretPlaceholder')}
                        className="flex-1 px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg dark:bg-gray-700"
                      />
                      <button className="px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
                        <Eye className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="text-sm text-gray-600 dark:text-gray-400">
                      {t('payments:settings.webhooksTab.eventsToSubscribe')}
                    </label>
                    <div className="grid grid-cols-2 gap-2 mt-2">
                      {[
                        t('payments:settings.webhooksTab.eventTypes.paymentCompleted'),
                        t('payments:settings.webhooksTab.eventTypes.paymentFailed'),
                        t('payments:settings.webhooksTab.eventTypes.refundCreated'),
                        t('payments:settings.webhooksTab.eventTypes.disputeCreated')
                      ].map((event) => (
                        <label key={event} className="flex items-center gap-2">
                          <input type="checkbox" className="rounded" defaultChecked />
                          <span className="text-sm">{event}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold mb-4">{t('payments:settings.analyticsTab.title')}</h3>

            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-4">
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t('payments:settings.analyticsTab.transactionVolume')}
                </h4>
                <div className="h-48 bg-gray-50 dark:bg-gray-900 rounded-lg flex items-center justify-center">
                  <span className="text-gray-500 dark:text-gray-400">{t('payments:settings.analyticsTab.chartPlaceholder')}</span>
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t('payments:settings.analyticsTab.successRateByProvider')}
                </h4>
                <div className="h-48 bg-gray-50 dark:bg-gray-900 rounded-lg flex items-center justify-center">
                  <span className="text-gray-500 dark:text-gray-400">{t('payments:settings.analyticsTab.chartPlaceholder')}</span>
                </div>
              </div>
            </div>

            <div className="mt-6">
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                {t('payments:settings.analyticsTab.recentTransactions')}
              </h4>
              <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                <table className="w-full">
                  <thead className="bg-gray-50 dark:bg-gray-900">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400">
                        {t('payments:settings.analyticsTab.tableHeaders.transactionId')}
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400">
                        {t('payments:settings.analyticsTab.tableHeaders.amount')}
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400">
                        {t('payments:settings.analyticsTab.tableHeaders.provider')}
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400">
                        {t('payments:settings.analyticsTab.tableHeaders.status')}
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400">
                        {t('payments:settings.analyticsTab.tableHeaders.date')}
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    <tr>
                      <td colSpan={5} className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                        {t('payments:settings.analyticsTab.noRecentTransactions')}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Credential Update Modal */}
      {showCredentialModal && selectedProvider && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                {t('payments:settings.credentialModal.title', { providerName: selectedProvider.name })}
              </h3>
              <button
                onClick={() => {
                  setShowCredentialModal(false);
                  setCredentialForm({
                    apiKey: '',
                    secret: '',
                    merchantId: '',
                    accessToken: '',
                    environment: 'sandbox'
                  });
                }}
                className="p-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              {/* Environment Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('payments:settings.credentialModal.environment')}
                </label>
                <select
                  value={credentialForm.environment}
                  onChange={(e) => setCredentialForm({ ...credentialForm, environment: e.target.value as 'sandbox' | 'production' })}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="sandbox">{t('payments:settings.credentialModal.environmentOptions.sandbox')}</option>
                  <option value="production">{t('payments:settings.credentialModal.environmentOptions.production')}</option>
                </select>
              </div>

              {/* API Key */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('payments:settings.credentialModal.apiKey')}
                </label>
                <input
                  type="password"
                  value={credentialForm.apiKey}
                  onChange={(e) => setCredentialForm({ ...credentialForm, apiKey: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder={t('payments:settings.credentialModal.apiKeyPlaceholder')}
                />
              </div>

              {/* Secret Key */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('payments:settings.credentialModal.secretKey')}
                </label>
                <input
                  type="password"
                  value={credentialForm.secret}
                  onChange={(e) => setCredentialForm({ ...credentialForm, secret: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder={t('payments:settings.credentialModal.secretKeyPlaceholder')}
                />
              </div>

              {/* Merchant ID (for Clover) */}
              {selectedProvider.type === 'clover' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      {t('payments:settings.credentialModal.merchantId')}
                    </label>
                    <input
                      type="text"
                      value={credentialForm.merchantId}
                      onChange={(e) => setCredentialForm({ ...credentialForm, merchantId: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      placeholder={t('payments:settings.credentialModal.merchantIdPlaceholder')}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      {t('payments:settings.credentialModal.accessToken')}
                    </label>
                    <input
                      type="password"
                      value={credentialForm.accessToken}
                      onChange={(e) => setCredentialForm({ ...credentialForm, accessToken: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      placeholder={t('payments:settings.credentialModal.accessTokenPlaceholder')}
                    />
                  </div>
                </>
              )}

              {/* Security Notice */}
              <div className="bg-warning-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                <div className="flex gap-2">
                  <Shield className="w-4 h-4 text-warning-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
                  <div className="text-xs text-yellow-700 dark:text-yellow-300">
                    {t('payments:settings.credentialModal.securityWarning')}
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-4 mt-6">
              <button
                onClick={() => {
                  setShowCredentialModal(false);
                  setCredentialForm({
                    apiKey: '',
                    secret: '',
                    merchantId: '',
                    accessToken: '',
                    environment: 'sandbox'
                  });
                }}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg"
              >
                {t('payments:settings.credentialModal.cancel')}
              </button>
              <button
                onClick={handleUpdateCredentials}
                disabled={loading || !credentialForm.apiKey || !credentialForm.secret}
                className="px-4 py-2 bg-accent-600 text-white rounded-lg hover:bg-accent-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    {t('payments:settings.credentialModal.updating')}
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    {t('payments:settings.credentialModal.updateButton')}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Success/Error Messages */}
      {success && (
        <div className="fixed bottom-4 right-4 bg-primary-500 text-white px-4 py-2 rounded-lg border border-gray-200 flex items-center gap-2">
          <CheckCircle className="w-5 h-5" />
          {success}
        </div>
      )}
      
      {error && (
        <div className="fixed bottom-4 right-4 bg-danger-500 text-white px-4 py-2 rounded-lg border border-gray-200 flex items-center gap-2">
          <AlertCircle className="w-5 h-5" />
          {error}
        </div>
      )}
    </div>
  );
};

export default TenantPaymentSettings;