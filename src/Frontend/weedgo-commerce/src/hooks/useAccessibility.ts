/**
 * Accessibility hooks for keyboard navigation and ARIA support
 */

import { useEffect, useRef, useCallback, useState } from 'react';

/**
 * Hook for managing focus trap within a component
 */
export const useFocusTrap = (isActive: boolean = true) => {
  const containerRef = useRef<HTMLElement>(null);
  const firstFocusableRef = useRef<HTMLElement | null>(null);
  const lastFocusableRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!isActive || !containerRef.current) return;

    const container = containerRef.current;
    const focusableSelectors = [
      'a[href]',
      'button:not([disabled])',
      'textarea:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
    ];

    const focusableElements = container.querySelectorAll<HTMLElement>(
      focusableSelectors.join(', ')
    );

    if (focusableElements.length > 0) {
      firstFocusableRef.current = focusableElements[0];
      lastFocusableRef.current = focusableElements[focusableElements.length - 1];

      // Focus first element
      firstFocusableRef.current?.focus();
    }

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        // Shift + Tab
        if (document.activeElement === firstFocusableRef.current) {
          e.preventDefault();
          lastFocusableRef.current?.focus();
        }
      } else {
        // Tab
        if (document.activeElement === lastFocusableRef.current) {
          e.preventDefault();
          firstFocusableRef.current?.focus();
        }
      }
    };

    container.addEventListener('keydown', handleKeyDown);

    return () => {
      container.removeEventListener('keydown', handleKeyDown);
    };
  }, [isActive]);

  return containerRef;
};

/**
 * Hook for keyboard navigation with arrow keys
 */
export const useArrowNavigation = (
  items: HTMLElement[],
  options: {
    orientation?: 'horizontal' | 'vertical' | 'both';
    loop?: boolean;
    onSelect?: (index: number) => void;
    onEscape?: () => void;
  } = {}
) => {
  const {
    orientation = 'vertical',
    loop = true,
    onSelect,
    onEscape,
  } = options;

  const currentIndex = useRef(0);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      const keyActions: Record<string, () => void> = {
        ArrowUp: () => {
          if (orientation === 'horizontal') return;
          e.preventDefault();
          moveFocus(-1);
        },
        ArrowDown: () => {
          if (orientation === 'horizontal') return;
          e.preventDefault();
          moveFocus(1);
        },
        ArrowLeft: () => {
          if (orientation === 'vertical') return;
          e.preventDefault();
          moveFocus(-1);
        },
        ArrowRight: () => {
          if (orientation === 'vertical') return;
          e.preventDefault();
          moveFocus(1);
        },
        Home: () => {
          e.preventDefault();
          currentIndex.current = 0;
          items[0]?.focus();
        },
        End: () => {
          e.preventDefault();
          currentIndex.current = items.length - 1;
          items[items.length - 1]?.focus();
        },
        Enter: () => {
          e.preventDefault();
          onSelect?.(currentIndex.current);
        },
        ' ': () => {
          e.preventDefault();
          onSelect?.(currentIndex.current);
        },
        Escape: () => {
          e.preventDefault();
          onEscape?.();
        },
      };

      keyActions[e.key]?.();
    },
    [items, orientation, loop, onSelect, onEscape]
  );

  const moveFocus = (direction: number) => {
    let newIndex = currentIndex.current + direction;

    if (loop) {
      if (newIndex < 0) {
        newIndex = items.length - 1;
      } else if (newIndex >= items.length) {
        newIndex = 0;
      }
    } else {
      newIndex = Math.max(0, Math.min(items.length - 1, newIndex));
    }

    currentIndex.current = newIndex;
    items[newIndex]?.focus();
  };

  useEffect(() => {
    items.forEach((item) => {
      item.addEventListener('keydown', handleKeyDown);
    });

    return () => {
      items.forEach((item) => {
        item.removeEventListener('keydown', handleKeyDown);
      });
    };
  }, [items, handleKeyDown]);

  return {
    currentIndex: currentIndex.current,
    setFocus: (index: number) => {
      currentIndex.current = index;
      items[index]?.focus();
    },
  };
};

/**
 * Hook for managing ARIA live regions for announcements
 */
