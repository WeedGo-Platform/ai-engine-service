import { useTranslation } from 'react-i18next';
import { useCallback } from 'react';
import { translateError, translateOperationError, isErrorType, extractValidationErrors } from '@/utils/errorTranslation';
import { toast } from 'react-hot-toast';

/**
 * Custom hook for standardized error handling with translation support
 * Provides convenient methods to handle and display translated error messages
 *
 * @example
 * ```typescript
 * const { handleError, handleOperationError } = useErrorHandler();
 *
 * try {
 *   await tenantService.loadTenant(id);
 * } catch (error) {
 *   handleOperationError(error, 'load', 'tenant');
 * }
 * ```
 */
export const useErrorHandler = () => {
  const { t } = useTranslation();

  /**
   * Handle and display a translated error message
   * @param error - The error object
   * @param fallbackKey - Optional fallback translation key
   * @param options - Display options
   * @returns The translated error message
   */
  const handleError = useCallback(
    (
      error: any,
      fallbackKey?: string,
      options?: {
        showToast?: boolean;
        toastDuration?: number;
        logError?: boolean;
      }
    ): string => {
      const {
        showToast = true,
        toastDuration = 4000,
        logError = true
      } = options || {};

      // Log error to console in development
      if (logError && import.meta.env.DEV) {
        console.error('Error occurred:', error);
      }

      // Translate the error
      const message = translateError(error, t, fallbackKey);

      // Show toast notification
      if (showToast) {
        toast.error(message, { duration: toastDuration });
      }

      return message;
    },
    [t]
  );

  /**
   * Handle operation-specific errors (load, create, update, delete)
   * Provides context-aware error messages
   */
  const handleOperationError = useCallback(
    (
      error: any,
      operation: 'load' | 'create' | 'update' | 'delete' | 'save',
      resource?: 'tenant' | 'store' | 'inventory' | 'order' | 'payment',
      options?: {
        showToast?: boolean;
        toastDuration?: number;
        logError?: boolean;
      }
    ): string => {
      const {
        showToast = true,
        toastDuration = 4000,
        logError = true
      } = options || {};

      // Log error to console in development
      if (logError && import.meta.env.DEV) {
        console.error(`${operation} ${resource || 'resource'} error:`, error);
      }

      // Translate the error with operation context
      const message = translateOperationError(error, t, operation, resource);

      // Show toast notification
      if (showToast) {
        toast.error(message, { duration: toastDuration });
      }

      return message;
    },
    [t]
  );

  /**
   * Handle validation errors from API responses
   * Returns a map of field names to error messages
   */
  const handleValidationErrors = useCallback(
    (error: any): Record<string, string> | null => {
      const validationErrors = extractValidationErrors(error);

      if (validationErrors) {
        // Optionally show a toast for the first validation error
        const firstError = Object.values(validationErrors)[0];
        if (firstError) {
          toast.error(firstError, { duration: 4000 });
        }

        return validationErrors;
      }

      return null;
    },
    []
  );

  /**
   * Check if error is of a specific type
   */
  const checkErrorType = useCallback(
    (error: any, type: 'network' | 'auth' | 'validation' | 'notFound'): boolean => {
      return isErrorType(error, type);
    },
    []
  );

  /**
   * Handle error with automatic type detection and appropriate actions
   * Provides smart error handling based on error type
   */
  const handleErrorSmart = useCallback(
    (error: any, fallbackKey?: string): string => {
      // Check for validation errors first
      if (isErrorType(error, 'validation')) {
        const validationErrors = handleValidationErrors(error);
        if (validationErrors) {
          return Object.values(validationErrors).join(', ');
        }
      }

      // Check for network errors
      if (isErrorType(error, 'network')) {
        const message = translateError(error, t, 'errors:api.networkError');
        toast.error(message, {
          duration: 5000,
          icon: '🌐'
        });
        return message;
      }

      // Check for auth errors (no toast needed as redirect will happen)
      if (isErrorType(error, 'auth')) {
        const message = translateError(error, t, 'errors:auth.unauthorized');
        // Don't show toast for auth errors as user will be redirected
        if (import.meta.env.DEV) {
          console.error('Auth error:', message);
        }
        return message;
      }

      // Handle generic errors
      return handleError(error, fallbackKey);
    },
    [t, handleError, handleValidationErrors]
  );

  /**
   * Create an error handler wrapper for async functions
   * Useful for wrapping multiple operations
   */
  const withErrorHandler = useCallback(
    <T extends any[], R>(
      fn: (...args: T) => Promise<R>,
      fallbackKey?: string
    ) => {
      return async (...args: T): Promise<R | null> => {
        try {
          return await fn(...args);
        } catch (error) {
          handleErrorSmart(error, fallbackKey);
          return null;
        }
      };
    },
    [handleErrorSmart]
  );

  return {
    handleError,
    handleOperationError,
    handleValidationErrors,
    checkErrorType,
    handleErrorSmart,
    withErrorHandler
  };
};

export default useErrorHandler;
