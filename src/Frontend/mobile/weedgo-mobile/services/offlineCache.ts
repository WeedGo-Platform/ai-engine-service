/**
 * Offline Data Cache Service
 *
 * Provides persistent caching for user data to enable offline functionality
 * Uses SecureStore for sensitive data and AsyncStorage for general data
 */

import * as SecureStore from 'expo-secure-store';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface CachedUserProfile {
  id: string;
  phone: string;
  email?: string;
  firstName?: string;
  lastName?: string;
  profileImage?: string;
  cachedAt: number;
}

export interface CachedCart {
  items: any[];
  total: number;
  cachedAt: number;
}

export interface CachedStore {
  id: string;
  name: string;
  address: any;
  hours: any;
  cachedAt: number;
}

interface CacheMetadata {
  key: string;
  cachedAt: number;
  expiresAt: number;
  size: number;
}

class OfflineCache {
  // Cache keys
  private readonly USER_PROFILE_KEY = 'cache_user_profile';
  private readonly CART_KEY = 'cache_cart';
  private readonly STORE_KEY = 'cache_store';
  private readonly METADATA_KEY = 'cache_metadata';

  // Cache durations (in milliseconds)
  private readonly PROFILE_TTL = 7 * 24 * 60 * 60 * 1000; // 7 days
  private readonly CART_TTL = 24 * 60 * 60 * 1000; // 24 hours
  private readonly STORE_TTL = 24 * 60 * 60 * 1000; // 24 hours

  /**
   * Cache user profile data
   */
  async cacheUserProfile(profile: Omit<CachedUserProfile, 'cachedAt'>): Promise<void> {
    try {
      const cached: CachedUserProfile = {
        ...profile,
        cachedAt: Date.now(),
      };

      const data = JSON.stringify(cached);
      await AsyncStorage.setItem(this.USER_PROFILE_KEY, data);

      // Update metadata
      await this.updateMetadata(this.USER_PROFILE_KEY, data.length, this.PROFILE_TTL);

      console.log('✅ User profile cached for offline use');
    } catch (error) {
      console.error('Failed to cache user profile:', error);
      throw error;
    }
  }

  /**
   * Get cached user profile
   */
  async getCachedUserProfile(): Promise<CachedUserProfile | null> {
    try {
      const data = await AsyncStorage.getItem(this.USER_PROFILE_KEY);
      if (!data) {
        return null;
      }

      const cached: CachedUserProfile = JSON.parse(data);

      // Check if expired
      if (this.isExpired(cached.cachedAt, this.PROFILE_TTL)) {
        console.log('⚠️ Cached user profile expired');
        await this.clearUserProfile();
        return null;
      }

      console.log('✅ Retrieved cached user profile');
      return cached;
    } catch (error) {
      console.error('Failed to get cached user profile:', error);
      return null;
    }
  }

  /**
   * Clear cached user profile
   */
  async clearUserProfile(): Promise<void> {
    try {
      await AsyncStorage.removeItem(this.USER_PROFILE_KEY);
      await this.removeMetadata(this.USER_PROFILE_KEY);
      console.log('✅ User profile cache cleared');
    } catch (error) {
      console.error('Failed to clear user profile cache:', error);
    }
  }

  /**
   * Cache cart data
   */
  async cacheCart(items: any[], total: number): Promise<void> {
    try {
      const cached: CachedCart = {
        items,
        total,
        cachedAt: Date.now(),
      };

      const data = JSON.stringify(cached);
      await AsyncStorage.setItem(this.CART_KEY, data);

      await this.updateMetadata(this.CART_KEY, data.length, this.CART_TTL);

      console.log(`✅ Cart cached with ${items.length} items`);
    } catch (error) {
      console.error('Failed to cache cart:', error);
    }
  }

  /**
   * Get cached cart
   */
  async getCachedCart(): Promise<CachedCart | null> {
    try {
      const data = await AsyncStorage.getItem(this.CART_KEY);
      if (!data) {
        return null;
      }

      const cached: CachedCart = JSON.parse(data);

      if (this.isExpired(cached.cachedAt, this.CART_TTL)) {
        await this.clearCart();
        return null;
      }

      return cached;
    } catch (error) {
      console.error('Failed to get cached cart:', error);
      return null;
    }
  }

  /**
   * Clear cached cart
   */
  async clearCart(): Promise<void> {
    try {
      await AsyncStorage.removeItem(this.CART_KEY);
      await this.removeMetadata(this.CART_KEY);
    } catch (error) {
      console.error('Failed to clear cart cache:', error);
    }
  }

