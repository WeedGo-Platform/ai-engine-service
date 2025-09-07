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
    <div className={`fixed left-0 top-[72px] h-[calc(100vh-72px)] w-80 transform transition-transform duration-300 z-30 ${
      isOpen ? 'translate-x-0' : '-translate-x-full'
    }`}
    style={{
      background: 'linear-gradient(135deg, #8B5CF6 0%, #EC4899 25%, #F59E0B 50%, #10B981 75%, #8B5CF6 100%)',
      backgroundSize: '400% 400%',
      animation: 'psychedelicGradient 15s ease infinite'
    }}>
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
      
      {/* Floating cannabis decorations */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-10 left-5 text-4xl opacity-30 animate-float" style={{ animationDelay: '0s' }}>🌿</div>
        <div className="absolute top-32 right-8 text-3xl opacity-25 animate-float" style={{ animationDelay: '2s' }}>🍃</div>
        <div className="absolute bottom-20 left-12 text-5xl opacity-20 animate-float" style={{ animationDelay: '4s' }}>🌱</div>
        <div className="absolute bottom-40 right-6 text-4xl opacity-30 animate-float" style={{ animationDelay: '1s' }}>🌿</div>
      </div>

      <div className="relative p-6 h-full overflow-y-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl shadow-lg shadow-purple-500/50">
                <span className="text-2xl">🌿</span>
              </div>
              <div>
                <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-yellow-300 via-green-300 to-pink-300 drop-shadow-[0_0_20px_rgba(236,72,153,0.5)]">
                  AI Configuration
                </h2>
                <p className="text-xs text-purple-200">Customize your experience</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 bg-purple-800/50 hover:bg-purple-700/50 rounded-lg transition-all hover:scale-110 group"
            >
              <svg className="w-5 h-5 text-pink-300 group-hover:text-yellow-300 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Agent Selector */}
        <div className="mb-6">
          <h3 className="text-sm font-bold text-yellow-300 mb-3 uppercase tracking-wider drop-shadow-[0_0_10px_rgba(253,224,71,0.5)]">
            Select Agent 🎭
          </h3>
          <div className="relative">
            <select
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
              className="w-full px-4 py-3 bg-gradient-to-r from-purple-900/80 to-pink-900/80 text-yellow-300 border-2 border-pink-500/50 rounded-xl focus:outline-none focus:ring-2 focus:ring-yellow-400 focus:border-yellow-400 text-sm font-medium shadow-lg shadow-purple-500/30 appearance-none cursor-pointer hover:shadow-yellow-400/40 transition-all"
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

        {/* Quick Presets */}
        <div className="mb-6">
          <h3 className="text-sm font-bold text-green-300 mb-3 uppercase tracking-wider drop-shadow-[0_0_10px_rgba(134,239,172,0.5)]">
            Quick Presets ✨
          </h3>
          {isLoadingPersonalities ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-yellow-300"></div>
            </div>
          ) : (
            <div className="space-y-2">
              {personalities.map(preset => (
                <button
                  key={preset.id}
                  onClick={() => onPresetLoad(preset)}
                  disabled={!isModelLoaded}
                  className={`w-full p-3 bg-gradient-to-r from-purple-800/60 to-pink-800/60 hover:from-purple-700/70 hover:to-pink-700/70 border-2 border-purple-400/50 rounded-xl transition-all group shadow-lg hover:shadow-yellow-400/30 backdrop-blur-sm ${
                    !isModelLoaded ? 'opacity-50 cursor-not-allowed' : 'hover:scale-[1.02]'
                  } ${
                    selectedPersonality === preset.personality 
                      ? 'ring-2 ring-yellow-400 border-yellow-400/50 shadow-yellow-400/40' 
                      : ''
                  }`}
                  title={isModelLoaded ? `Switch to ${preset.name}` : 'Load a model first'}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-2xl filter drop-shadow-[0_0_8px_rgba(236,72,153,0.6)]">{preset.icon}</span>
                    <div className="text-left flex-1">
                      <div className="font-bold text-yellow-300 drop-shadow-[0_0_5px_rgba(253,224,71,0.4)]">
                        {preset.name}
                      </div>
                      <div className="text-xs text-green-200">
                        {preset.description}
                      </div>
                    </div>
                    {selectedPersonality === preset.personality ? (
                      <div className="p-1 bg-gradient-to-br from-yellow-400 to-green-400 rounded-full">
                        <svg className="w-3 h-3 text-purple-900" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" />
                        </svg>
                      </div>
                    ) : (
                      <svg className="w-4 h-4 text-purple-300 group-hover:text-yellow-300 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
        <div className="mb-6 p-4 bg-gradient-to-br from-indigo-900/60 to-purple-900/60 rounded-xl border-2 border-indigo-400/50 backdrop-blur-sm shadow-lg shadow-indigo-500/30">
          <h3 className="text-sm font-bold text-cyan-300 mb-3 uppercase tracking-wider drop-shadow-[0_0_10px_rgba(103,232,249,0.5)]">
            Voice Settings 🎵
          </h3>
          {isLoadingVoices ? (
            <div className="flex items-center justify-center py-4">
              <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-cyan-300"></div>
            </div>
          ) : (
            <div className="space-y-3">
              <div>
                <label className="text-xs text-pink-300 block mb-1 font-semibold">Voice Selection</label>
                <select
                  value={selectedVoice}
                  onChange={(e) => onVoiceChange(e.target.value)}
                  className="w-full px-3 py-2 bg-purple-900/70 text-yellow-300 border border-purple-400/50 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-cyan-400 text-sm shadow-inner"
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
                      ? 'bg-gradient-to-r from-green-500 to-yellow-500 text-purple-900 shadow-green-400/50 scale-110' 
                      : 'bg-purple-900/70 text-purple-300 hover:bg-purple-800/70 shadow-purple-500/30'
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
          <div className="mb-6 p-4 bg-gradient-to-br from-pink-900/60 to-orange-900/60 rounded-xl border-2 border-pink-400/50 backdrop-blur-sm shadow-lg shadow-pink-500/30">
            <h3 className="text-sm font-bold text-yellow-300 mb-3 uppercase tracking-wider drop-shadow-[0_0_10px_rgba(253,224,71,0.5)]">
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
          <div className="p-4 bg-gradient-to-br from-green-900/60 to-blue-900/60 rounded-xl border-2 border-green-400/50 backdrop-blur-sm shadow-lg shadow-green-500/30">
            <h3 className="text-sm font-bold text-pink-300 mb-3 uppercase tracking-wider drop-shadow-[0_0_10px_rgba(244,114,182,0.5)]">
              Active Tools 🛠️
            </h3>
            {isLoadingTools ? (
              <div className="flex items-center justify-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-pink-300"></div>
              </div>
            ) : (
              <div className="space-y-2">
                {activeTools.map(tool => (
                  <div key={tool.name} className="flex items-center gap-2 text-sm">
                    <div className={`w-2 h-2 rounded-full ${
                      tool.enabled 
                        ? 'bg-gradient-to-r from-yellow-400 to-green-400 shadow-[0_0_8px_rgba(134,239,172,0.8)] animate-pulse' 
                        : 'bg-purple-700'
                    }`} />
                    <span className="text-cyan-300 font-medium">{tool.name}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <style>{`
        @keyframes psychedelicGradient {
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
      `}</style>
    </div>
  );
};

export default ConfigurationPanel;