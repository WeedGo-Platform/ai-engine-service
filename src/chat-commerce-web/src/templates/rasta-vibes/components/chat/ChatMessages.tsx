import React, { useRef, useEffect } from 'react';
import { Message } from '../../types';
import AIChatBubble from './AIChatBubble';
import UserChatBubble from './UserChatBubble';
import ChatMetadata from './ChatMetadata';
import '../../styles/scrollbar.css';
import { safeStringify } from '../../../../utils/messageParser';

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
    <div className="flex-1 overflow-y-auto relative rasta-vibes-scrollbar rasta-vibes-scrollbar-glow" style={{
      background: 'linear-gradient(135deg, rgba(26, 26, 26, 0.9) 0%, rgba(45, 27, 0, 0.8) 25%, rgba(26, 46, 5, 0.7) 50%, rgba(45, 27, 0, 0.8) 75%, rgba(26, 26, 26, 0.9) 100%)',
      backgroundSize: '400% 400%',
      animation: 'rastaWave 15s ease infinite',
      paddingTop: '20px',
      paddingBottom: '20px',
      paddingLeft: '24px',
      paddingRight: '24px'
    }}>
      {/* Floating Rasta elements background */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-10 left-10 text-6xl opacity-10 animate-float" style={{ animationDelay: '0s' }}>🦁</div>
        <div className="absolute top-32 right-20 text-5xl opacity-10 animate-float" style={{ animationDelay: '2s' }}>🌿</div>
        <div className="absolute bottom-20 left-32 text-7xl opacity-10 animate-float" style={{ animationDelay: '4s' }}>☮</div>
        <div className="absolute bottom-40 right-10 text-6xl opacity-10 animate-float" style={{ animationDelay: '6s' }}>♥</div>
        <div className="absolute top-1/2 left-1/2 text-8xl opacity-5 animate-float" style={{ animationDelay: '8s' }}>✊</div>
      </div>
      
      <style>{`
        @keyframes rastaWave {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }
        @keyframes float {
          0%, 100% { transform: translateY(0px) rotate(0deg); }
          50% { transform: translateY(-20px) rotate(10deg); }
        }
        .animate-float {
          animation: float 6s ease-in-out infinite;
        }
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(200%); }
        }
        .rasta-vibes-scrollbar::-webkit-scrollbar {
          width: 8px;
        }
        .rasta-vibes-scrollbar::-webkit-scrollbar-track {
          background: rgba(0, 0, 0, 0.3);
          border-radius: 4px;
        }
        .rasta-vibes-scrollbar::-webkit-scrollbar-thumb {
          background: linear-gradient(180deg, #DC2626 0%, #FCD34D 50%, #16A34A 100%);
          border-radius: 4px;
        }
        .rasta-vibes-scrollbar::-webkit-scrollbar-thumb:hover {
          background: linear-gradient(180deg, #EF4444 0%, #FDE047 50%, #22C55E 100%);
        }
        .rasta-vibes-scrollbar-glow::-webkit-scrollbar-thumb {
          box-shadow: 0 0 10px rgba(252, 211, 77, 0.5);
        }
      `}</style>
      
      {/* Offline Overlay */}
      {!isModelLoaded && (
        <div className="absolute inset-0 bg-gradient-to-br from-red-900/95 via-yellow-900/90 to-green-900/95 backdrop-blur-md z-10 flex items-center justify-center">
          <div className="text-center p-8 bg-gradient-to-br from-black/90 to-green-950/90 rounded-3xl border-2 border-yellow-400/50 shadow-[0_0_40px_rgba(252,211,77,0.5)]">
            <div className="text-4xl mb-3">🔌</div>
            <p className="text-yellow-300 text-lg font-bold drop-shadow-[0_0_10px_rgba(253,224,71,0.5)]">Model Offline</p>
            <p className="text-green-200 text-sm mt-2">Waiting for the Irie connection...</p>
            <p className="text-red-300 text-xs mt-1">Loading up the wisdom...</p>
          </div>
        </div>
      )}
      
      {messages.length === 0 && (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="text-6xl mb-4 animate-float">🦁</div>
            <p className="text-yellow-400 text-lg">Welcome to Irie Vibes AI</p>
            <p className="text-green-400 text-sm mt-2">One Love, One Heart, Let's Get Together</p>
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
                <p className="text-sm text-yellow-400/60 italic">
                  Vibe changed to {personalityName}
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
              {message.role === 'user' ? (
                <UserChatBubble message={message} />
              ) : message.role === 'assistant' ? (
                <div className="max-w-4xl">
                  <AIChatBubble message={message} />
                  <ChatMetadata
                    timestamp={message.timestamp}
                    responseTime={message.responseTime}
                    tokens={message.tokens}
                    agent={message.agent}
                    personality={message.personality}
                    toolsUsed={message.toolsUsed}
                  />
                </div>
              ) : (
                // System message
                <div className="max-w-4xl w-full">
                  <div className="px-5 py-3 rounded-3xl shadow-2xl transition-all duration-300 hover:scale-105 relative overflow-hidden bg-gradient-to-br from-red-500/90 via-yellow-500/80 to-green-500/70 text-white border-2 border-yellow-400/50">
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full animate-shimmer" style={{ animation: 'shimmer 3s infinite' }}></div>
                    <div className="text-base font-medium whitespace-pre-wrap break-words">
                      {safeStringify(message.content || message.text, 'No message content')}
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
        
        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="px-5 py-3 rounded-3xl shadow-2xl bg-gradient-to-br from-green-500/90 via-yellow-500/80 to-red-500/70 text-white border-2 border-yellow-400/50">
              <div className="flex items-center gap-2">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-red-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-yellow-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
                <span className="text-sm font-medium">Vibing...</span>
              </div>
            </div>
          </div>
        )}
      </div>
      
      <div ref={chatEndRef} />
      {messagesEndRef && <div ref={messagesEndRef} />}
    </div>
  );
};

export default ChatMessages;