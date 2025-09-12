import type { ITheme } from '../../core/contracts/template.contracts';

export const darkTechTheme: ITheme = {
  name: 'Dark Tech',
  mode: 'dark',
  colors: {
    primary: '#00FF88',
    primaryLight: '#33FFB3',
    primaryDark: '#00CC6A',
    secondary: '#00D4FF',
    accent: '#FF00FF',
    
    success: '#00FF88',
    warning: '#FFD700',
    error: '#FF0066',
    info: '#00D4FF',
    
    background: '#0A0E1A',
    surface: '#1A1F2E',
    text: '#E0E6ED',
    textSecondary: '#A0A9B8',
    border: 'rgba(0, 255, 136, 0.2)',
    
    userMessage: 'rgba(0, 255, 136, 0.1)',
    assistantMessage: 'rgba(26, 31, 46, 0.9)',
    systemMessage: 'rgba(255, 215, 0, 0.1)',
  },
  typography: {
    fontFamily: {
      body: '"JetBrains Mono", "Fira Code", "Courier New", monospace',
      heading: '"JetBrains Mono", "Fira Code", "Courier New", monospace',
      mono: '"JetBrains Mono", "Fira Code", "Courier New", monospace',
    },
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      '2xl': '1.5rem',
      '3xl': '2rem',
    },
    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    '2xl': '3rem',
    '3xl': '4rem',
  },
  borderRadius: {
    sm: '0',
    md: '0.125rem',
    lg: '0.25rem',
    xl: '0.5rem',
    full: '9999px',
  },
  shadows: {
    sm: '0 0 10px rgba(0, 255, 136, 0.1)',
    md: '0 0 20px rgba(0, 255, 136, 0.15)',
    lg: '0 0 30px rgba(0, 255, 136, 0.2)',
    xl: '0 0 40px rgba(0, 255, 136, 0.25)',
    '2xl': '0 0 60px rgba(0, 255, 136, 0.3)',
  },
};