import React, { useRef, useEffect } from 'react';
import { Message } from '../../types';
import { formatTime, formatResponseTime } from '../../../../utils/formatters';

interface ChatMessagesProps {
  messages: Message[];
  isTyping?: boolean;
  isSending?: boolean;
  isModelLoaded: boolean;
  messagesEndRef?: React.RefObject<HTMLDivElement>;
}

const ChatMessages: React.FC<ChatMessagesProps> = ({
  messages,
  isTyping,
  isSending,
  isModelLoaded,
  messagesEndRef
}) => {
  const isLoading = isTyping || isSending;
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    messagesEndRef?.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping, isSending, messagesEndRef]);

  return (
    <div className="flex-1 overflow-y-auto p-6 bg-black/50 backdrop-blur-sm relative">
      {/* Offline Overlay */}
      {!isModelLoaded && (
        <div className="absolute inset-0 bg-black/95 backdrop-blur-md z-10 flex items-center justify-center">
          <div className="text-center p-8 bg-black/90 border-2 border-red-500/50 shadow-[0_0_30px_rgba(255,0,0,0.3)]">
            <div className="text-4xl mb-3 animate-pulse">⚠️</div>
            <p className="text-red-400 text-lg font-mono uppercase">SYSTEM.OFFLINE</p>
            <p className="text-cyan-400 text-sm mt-2 font-mono">{'>>> '} AWAITING NEURAL CONNECTION</p>
            <p className="text-cyan-500/60 text-xs mt-1 font-mono">INITIALIZING MATRIX PROTOCOLS...</p>
          </div>
        </div>
      )}
      
      {messages.length === 0 && (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="text-6xl mb-4 animate-pulse text-cyan-400">⚡</div>
            <p className="text-cyan-400 text-lg font-mono uppercase">MATRIX.INITIALIZED</p>
            <p className="text-purple-500 text-sm mt-2">Select a personality preset when model is ready</p>
          </div>
        </div>
      )}

      <div className="space-y-4 max-w-6xl mx-auto">
        {messages.map(message => {
          // Check if this is a personality change metadata message
          if (message.role === 'system' && (message.content || message.text || '').startsWith('personality-change:')) {
            const personalityName = (message.content || message.text || '').replace('personality-change:', '');
            return (
              <div key={message.id} className="flex justify-center py-2">
                <p className="text-sm text-white/60 italic">
                  Personality changed to {personalityName}
                </p>
              </div>
            );
          }
          
          return (
            <div
              key={message.id}
              className={`flex ${
                message.role === 'user' ? 'justify-end' : 
                message.role === 'system' ? 'justify-center' : 'justify-start'
              }`}
            >
              <div className={`max-w-4xl ${
                message.role === 'system' ? 'w-full' : ''
              }`}>
                <div className={`px-5 py-3 rounded-2xl ${
                  message.role === 'user'
                    ? 'bg-black/75 border border-yellow-600/40 text-yellow-400 shadow-lg backdrop-blur-sm'
                    : message.role === 'system'
                    ? 'bg-black/75 text-pink-400 border border-purple-600/50 backdrop-blur-sm'
                    : 'bg-black/75 text-green-400 border border-green-700/40 backdrop-blur-sm'
                }`}>
                  <div className="text-base font-medium">{message.content || message.text}</div>
                </div>
              
                {/* Metadata */}
                {message.role === 'assistant' && (
                  <div className="mt-1 px-2 text-xs text-white flex items-center gap-2 justify-start">
                    <span>{formatTime(new Date(message.timestamp))}</span>
                    
                    {message.responseTime && (
                      <>
                        <span>•</span>
                        <span>{formatResponseTime(message.responseTime)}</span>
                      </>
                    )}
                    
                    {message.tokens && (
                      <>
                        <span>•</span>
                        <span>{message.tokens} tokens</span>
                      </>
                    )}
                    
                    {message.agent && (
                      <>
                        <span>•</span>
                        <span>Agent: {message.agent}</span>
                      </>
                    )}
                    
                    {message.personality && (
                      <>
                        <span>•</span>
                        <span>Personality: {message.personality}</span>
                      </>
                    )}
                    
                    {(message.metadata?.prompt || message.metadata?.prompt_template) && (
                      <>
                        <span>•</span>
                        <span className="italic">Prompt: {(message.metadata.prompt || message.metadata.prompt_template || '').substring(0, 50)}...</span>
                      </>
                    )}
                    
                    {message.toolsUsed && message.toolsUsed.length > 0 && (
                      <>
                        <span>•</span>
                        <span>Tools: {message.toolsUsed.join(', ')}</span>
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="px-4 py-3 rounded-2xl bg-black/75 border border-purple-700/30 backdrop-blur-sm">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-pink-400 rounded-full animate-ping"></div>
                <div className="w-2 h-2 bg-pink-400 rounded-full animate-ping" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-2 h-2 bg-pink-400 rounded-full animate-ping" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
          </div>
        )}
      </div>
      <div ref={chatEndRef} />
    </div>
  );
};

export default ChatMessages;