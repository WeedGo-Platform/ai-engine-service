import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate, Link } from 'react-router-dom';
import { TrashIcon, MinusIcon, PlusIcon } from '@heroicons/react/24/outline';
import { RootState } from '@store/index';
import { removeItem, updateQuantity, clearCart } from '@features/cart/cartSlice';
import { promotionsAPI } from '@api/promotions';
import { recommendationsApi } from '@api/recommendations';
import { ProductRecommendations } from '@components/ProductRecommendations';
import toast from 'react-hot-toast';

const Cart: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [promoCode, setPromoCode] = useState('');
  const [discount, setDiscount] = useState(0);
  const [trendingProducts, setTrendingProducts] = useState<any[]>([]);
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);

  const { items, total } = useSelector((state: RootState) => state.cart);
  const { selectedStore } = useSelector((state: RootState) => state.store || {});
  const { isAuthenticated } = useSelector((state: RootState) => state.auth);

  const TAX_RATE = 0.13; // 13% HST in Ontario
  const DELIVERY_FEE = 5.99;
  const FREE_DELIVERY_THRESHOLD = 50;

  const subtotal = items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  const tax = subtotal * TAX_RATE;
  const deliveryFee = subtotal >= FREE_DELIVERY_THRESHOLD ? 0 : DELIVERY_FEE;
  const discountAmount = subtotal * discount;
  const finalTotal = subtotal + tax + deliveryFee - discountAmount;

  // Fetch trending products to show as recommendations
  useEffect(() => {
    const fetchRecommendations = async () => {
      if (items.length > 0) {
        setLoadingRecommendations(true);
        try {
          const trending = await recommendationsApi.getTrendingProducts(undefined, 10);
          setTrendingProducts(trending);
        } catch (error) {
          console.error('Error fetching recommendations:', error);
        } finally {
          setLoadingRecommendations(false);
        }
      }
    };

    fetchRecommendations();
  }, [items]);

  const handleUpdateQuantity = (id: string, newQuantity: number) => {
    if (newQuantity < 1) {
      handleRemoveItem(id);
      return;
    }
    dispatch(updateQuantity({ itemId: id, quantity: newQuantity }));
    toast.success('Cart updated');
  };

  const handleRemoveItem = (id: string) => {
    dispatch(removeItem(id));
    toast.success('Item removed from cart');
  };

  const handleClearCart = () => {
    if (window.confirm('Are you sure you want to clear your cart?')) {
      dispatch(clearCart());
      toast.success('Cart cleared');
    }
  };

  const handleApplyPromo = async () => {
    if (!promoCode.trim()) {
      toast.error('Please enter a promo code');
      return;
    }

    const result = await promotionsAPI.validatePromoCode(promoCode, subtotal);

    if (result.valid && result.discount) {
      setDiscount(result.discount / 100); // Convert percentage to decimal
      toast.success(result.message || `Promo code applied! ${result.discount}% off`);
    } else {
      toast.error(result.message || 'Invalid promo code');
      setDiscount(0);
    }
  };

  const handleCheckout = () => {
    if (!isAuthenticated) {
      toast('Please login to checkout', {
        icon: '🔒',
      });
      navigate('/login?redirect=/checkout');
      return;
    }

    navigate('/checkout');
  };

  if (items.length === 0) {
    return (
      <div className="container-max py-16">
        <div className="text-center">
          <div className="mb-8">
            <svg
              className="mx-auto h-24 w-24 text-gray-300"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1}
                d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17M17 13l2.293 2.293c.63.63.184 1.707-.707 1.707H5.414M17 21a2 2 0 100-4 2 2 0 000 4zM9 21a2 2 0 100-4 2 2 0 000 4z"
              />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Your cart is empty</h2>
          <p className="text-gray-500 mb-8">Add some products to get started!</p>
          <Link to="/products" className="btn-primary">
            Browse Products
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container-max py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Shopping Cart</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Cart Items */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex justify-between items-center mb-4">
            <span className="text-gray-600">{items.length} items</span>
            <button
              onClick={handleClearCart}
              className="text-red-600 hover:text-red-700 text-sm font-medium"
            >
              Clear Cart
            </button>
          </div>

          {items.map((item) => (
            <div
              key={item.id}
              className="bg-white rounded-lg shadow-sm border border-gray-200 p-4"
            >
              <div className="flex gap-4">
                {/* Product Image */}
                <div className="w-24 h-24 flex-shrink-0">
                  <img
                    src={item.product?.image_url || item.image || '/placeholder-product.png'}
                    alt={item.product?.name || item.name}
                    className="w-full h-full object-cover rounded-lg"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = '/placeholder-product.png';
                    }}
                  />
                </div>

                {/* Product Details */}
                <div className="flex-1">
                  <div className="flex justify-between">
                    <div>
                      <h3 className="font-semibold text-gray-900">
                        <Link to={`/products/${item.product?.sku || item.sku}`} className="hover:text-green-600">
                          {item.product?.name || item.name}
                        </Link>
                      </h3>
                      <p className="text-sm text-gray-500">{item.product?.brand || item.brand}</p>

                      {/* Size and Type Info */}
                      <div className="flex flex-wrap gap-3 mt-2">
                        {(item.product?.unit_weight || item.size) && (
                          <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                            Size: {item.product?.unit_weight || item.size}
                          </span>
                        )}
                        {item.weight && (
                          <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                            {item.weight}{item.unit || 'g'}
                          </span>
                        )}
                        {(item.product?.category || item.category) && (
                          <span className="text-xs bg-green-50 text-green-700 px-2 py-1 rounded">
                            {item.product?.category || item.category}
                          </span>
                        )}
                        {item.strain && (
                          <span className="text-xs bg-primary-50 text-primary-700 px-2 py-1 rounded">
                            {item.strain}
                          </span>
                        )}
                      </div>

                      <div className="flex gap-4 mt-2">
                        {(item.product?.thc_content || item.thc) ? (
                          <span className="text-xs text-primary-700">
                            THC: {(item.product?.thc_content || item.thc || 0).toFixed(1)}%
                          </span>
                        ) : null}
                        {(item.product?.cbd_content || item.cbd) ? (
                          <span className="text-xs text-blue-600">
                            CBD: {(item.product?.cbd_content || item.cbd || 0).toFixed(1)}%
                          </span>
                        ) : null}
                      </div>
                    </div>
                    <button
                      onClick={() => handleRemoveItem(item.id)}
                      className="text-red-500 hover:text-red-600"
                    >
                      <TrashIcon className="w-5 h-5" />
                    </button>
                  </div>

                  <div className="flex justify-between items-center mt-4">
                    {/* Quantity Controls */}
                    <div className="flex items-center border rounded-lg">
                      <button
                        onClick={() => handleUpdateQuantity(item.id, item.quantity - 1)}
                        className="p-2 hover:bg-gray-100"
                        disabled={item.quantity <= 1}
                      >
                        <MinusIcon className="w-4 h-4" />
                      </button>
                      <span className="px-4 py-2 border-x">{item.quantity}</span>
                      <button
                        onClick={() => handleUpdateQuantity(item.id, item.quantity + 1)}
                        className="p-2 hover:bg-gray-100"
                        disabled={item.maxQuantity ? item.quantity >= item.maxQuantity : false}
                      >
                        <PlusIcon className="w-4 h-4" />
                      </button>
                    </div>

                    {/* Price */}
                    <div className="text-right">
                      <div className="font-semibold text-gray-900">
                        ${(item.price * item.quantity).toFixed(2)}
                      </div>
                      <div className="text-xs text-gray-500">
                        ${item.price.toFixed(2)} each
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Order Summary */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 sticky top-4">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Order Summary</h2>

            {/* Promo Code */}
            <div className="mb-4">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={promoCode}
                  onChange={(e) => setPromoCode(e.target.value)}
                  placeholder="Promo code"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                />
                <button
                  onClick={handleApplyPromo}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Apply
                </button>
              </div>
              {discount > 0 && (
                <p className="text-sm text-green-600 mt-1">
                  Discount applied: {(discount * 100).toFixed(0)}% off
                </p>
              )}
            </div>

            {/* Price Breakdown */}
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Subtotal</span>
                <span className="font-medium">${subtotal.toFixed(2)}</span>
              </div>

              {discount > 0 && (
                <div className="flex justify-between text-green-600">
                  <span>Discount</span>
                  <span>-${discountAmount.toFixed(2)}</span>
                </div>
              )}

              <div className="flex justify-between">
                <span className="text-gray-600">Tax (HST)</span>
                <span className="font-medium">${tax.toFixed(2)}</span>
              </div>

              <div className="flex justify-between">
                <span className="text-gray-600">Delivery</span>
                <span className="font-medium">
                  {deliveryFee === 0 ? (
                    <span className="text-green-600">FREE</span>
                  ) : (
                    `$${deliveryFee.toFixed(2)}`
                  )}
                </span>
              </div>

              {subtotal < FREE_DELIVERY_THRESHOLD && (
                <p className="text-xs text-gray-500">
                  Add ${(FREE_DELIVERY_THRESHOLD - subtotal).toFixed(2)} more for free delivery
                </p>
              )}

              <div className="border-t pt-2 mt-4">
                <div className="flex justify-between text-lg font-semibold">
                  <span>Total</span>
                  <span>${finalTotal.toFixed(2)}</span>
                </div>
              </div>
            </div>

            {/* Store Selection */}
            {selectedStore && (
              <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-600">Pickup/Delivery from:</p>
                <p className="text-sm font-medium">{selectedStore.name}</p>
              </div>
            )}

            {/* Checkout Button */}
            <button
              onClick={handleCheckout}
              className="w-full mt-6 bg-green-600 text-white py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors"
            >
              Proceed to Checkout
            </button>

            {/* Continue Shopping */}
            <Link
              to="/products"
              className="block text-center text-sm text-gray-600 hover:text-gray-900 mt-4"
            >
              Continue Shopping
            </Link>
          </div>
        </div>
      </div>

      {/* Recommendations Section */}
      {items.length > 0 && (
        <div className="mt-16">
          <ProductRecommendations
            title="Trending Products You Might Like"
            products={trendingProducts}
            loading={loadingRecommendations}
          />
        </div>
      )}
    </div>
  );
};

export default Cart;