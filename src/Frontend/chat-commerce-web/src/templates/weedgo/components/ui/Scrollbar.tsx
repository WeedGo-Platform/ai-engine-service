import React, { useEffect, useRef } from 'react';

interface ScrollbarProps {
  children: React.ReactNode;
  className?: string;
  maxHeight?: string;
}

const Scrollbar: React.FC<ScrollbarProps> = ({ 
  children, 
  className = '',
  maxHeight = '100%'
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Add weedgo specific scrollbar styles
    if (scrollRef.current) {
      scrollRef.current.style.setProperty('--scrollbar-thumb', '#1E40AF');
      scrollRef.current.style.setProperty('--scrollbar-track', '#F3F4F6');
    }
  }, []);

  return (
    <div 
      ref={scrollRef}
      className={`weedgo-scrollbar overflow-y-auto ${className}`}
      style={{ maxHeight }}
    >
      {children}
      <style jsx>{`
        .weedgo-scrollbar::-webkit-scrollbar {
          width: 8px;
          height: 8px;
        }
        
        .weedgo-scrollbar::-webkit-scrollbar-track {
          background: #F3F4F6;
          border-radius: 4px;
        }
        
        .weedgo-scrollbar::-webkit-scrollbar-thumb {
          background: #1E40AF;
          border-radius: 4px;
        }
        
        .weedgo-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #1E3A8A;
        }
        
        .weedgo-scrollbar::-webkit-scrollbar-thumb:active {
          background: #1E3A8A;
        }
        
        /* Firefox */
        .weedgo-scrollbar {
          scrollbar-width: thin;
          scrollbar-color: #1E40AF #F3F4F6;
        }
        
        /* Dark mode support */
        @media (prefers-color-scheme: dark) {
          .weedgo-scrollbar::-webkit-scrollbar-track {
            background: #1F2937;
          }
          
          .weedgo-scrollbar::-webkit-scrollbar-thumb {
            background: #2563EB;
          }
          
          .weedgo-scrollbar::-webkit-scrollbar-thumb:hover {
            background: #3B82F6;
          }
          
          .weedgo-scrollbar {
            scrollbar-color: #2563EB #1F2937;
          }
        }
      `}</style>
    </div>
  );
};

export default Scrollbar;