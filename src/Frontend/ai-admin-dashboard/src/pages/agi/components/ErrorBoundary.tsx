/**
 * Error Boundary Component
 * Catches JavaScript errors anywhere in the component tree and displays a fallback UI
 * Provides graceful error handling and reporting
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Alert, Button, Card, CardContent } from './ui';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  resetKeys?: Array<string | number>;
  resetOnPropsChange?: boolean;
  isolate?: boolean;
  level?: 'page' | 'section' | 'component';
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorCount: number;
  lastErrorTime: Date | null;
}

/**
 * Main Error Boundary Component
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private resetTimeoutId: NodeJS.Timeout | null = null;
  private previousResetKeys: Array<string | number> = [];

  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0,
      lastErrorTime: null
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
      lastErrorTime: new Date()
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const { onError } = this.props;
    const { errorCount } = this.state;

    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('Error Boundary caught an error:', error, errorInfo);
    }

    // Call custom error handler if provided
    if (onError) {
      onError(error, errorInfo);
    }

    // Update error state
    this.setState({
      errorInfo,
      errorCount: errorCount + 1
    });

    // Send error to logging service
    this.logErrorToService(error, errorInfo);

    // Auto-reset after 30 seconds for transient errors
    if (this.props.isolate && errorCount < 3) {
      this.resetTimeoutId = setTimeout(() => {
        this.resetError();
      }, 30000);
    }
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps) {
    const { resetKeys, resetOnPropsChange } = this.props;
    const { hasError } = this.state;

    if (hasError) {
      // Check if reset keys have changed
      if (resetKeys && this.previousResetKeys) {
        const hasResetKeyChanged = resetKeys.some(
          (key, index) => key !== this.previousResetKeys[index]
        );
        if (hasResetKeyChanged) {
          this.resetError();
        }
      }

      // Reset on any props change if enabled
      if (resetOnPropsChange && prevProps !== this.props) {
        this.resetError();
      }
    }

    this.previousResetKeys = resetKeys || [];
  }

  componentWillUnmount() {
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
    }
  }

  logErrorToService = (error: Error, errorInfo: ErrorInfo) => {
    // In production, this would send to a logging service
    const errorData = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      level: this.props.level || 'component'
    };

    // Send to logging service (placeholder)
    if (process.env.NODE_ENV === 'production') {
      // fetch('/api/errors', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(errorData)
      // });
    }
  };

  resetError = () => {
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
      this.resetTimeoutId = null;
    }

    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  };

  render() {
    const { hasError, error, errorInfo, errorCount, lastErrorTime } = this.state;
    const { children, fallback, level = 'component' } = this.props;

    if (hasError && error) {
      // Use custom fallback if provided
      if (fallback) {
        return <>{fallback}</>;
      }

      // Default fallback UI based on error level
      return (
        <ErrorFallback
          error={error}
          errorInfo={errorInfo}
          level={level}
          errorCount={errorCount}
          lastErrorTime={lastErrorTime}
          onReset={this.resetError}
        />
      );
    }

    return children;
  }
}

/**
 * Error Fallback Component
 */
interface ErrorFallbackProps {
  error: Error;
  errorInfo: ErrorInfo | null;
  level: 'page' | 'section' | 'component';
  errorCount: number;
  lastErrorTime: Date | null;
  onReset: () => void;
}

const ErrorFallback: React.FC<ErrorFallbackProps> = ({
  error,
  errorInfo,
  level,
  errorCount,
  lastErrorTime,
  onReset
}) => {
  const isDevMode = process.env.NODE_ENV === 'development';

  // Different layouts based on error level
  if (level === 'page') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-2xl w-full">
          <Card>
            <CardContent className="p-8 text-center">
              <div className="mb-6">
                <svg className="w-24 h-24 text-red-500 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <h1 className="text-3xl font-bold text-gray-900 mb-2">Something went wrong</h1>
                <p className="text-gray-600 mb-4">
                  We encountered an unexpected error. Please try refreshing the page.
                </p>
              </div>

              {errorCount > 1 && (
                <Alert variant="warning" className="mb-6">
                  <p className="text-sm">This error has occurred {errorCount} times.</p>
                  {lastErrorTime && (
                    <p className="text-xs mt-1">
                      Last occurrence: {lastErrorTime.toLocaleTimeString()}
                    </p>
                  )}
                </Alert>
              )}

              {isDevMode && (
                <details className="text-left mb-6">
                  <summary className="cursor-pointer text-sm font-medium text-gray-700 mb-2">
                    Error Details (Development Mode)
                  </summary>
                  <div className="bg-gray-100 p-4 rounded-lg overflow-auto">
                    <p className="font-mono text-xs text-red-600 mb-2">{error.message}</p>
                    {error.stack && (
                      <pre className="font-mono text-xs text-gray-700 whitespace-pre-wrap">
                        {error.stack}
                      </pre>
                    )}
                    {errorInfo && (
                      <pre className="font-mono text-xs text-gray-600 mt-4 whitespace-pre-wrap">
                        {errorInfo.componentStack}
                      </pre>
                    )}
                  </div>
                </details>
              )}

              <div className="flex justify-center space-x-4">
                <Button onClick={() => window.location.reload()} variant="primary">
                  <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Refresh Page
                </Button>
                <Button onClick={() => window.history.back()} variant="ghost">
                  Go Back
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (level === 'section') {
    return (
      <Card className="m-4">
        <CardContent className="p-6">
          <div className="flex items-start space-x-4">
            <svg className="w-8 h-8 text-yellow-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 mb-1">
                This section couldn't load
              </h3>
              <p className="text-gray-600 mb-3">
                {error.message || 'An unexpected error occurred while loading this section.'}
              </p>
              <Button onClick={onReset} size="sm" variant="primary">
                Try Again
              </Button>
            </div>
          </div>
          {isDevMode && (
            <details className="mt-4">
              <summary className="cursor-pointer text-xs text-gray-500">
                Show error details
              </summary>
              <pre className="mt-2 text-xs bg-gray-100 p-2 rounded overflow-auto">
                {error.stack}
              </pre>
            </details>
          )}
        </CardContent>
      </Card>
    );
  }

  // Component level error
  return (
    <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
      <div className="flex items-center space-x-3">
        <svg className="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div className="flex-1">
          <p className="text-sm font-medium text-red-800">Component Error</p>
          <p className="text-xs text-red-600 mt-1">{error.message}</p>
        </div>
        <button
          onClick={onReset}
          className="text-red-600 hover:text-red-800"
          title="Retry"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>
    </div>
  );
};

/**
 * Higher-order component to wrap components with error boundary
 */
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<ErrorBoundaryProps, 'children'>
) {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;

  return WrappedComponent;
}

/**
 * Hook for error handling in functional components
 */
export function useErrorHandler() {
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    if (error) {
      throw error;
    }
  }, [error]);

  const resetError = () => setError(null);
  const captureError = (error: Error) => setError(error);

  return { captureError, resetError };
}

export default ErrorBoundary;