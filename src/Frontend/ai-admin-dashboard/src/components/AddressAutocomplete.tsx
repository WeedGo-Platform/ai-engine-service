/**
 * AddressAutocomplete Component
 *
 * Real-time address autocomplete using Mapbox Geocoding API
 * Features:
 * - Debounced search (300ms delay)
 * - Keyboard navigation (↑↓ Enter Escape)
 * - Loading states and error handling
 * - Canadian addresses only
 * - Returns structured address components + coordinates
 *
 * API: GET /api/geocoding/autocomplete
 * Backend: /Backend/api/geocoding_endpoints.py
 */

import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { MapPin, Loader2, AlertCircle, X } from 'lucide-react';
import { getApiEndpoint } from '../config/app.config';

// Address components returned from Mapbox
export interface AddressComponents {
  street: string;
  city: string;
  province: string;
  postal_code: string;
  country: string;
  full_address?: string;
}

// Suggestion from autocomplete API
interface Suggestion {
  id: string;
  place_name: string;
  address: AddressComponents;
  coordinates: {
    latitude: number;
    longitude: number;
  };
  relevance: number;
}

export interface AddressAutocompleteProps {
  value: string;
  onChange: (address: AddressComponents) => void;
  onCoordinatesChange?: (coords: { latitude: number; longitude: number }) => void;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
  required?: boolean;
}

