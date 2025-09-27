/**
 * Loading Components
 */

import React from 'react';

interface ISpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  color?: string;
  className?: string;
}

export const Spinner: React.FC<ISpinnerProps> = ({
  size = 'md',
  color = 'text-blue-600',
  className = ''
}) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12'
  };

  return (
    <div className={`flex justify-center items-center ${className}`}>
      <svg
        className={`animate-spin ${sizeClasses[size]} ${color}`}
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
    </div>
  );
};

interface ILoadingOverlayProps {
  message?: string;
}

export const LoadingOverlay: React.FC<ILoadingOverlayProps> = ({
  message = 'Loading...'
}) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 flex flex-col items-center space-y-4">
        <Spinner size="lg" />
        <p className="text-gray-700 font-medium">{message}</p>
      </div>
    </div>
  );
};

interface ISkeletonProps {
  className?: string;
  variant?: 'text' | 'rect' | 'circle';
  animation?: boolean;
}

export const Skeleton: React.FC<ISkeletonProps> = ({
  className = '',
  variant = 'rect',
  animation = true
}) => {
  const variantClasses = {
    text: 'h-4 rounded',
    rect: 'h-20 rounded',
    circle: 'h-12 w-12 rounded-full'
  };

  const animationClass = animation ? 'animate-pulse' : '';

  return (
    <div
      className={`bg-gray-200 ${variantClasses[variant]} ${animationClass} ${className}`}
    />
  );
};

interface ILoadingCardProps {
  lines?: number;
}

export const LoadingCard: React.FC<ILoadingCardProps> = ({ lines = 3 }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm p-6 animate-pulse">
      <Skeleton className="h-6 w-1/3 mb-4" />
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className="h-4 w-full mb-2" />
      ))}
    </div>
  );
};

interface ILoadingStateProps {
  loading: boolean;
  error?: Error | null;
  children: React.ReactNode;
  loadingComponent?: React.ReactNode;
  errorComponent?: React.ReactNode;
}

export const LoadingState: React.FC<ILoadingStateProps> = ({
  loading,
  error,
  children,
  loadingComponent,
  errorComponent
}) => {
  if (loading) {
    return <>{loadingComponent || <Spinner size="lg" />}</>;
  }

  if (error) {
    return (
      <>
        {errorComponent || (
          <div className="text-center py-8">
            <p className="text-red-600">Error: {error.message}</p>
          </div>
        )}
      </>
    );
  }

  return <>{children}</>;
};