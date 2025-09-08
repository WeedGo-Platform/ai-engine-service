import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { cartService, Cart, CartItem, AddToCartRequest } from '../services/cart';
import { Product } from '../services/productSearch';

interface CartContextType {
  cart: Cart | null;
  isLoading: boolean;
  error: string | null;
  itemCount: number;
  addToCart: (product: Product, quantity: number) => Promise<void>;
  updateQuantity: (itemId: string, quantity: number) => Promise<void>;
  removeFromCart: (itemId: string) => Promise<void>;
  clearCart: () => Promise<void>;
  refreshCart: () => Promise<void>;
  showNotification: (message: string, type: 'success' | 'error') => void;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};

interface CartProviderProps {
  children: React.ReactNode;
}

export const CartProvider: React.FC<CartProviderProps> = ({ children }) => {
  const [cart, setCart] = useState<Cart | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notification, setNotification] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // Load cart on mount
  const loadCart = useCallback(async () => {
    setIsLoading(true);
    try {
      const cartData = await cartService.getCart();
      setCart(cartData);
      setError(null);
    } catch (err) {
      console.error('Failed to load cart:', err);
      setError('Failed to load cart');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCart();
  }, [loadCart]);

  // Add to cart
  const addToCart = async (product: Product, quantity: number) => {
    setIsLoading(true);
    try {
      const request: AddToCartRequest = {
        product_id: product.id,
        quantity,
        price: product.price,
        product_name: product.name,
        product_image: product.thumbnail_url || product.image_url
      };
      
      const updatedCart = await cartService.addToCart(request);
      setCart(updatedCart);
      showNotification(`Added ${quantity} × ${product.name} to cart`, 'success');
      setError(null);
    } catch (err) {
      console.error('Failed to add to cart:', err);
      setError('Failed to add item to cart');
      showNotification('Failed to add item to cart', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // Update quantity
  const updateQuantity = async (itemId: string, quantity: number) => {
    if (quantity < 1) return;
    
    setIsLoading(true);
    try {
      const updatedCart = await cartService.updateCartItem(itemId, quantity);
      setCart(updatedCart);
      setError(null);
    } catch (err) {
      console.error('Failed to update quantity:', err);
      setError('Failed to update quantity');
      showNotification('Failed to update quantity', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // Remove from cart
  const removeFromCart = async (itemId: string) => {
    setIsLoading(true);
    try {
      const updatedCart = await cartService.removeFromCart(itemId);
      setCart(updatedCart);
      showNotification('Item removed from cart', 'success');
      setError(null);
    } catch (err) {
      console.error('Failed to remove from cart:', err);
      setError('Failed to remove item');
      showNotification('Failed to remove item', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // Clear cart
  const clearCart = async () => {
    setIsLoading(true);
    try {
      await cartService.clearCart();
      setCart({ id: '', items: [], total: 0, item_count: 0 });
      showNotification('Cart cleared', 'success');
      setError(null);
    } catch (err) {
      console.error('Failed to clear cart:', err);
      setError('Failed to clear cart');
      showNotification('Failed to clear cart', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // Show notification
  const showNotification = (message: string, type: 'success' | 'error') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  const value: CartContextType = {
    cart,
    isLoading,
    error,
    itemCount: cart?.item_count || 0,
    addToCart,
    updateQuantity,
    removeFromCart,
    clearCart,
    refreshCart: loadCart,
    showNotification
  };

  return (
    <CartContext.Provider value={value}>
      {children}
      
      {/* Notification Toast */}
      {notification && (
        <div
          className={`fixed top-20 right-4 z-[999999] px-4 py-3 rounded-lg shadow-lg transition-all duration-300 ${
            notification.type === 'success' 
              ? 'bg-green-500 text-white' 
              : 'bg-red-500 text-white'
          }`}
        >
          <div className="flex items-center gap-2">
            {notification.type === 'success' ? (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            )}
            <span>{notification.message}</span>
          </div>
        </div>
      )}
    </CartContext.Provider>
  );
};