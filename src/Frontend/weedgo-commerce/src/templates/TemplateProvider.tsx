import React, { createContext, useContext, useMemo, useEffect } from 'react';
import type { ITemplate } from './types';
import { ModernTemplate } from './modern';
// Template imports will be added as we create them
// import { PotPalaceTemplate } from './pot-palace';
// import { HeadlessTemplate } from './headless';

// Import theme CSS files
import './modern/modern.css';

const TemplateContext = createContext<ITemplate | null>(null);

interface TemplateProviderProps {
  children: React.ReactNode;
  templateOverride?: string;
}

export const TemplateProvider: React.FC<TemplateProviderProps> = ({
  children,
  templateOverride
}) => {
  const templateName = templateOverride || import.meta.env.VITE_TEMPLATE || 'modern';

  const template = useMemo(() => {
    // Select the appropriate template based on the name
    if (templateName === 'modern') {
      return ModernTemplate;
    }

    // Default placeholder template for other themes
    const placeholderTemplate: ITemplate = {
      name: templateName,
      theme: {
        colors: {
          primary: '#2E7D32',
          secondary: '#FDD835',
          accent: '#8B4513',
          background: '#FFFFFF',
          surface: '#F5F5F5',
          text: '#212121',
          textSecondary: '#757575',
          border: '#E0E0E0',
          error: '#F44336',
          success: '#4CAF50',
          warning: '#FF9800',
          info: '#2196F3'
        },
        spacing: {
          xs: '0.25rem',
          sm: '0.5rem',
          md: '1rem',
          lg: '1.5rem',
          xl: '2rem',
          '2xl': '3rem'
        },
        borderRadius: {
          none: '0',
          sm: '0.125rem',
          md: '0.375rem',
          lg: '0.5rem',
          xl: '0.75rem',
          full: '9999px'
        },
        shadows: {
          sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
          md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
          lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
          xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1)'
        }
      },
      layout: {
        maxWidth: '1280px',
        headerHeight: '64px',
        footerHeight: '200px',
        mobileBreakpoint: '640px',
        tabletBreakpoint: '768px'
      },
      components: {} as any, // Will be populated with actual components
      animations: {
        defaultDuration: 200,
        defaultEasing: 'ease-in-out',
        pageTransition: 'fade',
        cardHover: 'scale',
        buttonPress: 'scale'
      },
      typography: {
        fontFamily: {
          sans: 'Inter, system-ui, sans-serif'
        },
        fontSize: {
          xs: '0.75rem',
          sm: '0.875rem',
          base: '1rem',
          lg: '1.125rem',
          xl: '1.25rem',
          '2xl': '1.5rem',
          '3xl': '1.875rem',
          '4xl': '2.25rem',
          '5xl': '3rem'
        },
        fontWeight: {
          light: 300,
          normal: 400,
          medium: 500,
          semibold: 600,
          bold: 700
        },
        lineHeight: {
          tight: 1.25,
          normal: 1.5,
          relaxed: 1.75
        }
      }
    };

    return placeholderTemplate;
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