/**
 * Lightweight persistent state hooks
 * Ensures proper data partitioning per user
 */

import { useState, useEffect, useCallback } from 'react';

type SetValue<T> = (value: T | ((prev: T) => T)) => void;

/**
 * Get a properly namespaced storage key to prevent data leakage
 */
function getStorageKey(key: string): string {
  const userId = localStorage.getItem('weedgo_user_id') ||
                 sessionStorage.getItem('weedgo_user_id') ||
                 'default';
  return `weedgo_${userId}_${key}`;
}

/**
 * Persist any state to localStorage
 */
export function usePersistentState<T>(
  key: string,
  defaultValue: T
): [T, SetValue<T>, () => void] {
  const storageKey = getStorageKey(key);

  const [state, setState] = useState<T>(() => {
    try {
      const stored = localStorage.getItem(storageKey);
      return stored ? JSON.parse(stored) : defaultValue;
    } catch {
      return defaultValue;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(storageKey, JSON.stringify(state));
    } catch {
      // Storage full or disabled
    }
  }, [storageKey, state]);

  const clear = useCallback(() => {
    localStorage.removeItem(storageKey);
    setState(defaultValue);
  }, [storageKey, defaultValue]);

  return [state, setState, clear];
}

/**
 * Persist tab selection
 */
export function usePersistentTab<T extends string>(
  pageKey: string,
  defaultTab: T
): [T, (tab: T) => void] {
  const [tab, setTab] = usePersistentState<T>(`tab_${pageKey}`, defaultTab);
  return [tab, setTab];
}

/**
 * Persist filter state
 */
export function usePersistentFilters<T extends Record<string, any>>(
  pageKey: string,
  defaultFilters: T
): [T, (filters: T | ((prev: T) => T)) => void, () => void] {
  return usePersistentState<T>(`filters_${pageKey}`, defaultFilters);
}