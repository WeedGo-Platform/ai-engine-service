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
  ChevronUp
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { useTranslation } from 'react-i18next';

interface InferenceTabProps {
  token?: string;
}

const InferenceTab: React.FC<InferenceTabProps> = ({ token }) => {
  const { t } = useTranslation(['common']);

  // State for router and inference
  const [routerStats, setRouterStats] = useState<any>(null);
  const [isLoadingRouter, setIsLoadingRouter] = useState(false);
  const [isTogglingRouter, setIsTogglingRouter] = useState(false);
  const [providerModels, setProviderModels] = useState<Record<string, string>>({});
  const [availableModels, setAvailableModels] = useState<Record<string, any[]>>({});
  const [isLoadingModels, setIsLoadingModels] = useState(false);
  const [isUpdatingModel, setIsUpdatingModel] = useState(false);
  const [showModelConfig, setShowModelConfig] = useState(false);

  // Fetch router stats
  const fetchRouterStats = async () => {
    setIsLoadingRouter(true);
    try {
      const response = await fetch('http://localhost:5024/api/admin/router/stats', {
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
      const response = await fetch('http://localhost:5024/api/admin/router/model-config', {
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
      const response = await fetch('http://localhost:5024/api/admin/router/toggle', {
        method: 'POST',
        headers: {
          'Authorization': token ? `Bearer ${token}` : ''
        }
      });
      const data = await response.json();

      if (data.status === 'success') {
        await fetchRouterStats();
        toast.success(data.active ? 'Switched to cloud inference' : 'Switched to local inference');
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
      const response = await fetch('http://localhost:5024/api/admin/router/update-model', {
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

  useEffect(() => {
    fetchRouterStats();
    fetchModelConfig();
  }, []);

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
                            <select
                              value={currentModel}
                              onChange={(e) => updateProviderModel(provider, e.target.value)}
                              disabled={isUpdatingModel}
                              className="w-full sm:w-auto px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white disabled:opacity-50"
                            >
                              {models.map((model: any) => (
                                <option key={model.name} value={model.name}>
                                  {model.name} {model.default && '(default)'}
                                </option>
                              ))}
                            </select>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  <div className="mt-4 flex items-start gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <AlertCircle className="h-4 w-4 sm:h-5 sm:w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                    <div className="text-xs sm:text-sm text-blue-800 dark:text-blue-300">
                      <p className="font-medium mb-1">Model Selection Tips:</p>
                      <ul className="list-disc list-inside space-y-1">
                        <li>Changes take effect immediately</li>
                        <li>Different models have different strengths (speed, reasoning, cost)</li>
                        <li>Free tier models have rate limits - monitor your usage</li>
                      </ul>
                    </div>
                  </div>
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