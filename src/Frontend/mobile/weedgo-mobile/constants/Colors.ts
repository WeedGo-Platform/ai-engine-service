// Vibrant, colorful theme for WeedGo
export const Colors = {
  light: {
    // Primary & accent colors - Vibrant greens with gradients
    primary: '#00D084', // Bright mint green
    primaryLight: '#00F5A0', // Light vibrant green
    primaryDark: '#00B371', // Deep mint
    secondary: '#FF6B9D', // Vibrant pink
    accent: '#FFD93D', // Bright yellow

    // Cannabis strain colors - Colorful badges
    strainIndica: '#3B82F6', // Blue (includes Indica Dominant)
    strainSativa: '#FB923C', // Bright orange (includes Sativa Dominant)
    strainHybrid: '#10B981', // Green (Hybrid/Balanced)
    strainBlend: '#A855F7', // Purple (Blends)
    strainCBD: '#06B6D4', // Teal (CBD products)

    // Gradient colors for backgrounds
    gradientStart: '#FFEAA7', // Light yellow
    gradientMid: '#74B9FF', // Sky blue
    gradientEnd: '#A29BFE', // Soft purple

    // Base colors - Bright and clean
    background: '#FFFFFF',
    backgroundSecondary: '#FFF5F7', // Slight pink tint
    surface: '#FFFFFF',
    card: 'rgba(255, 255, 255, 0.95)',

    // Colorful card backgrounds
    cardGradientStart: 'rgba(255, 255, 255, 0.9)',
    cardGradientEnd: 'rgba(250, 250, 255, 0.9)',

    // Text colors - High contrast for clarity
    text: '#2D3436',
    textSecondary: '#636E72',
    textTertiary: '#95A5A6',
    textOnPrimary: '#FFFFFF',

    // Semantic colors - Bright and friendly
    success: '#00B894', // Mint green
    error: '#FF7675', // Soft red
    warning: '#FDCB6E', // Warm yellow
    info: '#74B9FF', // Light blue

    // UI elements
    border: 'rgba(223, 230, 233, 0.6)',
    gray: '#B2BEC3',
    disabled: '#DFE6E9',
    inputBackground: '#F8F9FA',
    star: '#FFC107',

    // Special effects
    shimmer: 'rgba(255, 255, 255, 0.8)',
    glow: 'rgba(0, 240, 132, 0.3)',
    rainbow: 'linear-gradient(90deg, #FF6B9D, #FFD93D, #00D084, #4A90E2, #9D50BB)',

    // Glass morphism - Light and airy
    glass: 'rgba(255, 255, 255, 0.85)',
    glassLight: 'rgba(255, 255, 255, 0.7)',
    glassDark: 'rgba(255, 255, 255, 0.95)',
    glassBorder: 'rgba(255, 255, 255, 0.3)',
    overlay: 'rgba(0, 0, 0, 0.05)',
  },
  dark: {
    // Primary & accent colors - Neon vibrant for dark mode
    primary: '#00FF88', // Neon green
    primaryLight: '#5EFFA5', // Light neon green
    primaryDark: '#00CC6A', // Deep neon green
    secondary: '#FF79C6', // Neon pink
    accent: '#FFE66D', // Bright yellow

    // Cannabis strain colors - Neon variants
    strainIndica: '#60A5FA', // Bright blue
    strainSativa: '#FB923C', // Bright orange
    strainHybrid: '#34D399', // Bright green
    strainBlend: '#C084FC', // Bright purple
    strainCBD: '#22D3EE', // Bright teal

    // Gradient colors for dark backgrounds
    gradientStart: '#667EEA', // Purple blue
    gradientMid: '#764BA2', // Purple
    gradientEnd: '#F093FB', // Pink

    // Base colors - Rich dark with color hints
    background: '#1A1A2E', // Deep blue-black
    backgroundSecondary: '#16213E', // Navy blue
    surface: '#0F3460', // Deep ocean blue
    card: 'rgba(22, 33, 62, 0.95)',

    // Colorful card backgrounds for dark mode
    cardGradientStart: 'rgba(22, 33, 62, 0.9)',
    cardGradientEnd: 'rgba(53, 59, 125, 0.9)',

    // Text colors - High contrast
    text: '#F8F9FA',
    textSecondary: '#CED6E0',
    textTertiary: '#A4B0BE',
    textOnPrimary: '#1A1A2E',

    // Semantic colors - Neon bright
    success: '#50FA7B', // Neon green
    error: '#FF5555', // Bright red
    warning: '#F1FA8C', // Neon yellow
    info: '#8BE9FD', // Cyan

    // UI elements
    border: 'rgba(116, 185, 255, 0.2)',
    gray: '#57606F',
    disabled: '#2F3542',
    inputBackground: 'rgba(53, 59, 125, 0.3)',
    star: '#FFD700',

    // Special effects
    shimmer: 'rgba(255, 255, 255, 0.1)',
    glow: 'rgba(0, 255, 136, 0.4)',
    rainbow: 'linear-gradient(90deg, #FF79C6, #FFE66D, #00FF88, #8BE9FD, #BD93F9)',

    // Glass morphism - Dark with color hints
    glass: 'rgba(30, 30, 50, 0.85)',
    glassLight: 'rgba(30, 30, 50, 0.7)',
    glassDark: 'rgba(30, 30, 50, 0.95)',
    glassBorder: 'rgba(116, 185, 255, 0.15)',
    overlay: 'rgba(0, 0, 0, 0.3)',
  },
};

