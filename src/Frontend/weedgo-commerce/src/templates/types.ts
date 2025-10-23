import React from 'react';

// ========================================
// Component Props Interfaces
// ========================================

// Core UI Components
export interface IButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  className?: string;
  type?: 'button' | 'submit' | 'reset';
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
  icon?: React.ReactNode;
}

export interface IBadgeProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'warning' | 'info';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  className?: string;
}

export interface ILogoProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'full' | 'icon';
  className?: string;
}

export interface ISkeletonProps {
  width?: string | number;
  height?: string | number;
  variant?: 'text' | 'circular' | 'rectangular';
  className?: string;
  animation?: 'pulse' | 'wave' | 'none';
}

// Navigation Components
export interface IHeaderProps {
  onChatToggle?: () => void;
  className?: string;
}

export interface IFooterProps {
  className?: string;
}

export interface IBreadcrumbsProps {
  items: Array<{
    label: string;
    href?: string;
  }>;
  separator?: React.ReactNode;
  className?: string;
}

// Search & Filter Components
export interface ISearchBarProps {
  value?: string;
  onChange?: (value: string) => void;
  onSearch?: (query: string) => void;
  placeholder?: string;
  variant?: 'default' | 'compact' | 'minimal';
  className?: string;
  showSuggestions?: boolean;
  showButton?: boolean;
}

export interface IFilterPanelProps {
  filters: IFilter[];
  onFilterChange: (filters: IFilter[]) => void;
  className?: string;
}

export interface IAdvancedSearchProps {
  onSearch: (criteria: ISearchCriteria) => void;
  categories?: string[];
  brands?: string[];
  className?: string;
}

// Product Components
export interface IProductCardProps {
  product: IProduct;
  onAddToCart: (product: IProduct) => void;
  onQuickView?: (product: IProduct) => void;
  variant?: 'default' | 'compact' | 'detailed';
  className?: string;
}

export interface IProductRecommendationsProps {
  productId?: string;
  type?: 'similar' | 'complementary' | 'trending' | 'personalized';
  limit?: number;
  className?: string;
}

// Cart Components
export interface ICartItemProps {
  item: ICartItem;
  onUpdateQuantity: (id: string, quantity: number) => void;
  onRemove: (id: string) => void;
  variant?: 'default' | 'compact';
  className?: string;
}

// Chat Components
export interface IChatInterfaceProps {
  isOpen?: boolean;
  onClose?: () => void;
  position?: 'bottom-right' | 'bottom-left' | 'center';
  className?: string;
}

export interface IChatBubbleProps {
  message: IChatMessage;
  isUser: boolean;
  showAvatar?: boolean;
  className?: string;
}

// Review Components
export interface IProductReviewsProps {
  productId: string;
  reviews?: IReview[];
  onReviewSubmit?: (review: IReview) => void;
  className?: string;
}

export interface IReviewFormProps {
  productId: string;
  onSubmit: (review: IReview) => void;
  onCancel?: () => void;
  className?: string;
}

export interface IReviewItemProps {
  review: IReview;
  onHelpful?: (reviewId: string) => void;
  onReport?: (reviewId: string) => void;
  className?: string;
}

// Common Components
export interface IModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  title?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  closeOnOverlayClick?: boolean;
  className?: string;
}

export interface ILoadingScreenProps {
  message?: string;
  variant?: 'spinner' | 'dots' | 'bars' | 'pulse';
  fullScreen?: boolean;
  className?: string;
}

export interface IOptimizedImageProps {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  loading?: 'lazy' | 'eager';
  fallback?: string;
  className?: string;
}

export interface IStoreSelectorProps {
  selectedStoreId?: string;
  onStoreChange?: (storeId: string) => void;
  variant?: 'dropdown' | 'modal' | 'inline';
  className?: string;
}

export interface ILanguageSelectorProps {
  currentLanguage?: string;
  languages?: Array<{ code: string; label: string; flag?: string }>;
  onLanguageChange?: (language: string) => void;
  className?: string;
}

export interface IWishlistButtonProps {
  productId: string;
  isWishlisted?: boolean;
  onToggle?: (productId: string) => void;
  variant?: 'icon' | 'text' | 'both';
  className?: string;
}

