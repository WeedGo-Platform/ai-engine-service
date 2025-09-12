import type { ITheme } from '../../core/contracts/template.contracts';

export const weedgoTheme: ITheme = {
  name: 'WeedGo',
  mode: 'light',
  colors: {
    primary: '#DC2626', // Red - primary brand color
    primaryLight: '#EF4444',
    primaryDark: '#B91C1C',
    secondary: '#1E40AF', // Deep Blue - for primary buttons/CTAs
    accent: '#2563EB', // Lighter blue for accents
    
    success: '#16A34A',
    warning: '#EA580C',
    error: '#DC2626',
    info: '#2563EB',
    
    background: '#FFFFFF', // Pure white background
    surface: '#FFFFFF', // Pure white surface
    text: '#1F2937', // Dark gray text
    textSecondary: '#6B7280', // Medium gray text
    border: '#E5E7EB', // Light gray borders
    
    userMessage: '#EFF6FF', // Very light blue for user messages
    assistantMessage: '#FFFFFF', // White for assistant messages
    systemMessage: '#FEF3C7', // Light yellow for system messages
  },
  typography: {
    fontFamily: {
      body: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      heading: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
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