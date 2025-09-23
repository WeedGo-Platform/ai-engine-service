export const Colors = {
  light: {
    primary: '#4CAF50',
    primaryLight: '#66BB6A',
    secondary: '#8BC34A',
    accent: '#FF9800',
    success: '#4CAF50',
    error: '#F44336',
    warning: '#FF9800',
    info: '#2196F3',
    text: '#212121',
    textSecondary: '#757575',
    background: '#F5F5F5',
    backgroundSecondary: '#FFFFFF',
    surface: '#FFFFFF',
    border: '#E0E0E0',
    gray: '#9E9E9E',
    disabled: '#BDBDBD',
    card: '#FFFFFF',
    inputBackground: '#F5F5F5',
    star: '#FFB800',
  },
  dark: {
    primary: '#66BB6A',
    secondary: '#9CCC65',
    accent: '#FFB74D',
    success: '#66BB6A',
    error: '#EF5350',
    warning: '#FFB74D',
    info: '#42A5F5',
    text: '#FFFFFF',
    textSecondary: '#B0B0B0',
    background: '#121212',
    backgroundSecondary: '#1E1E1E',
    surface: '#2C2C2C',
    border: '#3C3C3C',
    gray: '#757575',
    disabled: '#616161',
    card: '#2C2C2C',
    inputBackground: '#1E1E1E',
    star: '#FFB800',
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
  sm: 4,
  md: 8,
  lg: 12,
  xl: 16,
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