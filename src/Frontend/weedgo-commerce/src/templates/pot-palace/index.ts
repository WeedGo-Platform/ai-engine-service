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
      // Vibrant, playful cannabis-inspired color palette
      primary: '#2E7D32',        // Cannabis green
      secondary: '#FDD835',       // Sunny yellow
      accent: '#8B4513',          // Earthy brown
      background: '#FFF8E1',      // Warm cream background
      surface: '#FFFFFF',         // White surfaces
      text: '#212121',           // Dark gray text
      textSecondary: '#757575',  // Medium gray text
      border: '#BDBDBD',         // Light gray borders
      error: '#F44336',
      success: '#4CAF50',
      warning: '#FF9800',
      info: '#03A9F4'
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
      sm: '0.25rem',
      md: '0.5rem',
      lg: '1rem',
      xl: '1.5rem',
      full: '9999px'
    },
    shadows: {
      sm: '0 1px 3px rgba(0, 0, 0, 0.12)',
      md: '0 4px 6px rgba(0, 0, 0, 0.15)',
      lg: '0 10px 20px rgba(0, 0, 0, 0.18)',
      xl: '0 20px 40px rgba(0, 0, 0, 0.22)'
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
    defaultDuration: 400,
    defaultEasing: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)', // Bouncy feel
    pageTransition: 'bounce',
    cardHover: 'grow',
    buttonPress: 'bounce'
  },
  typography: {
    fontFamily: {
      sans: "'Rubik', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      display: "'Bebas Neue', cursive",
      mono: "'Source Code Pro', monospace"
    },
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      '2xl': '1.5rem',
      '3xl': '2rem',
      '4xl': '2.5rem',
      '5xl': '3.5rem'
    },
    fontWeight: {
      light: 300,
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700
    },
    lineHeight: {
      tight: 1.1,
      normal: 1.5,
      relaxed: 1.7
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