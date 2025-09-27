import React, { createContext, useContext, useEffect, ReactNode } from 'react';
import { useColorScheme } from 'react-native';
import { useThemeStore } from '@/stores/themeStore';
import { Colors } from '@/constants/Colors';

interface ThemeContextType {
  theme: typeof Colors.light | typeof Colors.dark;
  isDark: boolean;
  colors: typeof Colors.light | typeof Colors.dark;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider = ({ children }: { children: ReactNode }) => {
  const systemColorScheme = useColorScheme();
  const { mode, isDark, syncWithSystem } = useThemeStore();

  useEffect(() => {
    // Sync with system theme if mode is 'system'
    syncWithSystem(systemColorScheme === 'dark');
  }, [systemColorScheme, syncWithSystem]);

  const theme = isDark ? Colors.dark : Colors.light;

  return (
    <ThemeContext.Provider value={{ theme, isDark, colors: theme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};