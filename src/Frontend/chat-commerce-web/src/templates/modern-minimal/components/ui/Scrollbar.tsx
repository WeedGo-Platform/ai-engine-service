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
    // Add modern-minimal specific scrollbar styles
    if (scrollRef.current) {
      scrollRef.current.style.setProperty('--scrollbar-thumb', '#10B981');
      scrollRef.current.style.setProperty('--scrollbar-track', '#F3F4F6');
    }
  }, []);

  return (
    <div 
      ref={scrollRef}
      className={`modern-scrollbar overflow-y-auto ${className}`}
      style={{ maxHeight }}
    >
      {children}
      <style jsx>{`
        .modern-scrollbar::-webkit-scrollbar {
          width: 8px;
          height: 8px;
        }
        
        .modern-scrollbar::-webkit-scrollbar-track {
          background: #F3F4F6;
          border-radius: 4px;
        }
        
        .modern-scrollbar::-webkit-scrollbar-thumb {
          background: #10B981;
          border-radius: 4px;
          transition: background 0.2s ease;
        }
        
        .modern-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #059669;
        }
        
        .modern-scrollbar::-webkit-scrollbar-thumb:active {
          background: #047857;
        }
        
        /* Firefox */
        .modern-scrollbar {
          scrollbar-width: thin;
          scrollbar-color: #10B981 #F3F4F6;
        }
        
        /* Dark mode support */
        @media (prefers-color-scheme: dark) {
          .modern-scrollbar::-webkit-scrollbar-track {
            background: #1F2937;
          }
          
          .modern-scrollbar::-webkit-scrollbar-thumb {
            background: #10B981;
          }
          
          .modern-scrollbar::-webkit-scrollbar-thumb:hover {
            background: #34D399;
          }
          
          .modern-scrollbar {
            scrollbar-color: #10B981 #1F2937;
          }
        }
      `}</style>
    </div>
  );
};

export default Scrollbar;