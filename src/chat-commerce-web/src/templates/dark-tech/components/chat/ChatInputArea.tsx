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
    <div className="border-t-2 border-cyan-500/30 bg-black/95 backdrop-blur-xl shadow-[0_-10px_40px_rgba(6,182,212,0.2)]">
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
          {/* Templates Button - Terminal Icon */}
          <button
            onClick={onToggleTemplates}
            disabled={!isModelLoaded}
            className="p-3 rounded-lg bg-gray-900/80 hover:bg-cyan-900/50 text-cyan-400 hover:text-cyan-300 transition-all disabled:opacity-50 disabled:cursor-not-allowed border border-cyan-500/30 hover:border-cyan-400/50 shadow-lg hover:shadow-[0_0_20px_rgba(6,182,212,0.4)]"
            title="Command templates"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </button>

          {/* Voice Button - Mic Icon */}
          <button
            onClick={onToggleVoiceRecording}
            disabled={!isModelLoaded || isSending}
            className={`p-3 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed border ${
              isRecording 
                ? 'bg-red-900/80 text-red-400 animate-pulse shadow-[0_0_30px_rgba(239,68,68,0.6)] border-red-500/50' 
                : 'bg-gray-900/80 hover:bg-green-900/50 text-green-400 hover:text-green-300 border-green-500/30 hover:border-green-400/50 shadow-lg hover:shadow-[0_0_20px_rgba(34,197,94,0.4)]'
            }`}
            title={isRecording ? "[RECORDING]" : "[MIC]"}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
          </button>
          
          {/* Text Input - Terminal Style */}
          <input
            ref={ref}
            type="text"
            value={inputMessage}
            onChange={(e) => onInputChange(e.target.value)}
            onKeyPress={onKeyPress}
            placeholder={isModelLoaded ? "root@ai:~$ Enter command..." : "[SYSTEM OFFLINE]"}
            disabled={!isModelLoaded}
            className={`flex-1 px-5 py-3 bg-gray-950/90 border-2 border-cyan-500/30 rounded-lg text-cyan-300 placeholder-cyan-800 focus:outline-none focus:border-cyan-400/50 focus:shadow-[0_0_15px_rgba(6,182,212,0.3)] transition-all font-mono text-sm`}
          />
          
          {/* Speaker Button - Audio Icon */}
          <button
            onClick={onToggleSpeaker}
            className={`p-3 rounded-lg transition-all border ${
              isSpeakerEnabled 
                ? 'bg-green-900/80 text-green-400 shadow-[0_0_30px_rgba(34,197,94,0.6)] border-green-500/50' 
                : 'bg-gray-900/80 hover:bg-purple-900/50 text-purple-400 hover:text-purple-300 border-purple-500/30 hover:border-purple-400/50 shadow-lg hover:shadow-[0_0_20px_rgba(168,85,247,0.4)]'
            } ${isSpeaking ? 'animate-pulse' : ''}`}
            title={isSpeakerEnabled ? "[AUDIO ON]" : "[AUDIO OFF]"}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {isSpeakerEnabled ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
              )}
            </svg>
          </button>
          
          {/* Send Button - Execute Icon */}
          <button
            id="send-button"
            onClick={onSendMessage}
            disabled={!isModelLoaded || !inputMessage.trim() || isSending}
            className="px-6 py-3 bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 text-black font-bold rounded-lg transition-all transform hover:scale-105 active:scale-95 shadow-xl hover:shadow-[0_0_40px_rgba(6,182,212,0.6)] disabled:from-gray-800 disabled:to-gray-700 disabled:text-gray-500 disabled:cursor-not-allowed flex items-center gap-2 border-2 border-cyan-400/50 font-mono uppercase tracking-wider"
          >
            {isSending ? (
              <>
                <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>[PROCESSING]</span>
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                <span>[EXECUTE]</span>
              </>
            )}
          </button>
        </div>

        {/* Templates Dropdown - Terminal Style */}
        {showTemplates && (
          <div className="absolute bottom-20 left-4 right-4 max-w-6xl mx-auto bg-black/95 backdrop-blur-xl border-2 border-cyan-500/30 rounded-lg shadow-[0_0_40px_rgba(6,182,212,0.3)] p-4 z-50">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-cyan-400 uppercase tracking-widest font-mono">[COMMAND PRESETS]</h3>
              <button
                onClick={onToggleTemplates}
                className="p-1 hover:bg-gray-900 rounded transition-colors"
              >
                <svg className="w-4 h-4 text-cyan-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="grid grid-cols-2 gap-2 max-h-60 overflow-y-auto">
              {CONVERSATION_TEMPLATES.map(template => (
                <button
                  key={template.id}
                  onClick={() => onUseTemplate(template as any)}
                  className="text-left p-3 bg-gray-900/80 hover:bg-cyan-900/30 border border-cyan-500/20 hover:border-cyan-400/40 rounded-lg transition-all group hover:shadow-[0_0_15px_rgba(6,182,212,0.2)]"
                >
                  <div className="flex items-start gap-2">
                    <span className="text-lg opacity-60">{template.icon}</span>
                    <div className="flex-1">
                      <div className="text-xs font-bold text-cyan-400 group-hover:text-cyan-300 font-mono uppercase">{template.title}</div>
                      <div className="text-xs text-gray-500 mt-1 line-clamp-2 font-mono">{template.message}</div>
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