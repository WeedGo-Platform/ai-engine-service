import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Globe, 
  Languages, 
  TrendingUp, 
  AlertCircle, 
  CheckCircle,
  RefreshCw,
  Settings,
  BarChart3,
  MessageSquare,
  Zap
} from 'lucide-react';
import toast from 'react-hot-toast';

interface LanguageConfig {
  code: string;
  name: string;
  nativeName: string;
  tier: number;
  isRtl: boolean;
  tokenizerEfficiency: number;
  modelPerformanceScore: number;
  isActive: boolean;
}

interface LanguageMetrics {
  languageCode: string;
  totalRequests: number;
  successfulRequests: number;
  fallbackCount: number;
  avgQualityScore: number;
  avgResponseTimeMs: number;
}

interface TranslationCache {
  sourceText: string;
  sourceLang: string;
  targetLang: string;
  translatedText: string;
  usageCount: number;
  qualityScore: number;
}

const MultilingualManager: React.FC = () => {
  const [selectedLanguage, setSelectedLanguage] = useState<string>('es');
  const [testText, setTestText] = useState('');
  const [translationResult, setTranslationResult] = useState<any>(null);
  const queryClient = useQueryClient();

  // Fetch language configurations
  const { data: languages, isLoading: languagesLoading } = useQuery({
    queryKey: ['languages'],
    queryFn: async () => {
      const response = await fetch('http://localhost:5024/api/v1/languages');
      if (!response.ok) throw new Error('Failed to fetch languages');
      return response.json();
    }
  });

  // Fetch language metrics
  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['language-metrics'],
    queryFn: async () => {
      const response = await fetch('http://localhost:5024/api/v1/languages/metrics');
      if (!response.ok) throw new Error('Failed to fetch metrics');
      return response.json();
    },
    refetchInterval: 30000 // Refresh every 30 seconds
  });

  // Fetch translation cache stats
  const { data: cacheStats } = useQuery({
    queryKey: ['translation-cache-stats'],
    queryFn: async () => {
      const response = await fetch('http://localhost:5024/api/v1/languages/cache/stats');
      if (!response.ok) throw new Error('Failed to fetch cache stats');
      return response.json();
    }
  });

  // Test translation mutation
  const testTranslationMutation = useMutation({
    mutationFn: async (params: { text: string; targetLang: string }) => {
      const response = await fetch('http://localhost:5024/api/v1/languages/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      });
      if (!response.ok) throw new Error('Translation test failed');
      return response.json();
    },
    onSuccess: (data) => {
      setTranslationResult(data);
      toast.success('Translation test completed');
    },
    onError: () => {
      toast.error('Translation test failed');
    }
  });

  // Toggle language activation
  const toggleLanguageMutation = useMutation({
    mutationFn: async (languageCode: string) => {
      const response = await fetch(`http://localhost:5024/api/v1/languages/${languageCode}/toggle`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to toggle language');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['languages'] });
      toast.success('Language status updated');
    }
  });

  // Clear translation cache
  const clearCacheMutation = useMutation({
    mutationFn: async (languageCode?: string) => {
      const url = languageCode 
        ? `http://localhost:5024/api/v1/languages/cache/clear/${languageCode}`
        : 'http://localhost:5024/api/v1/languages/cache/clear';
      const response = await fetch(url, { method: 'POST' });
      if (!response.ok) throw new Error('Failed to clear cache');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['translation-cache-stats'] });
      toast.success('Translation cache cleared');
    }
  });

  const getTierColor = (tier: number) => {
    switch (tier) {
      case 1: return 'text-green-600 bg-green-50';
      case 2: return 'text-yellow-600 bg-yellow-50';
      case 3: return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getQualityColor = (score: number) => {
    if (score >= 0.85) return 'text-green-600';
    if (score >= 0.7) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Globe className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Multilingual Support</h2>
              <p className="text-sm text-gray-500">Manage language configurations and translations</p>
            </div>
          </div>
          <button
            onClick={() => clearCacheMutation.mutate()}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Clear All Cache
          </button>
        </div>
      </div>

      {/* Language Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {languages?.map((lang: LanguageConfig) => (
          <div key={lang.code} className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <Languages className="w-5 h-5 text-gray-400" />
                <div>
                  <h3 className="font-semibold text-gray-900">{lang.name}</h3>
                  <p className="text-sm text-gray-500">{lang.nativeName}</p>
                </div>
              </div>
              <button
                onClick={() => toggleLanguageMutation.mutate(lang.code)}
                className={`p-2 rounded-lg ${
                  lang.isActive 
                    ? 'bg-green-100 text-green-600' 
                    : 'bg-gray-100 text-gray-400'
                }`}
              >
                {lang.isActive ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
              </button>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Tier</span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getTierColor(lang.tier)}`}>
                  Tier {lang.tier}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Performance</span>
                <span className={`text-sm font-medium ${getQualityColor(lang.modelPerformanceScore)}`}>
                  {(lang.modelPerformanceScore * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Efficiency</span>
                <span className="text-sm font-medium">
                  {(lang.tokenizerEfficiency * 100).toFixed(0)}%
                </span>
              </div>
              {lang.isRtl && (
                <div className="mt-2 px-2 py-1 bg-blue-50 rounded text-xs text-blue-600">
                  RTL Language
                </div>
              )}
            </div>

            {/* Language Metrics */}
            {metrics?.find((m: LanguageMetrics) => m.languageCode === lang.code) && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">Requests Today</span>
                    <span className="font-medium">
                      {metrics.find((m: LanguageMetrics) => m.languageCode === lang.code)?.totalRequests || 0}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">Avg Response</span>
                    <span className="font-medium">
                      {metrics.find((m: LanguageMetrics) => m.languageCode === lang.code)?.avgResponseTimeMs || 0}ms
                    </span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">Quality Score</span>
                    <span className={`font-medium ${
                      getQualityColor(metrics.find((m: LanguageMetrics) => m.languageCode === lang.code)?.avgQualityScore || 0)
                    }`}>
                      {((metrics.find((m: LanguageMetrics) => m.languageCode === lang.code)?.avgQualityScore || 0) * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Translation Tester */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Translation Tester</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Test Message
              </label>
              <textarea
                value={testText}
                onChange={(e) => setTestText(e.target.value)}
                placeholder="Enter text to test translation..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={4}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Target Language
              </label>
              <select
                value={selectedLanguage}
                onChange={(e) => setSelectedLanguage(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                {languages?.filter((l: LanguageConfig) => l.isActive).map((lang: LanguageConfig) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.name} ({lang.nativeName})
                  </option>
                ))}
              </select>
            </div>
            
            <button
              onClick={() => testTranslationMutation.mutate({ 
                text: testText, 
                targetLang: selectedLanguage 
              })}
              disabled={!testText || testTranslationMutation.isPending}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <MessageSquare className="w-4 h-4" />
              Test Translation
            </button>
          </div>
          
          {/* Translation Result */}
          {translationResult && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="font-medium text-gray-900 mb-3">Translation Result</h4>
              
              <div className="space-y-3">
                <div>
                  <span className="text-xs text-gray-500">Detected Language</span>
                  <p className="text-sm font-medium">{translationResult.detectedLanguage}</p>
                </div>
                
                <div>
                  <span className="text-xs text-gray-500">Translated Text</span>
                  <p className="text-sm font-medium">{translationResult.translatedText}</p>
                </div>
                
                <div>
                  <span className="text-xs text-gray-500">Quality Score</span>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${translationResult.qualityScore * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium">
                      {(translationResult.qualityScore * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
                
                <div>
                  <span className="text-xs text-gray-500">Provider</span>
                  <p className="text-sm font-medium">{translationResult.provider}</p>
                </div>
                
                <div>
                  <span className="text-xs text-gray-500">Processing Time</span>
                  <p className="text-sm font-medium">{translationResult.processingTime}ms</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Cache Statistics */}
      {cacheStats && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Translation Cache</h3>
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-yellow-500" />
              <span className="text-sm text-gray-600">
                {cacheStats.totalEntries} cached translations
              </span>
            </div>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{cacheStats.hitRate}%</div>
              <div className="text-xs text-gray-500">Cache Hit Rate</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{cacheStats.avgUsageCount}</div>
              <div className="text-xs text-gray-500">Avg Usage Count</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{cacheStats.memorySizeMb}MB</div>
              <div className="text-xs text-gray-500">Memory Usage</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{cacheStats.languagePairs}</div>
              <div className="text-xs text-gray-500">Language Pairs</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MultilingualManager;