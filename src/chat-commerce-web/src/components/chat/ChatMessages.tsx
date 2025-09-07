import React, { useRef, useEffect } from 'react';
import { Message } from '../../types';
import { formatTime, formatResponseTime } from '../../utils/formatters';

interface ChatMessagesProps {
  messages: Message[];
  isSending: boolean;
  isModelLoaded: boolean;
}

const ChatMessages: React.FC<ChatMessagesProps> = ({
  messages,
  isSending,
  isModelLoaded
}) => {
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSending]);

  return (
    <div className="flex-1 overflow-y-auto p-6 bg-black/50 backdrop-blur-sm relative">
      {/* Offline Overlay */}
      {!isModelLoaded && (
        <div className="absolute inset-0 bg-white/80 backdrop-blur-sm z-10 flex items-center justify-center">
          <div className="text-center p-8 bg-white rounded-2xl border border-gray-200 shadow-xl">
            <div className="text-4xl mb-3">🔌</div>
            <p className="text-[#E91ED4] text-lg font-semibold">Model Offline</p>
            <p className="text-gray-600 text-sm mt-2">Waiting for model to be loaded...</p>
            <p className="text-gray-500 text-xs mt-1">Model must be loaded via API</p>
          </div>
        </div>
      )}
      
      {messages.length === 0 && (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="text-6xl mb-4 animate-float">🌿</div>
            <p className="text-purple-400 text-lg">Welcome to Pot Palace AI</p>
            <p className="text-purple-500 text-sm mt-2">Select a personality preset when model is ready</p>
          </div>
        </div>
      )}

      <div className="space-y-4 max-w-6xl mx-auto">
        {messages.map(message => {
          // Check if this is a personality change metadata message
          if (message.role === 'system' && message.content.startsWith('personality-change:')) {
            const personalityName = message.content.replace('personality-change:', '');
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
                  <div className="text-base font-medium">{message.content}</div>
                </div>
              
                {/* Metadata */}
                {message.role === 'assistant' && (
                  <div className="mt-1 px-2 text-xs text-white flex items-center gap-2 justify-start">
                    <span>{formatTime(message.timestamp)}</span>
                    
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
        
        {isSending && (
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