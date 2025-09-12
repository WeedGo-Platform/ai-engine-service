import { Product } from '../services/productSearch';

// Product Details Component Props
export interface ProductDetailsProps {
  product: Product;
  onClose?: () => void;
  onAddToCart?: (product: Product, quantity: number) => Promise<void>;
  showRecommendations?: boolean;
}

// Product Recommendations Props
export interface ProductRecommendationsProps {
  currentProduct: Product;
  onProductSelect?: (product: Product) => void;
  onAddToCart?: (product: Product, quantity: number) => Promise<void>;
  maxRecommendations?: number;
}

// Product Recommendation Interface
export interface ProductRecommendation extends Product {
  relevanceScore?: number;
  reason?: string; // Why this product is recommended
}

// Quantity Selector Props
export interface QuantitySelectorProps {
  quantity: number;
  onQuantityChange: (quantity: number) => void;
  min?: number;
  max?: number;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

// Product Details Message for Chat
export interface ProductDetailsMessage {
  type: 'product-details';
  product: Product;
  timestamp: Date;
}

// Extended Message Type for Chat
export interface ExtendedMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string | ProductDetailsMessage;
  timestamp: Date;
  responseTime?: number;
  tokens?: number;
  tokensPerSec?: number;
  promptUsed?: string;
  toolsUsed?: string[];
  model?: string;
  agent?: string;
  personality?: string;
  metadata?: any;
}

// Product Card Props for inline display
export interface ProductCardProps {
  product: Product;
  variant?: 'compact' | 'full' | 'minimal';
  showActions?: boolean;
  onViewDetails?: (product: Product) => void;
  onAddToCart?: (product: Product, quantity: number) => Promise<void>;
}

// Terpene Profile Display
export interface TerpeneProfileProps {
  terpenes?: string[];
  showDescriptions?: boolean;
}

// Stock Status Display
export interface StockStatusProps {
  inStock?: boolean;
  quantity?: number;
  showQuantity?: boolean;
}

// Product Image Gallery
export interface ProductImageGalleryProps {
  images: string[];
  productName: string;
  thumbnailPosition?: 'left' | 'bottom' | 'right';
}

// Effects and Feelings Display
export interface ProductEffectsProps {
  effects?: string[];
  feelings?: string[];
  medicalBenefits?: string[];
}

// Product Rating Display
export interface ProductRatingProps {
  rating?: number;
  reviewCount?: number;
  showStars?: boolean;
  showCount?: boolean;
}

// Price Display with Discounts
export interface ProductPriceProps {
  price: number;
  originalPrice?: number;
  discount?: number;
  showSavings?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

// Lab Results Display
export interface LabResultsProps {
  thcContent?: number;
  cbdContent?: number;
  cbgContent?: number;
  cbnContent?: number;
  terpenePercentage?: number;
  testDate?: string;
  labName?: string;
  certificateUrl?: string;
}

// Product Badge Types
export type ProductBadgeType = 
  | 'new'
  | 'sale'
  | 'bestseller'
  | 'limited'
  | 'organic'
  | 'indoor'
  | 'outdoor'
  | 'greenhouse'
  | 'lab-tested'
  | 'craft';

export interface ProductBadgeProps {
  type: ProductBadgeType;
  text?: string;
  color?: string;
  size?: 'sm' | 'md' | 'lg';
}

// Product Actions Props
export interface ProductActionsProps {
  product: Product;
  quantity: number;
  onQuantityChange: (quantity: number) => void;
  onAddToCart: () => Promise<void>;
  onAddToWishlist?: () => void;
  onShare?: () => void;
  isInCart?: boolean;
  isInWishlist?: boolean;
  disabled?: boolean;
}

// Strain Information Display
export interface StrainInfoProps {
  strainType?: string;
  plantType?: string;
  genetics?: string;
  growMethod?: string;
  harvestDate?: string;
}

// Product Tabs Configuration
export interface ProductTabConfig {
  id: string;
  label: string;
  icon?: React.ReactNode;
  content: React.ReactNode;
  badge?: string | number;
}

export interface ProductTabsProps {
  tabs: ProductTabConfig[];
  defaultTab?: string;
  variant?: 'pills' | 'underline' | 'bordered';
}