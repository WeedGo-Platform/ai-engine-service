import type { ITemplate } from '../types';

export const ModernTemplate: ITemplate = {
  name: 'modern',
  theme: {
    colors: {
      // Premium purple and gold theme with sophisticated accents
      primary: '#1A0B2E',        // Deep midnight purple
      secondary: '#6366F1',      // Electric indigo
      accent: '#F59E0B',         // Luxe gold
      background: '#FAF9FC',     // Soft lavender white
      surface: '#FFFFFF',        // Pure white surfaces
      text: '#1A1F2E',          // Rich dark text
      textSecondary: '#64748B', // Muted gray text
      border: '#E0E1F6',        // Light purple-gray borders
      error: '#DC2626',
      success: '#8B5CF6',       // Purple success
      warning: '#F59E0B',
      info: '#3B82F6'
    },
    spacing: {
      xs: '0.5rem',
      sm: '0.75rem',
      md: '1.25rem',
      lg: '2rem',
      xl: '3rem',
      '2xl': '4rem'
    },
    borderRadius: {
      none: '0',
      sm: '0.25rem',
      md: '0.5rem',
      lg: '0.75rem',
      xl: '1rem',
      full: '9999px'
    },
    shadows: {
      sm: '0 2px 4px 0 rgba(0, 0, 0, 0.03)',
      md: '0 4px 8px 0 rgba(0, 0, 0, 0.06)',
      lg: '0 10px 25px 0 rgba(0, 0, 0, 0.08)',
      xl: '0 25px 50px -12px rgba(0, 0, 0, 0.15)'
    },
    cssVariables: true
  },
  layout: {
    maxWidth: '1440px',
    headerHeight: '72px',
    footerHeight: '240px',
    mobileBreakpoint: '640px',
    tabletBreakpoint: '1024px'
  },
  animations: {
    defaultDuration: 300,
    defaultEasing: 'cubic-bezier(0.4, 0, 0.2, 1)',
    pageTransition: 'slide',
    cardHover: 'lift',
    buttonPress: 'subtle'
  },
  typography: {
    fontFamily: {
      sans: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      display: "'Poppins', sans-serif",
      mono: "'Fira Code', 'Courier New', monospace"
    },
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      '2xl': '1.75rem',
      '3xl': '2.25rem',
      '4xl': '3rem',
      '5xl': '4rem'
    },
    fontWeight: {
      light: 300,
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700
    },
    lineHeight: {
      tight: 1.2,
      normal: 1.6,
      relaxed: 1.8
    }
  },
  components: {} // Will be populated with actual component overrides
};