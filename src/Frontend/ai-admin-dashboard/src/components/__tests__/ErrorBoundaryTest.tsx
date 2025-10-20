/**
 * Error Boundary Test Component
 *
 * Component to manually test error boundaries during development.
 * Provides buttons to trigger different types of errors.
 *
 * Usage (Development Only):
 * 1. Import this component in a development route
 * 2. Wrap it in an ErrorBoundary
 * 3. Click buttons to test error handling
 *
 * @example
 * <ErrorBoundary>
 *   <ErrorBoundaryTest />
 * </ErrorBoundary>
 */

import React, { useState } from 'react';
import { Bomb, AlertTriangle, Network, Lock } from 'lucide-react';

const ErrorBoundaryTest: React.FC = () => {
  const [shouldThrow, setShouldThrow] = useState(false);
  const [errorType, setErrorType] = useState<'render' | 'async' | 'event'>('render');

  // Throw error in render (caught by Error Boundary)
  if (shouldThrow && errorType === 'render') {
    throw new Error('Test error: Render phase error thrown intentionally');
  }

  // Throw error in async function (NOT caught by Error Boundary)
  const throwAsyncError = async () => {
    await new Promise((resolve) => setTimeout(resolve, 100));
    throw new Error('Test error: Async error thrown intentionally');
  };

  // Throw error in event handler (NOT caught by Error Boundary)
  const throwEventError = () => {
    throw new Error('Test error: Event handler error thrown intentionally');
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-3 mb-6">
          <Bomb className="w-6 h-6 text-red-600" />
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            Error Boundary Test Component
          </h2>
        </div>

        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-yellow-800 dark:text-yellow-200">
              <p className="font-medium mb-1">Development Tool</p>
              <p>
                This component is for testing error boundaries during development. It provides
                buttons to intentionally trigger different types of errors.
              </p>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
            Test Error Types
          </h3>

          {/* Render Error (Caught by Error Boundary) */}
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <div className="flex items-start gap-3 mb-3">
              <div className="bg-red-100 dark:bg-red-900/30 rounded p-2">
                <Bomb className="w-5 h-5 text-red-600 dark:text-red-400" />
              </div>
              <div className="flex-1">
                <h4 className="font-medium text-gray-900 dark:text-white mb-1">
                  Render Phase Error
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  Throws an error during component render. <strong>This will be caught</strong>{' '}
                  by the Error Boundary.
                </p>
                <button
                  onClick={() => {
                    setErrorType('render');
                    setShouldThrow(true);
                  }}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors"
                >
                  Trigger Render Error
                </button>
              </div>
            </div>
          </div>

          {/* Async Error (NOT Caught by Error Boundary) */}
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <div className="flex items-start gap-3 mb-3">
              <div className="bg-orange-100 dark:bg-orange-900/30 rounded p-2">
                <Network className="w-5 h-5 text-orange-600 dark:text-orange-400" />
              </div>
              <div className="flex-1">
                <h4 className="font-medium text-gray-900 dark:text-white mb-1">
                  Async Function Error
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  Throws an error in an async function.{' '}
                  <strong>This will NOT be caught</strong> by the Error Boundary. It will
                  appear in the console as an unhandled promise rejection.
                </p>
                <button
                  onClick={() => throwAsyncError()}
                  className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white font-medium rounded-lg transition-colors"
                >
                  Trigger Async Error
                </button>
              </div>
            </div>
          </div>

          {/* Event Handler Error (NOT Caught by Error Boundary) */}
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <div className="flex items-start gap-3 mb-3">
              <div className="bg-purple-100 dark:bg-purple-900/30 rounded p-2">
                <Lock className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div className="flex-1">
                <h4 className="font-medium text-gray-900 dark:text-white mb-1">
                  Event Handler Error
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  Throws an error in an event handler.{' '}
                  <strong>This will NOT be caught</strong> by the Error Boundary. It will
                  appear in the console.
                </p>
                <button
                  onClick={throwEventError}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors"
                >
                  Trigger Event Error
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
            Understanding Error Boundaries
          </h3>
          <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1 list-disc list-inside">
            <li>Error Boundaries catch errors during rendering, lifecycle methods, and constructors</li>
            <li>They do NOT catch errors in event handlers, async code, or server-side rendering</li>
            <li>For event handlers and async code, use try-catch blocks instead</li>
            <li>Error Boundaries only catch errors in child components, not in themselves</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ErrorBoundaryTest;
