import React, { createContext, useContext, useMemo, useEffect } from 'react';
import type { ITemplate } from './types';
import { ModernTemplate } from './modern';
import { PotPalaceTemplate } from './pot-palace';
import { useStore } from '@contexts/StoreContext';
// import { HeadlessTemplate } from './headless';

// Import theme CSS files
import './modern/modern.css';
import './pot-palace/pot-palace.css';

const TemplateContext = createContext<ITemplate | null>(null);

interface TemplateProviderProps {
  children: React.ReactNode;
  templateOverride?: string;
}

export const TemplateProvider: React.FC<TemplateProviderProps> = ({
  children,
  templateOverride
}) => {
  const { selectedStore } = useStore();

  // Use store template if available, otherwise fall back to override or env variable
  const templateName = selectedStore?.template || templateOverride || import.meta.env.VITE_TEMPLATE || 'modern';

  const template = useMemo(() => {
    // Select the appropriate template based on the name
    switch (templateName) {
      case 'modern':
        return ModernTemplate;
      case 'pot-palace':
        return PotPalaceTemplate;
      default:
        // Default to modern template if unknown
        console.warn(`Unknown template: ${templateName}, falling back to modern`);
        return ModernTemplate;
    }
  }, [templateName]);

  // Apply theme CSS variables
  useEffect(() => {
    if (template.theme.cssVariables) {
      const root = document.documentElement;
      Object.entries(template.theme.colors).forEach(([key, value]) => {
        root.style.setProperty(`--color-${key}`, value);
      });
      Object.entries(template.theme.spacing).forEach(([key, value]) => {
        root.style.setProperty(`--spacing-${key}`, value);
      });
      Object.entries(template.theme.borderRadius).forEach(([key, value]) => {
        root.style.setProperty(`--radius-${key}`, value);
      });
    }
  }, [template]);

  return (
    <TemplateContext.Provider value={template}>
      <div className={`template-${template.name}`} data-theme={template.name}>
        {children}
      </div>
    </TemplateContext.Provider>
  );
};

export const useTemplate = () => {
  const context = useContext(TemplateContext);
  if (!context) {
    throw new Error('useTemplate must be used within TemplateProvider');
  }
  return context;
};

// Helper hook for accessing theme values
export const useTheme = () => {
  const template = useTemplate();
  return template.theme;
};

// Helper hook for accessing components
export const useTemplateComponents = () => {
  const template = useTemplate();
  return template.components;
};