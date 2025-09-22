import React from 'react';
import { Leaf } from 'lucide-react';

interface ProductProps {
  product: {
    id: string;
    product_name: string;
    brand?: string;
    image_url?: string;
    thc_content?: number;
    cbd_content?: number;
    plant_type?: string;
    strain_type?: string;
    size?: string;
    retail_price: number;
    sale_price?: number;
    is_sale?: boolean;
    quantity_available: number;
  };
}

export default function MenuProductCard({ product }: ProductProps) {
  // Determine plant type color and label
  const getPlantTypeBadge = () => {
    const type = (product.plant_type || product.strain_type || '').toLowerCase();
    if (type.includes('sativa')) {
      return { color: 'bg-orange-500', label: 'Sativa' };
    }
    if (type.includes('indica')) {
      return { color: 'bg-purple-500', label: 'Indica' };
    }
    if (type.includes('hybrid')) {
      return { color: 'bg-green-500', label: 'Hybrid' };
    }
    if (type.includes('cbd')) {
      return { color: 'bg-blue-500', label: 'CBD' };
    }
    return null;
  };

  const plantType = getPlantTypeBadge();
  const displayPrice = product.is_sale && product.sale_price
    ? product.sale_price
    : product.retail_price;

  return (
    <div className="bg-gray-900 rounded-lg p-3 border border-gray-700 hover:border-gray-600 transition-colors">
      <div className="flex gap-3">
        {/* Product Image */}
        <div className="w-16 h-16 flex-shrink-0 bg-gray-800 rounded-lg overflow-hidden">
          {product.image_url ? (
            <img
              src={product.image_url}
              alt={product.product_name}
              className="w-full h-full object-cover"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = 'none';
                (e.target as HTMLImageElement).nextElementSibling?.classList.remove('hidden');
              }}
            />
          ) : null}
          <div className={`w-full h-full flex items-center justify-center ${product.image_url ? 'hidden' : ''}`}>
            <Leaf className="w-8 h-8 text-gray-600" />
          </div>
        </div>

        {/* Product Info */}
        <div className="flex-1 min-w-0">
          {/* Name and Brand */}
          <h4 className="text-sm font-semibold text-white truncate">
            {product.product_name}
          </h4>
          {product.brand && (
            <p className="text-xs text-gray-400 truncate">{product.brand}</p>
          )}

          {/* THC/CBD and Size Row */}
          <div className="flex items-center gap-2 mt-1">
            {/* THC Badge */}
            {product.thc_content !== undefined && product.thc_content > 0 && (
              <span className="text-xs bg-green-900 text-green-300 px-1.5 py-0.5 rounded">
                THC {product.thc_content.toFixed(1)}%
              </span>
            )}

            {/* CBD Badge */}
            {product.cbd_content !== undefined && product.cbd_content > 0 && (
              <span className="text-xs bg-blue-900 text-blue-300 px-1.5 py-0.5 rounded">
                CBD {product.cbd_content.toFixed(1)}%
              </span>
            )}

            {/* Size */}
            {product.size && (
              <span className="text-xs text-gray-500">
                {product.size}
              </span>
            )}
          </div>

          {/* Price and Plant Type Row */}
          <div className="flex items-center justify-between mt-1">
            {/* Price */}
            <div className="flex items-baseline gap-1">
              {product.is_sale && product.sale_price ? (
                <>
                  <span className="text-sm font-bold text-red-400">
                    ${displayPrice.toFixed(2)}
                  </span>
                  <span className="text-xs text-gray-500 line-through">
                    ${product.retail_price.toFixed(2)}
                  </span>
                </>
              ) : (
                <span className="text-sm font-bold text-white">
                  ${displayPrice.toFixed(2)}
                </span>
              )}
            </div>

            {/* Plant Type Badge */}
            {plantType && (
              <span className={`text-xs ${plantType.color} px-1.5 py-0.5 rounded text-white font-medium`}>
                {plantType.label}
              </span>
            )}
          </div>

          {/* Out of Stock Indicator */}
          {product.quantity_available === 0 && (
            <div className="mt-1">
              <span className="text-xs bg-red-900 text-red-300 px-1.5 py-0.5 rounded">
                Out of Stock
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}