/**
 * Skeleton Components
 * Loading placeholder components with shimmer animations
 * Provides better UX during data loading
 */

import React from 'react';

/**
 * Base skeleton component with shimmer animation
 */
interface SkeletonProps {
  className?: string;
  width?: string | number;
  height?: string | number;
  rounded?: boolean;
  circle?: boolean;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  className = '',
  width,
  height = 20,
  rounded = false,
  circle = false
}) => {
  const style: React.CSSProperties = {
    width: width || '100%',
    height,
    borderRadius: circle ? '50%' : rounded ? '0.375rem' : '0.25rem'
  };

  return (
    <div
      className={`animate-pulse bg-gray-200 ${className}`}
      style={style}
    />
  );
};

/**
 * Card skeleton component
 */
export const CardSkeleton: React.FC<{ lines?: number }> = ({ lines = 3 }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <Skeleton height={24} width="60%" className="mb-4" />
      {[...Array(lines)].map((_, i) => (
        <Skeleton
          key={i}
          height={16}
          width={i === lines - 1 ? "40%" : "100%"}
          className="mb-2"
        />
      ))}
    </div>
  );
};

/**
 * Stats card skeleton
 */
export const StatsCardSkeleton: React.FC = () => {
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <Skeleton height={16} width="60%" className="mb-2" />
          <Skeleton height={32} width="40%" className="mb-1" />
          <Skeleton height={12} width="80%" />
        </div>
        <Skeleton circle width={48} height={48} />
      </div>
    </div>
  );
};

/**
 * Table skeleton component
 */
