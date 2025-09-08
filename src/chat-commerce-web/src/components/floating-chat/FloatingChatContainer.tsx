import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { useFloatingChat } from '../../contexts/FloatingChatContext';
import { useTemplateContext } from '../../contexts/TemplateContext';
import FloatingChatWindow from './FloatingChatWindow';

interface FloatingChatContainerProps {
  children: React.ReactNode;
  className?: string;
  isPanelOpen?: boolean;
}

const FloatingChatContainer: React.FC<FloatingChatContainerProps> = ({ 
  children, 
  className = '',
  isPanelOpen = false
}) => {
  const {
    windowState,
    isAnimating,
    position,
    size,
    toggleFloating,
    minimize,
    maximize,
    restore
  } = useFloatingChat();
  
  const { currentTemplate } = useTemplateContext();
  const [portalRoot, setPortalRoot] = useState<HTMLElement | null>(null);
  
  // Get template-specific border colors
  const getBorderColor = () => {
    switch (currentTemplate) {
      case 'pot-palace':
        return 'border-purple-400/60';
      case 'modern-minimal':
        return 'border-blue-400/60';
      case 'dark-tech':
        return 'border-green-400/60';
      default:
        return 'border-gray-400/60';
    }
  };

  // Create portal root on mount
  useEffect(() => {
    const root = document.getElementById('floating-chat-portal');
    if (!root) {
      const newRoot = document.createElement('div');
      newRoot.id = 'floating-chat-portal';
      newRoot.style.position = 'fixed';
      newRoot.style.top = '0';
      newRoot.style.left = '0';
      newRoot.style.width = '100%';
      newRoot.style.height = '100%';
      newRoot.style.pointerEvents = 'none';
      newRoot.style.zIndex = '50000'; // High but lower than search dropdown portal
      document.body.appendChild(newRoot);
      setPortalRoot(newRoot);
    } else {
      setPortalRoot(root);
    }

    return () => {
      // Cleanup portal root if needed
      const root = document.getElementById('floating-chat-portal');
      if (root && root.childNodes.length === 0) {
        root.remove();
      }
    };
  }, []);

  // Animation variants for different states
  const variants: Record<string, any> = {
    docked: {
      x: 0,
      y: 0,
      width: typeof size.width === 'string' ? size.width : `${size.width}px`,
      height: '100%',
      borderRadius: 0,
      transition: {
        type: 'spring',
        damping: 25,
        stiffness: 300
      }
    },
    floating: {
      x: isPanelOpen && window.innerWidth > 640 ? position.x + 320 : position.x,
      y: position.y,
      width: typeof size.width === 'string' ? size.width : `${size.width}px`,
      height: typeof size.height === 'string' ? size.height : `${size.height}px`,
      borderRadius: 16,
      transition: {
        type: 'spring',
        damping: 25,
        stiffness: 300
      }
    },
    minimized: {
      x: window.innerWidth - 340,
      y: window.innerHeight - 80,
      width: '320px',
      height: '60px',
      borderRadius: 30,
      transition: {
        type: 'spring',
        damping: 20,
        stiffness: 300
      }
    },
    maximized: {
      x: 0,
      y: 0,
      width: '100%',
      height: '100%',
      borderRadius: 0,
      transition: {
        type: 'spring',
        damping: 25,
        stiffness: 300
      }
    }
  };

  // Render docked state (no portal needed)
  if (windowState === 'docked') {
    return (
      <div className={`relative flex flex-col h-full ${className}`} style={{ overflow: 'hidden' }}>
        {/* Main chat content with rounded borders */}
        <div className={`flex-1 flex flex-col overflow-hidden rounded-2xl border-4 ${getBorderColor()} bg-white/95`} 
             style={{ margin: '8px' }}>
          {children}
        </div>
      </div>
    );
  }

  // Render floating/minimized/maximized states (use portal)
  if (!portalRoot) return null;

  return (
    <>
      {/* Placeholder for docked space when floating */}
      <div className={`${className} flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100`}>
        <div className="text-center p-8">
          <div className="mb-4">
            <svg className="w-16 h-16 mx-auto text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Chat is floating</h3>
          <p className="text-gray-500 mb-4">The chat window is now floating. You can continue browsing while chatting.</p>
          <button
            onClick={toggleFloating}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            Dock Chat Window
          </button>
        </div>
      </div>

      {/* Floating window rendered in portal */}
      {createPortal(
        <AnimatePresence mode="wait">
          <motion.div
            key={windowState}
            variants={variants}
            initial={false}
            animate={windowState}
            style={{
              position: 'fixed',
              pointerEvents: 'auto'
            }}
            className="floating-chat-window"
          >
            <FloatingChatWindow
              windowState={windowState}
              onMinimize={minimize}
              onMaximize={maximize}
              onRestore={restore}
              onClose={toggleFloating}
            >
              {children}
            </FloatingChatWindow>
          </motion.div>
        </AnimatePresence>,
        portalRoot
      )}
    </>
  );
};

export default FloatingChatContainer;