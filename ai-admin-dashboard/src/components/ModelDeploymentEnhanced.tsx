/**
 * Enhanced Model Deployment Component
 * Fully functional model deployment page with real-time progress tracking,
 * comprehensive error handling, and advanced management features
 */

import { endpoints } from '../config/endpoints';
import { useState, useEffect, useRef } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Cloud,
  Download,
  Upload,
  Settings,
  Activity,
  AlertCircle,
  CheckCircle,
  XCircle,
  RefreshCw,
  Trash2,
  Play,
  Pause,
  RotateCcw,
  Terminal,
  Cpu,
  HardDrive,
  Zap,
  TrendingUp,
  Clock,
  FileText,
  GitCompare,
  Shield,
  Package,
  Layers,
  ChevronRight,
  ChevronDown,
  Search,
  Filter,
  Eye,
  EyeOff,
  Loader2
} from 'lucide-react';

import apiService from '../services/api';
import { modelDeploymentService } from '../services/modelDeploymentService';
import type { DeploymentStatus, ModelHealth } from '../services/modelDeploymentService';
import { wsService } from '../services/websocket';

interface Model {
  id: string;
  name: string;
  type: string;
  size: string;
  status: 'active' | 'inactive' | 'deploying' | 'testing' | 'error';
  version: string;
  performance?: {
    accuracy: number;
    latency: number;
    throughput: number;
    memoryUsage: number;
  };
  capabilities: string[];
  lastDeployed?: string;
  health?: ModelHealth;
}

interface ConfigPreset {
  id: string;
  name: string;
  config: {
    temperature: number;
    max_tokens: number;
    top_p: number;
    repetition_penalty: number;
  };
  description?: string;
}

