import React, { useState } from 'react';
import { useCart } from '../../contexts/CartContext';
import SimpleCart from '../cart/SimpleCart';

interface CartButtonProps {
  className?: string;
  buttonClassName?: string;
  iconClassName?: string;
  badgeClassName?: string;
  counterClassName?: string;
}

const CartButton: React.FC<CartButtonProps> = ({
  className = '',
  buttonClassName = 'p-2.5 rounded-lg hover:bg-slate-100 transition-all duration-200 group relative',
  iconClassName = 'w-4 h-4 text-slate-700 group-hover:text-slate-900 transition-colors',
  badgeClassName = 'absolute -top-1 -right-1 min-w-[20px] h-5 bg-red-500 text-white rounded-full flex items-center justify-center',
  counterClassName = 'text-xs font-bold px-1'
}) => {
  const { itemCount } = useCart();
  const [showCart, setShowCart] = useState(false);

  return (
    <>
      <button 
        onClick={() => setShowCart(true)}
        className={`${buttonClassName} ${className}`} 
        title="Cart"
      >
        <svg 
          className={iconClassName} 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth="1.5" 
            d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" 
          />
        </svg>
        {itemCount > 0 && (
          <span className={badgeClassName}>
            <span className={counterClassName}>
              {itemCount > 99 ? '99+' : itemCount}
            </span>
          </span>
        )}
      </button>

      {/* Cart Modal - SimpleCart handles its own modal */}
      <SimpleCart 
        isOpen={showCart} 
        onClose={() => setShowCart(false)} 
      />
    </>
  );
};

export default CartButton;