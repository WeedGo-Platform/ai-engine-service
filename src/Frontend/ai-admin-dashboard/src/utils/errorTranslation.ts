import { TFunction } from 'i18next';
import { AxiosError } from 'axios';

/**
 * Centralized error translation utility
 * Maps API errors to appropriate translation keys and provides localized error messages
 */

interface ApiErrorResponse {
  message?: string;
  error?: string;
  code?: string;
  details?: any;
  statusCode?: number;
}

/**
 * Extract error information from various error formats
 */
const extractErrorInfo = (error: any): { code?: string; message?: string; statusCode?: number } => {
  if (error.response) {
    // Axios error with response
    const data = error.response.data as ApiErrorResponse;
    return {
      code: data.code,
      message: data.message || data.error,
      statusCode: error.response.status
    };
  }

  if (error.request) {
    // Network error (request made but no response)
    return {
      code: 'NETWORK_ERROR',
      message: 'Network error occurred',
      statusCode: 0
    };
  }

  // Other errors (programming errors, etc.)
  return {
    message: error.message || 'Unknown error',
    statusCode: undefined
  };
};

/**
 * Map HTTP status codes to translation keys
 */
const mapStatusCodeToTranslationKey = (statusCode: number): string | null => {
  const statusMap: Record<number, string> = {
    400: 'errors:api.badRequest',
    401: 'errors:auth.unauthorized',
    403: 'errors:api.forbidden',
    404: 'errors:api.notFound',
    409: 'errors:api.conflict',
    422: 'errors:api.validationError',
    429: 'errors:api.tooManyRequests',
    500: 'errors:api.internalError',
    502: 'errors:api.serviceUnavailable',
    503: 'errors:api.serviceUnavailable',
    504: 'errors:api.timeout'
  };

  return statusMap[statusCode] || null;
};

/**
 * Map specific error codes to translation keys
 * These are custom error codes returned by the backend
 */
const mapErrorCodeToTranslationKey = (code: string): string | null => {
  const codeMap: Record<string, string> = {
    // Network errors
    'NETWORK_ERROR': 'errors:api.networkError',
    'TIMEOUT': 'errors:api.timeout',
    'ECONNABORTED': 'errors:api.timeout',
    'ERR_NETWORK': 'errors:api.networkError',

    // Auth errors
    'INVALID_CREDENTIALS': 'errors:auth.invalidCredentials',
    'SESSION_EXPIRED': 'errors:auth.sessionExpired',
    'TOKEN_EXPIRED': 'errors:auth.tokenExpired',
    'TOKEN_INVALID': 'errors:auth.tokenInvalid',
    'ACCOUNT_DISABLED': 'errors:auth.accountDisabled',
    'ACCOUNT_LOCKED': 'errors:auth.accountLocked',
    'EMAIL_NOT_VERIFIED': 'errors:auth.emailNotVerified',
    'TOO_MANY_ATTEMPTS': 'errors:auth.tooManyAttempts',

    // Tenant errors
    'TENANT_NOT_FOUND': 'errors:tenant.loadFailed',
    'TENANT_EXISTS': 'errors:api.conflict',
    'TENANT_LIMIT_REACHED': 'errors:tenant.limitReached',
    'INVALID_SUBSCRIPTION': 'errors:tenant.invalidSubscription',
    'NO_ORGANIZATION': 'errors:tenant.noOrganization',

    // Store errors
    'STORE_NOT_FOUND': 'errors:store.notFound',
    'STORE_EXISTS': 'errors:store.alreadyExists',
    'STORE_LIMIT_REACHED': 'errors:tenant.limitReached',

    // Inventory errors
    'LOW_STOCK': 'errors:inventory.lowStock',
    'OUT_OF_STOCK': 'errors:inventory.outOfStock',
    'INVALID_QUANTITY': 'errors:inventory.invalidQuantity',

    // Order errors
    'ORDER_NOT_FOUND': 'errors:order.notFound',
    'ORDER_ALREADY_PROCESSED': 'errors:order.alreadyProcessed',

    // Payment errors
    'PAYMENT_FAILED': 'errors:payment.processingFailed',
    'CARD_DECLINED': 'errors:payment.cardDeclined',
    'INSUFFICIENT_FUNDS': 'errors:payment.insufficientFunds',
    'INVALID_PAYMENT_METHOD': 'errors:payment.paymentMethodInvalid',
    'INVALID_AMOUNT': 'errors:payment.invalidAmount',

    // Upload errors
    'FILE_TOO_LARGE': 'errors:upload.fileTooLarge',
    'INVALID_FILE_TYPE': 'errors:upload.invalidFileType',
    'CORRUPTED_FILE': 'errors:upload.corruptedFile',

    // General errors
    'VALIDATION_ERROR': 'errors:api.validationError',
    'PERMISSION_DENIED': 'errors:general.permissionDenied',
    'REQUIRED_FIELD_MISSING': 'errors:general.requiredFieldMissing',
    'INVALID_INPUT': 'errors:general.invalidInput'
  };

  return codeMap[code.toUpperCase()] || null;
};

