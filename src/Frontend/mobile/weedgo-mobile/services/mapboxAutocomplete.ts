/**
 * Mapbox Address Autocomplete Service
 * Provides address search with local caching and backend API integration
 * Implements debouncing and proximity-based search
 */

import { addressCache, CachedAddress } from './addressCache';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://10.0.0.29:5024';

export interface AddressSuggestion {
  id: string;
  place_name: string;
  address: {
    street: string;
    city: string;
    province: string;
    postal_code: string;
    country: string;
  };
  coordinates: {
    latitude: number;
    longitude: number;
  };
  relevance: number;
}

export interface AutocompleteOptions {
  proximity?: {
    latitude: number;
    longitude: number;
  };
  limit?: number;
  useCache?: boolean;
}

class MapboxAutocompleteService {
  private debounceTimers: Map<string, NodeJS.Timeout> = new Map();
  private readonly DEBOUNCE_DELAY = 300; // 300ms debounce for search-as-you-type

  /**
   * Search addresses with autocomplete
   * Checks cache first, then calls backend API
   */
  async searchAddresses(
    query: string,
    options: AutocompleteOptions = {}
  ): Promise<AddressSuggestion[]> {
    // Validate query
    if (!query || query.trim().length < 3) {
      return [];
    }

    const normalizedQuery = query.trim();

    try {
      // 1. Check local cache first (if enabled)
      if (options.useCache !== false) {
        const cachedResults = await addressCache.searchCache(normalizedQuery);
        if (cachedResults.length > 0) {
          console.log(`[MapboxAutocomplete] Found ${cachedResults.length} cached results`);
          return this._convertCachedToSuggestions(cachedResults);
        }
      }

      // 2. Call backend API for fresh results
      const suggestions = await this._callBackendAPI(normalizedQuery, options);

      // 3. Cache successful results for future use
      if (suggestions.length > 0 && options.useCache !== false) {
        await this._cacheResults(normalizedQuery, suggestions);
      }

      return suggestions;
    } catch (error) {
      console.error('[MapboxAutocomplete] Search failed:', error);
      return [];
    }
  }

  /**
   * Search addresses with debouncing (for real-time search-as-you-type)
   * Cancels pending requests if user keeps typing
   */
  async searchAddressesDebounced(
    query: string,
    options: AutocompleteOptions = {},
    debounceKey: string = 'default'
  ): Promise<AddressSuggestion[]> {
    return new Promise((resolve) => {
      // Clear existing timer for this key
      const existingTimer = this.debounceTimers.get(debounceKey);
      if (existingTimer) {
        clearTimeout(existingTimer);
      }

      // Set new timer
      const timer = setTimeout(async () => {
        const results = await this.searchAddresses(query, options);
        resolve(results);
        this.debounceTimers.delete(debounceKey);
      }, this.DEBOUNCE_DELAY);

      this.debounceTimers.set(debounceKey, timer);
    });
  }

