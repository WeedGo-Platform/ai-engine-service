import type { ITemplate } from '../types';

// Import all Modern components
import { ModernButton } from './components/Button';
import { ModernBadge } from './components/Badge';
import { ModernLogo } from './components/Logo';
import { ModernInput } from './components/Input';
import { ModernSkeleton } from './components/Skeleton';
import { ModernModal } from './components/Modal';
import { ModernHeader } from './components/Header';
import { ModernFooter } from './components/Footer';
import { ModernBreadcrumbs } from './components/Breadcrumbs';
import { ModernSearchBar } from './components/SearchBar';
import { ModernFilterPanel } from './components/FilterPanel';
import { ModernAdvancedSearch } from './components/AdvancedSearch';
import { ModernProductCard } from './components/ProductCard';
import { ModernProductRecommendations } from './components/ProductRecommendations';
import { ModernCartItem } from './components/CartItem';
import { ModernChatInterface } from './components/ChatInterface';
import { ModernChatBubble } from './components/ChatBubble';
import { ModernProductReviews } from './components/ProductReviews';
import { ModernReviewForm } from './components/ReviewForm';
import { ModernReviewItem } from './components/ReviewItem';
import { ModernLoadingScreen } from './components/LoadingScreen';
import { ModernOptimizedImage } from './components/OptimizedImage';
import { ModernStoreSelector } from './components/StoreSelector';
import { ModernLanguageSelector } from './components/LanguageSelector';
import { ModernWishlistButton } from './components/WishlistButton';
import { ModernErrorBoundary } from './components/ErrorBoundary';
import { ModernHero } from './components/Hero';
import { ModernCategoryCard } from './components/CategoryCard';

export const ModernTemplate: ITemplate = {
  name: 'modern',
  theme: {
    colors: {
      // Space Gray inspired palette - Apple-like sophisticated design
      primary: '#1D1D1F',        // Space gray primary
      secondary: '#86868B',      // System gray
      accent: '#0A84FF',         // System blue accent
      background: '#F5F5F7',     // Light gray background
      surface: '#FFFFFF',        // Pure white surfaces with subtle shadows
      text: '#1D1D1F',           // Dark space gray text
      textSecondary: '#86868B',  // Medium gray text
      border: '#D2D2D7',         // Light gray borders
      error: '#FF3B30',          // System red
      success: '#34C759',        // System green
      warning: '#FF9500',        // System orange
      info: '#0A84FF'            // System blue
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
  components: {
    // Core UI Components
    Button: ModernButton,
    Input: ModernInput,
    Badge: ModernBadge,
    Logo: ModernLogo,
    Skeleton: ModernSkeleton,
    Modal: ModernModal,

    // Navigation Components
    Header: ModernHeader,
    Footer: ModernFooter,
    Breadcrumbs: ModernBreadcrumbs,

    // Search & Filter Components
    SearchBar: ModernSearchBar,
    FilterPanel: ModernFilterPanel,
    AdvancedSearch: ModernAdvancedSearch,

    // Product Components
    ProductCard: ModernProductCard,
    ProductRecommendations: ModernProductRecommendations,

    // Cart Components
    CartItem: ModernCartItem,

    // Chat Components
    ChatInterface: ModernChatInterface,
    ChatBubble: ModernChatBubble,

    // Review Components
    ProductReviews: ModernProductReviews,
    ReviewForm: ModernReviewForm,
    ReviewItem: ModernReviewItem,

    // Common Components
    LoadingScreen: ModernLoadingScreen,
    OptimizedImage: ModernOptimizedImage,
    StoreSelector: ModernStoreSelector,
    LanguageSelector: ModernLanguageSelector,
    WishlistButton: ModernWishlistButton,
    ErrorBoundary: ModernErrorBoundary,

    // Layout Components
    Hero: ModernHero,
    CategoryCard: ModernCategoryCard
  }
};