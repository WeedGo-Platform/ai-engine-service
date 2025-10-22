import React, { useState, useEffect } from 'react';
import { getApiUrl } from '../../config/app.config';
import { Plus, Sparkles } from 'lucide-react';
import { useKiosk } from '../../contexts/KioskContext';
import { formatCurrency } from '../../utils/currency';

interface RecommendedProduct {
  id: string;
  sku: string;
  ocs_variant_number: string;
  product_name: string;
  brand: string;
  retail_price: number;
  image_url: string;
  thc_content: number;
  cbd_content: number;
  category: string;
  subcategory: string;
  plant_type: string;
  quantity_available: number;
  is_featured: boolean;
  is_sale: boolean;
  sale_price?: number;
  rating?: number;
}

interface ProductRecommendationsProps {
  storeId: string;
  sessionId?: string | null;
  onProductClick: (product: any) => void;
}

export default function ProductRecommendations({
  storeId,
  sessionId,
  onProductClick
}: ProductRecommendationsProps) {
  const [recommendations, setRecommendations] = useState<RecommendedProduct[]>([]);
  const [loading, setLoading] = useState(false);
  const { cart, addToCart } = useKiosk();

  useEffect(() => {
    fetchRecommendations();
  }, [cart, storeId]);

  const fetchRecommendations = async () => {
    setLoading(true);
    try {
      const cartItems = cart.map(item => ({
        product_id: item.productId,
        sku: item.sku,
        quantity: item.quantity,
        category: item.category
      }));

      const response = await fetch(getApiUrl('/api/kiosk/products/recommendations'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          store_id: storeId,
          cart_items: cartItems
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setRecommendations(data.recommendations || []);
      }
    } catch (error) {
      console.error('Error fetching recommendations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = (product: RecommendedProduct) => {
    addToCart({
      productId: product.id,
      sku: product.sku || product.ocs_variant_number,
      name: product.product_name,
      price: product.sale_price || product.retail_price,
      quantity: 1,
      image: product.image_url,
      thc: product.thc_content,
      cbd: product.cbd_content,
      category: product.category,
      subcategory: product.subcategory
    });
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="w-5 h-5 text-primary-600" />
          <h3 className="text-lg font-semibold">Loading Recommendations...</h3>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="bg-gray-200 h-40 rounded-lg mb-2"></div>
              <div className="bg-gray-200 h-4 rounded w-3/4 mb-1"></div>
              <div className="bg-gray-200 h-4 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (recommendations.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center gap-2 mb-4">
        <Sparkles className="w-5 h-5 text-primary-600" />
        <h3 className="text-lg font-semibold">Recommended for You</h3>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {recommendations.slice(0, 6).map((product) => (
          <div
            key={product.id}
            className="border rounded-lg overflow-hidden hover:shadow-lg transition-shadow cursor-pointer"
            onClick={() => onProductClick(product)}
          >
            <div className="relative">
              <img
                src={product.image_url || '/placeholder-product.jpg'}
                alt={product.product_name}
                className="w-full h-32 object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = '/placeholder-product.jpg';
                }}
              />
              {product.is_sale && product.sale_price && (
                <span className="absolute top-2 right-2 px-2 py-1 bg-red-500 text-white text-xs rounded-full">
                  Sale
                </span>
              )}
              {product.quantity_available === 0 && (
                <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
                  <span className="text-white font-semibold">Out of Stock</span>
                </div>
              )}
            </div>

            <div className="p-3">
              <h4 className="font-medium text-sm line-clamp-1">{product.product_name}</h4>
              <p className="text-xs text-gray-500">{product.brand}</p>

              <div className="flex gap-1 mt-1">
                {product.thc_content > 0 && (
                  <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded">
                    THC {product.thc_content}%
                  </span>
                )}
                {product.cbd_content > 0 && (
                  <span className="text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">
                    CBD {product.cbd_content}%
                  </span>
                )}
              </div>

              <div className="flex items-center justify-between mt-2">
                <div>
                  {product.is_sale && product.sale_price ? (
                    <>
                      <span className="text-sm font-semibold text-red-600">
                        {formatCurrency(product.sale_price)}
                      </span>
                      <span className="text-xs text-gray-500 line-through ml-1">
                        {formatCurrency(product.retail_price)}
                      </span>
                    </>
                  ) : (
                    <span className="text-sm font-semibold text-primary-600">
                      {formatCurrency(product.retail_price)}
                    </span>
                  )}
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleAddToCart(product);
                  }}
                  disabled={product.quantity_available === 0}
                  className="p-1.5 bg-primary-600 text-white rounded hover:bg-primary-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}