  /**
   * Get user's current location for proximity-based search
   * Returns null if location permission not granted or unavailable
   */
  async getCurrentLocation(): Promise<{ latitude: number; longitude: number } | null> {
    try {
      // Dynamic import to avoid issues if expo-location not installed
      const Location = await import('expo-location');

      // Check permissions
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        console.log('[MapboxAutocomplete] Location permission not granted');
        return null;
      }

      // Get current position
      const location = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
      });

      return {
        latitude: location.coords.latitude,
        longitude: location.coords.longitude,
      };
    } catch (error) {
      console.error('[MapboxAutocomplete] Failed to get location:', error);
      return null;
    }
  }

  /**
   * Search with automatic proximity bias (uses device location)
   */
  async searchNearby(query: string, options: AutocompleteOptions = {}): Promise<AddressSuggestion[]> {
    // Try to get current location for proximity bias
    if (!options.proximity) {
      const location = await this.getCurrentLocation();
      if (location) {
        options.proximity = location;
      }
    }

    return this.searchAddresses(query, options);
  }

  /**
   * Convert cached address to suggestion format
   */
  private _convertCachedToSuggestions(cached: CachedAddress[]): AddressSuggestion[] {
    return cached.map((item) => ({
      id: item.id,
      place_name: item.address.full_address,
      address: {
        street: item.address.street,
        city: item.address.city,
        province: item.address.province,
        postal_code: item.address.postal_code,
        country: item.address.country,
      },
      coordinates: item.coordinates || { latitude: 0, longitude: 0 },
      relevance: 1.0, // Cached results have full relevance
    }));
  }

  /**
   * Call backend autocomplete API
   */
  private async _callBackendAPI(
    query: string,
    options: AutocompleteOptions
  ): Promise<AddressSuggestion[]> {
    try {
      // Build query params
      const params = new URLSearchParams({
        query,
        limit: (options.limit || 5).toString(),
      });

      // Add proximity if provided
      if (options.proximity) {
        params.append('latitude', options.proximity.latitude.toString());
        params.append('longitude', options.proximity.longitude.toString());
      }

      // Make API request
      const response = await fetch(`${API_URL}/api/geocoding/autocomplete?${params.toString()}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        console.error(`[MapboxAutocomplete] API error: ${response.status}`);
        return [];
      }

      const suggestions: AddressSuggestion[] = await response.json();
      console.log(`[MapboxAutocomplete] API returned ${suggestions.length} suggestions`);

      return suggestions;
    } catch (error) {
      console.error('[MapboxAutocomplete] API call failed:', error);
      return [];
    }
  }

  /**
   * Cache API results for future use
   */
  private async _cacheResults(query: string, suggestions: AddressSuggestion[]): Promise<void> {
    try {
      // Cache each suggestion
      for (const suggestion of suggestions) {
        await addressCache.cacheAddress({
          query,
          address: {
            street: suggestion.address.street,
            city: suggestion.address.city,
            province: suggestion.address.province,
            postal_code: suggestion.address.postal_code,
            country: suggestion.address.country,
            full_address: suggestion.place_name,
          },
          coordinates: suggestion.coordinates,
        });
      }

      console.log(`[MapboxAutocomplete] Cached ${suggestions.length} results`);
    } catch (error) {
      console.error('[MapboxAutocomplete] Failed to cache results:', error);
    }
  }

  /**
   * Mark an address as selected (increments use count for prioritization)
   */
  async selectAddress(suggestion: AddressSuggestion): Promise<void> {
    try {
      // Increment use count in cache
      await addressCache.incrementUseCount(suggestion.place_name);

      console.log(`[MapboxAutocomplete] Marked address as selected: ${suggestion.place_name}`);
    } catch (error) {
      console.error('[MapboxAutocomplete] Failed to mark address as selected:', error);
    }
  }

  /**
   * Get recently used addresses (from cache)
   */
  async getRecentAddresses(limit: number = 5): Promise<AddressSuggestion[]> {
    try {
      const cached = await addressCache.getAllCached();
      const recent = cached.slice(0, limit);
      return this._convertCachedToSuggestions(recent);
    } catch (error) {
      console.error('[MapboxAutocomplete] Failed to get recent addresses:', error);
      return [];
    }
  }

  /**
   * Clear all cached addresses
   */
  async clearCache(): Promise<void> {
    try {
      await addressCache.clearCache();
      console.log('[MapboxAutocomplete] Cache cleared');
    } catch (error) {
      console.error('[MapboxAutocomplete] Failed to clear cache:', error);
    }
  }

  /**
   * Get cache statistics
   */
  async getCacheStats() {
    return addressCache.getStats();
  }

  /**
   * Cancel all pending debounced searches
   */
  cancelPendingSearches(): void {
    this.debounceTimers.forEach((timer) => clearTimeout(timer));
    this.debounceTimers.clear();
  }
}

// Export singleton instance
export const mapboxAutocomplete = new MapboxAutocompleteService();
