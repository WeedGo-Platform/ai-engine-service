import { Theme } from '../types';
import { Platform } from 'react-native';

// Headless theme uses system defaults and can be configured via environment
export const HeadlessTheme: Theme = {
  name: 'Headless',
  colors: {
    primary: process.env.EXPO_PUBLIC_THEME_PRIMARY || '#007AFF', // iOS blue
    secondary: process.env.EXPO_PUBLIC_THEME_SECONDARY || '#5856D6', // iOS purple
    accent: process.env.EXPO_PUBLIC_THEME_ACCENT || '#FF9500', // iOS orange
    background: '#F2F2F7', // iOS system background
    surface: '#FFFFFF',
    text: '#000000',
    textSecondary: '#8E8E93',
    error: '#FF3B30',
    warning: '#FF9500',
    success: '#34C759',
    info: '#007AFF',
    border: '#C6C6C8',
    disabled: '#C7C7CC',
    overlay: 'rgba(0, 0, 0, 0.4)',
  },
  typography: {
    fontFamily: {
      regular: Platform.select({
        ios: 'System',
        android: 'Roboto',
        default: 'System',
      }),
      medium: Platform.select({
        ios: 'System',
        android: 'Roboto-Medium',
        default: 'System',
      }),
      bold: Platform.select({
        ios: 'System',
        android: 'Roboto-Bold',
        default: 'System',
      }),
      light: Platform.select({
        ios: 'System',
        android: 'Roboto-Light',
        default: 'System',
      }),
    },
    sizes: {
      h1: 34,
      h2: 28,
      h3: 22,
      body: 17,
      bodySmall: 15,
      caption: 13,
      button: 17,
    },
    lineHeights: {
      h1: 41,
      h2: 34,
      h3: 28,
      body: 22,
      bodySmall: 20,
      caption: 18,
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
    sm: Platform.select({ ios: 6, android: 4, default: 4 }),
    md: Platform.select({ ios: 10, android: 8, default: 8 }),
    lg: Platform.select({ ios: 14, android: 12, default: 12 }),
    xl: Platform.select({ ios: 18, android: 16, default: 16 }),
    round: 999,
  },
  shadows: {
    sm: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: Platform.select({ ios: 0.18, android: 0.2, default: 0.18 }),
      shadowRadius: 1.0,
      elevation: 1,
    },
    md: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: Platform.select({ ios: 0.25, android: 0.3, default: 0.25 }),
      shadowRadius: 3.84,
      elevation: 3,
    },
    lg: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 5 },
      shadowOpacity: Platform.select({ ios: 0.30, android: 0.35, default: 0.30 }),
      shadowRadius: 6.27,
      elevation: 5,
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