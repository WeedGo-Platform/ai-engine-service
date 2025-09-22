import { Theme } from '../types';

export const ModernTheme: Theme = {
  name: 'Modern Medical',
  colors: {
    primary: '#2196F3', // Medical Blue
    secondary: '#757575', // Grey
    accent: '#00BCD4', // Cyan
    background: '#FAFAFA',
    surface: '#FFFFFF',
    text: '#212121',
    textSecondary: '#757575',
    error: '#D32F2F',
    warning: '#F57C00',
    success: '#388E3C',
    info: '#1976D2',
    border: '#E0E0E0',
    disabled: '#BDBDBD',
    overlay: 'rgba(33, 33, 33, 0.4)',
  },
  typography: {
    fontFamily: {
      regular: 'System',
      medium: 'System',
      bold: 'System',
      light: 'System',
    },
    sizes: {
      h1: 28,
      h2: 20,
      h3: 18,
      body: 14,
      bodySmall: 12,
      caption: 11,
      button: 14,
    },
    lineHeights: {
      h1: 36,
      h2: 28,
      h3: 24,
      body: 20,
      bodySmall: 16,
      caption: 14,
    },
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
  },
  borderRadius: {
    sm: 2,
    md: 4,
    lg: 8,
    xl: 12,
    round: 999,
  },
  shadows: {
    sm: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.05,
      shadowRadius: 2,
      elevation: 1,
    },
    md: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.08,
      shadowRadius: 4,
      elevation: 2,
    },
    lg: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.12,
      shadowRadius: 8,
      elevation: 4,
    },
  },
  animation: {
    duration: {
      fast: 150,
      normal: 250,
      slow: 400,
    },
    easing: {
      standard: 'cubic-bezier(0.4, 0.0, 0.2, 1)',
      decelerate: 'cubic-bezier(0.0, 0.0, 0.2, 1)',
      accelerate: 'cubic-bezier(0.4, 0.0, 1, 1)',
      sharp: 'cubic-bezier(0.4, 0.0, 0.6, 1)',
    },
  },
};