/**
 * API Error Handling Utilities
 *
 * Provides centralized error handling for API calls with:
 * - Custom error classes for different error types
 * - Error classification (network, client, server)
 * - User-friendly error messages
 * - Retry logic with exponential backoff
 *
 * Principles:
 * - SRP: Each class handles one type of error
 * - DRY: Reusable error handling logic
 * - KISS: Simple, predictable error handling
 */

import { AxiosError } from 'axios';
import { ErrorResponse } from '../types/payment';

// ============================================================================
// Error Classification
// ============================================================================

/**
 * Error severity levels
 */
export enum ErrorSeverity {
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error',
  CRITICAL = 'critical',
}

/**
 * Error categories for different handling strategies
 */
export enum ErrorCategory {
  NETWORK = 'network', // Network issues, timeouts
  CLIENT = 'client', // 4xx errors - user/client fault
  SERVER = 'server', // 5xx errors - server fault
  VALIDATION = 'validation', // Data validation errors
  AUTHENTICATION = 'authentication', // 401, 403 errors
  NOT_FOUND = 'not_found', // 404 errors
  CONFLICT = 'conflict', // 409 errors
  UNKNOWN = 'unknown', // Unclassified errors
}

// ============================================================================
// Custom Error Classes
// ============================================================================

/**
 * Base error class for all API errors
 *
 * Following SRP - provides common error properties and methods
 */
export class ApiError extends Error {
  public readonly timestamp: Date;
  public readonly category: ErrorCategory;
  public readonly severity: ErrorSeverity;
  public readonly statusCode?: number;
  public readonly errorCode?: string;
  public readonly details?: Record<string, unknown>;
  public readonly retryable: boolean;

  constructor(
    message: string,
    category: ErrorCategory,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    statusCode?: number,
    errorCode?: string,
    details?: Record<string, unknown>,
    retryable: boolean = false
  ) {
    super(message);
    this.name = 'ApiError';
    this.timestamp = new Date();
    this.category = category;
    this.severity = severity;
    this.statusCode = statusCode;
    this.errorCode = errorCode;
    this.details = details;
    this.retryable = retryable;

    // Maintains proper stack trace for where error was thrown
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, ApiError);
    }
  }

  /**
   * Get user-friendly error message
   */
  getUserMessage(): string {
    switch (this.category) {
      case ErrorCategory.NETWORK:
        return 'Network error. Please check your connection and try again.';
      case ErrorCategory.AUTHENTICATION:
        return 'Authentication failed. Please log in again.';
      case ErrorCategory.NOT_FOUND:
        return 'The requested resource was not found.';
      case ErrorCategory.VALIDATION:
        return this.message || 'Invalid data provided.';
      case ErrorCategory.SERVER:
        return 'Server error. Please try again later.';
      default:
        return this.message || 'An unexpected error occurred.';
    }
  }

  /**
   * Check if error is retryable
   */
  isRetryable(): boolean {
    return this.retryable;
  }

  /**
   * Convert to plain object for logging
   */
  toJSON(): Record<string, unknown> {
    return {
      name: this.name,
      message: this.message,
      category: this.category,
      severity: this.severity,
      statusCode: this.statusCode,
      errorCode: this.errorCode,
      details: this.details,
      retryable: this.retryable,
      timestamp: this.timestamp.toISOString(),
      stack: this.stack,
    };
  }
}

/**
 * Network-related errors (timeouts, no connection)
 */
export class NetworkError extends ApiError {
  constructor(message: string = 'Network request failed') {
    super(
      message,
      ErrorCategory.NETWORK,
      ErrorSeverity.WARNING,
      undefined,
      'NETWORK_ERROR',
      undefined,
      true // Network errors are retryable
    );
    this.name = 'NetworkError';
  }
}

/**
 * Authentication/Authorization errors (401, 403)
 */
export class AuthenticationError extends ApiError {
  constructor(message: string = 'Authentication required', statusCode?: number) {
    super(
      message,
      ErrorCategory.AUTHENTICATION,
      ErrorSeverity.ERROR,
      statusCode,
      'AUTH_ERROR',
      undefined,
      false // Don't retry auth errors
    );
    this.name = 'AuthenticationError';
  }
}

/**
 * Resource not found errors (404)
 */
export class NotFoundError extends ApiError {
  constructor(resource: string, id?: string) {
    const message = id
      ? `${resource} with ID ${id} not found`
      : `${resource} not found`;

    super(
      message,
      ErrorCategory.NOT_FOUND,
      ErrorSeverity.WARNING,
      404,
      'NOT_FOUND',
      { resource, id },
      false // Don't retry not found
    );
    this.name = 'NotFoundError';
  }
}

