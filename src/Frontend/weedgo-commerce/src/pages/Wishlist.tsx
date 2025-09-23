/**
 * Wishlist page component
 */

import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Link, useNavigate } from 'react-router-dom';
import { HeartIcon, ShoppingCartIcon, TrashIcon } from '@heroicons/react/24/outline';
import {
  fetchWishlist,
  removeFromWishlist,
  moveToCart,
  clearWishlist,
  selectWishlistItems,
  selectWishlistTotal,
  selectWishlistLoading,
} from '@features/wishlist/wishlistSlice';
import { selectIsAuthenticated } from '@features/auth/authSlice';
import { AccessibleButton } from '@components/common/AccessibleComponents';
import WishlistButton from '@components/wishlist/WishlistButton';
import toast from 'react-hot-toast';

const Wishlist: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const isAuthenticated = useSelector(selectIsAuthenticated);
  const items = useSelector(selectWishlistItems);
  const total = useSelector(selectWishlistTotal);
  const { isLoading, isRemoving } = useSelector(selectWishlistLoading);

  useEffect(() => {
    if (!isAuthenticated) {
      toast('Please login to view your wishlist', { icon: '🔒' });
      navigate('/login?redirect=/wishlist');
      return;
    }

    // Fetch wishlist on mount
    dispatch(fetchWishlist() as any);
  }, [dispatch, isAuthenticated, navigate]);

  const handleRemove = (productId: string) => {
    dispatch(removeFromWishlist(productId) as any);
  };

  const handleMoveToCart = (productId: string) => {
    dispatch(moveToCart(productId) as any);
  };

  const handleClearWishlist = () => {
    if (window.confirm('Are you sure you want to clear your entire wishlist?')) {
      dispatch(clearWishlist() as any);
    }
  };

  const renderEmptyWishlist = () => (
    <div className="text-center py-16">
      <HeartIcon className="mx-auto h-16 w-16 text-gray-400" aria-hidden="true" />
      <h3 className="mt-4 text-lg font-medium text-gray-900">Your wishlist is empty</h3>
      <p className="mt-2 text-sm text-gray-500">
        Save your favorite products to buy them later
      </p>
      <Link to="/products">
        <AccessibleButton variant="primary" className="mt-6">
          Browse Products
        </AccessibleButton>
      </Link>
    </div>
  );

  const renderWishlistItem = (item: any) => {
    const product = item.product;
    const productImage = product.images?.[0] || '/placeholder.png';

    return (
      <div
        key={item.id}
        className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow"
      >
        <Link to={`/products/${product.sku}`} className="block">
          <div className="aspect-w-1 aspect-h-1 bg-gray-200">
            <img
              src={productImage}
              alt={product.name}
              className="object-cover object-center w-full h-48"
              loading="lazy"
            />
            {!product.inStock && (
              <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
                <span className="text-white font-medium">Out of Stock</span>
              </div>
            )}
          </div>
        </Link>

        <div className="p-4">
          <Link to={`/products/${product.sku}`}>
            <h3 className="text-lg font-medium text-gray-900 hover:text-green-600 transition-colors">
              {product.name}
            </h3>
          </Link>

          <div className="mt-2 flex items-center justify-between">
            <div>
              {product.brand && (
                <p className="text-sm text-gray-500">{product.brand}</p>
              )}
              {product.strain && (
                <p className="text-xs text-gray-500">{product.strain}</p>
              )}
            </div>
            <p className="text-lg font-semibold text-green-600">
              ${product.price.toFixed(2)}
            </p>
          </div>

          {/* THC/CBD Content */}
          {(product.thc || product.cbd) && (
            <div className="mt-2 flex gap-2 text-xs">
              {product.thc && (
                <span className="bg-orange-100 text-orange-800 px-2 py-1 rounded">
                  THC: {product.thc}%
                </span>
              )}
              {product.cbd && (
                <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded">
                  CBD: {product.cbd}%
                </span>
              )}
            </div>
          )}

          {/* Rating */}
          {product.rating && (
            <div className="mt-2 flex items-center text-sm">
              <div className="flex items-center">
                {[...Array(5)].map((_, i) => (
                  <svg
                    key={i}
                    className={`h-4 w-4 ${
                      i < Math.floor(product.rating)
                        ? 'text-yellow-400'
                        : 'text-gray-300'
                    }`}
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                ))}
              </div>
              <span className="ml-1 text-gray-600">
                ({product.reviewCount || 0})
              </span>
            </div>
          )}

          {/* Actions */}
          <div className="mt-4 flex gap-2">
            <AccessibleButton
              onClick={() => handleMoveToCart(product.id)}
              variant="primary"
              size="sm"
              fullWidth
              disabled={!product.inStock || isRemoving}
              aria-label={`Add ${product.name} to cart`}
            >
              <ShoppingCartIcon className="h-4 w-4 mr-1" aria-hidden="true" />
              Add to Cart
            </AccessibleButton>
            <button
              onClick={() => handleRemove(product.id)}
              className="p-2 text-gray-400 hover:text-red-500 transition-colors"
              aria-label={`Remove ${product.name} from wishlist`}
              disabled={isRemoving}
            >
              <TrashIcon className="h-5 w-5" aria-hidden="true" />
            </button>
          </div>

          {/* Added Date */}
          <p className="mt-2 text-xs text-gray-500">
            Added {new Date(item.addedAt).toLocaleDateString()}
          </p>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">My Wishlist</h1>
            <p className="mt-1 text-sm text-gray-500">
              {total} {total === 1 ? 'item' : 'items'} saved
            </p>
          </div>

          {total > 0 && (
            <AccessibleButton
              onClick={handleClearWishlist}
              variant="secondary"
              size="sm"
              disabled={isLoading}
            >
              Clear Wishlist
            </AccessibleButton>
          )}
        </div>

        {/* Content */}
        {isLoading && items.length === 0 ? (
          <div className="flex justify-center py-16">
            <div className="text-center">
              <svg
                className="animate-spin h-8 w-8 text-gray-600 mx-auto"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              <p className="mt-2 text-gray-600">Loading your wishlist...</p>
            </div>
          </div>
        ) : items.length === 0 ? (
          renderEmptyWishlist()
        ) : (
          <>
            {/* Wishlist Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {items.map(renderWishlistItem)}
            </div>

            {/* Summary Actions */}
            <div className="mt-12 bg-white rounded-lg shadow p-6">
              <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
                <div className="text-center sm:text-left">
                  <h3 className="text-lg font-medium text-gray-900">
                    Ready to purchase?
                  </h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Move items to your cart to complete your order
                  </p>
                </div>

                <div className="flex gap-4">
                  <Link to="/products">
                    <AccessibleButton variant="secondary">
                      Continue Shopping
                    </AccessibleButton>
                  </Link>
                  <Link to="/cart">
                    <AccessibleButton variant="primary">
                      <ShoppingCartIcon className="h-5 w-5 mr-2" aria-hidden="true" />
                      View Cart
                    </AccessibleButton>
                  </Link>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default Wishlist;