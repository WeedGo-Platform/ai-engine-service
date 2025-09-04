import { useState, useRef } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { motion } from 'framer-motion';
import apiService from '../services/api';

interface Model {
  id: string;
  name: string;
  type: string;
  size: string;
  status: 'active' | 'inactive' | 'loading' | 'error';
  performance: {
    accuracy: number;
    latency: number;
    throughput: number;
    memoryUsage: number;
  };
  capabilities: string[];
  lastDeployed?: string;
  version: string;
}

interface ModelConfig {
  temperature: number;
  max_tokens: number;
  top_p: number;
  repetition_penalty: number;
}

export default function ModelDeployment() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedModel, setSelectedModel] = useState<string>('llama2-7b');
  const [isDeploying, setIsDeploying] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [showImportModal, setShowImportModal] = useState(false);
  const [showFineTuneModal, setShowFineTuneModal] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [modelConfig, setModelConfig] = useState<ModelConfig>({
    temperature: 0.7,
    max_tokens: 150,
    top_p: 0.9,
    repetition_penalty: 1.1
  });

  // Fetch active model from API
  const { data: activeModelData, isLoading: activeModelLoading, error: activeModelError } = useQuery({
    queryKey: ['active-model'],
    queryFn: async () => {
      return await apiService.getActiveModel();
    },
    refetchInterval: 30000, // Refetch every 30 seconds
    retry: 3,
    retryDelay: 1000,
  });

  // Fetch available models from API
  const { data: availableModelsData, isLoading: modelsLoading, error: modelsError } = useQuery({
    queryKey: ['available-models'],
    queryFn: async () => {
      return await apiService.getAvailableModels();
    },
    refetchInterval: 60000, // Refetch every minute
    retry: 3,
    retryDelay: 1000,
  });

  // Fetch model deployments history from API
  const { data: deploymentsData, isLoading: deploymentsLoading, error: deploymentsError } = useQuery({
    queryKey: ['model-deployments'],
    queryFn: async () => {
      return await apiService.getModelDeployments();
    },
    refetchInterval: 60000,
    retry: 3,
    retryDelay: 1000,
  });

  // Process and combine the data from API calls
  const processModelsData = () => {
    if (!availableModelsData?.models) return [];
    
    const activeModelId = activeModelData?.model || activeModelData?.model_id;
    
    return availableModelsData.models.map((model: any) => {
      // Find deployment history for this model
      const deployment = deploymentsData?.deployments?.find((d: any) => d.model_id === model.id || d.model_name === model.name);
      
      return {
        id: model.id || model.name,
        name: model.name || model.display_name || model.id,
        type: model.type || model.model_type || 'AI Model',
        size: model.size || model.model_size || 'Unknown',
        status: (activeModelId === model.id || activeModelId === model.name) ? 'active' : 'inactive',
        performance: {
          accuracy: model.metrics?.accuracy || model.accuracy || 0.85,
          latency: model.metrics?.latency || model.latency || 50,
          throughput: model.metrics?.throughput || model.throughput || 100,
          memoryUsage: model.metrics?.memory_usage || model.memory_usage || 4.0,
        },
        capabilities: model.capabilities || model.features || ['General AI'],
        lastDeployed: deployment?.deployed_at || deployment?.timestamp || model.last_deployed,
        version: model.version || deployment?.version || '1.0',
      };
    });
  };

  const models = processModelsData();

  // Deploy model mutation
  const deployModel = useMutation({
    mutationFn: async (modelId: string) => {
      setIsDeploying(true);
      
      // Simulate deployment progress for UI
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 300);

      try {
        // Use apiService to deploy model
        const result = await apiService.deployModel(modelId);

        clearInterval(progressInterval);
        setUploadProgress(100);
        
        await new Promise(resolve => setTimeout(resolve, 500));
        
        return { success: true, modelId, result };
      } catch (error) {
        clearInterval(progressInterval);
        throw error;
      } finally {
        setIsDeploying(false);
        setUploadProgress(0);
      }
    },
    onSuccess: (data) => {
      toast.success(`Model ${data.modelId} deployed successfully`);
      setSelectedModel(data.modelId);
      // Invalidate relevant queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['active-model'] });
      queryClient.invalidateQueries({ queryKey: ['model-deployments'] });
      queryClient.invalidateQueries({ queryKey: ['available-models'] });
    },
    onError: () => {
      toast.error('Failed to deploy model');
    },
  });

  // Apply configuration mutation
  const applyConfig = useMutation({
    mutationFn: async (config: ModelConfig) => {
      return await apiService.updateModelConfig(config);
    },
    onSuccess: () => {
      toast.success('Configuration applied successfully');
    },
    onError: () => {
      toast.error('Failed to apply configuration');
    }
  });

  // Import model handler
  const handleImportModel = async () => {
    if (!importFile) {
      toast.error('Please select a model file');
      return;
    }

    const formData = new FormData();
    formData.append('model', importFile);
    formData.append('name', importFile.name.replace(/\.[^/.]+$/, ''));

    try {
      const newModel = await apiService.importModel(formData);
      
      toast.success('Model imported successfully');
      setShowImportModal(false);
      setImportFile(null);
      
      // Refresh available models
      queryClient.invalidateQueries({ queryKey: ['available-models'] });
    } catch (error) {
      toast.error('Failed to import model');
    }
  };


  const activeModel = models.find(m => m.status === 'active');
  const isLoading = activeModelLoading || modelsLoading || deploymentsLoading;
  const hasErrors = activeModelError || modelsError || deploymentsError;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Model Deployment</h2>
            <p className="text-gray-600 mt-1">Deploy and manage AI models for the budtender</p>
          </div>
          <div className="flex items-center space-x-4">
            <button 
              onClick={() => {
                queryClient.invalidateQueries({ queryKey: ['available-models'] });
                queryClient.invalidateQueries({ queryKey: ['active-model'] });
                queryClient.invalidateQueries({ queryKey: ['model-deployments'] });
              }}
              disabled={isLoading}
              className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 disabled:opacity-50"
            >
              {isLoading ? 'Loading...' : 'Refresh'}
            </button>
            <button 
              onClick={() => setShowImportModal(true)}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
            >
              Import Model
            </button>
            <button 
              onClick={() => setShowFineTuneModal(true)}
              className="px-4 py-2 bg-purple-haze-600 text-white rounded-lg hover:bg-purple-haze-700"
            >
              Fine-tune Current
            </button>
          </div>
        </div>
      </div>

      {/* Error State */}
      {hasErrors && !isLoading && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6">
          <div className="flex items-center space-x-3">
            <div className="text-red-500">
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h3 className="text-red-800 font-medium">Failed to Load Model Data</h3>
              <p className="text-red-700 text-sm mt-1">
                Unable to connect to the AI service. Please check your connection and try again.
              </p>
            </div>
            <button 
              onClick={() => {
                queryClient.invalidateQueries({ queryKey: ['available-models'] });
                queryClient.invalidateQueries({ queryKey: ['active-model'] });
                queryClient.invalidateQueries({ queryKey: ['model-deployments'] });
              }}
              className="ml-auto px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
            <div className="h-8 bg-gray-200 rounded w-1/2 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-1/3"></div>
          </div>
        </div>
      )}

      {/* Current Active Model */}
      {!isLoading && activeModel && (
        <div className="bg-gradient-to-r from-weed-green-500 to-weed-green-600 rounded-xl shadow-lg p-6 text-white">
          <div className="flex justify-between items-start">
            <div>
              <h3 className="text-xl font-bold mb-2">Active Model</h3>
              <p className="text-2xl font-bold">{activeModel.name}</p>
              <p className="text-green-100">Version {activeModel.version}</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-green-100">Deployed</p>
              <p className="text-lg font-semibold">
                {activeModel.lastDeployed ? new Date(activeModel.lastDeployed).toLocaleDateString() : 'Now'}
              </p>
            </div>
          </div>
          
          <div className="grid grid-cols-4 gap-4 mt-6">
            <div>
              <p className="text-green-100 text-sm">Accuracy</p>
              <p className="text-2xl font-bold">{(activeModel.performance.accuracy * 100).toFixed(0)}%</p>
            </div>
            <div>
              <p className="text-green-100 text-sm">Latency</p>
              <p className="text-2xl font-bold">{activeModel.performance.latency}ms</p>
            </div>
            <div>
              <p className="text-green-100 text-sm">Throughput</p>
              <p className="text-2xl font-bold">{activeModel.performance.throughput}/min</p>
            </div>
            <div>
              <p className="text-green-100 text-sm">Memory</p>
              <p className="text-2xl font-bold">{activeModel.performance.memoryUsage}GB</p>
            </div>
          </div>
        </div>
      )}

      {/* Available Models */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Available Models</h3>
        
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="border-2 border-gray-200 rounded-xl p-6 animate-pulse">
                <div className="h-6 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
                <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-2/3"></div>
              </div>
            ))}
          </div>
        ) : models.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-500 mb-4">
              <svg className="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Models Available</h3>
            <p className="text-gray-600 mb-4">No AI models are currently available. Try importing a model or check your connection.</p>
            <button 
              onClick={() => {
                queryClient.invalidateQueries({ queryKey: ['available-models'] });
                queryClient.invalidateQueries({ queryKey: ['active-model'] });
              }}
              className="px-4 py-2 bg-weed-green-500 text-white rounded-lg hover:bg-weed-green-600"
            >
              Refresh Models
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {models.map((model) => (
            <motion.div
              key={model.id}
              whileHover={{ scale: 1.02 }}
              className={`border-2 rounded-xl p-6 cursor-pointer transition-all ${
                model.status === 'active'
                  ? 'border-weed-green-500 bg-green-50'
                  : 'border-gray-200 hover:border-purple-haze-400'
              }`}
              onClick={() => !isDeploying && setSelectedModel(model.id)}
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h4 className="text-lg font-semibold text-gray-900">{model.name}</h4>
                  <p className="text-sm text-gray-600">{model.type} • {model.size}</p>
                </div>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                  model.status === 'active'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-600'
                }`}>
                  {model.status}
                </span>
              </div>

              {/* Capabilities */}
              <div className="mb-4">
                <p className="text-sm text-gray-600 mb-2">Capabilities:</p>
                <div className="flex flex-wrap gap-1">
                  {model.capabilities.map((cap) => (
                    <span key={cap} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                      {cap}
                    </span>
                  ))}
                </div>
              </div>

              {/* Performance Metrics */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <p className="text-xs text-gray-600">Accuracy</p>
                  <div className="flex items-center">
                    <div className="flex-1 bg-gray-200 rounded-full h-1.5 mr-2">
                      <div
                        className="bg-weed-green-500 h-1.5 rounded-full"
                        style={{ width: `${model.performance.accuracy * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-xs font-medium">{(model.performance.accuracy * 100).toFixed(0)}%</span>
                  </div>
                </div>
                <div>
                  <p className="text-xs text-gray-600">Latency</p>
                  <p className="text-sm font-medium">{model.performance.latency}ms</p>
                </div>
              </div>

              {/* Deploy Button */}
              {model.status !== 'active' && selectedModel === model.id && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="mt-4"
                >
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deployModel.mutate(model.id);
                    }}
                    disabled={isDeploying}
                    className="w-full px-4 py-2 bg-purple-haze-600 text-white rounded-lg hover:bg-purple-haze-700 disabled:opacity-50"
                  >
                    {isDeploying ? 'Deploying...' : 'Deploy This Model'}
                  </button>
                </motion.div>
              )}
            </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Deployment Progress */}
      {isDeploying && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-8 max-w-md w-full">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Deploying Model</h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm text-gray-600 mb-2">
                  <span>Progress</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="bg-gray-200 rounded-full h-2">
                  <motion.div
                    className="bg-weed-green-500 h-2 rounded-full"
                    animate={{ width: `${uploadProgress}%` }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <div className={`w-4 h-4 rounded-full ${uploadProgress > 0 ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                  <span className="text-sm text-gray-700">Downloading model weights</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className={`w-4 h-4 rounded-full ${uploadProgress > 30 ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                  <span className="text-sm text-gray-700">Loading into memory</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className={`w-4 h-4 rounded-full ${uploadProgress > 60 ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                  <span className="text-sm text-gray-700">Initializing inference engine</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className={`w-4 h-4 rounded-full ${uploadProgress > 90 ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                  <span className="text-sm text-gray-700">Running health checks</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Import Model Modal */}
      {showImportModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-8 max-w-md w-full">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Import Model</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Model File
                </label>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".bin,.safetensors,.gguf,.onnx"
                  onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                  className="hidden"
                />
                <div 
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-weed-green-500"
                >
                  {importFile ? (
                    <div>
                      <p className="text-sm font-medium text-gray-900">{importFile.name}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {(importFile.size / (1024 * 1024)).toFixed(1)} MB
                      </p>
                    </div>
                  ) : (
                    <div>
                      <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                      <p className="mt-2 text-sm text-gray-600">Click to select model file</p>
                      <p className="text-xs text-gray-500">Supported: .bin, .safetensors, .gguf, .onnx</p>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={() => {
                    setShowImportModal(false);
                    setImportFile(null);
                  }}
                  className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={handleImportModel}
                  disabled={!importFile}
                  className="flex-1 px-4 py-2 bg-weed-green-500 text-white rounded-lg hover:bg-weed-green-600 disabled:opacity-50"
                >
                  Import
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Fine-tune Modal */}
      {showFineTuneModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-8 max-w-md w-full">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Fine-tune Model</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Training Dataset
                </label>
                <input
                  type="file"
                  accept=".json,.jsonl,.csv"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Epochs
                </label>
                <input
                  type="number"
                  defaultValue="3"
                  min="1"
                  max="10"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Learning Rate
                </label>
                <input
                  type="number"
                  defaultValue="0.0001"
                  step="0.0001"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                <p className="text-sm text-yellow-800">
                  <strong>Note:</strong> Fine-tuning can take several hours depending on dataset size and model complexity.
                </p>
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={() => setShowFineTuneModal(false)}
                  className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={async () => {
                    try {
                      const formData = new FormData();
                      const fileInput = document.querySelector('input[type="file"][accept=".json,.jsonl,.csv"]') as HTMLInputElement;
                      const epochsInput = document.querySelector('input[type="number"][defaultValue="3"]') as HTMLInputElement;
                      const learningRateInput = document.querySelector('input[type="number"][defaultValue="0.0001"]') as HTMLInputElement;
                      
                      if (fileInput?.files?.[0]) {
                        formData.append('dataset', fileInput.files[0]);
                      }
                      formData.append('epochs', epochsInput?.value || '3');
                      formData.append('learning_rate', learningRateInput?.value || '0.0001');
                      
                      await apiService.fineTuneModel(formData);
                      toast.success('Fine-tuning job started');
                      setShowFineTuneModal(false);
                    } catch (error) {
                      toast.error('Failed to start fine-tuning');
                    }
                  }}
                  className="flex-1 px-4 py-2 bg-purple-haze-600 text-white rounded-lg hover:bg-purple-haze-700"
                >
                  Start Fine-tuning
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Model Configuration */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Model Configuration</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Temperature ({modelConfig.temperature})
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={modelConfig.temperature}
              onChange={(e) => setModelConfig(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-600 mt-1">
              <span>Conservative</span>
              <span>Creative</span>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Max Tokens
            </label>
            <input
              type="number"
              value={modelConfig.max_tokens}
              onChange={(e) => setModelConfig(prev => ({ ...prev, max_tokens: parseInt(e.target.value) }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Top P
            </label>
            <input
              type="number"
              step="0.1"
              value={modelConfig.top_p}
              onChange={(e) => setModelConfig(prev => ({ ...prev, top_p: parseFloat(e.target.value) }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Repetition Penalty
            </label>
            <input
              type="number"
              step="0.1"
              value={modelConfig.repetition_penalty}
              onChange={(e) => setModelConfig(prev => ({ ...prev, repetition_penalty: parseFloat(e.target.value) }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>
        </div>
        
        <div className="mt-6 flex justify-end space-x-3">
          <button 
            onClick={() => setModelConfig({
              temperature: 0.7,
              max_tokens: 150,
              top_p: 0.9,
              repetition_penalty: 1.1
            })}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
          >
            Reset to Defaults
          </button>
          <button 
            onClick={() => applyConfig.mutate(modelConfig)}
            className="px-4 py-2 bg-weed-green-500 text-white rounded-lg hover:bg-weed-green-600"
          >
            Apply Configuration
          </button>
        </div>
      </div>
    </div>
  );
}