import React, { useState } from 'react';
import { Product } from '../../../../services/productSearch';
import { ProductDetailsProps } from '../../../../types/product.types';
import { useCart } from '../../../../contexts/CartContext';
import ProductRecommendations from './ProductRecommendations';
import QuantitySelector from './QuantitySelector';

const ProductDetails: React.FC<ProductDetailsProps> = ({
  product,
  onClose,
  onAddToCart,
  showRecommendations = true
}) => {
  const [quantity, setQuantity] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [activeImageIndex, setActiveImageIndex] = useState(0);
  const { addToCart } = useCart();

  // Format price
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(price);
  };

  // Handle add to cart
  const handleAddToCart = async () => {
    setIsLoading(true);
    try {
      if (onAddToCart) {
        await onAddToCart(product, quantity);
      } else {
        await addToCart(product, quantity);
      }
      setQuantity(1);
    } catch (error) {
      console.error('Failed to add to cart:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Get strain type style - Pot Palace purple theme
  const getStrainTypeStyle = (type?: string) => {
    switch (type?.toLowerCase()) {
      case 'indica': return 'bg-gradient-to-r from-purple-600 to-purple-700';
      case 'sativa': return 'bg-gradient-to-r from-green-500 to-green-600';
      case 'hybrid': return 'bg-gradient-to-r from-purple-500 to-green-500';
      case 'cbd': return 'bg-gradient-to-r from-orange-500 to-orange-600';
      default: return 'bg-gradient-to-r from-gray-500 to-gray-600';
    }
  };

  // Product images
  const productImages = [
    product.image_url,
    product.thumbnail_url
  ].filter(Boolean);

  return (
    <div className="bg-gradient-to-br from-purple-50 to-white rounded-2xl shadow-xl overflow-hidden border border-purple-200">
      {/* Header with close button - Pot Palace style */}
      {onClose && (
        <div className="flex justify-between items-center p-4 bg-gradient-to-r from-purple-600 to-purple-700 text-white">
          <div className="flex items-center gap-2">
            {/* Cannabis leaf icon */}
            <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C12 2 9 4 9 7C9 7 6 5 3 7C3 7 5 10 5 13C5 13 2 12 0 15C0 15 3 17 6 17C6 17 5 20 7 22C7 22 9 19 12 19C15 19 17 22 17 22C19 20 18 17 18 17C21 17 24 15 24 15C22 12 19 13 19 13C19 10 21 7 21 7C18 5 15 7 15 7C15 4 12 2 12 2Z"/>
            </svg>
            <h2 className="text-xl font-bold">Product Details</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/20 rounded-full transition-colors"
            aria-label="Close"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Product Images with Pot Palace styling */}
          <div className="space-y-4">
            <div className="aspect-square bg-gradient-to-br from-purple-100 to-purple-50 rounded-xl overflow-hidden shadow-lg">
              {productImages[activeImageIndex] ? (
                <img
                  src={productImages[activeImageIndex]}
                  alt={product.name}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = '/placeholder-product.png';
                  }}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <svg className="w-20 h-20 text-purple-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
              )}
              
              {/* Decorative cannabis leaf overlay */}
              <div className="absolute top-2 right-2 opacity-10">
                <svg className="w-16 h-16 text-purple-700" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C12 2 9 4 9 7C9 7 6 5 3 7C3 7 5 10 5 13C5 13 2 12 0 15C0 15 3 17 6 17C6 17 5 20 7 22C7 22 9 19 12 19C15 19 17 22 17 22C19 20 18 17 18 17C21 17 24 15 24 15C22 12 19 13 19 13C19 10 21 7 21 7C18 5 15 7 15 7C15 4 12 2 12 2Z"/>
                </svg>
              </div>
            </div>

            {/* Thumbnail Images */}
            {productImages.length > 1 && (
              <div className="flex gap-2">
                {productImages.map((img, index) => img && (
                  <button
                    key={index}
                    onClick={() => setActiveImageIndex(index)}
                    className={`w-20 h-20 rounded-lg overflow-hidden border-2 transition-all ${
                      activeImageIndex === index 
                        ? 'border-purple-500 shadow-lg scale-105' 
                        : 'border-purple-200 hover:border-purple-400'
                    }`}
                  >
                    <img
                      src={img}
                      alt={`${product.name} ${index + 1}`}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = '/placeholder-product.png';
                      }}
                    />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Product Information with Pot Palace theme */}
          <div className="space-y-4">
            {/* Name and Brand */}
            <div>
              <h1 className="text-3xl font-bold text-purple-900">{product.name}</h1>
              {product.brand && (
                <p className="text-lg text-purple-600 font-medium">{product.brand}</p>
              )}
            </div>

            {/* Badges with cannabis theme */}
            <div className="flex flex-wrap gap-2">
              {product.plant_type && (
                <span className={`px-4 py-1.5 rounded-full text-white text-sm font-medium shadow-lg ${getStrainTypeStyle(product.plant_type)}`}>
                  {product.plant_type}
                </span>
              )}
              {product.strain_type && (
                <span className="px-4 py-1.5 rounded-full bg-gradient-to-r from-purple-200 to-purple-300 text-purple-800 text-sm font-medium">
                  {product.strain_type}
                </span>
              )}
              {product.category && (
                <span className="px-4 py-1.5 rounded-full bg-purple-100 text-purple-700 text-sm font-medium">
                  {product.category}
                </span>
              )}
            </div>

            {/* THC/CBD Content with special styling */}
            {(product.thc_content || product.cbd_content) && (
              <div className="flex gap-4 p-4 bg-gradient-to-r from-purple-100 to-purple-50 rounded-xl shadow-inner">
                {product.thc_content !== undefined && (
                  <div className="flex-1 text-center">
                    <div className="flex items-center justify-center gap-1 mb-1">
                      <span className="text-sm text-purple-600 font-medium">THC</span>
                      <svg className="w-4 h-4 text-purple-500" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C12 2 9 4 9 7C9 7 6 5 3 7C3 7 5 10 5 13C5 13 2 12 0 15C0 15 3 17 6 17C6 17 5 20 7 22C7 22 9 19 12 19C15 19 17 22 17 22C19 20 18 17 18 17C21 17 24 15 24 15C22 12 19 13 19 13C19 10 21 7 21 7C18 5 15 7 15 7C15 4 12 2 12 2Z"/>
                      </svg>
                    </div>
                    <p className="text-2xl font-bold text-purple-800">{product.thc_content}%</p>
                  </div>
                )}
                {product.cbd_content !== undefined && (
                  <div className="flex-1 text-center">
                    <div className="flex items-center justify-center gap-1 mb-1">
                      <span className="text-sm text-purple-600 font-medium">CBD</span>
                      <svg className="w-4 h-4 text-purple-500" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C12 2 9 4 9 7C9 7 6 5 3 7C3 7 5 10 5 13C5 13 2 12 0 15C0 15 3 17 6 17C6 17 5 20 7 22C7 22 9 19 12 19C15 19 17 22 17 22C19 20 18 17 18 17C21 17 24 15 24 15C22 12 19 13 19 13C19 10 21 7 21 7C18 5 15 7 15 7C15 4 12 2 12 2Z"/>
                      </svg>
                    </div>
                    <p className="text-2xl font-bold text-purple-800">{product.cbd_content}%</p>
                  </div>
                )}
              </div>
            )}

            {/* Price with decorative style */}
            <div className="flex items-center justify-between p-4 bg-gradient-to-r from-purple-600 to-purple-700 rounded-xl text-white">
              <div>
                <p className="text-3xl font-bold">
                  {formatPrice(product.price)}
                </p>
                {product.size && (
                  <p className="text-sm opacity-90">{product.size}</p>
                )}
              </div>
              
              {/* Stock Status */}
              <div>
                {product.in_stock !== undefined && (
                  <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                    product.in_stock 
                      ? 'bg-green-500 text-white' 
                      : 'bg-red-500 text-white'
                  }`}>
                    {product.in_stock ? '✓ In Stock' : '✗ Out of Stock'}
                  </div>
                )}
              </div>
            </div>

            {/* Description */}
            {product.description && (
              <div className="border-t border-purple-200 pt-4">
                <h3 className="font-semibold text-purple-800 mb-2 flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Description
                </h3>
                <p className="text-gray-700">{product.description}</p>
              </div>
            )}

            {/* Terpenes with cannabis theme */}
            {product.terpenes && product.terpenes.length > 0 && (
              <div className="border-t border-purple-200 pt-4">
                <h3 className="font-semibold text-purple-800 mb-3 flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                  </svg>
                  Terpene Profile
                </h3>
                <div className="flex flex-wrap gap-2">
                  {product.terpenes && Array.isArray(product.terpenes) && product.terpenes.map((terpene, index) => (
                    <span
                      key={index}
                      className="px-3 py-1.5 bg-gradient-to-r from-green-100 to-purple-100 text-purple-700 rounded-lg text-sm font-medium border border-purple-200"
                    >
                      🌿 {terpene}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Quantity and Add to Cart */}
            <div className="flex items-center gap-4 pt-4">
              <QuantitySelector
                quantity={quantity}
                onQuantityChange={setQuantity}
                disabled={!product.in_stock}
              />

              {/* Add to Cart Button with cannabis theme */}
              <button
                onClick={handleAddToCart}
                disabled={isLoading || !product.in_stock}
                className={`flex-1 py-3 px-6 rounded-xl font-bold transition-all transform hover:scale-105 flex items-center justify-center gap-2 shadow-lg ${
                  product.in_stock
                    ? 'bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                {isLoading ? (
                  <>
                    <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Adding...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                    Add to Cart
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Product Recommendations */}
        {showRecommendations && (
          <div className="mt-8 pt-8 border-t border-purple-200">
            <ProductRecommendations
              currentProduct={product}
              onAddToCart={onAddToCart}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default ProductDetails;