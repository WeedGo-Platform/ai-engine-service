import React, { useState, useEffect } from 'react';
import { FiTag, FiTrash2, FiPlus, FiMinus, FiShoppingCart } from 'react-icons/fi';
import { CheckoutSession } from '../../services/checkout';
import { Cart, cartService } from '../../services/cart';

interface CartReviewProps {
  session: CheckoutSession;
  onContinue: () => void;
  onApplyDiscount: (code: string) => Promise<{ success: boolean; message: string }>;
  theme: any;
}

const CartReview: React.FC<CartReviewProps> = ({ session, onContinue, onApplyDiscount, theme }) => {
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState(true);
  const [discountCode, setDiscountCode] = useState('');
  const [discountMessage, setDiscountMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [updatingItems, setUpdatingItems] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadCart();
  }, []);

  const loadCart = async () => {
    setLoading(true);
    try {
      const cartData = await cartService.getCart();
      setCart(cartData);
    } catch (error) {
      console.error('Failed to load cart:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateQuantity = async (itemId: string, newQuantity: number) => {
    if (!cart || newQuantity < 1) return;
    
    setUpdatingItems(prev => new Set(prev).add(itemId));
    
    try {
      const updatedCart = await cartService.updateCartItem(itemId, newQuantity);
      setCart(updatedCart);
    } catch (error) {
      console.error('Failed to update quantity:', error);
    } finally {
      setUpdatingItems(prev => {
        const newSet = new Set(prev);
        newSet.delete(itemId);
        return newSet;
      });
    }
  };

  const handleRemoveItem = async (itemId: string) => {
    if (!cart) return;
    
    setUpdatingItems(prev => new Set(prev).add(itemId));
    
    try {
      const updatedCart = await cartService.removeFromCart(itemId);
      setCart(updatedCart);
    } catch (error) {
      console.error('Failed to remove item:', error);
    } finally {
      setUpdatingItems(prev => {
        const newSet = new Set(prev);
        newSet.delete(itemId);
        return newSet;
      });
    }
  };

  const handleApplyDiscountCode = async () => {
    if (!discountCode.trim()) return;
    
    setDiscountMessage(null);
    const result = await onApplyDiscount(discountCode);
    
    setDiscountMessage({
      type: result.success ? 'success' : 'error',
      text: result.message
    });
    
    if (result.success) {
      setDiscountCode('');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!cart || cart.items.length === 0) {
    return (
      <div className="text-center py-12">
        <FiShoppingCart className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-lg font-medium text-gray-900">Your cart is empty</h3>
        <p className="mt-1 text-sm text-gray-500">Add some items to your cart to continue.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      {/* Cart Items */}
      <div className="lg:col-span-2">
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">Cart Items ({cart.item_count})</h2>
          </div>
          
          <div className="divide-y">
            {cart.items.map((item) => (
              <div key={item.id} className="p-6">
                <div className="flex items-start space-x-4">
                  {/* Product Image */}
                  {item.product_image && (
                    <img
                      src={item.product_image}
                      alt={item.product_name}
                      className="w-20 h-20 object-cover rounded-lg"
                    />
                  )}
                  
                  {/* Product Details */}
                  <div className="flex-1">
                    <h3 className="text-base font-medium text-gray-900">{item.product_name}</h3>
                    <p className="mt-1 text-sm text-gray-500">SKU: {item.product_id}</p>
                    <p className="mt-1 text-sm font-medium text-gray-900">${item.price.toFixed(2)} each</p>
                  </div>
                  
                  {/* Quantity Controls */}
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleUpdateQuantity(item.id, item.quantity - 1)}
                      disabled={item.quantity <= 1 || updatingItems.has(item.id)}
                      className="p-1 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <FiMinus className="w-4 h-4" />
                    </button>
                    
                    <span className="w-12 text-center font-medium">
                      {updatingItems.has(item.id) ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600 mx-auto"></div>
                      ) : (
                        item.quantity
                      )}
                    </span>
                    
                    <button
                      onClick={() => handleUpdateQuantity(item.id, item.quantity + 1)}
                      disabled={updatingItems.has(item.id)}
                      className="p-1 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <FiPlus className="w-4 h-4" />
                    </button>
                  </div>
                  
                  {/* Subtotal & Remove */}
                  <div className="text-right">
                    <p className="text-base font-medium text-gray-900">${item.subtotal.toFixed(2)}</p>
                    <button
                      onClick={() => handleRemoveItem(item.id)}
                      disabled={updatingItems.has(item.id)}
                      className="mt-2 text-red-600 hover:text-red-700 disabled:opacity-50"
                    >
                      <FiTrash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Order Summary */}
      <div className="lg:col-span-1">
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">Order Summary</h2>
          </div>
          
          <div className="p-6 space-y-4">
            {/* Discount Code */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Discount Code
              </label>
              <div className="flex space-x-2">
                <div className="relative flex-1">
                  <FiTag className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input
                    type="text"
                    value={discountCode}
                    onChange={(e) => setDiscountCode(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleApplyDiscountCode()}
                    placeholder="Enter code"
                    className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    disabled={!!session.discount_id}
                  />
                </div>
                <button
                  onClick={handleApplyDiscountCode}
                  disabled={!discountCode.trim() || !!session.discount_id}
                  className={`px-4 py-2 text-white rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${theme.primary}`}
                >
                  Apply
                </button>
              </div>
              
              {discountMessage && (
                <p className={`mt-2 text-sm ${discountMessage.type === 'success' ? 'text-green-600' : 'text-red-600'}`}>
                  {discountMessage.text}
                </p>
              )}
              
              {session.discount_id && (
                <div className="mt-2 p-2 bg-green-50 rounded-md">
                  <p className="text-sm text-green-700">
                    Discount applied: {session.coupon_code}
                  </p>
                </div>
              )}
            </div>

            {/* Price Breakdown */}
            <div className="space-y-2 pt-4 border-t">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Subtotal</span>
                <span className="font-medium">${session.subtotal.toFixed(2)}</span>
              </div>
              
              {session.discount_amount > 0 && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Discount</span>
                  <span className="font-medium text-green-600">-${session.discount_amount.toFixed(2)}</span>
                </div>
              )}
              
              {session.tax_amount > 0 && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Estimated Tax</span>
                  <span className="font-medium">${session.tax_amount.toFixed(2)}</span>
                </div>
              )}
              
              {session.delivery_fee > 0 && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Delivery Fee</span>
                  <span className="font-medium">${session.delivery_fee.toFixed(2)}</span>
                </div>
              )}
              
              <div className="flex justify-between text-base font-semibold pt-2 border-t">
                <span>Total</span>
                <span>${(session.subtotal - session.discount_amount).toFixed(2)}</span>
              </div>
              
              <p className="text-xs text-gray-500 pt-2">
                * Final total will be calculated after delivery details
              </p>
            </div>

            {/* Continue Button */}
            <button
              onClick={onContinue}
              className={`w-full py-3 text-white font-medium rounded-md transition-colors ${theme.primary}`}
            >
              Continue to Delivery
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CartReview;