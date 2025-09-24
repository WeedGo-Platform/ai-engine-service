import React from 'react';

// Component Props Interfaces
export interface IProductCardProps {
  product: IProduct;
  onAddToCart: (product: IProduct) => void;
  onQuickView?: (product: IProduct) => void;
}

export interface ICartItemProps {
  item: ICartItem;
  onUpdateQuantity: (id: string, quantity: number) => void;
  onRemove: (id: string) => void;
}

export interface IChatBubbleProps {
  message: IChatMessage;
  isUser: boolean;
}

export interface IButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
  className?: string;
}

export interface IInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: string;
  error?: string;
  label?: string;
  required?: boolean;
  disabled?: boolean;
  className?: string;
}

export interface IModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  title?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

// Data Models
export interface IProduct {
  id: string;
  sku: string;
  slug: string; // SEO-friendly URL slug
  name: string;
  description: string;
  category: string;
  brand: string;
  price: number;
  sale_price?: number;
  thc_content: number;
  cbd_content: number;
  terpenes?: string[];
  effects?: string[];
  image_url: string;
  images?: string[];
  in_stock: boolean;
  quantity_available: number;
  unit_weight?: string;
  rating?: number;
  reviews_count?: number;
}

export interface ICartItem {
  id: string;
  product: IProduct;
  quantity: number;
  price: number;
}

export interface IChatMessage {
  id: string;
  text: string;
  timestamp: Date;
  isUser: boolean;
  products?: IProduct[];
  actions?: IMessageAction[];
}

export interface IMessageAction {
  label: string;
  action: string;
  data?: any;
}

// Template Configuration
export interface ITemplate {
  name: string;
  theme: ITheme;
  layout: ILayout;
  components: IComponentMap;
  animations: IAnimationConfig;
  typography: ITypography;
}

export interface ITheme {
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    border: string;
    error: string;
    success: string;
    warning: string;
    info: string;
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    '2xl': string;
  };
  borderRadius: {
    none: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    full: string;
  };
  shadows: {
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
  cssVariables?: boolean;
}

export interface ILayout {
  maxWidth: string;
  headerHeight: string;
  footerHeight: string;
  sidebarWidth?: string;
  mobileBreakpoint: string;
  tabletBreakpoint: string;
}

export interface IComponentMap {
  ProductCard: React.FC<IProductCardProps>;
  CartItem: React.FC<ICartItemProps>;
  ChatBubble: React.FC<IChatBubbleProps>;
  Button: React.FC<IButtonProps>;
  Input: React.FC<IInputProps>;
  Modal: React.FC<IModalProps>;
  Header: React.FC;
  Footer: React.FC;
  Hero: React.FC;
  CategoryCard: React.FC<any>;
}

export interface IAnimationConfig {
  defaultDuration: number;
  defaultEasing: string;
  pageTransition: string;
  cardHover: string;
  buttonPress: string;
}

export interface ITypography {
  fontFamily: {
    sans: string;
    serif?: string;
    mono?: string;
  };
  fontSize: {
    xs: string;
    sm: string;
    base: string;
    lg: string;
    xl: string;
    '2xl': string;
    '3xl': string;
    '4xl': string;
    '5xl': string;
  };
  fontWeight: {
    light: number;
    normal: number;
    medium: number;
    semibold: number;
    bold: number;
  };
  lineHeight: {
    tight: number;
    normal: number;
    relaxed: number;
  };
}