export const TableSkeleton: React.FC<{ rows?: number; cols?: number }> = ({
  rows = 5,
  cols = 4
}) => {
  return (
    <div className="overflow-hidden">
      <div className="border-b border-gray-200 pb-3 mb-3">
        <div className="flex space-x-4">
          {[...Array(cols)].map((_, i) => (
            <Skeleton key={i} height={16} width={`${100 / cols}%`} />
          ))}
        </div>
      </div>
      <div className="space-y-3">
        {[...Array(rows)].map((_, rowIndex) => (
          <div key={rowIndex} className="flex space-x-4">
            {[...Array(cols)].map((_, colIndex) => (
              <Skeleton
                key={colIndex}
                height={20}
                width={`${100 / cols}%`}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};

/**
 * Agent card skeleton
 */
export const AgentCardSkeleton: React.FC = () => {
  return (
    <div className="p-4 border border-gray-200 rounded-lg">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-3">
          <Skeleton circle width={40} height={40} />
          <div>
            <Skeleton height={18} width={120} className="mb-1" />
            <Skeleton height={14} width={80} />
          </div>
        </div>
        <Skeleton width={60} height={24} rounded />
      </div>
      <div className="space-y-2">
        <div className="flex justify-between">
          <Skeleton height={14} width="30%" />
          <Skeleton height={14} width="20%" />
        </div>
        <div className="flex justify-between">
          <Skeleton height={14} width="35%" />
          <Skeleton height={14} width="15%" />
        </div>
      </div>
      <div className="mt-3">
        <Skeleton height={8} className="rounded-full" />
      </div>
    </div>
  );
};

/**
 * Chat message skeleton
 */
export const ChatMessageSkeleton: React.FC<{ isUser?: boolean }> = ({ isUser = false }) => {
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`flex items-start space-x-2 max-w-[70%] ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
        <Skeleton circle width={32} height={32} />
        <div className={`space-y-2 ${isUser ? 'items-end' : ''}`}>
          <Skeleton height={16} width={200} rounded />
          <Skeleton height={16} width={150} rounded />
          <Skeleton height={16} width={100} rounded />
        </div>
      </div>
    </div>
  );
};

/**
 * Chart skeleton
 */
export const ChartSkeleton: React.FC<{ height?: number }> = ({ height = 300 }) => {
  return (
    <div className="relative" style={{ height }}>
      <div className="absolute bottom-0 left-0 right-0 flex items-end justify-between space-x-2">
        {[...Array(10)].map((_, i) => (
          <div
            key={i}
            className="flex-1 bg-gray-200 rounded-t animate-pulse"
            style={{
              height: `${Math.random() * 80 + 20}%`,
              animationDelay: `${i * 100}ms`
            }}
          />
        ))}
      </div>
    </div>
  );
};

/**
 * Activity feed skeleton
 */
export const ActivitySkeleton: React.FC = () => {
  return (
    <div className="space-y-3">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="flex items-start space-x-3 p-3">
          <Skeleton circle width={32} height={32} />
          <div className="flex-1">
            <Skeleton height={16} width="80%" className="mb-1" />
            <Skeleton height={12} width="30%" />
          </div>
        </div>
      ))}
    </div>
  );
};

/**
 * Dashboard skeleton
 */
export const DashboardSkeleton: React.FC = () => {
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <Skeleton height={36} width={300} className="mb-2" />
          <Skeleton height={20} width={200} />
        </div>
        <div className="flex space-x-3">
          <Skeleton width={100} height={40} rounded />
          <Skeleton width={100} height={40} rounded />
        </div>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <StatsCardSkeleton key={i} />
        ))}
      </div>

      {/* Main content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <CardSkeleton lines={10} />
        </div>
        <div>
          <CardSkeleton lines={8} />
        </div>
      </div>
    </div>
  );
};

/**
 * List skeleton with multiple items
 */
export const ListSkeleton: React.FC<{ items?: number }> = ({ items = 5 }) => {
  return (
    <div className="space-y-3">
      {[...Array(items)].map((_, i) => (
        <div key={i} className="flex items-center space-x-4 p-3 border border-gray-200 rounded-lg">
          <Skeleton circle width={48} height={48} />
          <div className="flex-1">
            <Skeleton height={18} width="60%" className="mb-2" />
            <Skeleton height={14} width="40%" />
          </div>
          <Skeleton width={80} height={32} rounded />
        </div>
      ))}
    </div>
  );
};

/**
 * Form skeleton
 */
export const FormSkeleton: React.FC<{ fields?: number }> = ({ fields = 4 }) => {
  return (
    <div className="space-y-4">
      {[...Array(fields)].map((_, i) => (
        <div key={i}>
          <Skeleton height={16} width={100} className="mb-2" />
          <Skeleton height={40} rounded />
        </div>
      ))}
      <div className="flex justify-end space-x-3 mt-6">
        <Skeleton width={100} height={40} rounded />
        <Skeleton width={100} height={40} rounded />
      </div>
    </div>
  );
};

/**
 * Navigation skeleton
 */
export const NavigationSkeleton: React.FC = () => {
  return (
    <div className="p-4 space-y-2">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="flex items-center space-x-3 p-2">
          <Skeleton circle width={24} height={24} />
          <Skeleton height={16} width={120} />
        </div>
      ))}
    </div>
  );
};

/**
 * Grid skeleton for galleries
 */
export const GridSkeleton: React.FC<{ items?: number; cols?: number }> = ({
  items = 6,
  cols = 3
}) => {
  return (
    <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-${cols} gap-4`}>
      {[...Array(items)].map((_, i) => (
        <div key={i} className="aspect-square">
          <Skeleton height="100%" rounded />
        </div>
      ))}
    </div>
  );
};

/**
 * Custom shimmer effect component
 */
export const ShimmerEffect: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="relative overflow-hidden">
      {children}
      <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
    </div>
  );
};

/**
 * Pulse animation wrapper
 */
export const PulseLoader: React.FC<{ size?: 'sm' | 'md' | 'lg' }> = ({ size = 'md' }) => {
  const sizeClasses = {
    sm: 'w-2 h-2',
    md: 'w-3 h-3',
    lg: 'w-4 h-4'
  };

  return (
    <div className="flex space-x-1">
      {[...Array(3)].map((_, i) => (
        <div
          key={i}
          className={`${sizeClasses[size]} bg-blue-600 rounded-full animate-pulse`}
          style={{ animationDelay: `${i * 150}ms` }}
        />
      ))}
    </div>
  );
};

/**
 * Skeleton provider for theming
 */
interface SkeletonTheme {
  baseColor?: string;
  highlightColor?: string;
  duration?: number;
}

const SkeletonThemeContext = React.createContext<SkeletonTheme>({
  baseColor: '#e5e7eb',
  highlightColor: '#f3f4f6',
  duration: 1.5
});

export const SkeletonThemeProvider: React.FC<{
  children: React.ReactNode;
  theme?: SkeletonTheme;
}> = ({ children, theme }) => {
  return (
    <SkeletonThemeContext.Provider value={theme || {}}>
      {children}
    </SkeletonThemeContext.Provider>
  );
};

// Add CSS for animations (add to global styles)
const skeletonStyles = `
@keyframes shimmer {
  100% {
    transform: translateX(100%);
  }
}

.animate-shimmer {
  animation: shimmer 1.5s ease-in-out infinite;
}
`;

export default {
  Skeleton,
  CardSkeleton,
  StatsCardSkeleton,
  TableSkeleton,
  AgentCardSkeleton,
  ChatMessageSkeleton,
  ChartSkeleton,
  ActivitySkeleton,
  DashboardSkeleton,
  ListSkeleton,
  FormSkeleton,
  NavigationSkeleton,
  GridSkeleton,
  ShimmerEffect,
  PulseLoader,
  SkeletonThemeProvider
};