/**
 * Map error messages to translation keys based on content
 * Fallback for when we don't have specific error codes
 */
const mapMessageToTranslationKey = (message: string): string | null => {
  const lowerMessage = message.toLowerCase();

  // Auth related
  if (lowerMessage.includes('unauthorized') || lowerMessage.includes('not authorized')) {
    return 'errors:auth.unauthorized';
  }
  if (lowerMessage.includes('invalid credentials') || lowerMessage.includes('incorrect password')) {
    return 'errors:auth.invalidCredentials';
  }
  if (lowerMessage.includes('session expired') || lowerMessage.includes('token expired')) {
    return 'errors:auth.sessionExpired';
  }
  if (lowerMessage.includes('account disabled')) {
    return 'errors:auth.accountDisabled';
  }

  // Network related
  if (lowerMessage.includes('network') || lowerMessage.includes('connection')) {
    return 'errors:api.networkError';
  }
  if (lowerMessage.includes('timeout') || lowerMessage.includes('timed out')) {
    return 'errors:api.timeout';
  }

  // Resource related
  if (lowerMessage.includes('not found')) {
    return 'errors:api.notFound';
  }
  if (lowerMessage.includes('already exists') || lowerMessage.includes('duplicate')) {
    return 'errors:api.conflict';
  }

  // Permission related
  if (lowerMessage.includes('forbidden') || lowerMessage.includes('access denied')) {
    return 'errors:api.forbidden';
  }
  if (lowerMessage.includes('permission denied')) {
    return 'errors:general.permissionDenied';
  }

  // Validation related
  if (lowerMessage.includes('validation')) {
    return 'errors:api.validationError';
  }
  if (lowerMessage.includes('invalid') || lowerMessage.includes('bad request')) {
    return 'errors:api.badRequest';
  }

  // Payment related
  if (lowerMessage.includes('card declined') || lowerMessage.includes('payment declined')) {
    return 'errors:payment.cardDeclined';
  }
  if (lowerMessage.includes('insufficient funds')) {
    return 'errors:payment.insufficientFunds';
  }

  // Upload related
  if (lowerMessage.includes('file too large') || lowerMessage.includes('file size')) {
    return 'errors:upload.fileTooLarge';
  }
  if (lowerMessage.includes('invalid file type') || lowerMessage.includes('unsupported file')) {
    return 'errors:upload.invalidFileType';
  }

  return null;
};

/**
 * Main error translation function
 * Translates API errors into user-friendly localized messages
 *
 * @param error - The error object (typically an AxiosError)
 * @param t - The i18next translation function
 * @param fallbackKey - Optional fallback translation key
 * @returns Translated error message
 *
 * @example
 * ```typescript
 * try {
 *   await api.get('/tenants');
 * } catch (error) {
 *   const message = translateError(error, t, 'errors:tenant.loadFailed');
 *   toast.error(message);
 * }
 * ```
 */
