import React, { useState, useEffect } from 'react';
import { Bot, Loader2, AlertCircle, CheckCircle, Cpu, Settings, Database, FileCode, ChevronDown, ChevronRight, Eye, Edit, Network, Zap, RefreshCw, Cloud, Monitor, Volume2, Mic, Play, Pause, Square, Upload, Check, X, Radio } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';
import JsonEditor from '../components/JsonEditor';
import Personalities from '../components/Personalities';

interface Model {
  name: string;
  filename: string;
  path: string;
  size_gb: number;
}

const AIManagement: React.FC = () => {
  const { token } = useAuth();
  const { t } = useTranslation(['common']);
  const [models, setModels] = useState<Model[]>([]);
  const [currentModel, setCurrentModel] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingModel, setIsLoadingModel] = useState<string | null>(null);
  const [modelLoadStatus, setModelLoadStatus] = useState<string>('');
  const [modelError, setModelError] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'models' | 'configuration' | 'inference' | 'voice' | 'personalities'>('models');
  const [configuration, setConfiguration] = useState<any>(null);
  const [isLoadingConfig, setIsLoadingConfig] = useState(false);
  const [expandedSections, setExpandedSections] = useState<{ [key: string]: boolean }>({});
  const [editingFile, setEditingFile] = useState<{ name: string; content: any; type: string } | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<string>('');
  const [selectedPersonality, setSelectedPersonality] = useState<string>('');
  const [agents, setAgents] = useState<any[]>([]);
  const [personalities, setPersonalities] = useState<any[]>([]);
  const [isLoadingAgents, setIsLoadingAgents] = useState(false);
  const [isLoadingPersonalities, setIsLoadingPersonalities] = useState(false);

  // Router/Inference state
  const [routerStats, setRouterStats] = useState<any>(null);
  const [isLoadingRouter, setIsLoadingRouter] = useState(false);
  const [isTogglingRouter, setIsTogglingRouter] = useState(false);

  // Model selection state
  const [providerModels, setProviderModels] = useState<{[key: string]: string}>({});
  const [availableModels, setAvailableModels] = useState<{[key: string]: any[]}>({});
  const [isUpdatingModel, setIsUpdatingModel] = useState(false);

  // Voice provider state
  const [voiceProviders, setVoiceProviders] = useState<any>(null);
  const [isLoadingVoiceProviders, setIsLoadingVoiceProviders] = useState(false);
  const [voiceCacheStats, setVoiceCacheStats] = useState<any>(null);
  const [allProviders, setAllProviders] = useState<any[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<any>(null);
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);
  const [googleCredentials, setGoogleCredentials] = useState({ credentials_path: '', project_id: '' });
  const [isSavingConfig, setIsSavingConfig] = useState(false);
  const [isTestingProvider, setIsTestingProvider] = useState<string | null>(null);
  const [voiceSampleFile, setVoiceSampleFile] = useState<File | null>(null);
  const [uploadingVoiceSample, setUploadingVoiceSample] = useState(false);

  // Voice recording state
  const [isRecording, setIsRecording] = useState(false);
  const [recordedAudio, setRecordedAudio] = useState<Blob | null>(null);
  const [currentPhraseIndex, setCurrentPhraseIndex] = useState(0);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [isVoiceModalOpen, setIsVoiceModalOpen] = useState(false);

  // Fetch available models
  const fetchModels = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:5024/api/admin/models', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      if (data.models) {
        setModels(data.models);
        setCurrentModel(data.current_model);
      }
    } catch (error) {
      console.error('Error fetching models:', error);
      toast.error(t('common:toasts.model.fetchFailed'));
    }
    setIsLoading(false);
  };

  // Get current model status
  const fetchModelStatus = async () => {
    try {
      const response = await fetch('http://localhost:5024/api/admin/model', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      if (data.model) {
        setCurrentModel(data.model);
        setModelLoadStatus(data.load_status || '');
      }
    } catch (error) {
      console.error('Error fetching model status:', error);
    }
  };

  // Load a model
  const loadModel = async (modelName: string) => {
    setIsLoadingModel(modelName);
    setModelError('');
    setModelLoadStatus('Loading...');

    try {
      const response = await fetch('http://localhost:5024/api/admin/model/load', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: modelName,
          agent: selectedAgent || 'assistant',
          personality: selectedPersonality || 'rhomida'
        })
      });

      const data = await response.json();

      if (data.success === true) {
        setCurrentModel(modelName);
        setModelLoadStatus('Model loaded successfully');
        toast.success(`Model ${modelName} loaded successfully`);

        // Fetch updated configuration after loading
        if (activeTab === 'configuration') {
          fetchConfiguration();
        }
      } else {
        setModelError(data.error || data.detail || t('common:toasts.model.loadFailed'));
        toast.error(data.error || data.detail || t('common:toasts.model.loadFailed'));
      }
    } catch (error) {
      console.error('Error loading model:', error);
      setModelError(t('common:toasts.model.loadFailed'));
      toast.error(t('common:toasts.model.loadFailed'));
    }

    setIsLoadingModel(null);
  };

  // Unload current model
  const unloadModel = async () => {
    setIsLoadingModel(currentModel || 'unload');
    setModelError('');

    try {
      const response = await fetch('http://localhost:5024/api/admin/model/unload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      const data = await response.json();

      if (data.status === 'success') {
        setCurrentModel(null);
        setModelLoadStatus('Model unloaded');
        toast.success(t('common:toasts.model.unloadSuccess'));
      } else {
        setModelError(data.error || t('common:toasts.model.unloadFailed'));
        toast.error(data.error || t('common:toasts.model.unloadFailed'));
      }
    } catch (error) {
      console.error('Error unloading model:', error);
      setModelError(t('common:toasts.model.unloadFailed'));
      toast.error(t('common:toasts.model.unloadFailed'));
    }

    setIsLoadingModel(null);
  };

  // Fetch configuration
  const fetchConfiguration = async (agent?: string, personality?: string) => {
    setIsLoadingConfig(true);
    try {
      let url = 'http://localhost:5024/api/admin/configuration';
      const params = new URLSearchParams();
      if (agent) params.append('agent', agent);
      if (personality) params.append('personality', personality);
      if (params.toString()) url += '?' + params.toString();

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      setConfiguration(data);
    } catch (error) {
      console.error('Error fetching configuration:', error);
      toast.error(t('common:toasts.config.fetchFailed'));
    }
    setIsLoadingConfig(false);
  };

  // Fetch available agents
  const fetchAgents = async () => {
    setIsLoadingAgents(true);
    try {
      const response = await fetch('http://localhost:5024/api/admin/agents', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      if (data.agents) {
        setAgents(data.agents);
        // Set default agent if not already selected
        if (!selectedAgent && data.agents.length > 0) {
          const defaultAgent = data.agents.find((a: any) => a.id === 'assistant') || data.agents[0];
          setSelectedAgent(defaultAgent.id);
        }
      }
    } catch (error) {
      console.error('Error fetching agents:', error);
      toast.error(t('common:toasts.agent.fetchFailed'));
    }
    setIsLoadingAgents(false);
  };

  // Fetch personalities for selected agent
  const fetchPersonalities = async (agentId: string) => {
    setIsLoadingPersonalities(true);
    try {
      const response = await fetch(`http://localhost:5024/api/admin/agents/${agentId}/personalities`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      if (data.personalities) {
        setPersonalities(data.personalities);
        // Set default personality to first in list
        if (data.personalities.length > 0) {
          setSelectedPersonality(data.personalities[0].id);
        }
      }
    } catch (error) {
      console.error('Error fetching personalities:', error);
      toast.error(t('common:toasts.personality.fetchFailed'));
    }
    setIsLoadingPersonalities(false);
  };

  // Fetch router stats
  const fetchRouterStats = async () => {
    setIsLoadingRouter(true);
    try {
      const response = await fetch('http://localhost:5024/api/admin/router/stats', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      setRouterStats(data);
    } catch (error) {
      console.error('Error fetching router stats:', error);
      toast.error(t('common:toasts.router.statsFetchFailed'));
    }
    setIsLoadingRouter(false);
  };

  // Toggle router (local <-> cloud)
  const toggleRouter = async () => {
    setIsTogglingRouter(true);
    try {
      const response = await fetch('http://localhost:5024/api/admin/router/toggle', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      if (data.success) {
        toast.success(data.message || 'Inference mode toggled successfully');
        fetchRouterStats(); // Refresh stats
      } else {
        toast.error(data.error || t('common:toasts.router.toggleFailed'));
      }
    } catch (error) {
      console.error('Error toggling router:', error);
      toast.error(t('common:toasts.router.toggleFailed'));
    }
    setIsTogglingRouter(false);
  };

  // Fetch voice provider status
  const fetchVoiceProviders = async () => {
    setIsLoadingVoiceProviders(true);
    try {
      const response = await fetch('http://localhost:5024/api/voice-synthesis/providers/status', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      if (data.success) {
        setVoiceProviders(data);
      }
    } catch (error) {
      console.error('Error fetching voice providers:', error);
      toast.error('Failed to fetch voice provider status');
    }
    setIsLoadingVoiceProviders(false);
  };

  // Fetch voice cache statistics
  const fetchVoiceCacheStats = async () => {
    try {
      const response = await fetch('http://localhost:5024/api/voice-synthesis/cache/stats', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      if (data.success) {
        setVoiceCacheStats(data.cache);
      }
    } catch (error) {
      console.error('Error fetching voice cache stats:', error);
    }
  };

  // Fetch all voice providers (management endpoint)
  const fetchAllProviders = async () => {
    try {
      const response = await fetch('http://localhost:5024/api/voice-providers/list', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      if (data.success) {
        setAllProviders(data.providers || []);
      }
    } catch (error) {
      console.error('Error fetching all providers:', error);
      toast.error('Failed to fetch voice providers');
    }
  };

  // Set active voice provider
  const handleSetActiveProvider = async (providerId: string) => {
    try {
      const response = await fetch('http://localhost:5024/api/voice-providers/active', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ provider: providerId })
      });
      const data = await response.json();
      if (data.success) {
        toast.success(`Active provider set to ${providerId}`);
        fetchAllProviders();
        fetchVoiceProviders();
      } else {
        toast.error(data.message || 'Failed to set active provider');
      }
    } catch (error) {
      console.error('Error setting active provider:', error);
      toast.error('Failed to set active provider');
    }
  };

  // Configure Google Cloud TTS
  const handleConfigureProvider = async () => {
    setIsSavingConfig(true);
    try {
      const response = await fetch(`http://localhost:5024/api/voice-providers/${selectedProvider.id}/configure`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          credentials: googleCredentials,
          enabled: true
        })
      });
      const data = await response.json();
      if (data.success) {
        toast.success(`${selectedProvider.name} configured successfully`);
        setIsConfigModalOpen(false);
        setGoogleCredentials({ credentials_path: '', project_id: '' });
        fetchAllProviders();
      } else {
        toast.error(data.message || 'Configuration failed');
      }
    } catch (error) {
      console.error('Error configuring provider:', error);
      toast.error('Failed to configure provider');
    }
    setIsSavingConfig(false);
  };

  // Test voice provider
  const handleTestProvider = async (providerId: string) => {
    setIsTestingProvider(providerId);
    try {
      const response = await fetch('http://localhost:5024/api/voice-providers/test', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          provider: providerId,
          text: 'Hello! This is a test of the voice synthesis system.'
        })
      });
      const data = await response.json();
      if (data.success) {
        toast.success(`Test successful! Audio generated in ${data.duration_ms.toFixed(0)}ms`);
      } else {
        toast.error(data.message || 'Test failed');
      }
    } catch (error) {
      console.error('Error testing provider:', error);
      toast.error('Failed to test provider');
    }
    setIsTestingProvider(null);
  };

  // Upload voice sample with microphone recording
  const handleVoiceSampleUpload = async (audioBlob: Blob, personalityId: string) => {
    setUploadingVoiceSample(true);
    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'voice_sample.wav');
      formData.append('personality_id', personalityId);

      const response = await fetch('http://localhost:5024/api/voice-providers/voice-samples/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      const data = await response.json();
      if (data.success) {
        toast.success('Voice sample uploaded successfully!');
        return true;
      } else {
        toast.error(data.message || 'Upload failed');
        return false;
      }
    } catch (error) {
      console.error('Error uploading voice sample:', error);
      toast.error('Failed to upload voice sample');
      return false;
    } finally {
      setUploadingVoiceSample(false);
    }
  };

  // Fetch current model configuration
  const fetchModelConfig = async () => {
    try {
      const response = await fetch('http://localhost:5024/api/admin/router/models/config', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      if (data.success) {
        setProviderModels(data.models);
        // Fetch available models for each provider
        Object.keys(data.models).forEach(provider => {
          fetchAvailableModels(provider);
        });
      }
    } catch (error) {
      console.error('Error fetching model config:', error);
    }
  };

  // Fetch available models for a provider
  const fetchAvailableModels = async (provider: string) => {
    try {
      const response = await fetch(`http://localhost:5024/api/admin/router/providers/${encodeURIComponent(provider)}/models`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      if (data.success) {
        setAvailableModels(prev => ({ ...prev, [provider]: data.models }));
      }
    } catch (error) {
      console.error('Error fetching available models:', error);
    }
  };

  // Update provider model
  const updateProviderModel = async (provider: string, model: string) => {
    setIsUpdatingModel(true);
    try {
      const response = await fetch(`http://localhost:5024/api/admin/router/providers/${encodeURIComponent(provider)}/model`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ model_name: model })
      });
      const data = await response.json();
      if (data.success) {
        toast.success(`Updated ${provider} model to ${model}`);
        fetchModelConfig();
        fetchRouterStats();
      } else {
        toast.error(data.error || t('common:toasts.model.updateFailed'));
      }
    } catch (error) {
      console.error('Error updating model:', error);
      toast.error(t('common:toasts.model.updateFailed'));
    }
    setIsUpdatingModel(false);
  };

  useEffect(() => {
    fetchModels();
    fetchModelStatus();

    // Auto-refresh model status every 5 seconds
    const interval = setInterval(() => {
      fetchModelStatus();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (activeTab === 'configuration') {
      fetchAgents();
      if (selectedAgent && selectedPersonality) {
        fetchConfiguration(selectedAgent, selectedPersonality);
      } else {
        fetchConfiguration();
      }
    } else if (activeTab === 'inference') {
      fetchRouterStats();
      fetchModelConfig();
    } else if (activeTab === 'voice') {
      fetchVoiceProviders();
      fetchVoiceCacheStats();
      fetchAllProviders();
    }
  }, [activeTab]);

  // Fetch personalities when agent changes
  useEffect(() => {
    if (selectedAgent) {
      fetchPersonalities(selectedAgent);
    }
  }, [selectedAgent]);

  // Fetch configuration when agent or personality changes
  useEffect(() => {
    if (activeTab === 'configuration' && selectedAgent && selectedPersonality) {
      fetchConfiguration(selectedAgent, selectedPersonality);
    }
  }, [selectedAgent, selectedPersonality]);

  // Voice sample phrases for cloning
  const voiceSamplePhrases = [
    "Welcome to WeedGo! How can I help you today?",
    "Thank you for your purchase. Have a great day!",
    "Your order is ready for pickup. Please come to the counter.",
    "We have a special promotion on selected products this week.",
    "Please let me know if you need any assistance finding something."
  ];

  // Start recording voice sample
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks: Blob[] = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunks.push(e.data);
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        setRecordedAudio(blob);
        stream.getTracks().forEach(track => track.stop());
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
    } catch (error) {
      console.error('Error starting recording:', error);
      toast.error('Failed to access microphone. Please check permissions.');
    }
  };

  // Stop recording
  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
      setIsRecording(false);
    }
  };

  // Play recorded audio
  const playRecordedAudio = () => {
    if (recordedAudio) {
      const audioURL = URL.createObjectURL(recordedAudio);
      const audio = new Audio(audioURL);
      audio.play();
    }
  };

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  return (
    <React.Fragment>
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-4 sm:p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-4 sm:p-6 transition-colors">
            <div className="flex items-center gap-3 mb-4 sm:mb-6">
              <div className="p-2 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg">
                <Bot className="h-5 w-5 sm:h-6 sm:w-6 text-indigo-600 dark:text-indigo-400" />
              </div>
              <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">AI Engine Management</h1>
            </div>

            {/* Tabs */}
            <div className="flex gap-2 sm:gap-4 mb-4 sm:mb-6 border-b border-gray-200 dark:border-gray-700 overflow-x-auto -mx-4 sm:mx-0 px-4 sm:px-0">
            <nav className="-mb-px flex space-x-2 sm:space-x-4 min-w-max sm:min-w-0">
              <button
                onClick={() => setActiveTab('models')}
                className={`pb-3 px-1 font-medium text-xs sm:text-sm whitespace-nowrap transition-colors ${
                  activeTab === 'models'
                    ? 'text-indigo-600 dark:text-indigo-400 border-b-2 border-indigo-600 dark:border-indigo-400'
                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
              >
                Models
              </button>
              <button
                onClick={() => setActiveTab('configuration')}
                className={`pb-3 px-1 font-medium text-xs sm:text-sm whitespace-nowrap transition-colors ${
                  activeTab === 'configuration'
                    ? 'text-indigo-600 dark:text-indigo-400 border-b-2 border-indigo-600 dark:border-indigo-400'
                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
              >
                Configuration
              </button>
              <button
                onClick={() => setActiveTab('inference')}
                className={`pb-3 px-1 font-medium text-xs sm:text-sm whitespace-nowrap transition-colors ${
                  activeTab === 'inference'
                    ? 'text-indigo-600 dark:text-indigo-400 border-b-2 border-indigo-600 dark:border-indigo-400'
                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
              >
                Inference
              </button>
              <button
                onClick={() => setActiveTab('voice')}
                className={`pb-3 px-1 font-medium text-xs sm:text-sm whitespace-nowrap transition-colors ${
                  activeTab === 'voice'
                    ? 'text-indigo-600 dark:text-indigo-400 border-b-2 border-indigo-600 dark:border-indigo-400'
                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
              >
                Voice
              </button>
              <button
                onClick={() => setActiveTab('personalities')}
                className={`pb-3 px-1 font-medium text-xs sm:text-sm whitespace-nowrap transition-colors ${
                  activeTab === 'personalities'
                    ? 'text-indigo-600 dark:text-indigo-400 border-b-2 border-indigo-600 dark:border-indigo-400'
                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
              >
                Personalities
              </button>
            </nav>
          </div>

          {/* Tab Content */}
          <div className="space-y-4 sm:space-y-6">
            {activeTab === 'models' && (
              <div>
                {/* Current Status */}
                <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4 sm:p-6 mb-4 sm:mb-6 transition-colors">
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                    <div>
                      <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Current Model</h3>
                      {currentModel ? (
                        <div className="mt-1 flex items-center gap-2">
                          <CheckCircle className="h-4 w-4 text-green-500" />
                          <span className="text-lg font-semibold text-gray-900 dark:text-white">{currentModel}</span>
                        </div>
                      ) : (
                        <div className="mt-1 flex items-center gap-2">
                          <AlertCircle className="h-4 w-4 text-gray-400" />
                          <span className="text-lg text-gray-500 dark:text-gray-400">No model loaded</span>
                        </div>
                      )}
                      {modelLoadStatus && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{modelLoadStatus}</p>
                      )}
                      {modelError && (
                        <p className="text-sm text-red-600 dark:text-red-400 mt-1">{modelError}</p>
                      )}
                    </div>
                    {/* Unload button commented out - endpoint not implemented
                    {currentModel && (
                      <button
                        onClick={unloadModel}
                        disabled={isLoadingModel}
                        className="px-4 py-2 text-sm bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-lg hover:bg-red-200 dark:hover:bg-red-900/50 disabled:opacity-50"
                      >
                        {isLoadingModel ? 'Processing...' : 'Unload Model'}
                      </button>
                    )}
                    */}
                  </div>
                </div>

                {/* Available Models */}
                <div>
                  <h2 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white mb-3 sm:mb-4">Available Models</h2>

                  {isLoading ? (
                    <div className="flex items-center justify-center py-12">
                      <Loader2 className="h-6 w-6 sm:h-8 sm:w-8 animate-spin text-indigo-600" />
                    </div>
                  ) : models.length === 0 ? (
                    <p className="text-sm sm:text-base text-gray-500 dark:text-gray-400 text-center py-12">No models found</p>
                  ) : (
                    <div className="grid gap-3 sm:gap-4">
                      {models.map((model) => (
                        <div
                          key={model.name}
                          className={`border rounded-lg p-3 sm:p-4 transition-all ${
                            currentModel === model.name
                              ? 'border-indigo-500 dark:border-indigo-400 bg-indigo-50 dark:bg-indigo-900/20'
                              : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                          }`}
                        >
                          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <Cpu className="h-4 w-4 sm:h-5 sm:w-5 text-gray-600 dark:text-gray-400 flex-shrink-0" />
                                <h3 className="font-medium text-sm sm:text-base text-gray-900 dark:text-white truncate">{model.name}</h3>
                                {currentModel === model.name && (
                                  <span className="px-2 py-0.5 text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full flex-shrink-0">
                                    Active
                                  </span>
                                )}
                              </div>
                              <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-1 truncate">
                                {model.filename} • {model.size_gb} GB
                              </p>
                            </div>
                            {currentModel !== model.name && (
                              <button
                                onClick={() => loadModel(model.name)}
                                disabled={isLoadingModel !== null}
                                className="w-full sm:w-auto px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-95 touch-manipulation"
                              >
                                {isLoadingModel === model.name ? (
                                  <span className="flex items-center justify-center gap-2">
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                    Loading...
                                  </span>
                                ) : (
                                  'Load Model'
                                )}
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
            )}

            {activeTab === 'configuration' && (
              <div>
                {/* Agent and Personality Selection */}
                <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4 mb-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Select Agent
                      </label>
                      <select
                        value={selectedAgent}
                        onChange={(e) => setSelectedAgent(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                        disabled={isLoadingAgents}
                      >
                        {!selectedAgent && <option value="">Select an agent...</option>}
                        {agents.map((agent) => (
                          <option key={agent.id} value={agent.id}>
                            {agent.name} {agent.description && `- ${agent.description}`}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Select Personality
                      </label>
                      <select
                        value={selectedPersonality}
                        onChange={(e) => setSelectedPersonality(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                        disabled={!selectedAgent || isLoadingPersonalities}
                      >
                        {!selectedPersonality && <option value="">Select a personality...</option>}
                        {personalities.map((personality) => (
                          <option key={personality.id} value={personality.id}>
                            {personality.name} {personality.description && `- ${personality.description}`}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                    Configuration for {selectedAgent || 'Default'} / {selectedPersonality || 'Default'}
                  </h3>
                  <button
                    onClick={() => fetchConfiguration(selectedAgent, selectedPersonality)}
                    disabled={isLoadingConfig}
                    className="px-4 py-2 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 flex items-center gap-2"
                  >
                    {isLoadingConfig && <Loader2 className="h-4 w-4 animate-spin" />}
                    Refresh
                  </button>
                </div>

                {isLoadingConfig ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
                  </div>
                ) : !configuration ? (
                  <p className="text-gray-500 dark:text-gray-400 text-center py-12">
                    No configuration loaded
                  </p>
                ) : (
                  <div className="space-y-4">
                    {/* System Configuration */}
                    {configuration.configurations?.system && (
                      <div className="border border-gray-200 dark:border-gray-700 rounded-lg">
                        <div className="p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => toggleSection('system')}
                                className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
                              >
                                {expandedSections.system ?
                                  <ChevronDown className="h-4 w-4" /> :
                                  <ChevronRight className="h-4 w-4" />
                                }
                              </button>
                              <Database className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                              <h4 className="font-medium text-gray-900 dark:text-white">System Configuration</h4>
                            </div>
                            {configuration.configurations.system.config && (
                              <button
                                onClick={() => setEditingFile({
                                  name: 'System Configuration',
                                  content: configuration.configurations.system.config,
                                  type: 'system'
                                })}
                                className="flex items-center gap-1 px-3 py-1 text-sm text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded transition-colors"
                              >
                                <Edit className="h-4 w-4" />
                                Edit
                              </button>
                            )}
                          </div>
                          <p className="text-sm text-gray-500 dark:text-gray-400 mt-2 ml-7">
                            Source: {configuration.configurations.system.source}
                          </p>
                          {expandedSections.system && configuration.configurations.system.config && (
                            <pre className="bg-gray-50 dark:bg-gray-900 p-3 rounded text-xs overflow-x-auto max-h-64 overflow-y-auto mt-3 ml-7">
                              {JSON.stringify(configuration.configurations.system.config, null, 2)}
                            </pre>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Agent Configuration */}
                    {configuration.configurations?.agent && (
                      <div className="border border-gray-200 dark:border-gray-700 rounded-lg">
                        <div className="p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => toggleSection('agent')}
                                className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
                              >
                                {expandedSections.agent ?
                                  <ChevronDown className="h-4 w-4" /> :
                                  <ChevronRight className="h-4 w-4" />
                                }
                              </button>
                              <Bot className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                              <h4 className="font-medium text-gray-900 dark:text-white">
                                Agent: {configuration.configurations.agent.name}
                              </h4>
                            </div>
                            <button
                              onClick={() => setEditingFile({
                                name: 'Agent Configuration',
                                content: configuration.configurations.agent.config || {},
                                type: 'agent'
                              })}
                              className="flex items-center gap-1 px-3 py-1 text-sm text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded transition-colors"
                            >
                              <Edit className="h-4 w-4" />
                              Edit
                            </button>
                          </div>
                          <p className="text-sm text-gray-500 dark:text-gray-400 mt-2 ml-7">
                            Source: {configuration.configurations.agent.source}
                          </p>
                          <p className="text-sm text-gray-600 dark:text-gray-300 ml-7">
                            Status: {configuration.configurations.agent.loaded ?
                              <span className="text-green-600 dark:text-green-400">Loaded</span> :
                              <span className="text-yellow-600 dark:text-yellow-400">Not Loaded</span>
                            }
                          </p>
                          {expandedSections.agent && configuration.configurations.agent.config && Object.keys(configuration.configurations.agent.config).length > 0 && (
                            <pre className="bg-gray-50 dark:bg-gray-900 p-3 rounded text-xs overflow-x-auto max-h-64 overflow-y-auto mt-3 ml-7">
                              {JSON.stringify(configuration.configurations.agent.config, null, 2)}
                            </pre>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Agent Prompts */}
                    {configuration.configurations?.agent_prompts && (
                      <div className="border border-gray-200 dark:border-gray-700 rounded-lg">
                        <div className="p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => toggleSection('prompts')}
                                className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
                              >
                                {expandedSections.prompts ?
                                  <ChevronDown className="h-4 w-4" /> :
                                  <ChevronRight className="h-4 w-4" />
                                }
                              </button>
                              <FileCode className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                              <h4 className="font-medium text-gray-900 dark:text-white">Agent Prompts</h4>
                            </div>
                            <button
                              onClick={() => setEditingFile({
                                name: 'Agent Prompts',
                                content: configuration.configurations.agent_prompts.prompts || {},
                                type: 'agent_prompts'
                              })}
                              className="flex items-center gap-1 px-3 py-1 text-sm text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded transition-colors"
                            >
                              <Edit className="h-4 w-4" />
                              Edit
                            </button>
                          </div>
                          <p className="text-sm text-gray-500 dark:text-gray-400 mt-2 ml-7">
                            Source: {configuration.configurations.agent_prompts.source}
                          </p>
                          <p className="text-sm text-gray-600 dark:text-gray-300 mb-2 ml-7">
                            {configuration.configurations.agent_prompts.count} prompts loaded
                          </p>
                          <div className="flex flex-wrap gap-2 ml-7">
                            {configuration.configurations.agent_prompts.prompt_types.map((type: string) => (
                              <span
                                key={type}
                                className="px-2 py-1 text-xs bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded"
                              >
                                {type}
                              </span>
                            ))}
                          </div>
                          {expandedSections.prompts && configuration.configurations.agent_prompts.prompts && (
                            <pre className="bg-gray-50 dark:bg-gray-900 p-3 rounded text-xs overflow-x-auto max-h-64 overflow-y-auto mt-3 ml-7">
                              {JSON.stringify(configuration.configurations.agent_prompts.prompts, null, 2)}
                            </pre>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Intent Configuration */}
                    {configuration.configurations?.intent && (
                      <div className="border border-gray-200 dark:border-gray-700 rounded-lg">
                        <div className="p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => toggleSection('intent')}
                                className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
                              >
                                {expandedSections.intent ?
                                  <ChevronDown className="h-4 w-4" /> :
                                  <ChevronRight className="h-4 w-4" />
                                }
                              </button>
                              <FileCode className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                              <h4 className="font-medium text-gray-900 dark:text-white">Intent Detection</h4>
                            </div>
                            {configuration.configurations.intent.config && (
                              <button
                                onClick={() => setEditingFile({
                                  name: 'Intent Configuration',
                                  content: configuration.configurations.intent.config,
                                  type: 'intent'
                                })}
                                className="flex items-center gap-1 px-3 py-1 text-sm text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded transition-colors"
                              >
                                <Edit className="h-4 w-4" />
                                Edit
                              </button>
                            )}
                          </div>
                          <p className="text-sm text-gray-500 dark:text-gray-400 mt-2 ml-7">
                            Source: {configuration.configurations.intent.source}
                          </p>
                          <p className="text-sm text-gray-600 dark:text-gray-300 mb-2 ml-7">
                            {configuration.configurations.intent.count} intents configured
                          </p>
                          <div className="flex flex-wrap gap-2 ml-7">
                            {configuration.configurations.intent.intents.map((intent: string) => (
                              <span
                                key={intent}
                                className="px-2 py-1 text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded"
                              >
                                {intent}
                              </span>
                            ))}
                          </div>
                          {expandedSections.intent && configuration.configurations.intent.config && (
                            <pre className="bg-gray-50 dark:bg-gray-900 p-3 rounded text-xs overflow-x-auto max-h-64 overflow-y-auto mt-3 ml-7">
                              {JSON.stringify(configuration.configurations.intent.config, null, 2)}
                            </pre>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Model Settings */}
                    {configuration.configurations?.model && (
                      <div className="border border-gray-200 dark:border-gray-700 rounded-lg">
                        <div className="p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => toggleSection('model')}
                                className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
                              >
                                {expandedSections.model ?
                                  <ChevronDown className="h-4 w-4" /> :
                                  <ChevronRight className="h-4 w-4" />
                                }
                              </button>
                              <Cpu className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                              <h4 className="font-medium text-gray-900 dark:text-white">
                                Model: {configuration.configurations.model.name}
                              </h4>
                            </div>
                          </div>
                          {expandedSections.model && (
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3 ml-7">
                              {Object.entries(configuration.configurations.model.settings).map(([key, value]) => (
                                <div key={key}>
                                  <p className="text-xs text-gray-500 dark:text-gray-400">{key}</p>
                                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                                    {value !== null ? String(value) : 'Default'}
                                  </p>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'inference' && (
              <div>
                {isLoadingRouter ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
                  </div>
                ) : !routerStats ? (
                  <p className="text-gray-500 dark:text-gray-400 text-center py-12">
                    No router information available
                  </p>
                ) : (
                  <div className="space-y-6">
                    {/* Current Mode & Toggle */}
                    <div className="bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-lg p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                            Inference Mode
                          </h3>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {routerStats.active
                              ? '☁️ Cloud inference (3 providers available)'
                              : '💻 Local inference (llama-cpp)'
                            }
                          </p>
                          {routerStats.active && routerStats.providers && routerStats.providers.length > 0 && (
                            <div className="mt-2 flex items-center gap-2">
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
                          className={`px-6 py-3 rounded-lg font-medium transition-all ${
                            routerStats.active
                              ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                              : 'bg-gray-600 text-white hover:bg-gray-700'
                          } disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2`}
                        >
                          {isTogglingRouter ? (
                            <>
                              <Loader2 className="h-5 w-5 animate-spin" />
                              Switching...
                            </>
                          ) : (
                            <>
                              <RefreshCw className="h-5 w-5" />
                              {routerStats.active ? 'Switch to Local' : 'Switch to Cloud'}
                            </>
                          )}
                        </button>
                      </div>

                      {/* Performance Info */}
                      <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-white dark:bg-gray-800 rounded-lg p-3">
                          <p className="text-xs text-gray-500 dark:text-gray-400">Latency</p>
                          <p className="text-lg font-semibold text-gray-900 dark:text-white">
                            {routerStats.active ? '0.5-2.5s' : '~5s'}
                          </p>
                        </div>
                        <div className="bg-white dark:bg-gray-800 rounded-lg p-3">
                          <p className="text-xs text-gray-500 dark:text-gray-400">Model Size</p>
                          <p className="text-lg font-semibold text-gray-900 dark:text-white">
                            {routerStats.active ? '70B params' : '0.5-7B'}
                          </p>
                        </div>
                        <div className="bg-white dark:bg-gray-800 rounded-lg p-3">
                          <p className="text-xs text-gray-500 dark:text-gray-400">Cost/Month</p>
                          <p className="text-lg font-semibold text-green-600 dark:text-green-400">$0</p>
                        </div>
                        <div className="bg-white dark:bg-gray-800 rounded-lg p-3">
                          <p className="text-xs text-gray-500 dark:text-gray-400">Daily Limit</p>
                          <p className="text-lg font-semibold text-gray-900 dark:text-white">
                            {routerStats.active ? '16K+' : 'Unlimited'}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Model Configuration Section */}
                    {routerStats.enabled && routerStats.active && (
                      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                        <div className="flex items-center justify-between mb-4">
                          <div className="flex items-center gap-2">
                            <Cpu className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                              Model Configuration
                            </h3>
                          </div>
                          <button
                            onClick={fetchModelConfig}
                            className="text-sm text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300 flex items-center gap-1"
                          >
                            <RefreshCw className="h-4 w-4" />
                            Refresh
                          </button>
                        </div>
                        
                        {Object.keys(providerModels).length === 0 ? (
                          <div className="text-center py-8">
                            <Loader2 className="h-8 w-8 animate-spin text-indigo-600 mx-auto mb-2" />
                            <p className="text-sm text-gray-500 dark:text-gray-400">Loading model configuration...</p>
                          </div>
                        ) : (
                          <>
                            <div className="space-y-3">
                              {Object.entries(providerModels).map(([provider, currentModel], idx) => {
                            const isGroq = provider.includes('Groq');
                            const isOpenRouter = provider.includes('OpenRouter');
                            const isLLM7 = provider.includes('LLM7');
                            const isPrimary = routerStats.providers && routerStats.providers[0] === provider;
                            
                            return (
                              <div key={provider} className={`flex items-center justify-between p-3 rounded-lg ${
                                isPrimary 
                                  ? 'bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-300 dark:border-indigo-700' 
                                  : 'bg-gray-50 dark:bg-gray-900/50'
                              }`}>
                                <div className="flex-1">
                                  <div className="flex items-center gap-2 mb-1">
                                    <span className="font-medium text-gray-900 dark:text-white">{provider.split(' (')[0]}</span>
                                    {isGroq && <Zap className="h-4 w-4 text-yellow-500" />}
                                    {isOpenRouter && <Network className="h-4 w-4 text-blue-500" />}
                                    {isLLM7 && <Cloud className="h-4 w-4 text-purple-500" />}
                                    {isPrimary && (
                                      <span className="px-2 py-0.5 text-xs bg-indigo-600 text-white rounded-full font-medium">
                                        PRIMARY
                                      </span>
                                    )}
                                  </div>
                                  <p className="text-sm text-gray-600 dark:text-gray-400">
                                    Current: <code className="px-1 py-0.5 bg-gray-200 dark:bg-gray-800 rounded text-xs">{currentModel}</code>
                                  </p>
                                </div>
                                
                                <select
                                  value={currentModel}
                                  onChange={(e) => updateProviderModel(provider, e.target.value)}
                                  disabled={isUpdatingModel}
                                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white disabled:opacity-50"
                                >
                                  {availableModels[provider]?.map((model) => (
                                    <option key={model.name} value={model.name}>
                                      {model.name} {model.default && '(default)'}
                                    </option>
                                  ))}
                                </select>
                              </div>
                            );
                          })}
                        </div>
                        
                        <div className="mt-4 flex items-start gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                          <AlertCircle className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                          <div className="text-sm text-blue-800 dark:text-blue-300">
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
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                          Cloud Providers
                        </h3>
                        <div className="grid gap-4 md:grid-cols-3">
                          {routerStats.providers.map((provider: string, index: number) => {
                            const providerStats = routerStats.stats?.providers?.[provider];
                            const isGroq = provider.includes('Groq');
                            const isOpenRouter = provider.includes('OpenRouter');
                            const isLLM7 = provider.includes('LLM7');

                            const isPrimary = index === 0; // First provider is primary
                            
                            return (
                              <div
                                key={provider}
                                className={`border rounded-lg p-4 hover:border-indigo-500 dark:hover:border-indigo-400 transition-colors ${
                                  isPrimary 
                                    ? 'border-indigo-500 dark:border-indigo-400 bg-indigo-50/50 dark:bg-indigo-900/10' 
                                    : 'border-gray-200 dark:border-gray-700'
                                }`}
                              >
                                <div className="flex items-center justify-between mb-3">
                                  <div className="flex items-center gap-2">
                                    {isGroq && <Zap className="h-5 w-5 text-yellow-500" />}
                                    {isOpenRouter && <Network className="h-5 w-5 text-blue-500" />}
                                    {isLLM7 && <Cloud className="h-5 w-5 text-purple-500" />}
                                    <h4 className="font-medium text-gray-900 dark:text-white">
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
                  )}
                </div>
            )}

            {activeTab === 'voice' && (
              <div>
                {isLoadingVoiceProviders || allProviders.length === 0 ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-indigo-600 dark:text-indigo-400" />
                    <span className="ml-3 text-gray-600 dark:text-gray-400">Loading voice providers...</span>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {/* Header */}
                    <div className="flex items-center justify-between">
                      <div>
                        <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                          <Volume2 className="h-7 w-7 text-purple-600 dark:text-purple-400" />
                          Voice Provider Management
                        </h2>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          Configure and manage voice synthesis providers
                        </p>
                      </div>
                      <button
                        onClick={() => {
                          fetchVoiceProviders();
                          fetchVoiceCacheStats();
                          fetchAllProviders();
                        }}
                        disabled={isLoadingVoiceProviders}
                        className="px-4 py-2 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 flex items-center gap-2 transition-colors disabled:opacity-50"
                      >
                        <RefreshCw className={`h-4 w-4 ${isLoadingVoiceProviders ? 'animate-spin' : ''}`} />
                        Refresh
                      </button>
                    </div>

                    {/* Provider Cards Grid */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {allProviders.map((provider) => {
                        const isActive = provider.active;
                        const isConfigured = provider.configured;
                        const isEnabled = provider.enabled;
                        const needsConfig = provider.config_required && !isConfigured;

                        return (
                          <div
                            key={provider.id}
                            className={`bg-white dark:bg-gray-800 rounded-lg p-6 border-2 transition-all ${
                              isActive
                                ? 'border-purple-500 dark:border-purple-400 shadow-lg shadow-purple-500/20'
                                : 'border-gray-200 dark:border-gray-700'
                            }`}
                          >
                            {/* Provider Header */}
                            <div className="flex items-start justify-between mb-4">
                              <div className="flex items-center gap-3">
                                <div className={`p-3 rounded-lg ${
                                  provider.type === 'local'
                                    ? 'bg-blue-100 dark:bg-blue-900/30'
                                    : 'bg-green-100 dark:bg-green-900/30'
                                }`}>
                                  {provider.type === 'local' ? (
                                    <Monitor className={`h-6 w-6 ${
                                      provider.type === 'local'
                                        ? 'text-blue-600 dark:text-blue-400'
                                        : 'text-green-600 dark:text-green-400'
                                    }`} />
                                  ) : (
                                    <Cloud className="h-6 w-6 text-green-600 dark:text-green-400" />
                                  )}
                                </div>
                                <div>
                                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                                    {provider.name}
                                    {isActive && (
                                      <span className="px-2 py-0.5 text-xs font-medium bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 rounded-full flex items-center gap-1">
                                        <Radio className="h-3 w-3" />
                                        Active
                                      </span>
                                    )}
                                  </h3>
                                  <p className="text-sm text-gray-600 dark:text-gray-400">{provider.description}</p>
                                </div>
                              </div>
                            </div>

                            {/* Provider Status */}
                            <div className="flex items-center gap-3 mb-4">
                              <span className={`px-3 py-1 text-xs font-medium rounded-full ${
                                provider.status === 'available'
                                  ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                                  : provider.status === 'needs_config'
                                  ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
                                  : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                              }`}>
                                {provider.status === 'available' ? 'Available' : provider.status === 'needs_config' ? 'Needs Config' : 'Needs Setup'}
                              </span>
                              <span className="px-3 py-1 text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full capitalize">
                                {provider.type}
                              </span>
                              {isConfigured && (
                                <span className="px-3 py-1 text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded-full flex items-center gap-1">
                                  <CheckCircle className="h-3 w-3" />
                                  Configured
                                </span>
                              )}
                            </div>

                            {/* Capabilities */}
                            {provider.capabilities && (
                              <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
                                <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Capabilities:</p>
                                <div className="grid grid-cols-2 gap-2 text-xs">
                                  <div className="flex items-center justify-between">
                                    <span className="text-gray-600 dark:text-gray-400">Voices:</span>
                                    <span className="font-medium text-gray-900 dark:text-white">{provider.capabilities.voices}</span>
                                  </div>
                                  {provider.capabilities.languages && (
                                    <div className="flex items-center justify-between">
                                      <span className="text-gray-600 dark:text-gray-400">Languages:</span>
                                      <span className="font-medium text-gray-900 dark:text-white">
                                        {Array.isArray(provider.capabilities.languages)
                                          ? provider.capabilities.languages.length
                                          : provider.capabilities.languages}
                                      </span>
                                    </div>
                                  )}
                                  <div className="flex items-center justify-between">
                                    <span className="text-gray-600 dark:text-gray-400">Quality:</span>
                                    <span className="font-medium text-gray-900 dark:text-white capitalize">{provider.capabilities.quality}</span>
                                  </div>
                                  <div className="flex items-center justify-between">
                                    <span className="text-gray-600 dark:text-gray-400">Speed:</span>
                                    <span className="font-medium text-gray-900 dark:text-white capitalize">{provider.capabilities.speed}</span>
                                  </div>
                                  {provider.capabilities.voice_cloning !== undefined && (
                                    <div className="col-span-2 flex items-center gap-2">
                                      <span className="text-gray-600 dark:text-gray-400">Voice Cloning:</span>
                                      <span className={`font-medium ${
                                        provider.capabilities.voice_cloning
                                          ? 'text-green-600 dark:text-green-400'
                                          : 'text-gray-500 dark:text-gray-500'
                                      }`}>
                                        {provider.capabilities.voice_cloning ? 'Yes' : 'No'}
                                      </span>
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}

                            {/* Action Buttons */}
                            <div className="flex flex-wrap gap-2">
                              {!isActive && isConfigured && (
                                <button
                                  onClick={() => handleSetActiveProvider(provider.id)}
                                  className="flex-1 px-4 py-2 text-sm bg-purple-600 dark:bg-purple-500 text-white rounded-lg hover:bg-purple-700 dark:hover:bg-purple-600 transition-colors flex items-center justify-center gap-2"
                                >
                                  <Radio className="h-4 w-4" />
                                  Set Active
                                </button>
                              )}

                              {provider.config_required && (
                                <button
                                  onClick={() => {
                                    setSelectedProvider(provider);
                                    setIsConfigModalOpen(true);
                                  }}
                                  className={`flex-1 px-4 py-2 text-sm rounded-lg transition-colors flex items-center justify-center gap-2 ${
                                    isConfigured
                                      ? 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                                      : 'bg-blue-600 dark:bg-blue-500 text-white hover:bg-blue-700 dark:hover:bg-blue-600'
                                  }`}
                                >
                                  <Settings className="h-4 w-4" />
                                  {isConfigured ? 'Reconfigure' : 'Configure'}
                                </button>
                              )}

                              {isConfigured && (
                                <button
                                  onClick={() => handleTestProvider(provider.id)}
                                  disabled={isTestingProvider === provider.id}
                                  className="px-4 py-2 text-sm bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-lg hover:bg-green-200 dark:hover:bg-green-900/50 transition-colors flex items-center gap-2 disabled:opacity-50"
                                >
                                  {isTestingProvider === provider.id ? (
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                  ) : (
                                    <Play className="h-4 w-4" />
                                  )}
                                  Test
                                </button>
                              )}

                              {provider.requires_voice_sample && (
                                <button
                                  onClick={() => setIsVoiceModalOpen(true)}
                                  className="px-4 py-2 text-sm bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 rounded-lg hover:bg-orange-200 dark:hover:bg-orange-900/50 transition-colors flex items-center gap-2"
                                >
                                  <Mic className="h-4 w-4" />
                                  Record Sample
                                </button>
                              )}
                            </div>

                            {/* Setup Note */}
                            {provider.setup_note && (
                              <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
                                <p className="text-xs text-yellow-800 dark:text-yellow-200 flex items-start gap-2">
                                  <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                                  <span>{provider.setup_note}</span>
                                </p>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>

                    {/* Voice Cache Statistics */}
                    {voiceCacheStats && (
                      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                        <div className="flex items-center justify-between mb-4">
                          <div className="flex items-center gap-2">
                            <Database className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                              Voice Cache Performance
                            </h3>
                          </div>
                          <button
                            onClick={() => {
                              if (confirm('Clear all cached voice audio? This cannot be undone.')) {
                                fetch('http://localhost:5024/api/voice-synthesis/cache/clear', {
                                  method: 'DELETE',
                                  headers: { 'Authorization': `Bearer ${token}` }
                                }).then(() => {
                                  toast.success('Voice cache cleared');
                                  fetchVoiceCacheStats();
                                }).catch(() => toast.error('Failed to clear cache'));
                              }
                            }}
                            className="px-4 py-2 text-sm bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-lg hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors"
                          >
                            Clear Cache
                          </button>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4">
                            <p className="text-sm text-gray-600 dark:text-gray-400">Cache Hits</p>
                            <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                              {voiceCacheStats.hits || 0}
                            </p>
                          </div>
                          <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4">
                            <p className="text-sm text-gray-600 dark:text-gray-400">Cache Misses</p>
                            <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                              {voiceCacheStats.misses || 0}
                            </p>
                          </div>
                          <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4">
                            <p className="text-sm text-gray-600 dark:text-gray-400">Total Size</p>
                            <p className="text-2xl font-bold text-gray-900 dark:text-white">
                              {voiceCacheStats.total_size_mb?.toFixed(1) || '0'} MB
                            </p>
                          </div>
                          <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4">
                            <p className="text-sm text-gray-600 dark:text-gray-400">Hit Rate</p>
                            <p className="text-2xl font-bold text-gray-900 dark:text-white">
                              {voiceCacheStats.hit_rate ? `${(voiceCacheStats.hit_rate * 100).toFixed(1)}%` : 'N/A'}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Google Cloud TTS Configuration Modal */}
                {isConfigModalOpen && selectedProvider && (
                  <div className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 p-4">
                    <div className="bg-white dark:bg-gray-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-xl">
                      <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between">
                        <h3 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                          <Settings className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                          Configure {selectedProvider.name}
                        </h3>
                        <button
                          onClick={() => setIsConfigModalOpen(false)}
                          className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
                        >
                          <X className="h-5 w-5 text-gray-500 dark:text-gray-400" />
                        </button>
                      </div>

                      <div className="p-6">
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                          {selectedProvider.description}
                        </p>

                        {selectedProvider.id === 'google_cloud' && (
                          <div className="space-y-4">
                            <div>
                              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Service Account JSON Path
                              </label>
                              <input
                                type="text"
                                value={googleCredentials.credentials_path}
                                onChange={(e) => setGoogleCredentials(prev => ({ ...prev, credentials_path: e.target.value }))}
                                placeholder="/path/to/service-account.json"
                                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 dark:focus:ring-purple-400 focus:border-transparent transition-colors"
                              />
                              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                                Path to your Google Cloud service account JSON file
                              </p>
                            </div>

                            <div>
                              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Project ID
                              </label>
                              <input
                                type="text"
                                value={googleCredentials.project_id}
                                onChange={(e) => setGoogleCredentials(prev => ({ ...prev, project_id: e.target.value }))}
                                placeholder="your-project-id"
                                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 dark:focus:ring-purple-400 focus:border-transparent transition-colors"
                              />
                              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                                Your Google Cloud Project ID
                              </p>
                            </div>

                            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                              <p className="text-sm text-blue-800 dark:text-blue-200">
                                <strong>Free Tier:</strong> Google Cloud TTS offers 1-4M characters per month for free.
                                <a href="https://cloud.google.com/text-to-speech/pricing" target="_blank" rel="noopener noreferrer" className="underline ml-1">
                                  Learn more
                                </a>
                              </p>
                            </div>
                          </div>
                        )}

                        <div className="flex gap-3 mt-6">
                          <button
                            onClick={() => setIsConfigModalOpen(false)}
                            className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                          >
                            Cancel
                          </button>
                          <button
                            onClick={handleConfigureProvider}
                            disabled={isSavingConfig || !googleCredentials.credentials_path || !googleCredentials.project_id}
                            className="flex-1 px-4 py-2 bg-purple-600 dark:bg-purple-500 text-white rounded-lg hover:bg-purple-700 dark:hover:bg-purple-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                          >
                            {isSavingConfig ? (
                              <>
                                <Loader2 className="h-4 w-4 animate-spin" />
                                Saving...
                              </>
                            ) : (
                              <>
                                <Check className="h-4 w-4" />
                                Save Configuration
                              </>
                            )}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Voice Recording Modal */}
                {isVoiceModalOpen && (
                  <div className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 p-4">
                    <div className="bg-white dark:bg-gray-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-xl">
                      <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between">
                        <h3 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                          <Mic className="h-6 w-6 text-orange-600 dark:text-orange-400" />
                          Record Voice Sample
                        </h3>
                        <button
                          onClick={() => {
                            setIsVoiceModalOpen(false);
                            setIsRecording(false);
                            setRecordedAudio(null);
                            setCurrentPhraseIndex(0);
                            if (mediaRecorder) {
                              mediaRecorder.stop();
                              setMediaRecorder(null);
                            }
                          }}
                          className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
                        >
                          <X className="h-5 w-5 text-gray-500 dark:text-gray-400" />
                        </button>
                      </div>

                      <div className="p-6 space-y-6">
                        {/* Instructions */}
                        <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                          <p className="text-sm text-blue-800 dark:text-blue-200">
                            <strong>Instructions:</strong> Read the following phrase clearly and naturally. This voice sample will be used for voice cloning with XTTS v2 or StyleTTS2.
                          </p>
                        </div>

                        {/* Sample Phrase Display */}
                        <div className="bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-lg p-6 border-2 border-purple-200 dark:border-purple-800">
                          <p className="text-xs font-medium text-purple-600 dark:text-purple-400 mb-2">
                            Sample Phrase {currentPhraseIndex + 1} of {voiceSamplePhrases.length}
                          </p>
                          <p className="text-lg font-medium text-gray-900 dark:text-white text-center py-4">
                            "{voiceSamplePhrases[currentPhraseIndex]}"
                          </p>
                          <div className="flex justify-between mt-4">
                            <button
                              onClick={() => setCurrentPhraseIndex(Math.max(0, currentPhraseIndex - 1))}
                              disabled={currentPhraseIndex === 0 || isRecording}
                              className="px-3 py-1 text-sm bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                              Previous
                            </button>
                            <button
                              onClick={() => setCurrentPhraseIndex(Math.min(voiceSamplePhrases.length - 1, currentPhraseIndex + 1))}
                              disabled={currentPhraseIndex === voiceSamplePhrases.length - 1 || isRecording}
                              className="px-3 py-1 text-sm bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                              Next
                            </button>
                          </div>
                        </div>

                        {/* Recording Controls */}
                        <div className="flex flex-col items-center gap-4">
                          {/* Recording Status Indicator */}
                          {isRecording && (
                            <div className="flex items-center gap-2 text-red-600 dark:text-red-400 animate-pulse">
                              <div className="h-3 w-3 bg-red-600 dark:bg-red-400 rounded-full" />
                              <span className="text-sm font-medium">Recording...</span>
                            </div>
                          )}

                          {/* Record/Stop Button */}
                          {!recordedAudio && (
                            <button
                              onClick={isRecording ? stopRecording : startRecording}
                              className={`px-8 py-4 rounded-full font-medium text-white transition-all transform hover:scale-105 active:scale-95 flex items-center gap-3 ${
                                isRecording
                                  ? 'bg-red-600 dark:bg-red-500 hover:bg-red-700 dark:hover:bg-red-600'
                                  : 'bg-orange-600 dark:bg-orange-500 hover:bg-orange-700 dark:hover:bg-orange-600'
                              }`}
                            >
                              {isRecording ? (
                                <>
                                  <Square className="h-6 w-6" />
                                  Stop Recording
                                </>
                              ) : (
                                <>
                                  <Mic className="h-6 w-6" />
                                  Start Recording
                                </>
                              )}
                            </button>
                          )}

                          {/* Playback & Upload Controls */}
                          {recordedAudio && (
                            <div className="w-full space-y-4">
                              <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800 flex items-center gap-3">
                                <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400 flex-shrink-0" />
                                <div className="flex-1">
                                  <p className="text-sm font-medium text-green-800 dark:text-green-200">
                                    Recording Complete!
                                  </p>
                                  <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                                    Review your recording or record a new one
                                  </p>
                                </div>
                              </div>

                              <div className="flex gap-3">
                                <button
                                  onClick={playRecordedAudio}
                                  className="flex-1 px-4 py-3 bg-blue-600 dark:bg-blue-500 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-600 transition-colors flex items-center justify-center gap-2"
                                >
                                  <Play className="h-5 w-5" />
                                  Play Recording
                                </button>
                                <button
                                  onClick={() => {
                                    setRecordedAudio(null);
                                    setIsRecording(false);
                                  }}
                                  className="flex-1 px-4 py-3 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors flex items-center justify-center gap-2"
                                >
                                  <RefreshCw className="h-5 w-5" />
                                  Record Again
                                </button>
                              </div>

                              <button
                                onClick={async () => {
                                  toast.info('Voice sample upload functionality will be integrated with personality selection');
                                }}
                                disabled={uploadingVoiceSample}
                                className="w-full px-4 py-3 bg-green-600 dark:bg-green-500 text-white rounded-lg hover:bg-green-700 dark:hover:bg-green-600 transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                              >
                                {uploadingVoiceSample ? (
                                  <>
                                    <Loader2 className="h-5 w-5 animate-spin" />
                                    Uploading...
                                  </>
                                ) : (
                                  <>
                                    <Upload className="h-5 w-5" />
                                    Upload Voice Sample
                                  </>
                                )}
                              </button>
                            </div>
                          )}
                        </div>

                        {/* Tips */}
                        <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
                          <p className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">Recording Tips:</p>
                          <ul className="text-xs text-gray-600 dark:text-gray-400 space-y-1 list-disc list-inside">
                            <li>Use a quiet environment</li>
                            <li>Speak naturally and clearly</li>
                            <li>Record 5-10 seconds of speech</li>
                            <li>Avoid background noise</li>
                            <li>Stay close to the microphone</li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'personalities' && (
              <Personalities />
            )}
          </div>
        </div>
      </div>
    </div>

    {/* JSON Editor Modal */}
    {editingFile && (
      <JsonEditor
        initialValue={editingFile.content}
        title={editingFile.name}
        onSave={async (updatedContent) => {
          try {
            const response = await fetch('http://localhost:5024/api/admin/configuration/update', {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                config_type: editingFile.type,
                config_data: updatedContent
              })
            });

            const data = await response.json();

            if (data.status === 'success') {
              toast.success(t('common:toasts.config.updateSuccess'));
              setEditingFile(null);
              // Refresh configuration to show updated values
              fetchConfiguration();
            } else {
              toast.error(data.detail || t('common:toasts.config.updateFailed'));
            }
          } catch (error) {
            console.error('Error saving configuration:', error);
            toast.error(t('common:toasts.config.updateFailed'));
          }
        }}
        onCancel={() => setEditingFile(null)}
      />
      )}
    </React.Fragment>
  );
};

export default AIManagement;