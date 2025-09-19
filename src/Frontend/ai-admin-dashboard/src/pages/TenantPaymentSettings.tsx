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
      setError('Failed to load tenant data');
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
      setError('Failed to load payment providers');
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
      setSuccess(`${provider.name} connection test successful`);
    } catch (err) {
      setError(`${provider.name} connection test failed`);
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
      
      setSuccess(`Credentials updated successfully for ${selectedProvider.name}`);
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
      let errorMessage = 'Failed to update credentials';
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
              Payment Settings
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              {tenant?.name} - {tenant?.code}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <button className="px-4 py-2 bg-accent-600 text-white rounded-lg hover:bg-accent-700 flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Add Provider
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">Total Volume</span>
              <DollarSign className="w-4 h-4 text-primary-500" />
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              ${stats.totalVolume.toLocaleString()}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {stats.totalTransactions} transactions
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">Success Rate</span>
              <TrendingUp className="w-4 h-4 text-accent-500" />
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {stats.successRate}%
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Avg ${stats.averageTransaction.toFixed(2)}
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">Today's Volume</span>
              <Activity className="w-4 h-4 text-purple-500" />
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              ${stats.todayVolume.toLocaleString()}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Pending: ${stats.pendingSettlement.toFixed(2)}
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">Net Revenue</span>
              <Zap className="w-4 h-4 text-yellow-500" />
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              ${stats.netRevenue.toLocaleString()}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Fees: ${stats.platformFees.toFixed(2)}
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="flex gap-6">
          {[
            { id: 'providers', label: 'Providers', icon: CreditCard },
            { id: 'credentials', label: 'Credentials', icon: Key },
            { id: 'fees', label: 'Fees & Limits', icon: DollarSign },
            { id: 'webhooks', label: 'Webhooks', icon: Link },
            { id: 'analytics', label: 'Analytics', icon: TrendingUp }
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
            <h3 className="text-lg font-semibold mb-4">Payment Providers</h3>
            
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
                            Production
                          </span>
                        ) : (
                          <span className="flex items-center gap-1">
                            <Server className="w-3 h-3" />
                            Sandbox
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        Health Status
                      </div>
                      <div className={`text-sm font-medium ${getStatusColor(provider.healthStatus || 'unknown')}`}>
                        {provider.healthStatus || 'Unknown'}
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <button
                        onClick={() => handleTestConnection(provider)}
                        disabled={isTestingConnection}
                        className="p-2 text-gray-600 hover:text-accent-600 dark:text-gray-400 dark:hover:text-blue-400"
                        title="Test Connection"
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
                        title="Configure"
                      >
                        <Settings className="w-4 h-4" />
                      </button>
                      <button
                        className="p-2 text-gray-600 hover:text-danger-600 dark:text-gray-400 dark:hover:text-red-400"
                        title="Remove"
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
                        <span className="text-gray-600 dark:text-gray-400">Merchant ID:</span>
                        <span className="ml-2 font-mono text-gray-900 dark:text-white">
                          {provider.merchantId}
                        </span>
                      </div>
                      {provider.lastSync && (
                        <div>
                          <span className="text-gray-600 dark:text-gray-400">Last Sync:</span>
                          <span className="ml-2 text-gray-900 dark:text-white">
                            {new Date(provider.lastSync).toLocaleDateString()}
                          </span>
                        </div>
                      )}
                      {provider.credentials?.oauthExpiry && (
                        <div>
                          <span className="text-gray-600 dark:text-gray-400">OAuth Expires:</span>
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
                No payment providers configured. Add one to start accepting payments.
              </div>
            )}
          </div>
        )}

        {activeTab === 'credentials' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold mb-4">API Credentials</h3>
            
            <div className="bg-warning-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-6">
              <div className="flex gap-2">
                <Shield className="w-5 h-5 text-warning-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-yellow-700 dark:text-yellow-300">
                  <strong>Security Notice:</strong> API credentials are encrypted and stored securely. 
                  Never share your secret keys or access tokens.
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
                    Update Credentials
                  </button>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between py-2">
                    <span className="text-sm text-gray-600 dark:text-gray-400">API Key</span>
                    <span className="flex items-center gap-2">
                      {provider.credentials?.hasApiKey ? (
                        <CheckCircle className="w-4 h-4 text-primary-500" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-500" />
                      )}
                      <span className="text-sm">
                        {provider.credentials?.hasApiKey ? 'Configured' : 'Not configured'}
                      </span>
                    </span>
                  </div>

                  <div className="flex items-center justify-between py-2">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Secret Key</span>
                    <span className="flex items-center gap-2">
                      {provider.credentials?.hasSecret ? (
                        <CheckCircle className="w-4 h-4 text-primary-500" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-500" />
                      )}
                      <span className="text-sm">
                        {provider.credentials?.hasSecret ? 'Configured' : 'Not configured'}
                      </span>
                    </span>
                  </div>

                  {provider.type === 'clover' && (
                    <div className="flex items-center justify-between py-2">
                      <span className="text-sm text-gray-600 dark:text-gray-400">OAuth Token</span>
                      <span className="flex items-center gap-2">
                        {provider.credentials?.hasOAuth ? (
                          <>
                            <CheckCircle className="w-4 h-4 text-primary-500" />
                            <span className="text-sm">
                              Connected
                              {provider.credentials.oauthExpiry && (
                                <span className="text-gray-500 ml-1">
                                  (expires {new Date(provider.credentials.oauthExpiry).toLocaleDateString()})
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
                              Connect with OAuth
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
            <h3 className="text-lg font-semibold mb-4">Fees & Transaction Limits</h3>
            
            {providers.map((provider) => (
              <div key={provider.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                <h4 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  {getProviderIcon(provider.type)} {provider.name}
                </h4>

                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                      Platform Fees
                    </h5>
                    <div className="space-y-3">
                      <div>
                        <label className="text-sm text-gray-600 dark:text-gray-400">
                          Percentage Fee
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
                          Fixed Fee
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
                      Transaction Limits
                    </h5>
                    <div className="space-y-3">
                      <div>
                        <label className="text-sm text-gray-600 dark:text-gray-400">
                          Daily Limit
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
                          Per Transaction Limit
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
                    Save Changes
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'webhooks' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold mb-4">Webhook Configuration</h3>
            
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
              <div className="flex gap-2">
                <Info className="w-5 h-5 text-accent-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-accent-700 dark:text-blue-300">
                  Configure webhook URLs in your payment provider's dashboard to receive real-time payment events.
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
                      Webhook URL
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
                      Webhook Secret
                    </label>
                    <div className="flex gap-2 mt-1">
                      <input
                        type="password"
                        placeholder="Enter webhook signing secret"
                        className="flex-1 px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg dark:bg-gray-700"
                      />
                      <button className="px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
                        <Eye className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="text-sm text-gray-600 dark:text-gray-400">
                      Events to Subscribe
                    </label>
                    <div className="grid grid-cols-2 gap-2 mt-2">
                      {['payment.completed', 'payment.failed', 'refund.created', 'dispute.created'].map((event) => (
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
            <h3 className="text-lg font-semibold mb-4">Payment Analytics</h3>
            
            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-4">
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Transaction Volume (Last 7 Days)
                </h4>
                <div className="h-48 bg-gray-50 dark:bg-gray-900 rounded-lg flex items-center justify-center">
                  <span className="text-gray-500 dark:text-gray-400">Chart Placeholder</span>
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Success Rate by Provider
                </h4>
                <div className="h-48 bg-gray-50 dark:bg-gray-900 rounded-lg flex items-center justify-center">
                  <span className="text-gray-500 dark:text-gray-400">Chart Placeholder</span>
                </div>
              </div>
            </div>

            <div className="mt-6">
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Recent Transactions
              </h4>
              <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                <table className="w-full">
                  <thead className="bg-gray-50 dark:bg-gray-900">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400">
                        Transaction ID
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400">
                        Amount
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400">
                        Provider
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400">
                        Status
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400">
                        Date
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    <tr>
                      <td colSpan={5} className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                        No recent transactions
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
                Update {selectedProvider.name} Credentials
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
                  Environment
                </label>
                <select
                  value={credentialForm.environment}
                  onChange={(e) => setCredentialForm({ ...credentialForm, environment: e.target.value as 'sandbox' | 'production' })}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="sandbox">Sandbox</option>
                  <option value="production">Production</option>
                </select>
              </div>

              {/* API Key */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  API Key
                </label>
                <input
                  type="password"
                  value={credentialForm.apiKey}
                  onChange={(e) => setCredentialForm({ ...credentialForm, apiKey: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Enter API Key"
                />
              </div>

              {/* Secret Key */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Secret Key
                </label>
                <input
                  type="password"
                  value={credentialForm.secret}
                  onChange={(e) => setCredentialForm({ ...credentialForm, secret: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Enter Secret Key"
                />
              </div>

              {/* Merchant ID (for Clover) */}
              {selectedProvider.type === 'clover' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Merchant ID
                    </label>
                    <input
                      type="text"
                      value={credentialForm.merchantId}
                      onChange={(e) => setCredentialForm({ ...credentialForm, merchantId: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      placeholder="Enter Merchant ID"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Access Token (Optional - for OAuth)
                    </label>
                    <input
                      type="password"
                      value={credentialForm.accessToken}
                      onChange={(e) => setCredentialForm({ ...credentialForm, accessToken: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      placeholder="Enter Access Token"
                    />
                  </div>
                </>
              )}

              {/* Security Notice */}
              <div className="bg-warning-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                <div className="flex gap-2">
                  <Shield className="w-4 h-4 text-warning-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
                  <div className="text-xs text-yellow-700 dark:text-yellow-300">
                    Credentials are encrypted using AES-256 encryption before storage. 
                    Make sure you're in a secure environment when entering sensitive data.
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
                Cancel
              </button>
              <button
                onClick={handleUpdateCredentials}
                disabled={loading || !credentialForm.apiKey || !credentialForm.secret}
                className="px-4 py-2 bg-accent-600 text-white rounded-lg hover:bg-accent-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Updating...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    Update Credentials
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