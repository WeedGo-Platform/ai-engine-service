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

  const sizeStyles = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base'
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
      <div className="flex items-center border border-gray-300 rounded-sm overflow-hidden bg-white">
        <button
          onClick={handleDecrease}
          disabled={disabled || quantity <= min}
          className={`${buttonSizeStyles[size]} hover:bg-gray-50 transition-colors disabled:opacity-30 disabled:cursor-not-allowed`}
          aria-label="Decrease quantity"
        >
          <svg 
            className="w-3 h-3 text-gray-600" 
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
          className={`${inputSizeStyles[size]} text-center font-light text-gray-900 border-x border-gray-300 focus:outline-none focus:bg-gray-50 disabled:opacity-30 disabled:cursor-not-allowed`}
        />
        
        <button
          onClick={handleIncrease}
          disabled={disabled || quantity >= max}
          className={`${buttonSizeStyles[size]} hover:bg-gray-50 transition-colors disabled:opacity-30 disabled:cursor-not-allowed`}
          aria-label="Increase quantity"
        >
          <svg 
            className="w-3 h-3 text-gray-600" 
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