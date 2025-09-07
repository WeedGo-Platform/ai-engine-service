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
    <div className="flex-1 overflow-y-auto p-6 bg-gradient-to-b from-black via-gray-950 to-black relative">
      {/* Matrix-style background pattern */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute inset-0" style={{
          backgroundImage: `repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(6,182,212,0.1) 2px, rgba(6,182,212,0.1) 4px)`,
        }}></div>
      </div>
      
      {/* Offline Overlay - Matrix style */}
      {!isModelLoaded && (
        <div className="absolute inset-0 bg-black/95 backdrop-blur-xl z-10 flex items-center justify-center">
          <div className="text-center p-8 bg-black/90 rounded-lg border border-red-500/50 shadow-[0_0_30px_rgba(239,68,68,0.3)]">
            <div className="text-4xl mb-4 animate-pulse text-red-500">⚠</div>
            <p className="text-red-500 text-lg font-mono uppercase tracking-wider">System Offline</p>
            <p className="text-red-400/70 text-sm mt-2 font-mono">Awaiting neural link...</p>
            <div className="mt-4 flex justify-center gap-1">
              <span className="w-2 h-2 bg-red-500 animate-pulse"></span>
              <span className="w-2 h-2 bg-red-500 animate-pulse" style={{animationDelay: '0.2s'}}></span>
              <span className="w-2 h-2 bg-red-500 animate-pulse" style={{animationDelay: '0.4s'}}></span>
            </div>
          </div>
        </div>
      )}
      
      {isEmpty && (
        <div className="flex items-center justify-center h-full relative z-10">
          <div className="text-center">
            <div className="text-6xl mb-4 text-cyan-500 animate-pulse filter drop-shadow-[0_0_20px_rgba(6,182,212,0.5)]">◈</div>
            <p className="text-cyan-400 text-lg font-mono uppercase tracking-wider">System Ready</p>
            <p className="text-cyan-500/60 text-sm mt-2 font-mono">Initialize communication protocol...</p>
          </div>
        </div>
      )}

      {!isEmpty && (
        <div className="space-y-4 max-w-6xl mx-auto relative z-10">
          {children}
        </div>
      )}
      
      <div ref={chatEndRef} />
    </div>
  );
};

export default TranscriptWindow;