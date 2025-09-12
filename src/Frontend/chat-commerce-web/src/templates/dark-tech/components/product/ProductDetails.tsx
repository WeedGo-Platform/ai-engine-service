import React, { useState } from 'react';
import { Product } from '../../../../services/productSearch';
import { useCart } from '../../../../contexts/CartContext';
import QuantitySelector from './QuantitySelector';
import ProductRecommendations from './ProductRecommendations';

interface ProductDetailsProps {
  product: Product;
}

const ProductDetails: React.FC<ProductDetailsProps> = ({ product }) => {
  const [quantity, setQuantity] = useState(1);
  const [imageError, setImageError] = useState(false);
  const [isAddingToCart, setIsAddingToCart] = useState(false);
  const { addToCart } = useCart();

  const handleAddToCart = async () => {
    setIsAddingToCart(true);
    try {
      await addToCart(product, quantity);
      // Reset quantity after successful add
      setQuantity(1);
    } catch (error) {
      console.error('Failed to add to cart:', error);
    } finally {
      setIsAddingToCart(false);
    }
  };

  const getStrainBadgeColor = (strain?: string) => {
    switch (strain?.toLowerCase()) {
      case 'indica':
        return 'bg-purple-900/50 text-purple-300 border-purple-500/50';
      case 'sativa':
        return 'bg-green-900/50 text-green-300 border-green-500/50';
      case 'hybrid':
        return 'bg-blue-900/50 text-blue-300 border-blue-500/50';
      default:
        return 'bg-gray-900/50 text-gray-300 border-gray-500/50';
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* Main Product Card - Dark Tech Style */}
      <div className="bg-black/90 backdrop-blur-xl rounded-lg border border-green-500/30 shadow-[0_0_30px_rgba(34,197,94,0.2)] overflow-hidden">
        {/* Matrix-style animated border */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute inset-0 border border-green-500/20 animate-pulse"></div>
          <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-green-400 to-transparent animate-scan"></div>
        </div>

        <div className="relative p-6">
          {/* Header with glitch effect */}
          <div className="flex items-start justify-between mb-6">
            <div>
              <h2 className="text-2xl font-mono font-bold text-green-400 mb-2 glitch-text">
                {product.name}
              </h2>
              {product.brand && (
                <p className="text-sm text-green-300/70 font-mono uppercase tracking-wider">
                  MANUFACTURER: {product.brand}
                </p>
              )}
            </div>
            
            {/* Price display with digital effect */}
            <div className="text-right">
              <div className="text-3xl font-mono font-bold text-green-400">
                <span className="text-lg">$</span>
                {product.price.toFixed(2)}
              </div>
              {product.size && (
                <div className="text-xs text-green-300/50 font-mono mt-1">
                  UNIT: {product.size}
                </div>
              )}
            </div>
          </div>

          {/* Product Image with cyber frame */}
          <div className="relative mb-6 group">
            <div className="absolute inset-0 bg-gradient-to-r from-green-500/20 to-blue-500/20 blur-xl group-hover:blur-2xl transition-all duration-500"></div>
            <div className="relative bg-black/50 rounded-lg p-2 border border-green-500/30">
              {(product.image_url || product.thumbnail_url) && !imageError ? (
                <img
                  src={product.image_url || product.thumbnail_url}
                  alt={product.name}
                  className="w-full h-64 object-contain rounded"
                  onError={() => setImageError(true)}
                />
              ) : (
                <div className="w-full h-64 flex items-center justify-center bg-gradient-to-br from-gray-900 to-black rounded">
                  <div className="text-center">
                    <svg className="w-20 h-20 mx-auto text-green-500/30 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    <p className="font-mono text-xs text-green-500/50">NO_IMAGE_DATA</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Strain and Category Badges */}
          <div className="flex flex-wrap gap-2 mb-6">
            {product.strain_type && (
              <span className={`px-3 py-1 text-xs font-mono uppercase border ${getStrainBadgeColor(product.strain_type)} rounded-full`}>
                {product.strain_type}
              </span>
            )}
            {product.category && (
              <span className="px-3 py-1 text-xs font-mono uppercase bg-gray-900/50 text-gray-300 border border-gray-500/50 rounded-full">
                {product.category}
              </span>
            )}
            {product.plant_type && (
              <span className="px-3 py-1 text-xs font-mono uppercase bg-cyan-900/50 text-cyan-300 border border-cyan-500/50 rounded-full">
                {product.plant_type}
              </span>
            )}
          </div>

          {/* THC/CBD Content - Digital Display */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-black/50 border border-green-500/20 rounded p-3">
              <div className="text-xs font-mono text-green-300/70 mb-1">THC_LEVEL</div>
              <div className="text-2xl font-mono font-bold text-green-400">
                {product.thc_content || 0}%
              </div>
              <div className="h-2 bg-black/50 rounded-full mt-2 overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-green-500 to-green-300 animate-pulse"
                  style={{ width: `${Math.min((product.thc_content || 0) * 3, 100)}%` }}
                ></div>
              </div>
            </div>

            <div className="bg-black/50 border border-blue-500/20 rounded p-3">
              <div className="text-xs font-mono text-blue-300/70 mb-1">CBD_LEVEL</div>
              <div className="text-2xl font-mono font-bold text-blue-400">
                {product.cbd_content || 0}%
              </div>
              <div className="h-2 bg-black/50 rounded-full mt-2 overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-blue-500 to-blue-300 animate-pulse"
                  style={{ width: `${Math.min((product.cbd_content || 0) * 10, 100)}%` }}
                ></div>
              </div>
            </div>
          </div>

          {/* Description with typewriter effect */}
          {product.description && (
            <div className="mb-6">
              <h3 className="text-sm font-mono uppercase text-green-400 mb-2">PRODUCT_DESCRIPTION</h3>
              <p className="text-gray-300 leading-relaxed font-mono text-sm">
                {product.description}
              </p>
            </div>
          )}

          {/* Terpenes - Matrix style list */}
          {product.terpenes && product.terpenes.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-mono uppercase text-green-400 mb-2">TERPENE_PROFILE</h3>
              <div className="flex flex-wrap gap-2">
                {product.terpenes && Array.isArray(product.terpenes) && product.terpenes.map((terpene, index) => (
                  <span 
                    key={index}
                    className="px-2 py-1 text-xs font-mono bg-green-900/20 text-green-300 border border-green-500/30 rounded"
                  >
                    {terpene}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Add to Cart Section */}
          <div className="border-t border-green-500/20 pt-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <QuantitySelector
                  quantity={quantity}
                  onChange={setQuantity}
                />
                <div className="text-green-400 font-mono">
                  <span className="text-sm text-green-300/70">TOTAL: </span>
                  <span className="text-xl font-bold">${(product.price * quantity).toFixed(2)}</span>
                </div>
              </div>

              <button
                onClick={handleAddToCart}
                disabled={isAddingToCart}
                className="px-6 py-3 bg-gradient-to-r from-green-500 to-green-600 text-black font-mono font-bold uppercase rounded hover:from-green-400 hover:to-green-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-[0_0_20px_rgba(34,197,94,0.5)] hover:shadow-[0_0_30px_rgba(34,197,94,0.7)]"
              >
                {isAddingToCart ? (
                  <span className="flex items-center gap-2">
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    PROCESSING...
                  </span>
                ) : (
                  'ADD_TO_CART'
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Product Recommendations */}
      <div className="mt-8">
        <ProductRecommendations currentProduct={product} />
      </div>

      {/* Add CSS for animations */}
      <style jsx>{`
        @keyframes scan {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        
        .animate-scan {
          animation: scan 3s linear infinite;
        }
        
        .glitch-text {
          position: relative;
        }
        
        .glitch-text::before,
        .glitch-text::after {
          content: attr(data-text);
          position: absolute;
          left: 0;
          top: 0;
          width: 100%;
          height: 100%;
        }
        
        .glitch-text::before {
          animation: glitch-1 0.3s linear infinite alternate-reverse;
          color: #00ff00;
          z-index: -1;
        }
        
        .glitch-text::after {
          animation: glitch-2 0.3s linear infinite alternate-reverse;
          color: #00ffff;
          z-index: -2;
        }
        
        @keyframes glitch-1 {
          0% { clip-path: inset(0 0 100% 0); transform: translateX(0); }
          100% { clip-path: inset(100% 0 0 0); transform: translateX(-2px); }
        }
        
        @keyframes glitch-2 {
          0% { clip-path: inset(0 0 100% 0); transform: translateX(0); }
          100% { clip-path: inset(100% 0 0 0); transform: translateX(2px); }
        }
      `}</style>
    </div>
  );
};

export default ProductDetails;