import React, { useState, useEffect } from 'react';
import { Preset, Tool, Voice } from '../../types';
import { modelApi, voiceApi } from '../../../../services/api';
import TemplateSwitcher from '../layout/TemplateSwitcher';

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
            icon: p.icon || '🌿',
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
    <div className={`fixed left-0 top-[60px] sm:top-[72px] h-[calc(100vh-60px)] sm:h-[calc(100vh-72px)] w-full sm:w-80 transform transition-transform duration-300 z-30 ${
      isOpen ? 'translate-x-0' : '-translate-x-full'
    }`}
    style={{
      background: 'linear-gradient(135deg, rgba(220, 38, 38, 0.95) 0%, rgba(252, 211, 77, 0.95) 25%, rgba(22, 163, 74, 0.95) 50%, rgba(252, 211, 77, 0.95) 75%, rgba(220, 38, 38, 0.95) 100%)',
      backgroundSize: '400% 400%',
      animation: 'rastaWave 15s ease infinite'
    }}>
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />
      
      {/* Floating Rasta decorations */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-10 left-5 text-4xl opacity-30 animate-float" style={{ animationDelay: '0s' }}>🦁</div>
        <div className="absolute top-32 right-8 text-3xl opacity-25 animate-float" style={{ animationDelay: '2s' }}>🌿</div>
        <div className="absolute bottom-20 left-12 text-5xl opacity-20 animate-float" style={{ animationDelay: '4s' }}>☮</div>
        <div className="absolute bottom-40 right-6 text-4xl opacity-30 animate-float" style={{ animationDelay: '1s' }}>♥</div>
      </div>

      <div className="relative p-4 sm:p-6 h-full overflow-y-auto rasta-vibes-scrollbar">
        {/* Header */}
        <div className="mb-6 sm:mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 sm:gap-3">
              <div className="p-1.5 sm:p-2 bg-gradient-to-br from-red-600 to-yellow-500 rounded-xl shadow-lg shadow-yellow-500/50">
                <span className="text-xl sm:text-2xl">🦁</span>
              </div>
              <div>
                <h2 className="text-xl sm:text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-red-400 via-yellow-400 to-green-400 drop-shadow-[0_0_20px_rgba(252,211,77,0.5)]"
                    style={{ fontFamily: 'Bebas Neue, sans-serif' }}>
                  Irie Configuration
                </h2>
                <p className="text-xs text-yellow-200 hidden sm:block">One Love, One Heart</p>
              </div>
            </div>
            
            {/* Close Button */}
            <button
              onClick={onClose}
              className="p-2 rounded-lg transition-all hover:scale-110"
              style={{
                background: 'rgba(220, 38, 38, 0.3)',
                border: '1px solid rgba(220, 38, 38, 0.5)',
                color: '#DC2626',
              }}
            >
              ✖
            </button>
          </div>
        </div>

        {/* Agent Selector Dropdown */}
        <div className="mb-6">
          <h3 className="text-sm font-bold text-yellow-300 mb-3 uppercase tracking-wider drop-shadow-[0_0_10px_rgba(253,224,71,0.5)]"
              style={{ fontFamily: 'Ubuntu, sans-serif' }}>
            Select Agent 🎭
          </h3>
          <div className="relative">
            <select
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
              className="w-full px-4 py-3 bg-gradient-to-r from-green-900/80 to-yellow-900/80 text-yellow-300 border-2 border-yellow-500/50 rounded-xl focus:outline-none focus:ring-2 focus:ring-red-400 focus:border-red-400 text-sm font-medium shadow-lg shadow-green-500/30 appearance-none cursor-pointer hover:shadow-yellow-400/40 transition-all"
              style={{ fontFamily: 'Ubuntu, sans-serif' }}
            >
              {agents.map(agent => (
                <option key={agent.id} value={agent.id}>
                  {agent.icon} {agent.name}
                </option>
              ))}
            </select>
            <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
              <svg className="w-5 h-5 text-yellow-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
        </div>

        {/* Theme Selector */}
        {currentTemplate && availableTemplates && onTemplateChange && (
          <div className="mb-6">
            <h3 className="text-sm font-bold text-green-300 mb-3 uppercase tracking-wider drop-shadow-[0_0_10px_rgba(134,239,172,0.5)]"
                style={{ fontFamily: 'Ubuntu, sans-serif' }}>
              Choose Theme 🎨
            </h3>
            <TemplateSwitcher 
              currentTemplate={currentTemplate}
              availableTemplates={availableTemplates}
              onTemplateChange={onTemplateChange}
            />
          </div>
        )}

        {/* Personality Selector */}
        <div className="mb-6">
          <h3 className="text-sm font-bold text-red-300 mb-3 uppercase tracking-wider drop-shadow-[0_0_10px_rgba(252,165,165,0.5)]"
              style={{ fontFamily: 'Ubuntu, sans-serif' }}>
            Vibe Selection 🌟
          </h3>
          {isLoadingPersonalities ? (
            <div className="flex items-center justify-center py-4">
              <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-red-300"></div>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-2">
              {personalities.map(preset => (
                <button
                  key={preset.id}
                  onClick={() => onPresetLoad(preset)}
                  className={`p-3 rounded-lg transition-all ${
                    selectedPersonality === preset.personality
                      ? 'bg-gradient-to-r from-red-500 to-yellow-500 text-black scale-105 shadow-lg shadow-yellow-500/50'
                      : 'bg-green-900/60 text-yellow-300 hover:bg-green-800/70 hover:scale-102'
                  } border border-yellow-500/30`}
                  style={{ fontFamily: 'Ubuntu, sans-serif' }}
                >
                  <div className="text-xl mb-1">{preset.icon}</div>
                  <div className="text-xs font-medium">{preset.name}</div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Voice Settings */}
        <div className="mb-6 p-4 bg-gradient-to-br from-red-900/60 to-green-900/60 rounded-xl border-2 border-yellow-400/50 backdrop-blur-sm shadow-lg shadow-yellow-500/30">
          <h3 className="text-sm font-bold text-yellow-300 mb-3 uppercase tracking-wider drop-shadow-[0_0_10px_rgba(253,224,71,0.5)]"
              style={{ fontFamily: 'Ubuntu, sans-serif' }}>
            Voice Settings 🎵
          </h3>
          {isLoadingVoices ? (
            <div className="flex items-center justify-center py-4">
              <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-yellow-300"></div>
            </div>
          ) : (
            <div className="space-y-3">
              <div>
                <label className="text-xs text-green-300 block mb-1 font-semibold">Voice Selection</label>
                <select
                  value={selectedVoice}
                  onChange={(e) => onVoiceChange(e.target.value)}
                  className="w-full px-3 py-2 bg-green-900/70 text-yellow-300 border border-green-400/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-400 focus:border-red-400 text-sm shadow-inner"
                  style={{ fontFamily: 'Ubuntu, sans-serif' }}
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
                <span className="text-xs text-green-300 font-semibold">Text-to-Speech</span>
                <button
                  onClick={onToggleSpeaker}
                  className={`p-2 rounded-lg transition-all shadow-lg ${
                    isSpeakerEnabled 
                      ? 'bg-gradient-to-r from-red-500 to-yellow-500 text-black shadow-yellow-400/50 scale-110' 
                      : 'bg-green-900/70 text-green-300 hover:bg-green-800/70 shadow-green-500/30'
                  }`}
                  title={isSpeakerEnabled ? 'Disable TTS' : 'Enable TTS'}
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    {isSpeakerEnabled ? (
                      <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
                    ) : (
                      <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/>
                    )}
                  </svg>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Configuration Status */}
        {configDetails && (
          <div className="mb-6 p-4 bg-gradient-to-br from-yellow-900/60 to-red-900/60 rounded-xl border-2 border-green-400/50 backdrop-blur-sm shadow-lg shadow-green-500/30">
            <h3 className="text-sm font-bold text-yellow-300 mb-3 uppercase tracking-wider drop-shadow-[0_0_10px_rgba(253,224,71,0.5)]"
                style={{ fontFamily: 'Ubuntu, sans-serif' }}>
              Applied Configuration 🔧
            </h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-green-300 font-semibold">Name:</span>
                <span className="text-yellow-200 font-medium">{configDetails.name || 'Custom Config'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-green-300 font-semibold">Version:</span>
                <span className="text-yellow-200">{configDetails.version || '1.0.0'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-green-300 font-semibold">Temperature:</span>
                <span className="text-yellow-200">{configDetails.temperature || 'Default'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-green-300 font-semibold">Max Tokens:</span>
                <span className="text-yellow-200">{configDetails.max_tokens || 'Default'}</span>
              </div>
            </div>
          </div>
        )}
        
        {/* Active Tools */}
        {(activeTools.length > 0 || isLoadingTools) && (
          <div className="p-4 bg-gradient-to-br from-green-900/60 to-yellow-900/60 rounded-xl border-2 border-red-400/50 backdrop-blur-sm shadow-lg shadow-red-500/30">
            <h3 className="text-sm font-bold text-red-300 mb-3 uppercase tracking-wider drop-shadow-[0_0_10px_rgba(252,165,165,0.5)]"
                style={{ fontFamily: 'Ubuntu, sans-serif' }}>
              Active Tools 🛠️
            </h3>
            {isLoadingTools ? (
              <div className="flex items-center justify-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-red-300"></div>
              </div>
            ) : (
              <div className="space-y-2">
                {activeTools.map(tool => (
                  <div key={tool.name} className="flex items-center gap-2 text-sm">
                    <div className={`w-2 h-2 rounded-full ${
                      tool.enabled 
                        ? 'bg-gradient-to-r from-red-400 to-yellow-400 shadow-[0_0_8px_rgba(252,211,77,0.8)] animate-pulse' 
                        : 'bg-green-700'
                    }`} />
                    <span className="text-yellow-300 font-medium">{tool.name}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="mt-8 pt-4 border-t border-yellow-500/30">
          <p className="text-xs text-center text-yellow-300 opacity-80 mb-2"
             style={{ fontFamily: 'Ubuntu, sans-serif' }}>
            "Get up, stand up, stand up for your rights"
          </p>
          <div className="flex justify-center space-x-3 text-lg">
            <span className="positive-vibration" style={{ color: '#DC2626' }}>☮</span>
            <span className="leaf-sway" style={{ color: '#FCD34D' }}>🌿</span>
            <span className="one-love-beat" style={{ color: '#16A34A' }}>♥</span>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes rastaWave {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }
        
        @keyframes float {
          0%, 100% { transform: translateY(0) rotate(0deg); }
          50% { transform: translateY(-20px) rotate(10deg); }
        }
        
        .animate-float {
          animation: float 6s ease-in-out infinite;
        }
        
        @keyframes positive-vibration {
          0%, 100% { transform: scale(1) rotate(0deg); }
          50% { transform: scale(1.2) rotate(180deg); }
        }
        
        @keyframes leaf-sway {
          0%, 100% { transform: translateX(0) rotate(0deg); }
          33% { transform: translateX(-5px) rotate(-10deg); }
          66% { transform: translateX(5px) rotate(10deg); }
        }
        
        @keyframes one-love-beat {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.3); }
        }
        
        .positive-vibration {
          display: inline-block;
          animation: positive-vibration 3s ease-in-out infinite;
        }
        
        .leaf-sway {
          display: inline-block;
          animation: leaf-sway 4s ease-in-out infinite;
        }
        
        .one-love-beat {
          display: inline-block;
          animation: one-love-beat 1.5s ease-in-out infinite;
        }
        
        .rasta-vibes-scrollbar::-webkit-scrollbar {
          width: 8px;
        }
        
        .rasta-vibes-scrollbar::-webkit-scrollbar-track {
          background: rgba(0, 0, 0, 0.3);
          border-radius: 4px;
        }
        
        .rasta-vibes-scrollbar::-webkit-scrollbar-thumb {
          background: linear-gradient(180deg, #DC2626 0%, #FCD34D 50%, #16A34A 100%);
          border-radius: 4px;
        }
        
        .rasta-vibes-scrollbar::-webkit-scrollbar-thumb:hover {
          background: linear-gradient(180deg, #EF4444 0%, #FDE047 50%, #22C55E 100%);
        }
      `}</style>
    </div>
  );
};

export default ConfigurationPanel;