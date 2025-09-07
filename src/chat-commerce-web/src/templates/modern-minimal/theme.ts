import type { ITheme } from '../../core/contracts/template.contracts';

export const modernMinimalTheme: ITheme = {
  name: 'Modern Minimal',
  mode: 'light',
  colors: {
    primary: '#000000',
    primaryLight: '#333333',
    primaryDark: '#000000',
    secondary: '#666666',
    accent: '#0066CC',
    
    success: '#00C853',
    warning: '#FFB300',
    error: '#D32F2F',
    info: '#0091EA',
    
    background: '#FFFFFF',
    surface: '#FAFAFA',
    text: '#000000',
    textSecondary: '#666666',
    border: '#E0E0E0',
    
    userMessage: '#F5F5F5',
    assistantMessage: '#FFFFFF',
    systemMessage: '#FFF9C4',
  },
  typography: {
    fontFamily: {
      body: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      heading: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      mono: '"JetBrains Mono", "Fira Code", monospace',
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
    lg: '0.5rem',
    xl: '0.75rem',
    full: '9999px',
  },
  shadows: {
    sm: 'none',
    md: '0 2px 4px rgba(0, 0, 0, 0.05)',
    lg: '0 4px 8px rgba(0, 0, 0, 0.05)',
    xl: '0 8px 16px rgba(0, 0, 0, 0.05)',
    '2xl': '0 16px 32px rgba(0, 0, 0, 0.05)',
  },
};