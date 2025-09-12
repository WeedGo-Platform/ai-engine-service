import React from 'react';

interface QuantitySelectorProps {
  quantity: number;
  onChange: (quantity: number) => void;
  min?: number;
  max?: number;
}

const QuantitySelector: React.FC<QuantitySelectorProps> = ({
  quantity,
  onChange,
  min = 1,
  max = 99
}) => {
  const handleIncrement = () => {
    if (quantity < max) {
      onChange(quantity + 1);
    }
  };

  const handleDecrement = () => {
    if (quantity > min) {
      onChange(quantity - 1);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value >= min && value <= max) {
      onChange(value);
    }
  };

  return (
    <div className="flex items-center">
      <div className="flex items-center bg-white rounded-full shadow-lg overflow-hidden border-2 border-yellow-400">
        {/* Decrement Button */}
        <button
          onClick={handleDecrement}
          disabled={quantity <= min}
          className="w-12 h-12 flex items-center justify-center text-red-600 hover:bg-red-50 disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-200 group"
          aria-label="Decrease quantity"
        >
          <svg className="w-6 h-6 group-hover:scale-110 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M20 12H4" />
          </svg>
        </button>

        {/* Quantity Display */}
        <div className="px-6 min-w-[80px] text-center bg-gradient-to-b from-yellow-50 to-yellow-100">
          <input
            type="number"
            value={quantity}
            onChange={handleInputChange}
            min={min}
            max={max}
            className="w-full bg-transparent text-green-700 font-bold text-xl text-center focus:outline-none appearance-none"
            style={{ MozAppearance: 'textfield' }}
          />
          <div className="text-xs text-gray-600 font-medium">Amount</div>
        </div>

        {/* Increment Button */}
        <button
          onClick={handleIncrement}
          disabled={quantity >= max}
          className="w-12 h-12 flex items-center justify-center text-green-600 hover:bg-green-50 disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-200 group"
          aria-label="Increase quantity"
        >
          <svg className="w-6 h-6 group-hover:scale-110 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M12 4v16m8-8H4" />
          </svg>
        </button>
      </div>

      {/* Decorative elements */}
      <div className="ml-3 flex flex-col gap-1">
        <div className="flex gap-1">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse delay-75"></div>
          <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse delay-150"></div>
        </div>
        <span className="text-xs text-gray-600 font-medium">Irie!</span>
      </div>

      <style jsx>{`
        /* Chrome, Safari, Edge, Opera */
        input::-webkit-outer-spin-button,
        input::-webkit-inner-spin-button {
          -webkit-appearance: none;
          margin: 0;
        }

        /* Firefox */
        input[type=number] {
          -moz-appearance: textfield;
        }

        .delay-75 {
          animation-delay: 75ms;
        }

        .delay-150 {
          animation-delay: 150ms;
        }
      `}</style>
    </div>
  );
};

export default QuantitySelector;