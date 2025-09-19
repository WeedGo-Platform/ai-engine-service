import React, { useState, useEffect } from 'react';
import { Bot, Loader2, AlertCircle, CheckCircle, Cpu } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';

interface Model {
  name: string;
  filename: string;
  path: string;
  size_gb: number;
}

interface ModelState {
  current_model: string | null;
  current_agent: string | null;
  current_personality: string | null;
  is_loaded: boolean;
  loading_status: string | null;
}

const AIManagement: React.FC = () => {
  const [models, setModels] = useState<Model[]>([]);
  const [currentModel, setCurrentModel] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [isFetchingModels, setIsFetchingModels] = useState(true);
  const [modelState, setModelState] = useState<ModelState | null>(null);
  const { user, isSuperAdmin: checkIsSuperAdmin } = useAuth();

  const isSuperAdmin = checkIsSuperAdmin();
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5024';

  // Fetch available models
  const fetchModels = async () => {
    setIsFetchingModels(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${apiUrl}/api/admin/models`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch models');
      }

      const data = await response.json();
      setModels(data.models || []);
      setCurrentModel(data.current_model);

      // Set initial selected model to current model if exists
      if (data.current_model && !selectedModel) {
        setSelectedModel(data.current_model);
      }
    } catch (error) {
      console.error('Error fetching models:', error);
      toast.error('Failed to fetch available models');
    } finally {
      setIsFetchingModels(false);
    }
  };

  // Fetch current model status
  const fetchModelStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${apiUrl}/api/admin/model`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch model status');
      }

      const data = await response.json();
      // Map the API response to our ModelState interface
      setModelState({
        current_model: data.model || data.current_model,
        current_agent: data.agent || data.current_agent,
        current_personality: data.personality || data.current_personality,
        is_loaded: data.loaded || data.ready || false,
        loading_status: data.message || null
      });
      setCurrentModel(data.model || data.current_model);
    } catch (error) {
      console.error('Error fetching model status:', error);
    }
  };

  // Load selected model
  const loadModel = async () => {
    if (!selectedModel || !isSuperAdmin) return;

    setIsLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${apiUrl}/api/admin/model/load`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: selectedModel,
          agent: 'dispensary',
          personality: 'friendly'
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to load model');
      }

      const data = await response.json();
      toast.success(`Model ${selectedModel} loaded successfully`);
      setCurrentModel(selectedModel);

      // Refresh model status
      await fetchModelStatus();
    } catch (error: any) {
      console.error('Error loading model:', error);
      toast.error(error.message || 'Failed to load model');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
    fetchModelStatus();

    // Refresh status every 30 seconds
    const interval = setInterval(() => {
      fetchModelStatus();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
            <Bot className="h-8 w-8" />
            AI Model Management
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Manage and monitor AI language models
          </p>
        </div>

        {/* Current Model Status */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Cpu className="h-5 w-5" />
            Current Model Status
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Active Model</p>
              <p className="text-lg font-medium text-gray-900 dark:text-white">
                {modelState?.current_model || currentModel || 'None'}
              </p>
            </div>

            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Agent</p>
              <p className="text-lg font-medium text-gray-900 dark:text-white">
                {modelState?.current_agent || 'dispensary'}
              </p>
            </div>

            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Personality</p>
              <p className="text-lg font-medium text-gray-900 dark:text-white">
                {modelState?.current_personality || 'friendly'}
              </p>
            </div>

            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Status</p>
              <div className="flex items-center gap-2">
                {modelState?.is_loaded ? (
                  <>
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <span className="text-lg font-medium text-green-600 dark:text-green-400">Loaded</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-5 w-5 text-yellow-500" />
                    <span className="text-lg font-medium text-yellow-600 dark:text-yellow-400">Not Loaded</span>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Model Selection */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Model Selection
          </h2>

          {isFetchingModels ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Available Models
                </label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  disabled={!isSuperAdmin || isLoading}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <option value="">Select a model...</option>
                  {models.map((model) => (
                    <option key={model.name} value={model.name}>
                      {model.name} ({model.size_gb} GB)
                    </option>
                  ))}
                </select>
              </div>

              {selectedModel && (
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                  <p className="text-sm text-blue-800 dark:text-blue-300">
                    <strong>Selected:</strong> {selectedModel}
                  </p>
                  {models.find(m => m.name === selectedModel) && (
                    <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                      File: {models.find(m => m.name === selectedModel)?.filename}
                    </p>
                  )}
                </div>
              )}

              {isSuperAdmin ? (
                <div className="flex items-center gap-4">
                  <button
                    onClick={loadModel}
                    disabled={!selectedModel || isLoading || selectedModel === currentModel}
                    className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Loading Model...
                      </>
                    ) : (
                      <>
                        <Bot className="h-4 w-4" />
                        Load Model
                      </>
                    )}
                  </button>

                  {selectedModel === currentModel && (
                    <span className="text-sm text-green-600 dark:text-green-400 flex items-center gap-1">
                      <CheckCircle className="h-4 w-4" />
                      Currently loaded
                    </span>
                  )}
                </div>
              ) : (
                <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4">
                  <p className="text-sm text-yellow-800 dark:text-yellow-300 flex items-center gap-2">
                    <AlertCircle className="h-4 w-4" />
                    Only Super Admins can change the loaded model
                  </p>
                </div>
              )}

              {/* Model Information */}
              {models.length > 0 && (
                <div className="mt-6">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
                    Available Models ({models.length})
                  </h3>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                      <thead>
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                            Model Name
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                            File Name
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                            Size
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                            Status
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                        {models.map((model) => (
                          <tr key={model.name} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                            <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">
                              {model.name}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                              {model.filename}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                              {model.size_gb} GB
                            </td>
                            <td className="px-4 py-3 text-sm">
                              {model.name === currentModel ? (
                                <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400 rounded-full text-xs">
                                  <CheckCircle className="h-3 w-3" />
                                  Active
                                </span>
                              ) : (
                                <span className="inline-flex items-center px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded-full text-xs">
                                  Inactive
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AIManagement;