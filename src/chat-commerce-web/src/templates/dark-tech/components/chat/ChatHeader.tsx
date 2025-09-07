import React from 'react';
import { Message, Preset } from '../../types';

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
  return (
    <div className="bg-black/90 backdrop-blur-md border-b border-cyan-500/20 px-6 py-3 relative overflow-hidden">
      {/* Matrix rain background effect */}
      <div className="absolute inset-0 opacity-10">
        <div className="h-full w-full bg-gradient-to-b from-cyan-500/5 to-transparent animate-pulse"></div>
      </div>
      
      <div className="flex items-center justify-between relative z-10">
        <div className={`flex items-center gap-4 ${isPanelOpen ? 'ml-16' : 'ml-16'}`}>
          <div className={`relative group`}>
            <div className={`flex items-center gap-2 px-4 py-2 border rounded-sm transition-all duration-300 ${
              isModelLoaded 
                ? 'bg-black/50 border-cyan-400/50 text-cyan-400 shadow-[0_0_15px_rgba(0,255,255,0.3)]' 
                : 'bg-black/30 border-red-500/30 text-red-400'
            }`}>
              <div className="relative">
                <div className={`w-2 h-2 ${
                  isModelLoaded ? 'bg-cyan-400' : 'bg-red-500'
                }`}></div>
                {isModelLoaded && (
                  <div className="absolute inset-0 bg-cyan-400 rounded-full animate-ping"></div>
                )}
              </div>
              <span className="text-xs font-mono uppercase tracking-wider">
                {isModelLoaded ? '[SYSTEM.ONLINE]' : '[SYSTEM.OFFLINE]'}
              </span>
            </div>
            {/* Holographic glow */}
            {isModelLoaded && (
              <div className="absolute -inset-1 bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-500 rounded-sm opacity-20 blur-md group-hover:opacity-30 transition-opacity"></div>
            )}
          </div>
          
          {selectedModel && (
            <div className="px-3 py-1 bg-purple-900/30 border border-purple-500/30 rounded-sm">
              <span className="text-xs text-purple-300 font-mono uppercase">
                MODEL:{selectedModel}
              </span>
            </div>
          )}
          
          {selectedPersonality && (
            <div className="px-3 py-1 bg-pink-900/30 border border-pink-500/30 rounded-sm relative overflow-hidden group">
              <span className="text-xs text-pink-300 font-mono uppercase relative z-10">
                PERSONA:{presets.find(p => p.personality === selectedPersonality)?.name || selectedPersonality}
              </span>
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-pink-500/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
            </div>
          )}
          
          {isSpeaking && (
            <div className="flex items-center gap-2 px-3 py-1 bg-green-900/30 border border-green-500/30 rounded-sm">
              <div className="flex gap-1">
                <span className="w-1 h-3 bg-green-400 animate-[pulse_0.5s_ease-in-out_infinite]"></span>
                <span className="w-1 h-3 bg-green-400 animate-[pulse_0.5s_ease-in-out_infinite_0.1s]"></span>
                <span className="w-1 h-3 bg-green-400 animate-[pulse_0.5s_ease-in-out_infinite_0.2s]"></span>
              </div>
              <span className="text-xs text-green-300 font-mono uppercase animate-pulse">
                AUDIO.ACTIVE
              </span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Fullscreen Toggle - Holographic button */}
          <button
            onClick={onToggleFullscreen}
            className="p-2 bg-black/50 border border-cyan-500/30 rounded-sm text-cyan-400 hover:text-cyan-300 hover:border-cyan-400 hover:bg-cyan-900/30 hover:shadow-[0_0_10px_rgba(0,255,255,0.5)] transition-all duration-300 group"
            title="FULLSCREEN.TOGGLE"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {isFullscreen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 8V4m0 0h4M4 4l5 5m11-5h-4m4 0v4m0 0l-5-5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5h-4m4 0v-4" />
              )}
            </svg>
          </button>

          {/* Copy Chat - Terminal style */}
          <button
            onClick={onCopyChat}
            disabled={messages.length === 0}
            className="p-2 bg-black/50 border border-purple-500/30 rounded-sm text-purple-400 hover:text-purple-300 hover:border-purple-400 hover:bg-purple-900/30 hover:shadow-[0_0_10px_rgba(147,51,234,0.5)] transition-all duration-300 disabled:opacity-30 disabled:cursor-not-allowed"
            title="CLIPBOARD.COPY"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </button>

          {/* Clear Chat - Danger zone */}
          <button
            onClick={onClearSession}
            disabled={messages.length === 0}
            className="p-2 bg-black/50 border border-red-500/30 rounded-sm text-red-400 hover:text-red-300 hover:border-red-400 hover:bg-red-900/30 hover:shadow-[0_0_10px_rgba(239,68,68,0.5)] transition-all duration-300 disabled:opacity-30 disabled:cursor-not-allowed group"
            title="MEMORY.PURGE"
          >
            <svg className="w-4 h-4 group-hover:animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>

          {/* Stats display */}
          <div className="flex items-center gap-2">
            {messages.length > 0 && (
              <div className="px-3 py-1 bg-green-900/30 border border-green-500/30 rounded-sm relative overflow-hidden">
                <span className="text-xs text-green-300 font-mono uppercase relative z-10">
                  MSG:[{messages.length}]
                </span>
                <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-green-400 to-transparent animate-shimmer"></div>
              </div>
            )}
            <div className="px-3 py-1 bg-gradient-to-r from-cyan-900/30 to-blue-900/30 border border-cyan-500/30 rounded-sm relative group" title={`Session ID: ${sessionId}`}>
              <span className="text-xs font-mono text-cyan-300 uppercase tracking-wider">
                ID:{sessionId.slice(-8)}
              </span>
              {/* Glitch effect on hover */}
              <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity">
                <span className="absolute inset-0 flex items-center justify-center text-xs font-mono text-pink-400 animate-glitch1">
                  ID:{sessionId.slice(-8)}
                </span>
                <span className="absolute inset-0 flex items-center justify-center text-xs font-mono text-cyan-400 animate-glitch2">
                  ID:{sessionId.slice(-8)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <style>{`
        @keyframes matrix {
          0% { transform: translateY(0); }
          100% { transform: translateY(20px); }
        }
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        @keyframes glitch1 {
          0%, 100% { clip-path: inset(0 0 100% 0); }
          25% { clip-path: inset(0 0 50% 0); }
          50% { clip-path: inset(50% 0 0 0); }
          75% { clip-path: inset(25% 0 25% 0); }
        }
        @keyframes glitch2 {
          0%, 100% { clip-path: inset(100% 0 0 0); }
          25% { clip-path: inset(50% 0 0 0); }
          50% { clip-path: inset(0 0 50% 0); }
          75% { clip-path: inset(25% 0 25% 0); }
        }
        .animate-matrix {
          animation: matrix 2s linear infinite;
        }
        .animate-shimmer {
          animation: shimmer 3s infinite;
        }
        .animate-glitch1 {
          animation: glitch1 0.5s infinite;
        }
        .animate-glitch2 {
          animation: glitch2 0.5s infinite reverse;
        }
      `}</style>
    </div>
  );
};

export default ChatHeader;