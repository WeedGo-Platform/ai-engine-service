/**
 * SEO Configuration Types
 * Comprehensive types for SEO management and optimization
 */

export interface SEORouteConfig {
  // Route pattern configuration
  productDetailPattern?: string; // e.g., "dispensary-near-me/{city}/{slug}" or "cannabis/{category}/{slug}"
  categoryPattern?: string; // e.g., "shop/{category}" or "menu/{category}"
  brandPattern?: string; // e.g., "brands/{brand-slug}"
  searchPattern?: string; // e.g., "search" or "find-cannabis"

  // Location-based patterns for local SEO
  locationPattern?: string; // e.g., "{city}-dispensary" or "weed-delivery-{city}"
  storeLocatorPattern?: string; // e.g., "dispensaries-near-me" or "locations"

  // Custom patterns
  customPatterns?: Record<string, string>;
}

export interface SEOMetaData {
  title: string;
  description: string;
  keywords?: string[];
  canonical?: string;

  // Open Graph
  ogTitle?: string;
  ogDescription?: string;
  ogImage?: string;
  ogType?: 'website' | 'product' | 'article';
  ogUrl?: string;
  ogSiteName?: string;

  // Twitter Card
  twitterCard?: 'summary' | 'summary_large_image' | 'app' | 'player';
  twitterTitle?: string;
  twitterDescription?: string;
  twitterImage?: string;
  twitterSite?: string;
  twitterCreator?: string;

  // Additional meta
  robots?: string; // "index,follow" | "noindex,nofollow" etc.
  author?: string;
  viewport?: string;
  themeColor?: string;

  // Language and region
  language?: string;
  region?: string;
  alternateLanguages?: Array<{
    hreflang: string;
    href: string;
  }>;
}

export interface StructuredData {
  '@context': 'https://schema.org';
  '@type': string;
  [key: string]: any;
}

export interface ProductStructuredData extends StructuredData {
  '@type': 'Product';
  name: string;
  description: string;
  image: string | string[];
  brand: {
    '@type': 'Brand';
    name: string;
  };
  sku: string;
  offers: {
    '@type': 'Offer';
    url: string;
    priceCurrency: string;
    price: string;
    availability: 'https://schema.org/InStock' | 'https://schema.org/OutOfStock' | 'https://schema.org/PreOrder';
    seller: {
      '@type': 'Organization';
      name: string;
    };
  };
  aggregateRating?: {
    '@type': 'AggregateRating';
    ratingValue: string;
    reviewCount: string;
  };
  review?: Array<{
    '@type': 'Review';
    author: string;
    datePublished: string;
    reviewBody: string;
    reviewRating: {
      '@type': 'Rating';
      ratingValue: string;
    };
  }>;
}

export interface LocalBusinessStructuredData extends StructuredData {
  '@type': 'Dispensary' | 'Store' | 'LocalBusiness';
  name: string;
  description: string;
  url: string;
  telephone: string;
  address: {
    '@type': 'PostalAddress';
    streetAddress: string;
    addressLocality: string;
    addressRegion: string;
    postalCode: string;
    addressCountry: string;
  };
  geo?: {
    '@type': 'GeoCoordinates';
    latitude: string;
    longitude: string;
  };
  openingHoursSpecification?: Array<{
    '@type': 'OpeningHoursSpecification';
    dayOfWeek: string | string[];
    opens: string;
    closes: string;
  }>;
  priceRange?: string;
  image?: string | string[];
  sameAs?: string[]; // Social media URLs
}

export interface BreadcrumbStructuredData extends StructuredData {
  '@type': 'BreadcrumbList';
  itemListElement: Array<{
    '@type': 'ListItem';
    position: number;
    name: string;
    item?: string;
  }>;
}

export interface SEOConfig {
  // Store/tenant level SEO settings
  storeName: string;
  storeDescription: string;
  defaultMetaTags: SEOMetaData;

  // Route configuration
  routes: SEORouteConfig;

  // URL structure preferences
  urlStructure: {
    useLowerCase: boolean;
    useTrailingSlash: boolean;
    removeStopWords: boolean;
    maxUrlLength: number;
  };

  // Sitemap configuration
  sitemap: {
    enabled: boolean;
    changeFreq: 'always' | 'hourly' | 'daily' | 'weekly' | 'monthly' | 'yearly' | 'never';
    priority: number;
    excludePatterns?: string[];
    includePatterns?: string[];
  };

  // Robots.txt configuration
  robots: {
    allowAll: boolean;
    disallowPatterns?: string[];
    crawlDelay?: number;
    sitemapUrl?: string;
  };

  // Local SEO
  localSEO: {
    enabled: boolean;
    businessType: 'Dispensary' | 'CannabisStore' | 'LocalBusiness';
    serviceArea?: string[];
    languages?: string[];
  };

  // Performance & Technical SEO
  technical: {
    enableAMP: boolean;
    enablePWA: boolean;
    lazyLoadImages: boolean;
    enableWebP: boolean;
    criticalCSS: boolean;
    preconnectDomains?: string[];
  };

  // Analytics & Monitoring
  analytics: {
    googleAnalyticsId?: string;
    googleTagManagerId?: string;
    facebookPixelId?: string;
    customTracking?: Record<string, string>;
  };
}

export interface DynamicRouteParams {
  slug?: string;
  category?: string;
  city?: string;
  state?: string;
  brand?: string;
  [key: string]: string | undefined;
}

export interface RouteGenerator {
  generate(pattern: string, params: DynamicRouteParams): string;
  parse(url: string, pattern: string): DynamicRouteParams | null;
  isValid(url: string, pattern: string): boolean;
}

export interface SEOPageData {
  meta: SEOMetaData;
  structuredData?: StructuredData[];
  breadcrumbs?: Array<{ name: string; url: string }>;
  alternateUrls?: Array<{ lang: string; url: string }>;
  canonicalUrl?: string;
}

// Utility types for SEO optimization
export interface SEOScore {
  overall: number;
  factors: {
    titleLength: boolean;
    descriptionLength: boolean;
    headings: boolean;
    images: boolean;
    internalLinks: boolean;
    metaTags: boolean;
    structuredData: boolean;
    mobileOptimized: boolean;
    pageSpeed: boolean;
    https: boolean;
  };
  suggestions: string[];
}

export interface SEOAnalysis {
  url: string;
  score: SEOScore;
  warnings: string[];
  errors: string[];
  improvements: string[];
}