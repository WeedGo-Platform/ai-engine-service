import React, { useEffect, useRef } from 'react';
import { Rnd } from 'react-rnd';
import { motion } from 'framer-motion';
import { useFloatingChat, ChatWindowState } from '../../contexts/FloatingChatContext';
import WindowControls from './WindowControls';
import { useTemplateContext } from '../../contexts/TemplateContext';

interface FloatingChatWindowProps {
  children: React.ReactNode;
  windowState: ChatWindowState;
  onMinimize: () => void;
  onMaximize: () => void;
  onRestore: () => void;
  onClose: () => void;
}

const FloatingChatWindow: React.FC<FloatingChatWindowProps> = ({
  children,
  windowState,
  onMinimize,
  onMaximize,
  onRestore,
  onClose
}) => {
  const {
    position,
    size,
    setPosition,
    setSize,
    setIsDragging,
    setIsResizing
  } = useFloatingChat();
  
  const { currentTemplate } = useTemplateContext();
  const windowRef = useRef<HTMLDivElement>(null);

  // Get theme-specific styles
  const getThemeStyles = () => {
    switch (currentTemplate) {
      case 'pot-palace':
        return {
          background: 'linear-gradient(135deg, rgba(147, 51, 234, 0.98) 0%, rgba(219, 39, 119, 0.98) 100%)',
          borderColor: 'rgba(168, 85, 247, 0.8)',
          shadow: '0 25px 50px -12px rgba(147, 51, 234, 0.5)',
          headerBg: 'rgba(88, 28, 135, 0.9)',
          borderWidth: '3px'
        };
      case 'modern-minimal':
        return {
          background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(249, 250, 251, 0.98) 100%)',
          borderColor: 'rgba(59, 130, 246, 0.6)',
          shadow: '0 20px 40px -10px rgba(0, 0, 0, 0.1)',
          headerBg: 'rgba(249, 250, 251, 0.95)',
          borderWidth: '3px'
        };
      case 'dark-tech':
        return {
          background: 'linear-gradient(135deg, rgba(17, 24, 39, 0.98) 0%, rgba(31, 41, 55, 0.98) 100%)',
          borderColor: 'rgba(16, 185, 129, 0.8)',
          shadow: '0 25px 50px -12px rgba(16, 185, 129, 0.3)',
          headerBg: 'rgba(17, 24, 39, 0.95)',
          borderWidth: '3px'
        };
      default:
        return {
          background: 'rgba(255, 255, 255, 0.98)',
          borderColor: 'rgba(209, 213, 219, 0.8)',
          shadow: '0 20px 40px -10px rgba(0, 0, 0, 0.1)',
          headerBg: 'rgba(249, 250, 251, 0.95)',
          borderWidth: '3px'
        };
    }
  };

  const themeStyles = getThemeStyles();

  // Handle escape key to minimize
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && windowState === 'floating') {
        onMinimize();
      }
    };
    
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [windowState, onMinimize]);

  // Focus management
  useEffect(() => {
    if (windowState === 'floating' && windowRef.current) {
      windowRef.current.focus();
    }
  }, [windowState]);

  // Render minimized state
  if (windowState === 'minimized') {
    return (
      <motion.div
        ref={windowRef}
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="fixed bottom-4 right-4 cursor-pointer"
        style={{
          background: themeStyles.background,
          borderRadius: '30px',
          boxShadow: themeStyles.shadow,
          border: `1px solid ${themeStyles.borderColor}`,
          backdropFilter: 'blur(10px)'
        }}
        onClick={onRestore}
      >
        <div className="flex items-center gap-3 px-4 py-3">
          <div className="relative">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full animate-pulse border-2 border-white"></div>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold truncate">AI Assistant</p>
            <p className="text-xs opacity-75 truncate">Click to expand</p>
          </div>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onClose();
            }}
            className="p-1 hover:bg-black/10 rounded-full transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </motion.div>
    );
  }

  // Render maximized state
  if (windowState === 'maximized') {
    return (
      <motion.div
        ref={windowRef}
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        className="fixed inset-0 flex flex-col"
        style={{
          background: themeStyles.background,
          backdropFilter: 'blur(10px)'
        }}
      >
        {/* Header */}
        <div 
          className="flex items-center justify-between px-4 py-3 border-b"
          style={{
            backgroundColor: themeStyles.headerBg,
            borderColor: themeStyles.borderColor
          }}
        >
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <span className="font-semibold">AI Chat Assistant</span>
          </div>
          <WindowControls
            windowState={windowState}
            onMinimize={onMinimize}
            onMaximize={onMaximize}
            onRestore={onRestore}
            onClose={onClose}
          />
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {children}
        </div>
      </motion.div>
    );
  }

  // Render floating state with drag and resize
  return (
    <Rnd
      size={{ width: size.width, height: size.height }}
      position={{ x: position.x, y: position.y }}
      onDragStart={() => setIsDragging(true)}
      onDragStop={(e, d) => {
        setIsDragging(false);
        setPosition({ x: d.x, y: d.y });
      }}
      onResizeStart={() => setIsResizing(true)}
      onResizeStop={(e, direction, ref, delta, position) => {
        setIsResizing(false);
        setSize({
          width: ref.offsetWidth,
          height: ref.offsetHeight
        });
        setPosition(position);
      }}
      minWidth={320}
      minHeight={400}
      maxWidth={window.innerWidth * 0.9}
      maxHeight={window.innerHeight * 0.9}
      bounds="window"
      dragHandleClassName="chat-window-header"
      enableResizing={{
        top: true,
        right: true,
        bottom: true,
        left: true,
        topRight: true,
        bottomRight: true,
        bottomLeft: true,
        topLeft: true
      }}
      resizeHandleStyles={{
        top: { cursor: 'ns-resize' },
        right: { cursor: 'ew-resize' },
        bottom: { cursor: 'ns-resize' },
        left: { cursor: 'ew-resize' },
        topRight: { cursor: 'nesw-resize' },
        bottomRight: { cursor: 'nwse-resize' },
        bottomLeft: { cursor: 'nesw-resize' },
        topLeft: { cursor: 'nwse-resize' }
      }}
      className="floating-chat-resizable"
    >
      <motion.div
        ref={windowRef}
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="h-full flex flex-col overflow-hidden"
        style={{
          background: themeStyles.background,
          boxShadow: themeStyles.shadow,
          border: `${themeStyles.borderWidth || '3px'} solid ${themeStyles.borderColor}`,
          borderRadius: '16px',
          backdropFilter: 'blur(10px)',
          overflow: 'hidden'
        }}
      >
        {/* Draggable Header */}
        <div 
          className="chat-window-header flex items-center justify-between px-4 py-3 border-b cursor-move select-none"
          style={{
            backgroundColor: themeStyles.headerBg,
            borderColor: themeStyles.borderColor
          }}
        >
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <div className="flex-1">
              <span className="font-semibold">AI Chat Assistant</span>
              <span className="ml-2 text-xs opacity-75">Drag to move</span>
            </div>
          </div>
          <WindowControls
            windowState={windowState}
            onMinimize={onMinimize}
            onMaximize={onMaximize}
            onRestore={onRestore}
            onClose={onClose}
          />
        </div>
        
        {/* Chat Content */}
        <div className="flex-1 overflow-hidden">
          {children}
        </div>
        
        {/* Resize indicator */}
        <div className="absolute bottom-2 right-2 w-4 h-4 opacity-30">
          <svg className="w-full h-full" fill="currentColor" viewBox="0 0 24 24">
            <path d="M22,22H20V20h2v2m-4,0H16V20h2v2m-4,0H12V20h2v2m0-4H12V16h2v2m4,0H16V16h2v2m4,0H20V16h2v2m0-4H20V12h2v2" />
          </svg>
        </div>
      </motion.div>
    </Rnd>
  );
};

export default FloatingChatWindow;