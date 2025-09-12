import React, { useRef, useEffect } from 'react';
import type { TranscriptWindowProps } from '../../../../core/contracts/template.contracts';

const TranscriptWindow: React.FC<TranscriptWindowProps> = ({
  children,
  isModelLoaded,
  isEmpty = false,
  messagesEndRef
}) => {
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    messagesEndRef?.current?.scrollIntoView({ behavior: 'smooth' });
  }, [children, messagesEndRef]);

  return (
    <div className="flex-1 overflow-y-auto p-8 bg-gradient-to-b from-gray-50 to-white relative">
      {/* Offline Overlay - Minimal design */}
      {!isModelLoaded && (
        <div className="absolute inset-0 bg-white/95 backdrop-blur-xl z-10 flex items-center justify-center">
          <div className="text-center p-12 bg-white rounded-2xl shadow-[0_20px_60px_-15px_rgba(0,0,0,0.1)] border border-gray-100">
            <div className="w-16 h-16 mx-auto mb-6 bg-gray-100 rounded-full flex items-center justify-center">
              <div className="w-3 h-3 bg-gray-400 rounded-full"></div>
            </div>
            <p className="text-gray-900 text-lg font-light">System Offline</p>
            <p className="text-gray-500 text-sm mt-3 font-light">Waiting for model initialization</p>
            <div className="mt-6 flex justify-center gap-1">
              <span className="w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></span>
              <span className="w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></span>
              <span className="w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></span>
            </div>
          </div>
        </div>
      )}
      
      {isEmpty && (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="w-20 h-20 mx-auto mb-6 bg-gray-100 rounded-full flex items-center justify-center">
              <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <p className="text-gray-900 text-lg font-light">Start a conversation</p>
            <p className="text-gray-500 text-sm mt-2 font-light">Type a message to begin</p>
          </div>
        </div>
      )}

      {!isEmpty && (
        <div className="space-y-4 max-w-4xl mx-auto">
          {children}
        </div>
      )}
      
      <div ref={chatEndRef} />
    </div>
  );
};

export default TranscriptWindow;