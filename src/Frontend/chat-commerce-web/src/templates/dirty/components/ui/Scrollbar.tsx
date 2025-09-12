import React, { useRef, useEffect } from 'react';

interface ScrollbarProps {
  children: React.ReactNode;
  className?: string;
  maxHeight?: string;
  autoHide?: boolean;
  thin?: boolean;
}

const Scrollbar: React.FC<ScrollbarProps> = ({
  children,
  className = '',
  maxHeight = '100%',
  autoHide = true,
  thin = false,
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    const element = scrollRef.current;
    if (!element) return;
    
    // Add custom scrollbar styles
    const style = document.createElement('style');
    style.textContent = `
      .weedgo-scrollbar::-webkit-scrollbar {
        width: ${thin ? '6px' : '8px'};
        height: ${thin ? '6px' : '8px'};
      }
      
      .weedgo-scrollbar::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
      }
      
      .weedgo-scrollbar::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 10px;
      }
      
      .weedgo-scrollbar::-webkit-scrollbar-thumb:hover {
        background: #555;
      }
      
      ${autoHide ? `
        .weedgo-scrollbar-autohide::-webkit-scrollbar {
          opacity: 0;
          transition: opacity 0.3s;
        }
        
        .weedgo-scrollbar-autohide:hover::-webkit-scrollbar {
          opacity: 1;
        }
      ` : ''}
    `;
    
    document.head.appendChild(style);
    
    return () => {
      document.head.removeChild(style);
    };
  }, [thin, autoHide]);
  
  return (
    <div
      ref={scrollRef}
      className={`weedgo-scrollbar ${autoHide ? 'weedgo-scrollbar-autohide' : ''} overflow-auto ${className}`}
      style={{ maxHeight }}
    >
      {children}
    </div>
  );
};

export default Scrollbar;