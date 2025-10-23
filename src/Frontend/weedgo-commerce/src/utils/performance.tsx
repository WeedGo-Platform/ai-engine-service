/**
 * Performance optimization utilities for React components
 */

import React, { useCallback, useEffect, useRef, useMemo } from 'react';

// Declare analytics on window
declare global {
  interface Window {
    analytics?: {
      track: (event: string, properties: any) => void;
      identify: (userId: string, traits?: any) => void;
      page: (name?: string, properties?: any) => void;
    };
  }
}

/**
 * Custom hook for debouncing values
 */
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

/**
 * Custom hook for throttling function calls
 */
export function useThrottle<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T {
  const lastRun = useRef(Date.now());

  return useCallback(
    (...args: Parameters<T>) => {
      if (Date.now() - lastRun.current >= delay) {
        callback(...args);
        lastRun.current = Date.now();
      }
    },
    [callback, delay]
  ) as T;
}

/**
 * Virtual scrolling hook for large lists
 */
export function useVirtualScroll<T>(
  items: T[],
  itemHeight: number,
  containerHeight: number,
  overscan = 3
) {
  const [scrollTop, setScrollTop] = useState(0);

  const startIndex = useMemo(
    () => Math.max(0, Math.floor(scrollTop / itemHeight) - overscan),
    [scrollTop, itemHeight, overscan]
  );

  const endIndex = useMemo(
    () =>
      Math.min(
        items.length - 1,
        Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
      ),
    [scrollTop, containerHeight, itemHeight, overscan, items.length]
  );

  const visibleItems = useMemo(
    () => items.slice(startIndex, endIndex + 1),
    [items, startIndex, endIndex]
  );

  const totalHeight = items.length * itemHeight;
  const offsetY = startIndex * itemHeight;

  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, []);

  return {
    visibleItems,
    totalHeight,
    offsetY,
    handleScroll,
    startIndex,
    endIndex,
  };
}

/**
 * Intersection Observer hook for lazy loading
 */
export function useIntersectionObserver(
  options: IntersectionObserverInit = {},
  targetRef: React.RefObject<Element>
): boolean {
  const [isIntersecting, setIsIntersecting] = useState(false);

  useEffect(() => {
    if (!targetRef.current) return;

    const observer = new IntersectionObserver(([entry]) => {
      setIsIntersecting(entry.isIntersecting);
    }, options);

    observer.observe(targetRef.current);

    return () => {
      observer.disconnect();
    };
  }, [targetRef, options]);

  return isIntersecting;
}

/**
 * Performance monitoring hook
 */
export function usePerformanceMonitor(componentName: string) {
  const renderCount = useRef(0);
  const renderStartTime = useRef(0);

  useEffect(() => {
    renderCount.current += 1;
    const renderTime = performance.now() - renderStartTime.current;

    if (process.env.NODE_ENV === 'development') {
      if (renderTime > 16) {
        // More than one frame (60fps)
        console.warn(
          `[Performance] ${componentName} took ${renderTime.toFixed(
            2
          )}ms to render (render #${renderCount.current})`
        );
      }
    }

    // Report to analytics in production
    if (process.env.NODE_ENV === 'production' && window.analytics) {
      window.analytics.track('Component Render', {
        component: componentName,
        renderTime,
        renderCount: renderCount.current,
      });
    }
  });

  renderStartTime.current = performance.now();
}

/**
 * Memory leak prevention hook
 */
export function useCleanup(cleanup: () => void) {
  const cleanupRef = useRef(cleanup);
  cleanupRef.current = cleanup;

  useEffect(() => {
    return () => {
      cleanupRef.current();
    };
  }, []);
}

/**
 * Lazy import with retry logic
 */
export async function lazyWithRetry<T>(
  importFunc: () => Promise<{ default: T }>,
  retries = 3,
  delay = 1000
): Promise<{ default: T }> {
  try {
    return await importFunc();
  } catch (error) {
    if (retries > 0) {
      await new Promise((resolve) => setTimeout(resolve, delay));
      return lazyWithRetry(importFunc, retries - 1, delay * 2);
    }
    throw error;
  }
}

/**
 * Batch state updates
 */