/**
 * Validation errors (400)
 */
export class ValidationError extends ApiError {
  constructor(
    message: string,
    details?: Record<string, unknown>
  ) {
    super(
      message,
      ErrorCategory.VALIDATION,
      ErrorSeverity.WARNING,
      400,
      'VALIDATION_ERROR',
      details,
      false // Don't retry validation errors
    );
    this.name = 'ValidationError';
  }
}

/**
 * Conflict errors (409)
 */
export class ConflictError extends ApiError {
  constructor(message: string, details?: Record<string, unknown>) {
    super(
      message,
      ErrorCategory.CONFLICT,
      ErrorSeverity.WARNING,
      409,
      'CONFLICT',
      details,
      false // Don't retry conflicts
    );
    this.name = 'ConflictError';
  }
}

/**
 * Server errors (5xx)
 */
export class ServerError extends ApiError {
  constructor(
    message: string = 'Server error occurred',
    statusCode: number = 500,
    errorCode?: string
  ) {
    super(
      message,
      ErrorCategory.SERVER,
      ErrorSeverity.ERROR,
      statusCode,
      errorCode || 'SERVER_ERROR',
      undefined,
      true // Server errors are retryable
    );
    this.name = 'ServerError';
  }
}

// ============================================================================
// Error Handler Factory
// ============================================================================

/**
 * Convert Axios error to appropriate ApiError subclass
 *
 * Following Factory Pattern - creates appropriate error type
 * based on response status and error characteristics
 */
export function handleApiError(error: unknown): ApiError {
  // Already an ApiError
  if (error instanceof ApiError) {
    return error;
  }

  // Axios error
  if (isAxiosError(error)) {
    const axiosError = error as AxiosError<ErrorResponse>;

    // Network error (no response)
    if (!axiosError.response) {
      if (axiosError.code === 'ECONNABORTED' || axiosError.message.includes('timeout')) {
        return new NetworkError('Request timeout. Please try again.');
      }
      return new NetworkError('Network error. Please check your connection.');
    }

    const status = axiosError.response.status;
    const data = axiosError.response.data;

    // Extract error message from backend response
    const message = data?.error || data?.detail || axiosError.message || 'Request failed';
    const errorCode = data?.error_code;
    const details = data?.details;

    // Classify by status code
    if (status === 401 || status === 403) {
      return new AuthenticationError(message, status);
    }

    if (status === 404) {
      // Try to extract resource info from URL
      const url = axiosError.config?.url || '';
      const resource = url.split('/').filter(Boolean).pop() || 'Resource';
      return new NotFoundError(resource);
    }

    if (status === 400) {
      return new ValidationError(message, details);
    }

    if (status === 409) {
      return new ConflictError(message, details);
    }

    if (status >= 500) {
      return new ServerError(message, status, errorCode);
    }

    if (status >= 400 && status < 500) {
      // Other 4xx errors
      return new ApiError(
        message,
        ErrorCategory.CLIENT,
        ErrorSeverity.WARNING,
        status,
        errorCode,
        details,
        false
      );
    }
  }

  // Generic JavaScript error
  if (error instanceof Error) {
    return new ApiError(
      error.message,
      ErrorCategory.UNKNOWN,
      ErrorSeverity.ERROR,
      undefined,
      'UNKNOWN_ERROR',
      undefined,
      false
    );
  }

  // Unknown error type
  return new ApiError(
    'An unknown error occurred',
    ErrorCategory.UNKNOWN,
    ErrorSeverity.ERROR,
    undefined,
    'UNKNOWN_ERROR',
    { originalError: String(error) },
    false
  );
}

/**
 * Type guard for Axios errors
 */
function isAxiosError(error: unknown): error is AxiosError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'isAxiosError' in error &&
    (error as AxiosError).isAxiosError === true
  );
}

// ============================================================================
// Retry Logic with Exponential Backoff
// ============================================================================

/**
 * Retry configuration options
 */
export interface RetryOptions {
  maxRetries: number;
  initialDelayMs: number;
  maxDelayMs: number;
  backoffMultiplier: number;
  retryableErrors?: ErrorCategory[];
  onRetry?: (error: ApiError, attempt: number, delayMs: number) => void;
}

/**
 * Default retry configuration
 */
export const DEFAULT_RETRY_OPTIONS: RetryOptions = {
  maxRetries: 3,
  initialDelayMs: 1000, // 1 second
  maxDelayMs: 10000, // 10 seconds
  backoffMultiplier: 2, // Exponential: 1s, 2s, 4s, 8s...
  retryableErrors: [ErrorCategory.NETWORK, ErrorCategory.SERVER],
};

