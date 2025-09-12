import type { ITheme } from '../../core/contracts/template.contracts';

export const metalTheme: ITheme = {
  name: 'Metal',
  mode: 'dark',
  colors: {
    primary: '#FF0000',
    primaryLight: '#FF4444',
    primaryDark: '#CC0000',
    secondary: '#000000',
    accent: '#C0C0C0',
    
    success: '#00FF00',
    warning: '#FFA500',
    error: '#DC143C',
    info: '#1E90FF',
    
    background: 'linear-gradient(135deg, #000000 0%, #1A1A1A 50%, #000000 100%)',
    surface: 'rgba(30, 30, 30, 0.98)',
    text: '#FFFFFF',
    textSecondary: '#C0C0C0',
    border: '#666666',
    
    userMessage: 'rgba(255, 0, 0, 0.1)',
    assistantMessage: 'rgba(48, 48, 48, 0.95)',
    systemMessage: 'rgba(192, 192, 192, 0.1)',
  },
  typography: {
    fontFamily: {
      body: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      heading: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
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
    sm: '0.125rem',
    md: '0.25rem',
    lg: '0.375rem',
    xl: '0.5rem',
    full: '9999px',
  },
  shadows: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
    xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
    '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
  },
};