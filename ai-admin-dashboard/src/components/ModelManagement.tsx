import { endpoints } from '../config/endpoints';
import React, { useState, useEffect } from 'react';
import { 
  Brain, 
  Download, 
  Upload, 
  Play, 
  Pause, 
  RotateCcw,
  Activity,
  Package,
  GitBranch,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  TrendingUp,
  Settings,
  Database,
  Cpu,
  HardDrive,
  Zap,
  Eye,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';
import axios from 'axios';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

interface ModelVersion {
  id: number;
  version_id: string;
  model_name: string;
  base_model: string;
  version_number: string;
  model_type: string;
  model_size: string;
  quantization: string;
  status: 'training' | 'ready' | 'deployed' | 'archived' | 'failed';
  is_active: boolean;
  is_default: boolean;
  accuracy?: number;
  loss?: number;
  perplexity?: number;
  file_size_mb?: number;
  training_examples_count?: number;
  created_at: string;
  created_by: string;
}

interface BaseModel {
  model_id: string;
  model_name: string;
  model_family: string;
  model_size: string;
  file_path: string;
  file_size_gb: number;
  is_available: boolean;
  is_default: boolean;
  download_status: string;
  context_length: number;
  min_gpu_memory_gb?: number;
}

interface TrainingSession {
  id: number;
  session_id: string;
  examples_trained: number;
  accuracy_before?: number;
  accuracy_after?: number;
  status: string;
  started_at: string;
  completed_at?: string;
}

interface ModelDeployment {
  deployment_id: string;
  model_version_id: number;
  environment: 'dev' | 'staging' | 'production';
  status: string;
  traffic_percentage: number;
  request_count: number;
  average_latency_ms?: number;
  error_rate?: number;
  deployed_at: string;
}

const ModelManagement: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'models' | 'training' | 'deployment'>('models');
  const [selectedModel, setSelectedModel] = useState<ModelVersion | null>(null);
  const [showTrainingModal, setShowTrainingModal] = useState(false);
  const [showDeployModal, setShowDeployModal] = useState(false);
  const [trainingConfig, setTrainingConfig] = useState({
    datasets: [] as string[],
    personalities: [] as string[],
    epochs: 3,
    batch_size: 4,
    learning_rate: 0.0002,
    use_lora: true
  });

  const queryClient = useQueryClient();

  // Fetch model versions
  const { data: modelVersions, isLoading: modelsLoading } = useQuery({
    queryKey: ['model-versions'],
    queryFn: async () => {
      const response = await axios.get(endpoints.models.versions);
      return response.data;
    },
    refetchInterval: 5000 // Refresh every 5 seconds for training updates
  });

  // Fetch base models
  const { data: baseModels } = useQuery({
    queryKey: ['base-models'],
    queryFn: async () => {
      const response = await axios.get(endpoints.models.base);
      return response.data;
    }
  });

  // Fetch training sessions
  const { data: trainingSessions } = useQuery({
    queryKey: ['training-sessions'],
    queryFn: async () => {
      const response = await axios.get(endpoints.models.trainingSessions);
      return response.data;
    }
  });

  // Fetch deployments
  const { data: deployments } = useQuery({
    queryKey: ['model-deployments'],
    queryFn: async () => {
      const response = await axios.get(endpoints.models.deployments);
      return response.data;
    }
  });

  // Deploy model mutation
  const deployModelMutation = useMutation({
    mutationFn: async ({ versionId, environment }: { versionId: string; environment: string }) => {
      const response = await axios.post(`http://localhost:8080/api/v1/models/deploy`, {
        version_id: versionId,
        environment
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['model-versions'] });
      queryClient.invalidateQueries({ queryKey: ['model-deployments'] });
      setShowDeployModal(false);
    }
  });

  // Start training mutation
  const startTrainingMutation = useMutation({
    mutationFn: async (config: typeof trainingConfig) => {
      const response = await axios.post(endpoints.models.train, config);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['training-sessions'] });
      setShowTrainingModal(false);
    }
  });

  // Switch active model mutation
  const switchModelMutation = useMutation({
    mutationFn: async (versionId: string) => {
      const response = await axios.post(`http://localhost:8080/api/v1/models/switch`, {
        version_id: versionId
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['model-versions'] });
    }
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'deployed':
      case 'active':
      case 'ready':
        return 'text-green-600 bg-green-100';
      case 'training':
        return 'text-blue-600 bg-blue-100';
      case 'failed':
        return 'text-red-600 bg-red-100';
      case 'archived':
        return 'text-gray-600 bg-gray-100';
      default:
        return 'text-yellow-600 bg-yellow-100';
    }
  };

  const formatFileSize = (mb?: number) => {
    if (!mb) return 'N/A';
    if (mb < 1024) return `${mb.toFixed(1)} MB`;
    return `${(mb / 1024).toFixed(2)} GB`;
  };

  const formatPercentage = (value?: number) => {
    if (value === undefined || value === null) return 'N/A';
    return `${(value * 100).toFixed(1)}%`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Brain className="w-7 h-7 text-purple-600" />
            Model Management
          </h2>
          <p className="text-gray-600 mt-1">
            Manage AI models, training, and deployments
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowTrainingModal(true)}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2"
          >
            <Zap className="w-4 h-4" />
            Train New Model
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {['models', 'training', 'deployment'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm capitalize ${
                activeTab === tab
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {/* Models Tab */}
      {activeTab === 'models' && (
        <div className="space-y-6">
          {/* Active Model Card */}
          {modelVersions?.find((m: ModelVersion) => m.is_active) && (
            <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-6 border border-purple-200">
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-3">
                    <h3 className="text-lg font-semibold text-gray-900">
                      Active Model
                    </h3>
                    <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
                      LIVE
                    </span>
                  </div>
                  <p className="text-gray-600 mt-1">
                    {modelVersions.find((m: ModelVersion) => m.is_active)?.model_name}
                  </p>
                  <p className="text-sm text-gray-500">
                    Version {modelVersions.find((m: ModelVersion) => m.is_active)?.version_number}
                  </p>
                </div>
                <div className="grid grid-cols-3 gap-6 text-sm">
                  <div>
                    <p className="text-gray-500">Accuracy</p>
                    <p className="text-xl font-semibold text-gray-900">
                      {formatPercentage(modelVersions.find((m: ModelVersion) => m.is_active)?.accuracy)}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500">Size</p>
                    <p className="text-xl font-semibold text-gray-900">
                      {formatFileSize(modelVersions.find((m: ModelVersion) => m.is_active)?.file_size_mb)}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500">Examples</p>
                    <p className="text-xl font-semibold text-gray-900">
                      {modelVersions.find((m: ModelVersion) => m.is_active)?.training_examples_count || 0}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Base Models */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Base Models</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {baseModels?.map((model: BaseModel) => (
                <div key={model.model_id} className="bg-white rounded-lg border border-gray-200 p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h4 className="font-medium text-gray-900">{model.model_name}</h4>
                      <p className="text-sm text-gray-500">{model.model_family} • {model.model_size}</p>
                    </div>
                    {model.is_default && (
                      <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                        DEFAULT
                      </span>
                    )}
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Size:</span>
                      <span className="font-medium">{model.file_size_gb.toFixed(1)} GB</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Context:</span>
                      <span className="font-medium">{model.context_length} tokens</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Status:</span>
                      <span className={`px-2 py-0.5 rounded text-xs ${
                        model.is_available ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                      }`}>
                        {model.download_status}
                      </span>
                    </div>
                  </div>
                  {model.min_gpu_memory_gb && (
                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        <Cpu className="w-3 h-3" />
                        Min GPU: {model.min_gpu_memory_gb} GB
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Trained Models */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Trained Models</h3>
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Model
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Version
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Performance
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Size
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {modelVersions?.filter((m: ModelVersion) => m.status !== 'training').map((model: ModelVersion) => (
                    <tr key={model.id} className={model.is_active ? 'bg-purple-50' : ''}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <Brain className="w-8 h-8 text-purple-600 mr-3" />
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {model.model_name}
                            </div>
                            <div className="text-sm text-gray-500">
                              {model.base_model}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{model.version_number}</div>
                        <div className="text-sm text-gray-500">{model.model_type}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(model.status)}`}>
                          {model.status}
                        </span>
                        {model.is_active && (
                          <span className="ml-2 px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full">
                            ACTIVE
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <div className="flex items-center gap-4">
                          <div>
                            <p className="text-gray-500 text-xs">Accuracy</p>
                            <p className="font-medium">{formatPercentage(model.accuracy)}</p>
                          </div>
                          {model.loss && (
                            <div>
                              <p className="text-gray-500 text-xs">Loss</p>
                              <p className="font-medium">{model.loss.toFixed(3)}</p>
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatFileSize(model.file_size_mb)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(model.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex justify-end gap-2">
                          {!model.is_active && model.status === 'ready' && (
                            <button
                              onClick={() => switchModelMutation.mutate(model.version_id)}
                              className="text-purple-600 hover:text-purple-900"
                              title="Activate Model"
                            >
                              <Play className="w-4 h-4" />
                            </button>
                          )}
                          <button
                            onClick={() => {
                              setSelectedModel(model);
                              setShowDeployModal(true);
                            }}
                            className="text-blue-600 hover:text-blue-900"
                            title="Deploy Model"
                          >
                            <Upload className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => setSelectedModel(model)}
                            className="text-gray-600 hover:text-gray-900"
                            title="View Details"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Training Tab */}
      {activeTab === 'training' && (
        <div className="space-y-6">
          {/* Active Training Sessions */}
          {trainingSessions?.filter((s: TrainingSession) => s.status === 'in_progress').length > 0 && (
            <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Active Training</h3>
              <div className="space-y-4">
                {trainingSessions.filter((s: TrainingSession) => s.status === 'in_progress').map((session: TrainingSession) => (
                  <div key={session.id} className="bg-white rounded-lg p-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="font-medium text-gray-900">{session.session_id}</p>
                        <p className="text-sm text-gray-500">
                          Training {session.examples_trained} examples
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                        <span className="text-sm text-blue-600">In Progress</span>
                      </div>
                    </div>
                    <div className="mt-3">
                      <div className="bg-gray-200 rounded-full h-2 w-full">
                        <div className="bg-blue-600 h-2 rounded-full" style={{ width: '45%' }}></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Training History */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Training History</h3>
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Session ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Examples
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Accuracy Change
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Duration
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Started
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {trainingSessions?.map((session: TrainingSession) => (
                    <tr key={session.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {session.session_id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {session.examples_trained}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {session.accuracy_before && session.accuracy_after ? (
                          <div className="flex items-center gap-2">
                            <span>{formatPercentage(session.accuracy_before)}</span>
                            <ArrowUpRight className="w-4 h-4 text-green-600" />
                            <span className="font-medium text-green-600">
                              {formatPercentage(session.accuracy_after)}
                            </span>
                          </div>
                        ) : (
                          'N/A'
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(session.status)}`}>
                          {session.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {session.completed_at ? (
                          `${Math.round((new Date(session.completed_at).getTime() - new Date(session.started_at).getTime()) / 60000)} min`
                        ) : (
                          'In Progress'
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(session.started_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Deployment Tab */}
      {activeTab === 'deployment' && (
        <div className="space-y-6">
          {/* Environment Status */}
          <div className="grid grid-cols-3 gap-4">
            {['production', 'staging', 'dev'].map((env) => {
              const deployment = deployments?.find((d: ModelDeployment) => 
                d.environment === env && d.status === 'active'
              );
              return (
                <div key={env} className="bg-white rounded-lg border border-gray-200 p-4">
                  <div className="flex justify-between items-start mb-3">
                    <h4 className="font-medium text-gray-900 capitalize">{env}</h4>
                    {deployment ? (
                      <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded">
                        ACTIVE
                      </span>
                    ) : (
                      <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                        INACTIVE
                      </span>
                    )}
                  </div>
                  {deployment ? (
                    <div className="space-y-2 text-sm">
                      <p className="text-gray-600">Model: {deployment.deployment_id}</p>
                      <div className="grid grid-cols-2 gap-2 mt-3">
                        <div>
                          <p className="text-gray-500 text-xs">Requests</p>
                          <p className="font-semibold">{deployment.request_count}</p>
                        </div>
                        <div>
                          <p className="text-gray-500 text-xs">Latency</p>
                          <p className="font-semibold">
                            {deployment.average_latency_ms ? `${deployment.average_latency_ms}ms` : 'N/A'}
                          </p>
                        </div>
                        <div>
                          <p className="text-gray-500 text-xs">Error Rate</p>
                          <p className="font-semibold">
                            {deployment.error_rate ? `${(deployment.error_rate * 100).toFixed(2)}%` : '0%'}
                          </p>
                        </div>
                        <div>
                          <p className="text-gray-500 text-xs">Traffic</p>
                          <p className="font-semibold">{deployment.traffic_percentage}%</p>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <p className="text-gray-500 text-sm">No active deployment</p>
                  )}
                </div>
              );
            })}
          </div>

          {/* Deployment History */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Deployment History</h3>
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Deployment ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Environment
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Metrics
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Deployed At
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {deployments?.map((deployment: ModelDeployment) => (
                    <tr key={deployment.deployment_id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {deployment.deployment_id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          deployment.environment === 'production' ? 'bg-red-100 text-red-800' :
                          deployment.environment === 'staging' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {deployment.environment}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(deployment.status)}`}>
                          {deployment.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div className="flex items-center gap-4">
                          <span>{deployment.request_count} reqs</span>
                          {deployment.average_latency_ms && (
                            <span>{deployment.average_latency_ms}ms</span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(deployment.deployed_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Training Modal */}
      {showTrainingModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Train New Model</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Datasets
                </label>
                <div className="space-y-2">
                  {['cannabis_slang_v1', 'medical_conditions_v1', 'product_quantities_v1'].map(dataset => (
                    <label key={dataset} className="flex items-center">
                      <input
                        type="checkbox"
                        value={dataset}
                        checked={trainingConfig.datasets.includes(dataset)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setTrainingConfig({
                              ...trainingConfig,
                              datasets: [...trainingConfig.datasets, dataset]
                            });
                          } else {
                            setTrainingConfig({
                              ...trainingConfig,
                              datasets: trainingConfig.datasets.filter(d => d !== dataset)
                            });
                          }
                        }}
                        className="mr-2"
                      />
                      <span className="text-sm text-gray-700">{dataset}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Training Parameters
                </label>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Epochs</label>
                    <input
                      type="number"
                      value={trainingConfig.epochs}
                      onChange={(e) => setTrainingConfig({
                        ...trainingConfig,
                        epochs: parseInt(e.target.value)
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Batch Size</label>
                    <input
                      type="number"
                      value={trainingConfig.batch_size}
                      onChange={(e) => setTrainingConfig({
                        ...trainingConfig,
                        batch_size: parseInt(e.target.value)
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Learning Rate</label>
                    <input
                      type="number"
                      step="0.0001"
                      value={trainingConfig.learning_rate}
                      onChange={(e) => setTrainingConfig({
                        ...trainingConfig,
                        learning_rate: parseFloat(e.target.value)
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Use LoRA</label>
                    <select
                      value={trainingConfig.use_lora ? 'yes' : 'no'}
                      onChange={(e) => setTrainingConfig({
                        ...trainingConfig,
                        use_lora: e.target.value === 'yes'
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    >
                      <option value="yes">Yes (Efficient)</option>
                      <option value="no">No (Full Fine-tuning)</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowTrainingModal(false)}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={() => startTrainingMutation.mutate(trainingConfig)}
                disabled={trainingConfig.datasets.length === 0}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
              >
                Start Training
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Deploy Modal */}
      {showDeployModal && selectedModel && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Deploy Model</h3>
            
            <div className="mb-4">
              <p className="text-sm text-gray-600">
                Deploy <strong>{selectedModel.model_name}</strong> v{selectedModel.version_number}
              </p>
            </div>

            <div className="space-y-3">
              <label className="block text-sm font-medium text-gray-700">
                Select Environment
              </label>
              {['dev', 'staging', 'production'].map(env => (
                <button
                  key={env}
                  onClick={() => {
                    deployModelMutation.mutate({
                      versionId: selectedModel.version_id,
                      environment: env
                    });
                  }}
                  className={`w-full px-4 py-3 border rounded-lg text-left hover:bg-gray-50 ${
                    env === 'production' ? 'border-red-200 hover:bg-red-50' :
                    env === 'staging' ? 'border-yellow-200 hover:bg-yellow-50' :
                    'border-gray-200'
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <span className="font-medium capitalize">{env}</span>
                    {env === 'production' && (
                      <span className="text-xs text-red-600">⚠️ Live Environment</span>
                    )}
                  </div>
                </button>
              ))}
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowDeployModal(false)}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelManagement;