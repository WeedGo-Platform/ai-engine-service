import React from 'react';
import { motion } from 'framer-motion';
import { useTemplateContext } from '../../contexts/TemplateContext';

interface ChatDockToggleProps {
  isFloating: boolean;
  onClick: () => void;
  className?: string;
  style?: React.CSSProperties;
}

const ChatDockToggle: React.FC<ChatDockToggleProps> = ({ 
  isFloating, 
  onClick, 
  className = '',
  style = {}
}) => {
  const { currentTemplate } = useTemplateContext();
  
  // Get theme-specific styles
  const getThemeStyles = () => {
    switch (currentTemplate) {
      case 'pot-palace':
        return {
          background: 'linear-gradient(135deg, #FDE047 0%, #FACC15 100%)',
          hoverBackground: 'linear-gradient(135deg, #FACC15 0%, #F59E0B 100%)',
          iconColor: '#7C2D12',
          shadow: '0 10px 25px -5px rgba(251, 191, 36, 0.5)',
          hoverShadow: '0 20px 35px -5px rgba(251, 191, 36, 0.7)',
          pulseColor: 'rgba(251, 191, 36, 0.4)'
        };
      case 'modern-minimal':
        return {
          background: 'linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)',
          hoverBackground: 'linear-gradient(135deg, #2563EB 0%, #1E40AF 100%)',
          iconColor: '#FFFFFF',
          shadow: '0 10px 25px -5px rgba(59, 130, 246, 0.3)',
          hoverShadow: '0 20px 35px -5px rgba(59, 130, 246, 0.5)',
          pulseColor: 'rgba(59, 130, 246, 0.3)'
        };
      case 'dark-tech':
        return {
          background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
          hoverBackground: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
          iconColor: '#FFFFFF',
          shadow: '0 10px 25px -5px rgba(16, 185, 129, 0.4)',
          hoverShadow: '0 20px 35px -5px rgba(16, 185, 129, 0.6)',
          pulseColor: 'rgba(16, 185, 129, 0.3)'
        };
      default:
        return {
          background: 'linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%)',
          hoverBackground: 'linear-gradient(135deg, #7C3AED 0%, #6D28D9 100%)',
          iconColor: '#FFFFFF',
          shadow: '0 10px 25px -5px rgba(139, 92, 246, 0.3)',
          hoverShadow: '0 20px 35px -5px rgba(139, 92, 246, 0.5)',
          pulseColor: 'rgba(139, 92, 246, 0.3)'
        };
    }
  };

  const themeStyles = getThemeStyles();

  return (
    <motion.button
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      className={`relative group ${className}`}
      title={isFloating ? 'Dock chat window' : 'Float chat window (Ctrl+Shift+C)'}
      style={{
        width: '56px',
        height: '56px',
        borderRadius: '50%',
        background: themeStyles.background,
        boxShadow: themeStyles.shadow,
        border: 'none',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        transition: 'all 0.3s ease',
        ...style
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = themeStyles.hoverBackground;
        e.currentTarget.style.boxShadow = themeStyles.hoverShadow;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = themeStyles.background;
        e.currentTarget.style.boxShadow = themeStyles.shadow;
      }}
    >
      {/* Pulse animation ring */}
      <motion.div
        className="absolute inset-0 rounded-full"
        style={{
          background: themeStyles.pulseColor
        }}
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.5, 0, 0.5]
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
      
      {/* Icon */}
      <motion.div
        animate={{ rotate: isFloating ? 180 : 0 }}
        transition={{ duration: 0.3 }}
        style={{ color: themeStyles.iconColor }}
      >
        {isFloating ? (
          // Dock icon
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
          </svg>
        ) : (
          // Float/Expand icon
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
          </svg>
        )}
      </motion.div>
      
      {/* Tooltip */}
      <div className="absolute -top-12 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white text-xs px-3 py-2 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
        {isFloating ? 'Dock Chat' : 'Float Chat'}
        <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-1/2 rotate-45 w-2 h-2 bg-gray-900"></div>
      </div>
      
      {/* Keyboard shortcut hint */}
      {!isFloating && (
        <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 text-xs opacity-0 group-hover:opacity-75 transition-opacity whitespace-nowrap pointer-events-none">
          <kbd className="px-1 py-0.5 bg-gray-200 rounded text-gray-700 font-mono text-[10px]">Ctrl+Shift+C</kbd>
        </div>
      )}
    </motion.button>
  );
};

export default ChatDockToggle;