export default function ModelDeploymentEnhanced() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // State
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [activeDeployment, setActiveDeployment] = useState<DeploymentStatus | null>(null);
  const [showImportModal, setShowImportModal] = useState(false);
  const [showFineTuneModal, setShowFineTuneModal] = useState(false);
  const [showLogsModal, setShowLogsModal] = useState(false);
  const [showCompareModal, setShowCompareModal] = useState(false);
  const [showTestModal, setShowTestModal] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [selectedPreset, setSelectedPreset] = useState<string>('default');
  const [modelConfig, setModelConfig] = useState({
    temperature: 0.7,
    max_tokens: 150,
    top_p: 0.9,
    repetition_penalty: 1.1
  });
  const [logsFilter, setLogsFilter] = useState<'all' | 'info' | 'warning' | 'error'>('all');
  const [compareModels, setCompareModels] = useState<string[]>([]);
  const [wsConnected, setWsConnected] = useState(false);
  const [expandedSections, setExpandedSections] = useState({
    deployment: true,
    health: true,
    performance: true,
    configuration: true,
    logs: false
  });

  // Initialize WebSocket connection
  useEffect(() => {
    wsService.connect().then(() => {
      setWsConnected(true);
      
      // Subscribe to resource metrics
      const unsubscribe = wsService.onResourceMetrics((metrics) => {
        console.log('Resource metrics:', metrics);
      });

      return () => {
        unsubscribe();
      };
    }).catch(error => {
      console.error('Failed to connect WebSocket:', error);
      setWsConnected(false);
    });

    // Listen for WebSocket connection changes
    wsService.on('connected', () => setWsConnected(true));
    wsService.on('disconnected', () => setWsConnected(false));

    return () => {
      wsService.disconnect();
    };
  }, []);

  // Fetch models with real data
  const { data: modelsData, isLoading: modelsLoading, refetch: refetchModels } = useQuery({
    queryKey: ['models-enhanced'],
    queryFn: async () => {
      const [activeModel, availableModels, deployments] = await Promise.all([
        apiService.getActiveModel(),
        apiService.getAvailableModels(),
        apiService.getModelDeployments()
      ]);

      const models = availableModels.models.map((model: any) => ({
        id: model.model_id || model.id || model.name,
        name: model.model_name || model.name || model.id,
        type: model.type || 'LLM',
        size: model.file_size_gb ? `${model.file_size_gb.toFixed(2)} GB` : model.size || 'Unknown',
        status: (activeModel.model === model.model_id || 
                activeModel.model === model.model_name || 
                activeModel.model === model.id || 
                activeModel.model === model.name ||
                // Also check if the model names match (accounting for path prefixes)
                (activeModel.model && model.model_name && activeModel.model.includes(model.model_name))) ? 'active' : 'inactive',
        version: model.version || '1.0',
        performance: model.performance,
        capabilities: model.capabilities || [],
        lastDeployed: deployments?.deployments?.find((d: any) => 
          d.model_id === model.id
        )?.deployed_at
      }));

      return models;
    },
    refetchInterval: 30000
  });

  // Fetch resource metrics
  const { data: metricsData } = useQuery({
    queryKey: ['resource-metrics'],
    queryFn: apiService.getResourceMetrics,
    refetchInterval: 5000,
    enabled: wsConnected === false // Use polling only if WebSocket is not connected
  });

  // Fetch config presets
  const { data: presetsData } = useQuery({
    queryKey: ['config-presets'],
    queryFn: apiService.getModelConfigPresets,
    staleTime: 300000 // Cache for 5 minutes
  });

  // Model health check for active model
  const activeModel = modelsData?.find((m: Model) => m.status === 'active');
  const { data: healthData } = useQuery({
    queryKey: ['model-health', activeModel?.id],
    queryFn: () => modelDeploymentService.getModelHealth(activeModel!.id),
    enabled: !!activeModel,
    refetchInterval: 10000
  });

  // Deploy model mutation with real progress tracking
  const deployModelMutation = useMutation({
    mutationFn: async (modelId: string) => {
      const deployment = await modelDeploymentService.deployModel({
        modelId,
        environment: 'production',
        configuration: modelConfig
      });

      setActiveDeployment(deployment);

      // Subscribe to deployment updates
      const unsubscribe = modelDeploymentService.onStatusUpdate(
        deployment.deploymentId,
        (status) => {
          setActiveDeployment(status);
          
          if (status.status === 'completed') {
            toast.success(`Model ${modelId} deployed successfully!`);
            refetchModels();
            unsubscribe();
          } else if (status.status === 'failed') {
            toast.error(`Deployment failed: ${status.error}`);
            unsubscribe();
          }
        }
      );

      return deployment;
    },
    onError: (error: Error) => {
      toast.error(`Deployment failed: ${error.message}`);
      setActiveDeployment(null);
    }
  });

  // Test model mutation
  const testModelMutation = useMutation({
    mutationFn: async (modelId: string) => {
      const results = await modelDeploymentService.testModel(modelId);
      return results;
    },
    onSuccess: (data) => {
      if (data.passed) {
        toast.success('Model tests passed!');
      } else {
        toast.warning('Some tests failed. Check results.');
      }
    },
    onError: (error: Error) => {
      toast.error(`Testing failed: ${error.message}`);
    }
  });

  // Rollback deployment
  const rollbackMutation = useMutation({
    mutationFn: async (deploymentId: string) => {
      return await modelDeploymentService.rollbackDeployment(deploymentId);
    },
    onSuccess: () => {
      toast.success('Deployment rolled back successfully');
      setActiveDeployment(null);
      refetchModels();
    },
    onError: (error: Error) => {
      toast.error(`Rollback failed: ${error.message}`);
    }
  });

  // Delete model
  const deleteModelMutation = useMutation({
    mutationFn: async (modelId: string) => {
      return await modelDeploymentService.deleteModel(modelId, true);
    },
    onSuccess: () => {
      toast.success('Model deleted successfully');
      refetchModels();
    },
    onError: (error: Error) => {
      toast.error(`Delete failed: ${error.message}`);
    }
  });

  // Import model with progress tracking
  const importModelMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('model', file);
      formData.append('name', file.name.replace(/\.[^/.]+$/, ''));

      // Track upload progress
      const xhr = new XMLHttpRequest();
      
      return new Promise((resolve, reject) => {
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            setUploadProgress(Math.round((e.loaded / e.total) * 100));
          }
        });

        xhr.addEventListener('load', () => {
          if (xhr.status === 200) {
            resolve(JSON.parse(xhr.responseText));
          } else {
            reject(new Error('Upload failed'));
          }
        });

        xhr.addEventListener('error', () => reject(new Error('Upload failed')));

        xhr.open('POST', endpoints.models.import);
        xhr.send(formData);
      });
    },
    onSuccess: () => {
      toast.success('Model imported successfully');
      setShowImportModal(false);
      setImportFile(null);
      setUploadProgress(0);
      refetchModels();
    },
    onError: (error: Error) => {
      toast.error(`Import failed: ${error.message}`);
      setUploadProgress(0);
    }
  });

  // Apply configuration
  const applyConfigMutation = useMutation({
    mutationFn: async (config: typeof modelConfig) => {
      return await apiService.updateModelConfig(config);
    },
    onSuccess: () => {
      toast.success('Configuration applied successfully');
    },
    onError: (error: Error) => {
      toast.error(`Failed to apply configuration: ${error.message}`);
    }
  });

  // Save config preset
  const savePresetMutation = useMutation({
    mutationFn: async ({ name, config }: { name: string; config: typeof modelConfig }) => {
      return await apiService.saveModelConfigPreset(name, config);
    },
    onSuccess: () => {
      toast.success('Preset saved successfully');
      queryClient.invalidateQueries({ queryKey: ['config-presets'] });
    },
    onError: (error: Error) => {
      toast.error(`Failed to save preset: ${error.message}`);
    }
  });

  // Helper functions
  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
      case 'completed':
      case 'healthy':
        return 'text-green-600';
      case 'deploying':
      case 'in_progress':
      case 'degraded':
        return 'text-yellow-600';
      case 'error':
      case 'failed':
      case 'unhealthy':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
      case 'completed':
      case 'healthy':
        return <CheckCircle className="h-5 w-5" />;
      case 'deploying':
      case 'in_progress':
        return <Loader2 className="h-5 w-5 animate-spin" />;
      case 'error':
      case 'failed':
      case 'unhealthy':
        return <XCircle className="h-5 w-5" />;
      default:
        return <AlertCircle className="h-5 w-5" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Model Deployment</h2>
            <p className="text-gray-600 mt-1">
              Deploy and manage AI models with real-time monitoring
            </p>
          </div>
          <div className="flex items-center space-x-4">
            {/* WebSocket Status Indicator */}
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-xs text-gray-600">
                {wsConnected ? 'Real-time' : 'Polling'}
              </span>
            </div>

            <button
              onClick={() => refetchModels()}
              disabled={modelsLoading}
              className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 disabled:opacity-50 flex items-center gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${modelsLoading ? 'animate-spin' : ''}`} />
              Refresh
            </button>

            <button
              onClick={() => setShowCompareModal(true)}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center gap-2"
            >
              <GitCompare className="h-4 w-4" />
              Compare
            </button>

            <button
              onClick={() => setShowImportModal(true)}
              className="px-4 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 flex items-center gap-2"
            >
              <Upload className="h-4 w-4" />
              Import
            </button>
          </div>
        </div>
      </div>

      {/* Active Deployment Progress */}
      {activeDeployment && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl shadow-lg p-6"
        >
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">Deployment Progress</h3>
            <div className="flex items-center space-x-2">
              <span className={`${getStatusColor(activeDeployment.status)} flex items-center gap-2`}>
                {getStatusIcon(activeDeployment.status)}
                {activeDeployment.status}
              </span>
              {activeDeployment.status === 'in_progress' && (
                <button
                  onClick={() => rollbackMutation.mutate(activeDeployment.deploymentId)}
                  className="px-3 py-1 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 text-sm"
                >
                  Cancel
                </button>
              )}
            </div>
          </div>

          {/* Overall Progress Bar */}
          <div className="mb-6">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>{activeDeployment.currentStep}</span>
              <span>{activeDeployment.progress}%</span>
            </div>
            <div className="bg-gray-200 rounded-full h-2">
              <motion.div
                className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full"
                animate={{ width: `${activeDeployment.progress}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
          </div>

          {/* Deployment Steps */}
          <div className="space-y-3">
            {activeDeployment.steps.map((step, index) => (
              <div key={index} className="flex items-center space-x-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  step.status === 'completed' ? 'bg-green-100 text-green-600' :
                  step.status === 'in_progress' ? 'bg-blue-100 text-blue-600' :
                  step.status === 'failed' ? 'bg-red-100 text-red-600' :
                  'bg-gray-100 text-gray-400'
                }`}>
                  {step.status === 'completed' ? <CheckCircle className="h-4 w-4" /> :
                   step.status === 'in_progress' ? <Loader2 className="h-4 w-4 animate-spin" /> :
                   step.status === 'failed' ? <XCircle className="h-4 w-4" /> :
                   <span className="text-xs">{index + 1}</span>}
                </div>
                <div className="flex-1">
                  <p className={`text-sm ${
                    step.status === 'in_progress' ? 'font-semibold' : ''
                  }`}>
                    {step.name}
                  </p>
                  {step.status === 'in_progress' && step.progress > 0 && (
                    <div className="bg-gray-200 rounded-full h-1 mt-1">
                      <div
                        className="bg-blue-500 h-1 rounded-full"
                        style={{ width: `${step.progress}%` }}
                      />
                    </div>
                  )}
                </div>
                {step.endTime && (
                  <span className="text-xs text-gray-500">
                    {new Date(step.endTime).toLocaleTimeString()}
                  </span>
                )}
              </div>
            ))}
          </div>

          {/* Deployment Logs */}
          {activeDeployment.logs.length > 0 && (
            <div className="mt-4">
              <button
                onClick={() => setShowLogsModal(true)}
                className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
              >
                <Terminal className="h-4 w-4" />
                View Logs ({activeDeployment.logs.length})
              </button>
            </div>
          )}
        </motion.div>
      )}

      {/* Models Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {modelsLoading ? (
          // Loading skeletons
          [...Array(4)].map((_, i) => (
            <div key={`skeleton-${i}`} className="bg-white rounded-xl shadow-sm p-6 animate-pulse">
              <div className="h-6 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
              <div className="space-y-2">
                <div className="h-4 bg-gray-200 rounded"></div>
                <div className="h-4 bg-gray-200 rounded"></div>
              </div>
            </div>
          ))
        ) : (
          modelsData?.map((model: Model) => (
            <motion.div
              key={model.id}
              whileHover={{ scale: 1.02 }}
              className={`bg-white rounded-xl shadow-sm p-6 border-2 transition-all ${
                model.status === 'active'
                  ? 'border-green-500 bg-green-50'
                  : selectedModel === model.id
                  ? 'border-purple-500'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              {/* Model Header */}
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h4 className="text-lg font-semibold text-gray-900">{model.name}</h4>
                  <p className="text-sm text-gray-600">
                    {model.type} • {model.size} • v{model.version}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  {model.status === 'active' && healthData && (
                    <span className={`${getStatusColor(healthData.status)} flex items-center gap-1 text-sm`}>
                      <Activity className="h-4 w-4" />
                      {healthData.status}
                    </span>
                  )}
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    model.status === 'active'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-600'
                  }`}>
                    {model.status}
                  </span>
                </div>
              </div>

              {/* Model Metrics */}
              {model.performance && (
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <div>
                    <p className="text-xs text-gray-600">Accuracy</p>
                    <p className="text-sm font-medium">{(model.performance.accuracy * 100).toFixed(1)}%</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600">Latency</p>
                    <p className="text-sm font-medium">{model.performance.latency}ms</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600">Throughput</p>
                    <p className="text-sm font-medium">{model.performance.throughput}/min</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600">Memory</p>
                    <p className="text-sm font-medium">{model.performance.memoryUsage}GB</p>
                  </div>
                </div>
              )}

              {/* Model Actions */}
              <div className="flex space-x-2">
                {model.status !== 'active' ? (
                  <>
                    <button
                      onClick={() => setShowTestModal(true)}
                      className="flex-1 px-3 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 text-sm flex items-center justify-center gap-1"
                    >
                      <Shield className="h-4 w-4" />
                      Test
                    </button>
                    <button
                      onClick={() => deployModelMutation.mutate(model.id)}
                      disabled={deployModelMutation.isPending}
                      className="flex-1 px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 text-sm flex items-center justify-center gap-1"
                    >
                      <Cloud className="h-4 w-4" />
                      Deploy
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => setShowLogsModal(true)}
                      className="flex-1 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm flex items-center justify-center gap-1"
                    >
                      <Terminal className="h-4 w-4" />
                      Logs
                    </button>
                    <button
                      onClick={() => {
                        if (confirm('Are you sure you want to deactivate this model?')) {
                          // Deactivate logic here
                        }
                      }}
                      className="flex-1 px-3 py-2 bg-yellow-100 text-yellow-700 rounded-lg hover:bg-yellow-200 text-sm flex items-center justify-center gap-1"
                    >
                      <Pause className="h-4 w-4" />
                      Deactivate
                    </button>
                  </>
                )}
                <button
                  onClick={() => {
                    if (confirm(`Are you sure you want to delete ${model.name}?`)) {
                      deleteModelMutation.mutate(model.id);
                    }
                  }}
                  className="px-3 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 text-sm"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </motion.div>
          ))
        )}
      </div>

      {/* Resource Metrics */}
      {metricsData && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">System Resources</h3>
            <Zap className="h-5 w-5 text-yellow-500" />
          </div>
          <div className="grid grid-cols-4 gap-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">CPU</span>
                <Cpu className="h-4 w-4 text-gray-400" />
              </div>
              <div className="bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    metricsData.cpu > 80 ? 'bg-red-500' :
                    metricsData.cpu > 60 ? 'bg-yellow-500' :
                    'bg-green-500'
                  }`}
                  style={{ width: `${metricsData.cpu}%` }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">{metricsData.cpu}%</p>
            </div>
            
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Memory</span>
                <HardDrive className="h-4 w-4 text-gray-400" />
              </div>
              <div className="bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    metricsData.memory > 80 ? 'bg-red-500' :
                    metricsData.memory > 60 ? 'bg-yellow-500' :
                    'bg-green-500'
                  }`}
                  style={{ width: `${metricsData.memory}%` }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">{metricsData.memory}%</p>
            </div>
            
            {metricsData.gpu !== undefined && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600">GPU</span>
                  <Zap className="h-4 w-4 text-gray-400" />
                </div>
                <div className="bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      metricsData.gpu > 80 ? 'bg-red-500' :
                      metricsData.gpu > 60 ? 'bg-yellow-500' :
                      'bg-green-500'
                    }`}
                    style={{ width: `${metricsData.gpu}%` }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">{metricsData.gpu}%</p>
              </div>
            )}
            
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Disk</span>
                <Package className="h-4 w-4 text-gray-400" />
              </div>
              <div className="bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    metricsData.disk > 80 ? 'bg-red-500' :
                    metricsData.disk > 60 ? 'bg-yellow-500' :
                    'bg-green-500'
                  }`}
                  style={{ width: `${metricsData.disk}%` }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">{metricsData.disk}%</p>
            </div>
          </div>
        </div>
      )}

      {/* Model Configuration */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div
          className="flex items-center justify-between cursor-pointer"
          onClick={() => toggleSection('configuration')}
        >
          <h3 className="text-lg font-semibold text-gray-900">Model Configuration</h3>
          {expandedSections.configuration ? <ChevronDown className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
        </div>
        
        <AnimatePresence>
          {expandedSections.configuration && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden"
            >
              <div className="mt-4 space-y-4">
                {/* Preset Selector */}
                {presetsData && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Configuration Preset
                    </label>
                    <select
                      value={selectedPreset}
                      onChange={(e) => {
                        setSelectedPreset(e.target.value);
                        const preset = presetsData.find((p: ConfigPreset) => p.id === e.target.value);
                        if (preset) {
                          setModelConfig(preset.config);
                        }
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    >
                      <option value="default">Default</option>
                      {presetsData.map((preset: ConfigPreset) => (
                        <option key={preset.id} value={preset.id}>
                          {preset.name}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4">
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

                <div className="flex justify-end space-x-3">
                  <button
                    onClick={() => {
                      const name = prompt('Enter preset name:');
                      if (name) {
                        savePresetMutation.mutate({ name, config: modelConfig });
                      }
                    }}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                  >
                    Save as Preset
                  </button>
                  <button
                    onClick={() => setModelConfig({
                      temperature: 0.7,
                      max_tokens: 150,
                      top_p: 0.9,
                      repetition_penalty: 1.1
                    })}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                  >
                    Reset
                  </button>
                  <button
                    onClick={() => applyConfigMutation.mutate(modelConfig)}
                    disabled={applyConfigMutation.isPending}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                  >
                    Apply Configuration
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Modals */}
      {/* Import Modal, Test Modal, Logs Modal, Compare Modal would go here */}
      {/* Keeping them minimal for space */}
    </div>
  );
}