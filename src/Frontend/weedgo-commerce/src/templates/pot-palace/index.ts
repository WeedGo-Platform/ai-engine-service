import type { ITemplate } from '../types';

// Import all Pot Palace components
import { PotPalaceButton } from './components/Button';
import { PotPalaceBadge } from './components/Badge';
import { PotPalaceLogo } from './components/Logo';
import { PotPalaceInput } from './components/Input';
import { PotPalaceSkeleton } from './components/Skeleton';
import { PotPalaceModal } from './components/Modal';
import { PotPalaceHeader } from './components/Header';
import { PotPalaceFooter } from './components/Footer';
import { PotPalaceBreadcrumbs } from './components/Breadcrumbs';
import { PotPalaceSearchBar } from './components/SearchBar';
import { PotPalaceFilterPanel } from './components/FilterPanel';
import { PotPalaceAdvancedSearch } from './components/AdvancedSearch';
import { PotPalaceProductCard } from './components/ProductCard';
import { PotPalaceProductRecommendations } from './components/ProductRecommendations';
import { PotPalaceCartItem } from './components/CartItem';
import { PotPalaceChatInterface } from './components/ChatInterface';
import { PotPalaceChatBubble } from './components/ChatBubble';
import { PotPalaceProductReviews } from './components/ProductReviews';
import { PotPalaceReviewForm } from './components/ReviewForm';
import { PotPalaceReviewItem } from './components/ReviewItem';
import { PotPalaceLoadingScreen } from './components/LoadingScreen';
import { PotPalaceOptimizedImage } from './components/OptimizedImage';
import { PotPalaceStoreSelector } from './components/StoreSelector';
import { PotPalaceLanguageSelector } from './components/LanguageSelector';
import { PotPalaceWishlistButton } from './components/WishlistButton';
import { PotPalaceErrorBoundary } from './components/ErrorBoundary';
import { PotPalaceHero } from './components/Hero';
import { PotPalaceCategoryCard } from './components/CategoryCard';

export const PotPalaceTemplate: ITemplate = {
  name: 'pot-palace',
  theme: {
    colors: {
      // Professional, calm earth-tone palette
      primary: '#2D5F3F',        // Deep forest green
      secondary: '#7A9E88',      // Muted sage green
      accent: '#C9A86A',         // Warm gold accent
      background: '#FAFAF8',     // Off-white background
      surface: '#FFFFFF',        // Pure white surfaces
      text: '#1F2937',           // Charcoal gray text
      textSecondary: '#6B7280',  // Medium gray text
      border: '#E5E7EB',         // Light gray borders
      error: '#DC2626',
      success: '#059669',
      warning: '#D97706',
      info: '#0891B2'
    },
    spacing: {
      xs: '0.25rem',
      sm: '0.5rem',
      md: '1rem',
      lg: '1.5rem',
      xl: '2rem',
      '2xl': '3rem'
    },
    borderRadius: {
      none: '0',
      sm: '0.375rem',
      md: '0.5rem',
      lg: '0.75rem',
      xl: '1rem',
      full: '9999px'
    },
    shadows: {
      sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
      md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
      lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
      xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1)'
    },
    cssVariables: true
  },
  layout: {
    maxWidth: '1280px',
    headerHeight: '80px',
    footerHeight: '280px',
    sidebarWidth: '300px',
    mobileBreakpoint: '640px',
    tabletBreakpoint: '1024px'
  },
  animations: {
    defaultDuration: 300,
    defaultEasing: 'cubic-bezier(0.4, 0, 0.2, 1)', // Smooth, professional easing
    pageTransition: 'fade',
    cardHover: 'subtle-lift',
    buttonPress: 'subtle-scale'
  },
  typography: {
    fontFamily: {
      sans: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      display: "'Playfair Display', serif",
      mono: "'Source Code Pro', monospace"
    },
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      '2xl': '1.5rem',
      '3xl': '1.875rem',
      '4xl': '2.25rem',
      '5xl': '3rem'
    },
    fontWeight: {
      light: 300,
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700
    },
    lineHeight: {
      tight: 1.25,
      normal: 1.5,
      relaxed: 1.75
    }
  },
  components: {
    // Core UI Components
    Button: PotPalaceButton,
    Input: PotPalaceInput,
    Badge: PotPalaceBadge,
    Logo: PotPalaceLogo,
    Skeleton: PotPalaceSkeleton,
    Modal: PotPalaceModal,

    // Navigation Components
    Header: PotPalaceHeader,
    Footer: PotPalaceFooter,
    Breadcrumbs: PotPalaceBreadcrumbs,

    // Search & Filter Components
    SearchBar: PotPalaceSearchBar,
    FilterPanel: PotPalaceFilterPanel,
    AdvancedSearch: PotPalaceAdvancedSearch,

    // Product Components
    ProductCard: PotPalaceProductCard,
    ProductRecommendations: PotPalaceProductRecommendations,

    // Cart Components
    CartItem: PotPalaceCartItem,

    // Chat Components
    ChatInterface: PotPalaceChatInterface,
    ChatBubble: PotPalaceChatBubble,

    // Review Components
    ProductReviews: PotPalaceProductReviews,
    ReviewForm: PotPalaceReviewForm,
    ReviewItem: PotPalaceReviewItem,

    // Common Components
    LoadingScreen: PotPalaceLoadingScreen,
    OptimizedImage: PotPalaceOptimizedImage,
    StoreSelector: PotPalaceStoreSelector,
    LanguageSelector: PotPalaceLanguageSelector,
    WishlistButton: PotPalaceWishlistButton,
    ErrorBoundary: PotPalaceErrorBoundary,

    // Layout Components
    Hero: PotPalaceHero,
    CategoryCard: PotPalaceCategoryCard
  }
};