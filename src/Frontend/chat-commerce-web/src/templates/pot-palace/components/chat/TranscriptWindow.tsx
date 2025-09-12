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
      
      {isEmpty && (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="text-6xl mb-4 animate-float">🌿</div>
            <p className="text-purple-400 text-lg">Welcome to Pot Palace AI</p>
            <p className="text-purple-500 text-sm mt-2">Select a personality preset when model is ready</p>
          </div>
        </div>
      )}

      {!isEmpty && (
        <div className="space-y-4 max-w-6xl mx-auto">
          {children}
        </div>
      )}
      
      <div ref={chatEndRef} />
    </div>
  );
};

export default TranscriptWindow;