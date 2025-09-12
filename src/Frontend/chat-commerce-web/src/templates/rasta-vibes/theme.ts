import type { ITheme } from '../../core/contracts/template.contracts';

export const rastaVibesTheme: ITheme = {
  name: 'Rasta Vibes',
  mode: 'dark',
  colors: {
    // Rastafarian flag colors
    primary: '#FCD34D', // Gold - Primary
    primaryLight: '#FDE68A', // Light Gold
    primaryDark: '#F59E0B', // Dark Gold
    secondary: '#16A34A', // Green
    accent: '#DC2626', // Red
    
    // Status colors with Rasta influence
    success: '#16A34A', // Green
    warning: '#FCD34D', // Gold
    error: '#DC2626', // Red
    info: '#059669', // Deep Green
    
    // Background colors - warm earth tones
    background: 'linear-gradient(135deg, #1A1A1A 0%, #2D1B00 50%, #1A2E05 100%)',
    surface: 'rgba(26, 26, 26, 0.95)',
    text: '#FCD34D', // Gold text
    textSecondary: '#F3E7C3', // Light gold/cream
    border: 'rgba(252, 211, 77, 0.3)', // Gold border with transparency
    
    // Message bubble colors with gradient effects
    userMessage: 'linear-gradient(135deg, rgba(22, 163, 74, 0.2) 0%, rgba(22, 163, 74, 0.1) 100%)',
    assistantMessage: 'linear-gradient(135deg, rgba(252, 211, 77, 0.15) 0%, rgba(252, 211, 77, 0.05) 100%)',
    systemMessage: 'linear-gradient(135deg, rgba(220, 38, 38, 0.15) 0%, rgba(220, 38, 38, 0.05) 100%)',
  },
  typography: {
    fontFamily: {
      body: '"Rubik", "Ubuntu", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      heading: '"Bebas Neue", "Rubik", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      mono: '"Fira Code", "JetBrains Mono", monospace',
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
    xl: '1.5rem',
    full: '9999px',
  },
  shadows: {
    sm: '0 2px 4px rgba(252, 211, 77, 0.1)',
    md: '0 4px 8px rgba(252, 211, 77, 0.15), 0 0 20px rgba(252, 211, 77, 0.05)',
    lg: '0 8px 16px rgba(252, 211, 77, 0.2), 0 0 30px rgba(252, 211, 77, 0.1)',
    xl: '0 16px 32px rgba(252, 211, 77, 0.25), 0 0 40px rgba(252, 211, 77, 0.15)',
    '2xl': '0 24px 48px rgba(252, 211, 77, 0.3), 0 0 60px rgba(252, 211, 77, 0.2)',
  },
};