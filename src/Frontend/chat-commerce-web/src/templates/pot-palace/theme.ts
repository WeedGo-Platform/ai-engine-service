import type { ITheme } from '../../core/contracts/template.contracts';

export const potPalaceTheme: ITheme = {
  name: 'Pot Palace',
  mode: 'dark',
  colors: {
    primary: '#E91ED4',
    primaryLight: '#FF4FED',
    primaryDark: '#C018B1',
    secondary: '#FF006E',
    accent: '#FFB700',
    
    success: '#00E676',
    warning: '#FFB700',
    error: '#FF3B3B',
    info: '#00B8FF',
    
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    surface: 'rgba(255, 255, 255, 0.9)',
    text: '#1a1a1a',
    textSecondary: '#666666',
    border: 'rgba(0, 0, 0, 0.1)',
    
    userMessage: 'rgba(233, 30, 212, 0.1)',
    assistantMessage: 'rgba(255, 255, 255, 0.95)',
    systemMessage: 'rgba(255, 183, 0, 0.1)',
  },
  typography: {
    fontFamily: {
      body: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      heading: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      mono: '"Fira Code", "Courier New", monospace',
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
    sm: '0.25rem',
    md: '0.5rem',
    lg: '0.75rem',
    xl: '1rem',
    full: '9999px',
  },
  shadows: {
    sm: '0 1px 2px rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px rgba(0, 0, 0, 0.1)',
    lg: '0 10px 15px rgba(0, 0, 0, 0.1)',
    xl: '0 20px 25px rgba(0, 0, 0, 0.15)',
    '2xl': '0 25px 50px rgba(0, 0, 0, 0.25)',
  },
};