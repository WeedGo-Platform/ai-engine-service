import React, { useState, useEffect } from 'react';
import { Product } from '../../services/productSearch';
import { ProductDetailsProps } from '../../types/product.types';
import { useCart } from '../../contexts/CartContext';
import ProductRecommendations from './ProductRecommendations';
import { useTemplateContext as useTemplate } from '../../contexts/TemplateContext';

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
  const { currentTemplate } = useTemplate();

  // Get template-specific component
  const TemplateProductDetails = currentTemplate?.getComponent('ProductDetails');
  
  // If template has its own implementation, use it
  if (TemplateProductDetails) {
    return (
      <TemplateProductDetails 
        product={product}
        onClose={onClose}
        onAddToCart={onAddToCart}
        showRecommendations={showRecommendations}
      />
    );
  }

  // Format price
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(price);
  };

  // Handle quantity change
  const handleQuantityChange = (delta: number) => {
    setQuantity(prev => Math.max(1, prev + delta));
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

  // Get strain type color
  const getStrainTypeColor = (type?: string) => {
    switch (type?.toLowerCase()) {
      case 'indica': return 'bg-purple-500';
      case 'sativa': return 'bg-green-500';
      case 'hybrid': return 'bg-blue-500';
      case 'cbd': return 'bg-orange-500';
      default: return 'bg-gray-500';
    }
  };

  // Product images (fallback to single image if no gallery)
  const productImages = [
    product.image_url,
    product.thumbnail_url
  ].filter(Boolean);

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header with close button */}
      {onClose && (
        <div className="flex justify-between items-center p-4 border-b">
          <h2 className="text-xl font-semibold">Product Details</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
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
          {/* Product Images */}
          <div className="space-y-4">
            {/* Main Image */}
            <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden">
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
                  <svg className="w-20 h-20 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
              )}
            </div>

            {/* Thumbnail Images */}
            {productImages.length > 1 && (
              <div className="flex gap-2">
                {productImages.map((img, index) => img && (
                  <button
                    key={index}
                    onClick={() => setActiveImageIndex(index)}
                    className={`w-20 h-20 rounded-lg overflow-hidden border-2 transition-colors ${
                      activeImageIndex === index ? 'border-blue-500' : 'border-gray-200'
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

          {/* Product Information */}
          <div className="space-y-4">
            {/* Name and Brand */}
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{product.name}</h1>
              {product.brand && (
                <p className="text-lg text-gray-600">{product.brand}</p>
              )}
            </div>

            {/* Badges */}
            <div className="flex flex-wrap gap-2">
              {product.plant_type && (
                <span className={`px-3 py-1 rounded-full text-white text-sm ${getStrainTypeColor(product.plant_type)}`}>
                  {product.plant_type}
                </span>
              )}
              {product.strain_type && (
                <span className="px-3 py-1 rounded-full bg-gray-200 text-gray-700 text-sm">
                  {product.strain_type}
                </span>
              )}
              {product.category && (
                <span className="px-3 py-1 rounded-full bg-gray-100 text-gray-600 text-sm">
                  {product.category}
                </span>
              )}
            </div>

            {/* THC/CBD Content */}
            {(product.thc_content || product.cbd_content) && (
              <div className="flex gap-4 p-3 bg-gray-50 rounded-lg">
                {product.thc_content !== undefined && (
                  <div>
                    <span className="text-sm text-gray-600">THC</span>
                    <p className="text-lg font-semibold">{product.thc_content}%</p>
                  </div>
                )}
                {product.cbd_content !== undefined && (
                  <div>
                    <span className="text-sm text-gray-600">CBD</span>
                    <p className="text-lg font-semibold">{product.cbd_content}%</p>
                  </div>
                )}
              </div>
            )}

            {/* Price */}
            <div className="flex items-center justify-between">
              <div>
                <p className="text-3xl font-bold text-gray-900">
                  {formatPrice(product.price)}
                </p>
                {product.size && (
                  <p className="text-sm text-gray-600">{product.size}</p>
                )}
              </div>
              
              {/* Stock Status */}
              <div>
                {product.in_stock !== undefined && (
                  <p className={`text-sm font-medium ${product.in_stock ? 'text-green-600' : 'text-red-600'}`}>
                    {product.in_stock ? '✓ In Stock' : '✗ Out of Stock'}
                  </p>
                )}
              </div>
            </div>

            {/* Description */}
            {product.description && (
              <div className="border-t pt-4">
                <h3 className="font-semibold mb-2">Description</h3>
                <p className="text-gray-600">{product.description}</p>
              </div>
            )}

            {/* Terpenes */}
            {product.terpenes && product.terpenes.length > 0 && (
              <div className="border-t pt-4">
                <h3 className="font-semibold mb-2">Terpene Profile</h3>
                <div className="flex flex-wrap gap-2">
                  {product.terpenes && Array.isArray(product.terpenes) && product.terpenes.map((terpene, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 bg-green-100 text-green-700 rounded-lg text-sm"
                    >
                      {terpene}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Additional Info */}
            <div className="border-t pt-4 space-y-2">
              {product.supplier_name && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Supplier</span>
                  <span className="font-medium">{product.supplier_name}</span>
                </div>
              )}
              {product.sku && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">SKU</span>
                  <span className="font-medium">{product.sku}</span>
                </div>
              )}
              {product.sub_category && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Subcategory</span>
                  <span className="font-medium">{product.sub_category}</span>
                </div>
              )}
            </div>

            {/* Quantity and Add to Cart */}
            <div className="flex items-center gap-4 pt-4">
              {/* Quantity Selector */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Quantity:</span>
                <div className="flex items-center border rounded-lg">
                  <button
                    onClick={() => handleQuantityChange(-1)}
                    className="p-2 hover:bg-gray-100 transition-colors"
                    disabled={quantity <= 1}
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                    </svg>
                  </button>
                  <span className="px-4 py-2 min-w-[3rem] text-center font-medium">
                    {quantity}
                  </span>
                  <button
                    onClick={() => handleQuantityChange(1)}
                    className="p-2 hover:bg-gray-100 transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Add to Cart Button */}
              <button
                onClick={handleAddToCart}
                disabled={isLoading || !product.in_stock}
                className={`flex-1 py-3 px-6 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 ${
                  product.in_stock
                    ? 'bg-blue-500 hover:bg-blue-600 text-white'
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
          <div className="mt-8 pt-8 border-t">
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