import React, { useState } from 'react';

interface ConfigToggleButtonProps {
  isOpen?: boolean;
  onClick?: () => void;
  position?: 'left' | 'right';
}

const ConfigToggleButton: React.FC<ConfigToggleButtonProps> = ({
  isOpen = false,
  onClick,
  position = 'right',
}) => {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className="fixed top-1/2 transform -translate-y-1/2 z-40 transition-all"
      style={{
        [position]: isOpen ? '320px' : '0px',
        transition: 'all 0.3s ease',
      }}
      aria-label={isOpen ? "Close configuration" : "Open configuration"}
    >
      <div 
        className="relative py-4 px-2 rounded-l-xl transition-all hover:scale-110"
        style={{
          background: 'linear-gradient(135deg, rgba(252, 211, 77, 0.95) 0%, rgba(252, 211, 77, 0.85) 100%)',
          border: '2px solid rgba(0, 0, 0, 0.3)',
          borderRight: 'none',
          boxShadow: '-5px 0 20px rgba(0, 0, 0, 0.3), 0 0 30px rgba(252, 211, 77, 0.3)',
          transform: position === 'left' ? 'scaleX(-1)' : 'scaleX(1)',
        }}
      >
        {/* Icon */}
        <div 
          className="flex flex-col items-center space-y-2"
          style={{ transform: position === 'left' ? 'scaleX(-1)' : 'scaleX(1)' }}
        >
          <svg 
            className="w-5 h-5 transition-transform"
            fill="currentColor" 
            viewBox="0 0 24 24"
            style={{
              color: '#000',
              transform: isOpen ? 'rotate(0deg)' : 'rotate(180deg)',
            }}
          >
            <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z" />
          </svg>
          
          {/* Settings Icon */}
          <div 
            className="text-lg"
            style={{ 
              color: '#000',
              animation: isHovered ? 'spin 2s linear infinite' : 'none',
            }}
          >
            ⚙️
          </div>
        </div>

        {/* Decorative Elements */}
        <div className="absolute top-1 left-1/2 transform -translate-x-1/2">
          <div 
            className="w-1 h-1 rounded-full"
            style={{ background: '#DC2626' }}
          />
        </div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
          <div 
            className="w-1 h-1 rounded-full"
            style={{ background: '#16A34A' }}
          />
        </div>
        <div className="absolute bottom-1 left-1/2 transform -translate-x-1/2">
          <div 
            className="w-1 h-1 rounded-full"
            style={{ background: '#DC2626' }}
          />
        </div>
      </div>

      {/* Tooltip */}
      {isHovered && !isOpen && (
        <div 
          className="absolute top-1/2 transform -translate-y-1/2 whitespace-nowrap smooth-fade-in"
          style={{
            [position]: '100%',
            marginLeft: position === 'right' ? '10px' : '0',
            marginRight: position === 'left' ? '10px' : '0',
          }}
        >
          <div 
            className="px-3 py-2 rounded-lg"
            style={{
              background: 'rgba(26, 26, 26, 0.95)',
              border: '1px solid rgba(252, 211, 77, 0.3)',
              color: '#FCD34D',
              fontSize: '0.75rem',
              fontFamily: 'Ubuntu, sans-serif',
            }}
          >
            Configuration Settings
          </div>
        </div>
      )}
    </button>
  );
};

export default ConfigToggleButton;