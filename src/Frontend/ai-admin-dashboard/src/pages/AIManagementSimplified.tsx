import React, { useState, useEffect } from 'react';
import { Bot, Cpu, Settings, Zap, Volume2, User } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { useStoreContext } from '../contexts/StoreContext';
import ModelsTab from '../components/aiManagement/ModelsTab';
import ConfigurationTab from '../components/aiManagement/ConfigurationTab';
import InferenceTab from '../components/aiManagement/InferenceTab';
import VoiceTab from '../components/aiManagement/VoiceTab';
import Personalities from '../components/Personalities';
import JsonEditor from '../components/JsonEditor';

const AIManagementSimplified: React.FC = () => {
  const { t } = useTranslation(['common']);
  const { currentStore } = useStoreContext();
  const [activeTab, setActiveTab] = useState<string>('models');

  // State for models tab
  const [models, setModels] = useState<any[]>([]);
  const [currentModel, setCurrentModel] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingModel, setIsLoadingModel] = useState<string | null>(null);
  const [modelStatuses, setModelStatuses] = useState<Record<string, any>>({});

  // State for JSON editor modal
  const [editingFile, setEditingFile] = useState<any>(null);

  // Placeholder functions for models
  const fetchModels = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get('/api/ai/models');
      setModels(response.data.models || []);
      setCurrentModel(response.data.current || null);
    } catch (error) {
      toast.error('Failed to fetch models');
    }
    setIsLoading(false);
  };

  const loadModel = async (modelName: string) => {
    setIsLoadingModel(modelName);
    try {
      await axios.post('/api/ai/models/load', { model: modelName });
      toast.success(`Model ${modelName} loaded`);
      await fetchModels();
    } catch (error) {
      toast.error('Failed to load model');
    }
    setIsLoadingModel(null);
  };

  const unloadModel = async (modelName: string) => {
    setIsLoadingModel(modelName);
    try {
      await axios.post('/api/ai/models/unload', { model: modelName });
      toast.success(`Model ${modelName} unloaded`);
      await fetchModels();
    } catch (error) {
      toast.error('Failed to unload model');
    }
    setIsLoadingModel(null);
  };

  const downloadModel = async (modelName: string) => {
    try {
      await axios.post('/api/ai/models/download', { model: modelName });
      toast.success(`Downloading ${modelName}...`);
    } catch (error) {
      toast.error('Failed to download model');
    }
  };

  useEffect(() => {
    if (activeTab === 'models') {
      fetchModels();
    }
  }, [activeTab]);

  const tabs = [
    { id: 'models', label: 'Models', icon: Cpu },
    { id: 'configuration', label: 'Configuration', icon: Settings },
    { id: 'inference', label: 'Inference', icon: Zap },
    { id: 'voice', label: 'Voice', icon: Volume2 },
    { id: 'personalities', label: 'Personalities', icon: User },
  ];

  return (
    <React.Fragment>
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-4 sm:p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-4 sm:p-6 transition-colors">
            {/* Header */}
            <div className="flex items-center gap-3 mb-4 sm:mb-6">
              <div className="p-2 sm:p-3 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-xl shadow-lg">
                <Bot className="h-5 w-5 sm:h-6 sm:w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
                  {t('ai.management.title')}
                </h1>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {t('ai.management.subtitle')}
                </p>
              </div>
            </div>

            {/* Tab Navigation */}
            <div className="flex gap-2 sm:gap-4 mb-4 sm:mb-6 border-b border-gray-200 dark:border-gray-700 overflow-x-auto -mx-4 sm:mx-0 px-4 sm:px-0">
              <nav className="-mb-px flex space-x-2 sm:space-x-4 min-w-max sm:min-w-0">
                {tabs.map(tab => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`pb-3 px-1 font-medium text-xs sm:text-sm whitespace-nowrap transition-colors ${
                        activeTab === tab.id
                          ? 'text-indigo-600 dark:text-indigo-400 border-b-2 border-indigo-600 dark:border-indigo-400'
                          : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                      }`}
                    >
                      <Icon className="h-4 w-4 inline mr-1" />
                      {tab.label}
                    </button>
                  );
                })}
              </nav>
            </div>

            {/* Tab Content */}
            <div className="space-y-4 sm:space-y-6">
              {activeTab === 'models' && (
                <ModelsTab
                  currentModel={currentModel}
                  models={models}
                  isLoading={isLoading}
                  isLoadingModel={isLoadingModel}
                  modelStatuses={modelStatuses}
                  fetchModels={fetchModels}
                  loadModel={loadModel}
                  unloadModel={unloadModel}
                  downloadModel={downloadModel}
                />
              )}

              {activeTab === 'configuration' && (
                <ConfigurationTab />
              )}

              {activeTab === 'inference' && (
                <InferenceTab tenantId={currentStore?.tenant_id} />
              )}

              {activeTab === 'voice' && (
                <VoiceTab />
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
              // Save logic here
              toast.success('Configuration updated');
              setEditingFile(null);
            } catch (error) {
              toast.error('Failed to update configuration');
            }
          }}
          onCancel={() => setEditingFile(null)}
        />
      )}
    </React.Fragment>
  );
};

export default AIManagementSimplified;