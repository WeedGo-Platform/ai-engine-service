import type { ITheme } from '../../core/contracts/template.contracts';

export const dirtyTheme: ITheme = {
  name: 'Dirty',
  mode: 'dark',
  colors: {
    primary: '#2C2416',
    primaryLight: '#3E342A',
    primaryDark: '#1A1511',
    secondary: '#5C4033',
    accent: '#8B7355',
    
    success: '#4A5D23',
    warning: '#B8860B',
    error: '#8B0000',
    info: '#4682B4',
    
    background: 'linear-gradient(135deg, #1C1C1C 0%, #2B2B2B 100%)',
    surface: 'rgba(40, 40, 40, 0.95)',
    text: '#D3D3D3',
    textSecondary: '#A9A9A9',
    border: '#4A4A4A',
    
    userMessage: 'rgba(92, 64, 51, 0.3)',
    assistantMessage: 'rgba(60, 60, 60, 0.95)',
    systemMessage: 'rgba(139, 115, 85, 0.2)',
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
    sm: '0.375rem',
    md: '0.5rem',
    lg: '0.75rem',
    xl: '1rem',
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