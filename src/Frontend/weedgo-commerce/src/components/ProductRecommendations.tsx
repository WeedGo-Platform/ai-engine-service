import React from 'react';
import { Link } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { ShoppingCartIcon, EyeIcon, ArrowTrendingUpIcon } from '@heroicons/react/24/outline';
import { RecommendedProduct } from '@/api/recommendations';
import { addItem } from '@/features/cart/cartSlice';
import toast from 'react-hot-toast';

interface ProductRecommendationsProps {
  title: string;
  products: RecommendedProduct[];
  loading?: boolean;
  className?: string;
}

export const ProductRecommendations: React.FC<ProductRecommendationsProps> = ({
  title,
  products,
  loading = false,
  className = ''
}) => {
  const dispatch = useDispatch();

  const handleAddToCart = (product: RecommendedProduct) => {
    dispatch(addItem({
      id: product.product_id,
      sku: product.product_id,
      name: product.product_name,
      price: product.unit_price,
      quantity: 1,
      image: product.image_url || '/placeholder-product.png',
      brand: product.brand,
      category: product.category,
      thc: product.thc_percentage || 0,
      cbd: product.cbd_percentage || 0,
      maxQuantity: 99
    }));

    toast.success('Added to cart!');
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-CA', {
      style: 'currency',
      currency: 'CAD'
    }).format(price);
  };

  const getProductUrl = (product: RecommendedProduct) => {
    const slug = product.product_name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
    return `/dispensary-near-me/toronto/${slug}`;
  };

  if (loading) {
    return (
      <div className={`recommendations-section ${className}`}>
        <h3 className="text-xl font-bold mb-4">{title}</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="bg-gray-200 h-48 rounded-lg mb-2"></div>
              <div className="bg-gray-200 h-4 rounded w-3/4 mb-2"></div>
              <div className="bg-gray-200 h-4 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!products || products.length === 0) {
    return null;
  }

  return (
    <div className={`recommendations-section ${className}`}>
      <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
        <ArrowTrendingUpIcon className="w-5 h-5" />
        {title}
      </h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
        {products.slice(0, 10).map((product) => (
          <div
            key={product.product_id}
            className="group bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow p-3"
          >
            <Link to={getProductUrl(product)} className="block">
              <div className="relative aspect-square mb-2 overflow-hidden rounded-md">
                <img
                  src={product.image_url || '/placeholder-product.png'}
                  alt={product.product_name}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = '/placeholder-product.png';
                  }}
                />
                {product.score && product.score > 0.7 && (
                  <div className="absolute top-2 right-2 bg-green-500 text-white text-xs px-2 py-1 rounded">
                    Top Match
                  </div>
                )}
              </div>
            </Link>

            <div className="space-y-1">
              <Link to={getProductUrl(product)}>
                <p className="text-xs text-gray-500">{product.brand}</p>
                <h4 className="font-medium text-sm line-clamp-2 hover:text-blue-600">
                  {product.product_name}
                </h4>
              </Link>

              <div className="flex flex-wrap gap-2 text-xs">
                {product.thc_percentage && (
                  <span className="bg-orange-100 text-orange-700 px-2 py-0.5 rounded">
                    THC {product.thc_percentage}%
                  </span>
                )}
                {product.cbd_percentage && product.cbd_percentage > 0 && (
                  <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                    CBD {product.cbd_percentage}%
                  </span>
                )}
                {product.strain_type && (
                  <span className="bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                    {product.strain_type}
                  </span>
                )}
              </div>

              <div className="flex items-center justify-between mt-2">
                <span className="font-bold text-lg">
                  {formatPrice(product.unit_price)}
                </span>
                <div className="flex gap-1">
                  <Link
                    to={getProductUrl(product)}
                    className="p-1.5 bg-gray-100 hover:bg-gray-200 rounded transition-colors"
                    title="View Details"
                  >
                    <EyeIcon className="w-4 h-4" />
                  </Link>
                  <button
                    onClick={() => handleAddToCart(product)}
                    className="p-1.5 bg-green-500 hover:bg-green-600 text-white rounded transition-colors"
                    title="Add to Cart"
                  >
                    <ShoppingCartIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};