export const Spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const BorderRadius = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 28,
  full: 9999,
};

export const Typography = {
  sizes: {
    xs: 10,
    sm: 12,
    base: 14,
    md: 16,
    lg: 18,
    xl: 20,
    xxl: 24,
    xxxl: 32,
  },
  weights: {
    regular: '400' as const,
    medium: '500' as const,
    semibold: '600' as const,
    bold: '700' as const,
  },
};

// Glass morphism styles helper
export const GlassStyles = {
  light: {
    backgroundColor: 'rgba(255, 255, 255, 0.72)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.18)',
  },
  dark: {
    backgroundColor: 'rgba(30, 30, 30, 0.72)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
  },
  button: {
    backgroundColor: 'rgba(16, 185, 129, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(16, 185, 129, 0.2)',
  },
  buttonDark: {
    backgroundColor: 'rgba(16, 185, 129, 0.15)',
    borderWidth: 1,
    borderColor: 'rgba(16, 185, 129, 0.25)',
  },
  card: {
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 8,
    },
    shadowOpacity: 0.12,
    shadowRadius: 16,
    elevation: 8,
  },
};

// Shadow presets - Colorful and soft
export const Shadows = {
  small: {
    shadowColor: '#667EEA',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 2,
  },
  medium: {
    shadowColor: '#667EEA',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 4,
  },
  large: {
    shadowColor: '#667EEA',
    shadowOffset: {
      width: 0,
      height: 8,
    },
    shadowOpacity: 0.25,
    shadowRadius: 16,
    elevation: 8,
  },
  colorful: {
    shadowColor: '#FF6B9D',
    shadowOffset: {
      width: 0,
      height: 6,
    },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 6,
  },
};

// Gradient presets for colorful UI
export const Gradients = {
  primary: ['#00D084', '#00F5A0'] as [string, string], // Green gradient
  secondary: ['#FF6B9D', '#FF79C6'] as [string, string], // Pink gradient
  accent: ['#FFD93D', '#FFE66D'] as [string, string], // Yellow gradient
  rainbow: ['#FF6B9D', '#FFD93D', '#00D084', '#4A90E2', '#9D50BB'] as [string, string, string, string, string],
  sunset: ['#FFB86C', '#FF79C6', '#BD93F9'] as [string, string, string],
  ocean: ['#4A90E2', '#00CEC9', '#00D084'] as [string, string, string],
  purple: ['#9D50BB', '#BD93F9', '#D4A5F9'] as [string, string, string],
  warm: ['#FF8C42', '#FFB86C', '#FFE66D'] as [string, string, string],
  cool: ['#4A90E2', '#74B9FF', '#8BE9FD'] as [string, string, string],
  indica: ['#3B82F6', '#2563EB'] as [string, string], // Blue for Indica/Indica Dominant
  sativa: ['#FB923C', '#F97316'] as [string, string], // Bright Orange for Sativa/Sativa Dominant
  hybrid: ['#10B981', '#059669'] as [string, string], // Green for Hybrid/Balanced
  blend: ['#A855F7', '#9333EA'] as [string, string], // Purple for Blends
  cbd: ['#06B6D4', '#0891B2'] as [string, string], // Teal for CBD products
  card: ['rgba(255, 255, 255, 0.95)', 'rgba(250, 250, 255, 0.9)'] as [string, string],
  cardDark: ['rgba(22, 33, 62, 0.95)', 'rgba(53, 59, 125, 0.9)'] as [string, string],
  button: ['#00D084', '#00F5A0', '#00B371'] as [string, string, string],
  buttonSecondary: ['#FF6B9D', '#FF79C6', '#FF5587'] as [string, string, string],
  success: ['#00D084', '#00F5A0'] as [string, string],
  // Background gradients for screens
  darkBackground: ['#1A1A2E', '#16213E', '#0F3460'] as [string, string, string],
  lightBackground: ['#FFFFFF', '#FFF5F7', '#F8F9FA'] as [string, string, string],
};