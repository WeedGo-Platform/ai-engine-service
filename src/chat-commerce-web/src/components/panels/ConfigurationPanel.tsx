import React from 'react';
import { Preset, Tool, Voice } from '../../types';

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
  presets,
  selectedPersonality,
  isModelLoaded,
  onPresetLoad,
  configDetails,
  availableVoices,
  selectedVoice,
  onVoiceChange,
  isSpeakerEnabled,
  onToggleSpeaker,
  activeTools
}) => {
  return (
    <div className={`fixed left-0 top-[72px] h-[calc(100vh-72px)] w-80 bg-white shadow-2xl border-r border-gray-200 transform transition-transform duration-300 z-30 ${
      isOpen ? 'translate-x-0' : '-translate-x-full'
    }`}>
      <div className="p-6 h-full overflow-y-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div>
                <h2 className="text-2xl font-bold bg-gradient-to-r from-[#3b82f6] via-[#9333ea] to-[#ec4899] bg-clip-text text-transparent">
                  AI Configuration
                </h2>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Quick Presets */}
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-[#E91ED4] mb-3 uppercase tracking-wider">Quick Presets</h3>
          <div className="space-y-2">
            {presets.map(preset => (
              <button
                key={preset.id}
                onClick={() => onPresetLoad(preset)}
                disabled={!isModelLoaded}
                className={`w-full p-3 bg-gradient-to-r from-purple-50 to-pink-50 hover:from-purple-100 hover:to-pink-100 border border-purple-200 rounded-xl transition-all group shadow-sm hover:shadow-md ${
                  !isModelLoaded ? 'opacity-50 cursor-not-allowed' : ''
                } ${
                  selectedPersonality === preset.personality ? 'ring-2 ring-[#E91ED4] bg-gradient-to-r from-purple-100 to-pink-100' : ''
                }`}
                title={isModelLoaded ? `Switch to ${preset.name}` : 'Load a model first'}
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{preset.icon}</span>
                  <div className="text-left flex-1">
                    <div className="font-medium text-gray-800">{preset.name}</div>
                    <div className="text-xs text-gray-600">{preset.description}</div>
                  </div>
                  {selectedPersonality === preset.personality ? (
                    <svg className="w-4 h-4 text-[#E91ED4]" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" />
                    </svg>
                  ) : (
                    <svg className="w-4 h-4 text-purple-400 group-hover:text-[#E91ED4] transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                    </svg>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Configuration Status */}
        {configDetails && (
          <div className="mt-6 p-4 bg-gradient-to-br from-purple-900/40 to-pink-900/40 rounded-xl border border-pink-600/20">
            <h3 className="text-sm font-semibold text-pink-400 mb-3 uppercase tracking-wider">Applied Configuration</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-purple-400">Name:</span>
                <span className="text-purple-200 font-medium">{configDetails.name || 'Custom Config'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-purple-400">Version:</span>
                <span className="text-purple-200">{configDetails.version || '1.0.0'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-purple-400">Temperature:</span>
                <span className="text-purple-200">{configDetails.temperature || 'Default'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-purple-400">Max Tokens:</span>
                <span className="text-purple-200">{configDetails.max_tokens || 'Default'}</span>
              </div>
            </div>
          </div>
        )}
        
        {/* Voice Settings */}
        <div className="mt-6 p-4 bg-gradient-to-br from-indigo-900/40 to-purple-900/40 rounded-xl border border-purple-600/20">
          <h3 className="text-sm font-semibold text-purple-400 mb-3 uppercase tracking-wider">Voice Settings</h3>
          <div className="space-y-3">
            <div>
              <label className="text-xs text-purple-400 block mb-1">Voice Selection</label>
              <select
                value={selectedVoice}
                onChange={(e) => onVoiceChange(e.target.value)}
                className="w-full px-3 py-2 bg-purple-900/50 text-purple-200 border border-purple-600/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm"
              >
                <option value="">Default Voice</option>
                {availableVoices.map(voice => (
                  <option key={voice.id} value={voice.id}>
                    {voice.name} {voice.language ? `(${voice.language})` : ''} {voice.gender ? `- ${voice.gender}` : ''}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-purple-400">Text-to-Speech</span>
              <button
                onClick={onToggleSpeaker}
                className={`p-1.5 rounded-lg transition-colors ${
                  isSpeakerEnabled 
                    ? 'bg-purple-600 text-white' 
                    : 'bg-purple-900/50 text-purple-400 hover:bg-purple-800/50'
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
        </div>
        
        {/* Active Tools */}
        {activeTools.length > 0 && (
          <div className="mt-6 p-4 bg-purple-900/30 rounded-xl">
            <h3 className="text-sm font-semibold text-pink-400 mb-3 uppercase tracking-wider">Active Tools</h3>
            <div className="space-y-2">
              {activeTools.map(tool => (
                <div key={tool.name} className="flex items-center gap-2 text-sm">
                  <div className={`w-2 h-2 rounded-full ${
                    tool.enabled ? 'bg-purple-400 animate-pulse' : 'bg-purple-700'
                  }`} />
                  <span className="text-purple-300">{tool.name}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ConfigurationPanel;