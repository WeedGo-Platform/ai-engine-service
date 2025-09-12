import React from 'react';
import { Message, Preset } from '../../types';
import CartButton from '../cart/CartButton';

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
    <div className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
      <div className="flex items-center justify-between">
        <div className={`flex items-center gap-4 ${isPanelOpen ? 'ml-16' : 'ml-16'}`}>
          <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${
            isModelLoaded 
              ? 'bg-gradient-to-r from-[#3b82f6] via-[#9333ea] to-[#ec4899] text-white' 
              : 'bg-gray-100 border border-gray-300 text-gray-600'
          }`}>
            <div className={`w-2 h-2 rounded-full ${
              isModelLoaded ? 'bg-white animate-pulse' : 'bg-gray-400'
            }`}></div>
            <span className="text-sm font-medium">
              {isModelLoaded ? 'Online' : 'Offline'}
            </span>
          </div>
          {selectedModel && (
            <span className="text-sm text-gray-600">
              {selectedModel}
            </span>
          )}
          {selectedPersonality && (
            <span className="text-sm text-gray-500 italic">
              • {presets.find(p => p.personality === selectedPersonality)?.name || selectedPersonality}
            </span>
          )}
          {isSpeaking && (
            <span className="text-sm text-green-500 flex items-center gap-1 animate-pulse">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
              </svg>
              Speaking...
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Cart Button */}
          <CartButton className="mr-2" />
          
          {/* Fullscreen Toggle */}
          <button
            onClick={onToggleFullscreen}
            className="p-2 rounded-xl bg-gray-100 hover:bg-gray-200 text-gray-600 hover:text-[#E91ED4] transition-all"
            title="Toggle fullscreen"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {isFullscreen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 8V4m0 0h4M4 4l5 5m11-5h-4m4 0v4m0 0l-5-5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5h-4m4 0v-4" />
              )}
            </svg>
          </button>

          {/* Copy Chat */}
          <button
            onClick={onCopyChat}
            disabled={messages.length === 0}
            className="p-2 rounded-xl bg-gray-100 hover:bg-gray-200 text-gray-600 hover:text-[#E91ED4] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
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
            className="p-2 rounded-xl bg-gray-100 hover:bg-gray-200 text-gray-600 hover:text-red-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            title="Clear chat and start new session"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>

          <div className="flex items-center gap-2">
            {messages.length > 0 && (
              <div className="px-2 py-1 bg-green-100 border border-green-300 rounded-lg text-xs text-green-700 font-medium">
                {messages.length} msgs
              </div>
            )}
            <div className="px-3 py-1.5 bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-xl text-xs font-mono text-purple-600" title={`Session ID: ${sessionId}`}>
              {sessionId.slice(-8)}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatHeader;