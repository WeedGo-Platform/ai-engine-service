/**
 * Secure Storage Adapter for Zustand Persist
 *
 * Wraps expo-secure-store to provide encrypted, hardware-backed token storage
 * Compatible with Zustand's persist middleware StateStorage interface
 */

import * as SecureStore from 'expo-secure-store';
import { StateStorage } from 'zustand/middleware';

/**
 * SecureStore adapter that implements Zustand's StateStorage interface
 *
 * This provides:
 * - iOS: Keychain with hardware encryption
 * - Android: EncryptedSharedPreferences backed by Android Keystore
 *
 * All methods are async but Zustand handles the promises internally
 */
export const secureStorage: StateStorage = {
  /**
   * Get item from secure storage
   * @param key - Storage key
   * @returns Promise resolving to stored value or null
   */
  getItem: async (key: string): Promise<string | null> => {
    try {
      const value = await SecureStore.getItemAsync(key);
      return value;
    } catch (error) {
      console.error(`SecureStorage getItem error for key "${key}":`, error);
      return null;
    }
  },

  /**
   * Set item in secure storage
   * @param key - Storage key
   * @param value - Value to store (must be string)
   */
  setItem: async (key: string, value: string): Promise<void> => {
    try {
      await SecureStore.setItemAsync(key, value);
    } catch (error) {
      console.error(`SecureStorage setItem error for key "${key}":`, error);
      throw error;
    }
  },

  /**
   * Remove item from secure storage
   * @param key - Storage key
   */
  removeItem: async (key: string): Promise<void> => {
    try {
      await SecureStore.deleteItemAsync(key);
    } catch (error) {
      console.error(`SecureStorage removeItem error for key "${key}":`, error);
      throw error;
    }
  },
};

/**
 * Migration utility to move data from AsyncStorage to SecureStore
 * Call this once during app initialization to migrate existing tokens
 */
export async function migrateFromAsyncStorage(
  AsyncStorage: any,
  keys: string[]
): Promise<void> {
  try {
    for (const key of keys) {
      // Get value from AsyncStorage
      const value = await AsyncStorage.getItem(key);

      if (value) {
        // Save to SecureStore
        await SecureStore.setItemAsync(key, value);

        // Remove from AsyncStorage
        await AsyncStorage.removeItem(key);

        console.log(`Migrated "${key}" from AsyncStorage to SecureStore`);
      }
    }
  } catch (error) {
    console.error('Migration from AsyncStorage failed:', error);
    // Don't throw - migration failure shouldn't break the app
  }
}
