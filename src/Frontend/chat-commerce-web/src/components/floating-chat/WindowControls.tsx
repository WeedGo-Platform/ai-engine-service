import React from 'react';
import { motion } from 'framer-motion';
import { ChatWindowState } from '../../contexts/FloatingChatContext';

interface WindowControlsProps {
  windowState: ChatWindowState;
  onMinimize: () => void;
  onMaximize: () => void;
  onRestore: () => void;
  onClose: () => void;
  className?: string;
}

const WindowControls: React.FC<WindowControlsProps> = ({
  windowState,
  onMinimize,
  onMaximize,
  onRestore,
  onClose,
  className = ''
}) => {
  const buttonClass = "p-1.5 rounded-lg hover:bg-black/10 transition-colors relative group";
  
  return (
    <div className={`flex items-center gap-1 ${className}`}>
      {/* Minimize Button */}
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        onClick={(e) => {
          e.stopPropagation();
          onMinimize();
        }}
        className={buttonClass}
        title="Minimize (Esc)"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 12H4" />
        </svg>
        <span className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
          Minimize
        </span>
      </motion.button>

      {/* Maximize/Restore Button */}
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        onClick={(e) => {
          e.stopPropagation();
          windowState === 'maximized' ? onRestore() : onMaximize();
        }}
        className={buttonClass}
        title={windowState === 'maximized' ? 'Restore' : 'Maximize'}
      >
        {windowState === 'maximized' ? (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 7h10v10M7 7v10h10M7 7l10 10" />
          </svg>
        ) : (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
          </svg>
        )}
        <span className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
          {windowState === 'maximized' ? 'Restore' : 'Maximize'}
        </span>
      </motion.button>

      {/* Close/Dock Button */}
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        onClick={(e) => {
          e.stopPropagation();
          onClose();
        }}
        className={`${buttonClass} hover:bg-red-500/20`}
        title="Dock to sidebar"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
        <span className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
          Dock
        </span>
      </motion.button>
    </div>
  );
};

export default WindowControls;