export const useAnnouncement = () => {
  const announcementRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    // Create live region if it doesn't exist
    if (!announcementRef.current) {
      const liveRegion = document.createElement('div');
      liveRegion.setAttribute('role', 'status');
      liveRegion.setAttribute('aria-live', 'polite');
      liveRegion.setAttribute('aria-atomic', 'true');
      liveRegion.className = 'sr-only'; // Screen reader only
      document.body.appendChild(liveRegion);
      announcementRef.current = liveRegion;
    }

    return () => {
      if (announcementRef.current) {
        document.body.removeChild(announcementRef.current);
        announcementRef.current = null;
      }
    };
  }, []);

  const announce = useCallback((message: string, priority: 'polite' | 'assertive' = 'polite') => {
    if (announcementRef.current) {
      announcementRef.current.setAttribute('aria-live', priority);
      announcementRef.current.textContent = message;

      // Clear after announcement
      setTimeout(() => {
        if (announcementRef.current) {
          announcementRef.current.textContent = '';
        }
      }, 1000);
    }
  }, []);

  return announce;
};

/**
 * Hook for escape key handler
 */
export const useEscapeKey = (handler: () => void, isActive: boolean = true) => {
  useEffect(() => {
    if (!isActive) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        handler();
      }
    };

    document.addEventListener('keydown', handleEscape);

    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [handler, isActive]);
};

/**
 * Hook for managing roving tabindex pattern
 */
export const useRovingTabIndex = (itemsCount: number) => {
  const [activeIndex, setActiveIndex] = useState(0);

  const getTabIndex = useCallback(
    (index: number) => (index === activeIndex ? 0 : -1),
    [activeIndex]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent, currentIndex: number) => {
      switch (e.key) {
        case 'ArrowRight':
        case 'ArrowDown':
          e.preventDefault();
          setActiveIndex((prev) => (prev + 1) % itemsCount);
          break;
        case 'ArrowLeft':
        case 'ArrowUp':
          e.preventDefault();
          setActiveIndex((prev) => (prev - 1 + itemsCount) % itemsCount);
          break;
        case 'Home':
          e.preventDefault();
          setActiveIndex(0);
          break;
        case 'End':
          e.preventDefault();
          setActiveIndex(itemsCount - 1);
          break;
      }
    },
    [itemsCount]
  );

  return {
    activeIndex,
    getTabIndex,
    handleKeyDown,
    setActiveIndex,
  };
};

/**
 * Hook for skip navigation links
 */
export const useSkipLinks = () => {
  const skipToMain = useCallback(() => {
    const mainContent = document.getElementById('main-content') || document.querySelector('main');
    if (mainContent) {
      mainContent.focus();
      mainContent.scrollIntoView();
    }
  }, []);

  const skipToNavigation = useCallback(() => {
    const nav = document.querySelector('nav') || document.getElementById('navigation');
    if (nav instanceof HTMLElement) {
      nav.focus();
      nav.scrollIntoView();
    }
  }, []);

  const skipToSearch = useCallback(() => {
    const search = document.querySelector('[role="search"]') || document.getElementById('search');
    if (search instanceof HTMLElement) {
      search.focus();
      search.scrollIntoView();
    }
  }, []);

  return {
    skipToMain,
    skipToNavigation,
    skipToSearch,
  };
};

/**
 * Hook for managing keyboard shortcuts
 */
export const useKeyboardShortcuts = (
  shortcuts: Record<string, () => void>,
  isActive: boolean = true
) => {
  useEffect(() => {
    if (!isActive) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Build key combination string
      const keys: string[] = [];
      if (e.ctrlKey) keys.push('Ctrl');
      if (e.altKey) keys.push('Alt');
      if (e.shiftKey) keys.push('Shift');
      if (e.metaKey) keys.push('Meta');

      // Add the actual key
      if (e.key !== 'Control' && e.key !== 'Alt' && e.key !== 'Shift' && e.key !== 'Meta') {
        keys.push(e.key.length === 1 ? e.key.toUpperCase() : e.key);
      }

      const combination = keys.join('+');

      if (shortcuts[combination]) {
        e.preventDefault();
        shortcuts[combination]();
      }
    };

    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [shortcuts, isActive]);
};

/**
 * Hook for managing focus restoration
 */
export const useFocusRestoration = () => {
  const previousFocus = useRef<HTMLElement | null>(null);

  const saveFocus = useCallback(() => {
    previousFocus.current = document.activeElement as HTMLElement;
  }, []);

  const restoreFocus = useCallback(() => {
    if (previousFocus.current && previousFocus.current.focus) {
      previousFocus.current.focus();
    }
  }, []);

  return {
    saveFocus,
    restoreFocus,
  };
};