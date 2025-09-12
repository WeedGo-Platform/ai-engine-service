import React, { useState, useEffect } from 'react';
import { Product } from '../../../../services/productSearch';
import { ProductRecommendationsProps } from '../../../../types/product.types';
import Card from '../ui/Card';
import Button from '../ui/Button';
import Badge from '../ui/Badge';

const ProductRecommendations: React.FC<ProductRecommendationsProps> = ({
  currentProduct,
  onProductSelect,
  onAddToCart,
  maxRecommendations = 4,
}) => {
  const [recommendations, setRecommendations] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    fetchRecommendations();
  }, [currentProduct]);

  const fetchRecommendations = async () => {
    setIsLoading(true);
    // Simulated recommendations - in real app, this would call an API
    setTimeout(() => {
      const mockRecommendations: Product[] = [
        {
          id: '1',
          name: 'Similar Strain 1',
          description: 'A similar product you might like',
          price: currentProduct.price * 0.9,
          category: currentProduct.category,
          plant_type: currentProduct.plant_type,
          thc_content: currentProduct.thc_content,
          in_stock: true,
        },
        {
          id: '2',
          name: 'Similar Strain 2',
          description: 'Another great option',
          price: currentProduct.price * 1.1,
          category: currentProduct.category,
          plant_type: currentProduct.plant_type,
          cbd_content: 5,
          in_stock: true,
        },
      ] as Product[];
      
      setRecommendations(mockRecommendations.slice(0, maxRecommendations));
      setIsLoading(false);
    }, 1000);
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(price);
  };

  if (isLoading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin h-8 w-8 border-2 border-red-500 border-t-transparent rounded-full mx-auto"></div>
        <p className="mt-2 text-gray-600">Finding recommendations...</p>
      </div>
    );
  }

  if (recommendations.length === 0) {
    return null;
  }

  return (
    <div>
      <h3 className="text-xl font-bold text-gray-900 mb-4">You Might Also Like</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {recommendations.map((product) => (
          <Card
            key={product.id}
            hoverable
            onClick={() => onProductSelect?.(product)}
            className="cursor-pointer"
          >
            <div className="aspect-square bg-gray-100 rounded-lg mb-3 overflow-hidden">
              {product.image_url ? (
                <img
                  src={product.image_url}
                  alt={product.name}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = '/placeholder-product.png';
                  }}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <svg className="w-12 h-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
              )}
            </div>
            
            <h4 className="font-semibold text-gray-900 mb-1">{product.name}</h4>
            
            <div className="flex flex-wrap gap-1 mb-2">
              {product.plant_type && (
                <Badge variant="primary" size="sm">
                  {product.plant_type}
                </Badge>
              )}
              {product.thc_content && (
                <Badge variant="default" size="sm">
                  THC {product.thc_content}%
                </Badge>
              )}
            </div>
            
            <p className="text-lg font-bold text-red-600 mb-3">
              {formatPrice(product.price)}
            </p>
            
            {onAddToCart && (
              <Button
                variant="secondary"
                size="sm"
                fullWidth
                onClick={(e) => {
                  e.stopPropagation();
                  onAddToCart(product, 1);
                }}
                disabled={!product.in_stock}
              >
                {product.in_stock ? 'Quick Add' : 'Out of Stock'}
              </Button>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
};

export default ProductRecommendations;