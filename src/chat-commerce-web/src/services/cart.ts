import api from './api';

export interface CartItem {
  id: string;
  product_id: string;
  product_name: string;
  product_image?: string;
  price: number;
  quantity: number;
  subtotal: number;
}

export interface Cart {
  id: string;
  user_id?: string;
  session_id?: string;
  items: CartItem[];
  total: number;
  item_count: number;
  created_at?: string;
  updated_at?: string;
}

export interface AddToCartRequest {
  product_id: string;
  quantity: number;
  price: number;
  product_name?: string;
  product_image?: string;
}

export interface UpdateCartItemRequest {
  quantity: number;
}

class CartService {
  private cartKey = 'cart_session_id';

  /**
   * Get or create a session ID for anonymous users
   */
  private getSessionId(): string {
    let sessionId = localStorage.getItem(this.cartKey);
    if (!sessionId) {
      sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem(this.cartKey, sessionId);
    }
    return sessionId;
  }

  /**
   * Get current cart
   */
  async getCart(): Promise<Cart> {
    try {
      const sessionId = this.getSessionId();
      const response = await api.get('/api/cart', {
        headers: {
          'X-Session-Id': sessionId
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching cart:', error);
      // Return empty cart on error
      return {
        id: '',
        items: [],
        total: 0,
        item_count: 0
      };
    }
  }

  /**
   * Add item to cart
   */
  async addToCart(item: AddToCartRequest): Promise<Cart> {
    try {
      const sessionId = this.getSessionId();
      const response = await api.post('/api/cart/add', item, {
        headers: {
          'X-Session-Id': sessionId
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error adding to cart:', error);
      throw error;
    }
  }

  /**
   * Update cart item quantity
   */
  async updateCartItem(itemId: string, quantity: number): Promise<Cart> {
    try {
      const sessionId = this.getSessionId();
      const response = await api.put(`/api/cart/item/${itemId}`, 
        { quantity },
        {
          headers: {
            'X-Session-Id': sessionId
          }
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error updating cart item:', error);
      throw error;
    }
  }

  /**
   * Remove item from cart
   */
  async removeFromCart(itemId: string): Promise<Cart> {
    try {
      const sessionId = this.getSessionId();
      const response = await api.delete(`/api/cart/item/${itemId}`, {
        headers: {
          'X-Session-Id': sessionId
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error removing from cart:', error);
      throw error;
    }
  }

  /**
   * Clear entire cart
   */
  async clearCart(): Promise<void> {
    try {
      const sessionId = this.getSessionId();
      await api.delete('/api/cart', {
        headers: {
          'X-Session-Id': sessionId
        }
      });
    } catch (error) {
      console.error('Error clearing cart:', error);
      throw error;
    }
  }

  /**
   * Get cart item count
   */
  async getCartCount(): Promise<number> {
    try {
      const cart = await this.getCart();
      return cart.item_count || 0;
    } catch (error) {
      console.error('Error getting cart count:', error);
      return 0;
    }
  }
}

// Export singleton instance
export const cartService = new CartService();