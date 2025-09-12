import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiShoppingCart, FiX, FiPlus, FiMinus, FiTrash2, FiArrowRight } from 'react-icons/fi';
import { cartService, Cart as CartType } from '../../services/cart';
import { useTemplateContext } from '../../contexts/TemplateContext';
import Checkout from '../checkout/Checkout';

interface CartProps {
  isOpen: boolean;
  onClose: () => void;
}

const Cart: React.FC<CartProps> = ({ isOpen, onClose }) => {
  const { currentTemplate } = useTemplateContext();
  const [cart, setCart] = useState<CartType | null>(null);
  const [loading, setLoading] = useState(false);
  const [updatingItems, setUpdatingItems] = useState<Set<string>>(new Set());
  const [showCheckout, setShowCheckout] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadCart();
    }
  }, [isOpen]);

  const loadCart = async () => {
    setLoading(true);
    try {
      const cartData = await cartService.getCart();
      setCart(cartData);
    } catch (error) {
      console.error('Failed to load cart:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateQuantity = async (itemId: string, newQuantity: number) => {
    if (!cart || newQuantity < 1) return;
    
    setUpdatingItems(prev => new Set(prev).add(itemId));
    
    try {
      const updatedCart = await cartService.updateCartItem(itemId, newQuantity);
      setCart(updatedCart);
    } catch (error) {
      console.error('Failed to update quantity:', error);
    } finally {
      setUpdatingItems(prev => {
        const newSet = new Set(prev);
        newSet.delete(itemId);
        return newSet;
      });
    }
  };

  const handleRemoveItem = async (itemId: string) => {
    if (!cart) return;
    
    setUpdatingItems(prev => new Set(prev).add(itemId));
    
    try {
      const updatedCart = await cartService.removeFromCart(itemId);
      setCart(updatedCart);
    } catch (error) {
      console.error('Failed to remove item:', error);
    } finally {
      setUpdatingItems(prev => {
        const newSet = new Set(prev);
        newSet.delete(itemId);
        return newSet;
      });
    }
  };

  const handleClearCart = async () => {
    try {
      await cartService.clearCart();
      setCart({ id: '', items: [], total: 0, item_count: 0 });
    } catch (error) {
      console.error('Failed to clear cart:', error);
    }
  };

  const handleProceedToCheckout = () => {
    setShowCheckout(true);
  };

  const handleCheckoutComplete = (orderId: string) => {
    // Cart is already cleared by checkout component
    setShowCheckout(false);
    onClose();
    // Could show a success notification here
  };

  const handleCheckoutClose = () => {
    setShowCheckout(false);
    loadCart(); // Reload cart in case it changed
  };

  const getThemeColors = () => {
    switch (currentTemplate) {
      case 'pot-palace':
        return {
          primary: 'bg-purple-600 hover:bg-purple-700',
          secondary: 'bg-purple-100 text-purple-700',
          accent: 'text-purple-600',
          border: 'border-purple-200'
        };
      case 'modern-minimal':
        return {
          primary: 'bg-blue-600 hover:bg-blue-700',
          secondary: 'bg-blue-100 text-blue-700',
          accent: 'text-blue-600',
          border: 'border-blue-200'
        };
      case 'dark-tech':
        return {
          primary: 'bg-green-600 hover:bg-green-700',
          secondary: 'bg-green-100 text-green-700',
          accent: 'text-green-600',
          border: 'border-green-200'
        };
      default:
        return {
          primary: 'bg-gray-600 hover:bg-gray-700',
          secondary: 'bg-gray-100 text-gray-700',
          accent: 'text-gray-600',
          border: 'border-gray-200'
        };
    }
  };

  const theme = getThemeColors();

  if (showCheckout) {
    return (
      <Checkout 
        onClose={handleCheckoutClose}
        onComplete={handleCheckoutComplete}
      />
    );
  }

  useEffect(() => {
    console.log('Cart component - isOpen:', isOpen);
  }, [isOpen]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 z-[9998]"
            onClick={onClose}
          />
          
          {/* Cart Sidebar */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed right-0 top-0 h-full w-full sm:w-96 bg-white shadow-xl z-[9999] flex flex-col"
          >
            {/* Header */}
            <div className={`flex items-center justify-between p-4 border-b ${theme.border}`}>
              <div className="flex items-center space-x-2">
                <FiShoppingCart className={`w-5 h-5 ${theme.accent}`} />
                <h2 className="text-lg font-semibold">Your Cart</h2>
                {cart && cart.item_count > 0 && (
                  <span className={`px-2 py-1 text-xs rounded-full ${theme.secondary}`}>
                    {cart.item_count} {cart.item_count === 1 ? 'item' : 'items'}
                  </span>
                )}
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <FiX className="w-5 h-5" />
              </button>
            </div>

            {/* Cart Content */}
            <div className="flex-1 overflow-y-auto">
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-600"></div>
                </div>
              ) : !cart || cart.items.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 px-4">
                  <FiShoppingCart className="w-16 h-16 text-gray-300 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Your cart is empty</h3>
                  <p className="text-sm text-gray-500 text-center">
                    Add some products to your cart and they'll appear here
                  </p>
                </div>
              ) : (
                <div className="p-4 space-y-4">
                  {cart.items.map((item) => (
                    <div key={item.id} className="flex space-x-3 p-3 bg-gray-50 rounded-lg">
                      {/* Product Image */}
                      {item.product_image && (
                        <img
                          src={item.product_image}
                          alt={item.product_name}
                          className="w-16 h-16 object-cover rounded-md"
                        />
                      )}
                      
                      {/* Product Details */}
                      <div className="flex-1">
                        <h4 className="text-sm font-medium text-gray-900">{item.product_name}</h4>
                        <p className="text-xs text-gray-500 mt-1">${item.price.toFixed(2)} each</p>
                        
                        {/* Quantity Controls */}
                        <div className="flex items-center mt-2 space-x-2">
                          <button
                            onClick={() => handleUpdateQuantity(item.id, item.quantity - 1)}
                            disabled={item.quantity <= 1 || updatingItems.has(item.id)}
                            className="p-1 hover:bg-gray-200 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            <FiMinus className="w-3 h-3" />
                          </button>
                          
                          <span className="text-sm font-medium w-8 text-center">
                            {updatingItems.has(item.id) ? (
                              <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-gray-600 mx-auto"></div>
                            ) : (
                              item.quantity
                            )}
                          </span>
                          
                          <button
                            onClick={() => handleUpdateQuantity(item.id, item.quantity + 1)}
                            disabled={updatingItems.has(item.id)}
                            className="p-1 hover:bg-gray-200 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            <FiPlus className="w-3 h-3" />
                          </button>
                          
                          <button
                            onClick={() => handleRemoveItem(item.id)}
                            disabled={updatingItems.has(item.id)}
                            className="ml-auto p-1 text-red-600 hover:bg-red-50 rounded disabled:opacity-50"
                          >
                            <FiTrash2 className="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                      
                      {/* Subtotal */}
                      <div className="text-right">
                        <p className="text-sm font-semibold text-gray-900">
                          ${item.subtotal.toFixed(2)}
                        </p>
                      </div>
                    </div>
                  ))}
                  
                  {/* Clear Cart Button */}
                  <button
                    onClick={handleClearCart}
                    className="w-full py-2 text-sm text-red-600 hover:text-red-700 transition-colors"
                  >
                    Clear Cart
                  </button>
                </div>
              )}
            </div>

            {/* Footer with Total and Checkout */}
            {cart && cart.items.length > 0 && (
              <div className={`border-t ${theme.border} p-4 space-y-4`}>
                <div className="flex justify-between items-center">
                  <span className="text-lg font-semibold">Total:</span>
                  <span className="text-xl font-bold">${cart.total.toFixed(2)}</span>
                </div>
                
                <button
                  onClick={handleProceedToCheckout}
                  className={`w-full py-3 px-4 text-white font-medium rounded-lg transition-colors flex items-center justify-center space-x-2 ${theme.primary}`}
                >
                  <span>Proceed to Checkout</span>
                  <FiArrowRight className="w-4 h-4" />
                </button>
                
                <p className="text-xs text-gray-500 text-center">
                  Taxes and delivery calculated at checkout
                </p>
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default Cart;