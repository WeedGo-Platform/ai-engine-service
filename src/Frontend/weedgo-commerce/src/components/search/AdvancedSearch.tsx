/**
 * Advanced search component with filtering capabilities
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  MagnifyingGlassIcon,
  XMarkIcon,
  AdjustmentsHorizontalIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from '@heroicons/react/24/outline';
import {
  searchService,
  SearchFilters,
  SearchResult,
  SearchSuggestion,
} from '@services/searchService';
import { AccessibleButton } from '@components/common/AccessibleComponents';
import { debounce } from '@utils/helpers';
import toast from 'react-hot-toast';

interface AdvancedSearchProps {
  onSearchResults?: (results: SearchResult) => void;
  showFilters?: boolean;
  className?: string;
}

const AdvancedSearch: React.FC<AdvancedSearchProps> = ({
  onSearchResults,
  showFilters = true,
  className = '',
}) => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Search state
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [filters, setFilters] = useState<SearchFilters>({});
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [searchHistory, setSearchHistory] = useState<string[]>([]);

  // Filter options
  const [facets, setFacets] = useState<any>({});

  // Initialize filters from URL params
  useEffect(() => {
    const initialFilters: SearchFilters = {
      query: searchParams.get('q') || undefined,
      category: searchParams.get('category') || undefined,
      brand: searchParams.get('brand') || undefined,
      priceMin: searchParams.get('price_min') ? Number(searchParams.get('price_min')) : undefined,
      priceMax: searchParams.get('price_max') ? Number(searchParams.get('price_max')) : undefined,
      thcMin: searchParams.get('thc_min') ? Number(searchParams.get('thc_min')) : undefined,
      thcMax: searchParams.get('thc_max') ? Number(searchParams.get('thc_max')) : undefined,
      cbdMin: searchParams.get('cbd_min') ? Number(searchParams.get('cbd_min')) : undefined,
      cbdMax: searchParams.get('cbd_max') ? Number(searchParams.get('cbd_max')) : undefined,
      strain: searchParams.get('strain')?.split(',') || undefined,
      inStock: searchParams.get('in_stock') === 'true' || undefined,
      onSale: searchParams.get('on_sale') === 'true' || undefined,
      sortBy: (searchParams.get('sort') as any) || undefined,
    };

    setFilters(initialFilters);
    if (initialFilters.query) {
      setQuery(initialFilters.query);
    }
  }, [searchParams]);

  // Load search history
  useEffect(() => {
    const history = searchService.getSearchHistory();
    setSearchHistory(history.map(h => h.query).slice(0, 5));
  }, []);

  // Debounced search suggestions
  const getSuggestions = useCallback(
    debounce(async (searchQuery: string) => {
      if (searchQuery.length < 2) {
        setSuggestions([]);
        return;
      }

      try {
        const results = await searchService.getSearchSuggestions(searchQuery);
        setSuggestions(results);
      } catch (error) {
        setSuggestions([]);
      }
    }, 300),
    []
  );

  // Handle query input change
  const handleQueryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    getSuggestions(value);
    setShowSuggestions(true);
  };

  // Perform search
  const handleSearch = async (e?: React.FormEvent) => {
    e?.preventDefault();

    if (!query.trim() && Object.keys(filters).length === 0) {
      toast.error('Please enter a search term or select filters');
      return;
    }

    setIsSearching(true);
    setShowSuggestions(false);

    try {
      const searchFilters: SearchFilters = {
        ...filters,
        query: query.trim() || undefined,
      };

      const results = await searchService.searchProducts(searchFilters);

      // Update URL params
      const newParams = new URLSearchParams();
      Object.entries(searchFilters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            newParams.set(key, value.join(','));
          } else {
            newParams.set(key, String(value));
          }
        }
      });

      setSearchParams(newParams);

      // Callback with results
      if (onSearchResults) {
        onSearchResults(results);
      } else {
        // Navigate to search results page
        navigate(`/search?${newParams.toString()}`);
      }

      // Update facets from results
      if (results.facets) {
        setFacets(results.facets);
      }
    } catch (error) {
      toast.error('Search failed. Please try again.');
    } finally {
      setIsSearching(false);
    }
  };

  // Handle suggestion click
  const handleSuggestionClick = (suggestion: SearchSuggestion) => {
    setQuery(suggestion.text);
    setShowSuggestions(false);
    handleSearch();
  };

  // Clear search
  const handleClearSearch = () => {
    setQuery('');
    setFilters({});
    setSuggestions([]);
    setShowSuggestions(false);
    searchInputRef.current?.focus();
  };

  // Handle filter change
  const handleFilterChange = (filterKey: keyof SearchFilters, value: any) => {
    setFilters(prev => ({
      ...prev,
      [filterKey]: value,
    }));
  };

  // Natural language search
  const handleNaturalSearch = () => {
    const parsedFilters = searchService.parseNaturalQuery(query);
    setFilters(parsedFilters);
    handleSearch();
  };

  // Quick filter buttons
  const renderQuickFilters = () => (
    <div className="flex flex-wrap gap-2 mt-4">
      <button
        onClick={() => handleFilterChange('inStock', !filters.inStock)}
        className={`px-3 py-1 rounded-full text-sm ${
          filters.inStock
            ? 'bg-green-600 text-white'
            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
        }`}
      >
        In Stock
      </button>
      <button
        onClick={() => handleFilterChange('onSale', !filters.onSale)}
        className={`px-3 py-1 rounded-full text-sm ${
          filters.onSale
            ? 'bg-red-600 text-white'
            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
        }`}
      >
        On Sale
      </button>
      {['indica', 'sativa', 'hybrid'].map(strain => (
        <button
          key={strain}
          onClick={() => {
            const currentStrains = filters.strain || [];
            const newStrains = currentStrains.includes(strain)
              ? currentStrains.filter(s => s !== strain)
              : [...currentStrains, strain];
            handleFilterChange('strain', newStrains.length > 0 ? newStrains : undefined);
          }}
          className={`px-3 py-1 rounded-full text-sm capitalize ${
            filters.strain?.includes(strain)
              ? 'bg-purple-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          {strain}
        </button>
      ))}
    </div>
  );

  // Advanced filters panel
  const renderAdvancedFilters = () => (
    <div className={`mt-4 p-4 border rounded-lg bg-gray-50 ${showAdvancedFilters ? '' : 'hidden'}`}>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Category */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Category
          </label>
          <select
            value={filters.category || ''}
            onChange={(e) => handleFilterChange('category', e.target.value || undefined)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
          >
            <option value="">All Categories</option>
            <option value="flower">Flower</option>
            <option value="edibles">Edibles</option>
            <option value="concentrates">Concentrates</option>
            <option value="vapes">Vapes</option>
            <option value="accessories">Accessories</option>
          </select>
        </div>

        {/* Price Range */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Price Range
          </label>
          <div className="flex gap-2">
            <input
              type="number"
              placeholder="Min"
              value={filters.priceMin || ''}
              onChange={(e) => handleFilterChange('priceMin', e.target.value ? Number(e.target.value) : undefined)}
              className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
            />
            <input
              type="number"
              placeholder="Max"
              value={filters.priceMax || ''}
              onChange={(e) => handleFilterChange('priceMax', e.target.value ? Number(e.target.value) : undefined)}
              className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
            />
          </div>
        </div>

        {/* THC Range */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            THC % Range
          </label>
          <div className="flex gap-2">
            <input
              type="number"
              placeholder="Min"
              value={filters.thcMin || ''}
              onChange={(e) => handleFilterChange('thcMin', e.target.value ? Number(e.target.value) : undefined)}
              className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
            />
            <input
              type="number"
              placeholder="Max"
              value={filters.thcMax || ''}
              onChange={(e) => handleFilterChange('thcMax', e.target.value ? Number(e.target.value) : undefined)}
              className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
            />
          </div>
        </div>

        {/* CBD Range */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            CBD % Range
          </label>
          <div className="flex gap-2">
            <input
              type="number"
              placeholder="Min"
              value={filters.cbdMin || ''}
              onChange={(e) => handleFilterChange('cbdMin', e.target.value ? Number(e.target.value) : undefined)}
              className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
            />
            <input
              type="number"
              placeholder="Max"
              value={filters.cbdMax || ''}
              onChange={(e) => handleFilterChange('cbdMax', e.target.value ? Number(e.target.value) : undefined)}
              className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
            />
          </div>
        </div>

        {/* Sort By */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Sort By
          </label>
          <select
            value={filters.sortBy || 'relevance'}
            onChange={(e) => handleFilterChange('sortBy', e.target.value as any)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
          >
            <option value="relevance">Relevance</option>
            <option value="price_asc">Price: Low to High</option>
            <option value="price_desc">Price: High to Low</option>
            <option value="rating">Highest Rated</option>
            <option value="newest">Newest First</option>
            <option value="name_asc">Name: A to Z</option>
            <option value="name_desc">Name: Z to A</option>
            <option value="thc_desc">THC: High to Low</option>
            <option value="cbd_desc">CBD: High to Low</option>
          </select>
        </div>

        {/* Rating */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Minimum Rating
          </label>
          <select
            value={filters.rating || ''}
            onChange={(e) => handleFilterChange('rating', e.target.value ? Number(e.target.value) : undefined)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
          >
            <option value="">Any Rating</option>
            <option value="4">4+ Stars</option>
            <option value="3">3+ Stars</option>
            <option value="2">2+ Stars</option>
            <option value="1">1+ Stars</option>
          </select>
        </div>
      </div>

      {/* Filter Actions */}
      <div className="mt-4 flex justify-end gap-2">
        <AccessibleButton
          onClick={() => {
            setFilters({});
            setQuery('');
          }}
          variant="secondary"
          size="sm"
        >
          Clear Filters
        </AccessibleButton>
        <AccessibleButton
          onClick={handleSearch}
          variant="primary"
          size="sm"
          disabled={isSearching}
        >
          Apply Filters
        </AccessibleButton>
      </div>
    </div>
  );

  return (
    <div className={`relative ${className}`}>
      {/* Search Bar */}
      <form onSubmit={handleSearch} className="relative">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <input
              ref={searchInputRef}
              type="text"
              value={query}
              onChange={handleQueryChange}
              onFocus={() => setShowSuggestions(true)}
              placeholder="Search for products, strains, effects..."
              className="w-full pl-10 pr-10 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              aria-label="Search products"
              aria-autocomplete="list"
              aria-controls="search-suggestions"
            />
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            {query && (
              <button
                type="button"
                onClick={handleClearSearch}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                aria-label="Clear search"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            )}
          </div>

          {showFilters && (
            <button
              type="button"
              onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
              className="px-4 py-3 bg-gray-100 hover:bg-gray-200 rounded-lg flex items-center gap-2"
              aria-label="Toggle advanced filters"
              aria-expanded={showAdvancedFilters}
            >
              <AdjustmentsHorizontalIcon className="h-5 w-5" />
              <span className="hidden sm:inline">Filters</span>
              {showAdvancedFilters ? (
                <ChevronUpIcon className="h-4 w-4" />
              ) : (
                <ChevronDownIcon className="h-4 w-4" />
              )}
            </button>
          )}

          <AccessibleButton
            type="submit"
            variant="primary"
            disabled={isSearching}
            aria-label="Search"
          >
            {isSearching ? (
              <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            ) : (
              'Search'
            )}
          </AccessibleButton>
        </div>
      </form>

      {/* Search Suggestions */}
      {showSuggestions && (suggestions.length > 0 || searchHistory.length > 0) && (
        <div
          id="search-suggestions"
          className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-lg shadow-lg"
        >
          {/* Search History */}
          {searchHistory.length > 0 && !query && (
            <div className="p-3 border-b">
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Recent Searches</p>
              {searchHistory.map((historyItem, index) => (
                <button
                  key={index}
                  onClick={() => {
                    setQuery(historyItem);
                    handleSearch();
                  }}
                  className="block w-full text-left px-2 py-1 hover:bg-gray-100 rounded"
                >
                  <MagnifyingGlassIcon className="inline h-4 w-4 text-gray-400 mr-2" />
                  {historyItem}
                </button>
              ))}
            </div>
          )}

          {/* Suggestions */}
          {suggestions.length > 0 && (
            <div className="p-3">
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Suggestions</p>
              {suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="block w-full text-left px-2 py-1 hover:bg-gray-100 rounded"
                >
                  <span className="font-medium">{suggestion.text}</span>
                  {suggestion.type !== 'product' && (
                    <span className="ml-2 text-xs text-gray-500 capitalize">
                      in {suggestion.type}
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}

          {/* Natural Language Search */}
          {query.length > 5 && (
            <div className="p-3 border-t">
              <button
                onClick={handleNaturalSearch}
                className="text-sm text-green-600 hover:text-green-700 font-medium"
              >
                Search with smart filters →
              </button>
            </div>
          )}
        </div>
      )}

      {/* Quick Filters */}
      {showFilters && renderQuickFilters()}

      {/* Advanced Filters */}
      {showFilters && renderAdvancedFilters()}
    </div>
  );
};

export default AdvancedSearch;