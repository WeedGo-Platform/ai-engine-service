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
    <div className="flex-1 overflow-y-auto p-6 relative" style={{
      background: 'linear-gradient(135deg, rgba(76, 29, 149, 0.9) 0%, rgba(91, 33, 182, 0.8) 25%, rgba(124, 58, 237, 0.7) 50%, rgba(139, 92, 246, 0.6) 75%, rgba(76, 29, 149, 0.9) 100%)',
      backgroundSize: '400% 400%',
      animation: 'psychedelicGradient 15s ease infinite'
    }}>
      {/* Floating cannabis leaves background */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-10 left-10 text-6xl opacity-10 animate-float" style={{ animationDelay: '0s' }}>🌿</div>
        <div className="absolute top-32 right-20 text-5xl opacity-10 animate-float" style={{ animationDelay: '2s' }}>🍃</div>
        <div className="absolute bottom-20 left-32 text-7xl opacity-10 animate-float" style={{ animationDelay: '4s' }}>🌿</div>
        <div className="absolute bottom-40 right-10 text-6xl opacity-10 animate-float" style={{ animationDelay: '6s' }}>🍃</div>
        <div className="absolute top-1/2 left-1/2 text-8xl opacity-5 animate-float" style={{ animationDelay: '8s' }}>🌿</div>
      </div>
      
      <style>{`
        @keyframes psychedelicGradient {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }
        @keyframes float {
          0%, 100% { transform: translateY(0) rotate(0deg); }
          33% { transform: translateY(-20px) rotate(5deg); }
          66% { transform: translateY(20px) rotate(-5deg); }
        }
        .animate-float {
          animation: float 6s ease-in-out infinite;
        }
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(200%); }
        }
      `}</style>
      {/* Offline Overlay */}
      {!isModelLoaded && (
        <div className="absolute inset-0 bg-gradient-to-br from-purple-900/95 via-pink-900/90 to-purple-900/95 backdrop-blur-md z-10 flex items-center justify-center">
          <div className="text-center p-8 bg-gradient-to-br from-purple-800/90 to-pink-800/90 rounded-3xl border-2 border-purple-400/50 shadow-[0_0_40px_rgba(168,85,247,0.5)]">
            <div className="text-4xl mb-3">🔌</div>
            <p className="text-yellow-300 text-lg font-bold drop-shadow-[0_0_10px_rgba(253,224,71,0.5)]">Model Offline</p>
            <p className="text-purple-200 text-sm mt-2">Waiting for the cosmic connection...</p>
            <p className="text-purple-300 text-xs mt-1">Rolling up the neural networks...</p>
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
                <div className={`px-5 py-3 rounded-3xl shadow-2xl transition-all duration-300 hover:scale-105 relative overflow-hidden ${
                  message.role === 'user'
                    ? 'bg-gradient-to-br from-yellow-500/90 via-amber-500/80 to-orange-500/70 text-white border-2 border-yellow-400/50'
                    : message.role === 'system'
                    ? 'bg-gradient-to-br from-pink-500/90 via-purple-500/80 to-indigo-500/70 text-white border-2 border-pink-400/50'
                    : 'bg-gradient-to-br from-green-500/90 via-emerald-500/80 to-teal-500/70 text-white border-2 border-green-400/50'
                }`}>
                  {/* Shimmer effect overlay */}
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full animate-shimmer" style={{ animation: 'shimmer 3s infinite' }}></div>
                  <div className="text-base font-medium">{message.content || message.text}</div>
                </div>
              
                {/* Metadata with psychedelic glow */}
                {message.role === 'assistant' && (
                  <div className="mt-1 px-2 text-xs text-purple-200 flex items-center gap-2 justify-start drop-shadow-[0_0_8px_rgba(168,85,247,0.5)]">
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
            <div className="px-4 py-3 rounded-3xl bg-gradient-to-r from-purple-600/80 via-pink-600/70 to-purple-600/80 border-2 border-purple-400/50 shadow-xl animate-pulse">
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