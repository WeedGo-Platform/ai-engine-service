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
    <div className="bg-white backdrop-blur-lg border-b border-slate-200 px-8 py-3">
      <div className="flex items-center justify-between">
        <div className={`flex items-center gap-3 ${isPanelOpen ? 'ml-16' : 'ml-16'}`}>
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-md transition-all duration-300 ${
            isModelLoaded 
              ? 'bg-slate-800 text-white shadow-md' 
              : 'bg-slate-100 border border-slate-300 text-slate-600'
          }`}>
            <div className={`w-1.5 h-1.5 rounded-full transition-all duration-300 ${
              isModelLoaded ? 'bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.6)]' : 'bg-slate-400'
            }`}></div>
            <span className="text-xs font-semibold uppercase tracking-wider">
              {isModelLoaded ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          {selectedModel && (
            <span className="text-xs text-slate-700 font-medium">
              {selectedModel}
            </span>
          )}
          {selectedPersonality && (
            <div className="px-2 py-1 bg-slate-100 rounded-md border border-slate-200">
              <span className="text-xs text-slate-800 font-medium">
                {presets.find(p => p.personality === selectedPersonality)?.name || selectedPersonality}
              </span>
            </div>
          )}
          {isSpeaking && (
            <div className="flex items-center gap-1.5 px-2 py-1 bg-emerald-50 rounded-md border border-emerald-200">
              <div className="flex gap-0.5">
                <span className="w-0.5 h-3 bg-emerald-400 rounded-full animate-[wave_1s_ease-in-out_infinite]"></span>
                <span className="w-0.5 h-3 bg-emerald-400 rounded-full animate-[wave_1s_ease-in-out_infinite_0.1s]"></span>
                <span className="w-0.5 h-3 bg-emerald-400 rounded-full animate-[wave_1s_ease-in-out_infinite_0.2s]"></span>
              </div>
              <span className="text-xs text-emerald-700 font-medium">Speaking</span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-1">
          {/* Floating Window Toggle */}
          <button
            onClick={toggleFloating}
            className={`p-2 rounded-lg ${windowState === 'floating' ? 'bg-blue-500 text-white' : 'hover:bg-slate-100 text-slate-600 hover:text-slate-900'} transition-all duration-200`}
            title={windowState === 'floating' ? 'Dock chat window' : 'Pop out chat window'}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {isFullscreen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M4 8V4m0 0h4M4 4l5 5m11-5h-4m4 0v4m0 0l-5-5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5h-4m4 0v-4" />
              )}
            </svg>
          </button>

          {/* Copy Chat */}
          <button
            onClick={onCopyChat}
            disabled={messages.length === 0}
            className="p-2 rounded-lg hover:bg-slate-100 text-slate-600 hover:text-slate-900 transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed"
            title="Copy chat history"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </button>

          {/* Clear Chat */}
          <button
            onClick={onClearSession}
            disabled={messages.length === 0}
            className="p-2 rounded-lg hover:bg-slate-100 text-slate-600 hover:text-slate-900 transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed"
            title="Clear chat and start new session"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>

          {/* Divider */}
          <div className="w-px h-4 bg-slate-300 mx-1"></div>
          
          <div className="flex items-center gap-2">
            {messages.length > 0 && (
              <div className="px-2.5 py-1 bg-slate-100 rounded-md border border-slate-200">
                <span className="text-xs text-slate-700 font-medium">{messages.length}</span>
              </div>
            )}
            <div className="px-2.5 py-1 bg-slate-800 text-white rounded-md" title={`Session ID: ${sessionId}`}>
              <span className="text-xs font-mono font-medium">{sessionId.slice(-8)}</span>
            </div>
          </div>
        </div>
      </div>
      
      <style>{`
        @keyframes wave {
          0%, 100% { transform: scaleY(1); }
          50% { transform: scaleY(0.5); }
        }
      `}</style>
    </div>
  );
};

export default ChatHeader;