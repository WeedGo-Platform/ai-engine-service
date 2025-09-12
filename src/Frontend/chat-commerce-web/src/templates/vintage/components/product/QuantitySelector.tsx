import React from 'react';
import { QuantitySelectorProps } from '../../../../types/product.types';

const QuantitySelector: React.FC<QuantitySelectorProps> = ({
  quantity,
  onQuantityChange,
  min = 1,
  max = 99,
  disabled = false,
  size = 'md',
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
    const value = parseInt(e.target.value);
    if (!isNaN(value) && value >= min && value <= max) {
      onQuantityChange(value);
    }
  };

  const sizes = {
    sm: {
      button: 'w-8 h-8 text-sm',
      input: 'w-12 text-sm',
    },
    md: {
      button: 'w-10 h-10 text-base',
      input: 'w-16 text-base',
    },
    lg: {
      button: 'w-12 h-12 text-lg',
      input: 'w-20 text-lg',
    },
  };

  const sizeClass = sizes[size];

  return (
    <div className="flex items-center">
      <button
        onClick={handleDecrease}
        disabled={disabled || quantity <= min}
        className={`${sizeClass.button} rounded-l-lg border border-r-0 border-gray-300 bg-white hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors`}
        aria-label="Decrease quantity"
      >
        <svg className="w-4 h-4 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
        className={`${sizeClass.input} h-10 text-center border-t border-b border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed`}
      />
      
      <button
        onClick={handleIncrease}
        disabled={disabled || quantity >= max}
        className={`${sizeClass.button} rounded-r-lg border border-l-0 border-gray-300 bg-white hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors`}
        aria-label="Increase quantity"
      >
        <svg className="w-4 h-4 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
      </button>
    </div>
  );
};

export default QuantitySelector;