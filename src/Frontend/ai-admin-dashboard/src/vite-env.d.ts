/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_API_TIMEOUT: string
  readonly VITE_API_RETRY_ATTEMPTS: string
  readonly VITE_API_RETRY_DELAY: string
  readonly VITE_NOTIFICATION_SUCCESS_TIMEOUT: string
  readonly VITE_NOTIFICATION_ERROR_TIMEOUT: string
  readonly VITE_NOTIFICATION_INFO_TIMEOUT: string
  readonly VITE_NOTIFICATION_WARNING_TIMEOUT: string
  readonly VITE_DEBOUNCE_SEARCH: string
  readonly VITE_DEBOUNCE_INPUT: string
  readonly VITE_DEBOUNCE_RESIZE: string
  readonly VITE_DEFAULT_PAGE_SIZE: string
  readonly VITE_PAGE_SIZE_OPTIONS: string
  readonly VITE_MODAL_ANIMATION_DELAY: string
  readonly VITE_TRANSITION_DURATION: string
  readonly VITE_FEATURE_BARCODE_SCANNING: string
  readonly VITE_FEATURE_QUICK_INTAKE: string
  readonly VITE_FEATURE_BULK_OPERATIONS: string
  readonly VITE_FEATURE_ADVANCED_SEARCH: string
  readonly VITE_FEATURE_EXPORT: string
  readonly VITE_FEATURE_IMPORT: string
  readonly VITE_FEATURE_ANALYTICS: string
  readonly VITE_FEATURE_RECOMMENDATIONS: string
  readonly VITE_FEATURE_PROMOTIONS: string
  readonly VITE_FEATURE_MULTI_STORE: string
  readonly VITE_STORE_LIMIT_COMMUNITY: string
  readonly VITE_STORE_LIMIT_SMALL: string
  readonly VITE_STORE_LIMIT_PROFESSIONAL: string
  readonly VITE_STORE_LIMIT_ENTERPRISE: string
  readonly VITE_LOW_STOCK_THRESHOLD: string
  readonly VITE_CRITICAL_STOCK_THRESHOLD: string
  readonly VITE_MAX_ORDER_QUANTITY: string
  readonly VITE_MAX_USERS_PER_TENANT: string
  readonly VITE_MAX_USERS_PER_STORE: string
  readonly VITE_SCANNER_TEST_DELAY: string
  readonly VITE_PAYMENT_PROCESSING_DELAY: string
  readonly VITE_RECEIPT_PRINT_DELAY: string
  readonly VITE_POS_SEARCH_DEBOUNCE: string
  readonly VITE_MAX_FILE_SIZE: string
  readonly VITE_ALLOWED_IMAGE_TYPES: string
  readonly VITE_ALLOWED_DOCUMENT_TYPES: string
  readonly VITE_MIN_PASSWORD_LENGTH: string
  readonly VITE_MAX_PASSWORD_LENGTH: string
  readonly VITE_REQUIRE_UPPERCASE: string
  readonly VITE_REQUIRE_LOWERCASE: string
  readonly VITE_REQUIRE_NUMBERS: string
  readonly VITE_REQUIRE_SPECIAL_CHARS: string
  readonly VITE_MAX_NAME_LENGTH: string
  readonly VITE_MAX_DESCRIPTION_LENGTH: string
  readonly VITE_MAX_CODE_LENGTH: string
  readonly VITE_GOOGLE_MAPS_API_KEY: string
  readonly VITE_STRIPE_PUBLIC_KEY: string
  readonly VITE_SENTRY_DSN: string
  readonly VITE_ENABLE_DEV_TOOLS: string
  readonly VITE_ENABLE_LOGGING: string
  readonly VITE_LOG_LEVEL: string
  readonly VITE_USE_MOCK_DATA: string
  // Add more env vars as needed
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}