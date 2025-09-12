import React, { useRef, useEffect } from 'react';
import { Message } from '../../types';
import { formatTime, formatResponseTime } from '../../../../utils/formatters';
import { safeStringify, isProductDetailsMessage } from '../../../../utils/messageParser';
import ProductDetails from '../product/ProductDetails';
import '../../styles/scrollbar.css';

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
    <div className="flex-1 overflow-y-auto bg-gradient-to-b from-slate-50 to-white relative modern-minimal-scrollbar"
         style={{ paddingTop: '20px', paddingBottom: '20px', paddingLeft: '32px', paddingRight: '32px' }}>
      {/* Offline Overlay - Minimal design */}
      {!isModelLoaded && (
        <div className="absolute inset-0 bg-white/95 backdrop-blur-xl z-10 flex items-center justify-center">
          <div className="text-center p-12 bg-white rounded-2xl shadow-[0_20px_60px_-15px_rgba(0,0,0,0.15)] border border-slate-200">
            <div className="w-16 h-16 mx-auto mb-6 bg-slate-100 rounded-full flex items-center justify-center">
              <div className="w-3 h-3 bg-slate-600 rounded-full"></div>
            </div>
            <p className="text-slate-900 text-lg font-medium">System Offline</p>
            <p className="text-slate-700 text-sm mt-3">Waiting for model initialization</p>
            <div className="mt-6 flex justify-center gap-1">
              <span className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></span>
              <span className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></span>
              <span className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></span>
            </div>
          </div>
        </div>
      )}
      
      {messages.length === 0 && (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-slate-100 to-slate-200 rounded-2xl flex items-center justify-center shadow-lg">
              <svg className="w-10 h-10 text-slate-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <p className="text-slate-900 text-xl font-medium">Start a Conversation</p>
            <p className="text-slate-700 text-sm mt-2">Select a personality to begin</p>
          </div>
        </div>
      )}

      <div className="space-y-6 max-w-4xl mx-auto">
        {messages.map(message => {
          // Check if this is a personality change metadata message
          if (message.role === 'system' && (message.content || message.text || '').startsWith('personality-change:')) {
            const personalityName = (message.content || message.text || '').replace('personality-change:', '');
            return (
              <div key={message.id} className="flex justify-center py-3">
                <div className="px-4 py-2 bg-slate-200 rounded-full">
                  <p className="text-xs text-slate-700 font-medium">
                    Switched to {personalityName}
                  </p>
                </div>
              </div>
            );
          }
          
          // Check if this is a product details message
          let parsedContent;
          try {
            parsedContent = typeof message.content === 'string' ? JSON.parse(message.content) : message.content;
          } catch {
            parsedContent = message.content;
          }
          
          if (isProductDetailsMessage(parsedContent)) {
            return (
              <div key={message.id} className="flex justify-start">
                <div className="max-w-3xl w-full">
                  <ProductDetails 
                    product={parsedContent.product}
                  />
                </div>
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
              <div className={`max-w-3xl ${
                message.role === 'system' ? 'w-full' : ''
              }`}>
                <div className={`px-6 py-4 ${
                  message.role === 'user'
                    ? 'bg-slate-800 text-white rounded-2xl rounded-br-sm shadow-md'
                    : message.role === 'system'
                    ? 'bg-gradient-to-r from-amber-50 to-orange-50 text-slate-800 rounded-xl border border-amber-200'
                    : 'bg-white text-slate-900 rounded-2xl rounded-bl-sm shadow-md border border-slate-200'
                }`}>
                  <div className="text-sm font-normal leading-relaxed whitespace-pre-wrap break-words">
                    {safeStringify(message.content || message.text, 'No message content')}
                  </div>
                </div>
              
                {/* Metadata - Clean and minimal */}
                {message.role === 'assistant' && (
                  <div className="mt-2 px-2 text-[11px] text-slate-600 flex items-center gap-2 justify-start">
                    <span className="font-medium">
                      {formatTime(new Date(message.timestamp))}
                    </span>
                    
                    {message.responseTime && (
                      <>
                        <span>•</span>
                        <span className="font-medium">
                          {formatResponseTime(message.responseTime)}
                        </span>
                      </>
                    )}
                    
                    {message.tokens && (
                      <>
                        <span>•</span>
                        <span className="font-medium">
                          {message.tokens} tokens
                        </span>
                      </>
                    )}
                    
                    {message.agent && (
                      <>
                        <span>•</span>
                        <span className="font-medium">Agent: {message.agent}</span>
                      </>
                    )}
                    
                    {message.personality && (
                      <>
                        <span>•</span>
                        <span className="font-medium">Personality: {message.personality}</span>
                      </>
                    )}
                    
                    {(message.metadata?.prompt || message.metadata?.prompt_template) && (
                      <>
                        <span>•</span>
                        <span className="italic font-medium">Prompt: {(message.metadata.prompt || message.metadata.prompt_template || '').substring(0, 50)}...</span>
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
            <div className="px-6 py-4 bg-white rounded-2xl rounded-bl-sm shadow-md border border-slate-200">
              <div className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-slate-600 rounded-full animate-[pulse_1.5s_ease-in-out_infinite]"></span>
                <span className="w-1.5 h-1.5 bg-slate-600 rounded-full animate-[pulse_1.5s_ease-in-out_infinite_0.2s]"></span>
                <span className="w-1.5 h-1.5 bg-slate-600 rounded-full animate-[pulse_1.5s_ease-in-out_infinite_0.4s]"></span>
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