/**
 * Advanced search bar with autocomplete
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { ClockIcon } from '@heroicons/react/20/solid';
import { searchService } from '@services/searchService';
import { useDebounce } from '@hooks/useDebounce';
import type { SearchSuggestion } from '@services/searchService';

interface SearchBarProps {
  placeholder?: string;
  onSearch?: (query: string) => void;
  className?: string;
  showHistory?: boolean;
  showSuggestions?: boolean;
  autoFocus?: boolean;
}

const SearchBar: React.FC<SearchBarProps> = ({
  placeholder = 'Search products, brands, strains...',
  onSearch,
  className = '',
  showHistory = true,
  showSuggestions = true,
  autoFocus = false,
}) => {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
  const [history, setHistory] = useState<string[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [loading, setLoading] = useState(false);

  const searchRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const debouncedQuery = useDebounce(query, 300);

  // Load search history on mount
  useEffect(() => {
    if (showHistory) {
      setHistory(searchService.getSearchHistory());
    }
  }, [showHistory]);

  // Fetch suggestions when query changes
  useEffect(() => {
    const fetchSuggestions = async () => {
      if (!debouncedQuery || debouncedQuery.length < 2 || !showSuggestions) {
        setSuggestions([]);
        return;
      }

      setLoading(true);
      try {
        const results = await searchService.getSearchSuggestions(debouncedQuery);
        setSuggestions(results);
      } catch (error) {
        console.error('Failed to fetch suggestions:', error);
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    };

    fetchSuggestions();
  }, [debouncedQuery, showSuggestions]);

  // Handle click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSearch = useCallback((searchQuery: string) => {
    if (!searchQuery.trim()) return;

    setQuery(searchQuery);
    setIsOpen(false);

    if (onSearch) {
      onSearch(searchQuery);
    } else {
      // Navigate to products page with search query
      navigate(`/products?q=${encodeURIComponent(searchQuery)}`);
    }

    // Update history
    if (showHistory) {
      const updatedHistory = searchService.getSearchHistory();
      setHistory(updatedHistory);
    }
  }, [navigate, onSearch, showHistory]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    const items = [...suggestions, ...history.slice(0, 3)];

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev < items.length - 1 ? prev + 1 : 0
        );
        break;

      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev > 0 ? prev - 1 : items.length - 1
        );
        break;

      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
          handleSearch(suggestions[selectedIndex].text);
        } else if (selectedIndex >= suggestions.length) {
          const historyIndex = selectedIndex - suggestions.length;
          handleSearch(history[historyIndex]);
        } else {
          handleSearch(query);
        }
        break;

      case 'Escape':
        setIsOpen(false);
        inputRef.current?.blur();
        break;
    }
  };

  const clearSearch = () => {
    setQuery('');
    setSuggestions([]);
    setSelectedIndex(-1);
    inputRef.current?.focus();
  };

  const clearHistory = () => {
    searchService.clearSearchHistory();
    setHistory([]);
  };

  const renderDropdown = () => {
    if (!isOpen) return null;

    const hasContent = suggestions.length > 0 || (history.length > 0 && (!query || query.length < 2));

    if (!hasContent && !loading) return null;

    return (
      <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden z-50 max-h-96 overflow-y-auto">
        {loading && (
          <div className="p-4 text-center text-gray-500">
            <svg className="animate-spin h-5 w-5 mx-auto text-gray-400" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          </div>
        )}

        {/* Suggestions */}
        {suggestions.length > 0 && !loading && (
          <div>
            <div className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Suggestions
            </div>
            {suggestions.map((suggestion, index) => (
              <button
                key={suggestion.id}
                className={`w-full text-left px-4 py-2 hover:bg-gray-50 focus:bg-gray-50 focus:outline-none ${
                  selectedIndex === index ? 'bg-gray-50' : ''
                }`}
                onClick={() => handleSearch(suggestion.text)}
                onMouseEnter={() => setSelectedIndex(index)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <MagnifyingGlassIcon className="h-4 w-4 text-gray-400 mr-3" />
                    <span className="text-sm text-gray-900">{suggestion.text}</span>
                    {suggestion.type && (
                      <span className="ml-2 text-xs text-gray-500 capitalize">
                        in {suggestion.type}
                      </span>
                    )}
                  </div>
                  {suggestion.count && (
                    <span className="text-xs text-gray-400">
                      {suggestion.count} results
                    </span>
                  )}
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Search History */}
        {history.length > 0 && (!query || query.length < 2) && !loading && (
          <div>
            <div className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider flex justify-between items-center">
              <span>Recent Searches</span>
              <button
                onClick={clearHistory}
                className="text-xs text-blue-600 hover:text-blue-800 normal-case font-normal"
              >
                Clear
              </button>
            </div>
            {history.slice(0, 5).map((item, index) => {
              const actualIndex = suggestions.length + index;
              return (
                <button
                  key={`history-${index}`}
                  className={`w-full text-left px-4 py-2 hover:bg-gray-50 focus:bg-gray-50 focus:outline-none ${
                    selectedIndex === actualIndex ? 'bg-gray-50' : ''
                  }`}
                  onClick={() => handleSearch(item)}
                  onMouseEnter={() => setSelectedIndex(actualIndex)}
                >
                  <div className="flex items-center">
                    <ClockIcon className="h-4 w-4 text-gray-400 mr-3" />
                    <span className="text-sm text-gray-900">{item}</span>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>
    );
  };

  return (
    <div ref={searchRef} className={`relative ${className}`}>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSearch(query);
        }}
        className="relative"
      >
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            ref={inputRef}
            type="search"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setIsOpen(true);
            }}
            onFocus={() => setIsOpen(true)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            autoFocus={autoFocus}
            className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
            aria-label="Search"
            aria-autocomplete="list"
            aria-controls="search-suggestions"
            aria-expanded={isOpen}
          />
          {query && (
            <button
              type="button"
              onClick={clearSearch}
              className="absolute right-3 top-1/2 transform -translate-y-1/2"
              aria-label="Clear search"
            >
              <XMarkIcon className="h-5 w-5 text-gray-400 hover:text-gray-600" />
            </button>
          )}
        </div>
      </form>

      {renderDropdown()}
    </div>
  );
};

export default SearchBar;