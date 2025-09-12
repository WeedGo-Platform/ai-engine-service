import React, { useState } from 'react';
import { Product } from '../../../../services/productSearch';
import { ProductDetailsProps } from '../../../../types/product.types';
import { useCart } from '../../../../contexts/CartContext';
import ProductRecommendations from './ProductRecommendations';
import QuantitySelector from './QuantitySelector';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import Card from '../ui/Card';

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
      case 'indica': return 'primary';
      case 'sativa': return 'success';
      case 'hybrid': return 'warning';
      case 'cbd': return 'info';
      default: return 'default';
    }
  };

  const productImages = [
    product.image_url,
    product.thumbnail_url
  ].filter(Boolean);

  return (
    <div className="bg-white rounded-xl shadow-xl overflow-hidden">
      {/* Header */}
      {onClose && (
        <div className="flex justify-between items-center p-4 bg-gradient-to-r from-red-500 to-red-600 text-white">
          <h2 className="text-xl font-bold">Product Details</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/20 rounded-lg transition-colors"
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
            <div className="aspect-square bg-gray-50 rounded-lg overflow-hidden">
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

            {/* Thumbnails */}
            {productImages.length > 1 && (
              <div className="flex gap-2">
                {productImages.map((img, index) => img && (
                  <button
                    key={index}
                    onClick={() => setActiveImageIndex(index)}
                    className={`w-20 h-20 rounded-lg overflow-hidden border-2 transition-all ${
                      activeImageIndex === index 
                        ? 'border-red-500 shadow-lg' 
                        : 'border-gray-200 hover:border-gray-400'
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
              <h1 className="text-3xl font-bold text-gray-900">{product.name}</h1>
              {product.brand && (
                <p className="text-lg text-gray-600 font-medium">{product.brand}</p>
              )}
            </div>

            {/* Badges */}
            <div className="flex flex-wrap gap-2">
              {product.plant_type && (
                <Badge variant={getStrainTypeColor(product.plant_type) as any} size="lg">
                  {product.plant_type}
                </Badge>
              )}
              {product.strain_type && (
                <Badge variant="default" size="lg">
                  {product.strain_type}
                </Badge>
              )}
              {product.category && (
                <Badge variant="default" size="lg">
                  {product.category}
                </Badge>
              )}
            </div>

            {/* THC/CBD Content */}
            {(product.thc_content || product.cbd_content) && (
              <Card className="bg-gray-50" padding="sm">
                <div className="flex gap-4">
                  {product.thc_content !== undefined && (
                    <div className="flex-1 text-center">
                      <span className="text-sm text-gray-600 font-medium">THC</span>
                      <p className="text-2xl font-bold text-gray-900">{product.thc_content}%</p>
                    </div>
                  )}
                  {product.cbd_content !== undefined && (
                    <div className="flex-1 text-center">
                      <span className="text-sm text-gray-600 font-medium">CBD</span>
                      <p className="text-2xl font-bold text-gray-900">{product.cbd_content}%</p>
                    </div>
                  )}
                </div>
              </Card>
            )}

            {/* Price */}
            <div className="flex items-center justify-between p-4 bg-gradient-to-r from-red-500 to-red-600 rounded-lg text-white">
              <div>
                <p className="text-3xl font-bold">
                  {formatPrice(product.price)}
                </p>
                {product.size && (
                  <p className="text-sm opacity-90">{product.size}</p>
                )}
              </div>
              
              {/* Stock Status */}
              {product.in_stock !== undefined && (
                <Badge variant={product.in_stock ? 'success' : 'danger'} size="lg">
                  {product.in_stock ? 'In Stock' : 'Out of Stock'}
                </Badge>
              )}
            </div>

            {/* Description */}
            {product.description && (
              <div className="border-t pt-4">
                <h3 className="font-semibold text-gray-900 mb-2">Description</h3>
                <p className="text-gray-700">{product.description}</p>
              </div>
            )}

            {/* Terpenes */}
            {product.terpenes && product.terpenes.length > 0 && (
              <div className="border-t pt-4">
                <h3 className="font-semibold text-gray-900 mb-3">Terpene Profile</h3>
                <div className="flex flex-wrap gap-2">
                  {product.terpenes && Array.isArray(product.terpenes) && product.terpenes.map((terpene, index) => (
                    <Badge key={index} variant="success" rounded>
                      {terpene}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Add to Cart */}
            <div className="flex items-center gap-4 pt-4">
              <QuantitySelector
                quantity={quantity}
                onQuantityChange={setQuantity}
                disabled={!product.in_stock}
              />

              <Button
                onClick={handleAddToCart}
                disabled={isLoading || !product.in_stock}
                variant="primary"
                size="lg"
                loading={isLoading}
                fullWidth
              >
                Add to Cart
              </Button>
            </div>
          </div>
        </div>

        {/* Recommendations */}
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