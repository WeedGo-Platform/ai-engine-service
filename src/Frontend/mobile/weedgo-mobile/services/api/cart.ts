import { apiClient } from './client';
import * as SecureStore from 'expo-secure-store';
import {
  Cart,
  CartItem,
  AddToCartRequest,
  UpdateCartItemRequest,
  ApplyPromoRequest,
} from '@/types/api.types';

const CART_SESSION_KEY = 'cart_session_id';

class CartService {
  private sessionId: string | null = null;

  /**
   * Initialize cart service and load existing session if available
   */
  async initialize(): Promise<void> {
    const storedSessionId = await SecureStore.getItemAsync(CART_SESSION_KEY);
    if (storedSessionId) {
      this.sessionId = storedSessionId;
    }
  }

  /**
   * Create a new cart session
   */
  async createSession(): Promise<string> {
    // The /api/cart endpoint manages sessions automatically
    // Just use a default session ID or get from cart response
    try {
      const response = await apiClient.get<Cart>('/api/cart/');
      this.sessionId = response.data.id || response.data.session_id || 'default';
    } catch (error) {
      // If cart doesn't exist, use default session
      this.sessionId = 'default';
    }

    await SecureStore.setItemAsync(CART_SESSION_KEY, this.sessionId);
    return this.sessionId;
  }

  /**
   * Get current cart session ID, creating one if needed
   */
  private async getSessionId(): Promise<string> {
    if (!this.sessionId) {
      await this.initialize();
    }

    if (!this.sessionId) {
      await this.createSession();
    }

    return this.sessionId!;
  }

  /**
   * Get current cart
   */
  async getCart(): Promise<Cart> {
    const response = await apiClient.get<Cart>('/api/cart/');
    return response.data;
  }

  /**
   * Add item to cart
   */
  async addItem(data: AddToCartRequest & { store_id?: string }): Promise<CartItem> {
    // Import the store to get current store ID
    const { default: useStoreStore } = await import('@/stores/storeStore');
    const currentStore = useStoreStore.getState().currentStore;

    if (!currentStore?.id) {
      throw new Error('No store selected. Please select a store first.');
    }

    const requestData = {
      product_id: data.product_id,
      quantity: data.quantity || 1,
      store_id: currentStore.id,
      size: data.size || undefined // Ensure size is included if provided
    };

    console.log('Adding to cart with data:', requestData);

    try {
      const response = await apiClient.post<CartItem>(
        '/api/cart/items',
        requestData
      );
      return response.data;
    } catch (error: any) {
      console.error('Cart API error:', error.response?.data || error);
      throw error;
    }
  }

  /**
   * Update cart item quantity
   */
  async updateItem(itemId: string, quantity: number): Promise<CartItem> {
    const response = await apiClient.put<CartItem>(
      `/api/cart/items/${itemId}`,
      { quantity } as UpdateCartItemRequest
    );

    return response.data;
  }

  /**
   * Remove item from cart
   */
  async removeItem(itemId: string): Promise<void> {
    await apiClient.delete(`/api/cart/items/${itemId}`);
  }

  /**
   * Clear entire cart
   */
  async clearCart(): Promise<void> {
    await apiClient.delete('/api/cart/');

    // Clear stored session
    this.sessionId = null;
    await SecureStore.deleteItemAsync(CART_SESSION_KEY);
  }

  /**
   * Apply promo code
   */
  async applyPromoCode(promoCode: string): Promise<{ success: boolean; discount: number }> {
    const response = await apiClient.post<{ success: boolean; discount: number }>(
      '/api/cart/promo',
      { promo_code: promoCode } as ApplyPromoRequest
    );

    return response.data;
  }

  /**
   * Remove promo code
   */
  async removePromoCode(): Promise<void> {
    await apiClient.delete('/api/cart/promo');
  }

  /**
   * Validate cart before checkout
   */
  async validateCart(): Promise<{ valid: boolean; issues: string[] }> {
    const response = await apiClient.post<{ valid: boolean; issues: string[] }>(
      '/api/cart/validate'
    );

    return response.data;
  }

  /**
   * Get cart item count
   */
  async getItemCount(): Promise<number> {
    try {
      const cart = await this.getCart();
      return cart.items.reduce((total, item) => total + item.quantity, 0);
    } catch (error) {
      return 0;
    }
  }

  /**
   * Check if product is in cart
   */
  async isProductInCart(productId: string): Promise<boolean> {
    try {
      const cart = await this.getCart();
      return cart.items.some(item => item.product_id === productId);
    } catch (error) {
      return false;
    }
  }

  /**
   * Get cart total
   */
  async getTotal(): Promise<number> {
    try {
      const cart = await this.getCart();
      return cart.total;
    } catch (error) {
      return 0;
    }
  }

  /**
   * Merge guest cart with user cart after login
   */
  async mergeCart(): Promise<Cart> {
    const response = await apiClient.post<Cart>(
      '/api/cart/merge'
    );

    return response.data;
  }

  /**
   * Calculate delivery fee
   */
  async calculateDeliveryFee(addressId: string): Promise<{ fee: number; estimated_time: string }> {
    const response = await apiClient.post<{ fee: number; estimated_time: string }>(
      '/api/cart/delivery-fee',
      { address_id: addressId }
    );

    return response.data;
  }

  /**
   * Set delivery method
   */
  async setDeliveryMethod(method: 'delivery' | 'pickup'): Promise<Cart> {
    const response = await apiClient.post<Cart>(
      '/api/cart/delivery-method',
      { method }
    );

    return response.data;
  }
}

// Export singleton instance
export const cartService = new CartService();