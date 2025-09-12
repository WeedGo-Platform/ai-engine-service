import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { getTemplateFactory, TemplateProvider } from '../core/providers/template.provider';
import { registerTemplates, DEFAULT_TEMPLATE } from '../templates';
import type { ITemplateProvider } from '../core/contracts/template.contracts';

interface TemplateContextType {
  currentTemplate: string;
  availableTemplates: string[];
  switchTemplate: (templateName: string) => void;
}

const TemplateContext = createContext<TemplateContextType | null>(null);

export function useTemplateContext() {
  const context = useContext(TemplateContext);
  if (!context) {
    throw new Error('useTemplateContext must be used within TemplateContextProvider');
  }
  return context;
}

interface TemplateContextProviderProps {
  children: ReactNode;
}

export function TemplateContextProvider({ children }: TemplateContextProviderProps) {
  const [currentTemplate, setCurrentTemplate] = useState<string>(() => {
    // Priority: 1. Environment variable, 2. localStorage, 3. Default
    const envTemplate = import.meta.env.VITE_TEMPLATE;
    if (envTemplate) {
      return envTemplate;
    }
    // Load saved template from localStorage
    return localStorage.getItem('selectedTemplate') || DEFAULT_TEMPLATE;
  });
  
  const [provider, setProvider] = useState<ITemplateProvider | null>(null);

  useEffect(() => {
    // Register all templates on mount
    registerTemplates();
    
    // Load the initial template
    const factory = getTemplateFactory();
    const initialProvider = factory.create(currentTemplate);
    setProvider(initialProvider);
  }, []);

  useEffect(() => {
    // Update provider when template changes
    const factory = getTemplateFactory();
    const newProvider = factory.create(currentTemplate);
    setProvider(newProvider);
    
    // Save to localStorage
    localStorage.setItem('selectedTemplate', currentTemplate);
    
    // Apply global styles
    const styleId = 'template-global-styles';
    let styleElement = document.getElementById(styleId) as HTMLStyleElement;
    
    if (!styleElement) {
      styleElement = document.createElement('style');
      styleElement.id = styleId;
      document.head.appendChild(styleElement);
    }
    
    styleElement.textContent = newProvider.getStyles().getGlobalStyles();
  }, [currentTemplate]);

  const switchTemplate = (templateName: string) => {
    setCurrentTemplate(templateName);
  };

  const factory = getTemplateFactory();
  const availableTemplates = factory.getAvailableTemplates();

  if (!provider) {
    return null; // Loading state
  }

  return (
    <TemplateContext.Provider
      value={{
        currentTemplate,
        availableTemplates,
        switchTemplate,
      }}
    >
      <TemplateProvider provider={provider}>
        {children}
      </TemplateProvider>
    </TemplateContext.Provider>
  );
}