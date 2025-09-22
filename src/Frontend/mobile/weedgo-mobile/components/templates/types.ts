export interface ColorScheme {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  surface: string;
  text: string;
  textSecondary: string;
  error: string;
  warning: string;
  success: string;
  info: string;
  border: string;
  disabled: string;
  overlay: string;
}

export interface Typography {
  fontFamily: {
    regular: string;
    medium: string;
    bold: string;
    light?: string;
  };
  sizes: {
    h1: number;
    h2: number;
    h3: number;
    body: number;
    bodySmall: number;
    caption: number;
    button: number;
  };
  lineHeights: {
    h1: number;
    h2: number;
    h3: number;
    body: number;
    bodySmall: number;
    caption: number;
  };
}

export interface SpacingScale {
  xs: number;
  sm: number;
  md: number;
  lg: number;
  xl: number;
  xxl: number;
}

export interface BorderRadius {
  sm: number;
  md: number;
  lg: number;
  xl: number;
  round: number;
}

export interface Shadows {
  sm: {
    shadowColor: string;
    shadowOffset: { width: number; height: number };
    shadowOpacity: number;
    shadowRadius: number;
    elevation: number;
  };
  md: {
    shadowColor: string;
    shadowOffset: { width: number; height: number };
    shadowOpacity: number;
    shadowRadius: number;
    elevation: number;
  };
  lg: {
    shadowColor: string;
    shadowOffset: { width: number; height: number };
    shadowOpacity: number;
    shadowRadius: number;
    elevation: number;
  };
}

export interface Animation {
  duration: {
    fast: number;
    normal: number;
    slow: number;
  };
  easing: {
    standard: string;
    decelerate: string;
    accelerate: string;
    sharp: string;
  };
}

export interface Theme {
  name: string;
  colors: ColorScheme;
  typography: Typography;
  spacing: SpacingScale;
  borderRadius: BorderRadius;
  shadows: Shadows;
  animation: Animation;
}

export type TemplateType = 'pot-palace' | 'modern' | 'headless';