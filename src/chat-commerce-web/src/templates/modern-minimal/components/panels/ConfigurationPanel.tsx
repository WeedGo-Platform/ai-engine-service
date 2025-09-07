import React, { useState, useEffect } from 'react';
import { Preset, Tool, Voice } from '../../types';
import { modelApi, voiceApi } from '../../../../services/api';

interface ConfigurationPanelProps {
  isOpen: boolean;
  onClose: () => void;
  presets: Preset[];
  selectedPersonality: string;
  isModelLoaded: boolean;
  onPresetLoad: (preset: Preset) => void;
  configDetails: any;
  availableVoices: Voice[];
  selectedVoice: string;
  onVoiceChange: (voiceId: string) => void;
  isSpeakerEnabled: boolean;
  onToggleSpeaker: () => void;
  activeTools: Tool[];
}

const ConfigurationPanel: React.FC<ConfigurationPanelProps> = ({
  isOpen,
  onClose,
  presets: propPresets,
  selectedPersonality,
  isModelLoaded,
  onPresetLoad,
  configDetails,
  availableVoices: propVoices,
  selectedVoice,
  onVoiceChange,
  isSpeakerEnabled,
  onToggleSpeaker,
  activeTools: propTools
}) => {
  const [selectedAgent, setSelectedAgent] = useState<string>('budtender');
  const [personalities, setPersonalities] = useState<Preset[]>(propPresets);
  const [voices, setVoices] = useState<Voice[]>(propVoices);
  const [activeTools, setActiveTools] = useState<Tool[]>(propTools);
  const [isLoadingPersonalities, setIsLoadingPersonalities] = useState(false);
  const [isLoadingVoices, setIsLoadingVoices] = useState(false);
  const [isLoadingTools, setIsLoadingTools] = useState(false);

  const agents = [
    { id: 'medical_advisor', name: 'Medical Advisor', icon: '⚕️' },
    { id: 'budtender', name: 'Budtender', icon: '🌿' },
    { id: 'cannabis_sommelier', name: 'Cannabis Sommelier', icon: '🍷' }
  ];

  // Fetch personalities when agent changes
  useEffect(() => {
    const fetchPersonalities = async () => {
      setIsLoadingPersonalities(true);
      try {
        const data = await modelApi.getPersonalities(selectedAgent);
        if (data && data.personalities) {
          const formattedPersonalities = data.personalities.map((p: any) => ({
            id: p.id || p.name,
            name: p.name,
            description: p.description || '',
            icon: p.icon || '💬',
            personality: p.id || p.name,
            config: p.config
          }));
          setPersonalities(formattedPersonalities);
        }
      } catch (error) {
        console.error('Failed to fetch personalities:', error);
        setPersonalities(propPresets);
      } finally {
        setIsLoadingPersonalities(false);
      }
    };

    if (selectedAgent) {
      fetchPersonalities();
    }
  }, [selectedAgent, propPresets]);

  // Fetch voices on mount
  useEffect(() => {
    const fetchVoices = async () => {
      setIsLoadingVoices(true);
      try {
        const data = await voiceApi.getVoices();
        if (Array.isArray(data)) {
          setVoices(data);
        }
      } catch (error) {
        console.error('Failed to fetch voices:', error);
        setVoices(propVoices);
      } finally {
        setIsLoadingVoices(false);
      }
    };

    fetchVoices();
  }, [propVoices]);

  // Fetch active tools on mount
  useEffect(() => {
    const fetchActiveTools = async () => {
      setIsLoadingTools(true);
      try {
        const data = await modelApi.getActiveTools();
        if (data && data.tools) {
          setActiveTools(data.tools);
        }
      } catch (error) {
        console.error('Failed to fetch active tools:', error);
        setActiveTools(propTools);
      } finally {
        setIsLoadingTools(false);
      }
    };

    fetchActiveTools();
  }, [propTools]);

  return (
    <div className={`fixed left-0 top-[72px] h-[calc(100vh-72px)] w-80 bg-white shadow-xl border-r border-slate-200 transform transition-transform duration-300 z-30 ${
      isOpen ? 'translate-x-0' : '-translate-x-full'
    }`}>
      <div className="p-6 h-full overflow-y-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-light text-slate-900">
                AI Configuration
              </h2>
              <p className="text-sm text-slate-500 mt-1">Manage your AI settings</p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Agent Selector */}
        <div className="mb-8">
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-3">
            Select Agent
          </label>
          <select
            value={selectedAgent}
            onChange={(e) => setSelectedAgent(e.target.value)}
            className="w-full px-4 py-3 bg-white text-slate-900 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent text-sm font-medium hover:border-slate-400 transition-colors"
          >
            {agents.map(agent => (
              <option key={agent.id} value={agent.id}>
                {agent.name}
              </option>
            ))}
          </select>
        </div>

        {/* Quick Presets */}
        <div className="mb-8">
          <h3 className="text-xs font-semibold text-slate-700 mb-4 uppercase tracking-wider">
            Quick Presets
          </h3>
          {isLoadingPersonalities ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div>
            </div>
          ) : (
            <div className="space-y-2">
              {personalities.map(preset => (
                <button
                  key={preset.id}
                  onClick={() => onPresetLoad(preset)}
                  disabled={!isModelLoaded}
                  className={`w-full p-4 bg-white hover:bg-slate-50 border rounded-lg transition-all group ${
                    !isModelLoaded ? 'opacity-50 cursor-not-allowed' : ''
                  } ${
                    selectedPersonality === preset.personality 
                      ? 'border-slate-900 shadow-md' 
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                  title={isModelLoaded ? `Switch to ${preset.name}` : 'Load a model first'}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xl">{preset.icon}</span>
                    <div className="text-left flex-1">
                      <div className="font-medium text-slate-900">
                        {preset.name}
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5">
                        {preset.description}
                      </div>
                    </div>
                    {selectedPersonality === preset.personality ? (
                      <div className="p-1 bg-slate-900 rounded-full">
                        <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" />
                        </svg>
                      </div>
                    ) : (
                      <svg className="w-4 h-4 text-slate-400 group-hover:text-slate-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                      </svg>
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Voice Settings */}
        <div className="mb-8 p-4 bg-slate-50 rounded-lg border border-slate-200">
          <h3 className="text-xs font-semibold text-slate-700 mb-4 uppercase tracking-wider">
            Voice Settings
          </h3>
          {isLoadingVoices ? (
            <div className="flex items-center justify-center py-6">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-slate-900"></div>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-xs text-slate-600 mb-2 font-medium">
                  Voice Selection
                </label>
                <select
                  value={selectedVoice}
                  onChange={(e) => onVoiceChange(e.target.value)}
                  className="w-full px-3 py-2 bg-white text-slate-900 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent text-sm"
                >
                  <option value="">Default Voice</option>
                  {Array.isArray(voices) && voices.map(voice => (
                    <option key={voice.id} value={voice.id}>
                      {voice.name} {voice.language ? `(${voice.language})` : ''} {voice.gender ? `- ${voice.gender}` : ''}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-600 font-medium">Text-to-Speech</span>
                <button
                  onClick={onToggleSpeaker}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    isSpeakerEnabled 
                      ? 'bg-slate-900' 
                      : 'bg-slate-300'
                  }`}
                  title={isSpeakerEnabled ? 'Disable TTS' : 'Enable TTS'}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      isSpeakerEnabled ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Configuration Status */}
        {configDetails && (
          <div className="mb-8 p-4 bg-slate-50 rounded-lg border border-slate-200">
            <h3 className="text-xs font-semibold text-slate-700 mb-4 uppercase tracking-wider">
              Applied Configuration
            </h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-600">Name</span>
                <span className="text-slate-900 font-medium">{configDetails.name || 'Custom Config'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Version</span>
                <span className="text-slate-900">{configDetails.version || '1.0.0'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Temperature</span>
                <span className="text-slate-900">{configDetails.temperature || 'Default'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Max Tokens</span>
                <span className="text-slate-900">{configDetails.max_tokens || 'Default'}</span>
              </div>
            </div>
          </div>
        )}
        
        {/* Active Tools */}
        {(activeTools.length > 0 || isLoadingTools) && (
          <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
            <h3 className="text-xs font-semibold text-slate-700 mb-4 uppercase tracking-wider">
              Active Tools
            </h3>
            {isLoadingTools ? (
              <div className="flex items-center justify-center py-6">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-slate-900"></div>
              </div>
            ) : (
              <div className="space-y-2">
                {activeTools.map(tool => (
                  <div key={tool.name} className="flex items-center gap-3 text-sm">
                    <div className={`w-2 h-2 rounded-full ${
                      tool.enabled 
                        ? 'bg-green-500' 
                        : 'bg-slate-300'
                    }`} />
                    <span className="text-slate-700">{tool.name}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ConfigurationPanel;