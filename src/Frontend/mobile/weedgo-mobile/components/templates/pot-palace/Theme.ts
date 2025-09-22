import { Theme } from '../types';

export const PotPalaceTheme: Theme = {
  name: 'Pot Palace',
  colors: {
    primary: '#4CAF50', // Cannabis Green
    secondary: '#9C27B0', // Purple Haze
    accent: '#FFD700', // Gold Leaf
    background: '#F5F5DC', // Beige
    surface: '#FFFFFF',
    text: '#1B5E20', // Dark Green
    textSecondary: '#558B2F',
    error: '#F44336',
    warning: '#FF9800',
    success: '#4CAF50',
    info: '#2196F3',
    border: '#E0E0E0',
    disabled: '#BDBDBD',
    overlay: 'rgba(27, 94, 32, 0.5)',
  },
  typography: {
    fontFamily: {
      regular: 'System',
      medium: 'System',
      bold: 'System',
      light: 'System',
    },
    sizes: {
      h1: 32,
      h2: 24,
      h3: 20,
      body: 16,
      bodySmall: 14,
      caption: 12,
      button: 16,
    },
    lineHeights: {
      h1: 40,
      h2: 32,
      h3: 28,
      body: 24,
      bodySmall: 20,
      caption: 16,
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
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    round: 999,
  },
  shadows: {
    sm: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.1,
      shadowRadius: 4,
      elevation: 2,
    },
    md: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.15,
      shadowRadius: 8,
      elevation: 4,
    },
    lg: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 8 },
      shadowOpacity: 0.2,
      shadowRadius: 16,
      elevation: 8,
    },
  },
  animation: {
    duration: {
      fast: 200,
      normal: 300,
      slow: 500,
    },
    easing: {
      standard: 'cubic-bezier(0.4, 0.0, 0.2, 1)',
      decelerate: 'cubic-bezier(0.0, 0.0, 0.2, 1)',
      accelerate: 'cubic-bezier(0.4, 0.0, 1, 1)',
      sharp: 'cubic-bezier(0.4, 0.0, 0.6, 1)',
    },
  },
};