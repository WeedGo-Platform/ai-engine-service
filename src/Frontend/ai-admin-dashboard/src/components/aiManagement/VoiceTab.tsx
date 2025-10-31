import React, { useState, useEffect } from 'react';
import {
  Volume2,
  Loader2,
  Radio,
  Monitor,
  Cloud,
  CheckCircle,
  AlertCircle,
  Play
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { getApiEndpoint } from '@/config/app.config';

interface VoiceTabProps {
  token?: string;
}

interface VoiceProvider {
  id: string;
  name: string;
  type: 'local' | 'cloud';
  active: boolean;
}

const VoiceTab: React.FC<VoiceTabProps> = ({ token }) => {
  const [providers, setProviders] = useState<VoiceProvider[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [testingProvider, setTestingProvider] = useState<string | null>(null);

  // Fetch providers list
  const fetchProviders = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(getApiEndpoint('/voice-providers/list'), {
        headers: {
          'Authorization': token ? `Bearer ${token}` : ''
        }
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.error || `Server error: ${response.status}`);
      }
      
      const data = await response.json();
      if (data.providers) {
        setProviders(data.providers);
      }
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to fetch voice providers';
      setError(errorMsg);
      console.error('Error fetching voice providers:', error);
      toast.error(errorMsg);
    }
    setIsLoading(false);
  };

  // Set active provider
  const setActiveProvider = async (providerId: string) => {
    try {
      const response = await fetch(getApiEndpoint('/voice-providers/active'), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: JSON.stringify({ provider: providerId })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.error || 'Failed to set active provider');
      }

      toast.success(`Switched to ${providers.find(p => p.id === providerId)?.name}`);
      await fetchProviders(); // Refresh the list
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to set active provider';
      console.error('Error setting active provider:', error);
      toast.error(errorMsg);
    }
  };

  // Test provider voice
  const testProvider = async (providerId: string) => {
    setTestingProvider(providerId);
    try {
      const response = await fetch(getApiEndpoint('/voice-providers/test'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: JSON.stringify({
          provider: providerId,
          text: 'Welcome to WeedGo! How can I help you today?'
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to test voice provider: ${errorText}`);
      }

      const blob = await response.blob();
      console.log('Audio blob:', { type: blob.type, size: blob.size });
      
      const audioURL = URL.createObjectURL(blob);
      const audio = new Audio(audioURL);
      
      // Handle playback completion
      audio.onended = () => {
        URL.revokeObjectURL(audioURL);
        console.log('Audio playback completed');
      };
      
      // Handle playback errors
      audio.onerror = (e) => {
        console.error('Audio playback error:', e);
        URL.revokeObjectURL(audioURL);
      };
      
      // Attempt to play
      try {
        await audio.play();
        console.log('Audio playing...');
        toast.success('🔊 Playing voice test');
      } catch (playError) {
        // Handle autoplay restrictions
        console.warn('Autoplay blocked, trying user interaction:', playError);
        toast.info('Click to play voice test', {
          duration: 5000,
          onClick: () => {
            audio.play().catch(e => console.error('Manual play failed:', e));
          }
        });
      }
    } catch (error) {
      console.error('Error testing provider:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to test voice provider');
    } finally {
      setTestingProvider(null);
    }
  };

  useEffect(() => {
    fetchProviders();
  }, []);

  if (isLoading && providers.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600 dark:text-indigo-400" />
        <span className="ml-3 text-gray-600 dark:text-gray-400">Loading voice providers...</span>
      </div>
    );
  }

  if (error && providers.length === 0) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 text-red-500 dark:text-red-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Failed to Load Voice Providers</h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{error}</p>
        <button
          onClick={fetchProviders}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  const activeProvider = providers.find(p => p.active);
  const localProviders = providers.filter(p => p.type === 'local');
  const cloudProviders = providers.filter(p => p.type === 'cloud');

  return (
    <div className="space-y-6">
      {/* Current Active Provider */}
      <div className="bg-gradient-to-r from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Active Voice Provider</h3>
            {activeProvider ? (
              <div className="flex items-center gap-2">
                {activeProvider.type === 'local' ? (
                  <Monitor className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                ) : (
                  <Cloud className="h-5 w-5 text-green-600 dark:text-green-400" />
                )}
                <span className="text-lg font-semibold text-gray-900 dark:text-white">{activeProvider.name}</span>
                <span className="px-2 py-0.5 text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-full">
                  Active
                </span>
              </div>
            ) : (
              <span className="text-gray-500 dark:text-gray-400">No provider selected</span>
            )}
          </div>
        </div>
      </div>

      {/* Local Voice Models */}
      {localProviders.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Monitor className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            Local Voice Models
          </h3>
          <div className="grid gap-4">
            {localProviders.map((provider) => (
              <div
                key={provider.id}
                className={`border rounded-lg p-4 transition-all ${
                  provider.active
                    ? 'border-blue-500 dark:border-blue-400 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Monitor className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white">{provider.name}</h4>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Local voice synthesis</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {provider.active ? (
                      <span className="flex items-center gap-1 px-3 py-1 text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-full">
                        <CheckCircle className="h-3 w-3" />
                        Active
                      </span>
                    ) : (
                      <button
                        onClick={() => setActiveProvider(provider.id)}
                        className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                      >
                        Activate
                      </button>
                    )}
                    <button
                      onClick={() => testProvider(provider.id)}
                      disabled={testingProvider === provider.id}
                      className="px-3 py-2 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors disabled:opacity-50 flex items-center gap-2"
                    >
                      {testingProvider === provider.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Play className="h-4 w-4" />
                      )}
                      <span>Test</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Cloud Providers */}
      {cloudProviders.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Cloud className="h-5 w-5 text-green-600 dark:text-green-400" />
            Cloud Voice Providers
          </h3>
          <div className="grid gap-4">
            {cloudProviders.map((provider) => (
              <div
                key={provider.id}
                className={`border rounded-lg p-4 transition-all ${
                  provider.active
                    ? 'border-green-500 dark:border-green-400 bg-green-50 dark:bg-green-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Cloud className="h-5 w-5 text-green-600 dark:text-green-400" />
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white">{provider.name}</h4>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Cloud-based voice synthesis</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {provider.active ? (
                      <span className="flex items-center gap-1 px-3 py-1 text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-full">
                        <CheckCircle className="h-3 w-3" />
                        Active
                      </span>
                    ) : (
                      <button
                        onClick={() => setActiveProvider(provider.id)}
                        className="px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                      >
                        Activate
                      </button>
                    )}
                    <button
                      onClick={() => testProvider(provider.id)}
                      disabled={testingProvider === provider.id}
                      className="px-3 py-2 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors disabled:opacity-50 flex items-center gap-2"
                    >
                      {testingProvider === provider.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Play className="h-4 w-4" />
                      )}
                      <span>Test</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {providers.length === 0 && !isLoading && (
        <div className="text-center py-12">
          <Volume2 className="h-12 w-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400">No voice providers available</p>
        </div>
      )}
    </div>
  );
};

export default VoiceTab;