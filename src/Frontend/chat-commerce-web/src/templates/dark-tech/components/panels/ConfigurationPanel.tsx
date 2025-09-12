import React, { useState, useEffect } from 'react';
import { Preset, Tool, Voice } from '../../types';
import { modelApi, voiceApi } from '../../../../services/api';
import TemplateSwitcher from '../layout/TemplateSwitcher';
import { Product } from '../../../../services/productSearch';
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
  activeTools: propTools,
  currentTemplate,
  availableTemplates,
  onTemplateChange
}) => {
  const [selectedAgent, setSelectedAgent] = useState<string>('budtender');
  const [personalities, setPersonalities] = useState<Preset[]>(propPresets);
  const [voices, setVoices] = useState<Voice[]>(propVoices);
  const [activeTools, setActiveTools] = useState<Tool[]>(propTools);
  const [isLoadingPersonalities, setIsLoadingPersonalities] = useState(false);
  const [isLoadingVoices, setIsLoadingVoices] = useState(false);
  const [isLoadingTools, setIsLoadingTools] = useState(false);
  
  // Product search state
  const [searchResults, setSearchResults] = useState<Product[]>([]);

  const agents = [
    { id: 'medical_advisor', name: 'MEDICAL_ADVISOR', icon: '⚕️' },
    { id: 'budtender', name: 'BUDTENDER', icon: '🌿' },
    { id: 'cannabis_sommelier', name: 'CANNABIS_SOMMELIER', icon: '🍷' }
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
            icon: p.icon || '💻',
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
    <div className={`fixed left-0 top-[60px] sm:top-[72px] h-[calc(100vh-60px)] sm:h-[calc(100vh-72px)] w-full sm:w-80 bg-black border-r border-cyan-500/30 transform transition-transform duration-300 z-30 ${
      isOpen ? 'translate-x-0' : '-translate-x-full'
    }`}
    style={{
      boxShadow: isOpen ? '0 0 40px rgba(0, 255, 255, 0.3)' : 'none'
    }}>
      {/* Matrix rain effect */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none opacity-10">
        <div className="matrix-rain"></div>
      </div>

      <div className="relative p-4 sm:p-6 h-full overflow-y-auto">
        {/* Header */}
        <div className="mb-6 sm:mb-8">
          <div>
            <h2 className="text-lg sm:text-2xl font-mono font-bold text-cyan-400 uppercase tracking-wider" 
                style={{ textShadow: '0 0 20px rgba(0, 255, 255, 0.8)' }}>
              [SYSTEM_CONFIG]
            </h2>
            <p className="text-xs text-green-400/80 mt-1 font-mono hidden sm:block">// Initialize AI parameters</p>
          </div>
        </div>

        {/* Enhanced Product Search Filter */}
        <div className="mb-8">
          <EnhancedProductFilter 
            onResultsChange={(results) => {
              setSearchResults(results);
              if (results.length > 0 && results.length <= 5) {
                console.log('Product search results:', results);
              }
            }}
            className=""
          />
        </div>

        {/* Agent Selector */}
        <div className="mb-6">
          <h3 className="text-xs font-mono font-bold text-green-400 mb-3 uppercase tracking-widest"
              style={{ textShadow: '0 0 10px rgba(74, 222, 128, 0.6)' }}>
            [AGENT_SELECT]
          </h3>
          <div className="relative">
            <select
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
              className="w-full px-4 py-3 bg-gray-900/80 text-cyan-300 border border-cyan-500/50 rounded focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-cyan-400 text-sm font-mono appearance-none cursor-pointer hover:border-cyan-400/70 transition-all"
              style={{ 
                boxShadow: '0 0 15px rgba(0, 255, 255, 0.2), inset 0 0 15px rgba(0, 255, 255, 0.05)'
              }}
            >
              {agents.map(agent => (
                <option key={agent.id} value={agent.id}>
                  {agent.icon} {agent.name}
                </option>
              ))}
            </select>
            <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
              <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
        </div>

        {/* Theme Selector */}
        {currentTemplate && availableTemplates && onTemplateChange && (
          <div className="mb-6">
            <h3 className="text-xs font-mono font-bold text-green-400 mb-3 uppercase tracking-widest"
                style={{ textShadow: '0 0 10px rgba(74, 222, 128, 0.6)' }}>
              [THEME_SELECT]
            </h3>
            <TemplateSwitcher 
              currentTemplate={currentTemplate}
              availableTemplates={availableTemplates}
              onTemplateChange={onTemplateChange}
            />
          </div>
        )}

        {/* Voice Settings */}
        <div className="mb-6 p-4 bg-gray-900/60 border border-cyan-500/30 rounded"
             style={{ boxShadow: '0 0 20px rgba(0, 255, 255, 0.1), inset 0 0 20px rgba(0, 255, 255, 0.05)' }}>
          <h3 className="text-xs font-mono font-bold text-cyan-400 mb-3 uppercase tracking-widest"
              style={{ textShadow: '0 0 10px rgba(0, 255, 255, 0.6)' }}>
            [AUDIO_INTERFACE]
          </h3>
          {isLoadingVoices ? (
            <div className="flex items-center justify-center py-4">
              <div className="relative">
                <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-green-400"></div>
                <div className="absolute inset-0 animate-ping rounded-full h-6 w-6 border border-green-400/30"></div>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <div>
                <label className="text-xs text-green-400/80 block mb-1 font-mono uppercase">Voice_Module</label>
                <select
                  value={selectedVoice}
                  onChange={(e) => onVoiceChange(e.target.value)}
                  className="w-full px-3 py-2 bg-black/70 text-cyan-300 border border-green-500/30 rounded focus:outline-none focus:ring-1 focus:ring-cyan-400 focus:border-cyan-400 text-sm font-mono"
                  style={{ boxShadow: 'inset 0 0 10px rgba(0, 255, 255, 0.1)' }}
                >
                  <option value="">DEFAULT_VOICE</option>
                  {Array.isArray(voices) && voices.map(voice => (
                    <option key={voice.id} value={voice.id}>
                      {voice.name} {voice.language ? `[${voice.language}]` : ''} {voice.gender ? `:: ${voice.gender}` : ''}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-green-400/80 font-mono uppercase">TTS_ENGINE</span>
                <button
                  onClick={onToggleSpeaker}
                  className={`relative w-12 h-6 rounded-full transition-all ${
                    isSpeakerEnabled 
                      ? 'bg-cyan-500/30 border border-cyan-400' 
                      : 'bg-gray-800 border border-green-500/30'
                  }`}
                  style={{ 
                    boxShadow: isSpeakerEnabled 
                      ? '0 0 15px rgba(0, 255, 255, 0.5), inset 0 0 10px rgba(0, 255, 255, 0.3)' 
                      : 'inset 0 0 5px rgba(0, 0, 0, 0.5)'
                  }}
                  title={isSpeakerEnabled ? 'Disable TTS' : 'Enable TTS'}
                >
                  <div className={`absolute top-1 transition-transform ${
                    isSpeakerEnabled ? 'translate-x-7' : 'translate-x-1'
                  }`}>
                    <div className={`w-4 h-4 rounded-full ${
                      isSpeakerEnabled 
                        ? 'bg-cyan-400 shadow-[0_0_10px_rgba(0,255,255,0.8)]' 
                        : 'bg-green-500/50'
                    }`} />
                  </div>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Configuration Status */}
        {configDetails && (
          <div className="mb-6 p-4 bg-gray-900/60 border border-green-500/30 rounded"
               style={{ boxShadow: '0 0 20px rgba(74, 222, 128, 0.1), inset 0 0 20px rgba(74, 222, 128, 0.05)' }}>
            <h3 className="text-xs font-mono font-bold text-green-400 mb-3 uppercase tracking-widest"
                style={{ textShadow: '0 0 10px rgba(74, 222, 128, 0.6)' }}>
              [CONFIG_STATUS]
            </h3>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-green-400/60">NAME:</span>
                <span className="text-cyan-300">{configDetails.name || 'CUSTOM_CONFIG'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-green-400/60">VERSION:</span>
                <span className="text-cyan-300">{configDetails.version || 'v1.0.0'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-green-400/60">TEMP:</span>
                <span className="text-cyan-300">{configDetails.temperature || 'DEFAULT'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-green-400/60">MAX_TOKENS:</span>
                <span className="text-cyan-300">{configDetails.max_tokens || 'DEFAULT'}</span>
              </div>
            </div>
          </div>
        )}
        
        {/* Active Tools */}
        {(activeTools.length > 0 || isLoadingTools) && (
          <div className="p-4 bg-gray-900/60 border border-cyan-500/30 rounded"
               style={{ boxShadow: '0 0 20px rgba(0, 255, 255, 0.1), inset 0 0 20px rgba(0, 255, 255, 0.05)' }}>
            <h3 className="text-xs font-mono font-bold text-cyan-400 mb-3 uppercase tracking-widest"
                style={{ textShadow: '0 0 10px rgba(0, 255, 255, 0.6)' }}>
              [ACTIVE_MODULES]
            </h3>
            {isLoadingTools ? (
              <div className="flex items-center justify-center py-4">
                <div className="relative">
                  <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-cyan-400"></div>
                  <div className="absolute inset-0 animate-ping rounded-full h-6 w-6 border border-cyan-400/30"></div>
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                {activeTools.map(tool => (
                  <div key={tool.name} className="flex items-center gap-2 text-xs font-mono">
                    <div className={`w-2 h-2 ${
                      tool.enabled 
                        ? 'bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.8)] animate-pulse' 
                        : 'bg-red-500/50'
                    }`} />
                    <span className={tool.enabled ? 'text-green-400' : 'text-red-400/60'}>
                      {tool.name.toUpperCase().replace(/ /g, '_')}
                    </span>
                    {tool.enabled && (
                      <span className="text-cyan-400/50 ml-auto">[ONLINE]</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <style>{`
        @keyframes matrix-fall {
          0% {
            transform: translateY(-100%);
            opacity: 0;
          }
          10% {
            opacity: 1;
          }
          90% {
            opacity: 1;
          }
          100% {
            transform: translateY(100vh);
            opacity: 0;
          }
        }
        
        .matrix-rain::before {
          content: '101010110101011010101101010110101011010101101010110101011010101';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          font-family: monospace;
          font-size: 10px;
          color: #00ff00;
          word-break: break-all;
          animation: matrix-fall 10s linear infinite;
        }
      `}</style>
    </div>
  );
};

export default ConfigurationPanel;