import React, { useRef, useEffect } from 'react';

interface TranscriptEntry {
  id: string;
  speaker: 'user' | 'assistant' | 'system';
  text: string;
  timestamp: Date;
  confidence?: number;
}

interface TranscriptWindowProps {
  entries: TranscriptEntry[];
  isListening?: boolean;
  className?: string;
}

const TranscriptWindow: React.FC<TranscriptWindowProps> = ({
  entries,
  isListening = false,
  className = '',
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [entries]);

  const getSpeakerStyle = (speaker: string) => {
    switch (speaker) {
      case 'user':
        return {
          color: '#16A34A',
          icon: '🎤',
          label: 'You',
        };
      case 'assistant':
        return {
          color: '#FCD34D',
          icon: '🦁',
          label: 'Assistant',
        };
      case 'system':
        return {
          color: '#DC2626',
          icon: '📢',
          label: 'System',
        };
      default:
        return {
          color: '#666666',
          icon: '💬',
          label: 'Unknown',
        };
    }
  };

  return (
    <div 
      className={`rounded-xl overflow-hidden ${className}`}
      style={{
        background: 'rgba(26, 26, 26, 0.8)',
        border: '2px solid rgba(252, 211, 77, 0.2)',
        backdropFilter: 'blur(10px)',
      }}
    >
      {/* Header */}
      <div 
        className="px-4 py-3 flex items-center justify-between"
        style={{
          background: 'linear-gradient(90deg, rgba(220, 38, 38, 0.1), rgba(252, 211, 77, 0.1), rgba(22, 163, 74, 0.1))',
          borderBottom: '1px solid rgba(252, 211, 77, 0.2)',
        }}
      >
        <div className="flex items-center space-x-2">
          <span className="text-lg" style={{ color: '#FCD34D' }}>
            📜
          </span>
          <h3 
            className="font-semibold"
            style={{ 
              color: '#FCD34D',
              fontFamily: 'Bebas Neue, sans-serif',
            }}
          >
            Voice Transcript
          </h3>
        </div>
        
        {isListening && (
          <div className="flex items-center space-x-2">
            <div 
              className="w-2 h-2 rounded-full"
              style={{ 
                background: '#DC2626',
                animation: 'reggae-pulse 1s ease-in-out infinite',
                boxShadow: '0 0 10px #DC2626',
              }}
            />
            <span className="text-xs" style={{ color: '#DC2626' }}>
              Listening...
            </span>
          </div>
        )}
      </div>

      {/* Transcript Content */}
      <div 
        ref={scrollRef}
        className="h-64 overflow-y-auto p-4 space-y-3 rasta-vibes-scrollbar"
      >
        {entries.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-3xl mb-2 opacity-50">🎙️</div>
            <p className="text-sm" style={{ color: '#F3E7C3', opacity: 0.6 }}>
              No transcript yet. Start speaking to see your words appear here.
            </p>
          </div>
        ) : (
          entries.map((entry) => {
            const style = getSpeakerStyle(entry.speaker);
            return (
              <div 
                key={entry.id}
                className="smooth-fade-in"
                style={{
                  background: 'rgba(0, 0, 0, 0.3)',
                  border: `1px solid ${style.color}33`,
                  borderRadius: '0.5rem',
                  padding: '0.75rem',
                }}
              >
                {/* Speaker Header */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span>{style.icon}</span>
                    <span 
                      className="text-xs font-semibold"
                      style={{ color: style.color }}
                    >
                      {style.label}
                    </span>
                  </div>
                  <span 
                    className="text-xs opacity-60"
                    style={{ color: '#F3E7C3' }}
                  >
                    {entry.timestamp.toLocaleTimeString()}
                  </span>
                </div>

                {/* Transcript Text */}
                <p 
                  className="text-sm"
                  style={{ 
                    color: '#F3E7C3',
                    fontFamily: 'Ubuntu, sans-serif',
                    lineHeight: '1.5',
                  }}
                >
                  {entry.text}
                </p>

                {/* Confidence Indicator */}
                {entry.confidence !== undefined && (
                  <div className="mt-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs" style={{ color: '#FCD34D', opacity: 0.6 }}>
                        Confidence:
                      </span>
                      <div className="flex-1 h-1 bg-black/50 rounded-full overflow-hidden">
                        <div 
                          className="h-full rounded-full transition-all"
                          style={{
                            width: `${entry.confidence * 100}%`,
                            background: entry.confidence > 0.8 ? '#16A34A' : 
                                       entry.confidence > 0.5 ? '#FCD34D' : '#DC2626',
                          }}
                        />
                      </div>
                      <span className="text-xs" style={{ color: '#FCD34D', opacity: 0.6 }}>
                        {Math.round(entry.confidence * 100)}%
                      </span>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Footer */}
      <div 
        className="px-4 py-2 text-center"
        style={{
          background: 'rgba(0, 0, 0, 0.5)',
          borderTop: '1px solid rgba(252, 211, 77, 0.2)',
        }}
      >
        <p className="text-xs" style={{ color: '#FCD34D', opacity: 0.5 }}>
          Voice powered by natural vibes 🌿
        </p>
      </div>
    </div>
  );
};

export default TranscriptWindow;