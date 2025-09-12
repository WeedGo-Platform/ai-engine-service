import React, { useState, useEffect } from 'react';
import { FiShoppingCart } from 'react-icons/fi';
import { motion, AnimatePresence } from 'framer-motion';
import { cartService } from '../../services/cart';
import { useTemplateContext } from '../../contexts/TemplateContext';
import { useCart } from '../../contexts/CartContext';
import SimpleCart from './SimpleCart';

interface CartButtonProps {
  className?: string;
}

const CartButton: React.FC<CartButtonProps> = ({ className = '' }) => {
  const { currentTemplate } = useTemplateContext();
  const { itemCount: contextItemCount } = useCart();
  const [itemCount, setItemCount] = useState(0);
  const [isCartOpen, setIsCartOpen] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    loadCartCount();
    
    // Set up interval to refresh cart count
    const interval = setInterval(loadCartCount, 5000);
    
    // Listen for cart updates
    const handleCartUpdate = () => {
      loadCartCount();
      setIsAnimating(true);
      setTimeout(() => setIsAnimating(false), 500);
    };
    
    window.addEventListener('cartUpdated', handleCartUpdate);
    
    return () => {
      clearInterval(interval);
      window.removeEventListener('cartUpdated', handleCartUpdate);
    };
  }, []);

  // Update local count when context count changes
  useEffect(() => {
    if (contextItemCount !== undefined && contextItemCount !== itemCount) {
      setItemCount(contextItemCount);
      setIsAnimating(true);
      setTimeout(() => setIsAnimating(false), 500);
    }
  }, [contextItemCount]);

  const loadCartCount = async () => {
    try {
      const count = await cartService.getCartCount();
      setItemCount(count);
    } catch (error) {
      console.error('Failed to load cart count:', error);
    }
  };

  const getThemeColors = () => {
    switch (currentTemplate) {
      case 'pot-palace':
        return {
          primary: 'bg-purple-600 hover:bg-purple-700',
          badge: 'bg-purple-500',
          text: 'text-white'
        };
      case 'modern-minimal':
        return {
          primary: 'bg-blue-600 hover:bg-blue-700',
          badge: 'bg-blue-500',
          text: 'text-white'
        };
      case 'dark-tech':
        return {
          primary: 'bg-green-600 hover:bg-green-700',
          badge: 'bg-green-500',
          text: 'text-white'
        };
      default:
        return {
          primary: 'bg-gray-600 hover:bg-gray-700',
          badge: 'bg-gray-500',
          text: 'text-white'
        };
    }
  };

  const theme = getThemeColors();

  const handleCartClick = () => {
    console.log('Cart button clicked, opening cart...');
    setIsCartOpen(true);
  };

  const handleCartClose = () => {
    console.log('Closing cart...');
    setIsCartOpen(false);
  };

  return (
    <>
      <button
        onClick={handleCartClick}
        className={`relative p-3 rounded-lg transition-all duration-200 ${theme.primary} ${theme.text} ${className}`}
        aria-label="Open cart"
      >
        <motion.div
          animate={isAnimating ? { scale: [1, 1.2, 1] } : {}}
          transition={{ duration: 0.3 }}
        >
          <FiShoppingCart className="w-5 h-5" />
        </motion.div>
        
        <AnimatePresence>
          {itemCount > 0 && (
            <motion.span
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0 }}
              className={`absolute -top-1 -right-1 min-w-[20px] h-5 px-1 flex items-center justify-center text-xs font-bold rounded-full ${theme.badge} ${theme.text}`}
            >
              {itemCount > 99 ? '99+' : itemCount}
            </motion.span>
          )}
        </AnimatePresence>
      </button>

      {isCartOpen && <SimpleCart isOpen={isCartOpen} onClose={handleCartClose} />}
    </>
  );
};

export default CartButton;