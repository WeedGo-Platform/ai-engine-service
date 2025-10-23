import React, { forwardRef } from 'react';
import { ConversationTemplate } from '../../types';
import { CONVERSATION_TEMPLATES } from '../../utils/constants';

interface ChatInputAreaProps {
  inputMessage: string;
  onInputChange: (value: string) => void;
  onSendMessage: () => void;
  onKeyPress: (e: React.KeyboardEvent) => void;
  isModelLoaded: boolean;
  isSending: boolean;
  isRecording: boolean;
  isTranscribing: boolean;
  transcript: string;
  micMode?: 'off' | 'wake' | 'active'; // New prop for mic mode
  onToggleVoiceRecording: () => void;
  isSpeakerEnabled: boolean;
  onToggleSpeaker: () => void;
  isSpeaking: boolean;
  showTemplates: boolean;
  onToggleTemplates: () => void;
  onUseTemplate: (template: ConversationTemplate) => void;
}

const ChatInputArea = forwardRef<HTMLInputElement, ChatInputAreaProps>(({  
  inputMessage,
  onInputChange,
  onSendMessage,
  onKeyPress,
  isModelLoaded,
  isSending,
  isRecording,
  isTranscribing,
  transcript,
  micMode = 'off',
  onToggleVoiceRecording,
  isSpeakerEnabled,
  onToggleSpeaker,
  isSpeaking,
  showTemplates,
  onToggleTemplates,
  onUseTemplate
}, ref) => {
  return (
    <div className="border-t border-pink-600/20 bg-purple-900/80 backdrop-blur-sm">
      {/* Voice Transcription */}
      {(isRecording || isTranscribing || transcript) && (
        <div className="px-6 py-3 border-b border-purple-700/30">
          <div className="flex items-center gap-3">
            {isRecording && (
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                <span className="text-sm font-medium text-red-400">Recording...</span>
              </div>
            )}
            {isTranscribing && (
              <div className="flex items-center gap-2">
                <svg className="animate-spin h-4 w-4 text-pink-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span className="text-sm font-medium text-pink-400">Transcribing...</span>
              </div>
            )}
            {transcript && !isRecording && !isTranscribing && (
              <div className="flex-1 px-4 py-2 bg-purple-800/50 rounded-xl border border-purple-600/30">
                <p className="text-sm text-purple-200">
                  <span className="font-medium text-pink-400">Transcript:</span> {transcript}
                </p>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Input Controls */}
      <div className="p-4">
        <div className="flex items-center gap-3 max-w-6xl mx-auto">
          {/* Templates Button */}
          <button
            onClick={onToggleTemplates}
            disabled={!isModelLoaded}
            className="p-3 rounded-xl bg-purple-800/50 hover:bg-purple-700/50 text-purple-300 hover:text-pink-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed relative"
            title="Conversation templates"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </button>

          {/* Voice Button */}
          <button
            onClick={onToggleVoiceRecording}
            disabled={!isModelLoaded || isSending}
            className={`p-3 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed ${
              micMode === 'active' || isRecording
                ? 'bg-gradient-to-r from-red-600 to-red-500 text-white animate-pulse shadow-lg' 
                : micMode === 'wake'
                ? 'bg-gradient-to-r from-amber-600 to-amber-500 text-white shadow-lg'
                : 'bg-purple-800/50 hover:bg-purple-700/50 text-purple-300 hover:text-pink-400'
            }`}
            title={
              micMode === 'active' ? 'Stop recording' 
              : micMode === 'wake' ? 'Wake word mode (click for active)' 
              : 'Start wake word mode'
            }
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
          </button>
          
          {/* Text Input */}
          <input
            ref={ref}
            type="text"
            value={inputMessage}
            onChange={(e) => onInputChange(e.target.value)}
            onKeyPress={onKeyPress}
            placeholder={isModelLoaded ? "Type your question here... (Cmd+K to focus)" : "Load a model to start chatting"}
            disabled={!isModelLoaded}
            className={`flex-1 px-5 py-3 bg-purple-900/50 border border-purple-600/30 rounded-xl text-purple-100 placeholder-purple-500 focus:outline-none focus:ring-2 focus:ring-pink-500/50 focus:border-transparent transition-all`}
          />
          
          {/* Speaker Button */}
          <button
            onClick={onToggleSpeaker}
            className={`p-3 rounded-xl transition-all ${
              isSpeakerEnabled 
                ? 'bg-gradient-to-r from-green-600 to-green-500 text-white shadow-lg' 
                : 'bg-purple-800/50 hover:bg-purple-700/50 text-purple-300 hover:text-pink-400'
            } ${isSpeaking ? 'animate-pulse' : ''}`}
            title={isSpeakerEnabled ? "Disable text-to-speech" : "Enable text-to-speech"}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {isSpeakerEnabled ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
              )}
            </svg>
          </button>
          
          {/* Chat Button */}
          <button
            id="send-button"
            onClick={onSendMessage}
            disabled={!isModelLoaded || !inputMessage.trim() || isSending}
            className="px-6 py-3 bg-gradient-to-r from-pink-600 to-pink-500 hover:from-pink-500 hover:to-pink-400 text-purple-950 font-bold rounded-xl transition-all transform hover:scale-105 active:scale-95 shadow-lg disabled:from-purple-700 disabled:to-purple-600 disabled:text-purple-400 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isSending ? (
              <>
                <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Chatting...</span>
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                <span>Chat</span>
              </>
            )}
          </button>
        </div>

        {/* Templates Dropdown */}
        {showTemplates && (
          <div className="absolute bottom-20 left-4 right-4 max-w-6xl mx-auto bg-purple-900/95 backdrop-blur-xl border border-pink-600/20 rounded-2xl shadow-2xl p-4 z-50">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-pink-400 uppercase tracking-wider">Quick Questions</h3>
              <button
                onClick={onToggleTemplates}
                className="p-1 hover:bg-purple-800 rounded-lg transition-colors"
              >
                <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="grid grid-cols-2 gap-2 max-h-60 overflow-y-auto">
              {CONVERSATION_TEMPLATES.map(template => (
                <button
                  key={template.id}
                  onClick={() => onUseTemplate(template)}
                  className="text-left p-3 bg-purple-800/50 hover:bg-purple-700/50 border border-purple-600/30 rounded-xl transition-all group"
                >
                  <div className="flex items-start gap-2">
                    <span className="text-lg">{template.icon}</span>
                    <div className="flex-1">
                      <div className="text-xs font-medium text-pink-300 group-hover:text-pink-200">{template.title}</div>
                      <div className="text-xs text-purple-400 mt-1 line-clamp-2">{template.message}</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
});

ChatInputArea.displayName = 'ChatInputArea';

export default ChatInputArea;