/**
 * Execute a function with retry logic and exponential backoff
 *
 * Implements:
 * - Exponential backoff (delays increase exponentially)
 * - Maximum retry limit
 * - Selective retry (only network and server errors)
 * - Callback for retry events
 *
 * @example
 * const result = await retryWithBackoff(
 *   () => axios.get('/api/data'),
 *   { maxRetries: 3, initialDelayMs: 1000 }
 * );
 */
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  options: Partial<RetryOptions> = {}
): Promise<T> {
  const config = { ...DEFAULT_RETRY_OPTIONS, ...options };
  let lastError: ApiError | undefined;

  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = handleApiError(error);

      // Don't retry on last attempt
      if (attempt === config.maxRetries) {
        throw lastError;
      }

      // Check if error is retryable
      if (!shouldRetry(lastError, config)) {
        throw lastError;
      }

      // Calculate delay with exponential backoff
      const delay = calculateBackoffDelay(attempt, config);

      // Call retry callback if provided
      if (config.onRetry) {
        config.onRetry(lastError, attempt + 1, delay);
      }

      // Log retry attempt
      console.warn(
        `Retry attempt ${attempt + 1}/${config.maxRetries} after ${delay}ms`,
        {
          error: lastError.message,
          category: lastError.category,
        }
      );

      // Wait before retrying
      await sleep(delay);
    }
  }

  // Should never reach here, but TypeScript needs it
  throw lastError || new ApiError('Retry failed', ErrorCategory.UNKNOWN, ErrorSeverity.ERROR);
}

/**
 * Determine if error should be retried
 */
function shouldRetry(error: ApiError, config: RetryOptions): boolean {
  // Check if error is marked as retryable
  if (!error.isRetryable()) {
    return false;
  }

  // Check if error category is retryable
  const retryableCategories = config.retryableErrors || DEFAULT_RETRY_OPTIONS.retryableErrors!;
  return retryableCategories.includes(error.category);
}

/**
 * Calculate exponential backoff delay
 */
function calculateBackoffDelay(attempt: number, config: RetryOptions): number {
  const delay = config.initialDelayMs * Math.pow(config.backoffMultiplier, attempt);
  return Math.min(delay, config.maxDelayMs);
}

/**
 * Sleep for specified milliseconds
 */
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// ============================================================================
// Request Deduplication
// ============================================================================

/**
 * Request deduplication cache
 *
 * Prevents duplicate simultaneous requests to same endpoint
 */
class RequestCache {
  private cache = new Map<string, Promise<unknown>>();

  /**
   * Get or execute request
   *
   * If request with same key is in progress, returns existing promise.
   * Otherwise, executes new request and caches the promise.
   */
  async getOrExecute<T>(key: string, fn: () => Promise<T>): Promise<T> {
    // Check if request is already in progress
    const existing = this.cache.get(key);
    if (existing) {
      return existing as Promise<T>;
    }

    // Execute new request
    const promise = fn();

    // Cache the promise
    this.cache.set(key, promise);

    // Remove from cache when done (success or failure)
    promise
      .finally(() => {
        this.cache.delete(key);
      });

    return promise;
  }

  /**
   * Clear entire cache
   */
  clear(): void {
    this.cache.clear();
  }

  /**
   * Clear specific key
   */
  clearKey(key: string): void {
    this.cache.delete(key);
  }
}

// Export singleton instance
export const requestCache = new RequestCache();

/**
 * Generate cache key for request
 */
export function generateCacheKey(
  method: string,
  url: string,
  params?: Record<string, unknown>
): string {
  const paramsStr = params ? JSON.stringify(params) : '';
  return `${method}:${url}:${paramsStr}`;
}

// ============================================================================
// Error Logging
// ============================================================================

/**
 * Log error to console (and optionally to external service)
 */
export function logError(error: ApiError, context?: Record<string, unknown>): void {
  const errorLog = {
    ...error.toJSON(),
    context,
    userAgent: navigator.userAgent,
    url: window.location.href,
  };

  // Log to console based on severity
  switch (error.severity) {
    case ErrorSeverity.CRITICAL:
    case ErrorSeverity.ERROR:
      console.error('[API Error]', errorLog);
      break;
    case ErrorSeverity.WARNING:
      console.warn('[API Warning]', errorLog);
      break;
    default:
      console.info('[API Info]', errorLog);
  }

  // TODO: Send to error tracking service (Sentry, Bugsnag, etc.)
  // if (error.severity === ErrorSeverity.CRITICAL || error.severity === ErrorSeverity.ERROR) {
  //   sendToErrorTracker(errorLog);
  // }
}