export function useBatchedState<T>(initialState: T) {
  const [state, setState] = useState(initialState);
  const pendingUpdates = useRef<Partial<T>[]>([]);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const batchedSetState = useCallback((update: Partial<T>) => {
    pendingUpdates.current.push(update);

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      setState((prevState) => {
        const merged = pendingUpdates.current.reduce(
          (acc, update) => ({ ...acc, ...update }),
          {}
        );
        pendingUpdates.current = [];
        return { ...prevState, ...merged };
      });
    }, 0);
  }, []);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return [state, batchedSetState] as const;
}

/**
 * Image preloading utility
 */
export function preloadImage(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve();
    img.onerror = reject;
    img.src = src;
  });
}

/**
 * Batch image preloading
 */
export async function preloadImages(urls: string[]): Promise<void[]> {
  const promises = urls.map(preloadImage);
  return Promise.all(promises);
}

/**
 * Request idle callback polyfill
 */
export const requestIdleCallback =
  window.requestIdleCallback ||
  function (cb: IdleRequestCallback) {
    const start = Date.now();
    return setTimeout(function () {
      cb({
        didTimeout: false,
        timeRemaining: function () {
          return Math.max(0, 50 - (Date.now() - start));
        },
      });
    }, 1);
  };

/**
 * Cancel idle callback polyfill
 */
export const cancelIdleCallback =
  window.cancelIdleCallback ||
  function (id: number) {
    clearTimeout(id);
  };

/**
 * Defer non-critical work
 */
export function deferWork(callback: () => void) {
  if ('requestIdleCallback' in window) {
    requestIdleCallback(callback);
  } else {
    setTimeout(callback, 0);
  }
}

/**
 * Memoized event handler creator
 */
export function createMemoizedHandler<T extends (...args: any[]) => any>(
  handler: T,
  deps: React.DependencyList
): T {
  return useCallback(handler, deps);
}

/**
 * Component render profiler
 */
export function withProfiler<P extends object>(
  Component: React.ComponentType<P>,
  componentName: string
): React.ComponentType<P> {
  return React.memo((props: P) => {
    usePerformanceMonitor(componentName);
    return <Component {...props} />;
  });
}

/**
 * Optimize re-renders with custom comparison
 */
export function arePropsEqual<T extends Record<string, any>>(
  prevProps: T,
  nextProps: T,
  keysToCompare?: (keyof T)[]
): boolean {
  const keys = keysToCompare || (Object.keys(prevProps) as (keyof T)[]);

  for (const key of keys) {
    if (!Object.is(prevProps[key], nextProps[key])) {
      return false;
    }
  }

  return true;
}

/**
 * Web Worker utilities
 */
export function createWorker<T, R>(
  workerFunction: (data: T) => R
): (data: T) => Promise<R> {
  const blob = new Blob(
    [`self.onmessage = function(e) { self.postMessage((${workerFunction})(e.data)); }`],
    { type: 'application/javascript' }
  );
  const worker = new Worker(URL.createObjectURL(blob));

  return (data: T) => {
    return new Promise((resolve, reject) => {
      worker.onmessage = (e) => resolve(e.data);
      worker.onerror = reject;
      worker.postMessage(data);
    });
  };
}

/**
 * Cache utility for expensive computations
 */
export class ComputationCache<K, V> {
  private cache = new Map<string, { value: V; timestamp: number }>();
  private maxAge: number;

  constructor(maxAge = 5 * 60 * 1000) {
    // 5 minutes default
    this.maxAge = maxAge;
  }

  get(key: K, compute: () => V): V {
    const keyStr = JSON.stringify(key);
    const cached = this.cache.get(keyStr);

    if (cached && Date.now() - cached.timestamp < this.maxAge) {
      return cached.value;
    }

    const value = compute();
    this.cache.set(keyStr, { value, timestamp: Date.now() });

    // Cleanup old entries
    if (this.cache.size > 100) {
      const entries = Array.from(this.cache.entries());
      entries.sort((a, b) => a[1].timestamp - b[1].timestamp);
      entries.slice(0, 50).forEach(([key]) => this.cache.delete(key));
    }

    return value;
  }

  clear() {
    this.cache.clear();
  }
}

// Add missing import
import { useState } from 'react';