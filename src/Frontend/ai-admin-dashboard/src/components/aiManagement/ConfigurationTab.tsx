import React, { useState, useEffect } from 'react';
import {
  Settings,
  Loader2,
  Database,
  Edit,
  ChevronRight,
  ChevronDown,
  User,
  MessageSquare,
  FileJson,
  AlertCircle
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { useTranslation } from 'react-i18next';
import JsonEditor from '../JsonEditor';
import { getApiEndpoint } from '@/config/app.config';

interface ConfigurationTabProps {
  token?: string;
}

const ConfigurationTab: React.FC<ConfigurationTabProps> = ({ token }) => {
  const { t } = useTranslation(['common']);

  // State for configuration
  const [configuration, setConfiguration] = useState<any>(null);
  const [isLoadingConfig, setIsLoadingConfig] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<string>('');
  const [selectedPersonality, setSelectedPersonality] = useState<string>('');
  const [agents, setAgents] = useState<any[]>([]);
  const [personalities, setPersonalities] = useState<any[]>([]);
  const [isLoadingAgents, setIsLoadingAgents] = useState(false);
  const [isLoadingPersonalities, setIsLoadingPersonalities] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    system: true,
    agent: true,
    personality: true
  });
  const [editingFile, setEditingFile] = useState<any>(null);

  // Fetch configuration
  const fetchConfiguration = async (agent?: string, personality?: string) => {
    setIsLoadingConfig(true);
    try {
      let url = getApiEndpoint('/admin/configuration');
      const params = new URLSearchParams();
      if (agent) params.append('agent', agent);
      if (personality) params.append('personality', personality);
      if (params.toString()) url += '?' + params.toString();

      const response = await fetch(url, {
        headers: {
          'Authorization': token ? `Bearer ${token}` : ''
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
      const response = await fetch(getApiEndpoint('/admin/agents'), {
        headers: {
          'Authorization': token ? `Bearer ${token}` : ''
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
      const response = await fetch(getApiEndpoint(`/admin/agents/${agentId}/personalities`), {
        headers: {
          'Authorization': token ? `Bearer ${token}` : ''
        }
      });
      const data = await response.json();
      if (data.personalities) {
        setPersonalities(data.personalities);
        // Set default personality if available
        if (!selectedPersonality && data.personalities.length > 0) {
          const defaultPersonality = data.personalities.find((p: any) => p.id === 'default') || data.personalities[0];
          setSelectedPersonality(defaultPersonality.id);
        }
      }
    } catch (error) {
      console.error('Error fetching personalities:', error);
      setPersonalities([]);
    }
    setIsLoadingPersonalities(false);
  };

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  useEffect(() => {
    fetchAgents();
    if (selectedAgent && selectedPersonality) {
      fetchConfiguration(selectedAgent, selectedPersonality);
    } else {
      fetchConfiguration();
    }
  }, []);

  useEffect(() => {
    if (selectedAgent) {
      fetchPersonalities(selectedAgent);
    }
  }, [selectedAgent]);

  useEffect(() => {
    if (selectedAgent && selectedPersonality) {
      fetchConfiguration(selectedAgent, selectedPersonality);
    }
  }, [selectedAgent, selectedPersonality]);

  return (
    <>
      <div>
        {/* Info Message for First Load */}
        {agents.length === 0 && !isLoadingAgents && !isLoadingConfig && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-medium text-blue-900 dark:text-blue-200 mb-1">
                  Configuration Not Loaded
                </h4>
                <p className="text-sm text-blue-700 dark:text-blue-300">
                  Click the "Refresh" button to load agents and configuration data.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Agent and Personality Selection */}
        <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4 sm:p-6 mb-4 sm:mb-6">
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

        <div className="flex items-center justify-between mb-4 sm:mb-6">
          <h3 className="text-base sm:text-lg font-medium text-gray-900 dark:text-white">
            Configuration for {selectedAgent || 'Default'} / {selectedPersonality || 'Default'}
          </h3>
          <button
            onClick={() => fetchConfiguration(selectedAgent, selectedPersonality)}
            disabled={isLoadingConfig}
            className="px-3 sm:px-4 py-2 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 flex items-center gap-2 transition-colors"
          >
            {isLoadingConfig && <Loader2 className="h-4 w-4 animate-spin" />}
            <span className="hidden sm:inline">Refresh</span>
            <span className="sm:hidden">Refresh</span>
          </button>
        </div>

        {isLoadingConfig ? (
          <div className="flex items-center justify-center py-8 sm:py-12">
            <Loader2 className="h-6 w-6 sm:h-8 sm:w-8 animate-spin text-indigo-600 dark:text-indigo-400" />
          </div>
        ) : !configuration ? (
          <p className="text-sm sm:text-base text-gray-500 dark:text-gray-400 text-center py-8 sm:py-12">
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
                      <Database className="h-4 w-4 sm:h-5 sm:w-5 text-gray-600 dark:text-gray-400" />
                      <h4 className="text-sm sm:text-base font-medium text-gray-900 dark:text-white">System Configuration</h4>
                    </div>
                    {configuration.configurations.system.config && (
                      <button
                        onClick={() => setEditingFile({
                          name: 'System Configuration',
                          content: configuration.configurations.system.config,
                          type: 'system'
                        })}
                        className="flex items-center gap-1 px-2 sm:px-3 py-1 text-xs sm:text-sm text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded transition-colors"
                      >
                        <Edit className="h-3 w-3 sm:h-4 sm:w-4" />
                        Edit
                      </button>
                    )}
                  </div>
                  <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-2 ml-7">
                    Core system settings and parameters
                  </p>
                </div>
                {expandedSections.system && configuration.configurations.system.config && (
                  <div className="border-t border-gray-200 dark:border-gray-700 p-4">
                    <pre className="text-xs sm:text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-mono">
                      {JSON.stringify(configuration.configurations.system.config, null, 2)}
                    </pre>
                  </div>
                )}
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
                      <User className="h-4 w-4 sm:h-5 sm:w-5 text-gray-600 dark:text-gray-400" />
                      <h4 className="text-sm sm:text-base font-medium text-gray-900 dark:text-white">Agent Configuration</h4>
                    </div>
                    {configuration.configurations.agent.config && (
                      <button
                        onClick={() => setEditingFile({
                          name: 'Agent Configuration',
                          content: configuration.configurations.agent.config,
                          type: 'agent'
                        })}
                        className="flex items-center gap-1 px-2 sm:px-3 py-1 text-xs sm:text-sm text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded transition-colors"
                      >
                        <Edit className="h-3 w-3 sm:h-4 sm:w-4" />
                        Edit
                      </button>
                    )}
                  </div>
                  <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-2 ml-7">
                    Agent behavior and response settings
                  </p>
                </div>
                {expandedSections.agent && configuration.configurations.agent.config && (
                  <div className="border-t border-gray-200 dark:border-gray-700 p-4">
                    <pre className="text-xs sm:text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-mono">
                      {JSON.stringify(configuration.configurations.agent.config, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}

            {/* Personality Configuration */}
            {configuration.configurations?.personality && (
              <div className="border border-gray-200 dark:border-gray-700 rounded-lg">
                <div className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => toggleSection('personality')}
                        className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
                      >
                        {expandedSections.personality ?
                          <ChevronDown className="h-4 w-4" /> :
                          <ChevronRight className="h-4 w-4" />
                        }
                      </button>
                      <MessageSquare className="h-4 w-4 sm:h-5 sm:w-5 text-gray-600 dark:text-gray-400" />
                      <h4 className="text-sm sm:text-base font-medium text-gray-900 dark:text-white">Personality Configuration</h4>
                    </div>
                    {configuration.configurations.personality.config && (
                      <button
                        onClick={() => setEditingFile({
                          name: 'Personality Configuration',
                          content: configuration.configurations.personality.config,
                          type: 'personality'
                        })}
                        className="flex items-center gap-1 px-2 sm:px-3 py-1 text-xs sm:text-sm text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded transition-colors"
                      >
                        <Edit className="h-3 w-3 sm:h-4 sm:w-4" />
                        Edit
                      </button>
                    )}
                  </div>
                  <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-2 ml-7">
                    Personality traits and dialogue style
                  </p>
                </div>
                {expandedSections.personality && configuration.configurations.personality.config && (
                  <div className="border-t border-gray-200 dark:border-gray-700 p-4">
                    <pre className="text-xs sm:text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-mono">
                      {JSON.stringify(configuration.configurations.personality.config, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}

            {/* No Configuration Message */}
            {!configuration.configurations?.system &&
             !configuration.configurations?.agent &&
             !configuration.configurations?.personality && (
              <div className="text-center py-8 sm:py-12">
                <AlertCircle className="h-10 w-10 sm:h-12 sm:w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-sm sm:text-base text-gray-500 dark:text-gray-400">
                  No configuration available for this combination
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* JSON Editor Modal */}
      {editingFile && (
        <JsonEditor
          initialValue={editingFile.content}
          title={editingFile.name}
          onSave={async (updatedContent) => {
            try {
              // Save logic here
              toast.success('Configuration updated');
              setEditingFile(null);
              // Refresh configuration after save
              fetchConfiguration(selectedAgent, selectedPersonality);
            } catch (error) {
              toast.error('Failed to update configuration');
            }
          }}
          onCancel={() => setEditingFile(null)}
        />
      )}
    </>
  );
};

export default ConfigurationTab;