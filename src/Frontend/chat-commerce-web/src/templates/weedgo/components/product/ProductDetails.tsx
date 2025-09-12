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
  const [activeTab, setActiveTab] = useState<'details' | 'info'>('details');
  const { addToCart } = useCart();

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(price);
  };

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

  const getStrainTypeColor = (type?: string) => {
    switch (type?.toLowerCase()) {
      case 'indica': return 'border-indigo-500 text-indigo-600 bg-indigo-50';
      case 'sativa': return 'border-emerald-500 text-emerald-600 bg-emerald-50';
      case 'hybrid': return 'border-blue-500 text-blue-600 bg-blue-50';
      case 'cbd': return 'border-blue-500 text-blue-600 bg-amber-50';
      default: return 'border-gray-300 text-gray-600 bg-gray-50';
    }
  };

  const productImages = [
    product.image_url,
    product.thumbnail_url
  ].filter(Boolean);

  return (
    <div className="bg-white rounded-none sm:rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Minimal Header */}
      {onClose && (
        <div className="flex justify-end p-4 border-b border-gray-100">
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-50 rounded-full "
            aria-label="Close"
          >
            <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      <div className="p-4 sm:p-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Product Images - Clean Minimal Style */}
          <div className="space-y-4">
            <div className="aspect-square bg-gray-50 rounded-sm overflow-hidden">
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
                  <svg className="w-16 h-16 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
              )}
            </div>

            {productImages.length > 1 && (
              <div className="flex gap-2">
                {productImages.map((img, index) => img && (
                  <button
                    key={index}
                    onClick={() => setActiveImageIndex(index)}
                    className={`w-20 h-20 rounded-sm overflow-hidden border  ${
                      activeImageIndex === index 
                        ? 'border-blue-500' 
                        : 'border-gray-200 hover:border-gray-300'
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

          {/* Product Information - Clean Typography */}
          <div className="space-y-6">
            {/* Name and Brand */}
            <div>
              <h1 className="text-2xl font-light text-gray-900">{product.name}</h1>
              {product.brand && (
                <p className="text-sm text-gray-500 mt-1 uppercase tracking-wider">{product.brand}</p>
              )}
            </div>

            {/* Price - Prominent but Clean */}
            <div className="py-4 border-y border-gray-100">
              <p className="text-3xl font-light text-gray-900">
                {formatPrice(product.price)}
              </p>
              {product.size && (
                <p className="text-sm text-gray-500 mt-1">{product.size}</p>
              )}
            </div>

            {/* Minimal Badges */}
            <div className="flex flex-wrap gap-2">
              {product.plant_type && (
                <span className={`px-3 py-1 border rounded-full text-xs font-medium ${getStrainTypeColor(product.plant_type)}`}>
                  {product.plant_type}
                </span>
              )}
              {(product.thc_content || product.cbd_content) && (
                <div className="flex gap-4">
                  {product.thc_content !== undefined && (
                    <span className="text-sm text-gray-600">
                      THC <span className="font-medium text-gray-900">{product.thc_content}%</span>
                    </span>
                  )}
                  {product.cbd_content !== undefined && (
                    <span className="text-sm text-gray-600">
                      CBD <span className="font-medium text-gray-900">{product.cbd_content}%</span>
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* Tabs for Details */}
            <div>
              <div className="flex gap-8 border-b border-gray-200">
                <button
                  onClick={() => setActiveTab('details')}
                  className={`pb-2 text-sm font-medium  relative ${
                    activeTab === 'details' 
                      ? 'text-gray-900' 
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Details
                  {activeTab === 'details' && (
                    <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500" />
                  )}
                </button>
                <button
                  onClick={() => setActiveTab('info')}
                  className={`pb-2 text-sm font-medium  relative ${
                    activeTab === 'info' 
                      ? 'text-gray-900' 
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Information
                  {activeTab === 'info' && (
                    <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500" />
                  )}
                </button>
              </div>

              <div className="pt-4">
                {activeTab === 'details' && (
                  <div className="space-y-4">
                    {product.description && (
                      <p className="text-sm text-gray-600 leading-relaxed">
                        {product.description}
                      </p>
                    )}
                    {product.terpenes && product.terpenes.length > 0 && (
                      <div>
                        <p className="text-xs uppercase tracking-wider text-gray-500 mb-2">Terpenes</p>
                        <div className="flex flex-wrap gap-1">
                          {product.terpenes && Array.isArray(product.terpenes) && product.terpenes.map((terpene, index) => (
                            <span
                              key={index}
                              className="px-2 py-1 bg-gray-50 text-gray-600 rounded text-xs"
                            >
                              {terpene}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
                
                {activeTab === 'info' && (
                  <div className="space-y-3">
                    {product.category && (
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Category</span>
                        <span className="text-gray-900">{product.category}</span>
                      </div>
                    )}
                    {product.strain_type && (
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Strain</span>
                        <span className="text-gray-900">{product.strain_type}</span>
                      </div>
                    )}
                    {product.supplier_name && (
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Supplier</span>
                        <span className="text-gray-900">{product.supplier_name}</span>
                      </div>
                    )}
                    {product.sku && (
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-500">SKU</span>
                        <span className="text-gray-900 font-mono text-xs">{product.sku}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Stock Status */}
            {product.in_stock !== undefined && (
              <div className={`text-sm ${product.in_stock ? 'text-green-600' : 'text-red-600'}`}>
                {product.in_stock ? '• Available' : '• Out of Stock'}
              </div>
            )}

            {/* Add to Cart Section */}
            <div className="flex items-center gap-4 pt-4">
              <QuantitySelector
                quantity={quantity}
                onQuantityChange={setQuantity}
                disabled={!product.in_stock}
              />

              <button
                onClick={handleAddToCart}
                disabled={isLoading || !product.in_stock}
                className={`flex-1 py-3 px-6 rounded-sm font-medium  flex items-center justify-center gap-2 ${
                  product.in_stock
                    ? 'bg-gray-900 hover:bg-gray-800 text-white'
                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                }`}
              >
                {isLoading ? (
                  <>
                    <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Processing
                  </>
                ) : (
                  'Add to Cart'
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Recommendations */}
        {showRecommendations && (
          <div className="mt-12 pt-12 border-t border-gray-100">
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