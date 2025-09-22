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
    const response = await apiClient.post<{ session_id: string }>(
      '/api/v1/cart/create-session'
    );

    this.sessionId = response.data.session_id;
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
    const sessionId = await this.getSessionId();

    const response = await apiClient.get<Cart>(
      `/api/v1/cart/${sessionId}`
    );

    return response.data;
  }

  /**
   * Add item to cart
   */
  async addItem(data: AddToCartRequest): Promise<CartItem> {
    const sessionId = await this.getSessionId();

    const response = await apiClient.post<CartItem>(
      `/api/v1/cart/${sessionId}/items`,
      data
    );

    return response.data;
  }

  /**
   * Update cart item quantity
   */
  async updateItem(itemId: string, quantity: number): Promise<CartItem> {
    const sessionId = await this.getSessionId();

    const response = await apiClient.put<CartItem>(
      `/api/v1/cart/${sessionId}/items/${itemId}`,
      { quantity } as UpdateCartItemRequest
    );

    return response.data;
  }

  /**
   * Remove item from cart
   */
  async removeItem(itemId: string): Promise<void> {
    const sessionId = await this.getSessionId();

    await apiClient.delete(
      `/api/v1/cart/${sessionId}/items/${itemId}`
    );
  }

  /**
   * Clear entire cart
   */
  async clearCart(): Promise<void> {
    const sessionId = await this.getSessionId();

    await apiClient.delete(`/api/v1/cart/${sessionId}`);

    // Clear stored session
    this.sessionId = null;
    await SecureStore.deleteItemAsync(CART_SESSION_KEY);
  }

  /**
   * Apply promo code
   */
  async applyPromoCode(promoCode: string): Promise<{ success: boolean; discount: number }> {
    const sessionId = await this.getSessionId();

    const response = await apiClient.post<{ success: boolean; discount: number }>(
      `/api/v1/cart/${sessionId}/promo`,
      { promo_code: promoCode } as ApplyPromoRequest
    );

    return response.data;
  }

  /**
   * Remove promo code
   */
  async removePromoCode(): Promise<void> {
    const sessionId = await this.getSessionId();

    await apiClient.delete(`/api/v1/cart/${sessionId}/promo`);
  }

  /**
   * Validate cart before checkout
   */
  async validateCart(): Promise<{ valid: boolean; issues: string[] }> {
    const sessionId = await this.getSessionId();

    const response = await apiClient.post<{ valid: boolean; issues: string[] }>(
      `/api/v1/cart/${sessionId}/validate`
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
    const sessionId = await this.getSessionId();

    const response = await apiClient.post<Cart>(
      `/api/v1/cart/${sessionId}/merge`
    );

    return response.data;
  }

  /**
   * Calculate delivery fee
   */
  async calculateDeliveryFee(addressId: string): Promise<{ fee: number; estimated_time: string }> {
    const sessionId = await this.getSessionId();

    const response = await apiClient.post<{ fee: number; estimated_time: string }>(
      `/api/v1/cart/${sessionId}/delivery-fee`,
      { address_id: addressId }
    );

    return response.data;
  }

  /**
   * Set delivery method
   */
  async setDeliveryMethod(method: 'delivery' | 'pickup'): Promise<Cart> {
    const sessionId = await this.getSessionId();

    const response = await apiClient.post<Cart>(
      `/api/v1/cart/${sessionId}/delivery-method`,
      { method }
    );

    return response.data;
  }
}

// Export singleton instance
export const cartService = new CartService();