  /**
   * Cache store data
   */
  async cacheStore(store: Omit<CachedStore, 'cachedAt'>): Promise<void> {
    try {
      const cached: CachedStore = {
        ...store,
        cachedAt: Date.now(),
      };

      const data = JSON.stringify(cached);
      await AsyncStorage.setItem(this.STORE_KEY, data);

      await this.updateMetadata(this.STORE_KEY, data.length, this.STORE_TTL);

      console.log('✅ Store data cached');
    } catch (error) {
      console.error('Failed to cache store:', error);
    }
  }

  /**
   * Get cached store
   */
  async getCachedStore(): Promise<CachedStore | null> {
    try {
      const data = await AsyncStorage.getItem(this.STORE_KEY);
      if (!data) {
        return null;
      }

      const cached: CachedStore = JSON.parse(data);

      if (this.isExpired(cached.cachedAt, this.STORE_TTL)) {
        await this.clearStore();
        return null;
      }

      return cached;
    } catch (error) {
      console.error('Failed to get cached store:', error);
      return null;
    }
  }

  /**
   * Clear cached store
   */
  async clearStore(): Promise<void> {
    try {
      await AsyncStorage.removeItem(this.STORE_KEY);
      await this.removeMetadata(this.STORE_KEY);
    } catch (error) {
      console.error('Failed to clear store cache:', error);
    }
  }

  /**
   * Clear all cached data
   */
  async clearAll(): Promise<void> {
    try {
      await Promise.all([
        this.clearUserProfile(),
        this.clearCart(),
        this.clearStore(),
        AsyncStorage.removeItem(this.METADATA_KEY),
      ]);

      console.log('✅ All offline cache cleared');
    } catch (error) {
      console.error('Failed to clear all cache:', error);
    }
  }

  /**
   * Get cache statistics
   */
  async getStats(): Promise<{
    totalSize: number;
    itemCount: number;
    items: CacheMetadata[];
  }> {
    try {
      const metadataStr = await AsyncStorage.getItem(this.METADATA_KEY);
      if (!metadataStr) {
        return { totalSize: 0, itemCount: 0, items: [] };
      }

      const items: CacheMetadata[] = JSON.parse(metadataStr);
      const totalSize = items.reduce((sum, item) => sum + item.size, 0);

      return {
        totalSize,
        itemCount: items.length,
        items,
      };
    } catch (error) {
      console.error('Failed to get cache stats:', error);
      return { totalSize: 0, itemCount: 0, items: [] };
    }
  }

  /**
   * Check if cache entry is expired
   */
  private isExpired(cachedAt: number, ttl: number): boolean {
    return Date.now() - cachedAt > ttl;
  }

  /**
   * Update cache metadata
   */
  private async updateMetadata(key: string, size: number, ttl: number): Promise<void> {
    try {
      const metadataStr = await AsyncStorage.getItem(this.METADATA_KEY);
      const metadata: CacheMetadata[] = metadataStr ? JSON.parse(metadataStr) : [];

      // Remove existing entry for this key
      const filtered = metadata.filter((item) => item.key !== key);

      // Add new entry
      const newEntry: CacheMetadata = {
        key,
        cachedAt: Date.now(),
        expiresAt: Date.now() + ttl,
        size,
      };

      filtered.push(newEntry);

      await AsyncStorage.setItem(this.METADATA_KEY, JSON.stringify(filtered));
    } catch (error) {
      console.error('Failed to update cache metadata:', error);
    }
  }

  /**
   * Remove metadata entry
   */
  private async removeMetadata(key: string): Promise<void> {
    try {
      const metadataStr = await AsyncStorage.getItem(this.METADATA_KEY);
      if (!metadataStr) return;

      const metadata: CacheMetadata[] = JSON.parse(metadataStr);
      const filtered = metadata.filter((item) => item.key !== key);

      await AsyncStorage.setItem(this.METADATA_KEY, JSON.stringify(filtered));
    } catch (error) {
      console.error('Failed to remove cache metadata:', error);
    }
  }

  /**
   * Clean up expired cache entries
   */
  async cleanupExpired(): Promise<void> {
    try {
      const metadataStr = await AsyncStorage.getItem(this.METADATA_KEY);
      if (!metadataStr) return;

      const metadata: CacheMetadata[] = JSON.parse(metadataStr);
      const now = Date.now();

      const expiredKeys = metadata
        .filter((item) => item.expiresAt < now)
        .map((item) => item.key);

      if (expiredKeys.length > 0) {
        await Promise.all(expiredKeys.map((key) => AsyncStorage.removeItem(key)));

        const remaining = metadata.filter((item) => item.expiresAt >= now);
        await AsyncStorage.setItem(this.METADATA_KEY, JSON.stringify(remaining));

        console.log(`✅ Cleaned up ${expiredKeys.length} expired cache entries`);
      }
    } catch (error) {
      console.error('Failed to cleanup expired cache:', error);
    }
  }
}

// Export singleton instance
export const offlineCache = new OfflineCache();
