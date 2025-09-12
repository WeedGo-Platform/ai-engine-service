import React from 'react';
import { QuantitySelectorProps } from '../../../../types/product.types';

const QuantitySelector: React.FC<QuantitySelectorProps> = ({
  quantity,
  onQuantityChange,
  min = 1,
  max = 99,
  disabled = false,
  size = 'md'
}) => {
  const handleDecrease = () => {
    if (quantity > min) {
      onQuantityChange(quantity - 1);
    }
  };

  const handleIncrease = () => {
    if (quantity < max) {
      onQuantityChange(quantity + 1);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value >= min && value <= max) {
      onQuantityChange(value);
    }
  };

  // Size styles
  const sizeStyles = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg'
  };

  const buttonSizeStyles = {
    sm: 'p-1',
    md: 'p-2',
    lg: 'p-3'
  };

  const inputSizeStyles = {
    sm: 'px-2 py-1 min-w-[2rem]',
    md: 'px-3 py-2 min-w-[3rem]',
    lg: 'px-4 py-3 min-w-[4rem]'
  };

  return (
    <div className={`flex items-center ${sizeStyles[size]}`}>
      <span className="text-purple-700 font-medium mr-3">Quantity:</span>
      <div className="flex items-center border-2 border-purple-300 rounded-xl overflow-hidden bg-white shadow-md">
        <button
          onClick={handleDecrease}
          disabled={disabled || quantity <= min}
          className={`${buttonSizeStyles[size]} bg-gradient-to-r from-purple-100 to-purple-50 hover:from-purple-200 hover:to-purple-100 transition-all disabled:opacity-50 disabled:cursor-not-allowed group`}
          aria-label="Decrease quantity"
        >
          <svg 
            className="w-4 h-4 text-purple-600 group-hover:text-purple-700" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
          </svg>
        </button>
        
        <input
          type="number"
          value={quantity}
          onChange={handleInputChange}
          disabled={disabled}
          min={min}
          max={max}
          className={`${inputSizeStyles[size]} text-center font-bold text-purple-800 bg-purple-50 border-x-2 border-purple-200 focus:outline-none focus:bg-white disabled:opacity-50 disabled:cursor-not-allowed`}
        />
        
        <button
          onClick={handleIncrease}
          disabled={disabled || quantity >= max}
          className={`${buttonSizeStyles[size]} bg-gradient-to-r from-purple-100 to-purple-50 hover:from-purple-200 hover:to-purple-100 transition-all disabled:opacity-50 disabled:cursor-not-allowed group`}
          aria-label="Increase quantity"
        >
          <svg 
            className="w-4 h-4 text-purple-600 group-hover:text-purple-700" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>
      </div>
    </div>
  );
};

export default QuantitySelector;