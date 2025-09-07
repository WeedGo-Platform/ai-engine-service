import { useEffect, useRef, RefObject } from 'react';

export function useClickOutside<T extends HTMLElement = HTMLElement>(
  handler: () => void,
  excludeRefs?: RefObject<HTMLElement>[]
): RefObject<T> {
  const ref = useRef<T>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      // Check if click is inside the main ref
      if (ref.current && ref.current.contains(event.target as Node)) {
        return;
      }

      // Check if click is inside any of the excluded refs
      if (excludeRefs) {
        for (const excludeRef of excludeRefs) {
          if (excludeRef.current && excludeRef.current.contains(event.target as Node)) {
            return;
          }
        }
      }

      // Click was outside all refs, call handler
      handler();
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [handler, excludeRefs]);

  return ref;
}