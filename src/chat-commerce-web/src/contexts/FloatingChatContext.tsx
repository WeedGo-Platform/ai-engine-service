import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';

// Types for floating chat states
export type ChatWindowState = 'docked' | 'floating' | 'minimized' | 'maximized';

export interface ChatWindowPosition {
  x: number;
  y: number;
}

export interface ChatWindowSize {
  width: number | string;
  height: number | string;
}

export interface FloatingChatContextType {
  // State
  windowState: ChatWindowState;
  position: ChatWindowPosition;
  size: ChatWindowSize;
  isDragging: boolean;
  isResizing: boolean;
  previousState: ChatWindowState | null;
  isAnimating: boolean;
  
  // Actions
  setWindowState: (state: ChatWindowState) => void;
  setPosition: (position: ChatWindowPosition) => void;
  setSize: (size: ChatWindowSize) => void;
  setIsDragging: (dragging: boolean) => void;
  setIsResizing: (resizing: boolean) => void;
  toggleFloating: () => void;
  minimize: () => void;
  maximize: () => void;
  restore: () => void;
  dock: () => void;
  
  // Preferences
  savePreferences: () => void;
  loadPreferences: () => void;
  resetPreferences: () => void;
}

// Default sizes for different states
const DEFAULT_DOCKED_SIZE: ChatWindowSize = {
  width: '70%',
  height: '100%'
};

const DEFAULT_FLOATING_SIZE: ChatWindowSize = {
  width: Math.floor(window.innerWidth / 3), // 1/3 of screen width
  height: '100vh'
};

const DEFAULT_MINIMIZED_SIZE: ChatWindowSize = {
  width: 320,
  height: 60
};

const DEFAULT_POSITION: ChatWindowPosition = {
  x: window.innerWidth - Math.floor(window.innerWidth / 3), // Position on right side
  y: 0
};

// Create context
const FloatingChatContext = createContext<FloatingChatContextType | undefined>(undefined);

// Provider component
export const FloatingChatProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [windowState, setWindowStateInternal] = useState<ChatWindowState>('docked');
  const [previousState, setPreviousState] = useState<ChatWindowState | null>(null);
  const [position, setPosition] = useState<ChatWindowPosition>(DEFAULT_POSITION);
  const [size, setSize] = useState<ChatWindowSize>(DEFAULT_DOCKED_SIZE);
  const [isDragging, setIsDragging] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);

  // Load preferences on mount
  useEffect(() => {
    loadPreferences();
    
    // Add keyboard shortcuts
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl/Cmd + Shift + C to toggle floating
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'C') {
        e.preventDefault();
        toggleFloating();
      }
      // Escape to minimize when floating
      if (e.key === 'Escape' && windowState === 'floating') {
        minimize();
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [windowState]);

  // State change handler with animation
  const setWindowState = useCallback((newState: ChatWindowState) => {
    setIsAnimating(true);
    setPreviousState(windowState);
    setWindowStateInternal(newState);
    
    // Update size based on new state
    switch (newState) {
      case 'docked':
        setSize(DEFAULT_DOCKED_SIZE);
        break;
      case 'floating':
        setSize(DEFAULT_FLOATING_SIZE);
        // Position on right side of screen
        setPosition({
          x: window.innerWidth - (DEFAULT_FLOATING_SIZE.width as number),
          y: 0
        });
        break;
      case 'minimized':
        setSize(DEFAULT_MINIMIZED_SIZE);
        break;
      case 'maximized':
        setSize({ width: '100%', height: '100%' });
        setPosition({ x: 0, y: 0 });
        break;
    }
    
    // End animation after transition
    setTimeout(() => setIsAnimating(false), 300);
  }, [windowState, position]);

  // Toggle between docked and floating
  const toggleFloating = useCallback(() => {
    if (windowState === 'docked') {
      setWindowState('floating');
    } else if (windowState === 'floating') {
      setWindowState('docked');
    } else if (windowState === 'minimized') {
      setWindowState('floating');
    } else if (windowState === 'maximized') {
      setWindowState('floating');
    }
  }, [windowState, setWindowState]);

  // Minimize window
  const minimize = useCallback(() => {
    if (windowState !== 'minimized') {
      setWindowState('minimized');
    }
  }, [windowState, setWindowState]);

  // Maximize window
  const maximize = useCallback(() => {
    if (windowState !== 'maximized') {
      setWindowState('maximized');
    }
  }, [windowState, setWindowState]);

  // Restore to previous state
  const restore = useCallback(() => {
    if (previousState) {
      setWindowState(previousState);
    } else {
      setWindowState('floating');
    }
  }, [previousState, setWindowState]);

  // Dock the window
  const dock = useCallback(() => {
    setWindowState('docked');
  }, [setWindowState]);

  // Save preferences to localStorage
  const savePreferences = useCallback(() => {
    const preferences = {
      windowState,
      position,
      size,
      timestamp: Date.now()
    };
    localStorage.setItem('floating_chat_preferences', JSON.stringify(preferences));
  }, [windowState, position, size]);

  // Load preferences from localStorage
  const loadPreferences = useCallback(() => {
    try {
      const saved = localStorage.getItem('floating_chat_preferences');
      if (saved) {
        const preferences = JSON.parse(saved);
        // Only restore if less than 24 hours old
        if (Date.now() - preferences.timestamp < 24 * 60 * 60 * 1000) {
          // Start in docked mode but remember floating preferences
          setWindowStateInternal('docked');
          if (preferences.position) {
            setPosition(preferences.position);
          }
          // Don't restore size as we want to start docked
        }
      }
    } catch (error) {
      console.error('Error loading floating chat preferences:', error);
    }
  }, []);

  // Reset preferences
  const resetPreferences = useCallback(() => {
    localStorage.removeItem('floating_chat_preferences');
    setWindowState('docked');
    setPosition(DEFAULT_POSITION);
    setSize(DEFAULT_DOCKED_SIZE);
  }, [setWindowState]);

  // Auto-save preferences on state changes
  useEffect(() => {
    if (!isAnimating && !isDragging && !isResizing) {
      savePreferences();
    }
  }, [windowState, position, size, isAnimating, isDragging, isResizing, savePreferences]);

  const value: FloatingChatContextType = {
    windowState,
    position,
    size,
    isDragging,
    isResizing,
    previousState,
    isAnimating,
    setWindowState,
    setPosition,
    setSize,
    setIsDragging,
    setIsResizing,
    toggleFloating,
    minimize,
    maximize,
    restore,
    dock,
    savePreferences,
    loadPreferences,
    resetPreferences
  };

  return (
    <FloatingChatContext.Provider value={value}>
      {children}
    </FloatingChatContext.Provider>
  );
};

// Custom hook to use the FloatingChat context
export const useFloatingChat = () => {
  const context = useContext(FloatingChatContext);
  if (!context) {
    throw new Error('useFloatingChat must be used within a FloatingChatProvider');
  }
  return context;
};