export const AddressAutocomplete: React.FC<AddressAutocompleteProps> = ({
  value,
  onChange,
  onCoordinatesChange,
  placeholder = 'Start typing an address...',
  className = '',
  disabled = false,
  required = false,
}) => {
  const [query, setQuery] = useState(value);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [hasSelected, setHasSelected] = useState(false);
  const [userIsTyping, setUserIsTyping] = useState(false);

  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Initialize hasSelected if value is already populated (navigating back to page)
  useEffect(() => {
    if (value && value.length > 0) {
      setHasSelected(true);
      setUserIsTyping(false);
    }
  }, []); // Only on mount

  // Sync external value changes
  useEffect(() => {
    if (value !== query) {
      setQuery(value);
      // If external value is being set (not empty), mark as selected
      if (value && value.length > 0) {
        setHasSelected(true);
        setUserIsTyping(false);
      }
    }
  }, [value]);

  // Debounced search
  useEffect(() => {
    // Don't search if user just selected an address
    if (hasSelected && !userIsTyping) {
      return;
    }

    // Don't search if query is too short
    if (query.length < 3) {
      setSuggestions([]);
      setShowDropdown(false);
      setError(null);
      return;
    }

    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      setError(null);

      // Create new AbortController
      abortControllerRef.current = new AbortController();

      try {
        const response = await axios.get<Suggestion[]>(
          getApiEndpoint('/api/geocoding/autocomplete'),
          {
            params: {
              query,
              limit: 5,
            },
            signal: abortControllerRef.current.signal,
          }
        );

        console.log('Autocomplete response:', {
          query,
          status: response.status,
          dataLength: response.data?.length,
          data: response.data
        });

        setSuggestions(response.data);
        setShowDropdown(true);
        setSelectedIndex(-1);
      } catch (err: any) {
        if (err.name !== 'CanceledError') {
          setError('Failed to fetch address suggestions');
          console.error('Autocomplete error:', {
            query,
            error: err,
            message: err.message,
            response: err.response?.data,
            status: err.response?.status
          });
        }
      } finally {
        setLoading(false);
      }
    }, 300); // 300ms debounce

    return () => {
      clearTimeout(timer);
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [query, hasSelected, userIsTyping]);

  // Handle suggestion selection
  const handleSelect = (suggestion: Suggestion) => {
    // Update address components
    onChange(suggestion.address);

    // Update coordinates
    if (onCoordinatesChange) {
      onCoordinatesChange(suggestion.coordinates);
    }

    // Update query with full address
    setQuery(suggestion.address.full_address || suggestion.place_name);
    setShowDropdown(false);
    setSuggestions([]);
    setHasSelected(true);
    setUserIsTyping(false); // Mark as not typing

    // Blur input to close dropdown
    if (inputRef.current) {
      inputRef.current.blur();
    }
  };

  // Clear input
  const handleClear = () => {
    setQuery('');
    setSuggestions([]);
    setShowDropdown(false);
    setHasSelected(false);
    onChange({
      street: '',
      city: '',
      province: '',
      postal_code: '',
      country: 'Canada',
    });
    if (onCoordinatesChange) {
      onCoordinatesChange({ latitude: 0, longitude: 0 });
    }
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showDropdown || suggestions.length === 0) {
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;

      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : 0));
        break;

      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
          handleSelect(suggestions[selectedIndex]);
        }
        break;

      case 'Escape':
        e.preventDefault();
        setShowDropdown(false);
        setSelectedIndex(-1);
        break;

      default:
        break;
    }
  };

  // Click outside to close dropdown with null checks
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      try {
        const dropdownElement = dropdownRef.current;
        const inputElement = inputRef.current;
        
        if (
          dropdownElement &&
          !dropdownElement.contains(event.target as Node) &&
          inputElement &&
          !inputElement.contains(event.target as Node)
        ) {
          setShowDropdown(false);
        }
      } catch (error) {
        // Handle edge case where elements were unmounted
        console.debug('Click outside handler error (safe to ignore):', error);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Scroll selected item into view with null checks
  useEffect(() => {
    if (selectedIndex >= 0 && dropdownRef.current && dropdownRef.current.children) {
      try {
        const selectedElement = dropdownRef.current.children[selectedIndex] as HTMLElement;
        if (selectedElement && typeof selectedElement.scrollIntoView === 'function') {
          selectedElement.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }
      } catch (error) {
        // Silently handle if element was unmounted during scroll
        console.debug('Scroll error (safe to ignore):', error);
      }
    }
  }, [selectedIndex]);

  return (
    <div className={`relative ${className}`}>
      {/* Input field with icons */}
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setUserIsTyping(true);  // User is actively typing
            setHasSelected(false);  // Reset selection state
          }}
          onFocus={() => {
            if (suggestions.length > 0 && !hasSelected) {
              setShowDropdown(true);
            }
          }}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          required={required}
          className="w-full px-3 py-2 pl-10 pr-10 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:cursor-not-allowed transition-colors"
          autoComplete="off"
        />

        {/* Map pin icon (left) */}
        <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />

        {/* Loading spinner or clear button (right) */}
        {loading ? (
          <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-blue-500 animate-spin" />
        ) : query.length > 0 ? (
          <button
            type="button"
            onClick={handleClear}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            aria-label="Clear address"
          >
            <X className="w-4 h-4" />
          </button>
        ) : null}
      </div>

      {/* Error message */}
      {error && (
        <div className="mt-1 flex items-center gap-1 text-xs text-red-600 dark:text-red-400">
          <AlertCircle className="w-3 h-3 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Helper text */}
      {query.length > 0 && query.length < 3 && !loading && (
        <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
          Type at least 3 characters to search
        </div>
      )}

      {/* Dropdown with suggestions */}
      {showDropdown && suggestions.length > 0 && (
        <div
          ref={dropdownRef}
          className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg max-h-60 overflow-y-auto"
          role="listbox"
        >
          {suggestions.map((suggestion, index) => (
            <button
              key={suggestion.id}
              type="button"
              onClick={() => handleSelect(suggestion)}
              onMouseEnter={() => setSelectedIndex(index)}
              className={`w-full px-3 py-2 text-left hover:bg-blue-50 dark:hover:bg-blue-900/20 flex items-start gap-2 transition-colors ${
                index === selectedIndex
                  ? 'bg-blue-50 dark:bg-blue-900/20'
                  : ''
              } ${index !== suggestions.length - 1 ? 'border-b border-gray-100 dark:border-gray-700' : ''}`}
              role="option"
              aria-selected={index === selectedIndex}
            >
              <MapPin className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {suggestion.address.street}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {suggestion.address.city}, {suggestion.address.province} {suggestion.address.postal_code}
                </div>
                {suggestion.relevance < 0.8 && (
                  <div className="text-xs text-yellow-600 dark:text-yellow-400 mt-0.5">
                    Low confidence match
                  </div>
                )}
              </div>
            </button>
          ))}
        </div>
      )}

      {/* No results message */}
      {showDropdown && !loading && suggestions.length === 0 && query.length >= 3 && (
        <div className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg p-3">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-gray-400 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm text-gray-600 dark:text-gray-300 font-medium">
                No addresses found
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                Type your address manually - city and postal code will need to be filled separately
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AddressAutocomplete;
