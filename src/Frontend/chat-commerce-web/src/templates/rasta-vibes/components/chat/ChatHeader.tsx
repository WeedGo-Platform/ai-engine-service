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
    <div 
      className="border-b-2 border-yellow-500/50 px-6 py-4 shadow-[0_4px_20px_rgba(252,211,77,0.3)] backdrop-blur-sm"
      style={{
        background: 'linear-gradient(135deg, rgba(26, 26, 26, 0.95) 0%, rgba(45, 27, 0, 0.9) 50%, rgba(26, 46, 5, 0.9) 100%)',
      }}
    >
      {/* Ethiopian Flag Colors Bar */}
      <div className="absolute top-0 left-0 right-0 h-1 flex">
        <div className="flex-1" style={{ background: '#16A34A' }} />
        <div className="flex-1" style={{ background: '#FCD34D' }} />
        <div className="flex-1" style={{ background: '#DC2626' }} />
      </div>

      <div className="flex items-center justify-between">
        <div className={`flex items-center gap-4 ${isPanelOpen ? 'ml-16' : 'ml-16'}`}>
          <div className={`flex items-center gap-2 px-4 py-2 rounded-full shadow-lg transition-all duration-500 ${
            isModelLoaded 
              ? 'bg-gradient-to-r from-green-600 via-yellow-500 to-red-600 text-black shadow-[0_0_20px_rgba(252,211,77,0.5)] animate-pulse' 
              : 'bg-black/50 border-2 border-yellow-600/50 text-yellow-300'
          }`}>
            <div className={`w-2 h-2 rounded-full ${
              isModelLoaded ? 'bg-white animate-pulse' : 'bg-gray-400'
            }`}></div>
            <span className="text-sm font-bold uppercase tracking-wider">
              {isModelLoaded ? '🦁 IRIE VIBES' : '💤 RESTING'}
            </span>
          </div>
          {selectedModel && (
            <span className="text-sm text-yellow-200 bg-green-900/50 px-3 py-1 rounded-full border border-green-600/30">
              {selectedModel}
            </span>
          )}
          {selectedPersonality && (
            <span className="text-sm text-green-200 italic bg-red-900/50 px-3 py-1 rounded-full border border-red-600/30">
              🌿 {presets.find(p => p.personality === selectedPersonality)?.name || selectedPersonality}
            </span>
          )}
          {isSpeaking && (
            <span className="text-sm text-yellow-300 flex items-center gap-1 bg-black/50 px-3 py-1 rounded-full border border-yellow-600/30 animate-pulse">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
              </svg>
              🎵 Jamming...
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Floating Window Toggle */}
          <button
            onClick={toggleFloating}
            className={`p-2 rounded-xl ${windowState === 'floating' ? 'bg-yellow-500/80 hover:bg-yellow-600/80' : 'bg-green-900/50 hover:bg-green-800/50'} text-yellow-300 hover:text-yellow-400 border border-yellow-600/30 transition-all shadow-lg hover:shadow-[0_0_15px_rgba(252,211,77,0.5)]`}
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
            className="p-2 rounded-xl bg-green-900/50 hover:bg-green-800/50 text-yellow-300 hover:text-yellow-400 border border-yellow-600/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-[0_0_15px_rgba(252,211,77,0.5)]"
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
            className="p-2 rounded-xl bg-red-900/50 hover:bg-red-800/50 text-yellow-300 hover:text-red-400 border border-yellow-600/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-[0_0_15px_rgba(239,68,68,0.5)]"
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
            <div className="px-3 py-1.5 bg-gradient-to-r from-red-900/50 via-yellow-900/50 to-green-900/50 border border-yellow-400/50 rounded-xl text-xs font-mono text-yellow-200 shadow-[0_0_15px_rgba(252,211,77,0.3)]" title={`Session ID: ${sessionId}`}>
              {sessionId.slice(-8)}
            </div>
          </div>
        </div>
      </div>

      {/* Decorative Elements */}
      <div className="absolute -bottom-1 left-0 right-0 flex justify-center space-x-4 text-xs opacity-50">
        <span style={{ color: '#FCD34D' }}>♪</span>
        <span style={{ color: '#16A34A' }}>☮</span>
        <span style={{ color: '#DC2626' }}>♥</span>
        <span style={{ color: '#FCD34D' }}>🌿</span>
        <span style={{ color: '#16A34A' }}>♪</span>
      </div>

      <style>{`
        @keyframes one-love-beat {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.3); }
        }
        .one-love-beat {
          animation: one-love-beat 1.5s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
};

export default ChatHeader;