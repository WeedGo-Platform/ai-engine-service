import React from 'react';
import { Message, Preset } from '../../types';
import { useFloatingChat } from '../../../../contexts/FloatingChatContext';

interface ChatHeaderProps {
  isModelLoaded: boolean;
  selectedModel: string;
  selectedPersonality: string;
  presets: Preset[];
  isSpeaking: boolean;
  isFullscreen: boolean;
  onToggleFullscreen: () => void;
  onCopyChat: () => void;
  onClearSession: () => void;
  messages: Message[];
  sessionId: string;
  isPanelOpen: boolean;
}

const ChatHeader: React.FC<ChatHeaderProps> = ({
  isModelLoaded,
  selectedModel,
  selectedPersonality,
  presets,
  isSpeaking,
  isFullscreen,
  onToggleFullscreen,
  onCopyChat,
  onClearSession,
  messages,
  sessionId,
  isPanelOpen
}) => {
  const { toggleFloating, windowState } = useFloatingChat();
  return (
    <div className="bg-gradient-to-r from-purple-900/95 via-pink-900/90 to-purple-900/95 border-b-2 border-purple-400/50 px-6 py-4 shadow-[0_4px_20px_rgba(168,85,247,0.3)] backdrop-blur-sm">
      <div className="flex items-center justify-between">
        <div className={`flex items-center gap-4 ${isPanelOpen ? 'ml-16' : 'ml-16'}`}>
          <div className={`flex items-center gap-2 px-4 py-2 rounded-full shadow-lg transition-all duration-500 ${
            isModelLoaded 
              ? 'bg-gradient-to-r from-green-500 via-emerald-500 to-green-400 text-white shadow-[0_0_20px_rgba(34,197,94,0.5)] animate-pulse' 
              : 'bg-purple-800/50 border-2 border-purple-600/50 text-purple-300'
          }`}>
            <div className={`w-2 h-2 rounded-full ${
              isModelLoaded ? 'bg-white animate-pulse' : 'bg-gray-400'
            }`}></div>
            <span className="text-sm font-bold uppercase tracking-wider">
              {isModelLoaded ? '🌿 VIBING' : '💤 SLEEPING'}
            </span>
          </div>
          {selectedModel && (
            <span className="text-sm text-purple-200 bg-purple-800/50 px-3 py-1 rounded-full border border-purple-600/30">
              {selectedModel}
            </span>
          )}
          {selectedPersonality && (
            <span className="text-sm text-pink-200 italic bg-pink-800/50 px-3 py-1 rounded-full border border-pink-600/30">
              🌿 {presets.find(p => p.personality === selectedPersonality)?.name || selectedPersonality}
            </span>
          )}
          {isSpeaking && (
            <span className="text-sm text-green-300 flex items-center gap-1 bg-green-800/50 px-3 py-1 rounded-full border border-green-600/30 animate-pulse">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
              </svg>
              🎵 Vibing...
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Floating Window Toggle */}
          <button
            onClick={toggleFloating}
            className={`p-2 rounded-xl ${windowState === 'floating' ? 'bg-yellow-500/80 hover:bg-yellow-600/80' : 'bg-purple-800/50 hover:bg-purple-700/50'} text-purple-300 hover:text-pink-400 border border-purple-600/30 transition-all shadow-lg hover:shadow-[0_0_15px_rgba(236,72,153,0.5)]`}
            title={windowState === 'floating' ? 'Dock chat window' : 'Pop out chat window'}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {windowState === 'floating' ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 8V4m0 0h4M4 4l5 5m11-5h-4m4 0v4m0 0l-5-5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5h-4m4 0v-4" />
              )}
            </svg>
          </button>

          {/* Copy Chat */}
          <button
            onClick={onCopyChat}
            disabled={messages.length === 0}
            className="p-2 rounded-xl bg-purple-800/50 hover:bg-purple-700/50 text-purple-300 hover:text-pink-400 border border-purple-600/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-[0_0_15px_rgba(236,72,153,0.5)]"
            title="Copy chat history"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </button>

          {/* Clear Chat */}
          <button
            onClick={onClearSession}
            disabled={messages.length === 0}
            className="p-2 rounded-xl bg-purple-800/50 hover:bg-red-700/50 text-purple-300 hover:text-red-400 border border-purple-600/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-[0_0_15px_rgba(239,68,68,0.5)]"
            title="Clear chat and start new session"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>

          <div className="flex items-center gap-2">
            {messages.length > 0 && (
              <div className="px-2 py-1 bg-green-800/50 border border-green-600/30 rounded-lg text-xs text-green-300 font-bold shadow-[0_0_10px_rgba(34,197,94,0.3)]">
                {messages.length} msgs
              </div>
            )}
            <div className="px-3 py-1.5 bg-gradient-to-r from-purple-800/50 to-pink-800/50 border border-purple-400/50 rounded-xl text-xs font-mono text-purple-200 shadow-[0_0_15px_rgba(168,85,247,0.3)]" title={`Session ID: ${sessionId}`}>
              {sessionId.slice(-8)}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatHeader;