import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { ShoppingCartIcon, HeartIcon, ShareIcon } from '@heroicons/react/24/outline';
import { HeartIcon as HeartSolidIcon } from '@heroicons/react/24/solid';
import { productsApi, Product } from '@api/products';
import { addItem } from '@features/cart/cartSlice';
import { RootState } from '@store/index';
import toast from 'react-hot-toast';

const ProductDetail: React.FC = () => {
  const { sku } = useParams<{ sku: string }>();
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [isWishlisted, setIsWishlisted] = useState(false);
  const [selectedImage, setSelectedImage] = useState(0);

  const { selectedStore } = useSelector((state: RootState) => state.store || {});

  useEffect(() => {
    loadProduct();
  }, [sku]);

  const loadProduct = async () => {
    if (!sku) return;

    setLoading(true);
    try {
      const data = await productsApi.getProduct(sku);
      if (data) {
        setProduct(data);
      } else {
        toast.error('Product not found');
        navigate('/products');
      }
    } catch (error) {
      console.error('Failed to load product:', error);
      toast.error('Failed to load product details');
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = () => {
    if (!product) return;

    if (!product.in_stock) {
      toast.error('Product is out of stock');
      return;
    }

    if (quantity > product.available_quantity) {
      toast.error(`Only ${product.available_quantity} available`);
      return;
    }

    dispatch(addItem({
      id: product.id,
      sku: product.sku,
      name: product.name,
      price: product.price,
      quantity,
      image: product.image_url,
      thc: product.thc_content,
      cbd: product.cbd_content,
      brand: product.brand,
      category: product.category,
      maxQuantity: product.available_quantity
    }));

    toast.success('Added to cart!');
  };

  const handleQuantityChange = (value: number) => {
    if (!product) return;
    const newQty = Math.max(1, Math.min(value, product.available_quantity));
    setQuantity(newQty);
  };

  const toggleWishlist = () => {
    setIsWishlisted(!isWishlisted);
    toast.success(isWishlisted ? 'Removed from wishlist' : 'Added to wishlist');
  };

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: product?.name,
          text: `Check out ${product?.name} on WeedGo`,
          url: window.location.href,
        });
      } catch (err) {
        console.log('Share failed:', err);
      }
    } else {
      navigator.clipboard.writeText(window.location.href);
      toast.success('Link copied to clipboard!');
    }
  };

  if (loading) {
    return (
      <div className="container-max py-8">
        <div className="animate-pulse">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="aspect-square bg-gray-200 rounded-lg"></div>
            <div className="space-y-4">
              <div className="h-8 bg-gray-200 rounded w-3/4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              <div className="h-6 bg-gray-200 rounded w-1/4"></div>
              <div className="h-32 bg-gray-200 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="container-max py-8">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900">Product not found</h2>
          <button
            onClick={() => navigate('/products')}
            className="mt-4 btn-primary"
          >
            Browse Products
          </button>
        </div>
      </div>
    );
  }

  // Parse batches if it's a JSON string
  let batches = [];
  try {
    if (product.batches && typeof product.batches === 'string') {
      batches = JSON.parse(product.batches);
    }
  } catch (e) {
    console.error('Failed to parse batches:', e);
  }

  return (
    <div className="container-max py-8">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Product Images */}
        <div className="space-y-4">
          <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden">
            <img
              src={product.image_url}
              alt={product.name}
              className="w-full h-full object-contain"
              onError={(e) => {
                (e.target as HTMLImageElement).src = '/placeholder-product.png';
              }}
            />
          </div>
        </div>

        {/* Product Info */}
        <div className="space-y-6">
          {/* Header */}
          <div>
            <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
              <span>{product.category}</span>
              {product.sub_category && (
                <>
                  <span>•</span>
                  <span>{product.sub_category}</span>
                </>
              )}
            </div>

            <h1 className="text-3xl font-bold text-gray-900">{product.name}</h1>

            <div className="flex items-center gap-4 mt-2">
              <span className="text-lg text-gray-600">by {product.brand}</span>
              {product.plant_type && (
                <span className="px-2 py-1 bg-green-100 text-green-800 text-sm rounded-full">
                  {product.plant_type}
                </span>
              )}
            </div>
          </div>

          {/* Price and Stock */}
          <div className="border-t border-b py-4">
            <div className="flex items-center justify-between mb-2">
              <div>
                <span className="text-3xl font-bold text-gray-900">
                  ${product.price.toFixed(2)}
                </span>
                {product.unit_price && (
                  <span className="text-sm text-gray-500 ml-2">
                    (${product.unit_price.toFixed(2)}/g)
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={toggleWishlist}
                  className="p-2 rounded-lg hover:bg-gray-100"
                >
                  {isWishlisted ? (
                    <HeartSolidIcon className="w-6 h-6 text-red-500" />
                  ) : (
                    <HeartIcon className="w-6 h-6 text-gray-400" />
                  )}
                </button>
                <button
                  onClick={handleShare}
                  className="p-2 rounded-lg hover:bg-gray-100"
                >
                  <ShareIcon className="w-6 h-6 text-gray-400" />
                </button>
              </div>
            </div>

            {/* Stock Status */}
            <div className="flex items-center gap-2">
              {product.in_stock ? (
                <>
                  <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                  <span className="text-green-600 text-sm">
                    In Stock ({product.available_quantity} available)
                  </span>
                </>
              ) : (
                <>
                  <span className="w-2 h-2 bg-red-500 rounded-full"></span>
                  <span className="text-red-600 text-sm">Out of Stock</span>
                </>
              )}
            </div>
          </div>

          {/* THC/CBD Content */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="text-sm text-purple-600">THC</div>
              <div className="text-2xl font-bold text-purple-900">
                {product.thc_content.toFixed(1)}%
              </div>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-sm text-blue-600">CBD</div>
              <div className="text-2xl font-bold text-blue-900">
                {product.cbd_content.toFixed(1)}%
              </div>
            </div>
          </div>

          {/* Add to Cart */}
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <label className="text-sm font-medium text-gray-700">Quantity:</label>
              <div className="flex items-center border rounded-lg">
                <button
                  onClick={() => handleQuantityChange(quantity - 1)}
                  className="px-3 py-2 hover:bg-gray-100"
                  disabled={quantity <= 1}
                >
                  -
                </button>
                <input
                  type="number"
                  value={quantity}
                  onChange={(e) => handleQuantityChange(parseInt(e.target.value) || 1)}
                  className="w-16 text-center border-x py-2"
                  min="1"
                  max={product.available_quantity}
                />
                <button
                  onClick={() => handleQuantityChange(quantity + 1)}
                  className="px-3 py-2 hover:bg-gray-100"
                  disabled={quantity >= product.available_quantity}
                >
                  +
                </button>
              </div>
            </div>

            <button
              onClick={handleAddToCart}
              disabled={!product.in_stock}
              className={`w-full flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-semibold transition-colors ${
                product.in_stock
                  ? 'bg-green-600 text-white hover:bg-green-700'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              <ShoppingCartIcon className="w-5 h-5" />
              {product.in_stock ? 'Add to Cart' : 'Out of Stock'}
            </button>
          </div>

          {/* Product Details */}
          <div className="space-y-4 pt-4 border-t">
            <h3 className="font-semibold text-lg">Product Details</h3>

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">SKU</span>
                <span className="font-medium">{product.sku}</span>
              </div>
              {product.gtin && (
                <div className="flex justify-between">
                  <span className="text-gray-600">GTIN</span>
                  <span className="font-medium">{product.gtin}</span>
                </div>
              )}
              {product.size && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Package Size</span>
                  <span className="font-medium">{product.size}g</span>
                </div>
              )}
              {batches.length > 0 && batches[0].batch_lot && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Batch</span>
                  <span className="font-medium">{batches[0].batch_lot}</span>
                </div>
              )}
              {batches.length > 0 && batches[0].packaged_on_date && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Packaged On</span>
                  <span className="font-medium">
                    {new Date(batches[0].packaged_on_date).toLocaleDateString()}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Description */}
          {product.description && (
            <div className="space-y-2 pt-4 border-t">
              <h3 className="font-semibold text-lg">Description</h3>
              <p className="text-gray-600">{product.description}</p>
            </div>
          )}

          {/* Store Info */}
          {selectedStore && (
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Available at</div>
              <div className="font-medium">{selectedStore.name}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProductDetail;