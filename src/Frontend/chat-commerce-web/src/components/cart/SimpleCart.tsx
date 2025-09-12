import React, { useState } from 'react';
import { FiShoppingCart, FiX, FiPlus, FiMinus, FiTrash2, FiArrowRight } from 'react-icons/fi';
import { useCart } from '../../contexts/CartContext';
import { useTemplateContext } from '../../contexts/TemplateContext';
import CartModal from './CartModal';
import Checkout from '../checkout/Checkout';

interface SimpleCartProps {
  isOpen: boolean;
  onClose: () => void;
}

const SimpleCart: React.FC<SimpleCartProps> = ({ isOpen, onClose }) => {
  const { currentTemplate } = useTemplateContext();
  const { cart, isLoading, updateQuantity, removeFromCart, clearCart } = useCart();
  const [updatingItems, setUpdatingItems] = useState<Set<string>>(new Set());
  const [showCheckout, setShowCheckout] = useState(false);

  const handleUpdateQuantity = async (itemId: string, newQuantity: number) => {
    if (!cart || newQuantity < 1) return;
    
    setUpdatingItems(prev => new Set(prev).add(itemId));
    
    try {
      await updateQuantity(itemId, newQuantity);
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
      await removeFromCart(itemId);
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
      await clearCart();
    } catch (error) {
      console.error('Failed to clear cart:', error);
    }
  };

  const handleProceedToCheckout = () => {
    setShowCheckout(true);
  };

  const handleCheckoutComplete = (orderId: string) => {
    setShowCheckout(false);
    onClose();
  };

  const handleCheckoutClose = () => {
    setShowCheckout(false);
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
      default:
        return {
          primary: 'bg-blue-600 hover:bg-blue-700',
          secondary: 'bg-blue-100 text-blue-700',
          accent: 'text-blue-600',
          border: 'border-blue-200'
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

  return (
    <CartModal isOpen={isOpen} onClose={onClose}>
      {/* Header */}
      <div className={`flex items-center justify-between p-4 border-b ${theme.border}`}>
        <div className="flex items-center space-x-2">
          <FiShoppingCart className={`w-5 h-5 ${theme.accent}`} />
          <h2 className="text-lg font-semibold">Your Cart</h2>
          {cart && cart.items && cart.items.length > 0 && (
            <span className={`px-2 py-1 text-xs rounded-full ${theme.secondary}`}>
              {cart.items.reduce((sum, item) => sum + item.quantity, 0)} items
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
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-600"></div>
          </div>
        ) : !cart || !cart.items || cart.items.length === 0 ? (
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
              <div key={item.id} className="flex space-x-4 p-4 bg-white rounded-lg border border-gray-200 hover:border-gray-300 hover:shadow-md transition-all duration-200">
                {/* Product Image */}
                <div className="w-20 h-20 flex-shrink-0 relative bg-gray-100 rounded-lg overflow-hidden">
                  <img
                    src={item.product_image || '/placeholder-product.png'}
                    alt={item.product_name || 'Product'}
                    className="w-full h-full object-cover rounded-lg"
                    loading="lazy"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.src = '/placeholder-product.png';
                      target.onerror = null; // Prevent infinite loop
                    }}
                  />
                </div>
                
                {/* Product Details */}
                <div className="flex-1 min-w-0">
                  <h4 className="text-base font-semibold text-gray-900 truncate">
                    {item.product_name || 'Unknown Product'}
                  </h4>
                  <p className="text-sm text-gray-600 mt-1">${(item.price || 0).toFixed(2)} each</p>
                  
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
                <div className="text-right flex-shrink-0">
                  <p className="text-lg font-bold text-gray-900">
                    ${(item.subtotal || 0).toFixed(2)}
                  </p>
                  <p className="text-xs text-gray-500">Subtotal</p>
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
      {cart && cart.items && cart.items.length > 0 && (
        <div className={`border-t ${theme.border} p-4 space-y-4`}>
          <div className="flex justify-between items-center">
            <span className="text-lg font-semibold">Total:</span>
            <span className="text-xl font-bold">${(cart.total || 0).toFixed(2)}</span>
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
    </CartModal>
  );
};

export default SimpleCart;