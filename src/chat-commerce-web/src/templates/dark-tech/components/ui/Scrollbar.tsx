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
    // Add dark-tech specific scrollbar styles
    if (scrollRef.current) {
      scrollRef.current.style.setProperty('--scrollbar-thumb', '#10B981');
      scrollRef.current.style.setProperty('--scrollbar-track', '#111827');
    }
  }, []);

  return (
    <div 
      ref={scrollRef}
      className={`dark-tech-scrollbar overflow-y-auto ${className}`}
      style={{ maxHeight }}
    >
      {children}
      <style jsx>{`
        .dark-tech-scrollbar::-webkit-scrollbar {
          width: 10px;
          height: 10px;
        }
        
        .dark-tech-scrollbar::-webkit-scrollbar-track {
          background: #111827;
          border-radius: 0;
          border: 1px solid #10B981;
        }
        
        .dark-tech-scrollbar::-webkit-scrollbar-thumb {
          background: linear-gradient(180deg, #10B981 0%, #059669 100%);
          border-radius: 0;
          border: 1px solid #10B981;
          box-shadow: 
            inset 0 0 3px rgba(16, 185, 129, 0.5),
            0 0 10px rgba(16, 185, 129, 0.3);
          transition: all 0.3s ease;
        }
        
        .dark-tech-scrollbar::-webkit-scrollbar-thumb:hover {
          background: linear-gradient(180deg, #34D399 0%, #10B981 100%);
          box-shadow: 
            inset 0 0 5px rgba(16, 185, 129, 0.7),
            0 0 20px rgba(16, 185, 129, 0.5);
        }
        
        .dark-tech-scrollbar::-webkit-scrollbar-thumb:active {
          background: linear-gradient(180deg, #059669 0%, #047857 100%);
        }
        
        /* Firefox scrollbar support */
        .dark-tech-scrollbar {
          scrollbar-width: thin;
          scrollbar-color: #10B981 #111827;
        }
        
        /* Glitch effect on hover */
        @keyframes glitch {
          0%, 100% {
            transform: translateX(0);
          }
          20% {
            transform: translateX(-1px);
          }
          40% {
            transform: translateX(1px);
          }
          60% {
            transform: translateX(-1px);
          }
          80% {
            transform: translateX(1px);
          }
        }
        
        .dark-tech-scrollbar:hover::-webkit-scrollbar-thumb {
          animation: glitch 0.3s ease-in-out;
        }
      `}</style>
    </div>
  );
};

export default Scrollbar;