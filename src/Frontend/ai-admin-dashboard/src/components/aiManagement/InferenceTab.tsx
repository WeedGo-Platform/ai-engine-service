import React, { useState, useEffect } from 'react';
import {
  Zap,
  Loader2,
  RefreshCw,
  AlertCircle,
  Cpu,
  Cloud,
  Network,
  ChevronDown,
  ChevronUp,
  Key,
  Check,
  X,
  Eye,
  EyeOff,
  Settings as SettingsIcon,
  TrendingUp,
  DollarSign,
  Clock
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../contexts/AuthContext';
import { useStoreContext } from '@/contexts/StoreContext';
import { getApiEndpoint } from '@/config/app.config';

interface InferenceTabProps {
  token?: string;
  tenantId?: string;
}

const InferenceTab: React.FC<InferenceTabProps> = ({ token, tenantId: propTenantId }) => {
  const { t } = useTranslation(['common']);
  const { user } = useAuth();
  const { currentStore } = useStoreContext();

  // Get tenant ID from props, user context, or current store
  const tenantId = propTenantId || user?.tenant_id || currentStore?.tenant_id;
  
  console.log('InferenceTab - tenantId:', tenantId, 'user:', user);

  // State for router and inference
  const [routerStats, setRouterStats] = useState<any>(null);
  const [isLoadingRouter, setIsLoadingRouter] = useState(false);
  const [isTogglingRouter, setIsTogglingRouter] = useState(false);
  const [providerModels, setProviderModels] = useState<Record<string, string>>({});
  const [availableModels, setAvailableModels] = useState<Record<string, any[]>>({});
  const [isLoadingModels, setIsLoadingModels] = useState(false);
  const [isUpdatingModel, setIsUpdatingModel] = useState(false);
  const [showModelConfig, setShowModelConfig] = useState(false);
  
  // State for tenant LLM configuration
  const [showTokenManagement, setShowTokenManagement] = useState(false);
  const [llmTokens, setLlmTokens] = useState<{groq?: string; openrouter?: string; llm7?: string}>({});
  const [tokenStatus, setTokenStatus] = useState<{groq?: boolean; openrouter?: boolean; llm7?: boolean}>({});
  const [showTokens, setShowTokens] = useState<{groq?: boolean; openrouter?: boolean; llm7?: boolean}>({});
  const [isLoadingTokens, setIsLoadingTokens] = useState(false);
  const [isSavingTokens, setIsSavingTokens] = useState(false);
  const [isTestingToken, setIsTestingToken] = useState<string | null>(null);
  
  // State for inference configuration
  const [inferenceConfig, setInferenceConfig] = useState<any>(null);
  const [isLoadingConfig, setIsLoadingConfig] = useState(false);
  const [isSavingConfig, setIsSavingConfig] = useState(false);
  
  // State for usage stats
  const [usageStats, setUsageStats] = useState<any>(null);
  const [isLoadingStats, setIsLoadingStats] = useState(false);
  const [statsTimeWindow, setStatsTimeWindow] = useState<number>(24);

  // Fetch router stats
  const fetchRouterStats = async () => {
    setIsLoadingRouter(true);
    try {
      const response = await fetch(getApiEndpoint('/admin/router/stats'), {
        headers: {
          'Authorization': token ? `Bearer ${token}` : ''
        }
      });
      const data = await response.json();
      setRouterStats(data);
    } catch (error) {
      console.error('Error fetching router stats:', error);
      toast.error(t('common:toasts.router.fetchFailed'));
    }
    setIsLoadingRouter(false);
  };

  // Fetch model configuration
  const fetchModelConfig = async () => {
    setIsLoadingModels(true);
    try {
      const response = await fetch(getApiEndpoint('/admin/router/models/config'), {
        headers: {
          'Authorization': token ? `Bearer ${token}` : ''
        }
      });
      const data = await response.json();

      if (data.current) {
        setProviderModels(data.current);
      }
      if (data.available) {
        setAvailableModels(data.available);
      }
    } catch (error) {
      console.error('Error fetching model config:', error);
      toast.error('Failed to fetch model configuration');
    }
    setIsLoadingModels(false);
  };

  // Toggle router mode
  const toggleRouter = async () => {
    setIsTogglingRouter(true);
    try {
      const response = await fetch(getApiEndpoint('/admin/router/toggle'), {
        method: 'POST',
        headers: {
          'Authorization': token ? `Bearer ${token}` : ''
        }
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.error || 'Failed to toggle router');
      }
      
      const data = await response.json();

      if (data.success) {
        await fetchRouterStats();
        toast.success(data.message || (data.active ? 'Switched to cloud inference' : 'Switched to local inference'));
      } else {
        toast.error(data.error || 'Failed to toggle router');
      }
    } catch (error) {
      console.error('Error toggling router:', error);
      toast.error('Failed to toggle router');
    }
    setIsTogglingRouter(false);
  };

  // Update provider model
  const updateProviderModel = async (provider: string, model: string) => {
    setIsUpdatingModel(true);
    try {
      const response = await fetch(getApiEndpoint('/admin/router/update-model'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: JSON.stringify({ provider, model })
      });
      const data = await response.json();

      if (data.status === 'success') {
        setProviderModels(prev => ({ ...prev, [provider]: model }));
        toast.success(`Updated model for ${provider.split(' (')[0]}`);
      } else {
        toast.error(data.error || 'Failed to update model');
      }
    } catch (error) {
      console.error('Error updating model:', error);
      toast.error('Failed to update model');
    }
    setIsUpdatingModel(false);
  };

  // Fetch tenant LLM tokens
  const fetchTenantTokens = async () => {
    if (!tenantId) return;

    setIsLoadingTokens(true);
    try {
      const response = await fetch(getApiEndpoint(`/tenants/${tenantId}/llm-tokens`), {
        headers: {
          'Authorization': token ? `Bearer ${token}` : ''
        }
      });
      const data = await response.json();
      
      if (data.configured) {
        setTokenStatus(data.configured);
      }
    } catch (error) {
      console.error('Error fetching tenant tokens:', error);
      toast.error('Failed to fetch API tokens configuration');
    }
    setIsLoadingTokens(false);
  };

  // Save tenant LLM tokens
  const saveTenantTokens = async () => {
    if (!tenantId) return;

    setIsSavingTokens(true);
    try {
      const response = await fetch(getApiEndpoint(`/tenants/${tenantId}/llm-tokens`), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: JSON.stringify({ tokens: llmTokens })
      });
      
      if (!response.ok) {
        throw new Error('Failed to save tokens');
      }
      
      const data = await response.json();
      toast.success('API tokens saved successfully');
      await fetchTenantTokens();
      setLlmTokens({}); // Clear form after save
    } catch (error) {
      console.error('Error saving tokens:', error);
      toast.error('Failed to save API tokens');
    }
    setIsSavingTokens(false);
  };

  // Test a specific token
  const testToken = async (provider: string) => {
    if (!tenantId || !llmTokens[provider as keyof typeof llmTokens]) return;

    setIsTestingToken(provider);
    try {
      const response = await fetch(getApiEndpoint(`/tenants/${tenantId}/llm-tokens/test`), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: JSON.stringify({
          provider,
          token: llmTokens[provider as keyof typeof llmTokens]
        })
      });
      
      const data = await response.json();
      
      if (data.valid) {
        toast.success(`✓ ${provider} token is valid!`);
      } else {
        toast.error(`✗ ${provider} token validation failed: ${data.error || 'Invalid'}`);
      }
    } catch (error) {
      console.error(`Error testing ${provider} token:`, error);
      toast.error(`Failed to test ${provider} token`);
    }
    setIsTestingToken(null);
  };

  // Fetch inference configuration
  const fetchInferenceConfig = async () => {
    if (!tenantId) return;

    setIsLoadingConfig(true);
    try {
      const response = await fetch(getApiEndpoint(`/tenants/${tenantId}/inference-config`), {
        headers: {
          'Authorization': token ? `Bearer ${token}` : ''
        }
      });
      const data = await response.json();
      setInferenceConfig(data);
    } catch (error) {
      console.error('Error fetching inference config:', error);
    }
    setIsLoadingConfig(false);
  };

  // Save inference configuration
  const saveInferenceConfig = async (config: any) => {
    if (!tenantId) return;

    setIsSavingConfig(true);
    try {
      const response = await fetch(getApiEndpoint(`/tenants/${tenantId}/inference-config`), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: JSON.stringify(config)
      });
      
      if (!response.ok) {
        throw new Error('Failed to save config');
      }
      
      toast.success('Inference configuration saved');
      await fetchInferenceConfig();
    } catch (error) {
      console.error('Error saving config:', error);
      toast.error('Failed to save inference configuration');
    }
    setIsSavingConfig(false);
  };

  // Fetch usage statistics
  const fetchUsageStats = async () => {
    if (!tenantId) return;

    setIsLoadingStats(true);
    try {
      const response = await fetch(
        getApiEndpoint(`/tenants/${tenantId}/usage-stats?hours=${statsTimeWindow}`),
        {
          headers: {
            'Authorization': token ? `Bearer ${token}` : ''
          }
        }
      );
      const data = await response.json();
      setUsageStats(data);
    } catch (error) {
      console.error('Error fetching usage stats:', error);
    }
    setIsLoadingStats(false);
  };

  useEffect(() => {
    fetchRouterStats();
    fetchModelConfig();
    if (tenantId) {
      fetchTenantTokens();
      fetchInferenceConfig();
      fetchUsageStats();
    }
  }, [tenantId]);

  return (
    <div>
      {isLoadingRouter ? (
        <div className="flex items-center justify-center py-8 sm:py-12">
          <Loader2 className="h-6 w-6 sm:h-8 sm:w-8 animate-spin text-indigo-600 dark:text-indigo-400" />
        </div>
      ) : !routerStats ? (
        <div className="text-center py-8 sm:py-12">
          <Zap className="h-12 w-12 sm:h-16 sm:w-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Inference Router Not Loaded</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
            Router configuration and stats are not currently loaded.
          </p>
          <button
            onClick={() => {
              fetchRouterStats();
              fetchModelConfig();
            }}
            disabled={isLoadingRouter}
            className="px-4 py-2 bg-indigo-600 dark:bg-indigo-500 text-white rounded-lg hover:bg-indigo-700 dark:hover:bg-indigo-600 transition-colors flex items-center gap-2 mx-auto disabled:opacity-50"
          >
            <RefreshCw className="h-4 w-4" />
            Load Router Stats
          </button>
        </div>
      ) : (
        <div className="space-y-4 sm:space-y-6">
          {/* Current Mode & Toggle */}
          <div className="bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-lg p-4 sm:p-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="flex-1">
                <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white mb-1">
                  Inference Mode
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {routerStats.active
                    ? '☁️ Cloud inference (3 providers available)'
                    : '💻 Local inference (llama-cpp)'
                  }
                </p>
                {routerStats.active && routerStats.providers && routerStats.providers.length > 0 && (
                  <div className="mt-2 flex items-center gap-2 flex-wrap">
                    <span className="text-xs text-gray-500 dark:text-gray-400">Primary:</span>
                    <span className="px-2 py-1 text-xs font-medium bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 rounded-full">
                      {routerStats.providers[0].split(' (')[0]}
                    </span>
                    {providerModels[routerStats.providers[0]] && (
                      <span className="text-xs text-gray-600 dark:text-gray-400">
                        → <code className="px-1.5 py-0.5 bg-white dark:bg-gray-800 rounded text-xs font-mono">
                          {providerModels[routerStats.providers[0]]}
                        </code>
                      </span>
                    )}
                  </div>
                )}
              </div>
              <button
                onClick={toggleRouter}
                disabled={isTogglingRouter || !routerStats.enabled}
                className={`w-full sm:w-auto px-4 sm:px-6 py-2.5 sm:py-3 rounded-lg font-medium transition-all ${
                  routerStats.active
                    ? 'bg-indigo-600 text-white hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600'
                    : 'bg-gray-600 text-white hover:bg-gray-700 dark:bg-gray-700 dark:hover:bg-gray-600'
                } disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2`}
              >
                {isTogglingRouter ? (
                  <>
                    <Loader2 className="h-4 w-4 sm:h-5 sm:w-5 animate-spin" />
                    <span className="hidden sm:inline">Switching...</span>
                    <span className="sm:hidden">Switch...</span>
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-4 w-4 sm:h-5 sm:w-5" />
                    <span className="hidden sm:inline">
                      {routerStats.active ? 'Switch to Local' : 'Switch to Cloud'}
                    </span>
                    <span className="sm:hidden">
                      {routerStats.active ? 'Local' : 'Cloud'}
                    </span>
                  </>
                )}
              </button>
            </div>

            {/* Performance Info */}
            <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-2 sm:gap-4">
              <div className="bg-white dark:bg-gray-800 rounded-lg p-2 sm:p-3">
                <p className="text-xs text-gray-500 dark:text-gray-400">Latency</p>
                <p className="text-sm sm:text-lg font-semibold text-gray-900 dark:text-white">
                  {routerStats.active ? '0.5-2.5s' : '~5s'}
                </p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-lg p-2 sm:p-3">
                <p className="text-xs text-gray-500 dark:text-gray-400">Model Size</p>
                <p className="text-sm sm:text-lg font-semibold text-gray-900 dark:text-white">
                  {routerStats.active ? '70B params' : '0.5-7B'}
                </p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-lg p-2 sm:p-3">
                <p className="text-xs text-gray-500 dark:text-gray-400">Cost/Month</p>
                <p className="text-sm sm:text-lg font-semibold text-green-600 dark:text-green-400">$0</p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-lg p-2 sm:p-3">
                <p className="text-xs text-gray-500 dark:text-gray-400">Daily Limit</p>
                <p className="text-sm sm:text-lg font-semibold text-gray-900 dark:text-white">
                  {routerStats.active ? '16K+' : 'Unlimited'}
                </p>
              </div>
            </div>
          </div>

          {/* Model Configuration Section */}
          {routerStats.enabled && routerStats.active && (
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 sm:p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Cpu className="h-4 w-4 sm:h-5 sm:w-5 text-indigo-600 dark:text-indigo-400" />
                  <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">
                    Model Configuration
                  </h3>
                </div>
                <button
                  onClick={() => setShowModelConfig(!showModelConfig)}
                  className="text-xs sm:text-sm text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300 flex items-center gap-1"
                >
                  {showModelConfig ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  {showModelConfig ? 'Hide' : 'Show'}
                </button>
              </div>

              {showModelConfig && (
                <>
                  {isLoadingModels ? (
                    <div className="flex items-center justify-center py-4">
                      <Loader2 className="h-5 w-5 animate-spin text-indigo-600 dark:text-indigo-400" />
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {Object.keys(providerModels).map(provider => {
                        const currentModel = providerModels[provider];
                        const models = availableModels[provider] || [];

                        return (
                          <div key={provider} className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-4">
                            <div className="flex-1">
                              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                {provider.split(' (')[0]}
                              </p>
                            </div>
                            <div className="w-full sm:w-auto px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-gray-50 dark:bg-gray-900">
                              <code className="text-xs font-mono text-gray-900 dark:text-white">
                                {currentModel}
                              </code>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  <div className="mt-4 flex items-start gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <AlertCircle className="h-4 w-4 sm:h-5 sm:w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                    <div className="text-xs sm:text-sm text-blue-800 dark:text-blue-300">
                      <p className="font-medium mb-1">Current Model Configuration:</p>
                      <ul className="list-disc list-inside space-y-1">
                        <li>Models are configured via backend settings</li>
                        <li>Different models have different strengths (speed, reasoning, cost)</li>
                        <li>Free tier models have rate limits - the router automatically switches on errors</li>
                      </ul>
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* Token Management Section */}
          {tenantId && (
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 sm:p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Key className="h-4 w-4 sm:h-5 sm:w-5 text-indigo-600 dark:text-indigo-400" />
                  <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">
                    API Token Management
                  </h3>
                </div>
                <button
                  onClick={() => setShowTokenManagement(!showTokenManagement)}
                  className="text-xs sm:text-sm text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300 flex items-center gap-1"
                >
                  {showTokenManagement ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  {showTokenManagement ? 'Hide' : 'Configure'}
                </button>
              </div>

              {showTokenManagement && (
                <>
                  {isLoadingTokens ? (
                    <div className="flex items-center justify-center py-4">
                      <Loader2 className="h-5 w-5 animate-spin text-indigo-600 dark:text-indigo-400" />
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {/* Groq Token */}
                      <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <Zap className="h-4 w-4 text-yellow-500" />
                            <h4 className="text-sm font-medium text-gray-900 dark:text-white">Groq API Key</h4>
                          </div>
                          {tokenStatus.groq && (
                            <span className="px-2 py-1 text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full flex items-center gap-1">
                              <Check className="h-3 w-3" /> Configured
                            </span>
                          )}
                        </div>
                        <div className="flex gap-2">
                          <div className="relative flex-1">
                            <input
                              type={showTokens.groq ? 'text' : 'password'}
                              value={llmTokens.groq || ''}
                              onChange={(e) => setLlmTokens({...llmTokens, groq: e.target.value})}
                              placeholder="gsk_..."
                              className="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm"
                            />
                            <button
                              onClick={() => setShowTokens({...showTokens, groq: !showTokens.groq})}
                              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                            >
                              {showTokens.groq ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                            </button>
                          </div>
                          <button
                            onClick={() => testToken('groq')}
                            disabled={!llmTokens.groq || isTestingToken === 'groq'}
                            className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                          >
                            {isTestingToken === 'groq' ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              'Test'
                            )}
                          </button>
                        </div>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                          Get your key from <a href="https://console.groq.com/keys" target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">console.groq.com</a>
                        </p>
                      </div>

                      {/* OpenRouter Token */}
                      <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <Network className="h-4 w-4 text-blue-500" />
                            <h4 className="text-sm font-medium text-gray-900 dark:text-white">OpenRouter API Key</h4>
                          </div>
                          {tokenStatus.openrouter && (
                            <span className="px-2 py-1 text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full flex items-center gap-1">
                              <Check className="h-3 w-3" /> Configured
                            </span>
                          )}
                        </div>
                        <div className="flex gap-2">
                          <div className="relative flex-1">
                            <input
                              type={showTokens.openrouter ? 'text' : 'password'}
                              value={llmTokens.openrouter || ''}
                              onChange={(e) => setLlmTokens({...llmTokens, openrouter: e.target.value})}
                              placeholder="sk-or-..."
                              className="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm"
                            />
                            <button
                              onClick={() => setShowTokens({...showTokens, openrouter: !showTokens.openrouter})}
                              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                            >
                              {showTokens.openrouter ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                            </button>
                          </div>
                          <button
                            onClick={() => testToken('openrouter')}
                            disabled={!llmTokens.openrouter || isTestingToken === 'openrouter'}
                            className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                          >
                            {isTestingToken === 'openrouter' ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              'Test'
                            )}
                          </button>
                        </div>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                          Get your key from <a href="https://openrouter.ai/keys" target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">openrouter.ai</a>
                        </p>
                      </div>

                      {/* LLM7 Token */}
                      <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <Cloud className="h-4 w-4 text-purple-500" />
                            <h4 className="text-sm font-medium text-gray-900 dark:text-white">LLM7 API Key</h4>
                          </div>
                          {tokenStatus.llm7 && (
                            <span className="px-2 py-1 text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full flex items-center gap-1">
                              <Check className="h-3 w-3" /> Configured
                            </span>
                          )}
                        </div>
                        <div className="flex gap-2">
                          <div className="relative flex-1">
                            <input
                              type={showTokens.llm7 ? 'text' : 'password'}
                              value={llmTokens.llm7 || ''}
                              onChange={(e) => setLlmTokens({...llmTokens, llm7: e.target.value})}
                              placeholder="sk-..."
                              className="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm"
                            />
                            <button
                              onClick={() => setShowTokens({...showTokens, llm7: !showTokens.llm7})}
                              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                            >
                              {showTokens.llm7 ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                            </button>
                          </div>
                          <button
                            onClick={() => testToken('llm7')}
                            disabled={!llmTokens.llm7 || isTestingToken === 'llm7'}
                            className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                          >
                            {isTestingToken === 'llm7' ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              'Test'
                            )}
                          </button>
                        </div>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                          Optional - for GPT-4 access
                        </p>
                      </div>

                      {/* Save Button */}
                      <div className="flex justify-end pt-2">
                        <button
                          onClick={saveTenantTokens}
                          disabled={isSavingTokens || Object.keys(llmTokens).length === 0}
                          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                        >
                          {isSavingTokens ? (
                            <>
                              <Loader2 className="h-4 w-4 animate-spin" />
                              Saving...
                            </>
                          ) : (
                            <>
                              <Check className="h-4 w-4" />
                              Save Tokens
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  )}

                  <div className="mt-4 flex items-start gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <AlertCircle className="h-4 w-4 sm:h-5 sm:w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                    <div className="text-xs sm:text-sm text-blue-800 dark:text-blue-300">
                      <p className="font-medium mb-1">🔐 Security Notes:</p>
                      <ul className="list-disc list-inside space-y-1">
                        <li>Tokens are encrypted and stored securely</li>
                        <li>Only you can see and manage your API tokens</li>
                        <li>Test tokens before saving to ensure they work</li>
                        <li>Revoke tokens from provider dashboards if compromised</li>
                      </ul>
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* Provider & Model Selection Cards */}
          {tenantId && inferenceConfig && (
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 sm:p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Network className="h-4 w-4 sm:h-5 sm:w-5 text-indigo-600 dark:text-indigo-400" />
                  <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">
                    Provider & Model Selection
                  </h3>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="auto-failover-toggle"
                    checked={inferenceConfig.auto_failover !== false}
                    onChange={(e) => {
                      const newConfig = { ...inferenceConfig, auto_failover: e.target.checked };
                      setInferenceConfig(newConfig);
                      saveInferenceConfig(newConfig);
                    }}
                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <label htmlFor="auto-failover-toggle" className="text-xs sm:text-sm text-gray-700 dark:text-gray-300">
                    Auto-failover
                  </label>
                </div>
              </div>

              {isLoadingConfig ? (
                <div className="flex items-center justify-center py-4">
                  <Loader2 className="h-5 w-5 animate-spin text-indigo-600 dark:text-indigo-400" />
                </div>
              ) : (
                <div className="space-y-3">
                  {/* Provider Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {/* Groq Card */}
                    <div
                      className={`relative border-2 rounded-lg p-4 cursor-pointer transition-all ${
                        inferenceConfig.preferred_provider === 'groq'
                          ? 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                      }`}
                      onClick={() => {
                        const newConfig = { ...inferenceConfig, preferred_provider: 'groq' };
                        setInferenceConfig(newConfig);
                        saveInferenceConfig(newConfig);
                      }}
                    >
                      {inferenceConfig.preferred_provider === 'groq' && (
                        <div className="absolute top-2 right-2">
                          <Check className="h-5 w-5 text-yellow-500" />
                        </div>
                      )}
                      <div className="flex items-center gap-2 mb-3">
                        <Zap className="h-5 w-5 text-yellow-500" />
                        <span className="font-semibold text-gray-900 dark:text-white">Groq</span>
                        {tokenStatus.groq && (
                          <span className="ml-auto px-2 py-0.5 text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded">
                            Configured
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-gray-600 dark:text-gray-400 mb-3">
                        Ultra-fast inference • Low latency • Best for chat
                      </p>
                      <div className="space-y-2">
                        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">
                          Model:
                        </label>
                        <select
                          value={inferenceConfig.preferred_models?.groq || 'llama-3.3-70b-versatile'}
                          onChange={(e) => {
                            e.stopPropagation();
                            const newConfig = {
                              ...inferenceConfig,
                              preferred_models: {
                                ...inferenceConfig.preferred_models,
                                groq: e.target.value
                              }
                            };
                            setInferenceConfig(newConfig);
                            saveInferenceConfig(newConfig);
                          }}
                          onClick={(e) => e.stopPropagation()}
                          className="w-full px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                        >
                          <option value="llama-3.3-70b-versatile">Llama 3.3 70B</option>
                          <option value="llama-3.1-70b-versatile">Llama 3.1 70B</option>
                          <option value="mixtral-8x7b-32768">Mixtral 8x7B</option>
                        </select>
                      </div>
                      <div className="mt-2 flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
                        <Clock className="h-3 w-3" />
                        ~0.5s latency
                      </div>
                    </div>

                    {/* OpenRouter Card */}
                    <div
                      className={`relative border-2 rounded-lg p-4 cursor-pointer transition-all ${
                        inferenceConfig.preferred_provider === 'openrouter'
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                      }`}
                      onClick={() => {
                        const newConfig = { ...inferenceConfig, preferred_provider: 'openrouter' };
                        setInferenceConfig(newConfig);
                        saveInferenceConfig(newConfig);
                      }}
                    >
                      {inferenceConfig.preferred_provider === 'openrouter' && (
                        <div className="absolute top-2 right-2">
                          <Check className="h-5 w-5 text-blue-500" />
                        </div>
                      )}
                      <div className="flex items-center gap-2 mb-3">
                        <Network className="h-5 w-5 text-blue-500" />
                        <span className="font-semibold text-gray-900 dark:text-white">OpenRouter</span>
                        {tokenStatus.openrouter && (
                          <span className="ml-auto px-2 py-0.5 text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded">
                            Configured
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-gray-600 dark:text-gray-400 mb-3">
                        Advanced reasoning • Multiple models • Best for complex tasks
                      </p>
                      <div className="space-y-2">
                        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">
                          Model:
                        </label>
                        <select
                          value={inferenceConfig.preferred_models?.openrouter || 'deepseek/deepseek-r1'}
                          onChange={(e) => {
                            e.stopPropagation();
                            const newConfig = {
                              ...inferenceConfig,
                              preferred_models: {
                                ...inferenceConfig.preferred_models,
                                openrouter: e.target.value
                              }
                            };
                            setInferenceConfig(newConfig);
                            saveInferenceConfig(newConfig);
                          }}
                          onClick={(e) => e.stopPropagation()}
                          className="w-full px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                        >
                          <option value="deepseek/deepseek-r1">DeepSeek R1</option>
                          <option value="anthropic/claude-3.5-sonnet">Claude 3.5 Sonnet</option>
                          <option value="google/gemini-pro-1.5">Gemini Pro 1.5</option>
                        </select>
                      </div>
                      <div className="mt-2 flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
                        <Clock className="h-3 w-3" />
                        ~2s latency
                      </div>
                    </div>

                    {/* LLM7 Card */}
                    <div
                      className={`relative border-2 rounded-lg p-4 cursor-pointer transition-all ${
                        inferenceConfig.preferred_provider === 'llm7'
                          ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                      }`}
                      onClick={() => {
                        const newConfig = { ...inferenceConfig, preferred_provider: 'llm7' };
                        setInferenceConfig(newConfig);
                        saveInferenceConfig(newConfig);
                      }}
                    >
                      {inferenceConfig.preferred_provider === 'llm7' && (
                        <div className="absolute top-2 right-2">
                          <Check className="h-5 w-5 text-purple-500" />
                        </div>
                      )}
                      <div className="flex items-center gap-2 mb-3">
                        <Cloud className="h-5 w-5 text-purple-500" />
                        <span className="font-semibold text-gray-900 dark:text-white">LLM7</span>
                        {tokenStatus.llm7 && (
                          <span className="ml-auto px-2 py-0.5 text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded">
                            Configured
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-gray-600 dark:text-gray-400 mb-3">
                        Reliable fallback • No auth required • Always available
                      </p>
                      <div className="space-y-2">
                        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">
                          Model:
                        </label>
                        <select
                          value={inferenceConfig.preferred_models?.llm7 || 'gpt-4o-mini'}
                          onChange={(e) => {
                            e.stopPropagation();
                            const newConfig = {
                              ...inferenceConfig,
                              preferred_models: {
                                ...inferenceConfig.preferred_models,
                                llm7: e.target.value
                              }
                            };
                            setInferenceConfig(newConfig);
                            saveInferenceConfig(newConfig);
                          }}
                          onClick={(e) => e.stopPropagation()}
                          className="w-full px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                        >
                          <option value="gpt-4o-mini">GPT-4o Mini</option>
                          <option value="gpt-4o">GPT-4o</option>
                          <option value="gpt-4-turbo">GPT-4 Turbo</option>
                        </select>
                      </div>
                      <div className="mt-2 flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
                        <Clock className="h-3 w-3" />
                        ~1.5s latency
                      </div>
                    </div>
                  </div>

                  {/* Active Provider Indicator */}
                  <div className="bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800 rounded-lg p-3">
                    <div className="flex items-center gap-2 text-sm">
                      <div className="flex items-center gap-1.5">
                        <div className="h-2 w-2 bg-indigo-500 rounded-full animate-pulse"></div>
                        <span className="font-medium text-indigo-900 dark:text-indigo-300">
                          Active Provider:
                        </span>
                      </div>
                      <span className="text-indigo-700 dark:text-indigo-400 capitalize">
                        {inferenceConfig.preferred_provider || 'groq'}
                      </span>
                      <span className="text-indigo-600 dark:text-indigo-500 text-xs">
                        • {inferenceConfig.preferred_models?.[inferenceConfig.preferred_provider] || 'default model'}
                      </span>
                    </div>
                    {inferenceConfig.auto_failover && (
                      <p className="text-xs text-indigo-600 dark:text-indigo-400 mt-1.5">
                        ℹ️ Auto-failover enabled: Will switch to alternative providers on rate limits or errors
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Provider Configuration & Stats */}
          {tenantId && inferenceConfig && (
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 sm:p-6">
              <div className="flex items-center gap-2 mb-4">
                <SettingsIcon className="h-4 w-4 sm:h-5 sm:w-5 text-indigo-600 dark:text-indigo-400" />
                <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">
                  Provider Preferences
                </h3>
              </div>

              {isLoadingConfig ? (
                <div className="flex items-center justify-center py-4">
                  <Loader2 className="h-5 w-5 animate-spin text-indigo-600 dark:text-indigo-400" />
                </div>
              ) : (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Preferred Provider
                    </label>
                    <select
                      value={inferenceConfig.preferred_provider || 'groq'}
                      onChange={(e) => {
                        const newConfig = { ...inferenceConfig, preferred_provider: e.target.value };
                        setInferenceConfig(newConfig);
                        saveInferenceConfig(newConfig);
                      }}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                    >
                      <option value="groq">Groq (Fastest)</option>
                      <option value="openrouter">OpenRouter (Reasoning)</option>
                      <option value="llm7">LLM7 (Fallback)</option>
                    </select>
                  </div>

                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="auto-failover"
                      checked={inferenceConfig.auto_failover !== false}
                      onChange={(e) => {
                        const newConfig = { ...inferenceConfig, auto_failover: e.target.checked };
                        setInferenceConfig(newConfig);
                        saveInferenceConfig(newConfig);
                      }}
                      className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    />
                    <label htmlFor="auto-failover" className="text-sm text-gray-700 dark:text-gray-300">
                      Enable automatic failover to other providers on rate limits or errors
                    </label>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Usage Statistics Dashboard */}
          {tenantId && usageStats && (
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 sm:p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 sm:h-5 sm:w-5 text-indigo-600 dark:text-indigo-400" />
                  <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">
                    Usage Statistics
                  </h3>
                </div>
                <select
                  value={statsTimeWindow}
                  onChange={(e) => {
                    setStatsTimeWindow(Number(e.target.value));
                    fetchUsageStats();
                  }}
                  className="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                >
                  <option value={1}>Last Hour</option>
                  <option value={24}>Last 24 Hours</option>
                  <option value={168}>Last 7 Days</option>
                  <option value={720}>Last 30 Days</option>
                </select>
              </div>

              {isLoadingStats ? (
                <div className="flex items-center justify-center py-4">
                  <Loader2 className="h-5 w-5 animate-spin text-indigo-600 dark:text-indigo-400" />
                </div>
              ) : (
                <>
                  {/* Summary Cards */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                    <div className="bg-gradient-to-br from-indigo-50 to-indigo-100 dark:from-indigo-900/20 dark:to-indigo-900/10 rounded-lg p-3">
                      <p className="text-xs text-indigo-600 dark:text-indigo-400 mb-1">Total Requests</p>
                      <p className="text-xl font-bold text-indigo-900 dark:text-indigo-300">
                        {usageStats.total_requests?.toLocaleString() || 0}
                      </p>
                    </div>
                    <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-900/10 rounded-lg p-3">
                      <p className="text-xs text-green-600 dark:text-green-400 mb-1">Total Tokens</p>
                      <p className="text-xl font-bold text-green-900 dark:text-green-300">
                        {usageStats.total_tokens?.toLocaleString() || 0}
                      </p>
                    </div>
                    <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-900/10 rounded-lg p-3">
                      <p className="text-xs text-yellow-600 dark:text-yellow-400 mb-1 flex items-center gap-1">
                        <DollarSign className="h-3 w-3" /> Total Cost
                      </p>
                      <p className="text-xl font-bold text-yellow-900 dark:text-yellow-300">
                        ${usageStats.total_cost_usd?.toFixed(4) || '0.0000'}
                      </p>
                    </div>
                    <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-900/10 rounded-lg p-3">
                      <p className="text-xs text-purple-600 dark:text-purple-400 mb-1 flex items-center gap-1">
                        <Clock className="h-3 w-3" /> Avg Latency
                      </p>
                      <p className="text-xl font-bold text-purple-900 dark:text-purple-300">
                        {usageStats.by_model?.[0]?.latency_ms?.avg?.toFixed(0) || 0}ms
                      </p>
                    </div>
                  </div>

                  {/* Rate Limit Warnings */}
                  {usageStats.by_provider && Object.keys(usageStats.by_provider).length > 0 && (
                    <>
                      {Object.entries(usageStats.by_provider).some(([provider, stats]: [string, any]) => {
                        const maxRequests = provider === 'groq' ? 14400 : provider === 'openrouter' ? 200 : 10000;
                        const usagePercent = (stats.requests / maxRequests) * 100;
                        return usagePercent > 50;
                      }) && (
                        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3 mb-4">
                          <div className="flex items-start gap-2">
                            <AlertCircle className="h-4 w-4 text-yellow-600 dark:text-yellow-400 mt-0.5 flex-shrink-0" />
                            <div className="flex-1">
                              <h5 className="text-sm font-medium text-yellow-900 dark:text-yellow-300 mb-1">
                                Rate Limit Notice
                              </h5>
                              <div className="text-xs text-yellow-800 dark:text-yellow-400 space-y-1">
                                {Object.entries(usageStats.by_provider).map(([provider, stats]: [string, any]) => {
                                  const maxRequests = provider === 'groq' ? 14400 : provider === 'openrouter' ? 200 : 10000;
                                  const usagePercent = (stats.requests / maxRequests) * 100;
                                  if (usagePercent > 50) {
                                    return (
                                      <p key={provider}>
                                        <span className="font-medium capitalize">{provider}</span>:{' '}
                                        {usagePercent.toFixed(0)}% of daily limit used
                                        {usagePercent > 80 && (
                                          <span className="ml-1 text-red-600 dark:text-red-400 font-medium">
                                            (Critical!)
                                          </span>
                                        )}
                                      </p>
                                    );
                                  }
                                  return null;
                                })}
                              </div>
                              {inferenceConfig?.auto_failover && (
                                <p className="text-xs text-yellow-700 dark:text-yellow-500 mt-2">
                                  ✓ Auto-failover is enabled - will switch providers automatically
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                      )}
                    </>
                  )}

                  {/* Per-Provider Breakdown */}
                  {usageStats.by_provider && Object.keys(usageStats.by_provider).length > 0 && (
                    <div className="space-y-3">
                      <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">Provider Breakdown</h4>
                      {Object.entries(usageStats.by_provider).map(([provider, stats]: [string, any]) => {
                        // Calculate rate limit percentage
                        const maxRequests = provider === 'groq' ? 14400 : provider === 'openrouter' ? 200 : 10000;
                        const usagePercent = (stats.requests / maxRequests) * 100;
                        const isWarning = usagePercent > 50;
                        const isCritical = usagePercent > 80;
                        
                        return (
                          <div 
                            key={provider} 
                            className={`border rounded-lg p-3 ${
                              isCritical 
                                ? 'border-red-300 dark:border-red-700 bg-red-50/50 dark:bg-red-900/10'
                                : isWarning
                                ? 'border-yellow-300 dark:border-yellow-700 bg-yellow-50/50 dark:bg-yellow-900/10'
                                : 'border-gray-200 dark:border-gray-700'
                            }`}
                          >
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                {provider === 'groq' && <Zap className="h-4 w-4 text-yellow-500" />}
                                {provider === 'openrouter' && <Network className="h-4 w-4 text-blue-500" />}
                                {provider === 'llm7' && <Cloud className="h-4 w-4 text-purple-500" />}
                                <span className="font-medium text-gray-900 dark:text-white capitalize">{provider}</span>
                              </div>
                              <div className="flex items-center gap-2">
                                {isCritical && (
                                  <span className="px-2 py-0.5 text-xs bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded font-medium">
                                    Critical
                                  </span>
                                )}
                                {isWarning && !isCritical && (
                                  <span className="px-2 py-0.5 text-xs bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 rounded font-medium">
                                    Warning
                                  </span>
                                )}
                                <span className="text-xs text-gray-500 dark:text-gray-400">
                                  {stats.requests} requests
                                </span>
                              </div>
                            </div>
                            
                            {/* Rate Limit Progress Bar */}
                            <div className="mb-3">
                              <div className="flex items-center justify-between text-xs mb-1">
                                <span className="text-gray-600 dark:text-gray-400">Daily Limit Usage</span>
                                <span className={`font-medium ${
                                  isCritical ? 'text-red-600 dark:text-red-400' :
                                  isWarning ? 'text-yellow-600 dark:text-yellow-400' :
                                  'text-gray-600 dark:text-gray-400'
                                }`}>
                                  {usagePercent.toFixed(1)}%
                                </span>
                              </div>
                              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                                <div 
                                  className={`h-2 rounded-full transition-all ${
                                    isCritical ? 'bg-red-500' :
                                    isWarning ? 'bg-yellow-500' :
                                    'bg-green-500'
                                  }`}
                                  style={{ width: `${Math.min(100, usagePercent)}%` }}
                                />
                              </div>
                              <div className="flex items-center justify-between text-xs mt-1 text-gray-500 dark:text-gray-400">
                                <span>{stats.requests.toLocaleString()} used</span>
                                <span>{maxRequests.toLocaleString()} max</span>
                              </div>
                            </div>

                            <div className="grid grid-cols-3 gap-2 text-xs">
                              <div>
                                <p className="text-gray-500 dark:text-gray-400">Tokens</p>
                                <p className="font-medium text-gray-900 dark:text-white">
                                  {stats.tokens?.toLocaleString() || 0}
                                </p>
                              </div>
                              <div>
                                <p className="text-gray-500 dark:text-gray-400">Cost</p>
                                <p className="font-medium text-gray-900 dark:text-white">
                                  ${stats.cost_usd?.toFixed(4) || '0.0000'}
                                </p>
                              </div>
                              <div>
                                <p className="text-gray-500 dark:text-gray-400">Models</p>
                                <p className="font-medium text-gray-900 dark:text-white">
                                  {stats.models?.length || 0}
                                </p>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {/* Per-Model Details */}
                  {usageStats.by_model && usageStats.by_model.length > 0 && (
                    <div className="space-y-3 mt-4">
                      <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">Model Performance</h4>
                      <div className="space-y-2">
                        {usageStats.by_model.slice(0, 5).map((modelStat: any, index: number) => (
                          <div 
                            key={`${modelStat.provider}-${modelStat.model}`}
                            className="border border-gray-200 dark:border-gray-700 rounded-lg p-2.5"
                          >
                            <div className="flex items-center justify-between mb-1.5">
                              <div className="flex items-center gap-2">
                                <span className="text-xs font-medium text-gray-900 dark:text-white">
                                  {modelStat.model}
                                </span>
                                <span className="text-xs text-gray-500 dark:text-gray-400">
                                  ({modelStat.provider})
                                </span>
                              </div>
                              <span className="text-xs text-gray-500 dark:text-gray-400">
                                {modelStat.requests} req
                              </span>
                            </div>
                            <div className="grid grid-cols-4 gap-2 text-xs">
                              <div>
                                <p className="text-gray-500 dark:text-gray-400 mb-0.5">Success</p>
                                <p className="font-medium text-green-600 dark:text-green-400">
                                  {((modelStat.successful / modelStat.requests) * 100).toFixed(0)}%
                                </p>
                              </div>
                              <div>
                                <p className="text-gray-500 dark:text-gray-400 mb-0.5">Latency</p>
                                <p className="font-medium text-gray-900 dark:text-white">
                                  {modelStat.latency_ms?.avg?.toFixed(0) || 0}ms
                                </p>
                              </div>
                              <div>
                                <p className="text-gray-500 dark:text-gray-400 mb-0.5">Tokens</p>
                                <p className="font-medium text-gray-900 dark:text-white">
                                  {modelStat.tokens?.total?.toLocaleString() || 0}
                                </p>
                              </div>
                              <div>
                                <p className="text-gray-500 dark:text-gray-400 mb-0.5">Cost</p>
                                <p className="font-medium text-gray-900 dark:text-white">
                                  ${modelStat.cost_usd?.toFixed(3) || '0.000'}
                                </p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Empty State */}
                  {usageStats.total_requests === 0 && (
                    <div className="text-center py-8">
                      <TrendingUp className="h-12 w-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        No usage data yet for this time period
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                        Make some requests to see statistics here
                      </p>
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* Providers Status */}
          {routerStats.enabled && routerStats.providers && routerStats.providers.length > 0 && (
            <div>
              <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white mb-3 sm:mb-4">
                Cloud Providers
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
                {routerStats.providers.map((provider: string, index: number) => {
                  const providerStats = routerStats.stats?.providers?.[provider];
                  const isGroq = provider.includes('Groq');
                  const isOpenRouter = provider.includes('OpenRouter');
                  const isLLM7 = provider.includes('LLM7');
                  const isPrimary = index === 0;

                  return (
                    <div
                      key={provider}
                      className={`border rounded-lg p-3 sm:p-4 hover:border-indigo-500 dark:hover:border-indigo-400 transition-colors ${
                        isPrimary
                          ? 'border-indigo-500 dark:border-indigo-400 bg-indigo-50/50 dark:bg-indigo-900/10'
                          : 'border-gray-200 dark:border-gray-700'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          {isGroq && <Zap className="h-4 w-4 sm:h-5 sm:w-5 text-yellow-500" />}
                          {isOpenRouter && <Network className="h-4 w-4 sm:h-5 sm:w-5 text-blue-500" />}
                          {isLLM7 && <Cloud className="h-4 w-4 sm:h-5 sm:w-5 text-purple-500" />}
                          <h4 className="text-sm sm:text-base font-medium text-gray-900 dark:text-white">
                            {provider.split(' (')[0]}
                          </h4>
                        </div>
                        <div className="flex items-center gap-2">
                          {isPrimary && (
                            <span className="px-2 py-1 text-xs bg-indigo-600 text-white rounded-full font-medium">
                              PRIMARY
                            </span>
                          )}
                          <span className="px-2 py-1 text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full">
                            Active
                          </span>
                        </div>
                      </div>
                      <div className="mb-2">
                        <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Current Model:</p>
                        <code className="text-xs bg-gray-100 dark:bg-gray-900 px-2 py-1 rounded text-gray-900 dark:text-white font-mono">
                          {providerModels[provider] || provider.split('(')[1]?.replace(')', '')}
                        </code>
                      </div>
                      {providerStats && (
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div>
                            <p className="text-gray-500 dark:text-gray-400">Requests</p>
                            <p className="font-medium text-gray-900 dark:text-white">
                              {providerStats.total_requests || 0}
                            </p>
                          </div>
                          <div>
                            <p className="text-gray-500 dark:text-gray-400">Success</p>
                            <p className="font-medium text-gray-900 dark:text-white">
                              {((providerStats.success_rate || 0) * 100).toFixed(0)}%
                            </p>
                          </div>
                        </div>
                      )}
                      <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                        {isGroq && '⚡ Ultra-fast (0.5s)'}
                        {isOpenRouter && '🧠 Reasoning (2s)'}
                        {isLLM7 && '🌐 Fallback (2.5s)'}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default InferenceTab;