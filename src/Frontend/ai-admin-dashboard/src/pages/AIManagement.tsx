import React, { useState, useEffect } from 'react';
import { Bot, Loader2, AlertCircle, CheckCircle, Cpu, Settings, Database, FileCode, ChevronDown, ChevronRight, Eye, Edit } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';
import JsonEditor from '../components/JsonEditor';

interface Model {
  name: string;
  filename: string;
  path: string;
  size_gb: number;
}

const AIManagement: React.FC = () => {
  const { token } = useAuth();
  const [models, setModels] = useState<Model[]>([]);
  const [currentModel, setCurrentModel] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingModel, setIsLoadingModel] = useState(false);
  const [modelLoadStatus, setModelLoadStatus] = useState<string>('');
  const [modelError, setModelError] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'models' | 'configuration'>('models');
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
      toast.error('Failed to fetch models');
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
    setIsLoadingModel(true);
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

      if (data.status === 'success') {
        setCurrentModel(modelName);
        setModelLoadStatus('Model loaded successfully');
        toast.success(`Model ${modelName} loaded successfully`);

        // Fetch updated configuration after loading
        if (activeTab === 'configuration') {
          fetchConfiguration();
        }
      } else {
        setModelError(data.error || 'Failed to load model');
        toast.error(data.error || 'Failed to load model');
      }
    } catch (error) {
      console.error('Error loading model:', error);
      setModelError('Failed to load model');
      toast.error('Failed to load model');
    }

    setIsLoadingModel(false);
  };

  // Unload current model
  const unloadModel = async () => {
    setIsLoadingModel(true);
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
        toast.success('Model unloaded successfully');
      } else {
        setModelError(data.error || 'Failed to unload model');
        toast.error(data.error || 'Failed to unload model');
      }
    } catch (error) {
      console.error('Error unloading model:', error);
      setModelError('Failed to unload model');
      toast.error('Failed to unload model');
    }

    setIsLoadingModel(false);
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
      toast.error('Failed to fetch configuration');
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
      toast.error('Failed to fetch agents');
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
      toast.error('Failed to fetch personalities');
    }
    setIsLoadingPersonalities(false);
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

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-4">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg">
              <Bot className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">AI Engine Management</h1>
          </div>

          {/* Tabs */}
          <div className="flex gap-4 mb-6 border-b border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setActiveTab('models')}
              className={`pb-3 px-1 font-medium transition-colors ${
                activeTab === 'models'
                  ? 'text-indigo-600 dark:text-indigo-400 border-b-2 border-indigo-600 dark:border-indigo-400'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              Models
            </button>
            <button
              onClick={() => setActiveTab('configuration')}
              className={`pb-3 px-1 font-medium transition-colors ${
                activeTab === 'configuration'
                  ? 'text-indigo-600 dark:text-indigo-400 border-b-2 border-indigo-600 dark:border-indigo-400'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              Configuration
            </button>
          </div>

          {/* Tab Content */}
          <div className="space-y-6">
            {activeTab === 'models' && (
              <div>
                {/* Current Status */}
                <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4 mb-6">
                  <div className="flex items-center justify-between">
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
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Available Models</h2>

                  {isLoading ? (
                    <div className="flex items-center justify-center py-12">
                      <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
                    </div>
                  ) : models.length === 0 ? (
                    <p className="text-gray-500 dark:text-gray-400 text-center py-12">No models found</p>
                  ) : (
                    <div className="grid gap-4">
                      {models.map((model) => (
                        <div
                          key={model.name}
                          className={`border rounded-lg p-4 transition-all ${
                            currentModel === model.name
                              ? 'border-indigo-500 dark:border-indigo-400 bg-indigo-50 dark:bg-indigo-900/20'
                              : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <Cpu className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                                <h3 className="font-medium text-gray-900 dark:text-white">{model.name}</h3>
                                {currentModel === model.name && (
                                  <span className="px-2 py-0.5 text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full">
                                    Active
                                  </span>
                                )}
                              </div>
                              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                                {model.filename} • {model.size_gb} GB
                              </p>
                            </div>
                            {currentModel !== model.name && (
                              <button
                                onClick={() => loadModel(model.name)}
                                disabled={isLoadingModel}
                                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                              >
                                {isLoadingModel ? (
                                  <span className="flex items-center gap-2">
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
                toast.success('Configuration updated successfully');
                setEditingFile(null);
                // Refresh configuration to show updated values
                fetchConfiguration();
              } else {
                toast.error(data.detail || 'Failed to update configuration');
              }
            } catch (error) {
              console.error('Error saving configuration:', error);
              toast.error('Failed to save configuration');
            }
          }}
          onCancel={() => setEditingFile(null)}
        />
      )}
    </div>
  );
};

export default AIManagement;