export interface IErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  className?: string;
}

// Layout Components
export interface IHeroProps {
  title?: string;
  subtitle?: string;
  backgroundImage?: string;
  cta?: {
    text: string;
    action: () => void;
  };
  primaryButton?: {
    text: string;
    href?: string;
    onClick?: () => void;
  };
  secondaryButton?: {
    text: string;
    href?: string;
    onClick?: () => void;
  };
  className?: string;
}

export interface ICategoryCardProps {
  category: ICategory;
  onClick?: (category: ICategory) => void;
  variant?: 'default' | 'featured' | 'compact';
  className?: string;
  // Additional props for direct usage
  title?: string;
  description?: string;
  icon?: string;
  image?: string;
}

// ========================================
// Data Models
// ========================================

export interface IProduct {
  id: string;
  sku: string;
  slug: string;
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
  // Additional optional properties for compatibility
  strain?: string;
  size?: number;
  thc?: number; // Alias for thc_content
  cbd?: number; // Alias for cbd_content
}

export interface ICartItem {
  id: string;
  product: IProduct;
  quantity: number;
  price: number;
  // Additional optional properties for legacy compatibility
  image?: string;
  name?: string;
  sku?: string;
  brand?: string;
  size?: number;
  weight?: number;
  unit?: string;
  category?: string;
  strain?: string;
  thc?: number;
  cbd?: number;
  maxQuantity?: number;
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

export interface IReview {
  id: string;
  productId: string;
  userId: string;
  userName: string;
  rating: number;
  title?: string;
  comment: string;
  helpful: number;
  verified: boolean;
  createdAt: Date;
}

export interface IFilter {
  id: string;
  type: 'category' | 'brand' | 'price' | 'thc' | 'cbd' | 'effect';
  label: string;
  value: any;
  active: boolean;
}

export interface ISearchCriteria {
  query?: string;
  categories?: string[];
  brands?: string[];
  priceRange?: { min: number; max: number };
  thcRange?: { min: number; max: number };
  cbdRange?: { min: number; max: number };
  effects?: string[];
  inStockOnly?: boolean;
}

export interface ICategory {
  id: string;
  name: string;
  slug: string;
  description?: string;
  image?: string;
  productCount?: number;
}

// ========================================
// Template Configuration
// ========================================

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

// Complete Component Map for Templates
export interface IComponentMap {
  // Core UI Components
  Button: React.FC<IButtonProps>;
  Input: React.FC<IInputProps>;
  Badge: React.FC<IBadgeProps>;
  Logo: React.FC<ILogoProps>;
  Skeleton: React.FC<ISkeletonProps>;
  Modal: React.FC<IModalProps>;

  // Navigation Components
  Header: React.FC<IHeaderProps>;
  Footer: React.FC<IFooterProps>;
  Breadcrumbs: React.FC<IBreadcrumbsProps>;

  // Search & Filter Components
  SearchBar: React.FC<ISearchBarProps>;
  FilterPanel: React.FC<IFilterPanelProps>;
  AdvancedSearch: React.FC<IAdvancedSearchProps>;

  // Product Components
  ProductCard: React.FC<IProductCardProps>;
  ProductRecommendations: React.FC<IProductRecommendationsProps>;

  // Cart Components
  CartItem: React.FC<ICartItemProps>;

  // Chat Components
  ChatInterface: React.FC<IChatInterfaceProps>;
  ChatBubble: React.FC<IChatBubbleProps>;

  // Review Components
  ProductReviews: React.FC<IProductReviewsProps>;
  ReviewForm: React.FC<IReviewFormProps>;
  ReviewItem: React.FC<IReviewItemProps>;

  // Common Components
  LoadingScreen: React.FC<ILoadingScreenProps>;
  OptimizedImage: React.FC<IOptimizedImageProps>;
  StoreSelector: React.FC<IStoreSelectorProps>;
  LanguageSelector: React.FC<ILanguageSelectorProps>;
  WishlistButton: React.FC<IWishlistButtonProps>;
  ErrorBoundary: React.FC<IErrorBoundaryProps>;

  // Layout Components
  Hero: React.FC<IHeroProps>;
  CategoryCard: React.FC<ICategoryCardProps>;
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
    display?: string;
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