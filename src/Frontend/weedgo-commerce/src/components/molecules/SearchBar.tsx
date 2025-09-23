import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { MagnifyingGlassIcon as SearchIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { clsx } from 'clsx';
import { Input } from '../atoms/Input';
import { Button } from '../atoms/Button';
import { useDebounce } from '@/hooks/useDebounce';
import { searchService } from '@services/searchService';

export interface SearchBarProps {
  placeholder?: string;
  onSearch?: (query: string) => void;
  showSuggestions?: boolean;
  variant?: 'default' | 'compact' | 'expanded';
  className?: string;
}

/**
 * SearchBar component with debounced search and suggestions
 */
export const SearchBar: React.FC<SearchBarProps> = ({
  placeholder,
  onSearch,
  showSuggestions = true,
  variant = 'default',
  className
}) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestionsList, setShowSuggestionsList] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const debouncedQuery = useDebounce(query, 300);

  useEffect(() => {
    if (debouncedQuery && showSuggestions) {
      fetchSuggestions(debouncedQuery);
    } else {
      setSuggestions([]);
    }
  }, [debouncedQuery]);

  const fetchSuggestions = async (searchQuery: string) => {
    setIsLoading(true);
    try {
      const results = await searchService.getSearchSuggestions(searchQuery);
      const suggestionTexts = results.map(result => result.text);
      setSuggestions(suggestionTexts);
      setShowSuggestionsList(true);
    } catch (error) {
      console.error('Error fetching suggestions:', error);
      setSuggestions([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      if (onSearch) {
        onSearch(query);
      } else {
        navigate(`/products?search=${encodeURIComponent(query)}`);
      }
      setShowSuggestionsList(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    setShowSuggestionsList(false);
    if (onSearch) {
      onSearch(suggestion);
    } else {
      navigate(`/products?search=${encodeURIComponent(suggestion)}`);
    }
  };

  const clearSearch = () => {
    setQuery('');
    setSuggestions([]);
    setShowSuggestionsList(false);
  };

  const variantClasses = {
    default: 'w-full max-w-lg',
    compact: 'w-full max-w-sm',
    expanded: 'w-full'
  };

  return (
    <div className={clsx('relative', variantClasses[variant], className)}>
      <form onSubmit={handleSubmit} className="relative">
        <Input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => suggestions.length > 0 && setShowSuggestionsList(true)}
          placeholder={placeholder || t('search.placeholder')}
          leftIcon={<SearchIcon className="h-5 w-5" />}
          rightIcon={
            query && (
              <button
                type="button"
                onClick={clearSearch}
                className="hover:bg-gray-200 dark:hover:bg-gray-700 rounded-full p-1"
              >
                <XMarkIcon className="h-4 w-4" />
              </button>
            )
          }
          className="pr-24"
        />

        <Button
          type="submit"
          size="sm"
          className="absolute right-1 top-1"
          isLoading={isLoading}
        >
          {t('search.button')}
        </Button>
      </form>

      {/* Suggestions dropdown */}
      {showSuggestionsList && suggestions.length > 0 && (
        <div className="absolute top-full mt-1 w-full bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50 max-h-64 overflow-y-auto">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              onClick={() => handleSuggestionClick(suggestion)}
              className="w-full px-4 py-3 text-left hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors flex items-center space-x-2"
            >
              <SearchIcon className="h-4 w-4 text-gray-400" />
              <span className="text-sm">{suggestion}</span>
            </button>
          ))}
        </div>
      )}

      {/* Loading state */}
      {isLoading && showSuggestions && (
        <div className="absolute top-full mt-1 w-full bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50 p-4">
          <div className="animate-pulse space-y-2">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
          </div>
        </div>
      )}
    </div>
  );
};