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
    // Add pot-palace specific scrollbar styles
    if (scrollRef.current) {
      scrollRef.current.style.setProperty('--scrollbar-thumb', 'linear-gradient(180deg, #9333EA 0%, #EC4899 100%)');
      scrollRef.current.style.setProperty('--scrollbar-track', '#FDF4FF');
    }
  }, []);

  return (
    <div 
      ref={scrollRef}
      className={`pot-palace-scrollbar overflow-y-auto ${className}`}
      style={{ maxHeight }}
    >
      {children}
      <style jsx>{`
        .pot-palace-scrollbar::-webkit-scrollbar {
          width: 10px;
          height: 10px;
        }
        
        .pot-palace-scrollbar::-webkit-scrollbar-track {
          background: #FDF4FF;
          border-radius: 10px;
        }
        
        .pot-palace-scrollbar::-webkit-scrollbar-thumb {
          background: linear-gradient(180deg, #9333EA 0%, #EC4899 100%);
          border-radius: 10px;
          border: 2px solid #FDF4FF;
        }
        
        .pot-palace-scrollbar::-webkit-scrollbar-thumb:hover {
          background: linear-gradient(180deg, #A855F7 0%, #F472B6 100%);
        }
        
        /* Firefox */
        .pot-palace-scrollbar {
          scrollbar-width: thin;
          scrollbar-color: #9333EA #FDF4FF;
        }
      `}</style>
    </div>
  );
};

export default Scrollbar;