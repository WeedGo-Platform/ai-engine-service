import React, { forwardRef } from 'react';
import { ConversationTemplate } from '../../types';
import { CONVERSATION_TEMPLATES } from '../../../../utils/constants';

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
  onToggleVoiceRecording,
  isSpeakerEnabled,
  onToggleSpeaker,
  isSpeaking,
  showTemplates,
  onToggleTemplates,
  onUseTemplate
}, ref) => {
  return (
    <div className="border-t-2 border-pink-600/50 bg-gradient-to-r from-purple-900/90 via-pink-900/80 to-purple-900/90 backdrop-blur-sm shadow-[0_-10px_30px_rgba(236,72,153,0.3)]">
      {/* Voice Transcription */}
      {(isRecording || isTranscribing || transcript) && (
        <div className="px-2 sm:px-6 py-3 border-b border-purple-700/30">
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
      <div className="p-2 sm:p-4">
        <div className="flex items-center gap-2 sm:gap-3 max-w-6xl mx-auto">
          {/* Templates Button - Document Icon */}
          <button
            onClick={onToggleTemplates}
            disabled={!isModelLoaded}
            className="p-2 sm:p-3 rounded-xl bg-gradient-to-br from-purple-700/70 to-pink-700/70 hover:from-purple-600/80 hover:to-pink-600/80 text-yellow-300 hover:text-yellow-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed relative shadow-lg hover:shadow-[0_0_20px_rgba(253,224,71,0.4)] border border-yellow-400/30"
            title="Conversation templates"
          >
            <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </button>

          {/* Voice Button - Microphone */}
          <button
            onClick={onToggleVoiceRecording}
            disabled={!isModelLoaded || isSending}
            className={`p-2 sm:p-3 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg border ${
              isRecording 
                ? 'bg-gradient-to-r from-red-600 to-red-500 text-white animate-pulse shadow-[0_0_25px_rgba(239,68,68,0.6)] border-red-400/50' 
                : 'bg-gradient-to-br from-purple-700/70 to-pink-700/70 hover:from-purple-600/80 hover:to-pink-600/80 text-cyan-300 hover:text-cyan-200 hover:shadow-[0_0_20px_rgba(6,182,212,0.4)] border-cyan-400/30'
            }`}
            title={isRecording ? "Stop recording" : "Start voice recording"}
          >
            <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
            className={`flex-1 px-3 sm:px-5 py-2 sm:py-3 bg-gradient-to-r from-purple-900/60 via-pink-900/50 to-purple-900/60 border-2 border-purple-400/40 rounded-xl text-yellow-100 placeholder-purple-300 focus:outline-none focus:ring-2 focus:ring-yellow-400/50 focus:border-yellow-400/50 transition-all shadow-inner backdrop-blur-sm font-medium text-sm sm:text-base`}
          />
          
          {/* Speaker Button */}
          <button
            onClick={onToggleSpeaker}
            className={`p-2 sm:p-3 rounded-xl transition-all shadow-lg border ${
              isSpeakerEnabled 
                ? 'bg-gradient-to-r from-green-600 to-green-500 text-white shadow-[0_0_25px_rgba(34,197,94,0.6)] border-green-400/50' 
                : 'bg-gradient-to-br from-purple-700/70 to-pink-700/70 hover:from-purple-600/80 hover:to-pink-600/80 text-orange-300 hover:text-orange-200 hover:shadow-[0_0_20px_rgba(251,146,60,0.4)] border-orange-400/30'
            } ${isSpeaking ? 'animate-pulse' : ''}`}
            title={isSpeakerEnabled ? "Disable text-to-speech" : "Enable text-to-speech"}
          >
            <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
            className="px-4 sm:px-6 py-2 sm:py-3 bg-gradient-to-r from-green-500 via-emerald-500 to-green-400 hover:from-green-400 hover:to-emerald-400 text-purple-950 font-bold rounded-xl transition-all transform hover:scale-105 active:scale-95 shadow-xl hover:shadow-[0_0_30px_rgba(34,197,94,0.5)] disabled:from-purple-700 disabled:to-purple-600 disabled:text-purple-400 disabled:cursor-not-allowed flex items-center gap-2 border-2 border-green-300/50 text-sm sm:text-base"
          >
            {isSending ? (
              <>
                <svg className="animate-spin h-3 w-3 sm:h-4 sm:w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Chatting...</span>
              </>
            ) : (
              <>
                <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                <span>Chat</span>
              </>
            )}
          </button>
        </div>

        {/* Templates Dropdown */}
        {showTemplates && (
          <div className="absolute bottom-16 sm:bottom-20 left-2 right-2 sm:left-4 sm:right-4 max-w-6xl mx-auto bg-purple-900/95 backdrop-blur-xl border border-pink-600/20 rounded-2xl shadow-2xl p-3 sm:p-4 z-50">
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
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-60 overflow-y-auto">
              {CONVERSATION_TEMPLATES.map(template => (
                <button
                  key={template.id}
                  onClick={() => onUseTemplate(template as any)}
                  className="text-left p-2 sm:p-3 bg-purple-800/50 hover:bg-purple-700/50 border border-purple-600/30 rounded-xl transition-all group"
                >
                  <div className="flex items-start gap-2">
                    <span className="text-lg">{template.icon}</span>
                    <div className="flex-1">
                      <div className="text-xs sm:text-xs font-medium text-pink-300 group-hover:text-pink-200">{template.title}</div>
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