// Application-wide configuration
export const appConfig = {
  // API Configuration
  api: {
    baseUrl: import.meta.env.VITE_API_URL || 'http://localhost:5024',
    timeout: parseInt(import.meta.env.VITE_API_TIMEOUT || '30000'),
    retryAttempts: parseInt(import.meta.env.VITE_API_RETRY_ATTEMPTS || '3'),
    retryDelay: parseInt(import.meta.env.VITE_API_RETRY_DELAY || '1000'),
  },

  // UI Configuration
  ui: {
    // Notification timeouts (in milliseconds)
    notifications: {
      success: parseInt(import.meta.env.VITE_NOTIFICATION_SUCCESS_TIMEOUT || '3000'),
      error: parseInt(import.meta.env.VITE_NOTIFICATION_ERROR_TIMEOUT || '5000'),
      info: parseInt(import.meta.env.VITE_NOTIFICATION_INFO_TIMEOUT || '4000'),
      warning: parseInt(import.meta.env.VITE_NOTIFICATION_WARNING_TIMEOUT || '4000'),
    },
    
    // Debounce delays
    debounce: {
      search: parseInt(import.meta.env.VITE_DEBOUNCE_SEARCH || '300'),
      input: parseInt(import.meta.env.VITE_DEBOUNCE_INPUT || '500'),
      resize: parseInt(import.meta.env.VITE_DEBOUNCE_RESIZE || '200'),
    },
    
    // Pagination
    pagination: {
      defaultPageSize: parseInt(import.meta.env.VITE_DEFAULT_PAGE_SIZE || '20'),
      pageSizeOptions: import.meta.env.VITE_PAGE_SIZE_OPTIONS?.split(',').map(Number) || [10, 20, 50, 100],
    },
    
    // Animation delays
    animations: {
      modalDelay: parseInt(import.meta.env.VITE_MODAL_ANIMATION_DELAY || '200'),
      transitionDuration: parseInt(import.meta.env.VITE_TRANSITION_DURATION || '300'),
    },
  },

  // Feature flags
  features: {
    enableBarcodeScanning: import.meta.env.VITE_FEATURE_BARCODE_SCANNING !== 'false',
    enableQuickIntake: import.meta.env.VITE_FEATURE_QUICK_INTAKE !== 'false',
    enableBulkOperations: import.meta.env.VITE_FEATURE_BULK_OPERATIONS !== 'false',
    enableAdvancedSearch: import.meta.env.VITE_FEATURE_ADVANCED_SEARCH !== 'false',
    enableExport: import.meta.env.VITE_FEATURE_EXPORT !== 'false',
    enableImport: import.meta.env.VITE_FEATURE_IMPORT !== 'false',
    enableAnalytics: import.meta.env.VITE_FEATURE_ANALYTICS !== 'false',
    enableRecommendations: import.meta.env.VITE_FEATURE_RECOMMENDATIONS !== 'false',
    enablePromotions: import.meta.env.VITE_FEATURE_PROMOTIONS !== 'false',
    enableMultiStore: import.meta.env.VITE_FEATURE_MULTI_STORE !== 'false',
  },

  // Business rules
  business: {
    // Store limits by subscription tier
    storeLimits: {
      community: parseInt(import.meta.env.VITE_STORE_LIMIT_COMMUNITY || '1'),
      small: parseInt(import.meta.env.VITE_STORE_LIMIT_SMALL || '5'),
      professional: parseInt(import.meta.env.VITE_STORE_LIMIT_PROFESSIONAL || '12'),
      enterprise: parseInt(import.meta.env.VITE_STORE_LIMIT_ENTERPRISE || '999'),
    },
    
    // Inventory thresholds
    inventory: {
      lowStockThreshold: parseInt(import.meta.env.VITE_LOW_STOCK_THRESHOLD || '10'),
      criticalStockThreshold: parseInt(import.meta.env.VITE_CRITICAL_STOCK_THRESHOLD || '5'),
      maxOrderQuantity: parseInt(import.meta.env.VITE_MAX_ORDER_QUANTITY || '9999'),
    },
    
    // User limits
    users: {
      maxUsersPerTenant: parseInt(import.meta.env.VITE_MAX_USERS_PER_TENANT || '100'),
      maxUsersPerStore: parseInt(import.meta.env.VITE_MAX_USERS_PER_STORE || '50'),
    },
  },

  // POS Configuration
  pos: {
    scannerTestDelay: parseInt(import.meta.env.VITE_SCANNER_TEST_DELAY || '2000'),
    paymentProcessingDelay: parseInt(import.meta.env.VITE_PAYMENT_PROCESSING_DELAY || '1500'),
    receiptPrintDelay: parseInt(import.meta.env.VITE_RECEIPT_PRINT_DELAY || '1000'),
    searchDebounce: parseInt(import.meta.env.VITE_POS_SEARCH_DEBOUNCE || '300'),
  },

  // Upload Configuration
  upload: {
    maxFileSize: parseInt(import.meta.env.VITE_MAX_FILE_SIZE || '10485760'), // 10MB default
    allowedImageTypes: import.meta.env.VITE_ALLOWED_IMAGE_TYPES?.split(',') || ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
    allowedDocumentTypes: import.meta.env.VITE_ALLOWED_DOCUMENT_TYPES?.split(',') || ['application/pdf', 'text/csv', 'application/vnd.ms-excel'],
  },

  // Validation rules
  validation: {
    minPasswordLength: parseInt(import.meta.env.VITE_MIN_PASSWORD_LENGTH || '8'),
    maxPasswordLength: parseInt(import.meta.env.VITE_MAX_PASSWORD_LENGTH || '128'),
    requireUppercase: import.meta.env.VITE_REQUIRE_UPPERCASE !== 'false',
    requireLowercase: import.meta.env.VITE_REQUIRE_LOWERCASE !== 'false',
    requireNumbers: import.meta.env.VITE_REQUIRE_NUMBERS !== 'false',
    requireSpecialChars: import.meta.env.VITE_REQUIRE_SPECIAL_CHARS !== 'false',
    
    // Field length limits
    maxNameLength: parseInt(import.meta.env.VITE_MAX_NAME_LENGTH || '100'),
    maxDescriptionLength: parseInt(import.meta.env.VITE_MAX_DESCRIPTION_LENGTH || '500'),
    maxCodeLength: parseInt(import.meta.env.VITE_MAX_CODE_LENGTH || '50'),
  },

  // External services
  external: {
    googleMapsApiKey: import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '',
    stripePublicKey: import.meta.env.VITE_STRIPE_PUBLIC_KEY || '',
    sentryDsn: import.meta.env.VITE_SENTRY_DSN || '',
  },

  // Development settings
  development: {
    enableDevTools: import.meta.env.VITE_ENABLE_DEV_TOOLS === 'true',
    enableLogging: import.meta.env.VITE_ENABLE_LOGGING !== 'false',
    logLevel: import.meta.env.VITE_LOG_LEVEL || 'info',
    mockData: import.meta.env.VITE_USE_MOCK_DATA === 'true',
  },
};

// Helper function to get API URL with optional path
export const getApiUrl = (path: string = ''): string => {
  const baseUrl = appConfig.api.baseUrl;
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${baseUrl}${cleanPath}`;
};

// Helper function to get API endpoint
export const getApiEndpoint = (endpoint: string): string => {
  const baseUrl = appConfig.api.baseUrl;
  // If endpoint already includes /api, don't add it again
  if (endpoint.startsWith('/api')) {
    return `${baseUrl}${endpoint}`;
  }
  // Otherwise, add /api prefix
  return `${baseUrl}/api${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
};

export default appConfig;