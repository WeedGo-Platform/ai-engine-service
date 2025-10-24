// Type fixes for remaining issues

// Fix for ProductService.ts - RequestOptions doesn't have useCache
// This would need to be fixed in the service file directly

// Fix for window.analytics type
declare global {
  interface Window {
    analytics?: {
      track: (event: string, properties: any) => void;
      identify: (userId: string, traits?: any) => void;
      page: (name?: string, properties?: any) => void;
    };
  }
}

// Fix for CategoryCard onClick handler wrapper
export function wrapCategoryClickHandler(
  onClick?: (category: any) => void
): ((event: React.MouseEvent<HTMLDivElement>) => void) | undefined {
  if (!onClick) return undefined;
  return (event: React.MouseEvent<HTMLDivElement>) => {
    // Extract category from event target if needed
    const category = (event.currentTarget as any).dataset.category;
    onClick(category);
  };
}

// Type for SearchBar props with showButton
export interface ExtendedSearchBarProps {
  showButton?: boolean;
  // ... other props
}

export {};