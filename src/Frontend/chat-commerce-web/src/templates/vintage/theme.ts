import type { ITheme } from '../../core/contracts/template.contracts';

export const vintageTheme: ITheme = {
  name: 'Vintage',
  mode: 'light',
  colors: {
    primary: '#8B4513',
    primaryLight: '#A0522D',
    primaryDark: '#654321',
    secondary: '#D2691E',
    accent: '#DEB887',
    
    success: '#556B2F',
    warning: '#DAA520',
    error: '#CD5C5C',
    info: '#708090',
    
    background: 'linear-gradient(135deg, #F5E6D3 0%, #E6D7C3 100%)',
    surface: '#FFF8DC',
    text: '#3E2723',
    textSecondary: '#5D4037',
    border: '#D2B48C',
    
    userMessage: '#F5DEB3',
    assistantMessage: '#FAEBD7',
    systemMessage: '#FFE4B5',
  },
  typography: {
    fontFamily: {
      body: "Georgia, 'Times New Roman', serif",
      heading: "Georgia, 'Times New Roman', serif",
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
    sm: '0.5rem',
    md: '0.75rem',
    lg: '1rem',
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