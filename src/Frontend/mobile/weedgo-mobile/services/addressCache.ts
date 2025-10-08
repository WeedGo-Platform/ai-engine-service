/**
 * Address Caching Service
 * Provides local caching for address lookups to reduce API calls
 * Uses AsyncStorage for persistence across app sessions
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

const CACHE_KEY = 'address_cache';
const MAX_CACHE_SIZE = 100; // Store up to 100 recent addresses
const CACHE_EXPIRY_HOURS = 72; // 3 days

export interface CachedAddress {
  id: string;
  query: string; // Search query that found this address
  address: {
    street: string;
    city: string;
    province: string;
    postal_code: string;
    country: string;
    full_address: string; // "123 Oak Street, Toronto, ON M5V 3A8, Canada"
  };
  coordinates?: {
    latitude: number;
    longitude: number;
  };
  timestamp: number;
  useCount: number; // Track how many times this address was selected
}

class AddressCacheService {
  private cache: Map<string, CachedAddress> = new Map();
  private initialized = false;

  /**
   * Initialize cache from AsyncStorage
   */
  async initialize(): Promise<void> {
    if (this.initialized) return;

    try {
      const cachedData = await AsyncStorage.getItem(CACHE_KEY);
      if (cachedData) {
        const parsed: CachedAddress[] = JSON.parse(cachedData);
        // Filter out expired entries
        const now = Date.now();
        const expiryMs = CACHE_EXPIRY_HOURS * 60 * 60 * 1000;

        parsed
          .filter(entry => (now - entry.timestamp) < expiryMs)
          .forEach(entry => {
            this.cache.set(this._generateKey(entry.query), entry);
          });

        console.log(`[AddressCache] Initialized with ${this.cache.size} cached addresses`);
      }
      this.initialized = true;
    } catch (error) {
      console.error('[AddressCache] Failed to initialize:', error);
      this.initialized = true; // Continue anyway
    }
  }

  /**
   * Generate cache key from search query
   */
  private _generateKey(query: string): string {
    return query.toLowerCase().trim().replace(/\s+/g, ' ');
  }

  /**
   * Search cached addresses by query
   * Returns addresses that match the search query
   */
  async searchCache(query: string): Promise<CachedAddress[]> {
    await this.initialize();

    const normalizedQuery = this._generateKey(query);
    const results: CachedAddress[] = [];

    // Exact match first
    const exactMatch = this.cache.get(normalizedQuery);
    if (exactMatch) {
      results.push(exactMatch);
    }

    // Partial matches (for autocomplete)
    if (query.length >= 3) {
      for (const [key, value] of this.cache) {
        if (key.includes(normalizedQuery) && key !== normalizedQuery) {
          results.push(value);
        }
      }
    }

    // Sort by use count (most used first)
    return results.sort((a, b) => b.useCount - a.useCount);
  }

  /**
   * Add address to cache
   */
  async cacheAddress(address: Omit<CachedAddress, 'timestamp' | 'useCount' | 'id'>): Promise<void> {
    await this.initialize();

    const key = this._generateKey(address.query);
    const existing = this.cache.get(key);

    const cachedAddress: CachedAddress = {
      id: existing?.id || `addr_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      ...address,
      timestamp: Date.now(),
      useCount: existing ? existing.useCount + 1 : 1,
    };

    this.cache.set(key, cachedAddress);

    // Limit cache size (remove least used entries)
    if (this.cache.size > MAX_CACHE_SIZE) {
      const entries = Array.from(this.cache.entries());
      entries.sort((a, b) => a[1].useCount - b[1].useCount); // Sort by use count ascending
      const toRemove = entries.slice(0, this.cache.size - MAX_CACHE_SIZE);
      toRemove.forEach(([key]) => this.cache.delete(key));
    }

    // Persist to AsyncStorage
    await this._persist();
  }

  /**
   * Increment use count for an address
   * Call this when user selects an address from cache
   */
  async incrementUseCount(query: string): Promise<void> {
    await this.initialize();

    const key = this._generateKey(query);
    const address = this.cache.get(key);

    if (address) {
      address.useCount++;
      address.timestamp = Date.now(); // Update timestamp
      this.cache.set(key, address);
      await this._persist();
    }
  }

  /**
   * Get all cached addresses sorted by use count
   */
  async getAllCached(): Promise<CachedAddress[]> {
    await this.initialize();

    const addresses = Array.from(this.cache.values());
    return addresses.sort((a, b) => b.useCount - a.useCount);
  }

  /**
   * Clear all cached addresses
   */
  async clearCache(): Promise<void> {
    this.cache.clear();
    await AsyncStorage.removeItem(CACHE_KEY);
    console.log('[AddressCache] Cache cleared');
  }

  /**
   * Get cache statistics
   */
  async getStats(): Promise<{
    size: number;
    mostUsed: string;
    oldestEntry: number;
  }> {
    await this.initialize();

    const addresses = Array.from(this.cache.values());
    const mostUsed = addresses.sort((a, b) => b.useCount - a.useCount)[0];
    const oldestEntry = addresses.length > 0
      ? Math.min(...addresses.map(a => a.timestamp))
      : 0;

    return {
      size: this.cache.size,
      mostUsed: mostUsed?.address.full_address || 'None',
      oldestEntry: oldestEntry ? Math.floor((Date.now() - oldestEntry) / (1000 * 60 * 60)) : 0, // hours
    };
  }

  /**
   * Persist cache to AsyncStorage
   */
  private async _persist(): Promise<void> {
    try {
      const data = Array.from(this.cache.values());
      await AsyncStorage.setItem(CACHE_KEY, JSON.stringify(data));
    } catch (error) {
      console.error('[AddressCache] Failed to persist:', error);
    }
  }
}

// Export singleton instance
export const addressCache = new AddressCacheService();