export const translateError = (
  error: any,
  t: TFunction,
  fallbackKey: string = 'errors:general.unexpectedError'
): string => {
  const { code, message, statusCode } = extractErrorInfo(error);

  // Try to find translation key in order of specificity:
  // 1. Specific error code from backend
  // 2. HTTP status code
  // 3. Message content matching
  // 4. Fallback key provided by caller
  // 5. Generic unexpected error

  let translationKey: string | null = null;

  if (code) {
    translationKey = mapErrorCodeToTranslationKey(code);
  }

  if (!translationKey && statusCode) {
    translationKey = mapStatusCodeToTranslationKey(statusCode);
  }

  if (!translationKey && message) {
    translationKey = mapMessageToTranslationKey(message);
  }

  if (!translationKey) {
    translationKey = fallbackKey;
  }

  // Translate the error
  const translatedMessage = t(translationKey);

  // If translation failed (returned the key itself), return the original message or a generic error
  if (translatedMessage === translationKey) {
    return message || t('errors:general.unexpectedError');
  }

  return translatedMessage;
};

/**
 * Helper function to get context-specific error messages for common operations
 * Provides more specific fallback keys based on the operation type
 */
export const translateOperationError = (
  error: any,
  t: TFunction,
  operation: 'load' | 'create' | 'update' | 'delete' | 'save',
  resource?: 'tenant' | 'store' | 'inventory' | 'order' | 'payment'
): string => {
  let fallbackKey = 'errors:general.unexpectedError';

  // Build context-specific fallback
  if (resource) {
    const operationMap = {
      load: 'loadFailed',
      create: 'createFailed',
      update: 'updateFailed',
      delete: 'deleteFailed',
      save: 'updateFailed' // 'save' maps to 'update'
    };

    const operationKey = operationMap[operation];
    fallbackKey = `errors:${resource}.${operationKey}`;
  } else {
    const generalOperationMap = {
      load: 'dataLoadFailed',
      create: 'operationFailed',
      update: 'saveFailed',
      delete: 'deleteFailed',
      save: 'saveFailed'
    };

    const operationKey = generalOperationMap[operation];
    fallbackKey = `errors:general.${operationKey}`;
  }

  return translateError(error, t, fallbackKey);
};

/**
 * Check if an error is a specific type
 * Useful for conditional error handling
 */
export const isErrorType = (error: any, type: 'network' | 'auth' | 'validation' | 'notFound'): boolean => {
  const { code, message, statusCode } = extractErrorInfo(error);

  switch (type) {
    case 'network':
      return code === 'NETWORK_ERROR' || code === 'ERR_NETWORK' || statusCode === 0;

    case 'auth':
      return statusCode === 401 ||
             statusCode === 403 ||
             code?.includes('AUTH') ||
             code?.includes('TOKEN') ||
             message?.toLowerCase().includes('unauthorized');

    case 'validation':
      return statusCode === 422 ||
             statusCode === 400 ||
             code === 'VALIDATION_ERROR' ||
             message?.toLowerCase().includes('validation');

    case 'notFound':
      return statusCode === 404 || message?.toLowerCase().includes('not found');

    default:
      return false;
  }
};

/**
 * Extract validation errors from API response
 * Many APIs return structured validation errors
 */
export const extractValidationErrors = (error: any): Record<string, string> | null => {
  if (!error.response?.data) return null;

  const data = error.response.data;

  // Check common validation error formats
  if (data.errors && typeof data.errors === 'object') {
    return data.errors;
  }

  if (data.validationErrors && typeof data.validationErrors === 'object') {
    return data.validationErrors;
  }

  if (data.fields && typeof data.fields === 'object') {
    return data.fields;
  }

  return null;
};

export default {
  translateError,
  translateOperationError,
  isErrorType,
  extractValidationErrors
};
