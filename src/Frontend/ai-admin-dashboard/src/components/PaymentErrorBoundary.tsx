/**
 * Payment Error Boundary
 *
 * Catches and handles errors in payment components, preventing app crashes.
 *
 * Features:
 * - Catches React component errors
 * - Shows user-friendly error UI
 * - Provides retry functionality
 * - Logs errors for debugging
 * - Optional error reporting integration
 *
 * Principles:
 * - SRP: Single responsibility - error catching and display
 * - KISS: Simple fallback UI
 * - UX: Always provide a way to recover
 *
 * @example
 * <PaymentErrorBoundary>
 *   <TenantPaymentSettings />
 * </PaymentErrorBoundary>
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home, XCircle } from 'lucide-react';

// ============================================================================
// Error Boundary Props & State
// ============================================================================

interface PaymentErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  showDetails?: boolean;
}

interface PaymentErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorCount: number;
}

// ============================================================================
// Error Boundary Component
// ============================================================================

/**
 * Error Boundary for Payment Components
 *
 * Wraps payment-related components to catch and handle errors gracefully.
 * Prevents entire app from crashing when payment operations fail.
 */
class PaymentErrorBoundary extends Component<
  PaymentErrorBoundaryProps,
  PaymentErrorBoundaryState
> {
  constructor(props: PaymentErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0,
    };
  }

  /**
   * Update state when error is caught
   */
  static getDerivedStateFromError(error: Error): Partial<PaymentErrorBoundaryState> {
    return {
      hasError: true,
      error,
    };
  }

  /**
   * Log error details and call optional error handler
   */
  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Increment error count
    this.setState((prevState) => ({
      errorInfo,
      errorCount: prevState.errorCount + 1,
    }));

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('PaymentErrorBoundary caught an error:', error);
      console.error('Error info:', errorInfo);
      console.error('Component stack:', errorInfo.componentStack);
    }

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // TODO: Send to error reporting service (Sentry, Bugsnag, etc.)
    // Example:
    // Sentry.captureException(error, {
    //   contexts: {
    //     react: {
    //       componentStack: errorInfo.componentStack,
    //     },
    //   },
    //   tags: {
    //     errorBoundary: 'PaymentErrorBoundary',
    //     errorCount: this.state.errorCount + 1,
    //   },
    // });
  }

  /**
   * Reset error state and try again
   */
  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  /**
   * Navigate to home page
   */
  handleGoHome = (): void => {
    window.location.href = '/';
  };

  /**
   * Reload the page
   */
  handleReload = (): void => {
    window.location.reload();
  };

  render(): ReactNode {
    const { hasError, error, errorInfo, errorCount } = this.state;
    const { children, fallback, showDetails = false } = this.props;

    // No error - render children normally
    if (!hasError) {
      return children;
    }

    // Custom fallback provided
    if (fallback) {
      return fallback;
    }

    // Default error UI
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 p-4">
        <div className="max-w-2xl w-full">
          {/* Error Card */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 border border-red-200 dark:border-red-800">
            {/* Error Icon */}
            <div className="flex items-center justify-center mb-6">
              <div className="bg-red-100 dark:bg-red-900/30 rounded-full p-4">
                <AlertTriangle className="w-12 h-12 text-red-600 dark:text-red-400" />
              </div>
            </div>

            {/* Error Title */}
            <h1 className="text-2xl font-bold text-center text-gray-900 dark:text-white mb-2">
              Payment System Error
            </h1>

            {/* Error Message */}
            <p className="text-center text-gray-600 dark:text-gray-400 mb-6">
              We encountered an issue while loading the payment system. This could be due to a
              temporary problem or network issue.
            </p>

            {/* Error Count Warning */}
            {errorCount > 2 && (
              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-6">
                <div className="flex items-start gap-3">
                  <XCircle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-yellow-800 dark:text-yellow-200">
                    <p className="font-medium">Multiple errors detected</p>
                    <p className="mt-1">
                      This error has occurred {errorCount} times. If the problem persists,
                      please contact support.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Error Details (Development Only) */}
            {showDetails && error && (
              <div className="mb-6 bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                <details className="cursor-pointer">
                  <summary className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Error Details (Development)
                  </summary>
                  <div className="mt-2 space-y-2">
                    <div>
                      <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                        Error Message:
                      </p>
                      <pre className="text-xs bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200 p-2 rounded overflow-x-auto">
                        {error.message}
                      </pre>
                    </div>
                    {errorInfo?.componentStack && (
                      <div>
                        <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                          Component Stack:
                        </p>
                        <pre className="text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 p-2 rounded overflow-x-auto max-h-40">
                          {errorInfo.componentStack}
                        </pre>
                      </div>
                    )}
                  </div>
                </details>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                onClick={this.handleReset}
                className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
              >
                <RefreshCw className="w-5 h-5" />
                Try Again
              </button>

              <button
                onClick={this.handleReload}
                className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white font-medium rounded-lg transition-colors"
              >
                <RefreshCw className="w-5 h-5" />
                Reload Page
              </button>

              <button
                onClick={this.handleGoHome}
                className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200 font-medium rounded-lg border border-gray-300 dark:border-gray-600 transition-colors"
              >
                <Home className="w-5 h-5" />
                Go Home
              </button>
            </div>

            {/* Help Text */}
            <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
              <p className="text-sm text-center text-gray-500 dark:text-gray-400">
                If this problem persists, please contact support at{' '}
                <a
                  href="mailto:support@weedgo.ca"
                  className="text-blue-600 dark:text-blue-400 hover:underline"
                >
                  support@weedgo.ca
                </a>
              </p>
            </div>
          </div>

          {/* Development Info */}
          {process.env.NODE_ENV === 'development' && (
            <div className="mt-4 text-center">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Error Boundary: PaymentErrorBoundary | Error Count: {errorCount}
              </p>
            </div>
          )}
        </div>
      </div>
    );
  }
}

export default PaymentErrorBoundary;

// ============================================================================
// Functional Wrapper for Hooks Support
// ============================================================================

/**
 * Functional wrapper to allow using hooks in error handler
 *
 * @example
 * <PaymentErrorBoundaryWithHooks onError={handleError}>
 *   <PaymentComponent />
 * </PaymentErrorBoundaryWithHooks>
 */
export function PaymentErrorBoundaryWithHooks({
  children,
  ...props
}: PaymentErrorBoundaryProps): JSX.Element {
  return <PaymentErrorBoundary {...props}>{children}</PaymentErrorBoundary>;
}
