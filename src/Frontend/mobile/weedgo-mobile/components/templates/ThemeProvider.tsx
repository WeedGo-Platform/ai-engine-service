import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Theme, TemplateType } from './types';

// Import themes (will be created next)
import { PotPalaceTheme } from './pot-palace/Theme';
import { ModernTheme } from './modern/Theme';
import { HeadlessTheme } from './headless/Theme';

interface ThemeContextType {
  theme: Theme;
  template: TemplateType;
  setTemplate: (template: TemplateType) => Promise<void>;
  colors: Theme['colors'];
  typography: Theme['typography'];
  spacing: Theme['spacing'];
  borderRadius: Theme['borderRadius'];
  shadows: Theme['shadows'];
  animation: Theme['animation'];
}

const ThemeContext = createContext<ThemeContextType | null>(null);

const THEME_STORAGE_KEY = '@weedgo/selected-template';

const themes: Record<TemplateType, Theme> = {
  'pot-palace': PotPalaceTheme,
  'modern': ModernTheme,
  'headless': HeadlessTheme,
};

interface ThemeProviderProps {
  children: ReactNode;
  defaultTemplate?: TemplateType;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({
  children,
  defaultTemplate = 'pot-palace'
}) => {
  const [template, setTemplateState] = useState<TemplateType>(defaultTemplate);
  const [isLoading, setIsLoading] = useState(true);

  // Load saved template preference on mount
  useEffect(() => {
    loadSavedTemplate();
  }, []);

  const loadSavedTemplate = async () => {
    try {
      const savedTemplate = await AsyncStorage.getItem(THEME_STORAGE_KEY);
      if (savedTemplate && savedTemplate in themes) {
        setTemplateState(savedTemplate as TemplateType);
      }
    } catch (error) {
      console.error('Error loading saved template:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const setTemplate = async (newTemplate: TemplateType) => {
    try {
      // Update state
      setTemplateState(newTemplate);

      // Save to storage
      await AsyncStorage.setItem(THEME_STORAGE_KEY, newTemplate);

      console.log(`Template switched to: ${newTemplate}`);
    } catch (error) {
      console.error('Error saving template preference:', error);
      throw error;
    }
  };

  // Get current theme based on template
  const currentTheme = themes[template];

  const contextValue: ThemeContextType = {
    theme: currentTheme,
    template,
    setTemplate,
    colors: currentTheme.colors,
    typography: currentTheme.typography,
    spacing: currentTheme.spacing,
    borderRadius: currentTheme.borderRadius,
    shadows: currentTheme.shadows,
    animation: currentTheme.animation,
  };

  // Show loading state while loading saved preference
  if (isLoading) {
    return null; // Or a splash screen component
  }

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
};

// Custom hook to use theme
export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

// Helper hook to get template-specific component
export const useTemplateComponent = <T extends {}>(
  components: Record<TemplateType, React.ComponentType<T>>
): React.ComponentType<T> => {
  const { template } = useTheme();
  return components[template] || components.headless;
};