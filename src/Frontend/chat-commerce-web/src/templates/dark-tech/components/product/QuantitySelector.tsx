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
      <div className="flex items-center bg-black/50 border border-green-500/30 rounded-lg overflow-hidden shadow-[0_0_10px_rgba(34,197,94,0.2)]">
        {/* Decrement Button */}
        <button
          onClick={handleDecrement}
          disabled={quantity <= min}
          className="w-10 h-10 flex items-center justify-center text-green-400 hover:bg-green-500/10 disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-200 group"
          aria-label="Decrease quantity"
        >
          <svg className="w-5 h-5 group-hover:scale-110 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
          </svg>
        </button>

        {/* Quantity Display */}
        <div className="px-4 min-w-[60px] text-center">
          <input
            type="number"
            value={quantity}
            onChange={handleInputChange}
            min={min}
            max={max}
            className="w-full bg-transparent text-green-400 font-mono font-bold text-lg text-center focus:outline-none appearance-none"
            style={{ MozAppearance: 'textfield' }}
          />
          <div className="text-xs text-green-300/50 font-mono">QTY</div>
        </div>

        {/* Increment Button */}
        <button
          onClick={handleIncrement}
          disabled={quantity >= max}
          className="w-10 h-10 flex items-center justify-center text-green-400 hover:bg-green-500/10 disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-200 group"
          aria-label="Increase quantity"
        >
          <svg className="w-5 h-5 group-hover:scale-110 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>
      </div>

      {/* Digital effect decorations */}
      <div className="ml-2 flex items-center gap-1">
        <div className="w-1 h-1 bg-green-400 rounded-full animate-pulse"></div>
        <div className="w-1 h-1 bg-green-400 rounded-full animate-pulse delay-75"></div>
        <div className="w-1 h-1 bg-green-400 rounded-full animate-pulse delay-150"></div>
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