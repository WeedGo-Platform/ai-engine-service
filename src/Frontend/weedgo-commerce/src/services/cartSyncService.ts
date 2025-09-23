/**
 * Cart synchronization service for server persistence
 */

import apiClient from '@api/client';
import { ICartItem } from '@templates/types';
import { logger } from '@utils/logger';

class CartSyncService {
  private static instance: CartSyncService;
  private syncInterval: NodeJS.Timeout | null = null;
  private pendingSync: boolean = false;
  private lastSyncTime: number = 0;
  private readonly SYNC_INTERVAL = 30000; // 30 seconds
  private readonly SYNC_DEBOUNCE = 2000; // 2 seconds

  private constructor() {
    this.initializeSync();
  }

  public static getInstance(): CartSyncService {
    if (!CartSyncService.instance) {
      CartSyncService.instance = new CartSyncService();
    }
    return CartSyncService.instance;
  }

  /**
   * Initialize cart synchronization
   */
  private initializeSync(): void {
    // Sync cart when user logs in
    window.addEventListener('auth:login', this.syncCartToServer.bind(this));

    // Sync cart before user logs out
    window.addEventListener('auth:logout', this.syncCartToServer.bind(this));

    // Sync cart when tab becomes visible
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) {
        this.syncCartWithServer();
      }
    });

    // Periodic sync while user is active
    this.startPeriodicSync();

    // Sync before page unload
    window.addEventListener('beforeunload', this.syncCartToServer.bind(this));
  }

  /**
   * Start periodic cart sync
   */
  private startPeriodicSync(): void {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
    }

    this.syncInterval = setInterval(() => {
      const token = localStorage.getItem('access_token');
      if (token) {
        this.syncCartWithServer();
      }
    }, this.SYNC_INTERVAL);
  }

  /**
   * Stop periodic sync
   */
  public stopPeriodicSync(): void {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
    }
  }

  /**
   * Sync local cart to server
   */
  public async syncCartToServer(): Promise<void> {
    const token = localStorage.getItem('access_token');
    if (!token) {
      logger.debug('No auth token, skipping cart sync to server');
      return;
    }

    const localCart = this.getLocalCart();
    if (!localCart || localCart.length === 0) {
      logger.debug('No items in local cart to sync');
      return;
    }

    try {
      // Debounce rapid sync calls
      const now = Date.now();
      if (now - this.lastSyncTime < this.SYNC_DEBOUNCE) {
        this.pendingSync = true;
        setTimeout(() => {
          if (this.pendingSync) {
            this.pendingSync = false;
            this.syncCartToServer();
          }
        }, this.SYNC_DEBOUNCE);
        return;
      }

      this.lastSyncTime = now;

      // Prepare cart data for API
      const cartData = {
        items: localCart.map(item => ({
          product_id: item.product.id,
          quantity: item.quantity,
          price: item.price,
          metadata: {
            size: item.product.size,
            strain: item.product.strain,
            thc: item.product.thc,
            cbd: item.product.cbd,
          }
        })),
        timestamp: new Date().toISOString(),
      };

      // Send to server
      const response = await apiClient.post('/api/cart/sync', cartData);

      logger.debug('Cart synced to server', { itemCount: localCart.length });

      // Update sync timestamp
      localStorage.setItem('cart_last_sync', new Date().toISOString());

      return response.data;
    } catch (error) {
      logger.error('Failed to sync cart to server', error);
      // Don't throw - we want to continue working offline
    }
  }

  /**
   * Sync cart from server to local
   */
  public async syncCartFromServer(): Promise<ICartItem[]> {
    const token = localStorage.getItem('access_token');
    if (!token) {
      logger.debug('No auth token, skipping cart sync from server');
      return this.getLocalCart();
    }

    try {
      const response = await apiClient.get('/api/cart');
      const serverCart = response.data.items;

      if (!serverCart || serverCart.length === 0) {
        logger.debug('No items in server cart');
        return this.getLocalCart();
      }

      // Convert server cart to local format
      const localCart: ICartItem[] = serverCart.map((item: any) => ({
        id: item.id || `${item.product_id}-${Date.now()}`,
        product: {
          id: item.product_id,
          name: item.product_name,
          price: item.price,
          sku: item.product_sku,
          images: item.product_images || [],
          category: item.product_category,
          brand: item.product_brand,
          size: item.metadata?.size,
          strain: item.metadata?.strain,
          thc: item.metadata?.thc,
          cbd: item.metadata?.cbd,
        },
        quantity: item.quantity,
        price: item.price,
      }));

      // Save to localStorage
      this.saveLocalCart(localCart);
      localStorage.setItem('cart_last_sync', new Date().toISOString());

      logger.debug('Cart synced from server', { itemCount: localCart.length });

      return localCart;
    } catch (error) {
      logger.error('Failed to sync cart from server', error);
      // Return local cart as fallback
      return this.getLocalCart();
    }
  }

  /**
   * Merge local and server carts
   */
  public async syncCartWithServer(): Promise<ICartItem[]> {
    const token = localStorage.getItem('access_token');
    if (!token) {
      return this.getLocalCart();
    }

    try {
      const localCart = this.getLocalCart();
      const lastSync = localStorage.getItem('cart_last_sync');
      const lastSyncTime = lastSync ? new Date(lastSync).getTime() : 0;
      const now = Date.now();

      // If last sync was recent, just return local cart
      if (now - lastSyncTime < 5000) {
        return localCart;
      }

      // Get server cart
      const serverCart = await this.syncCartFromServer();

      // If local cart is empty, use server cart
      if (!localCart || localCart.length === 0) {
        return serverCart;
      }

      // If server cart is empty, sync local to server
      if (!serverCart || serverCart.length === 0) {
        await this.syncCartToServer();
        return localCart;
      }

      // Merge carts (prefer local for conflicts)
      const mergedCart = this.mergeCarts(localCart, serverCart);

      // Save merged cart
      this.saveLocalCart(mergedCart);
      await this.syncCartToServer();

      return mergedCart;
    } catch (error) {
      logger.error('Failed to sync cart with server', error);
      return this.getLocalCart();
    }
  }

  /**
   * Merge two carts, preferring local for conflicts
   */
  private mergeCarts(localCart: ICartItem[], serverCart: ICartItem[]): ICartItem[] {
    const merged = new Map<string, ICartItem>();

    // Add server items first
    serverCart.forEach(item => {
      merged.set(item.product.id, item);
    });

    // Override with local items (local takes precedence)
    localCart.forEach(item => {
      const existing = merged.get(item.product.id);
      if (existing) {
        // Merge quantities
        item.quantity = Math.max(item.quantity, existing.quantity);
      }
      merged.set(item.product.id, item);
    });

    return Array.from(merged.values());
  }

  /**
   * Get cart from localStorage
   */
  private getLocalCart(): ICartItem[] {
    const cartStr = localStorage.getItem('cart');
    if (cartStr) {
      try {
        return JSON.parse(cartStr);
      } catch {
        return [];
      }
    }
    return [];
  }

  /**
   * Save cart to localStorage
   */
  private saveLocalCart(cart: ICartItem[]): void {
    localStorage.setItem('cart', JSON.stringify(cart));
  }

  /**
   * Clear cart from both local and server
   */
  public async clearCart(): Promise<void> {
    localStorage.removeItem('cart');
    localStorage.removeItem('cart_last_sync');

    const token = localStorage.getItem('access_token');
    if (token) {
      try {
        await apiClient.delete('/api/cart');
        logger.debug('Cart cleared from server');
      } catch (error) {
        logger.error('Failed to clear cart from server', error);
      }
    }
  }

  /**
   * Get cart summary for quick access
   */
  public getCartSummary(): { itemCount: number; total: number } {
    const cart = this.getLocalCart();
    const itemCount = cart.reduce((sum, item) => sum + item.quantity, 0);
    const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);

    return { itemCount, total };
  }

  /**
   * Check if cart needs sync
   */
  public needsSync(): boolean {
    const lastSync = localStorage.getItem('cart_last_sync');
    if (!lastSync) return true;

    const lastSyncTime = new Date(lastSync).getTime();
    const now = Date.now();

    return (now - lastSyncTime) > this.SYNC_INTERVAL;
  }
}

// Export singleton instance
export const cartSyncService = CartSyncService.getInstance();

// Export convenience functions
export const syncCart = () => cartSyncService.syncCartWithServer();
export const syncCartToServer = () => cartSyncService.syncCartToServer();
export const syncCartFromServer = () => cartSyncService.syncCartFromServer();
export const clearSyncedCart = () => cartSyncService.clearCart();
export const getCartSummary = () => cartSyncService.getCartSummary();