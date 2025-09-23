import { useEffect, useState } from 'react';
import { useLocalStorage } from './useLocalStorage';

export type DarkModeState = 'dark' | 'light' | 'system';

/**
 * Custom hook for managing dark mode with system preference support
 * Handles automatic theme switching and persistence
 */
export function useDarkMode() {
  const [darkModeState, setDarkModeState] = useLocalStorage<DarkModeState>('darkMode', 'system');
  const [isDarkMode, setIsDarkMode] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    const updateDarkMode = () => {
      let shouldBeDark = false;

      if (darkModeState === 'dark') {
        shouldBeDark = true;
      } else if (darkModeState === 'light') {
        shouldBeDark = false;
      } else {
        // System preference
        shouldBeDark = mediaQuery.matches;
      }

      setIsDarkMode(shouldBeDark);

      // Update document class
      if (shouldBeDark) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    };

    updateDarkMode();

    // Listen for system preference changes
    const handleChange = () => {
      if (darkModeState === 'system') {
        updateDarkMode();
      }
    };

    mediaQuery.addEventListener('change', handleChange);

    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, [darkModeState]);

  const toggleDarkMode = () => {
    setDarkModeState(current => {
      if (current === 'light') return 'dark';
      if (current === 'dark') return 'system';
      return 'light';
    });
  };

  const setMode = (mode: DarkModeState) => {
    setDarkModeState(mode);
  };

  return {
    isDarkMode,
    darkModeState,
    toggleDarkMode,
    setMode
  };
}