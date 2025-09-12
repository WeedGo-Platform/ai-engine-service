import React, { useState, useEffect } from 'react';
import { Preset, Tool, Voice } from '../../types';
import { modelApi, voiceApi } from '../../../../services/api';
import TemplateSwitcher from '../layout/TemplateSwitcher';
import { productSearchService, Product } from '../../../../services/productSearch';
import EnhancedProductFilter from '../../../../components/shared/EnhancedProductFilter';

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
  currentTemplate?: string;
  availableTemplates?: string[];
  onTemplateChange?: (template: string) => void;
}

const ConfigurationPanel: React.FC<ConfigurationPanelProps> = ({
  isOpen,
  onClose,
  presets: propPresets = [],
  selectedPersonality,
  isModelLoaded,
  onPresetLoad,
  configDetails,
  availableVoices: propVoices = [],
  selectedVoice,
  onVoiceChange,
  isSpeakerEnabled,
  onToggleSpeaker,
  activeTools: propTools = [],
  currentTemplate,
  availableTemplates,
  onTemplateChange
}) => {
  const [selectedAgent, setSelectedAgent] = useState<string>('budtender');
  const [personalities, setPersonalities] = useState<Preset[]>(propPresets || []);
  const [voices, setVoices] = useState<Voice[]>(propVoices || []);
  const [activeTools, setActiveTools] = useState<Tool[]>(propTools || []);
  const [isLoadingPersonalities, setIsLoadingPersonalities] = useState(false);
  const [isLoadingVoices, setIsLoadingVoices] = useState(false);
  const [isLoadingTools, setIsLoadingTools] = useState(false);
  
  // Product search state
  const [searchResults, setSearchResults] = useState<Product[]>([]);

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
        setPersonalities(propPresets || []);
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
        setVoices(propVoices || []);
      } finally {
        setIsLoadingVoices(false);
      }
    };

    fetchVoices();
  }, []); // Only run once on mount

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
        setActiveTools(propTools || []);
      } finally {
        setIsLoadingTools(false);
      }
    };

    fetchActiveTools();
  }, []); // Only run once on mount

  return (
    <div className={`fixed left-0 top-[60px] sm:top-[72px] h-[calc(100vh-60px)] sm:h-[calc(100vh-72px)] w-full sm:w-80 bg-white shadow-xl border-r border-[#E5E7EB] transform transition-transform duration-300 z-30 ${
      isOpen ? 'translate-x-0' : '-translate-x-full'
    }`}>
      <div className="p-4 sm:p-6 h-full overflow-y-auto">
        {/* Header */}
        <div className="mb-6 sm:mb-8">
          <div>
            <h2 className="text-xl sm:text-2xl font-semibold text-[#1F2937]">
              AI Configuration
            </h2>
            <p className="text-sm text-[#6B7280] mt-1 hidden sm:block">Manage your AI settings</p>
          </div>
        </div>

        {/* Enhanced Product Search Filter */}
        <div className="mb-8 -mx-2">
          <EnhancedProductFilter 
            onResultsChange={(results) => {
              setSearchResults(results);
              // Optionally send results to chat
              if (results.length > 0 && results.length <= 5) {
                console.log('Product search results:', results);
                // Could trigger a chat message with results here
              }
            }}
            className=""
          />
        </div>

        {/* Agent Selector */}
        <div className="mb-8">
          <label className="block text-xs font-semibold text-[#6B7280] uppercase tracking-wider mb-3 px-1">
            Select Agent
          </label>
          <select
            value={selectedAgent}
            onChange={(e) => setSelectedAgent(e.target.value)}
            className="w-full px-4 py-3 bg-white text-[#1F2937] border border-[#E5E7EB] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1E40AF] focus:border-transparent text-sm font-medium hover:border-[#DC2626] transition-colors"
          >
            {agents.map(agent => (
              <option key={agent.id} value={agent.id}>
                {agent.name}
              </option>
            ))}
          </select>
        </div>

        {/* Theme Selector */}
        {currentTemplate && availableTemplates && onTemplateChange && (
          <div className="mb-8">
            <h3 className="text-xs font-semibold text-[#6B7280] mb-4 uppercase tracking-wider px-1">
              Choose Theme
            </h3>
            <TemplateSwitcher 
              currentTemplate={currentTemplate}
              availableTemplates={availableTemplates}
              onTemplateChange={onTemplateChange}
            />
          </div>
        )}

        {/* Voice Settings */}
        <div className="mb-8 p-4 bg-[#EFF6FF] rounded-lg border border-[#E5E7EB]">
          <h3 className="text-xs font-semibold text-[#6B7280] mb-4 uppercase tracking-wider">
            Voice Settings
          </h3>
          {isLoadingVoices ? (
            <div className="flex items-center justify-center py-6">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-[#1E40AF]"></div>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-xs text-[#6B7280] mb-2 font-medium">
                  Voice Selection
                </label>
                <select
                  value={selectedVoice}
                  onChange={(e) => onVoiceChange(e.target.value)}
                  className="w-full px-3 py-2 bg-white text-[#1F2937] border border-[#E5E7EB] rounded-md focus:outline-none focus:ring-2 focus:ring-[#1E40AF] focus:border-transparent text-sm"
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
                <span className="text-xs text-[#6B7280] font-medium">Text-to-Speech</span>
                <button
                  onClick={onToggleSpeaker}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    isSpeakerEnabled 
                      ? 'bg-[#1E40AF]' 
                      : 'bg-[#E5E7EB]'
                  }`}
                  title={isSpeakerEnabled ? 'Disable TTS' : 'Enable TTS'}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white ${
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
          <div className="mb-8 p-4 bg-[#EFF6FF] rounded-lg border border-[#E5E7EB]">
            <h3 className="text-xs font-semibold text-[#6B7280] mb-4 uppercase tracking-wider px-1">
              Applied Configuration
            </h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-[#6B7280]">Name</span>
                <span className="text-[#1F2937] font-medium">{configDetails.name || 'Custom Config'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#6B7280]">Version</span>
                <span className="text-[#1F2937]">{configDetails.version || '1.0.0'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#6B7280]">Temperature</span>
                <span className="text-[#1F2937]">{configDetails.temperature || 'Default'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#6B7280]">Max Tokens</span>
                <span className="text-[#1F2937]">{configDetails.max_tokens || 'Default'}</span>
              </div>
            </div>
          </div>
        )}
        
        {/* Active Tools */}
        {((activeTools && activeTools.length > 0) || isLoadingTools) && (
          <div className="p-4 bg-[#EFF6FF] rounded-lg border border-[#E5E7EB]">
            <h3 className="text-xs font-semibold text-[#6B7280] mb-4 uppercase tracking-wider px-1">
              Active Tools
            </h3>
            {isLoadingTools ? (
              <div className="flex items-center justify-center py-6">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-[#1E40AF]"></div>
              </div>
            ) : (
              <div className="space-y-2">
                {activeTools.map(tool => (
                  <div key={tool.name} className="flex items-center gap-3 text-sm">
                    <div className={`w-2 h-2 rounded-full ${
                      tool.enabled 
                        ? 'bg-[#16A34A]' 
                        : 'bg-[#E5E7EB]'
                    }`} />
                    <span className="text-[#1F2937]">{tool.name}</span>
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